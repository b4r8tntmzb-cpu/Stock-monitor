#!/usr/bin/env python3
"""
Pokémon product stock monitor.
Checks product pages for availability and sends Pushover notifications.
"""

import os
import re
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Products to monitor: (name, url)
PRODUCTS = [
    ("Pokémon TCG Perfect Order ETB", "https://www.pokemoncenter.com/product/10-10372-109/pokemon-tcg-mega-evolution-perfect-order-pokemon-center-elite-trainer-box"),
    ("Pokémon TCG Ascended Heroes ETB", "https://www.pokemoncenter.com/product/10-10315-108/pokemon-tcg-mega-evolution-ascended-heroes-pokemon-center-elite-trainer-box"),
    ("Pokémon TCG Ascended Heroes Booster Bundle", "https://www.pokemoncenter.com/product/10-10311-114/pokemon-tcg-mega-evolution-ascended-heroes-booster-bundle-6-packs"),
    ("MediaMarkt Ascended Heroes ETB", "https://www.mediamarkt.nl/nl/product/_pokemon-ue-me025-ascended-heroes-etb-trading-cards-1895844.html"),
]

# Browser-like headers to reduce bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# File to remember what we've already notified (avoid spam)
# Use STATE_DIR env var for GitHub Actions (cacheable path)
_state_dir = os.environ.get("STATE_DIR", os.path.dirname(__file__))
STATE_FILE = os.path.join(_state_dir, "last_notified.txt")


def get_session():
    """Create requests session with retries."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def check_pokemon_center(html: str, url: str) -> str | None:
    """
    Check Pokémon Center page for stock.
    Returns: 'in_stock', 'out_of_stock', or None (could not determine)
    """
    # Bot block / captcha page
    if "Pardon Our Interruption" in html or "made us think you were a bot" in html:
        return None

    text_lower = html.lower()

    # Out of stock indicators
    out_of_stock = [
        "out of stock",
        "sold out",
        "notify me",
        "notify me when back",
        "currently unavailable",
        "coming soon",
        "out-of-stock",
    ]
    for indicator in out_of_stock:
        if indicator in text_lower:
            return "out_of_stock"

    # In stock indicators
    in_stock = [
        "add to cart",
        "add to bag",
        "in stock",
        "buy now",
    ]
    for indicator in in_stock:
        if indicator in text_lower:
            return "in_stock"

    return None


def check_mediamarkt(html: str, url: str) -> str | None:
    """
    Check MediaMarkt page for stock.
    Returns: 'in_stock', 'out_of_stock', or None (could not determine)
    """
    text_lower = html.lower()

    # Out of stock
    if any(x in text_lower for x in ["uitverkocht", "niet op voorraad", "niet beschikbaar", "out of stock"]):
        return "out_of_stock"

    # In stock
    if any(x in text_lower for x in ["in winkelwagen", "bestel", "op voorraad", "add to cart"]):
        return "in_stock"

    return None


def check_product(session: requests.Session, name: str, url: str) -> str | None:
    """Fetch page and determine stock status."""
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text

        if "pokemoncenter.com" in url:
            return check_pokemon_center(html, url)
        if "mediamarkt.nl" in url:
            return check_mediamarkt(html, url)

        return None
    except Exception as e:
        print(f"Error checking {name}: {e}", file=sys.stderr)
        return None


def send_pushover(message: str, title: str = "Voorraad alert"):
    """Send Pushover notification."""
    user_key = os.environ.get("PUSHOVER_USER_KEY")
    api_token = os.environ.get("PUSHOVER_API_TOKEN")

    if not user_key or not api_token:
        print("PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN must be set", file=sys.stderr)
        return False

    try:
        r = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": api_token,
                "user": user_key,
                "title": title,
                "message": message,
                "priority": 1,
            },
            timeout=10,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"Pushover error: {e}", file=sys.stderr)
        return False


def load_notified_set() -> set[str]:
    """Load set of product URLs we've already sent notifications for."""
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE) as f:
        return set(line.strip() for line in f if line.strip())


def save_notified(url: str):
    """Record that we sent a notification for this URL."""
    notified = load_notified_set()
    notified.add(url)
    with open(STATE_FILE, "w") as f:
        for u in notified:
            f.write(u + "\n")


def main():
    session = get_session()
    in_stock = []
    notified = load_notified_set()

    for name, url in PRODUCTS:
        status = check_product(session, name, url)
        print(f"{name}: {status or 'unknown'}")

        if status == "in_stock":
            in_stock.append((name, url))
        elif status == "out_of_stock" and url in notified:
            # Was in stock before, now out - could remove from notified to allow re-alert on next restock
            pass

        time.sleep(1)  # Be nice to servers

    if not in_stock:
        sys.exit(0)

    # Send notification for new in-stock items we haven't notified yet
    new_items = [(n, u) for n, u in in_stock if u not in notified]
    if not new_items:
        sys.exit(0)

    lines = [f"✅ {n}\n{u}" for n, u in new_items]
    message = "\n\n".join(lines)
    title = "Voorraad beschikbaar!" if len(new_items) == 1 else f"{len(new_items)} producten op voorraad!"

    if send_pushover(message, title):
        for _, url in new_items:
            save_notified(url)
        print("Notification sent.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
