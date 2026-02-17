# Pokémon Stock Monitor

Monitor Pokémon TCG producten en krijg een Pushover-notificatie op je iPhone zodra iets op voorraad is. Draait automatisch in de cloud via GitHub Actions (elke 5 minuten).

## Producten die gevolgd worden

- Pokémon TCG Mega Evolution Perfect Order Elite Trainer Box (Pokémon Center)
- Pokémon TCG Mega Evolution Ascended Heroes Elite Trainer Box (Pokémon Center)
- Pokémon TCG Ascended Heroes Booster Bundle 6-packs (Pokémon Center)
- Pokémon Ascended Heroes ETB (MediaMarkt NL)

## Setup

### 1. Pushover

1. Installeer de Pushover-app op je iPhone ([App Store](https://apps.apple.com/app/pushover/id506088175))
2. Maak een account op [pushover.net](https://pushover.net)
3. Log in en kopieer je **User Key**
4. Ga naar [pushover.net/apps/build](https://pushover.net/apps/build) en maak een nieuwe applicatie
5. Vul een naam in (bijv. "Stock Monitor") en klik Create Application
6. Kopieer de **API Token/Key** van je nieuwe app

### 2. GitHub Repository

1. Maak een nieuw repository op GitHub (bijv. `pokemon-stock-monitor`)
2. Upload de bestanden uit deze map:
   - `check_stock.py`
   - `requirements.txt`
   - `.github/workflows/stock-monitor.yml`
3. Ga in je repo naar **Settings** → **Secrets and variables** → **Actions**
4. Klik **New repository secret** en voeg toe:
   - **PUSHOVER_USER_KEY** – je User Key van Pushover
   - **PUSHOVER_API_TOKEN** – de API Token van je app

### 3. Workflow activeren

1. Ga in je repo naar **Actions**
2. Selecteer de workflow **Stock Monitor**
3. Klik **Enable workflow** als dat nog niet gedaan is
4. De workflow draait nu automatisch elke 5 minuten

Je kunt ook handmatig draaien via **Actions** → **Stock Monitor** → **Run workflow**.

## Handmatig testen (lokaal)

```bash
cd stock-monitor
pip install -r requirements.txt

# Stel je Pushover-gegevens in
export PUSHOVER_USER_KEY="jouw_user_key"
export PUSHOVER_API_TOKEN="jouw_api_token"

python check_stock.py
```

## Let op

- **Pokémon Center** heeft soms bot-beveiliging. Als de pagina geblokkeerd wordt, wordt de status als "unknown" gemeld (geen notificatie).
- Notificaties worden alleen verstuurd bij producten die **net** op voorraad komen. Als iets al langer op voorraad is, krijg je geen dubbele meldingen.
