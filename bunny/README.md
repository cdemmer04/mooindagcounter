# Mooindagcounter - Bunny

Flask app voor Bunny.net met een duidelijke scheiding:
- **Magic Containers** draait de app image
- **Bunny Database** levert de data-opslag

## Wat is het package op GHCR precies?

Het package op GHCR (`ghcr.io/stensel8/mooindagcounter`) is een kant-en-klare image voor de app container.

Belangrijk:
- Deze image bevat **niet** ook een database.
- Een database bundel je in de praktijk als **aparte service/container**.
- In de huidige `bunny/` code wordt specifiek Bunny Database (libSQL) gebruikt.

Dus: package pullen = app direct deploybaar, maar database moet nog gekoppeld worden via env vars.

## Standaard Bunny setup (aanbevolen)

### 1. Bunny Database aanmaken

Maak een database aan via **Edge Platform -> Database** in het Bunny dashboard.

Bewaar deze credentials:

| Veld | Variabele |
|---|---|
| `BUNNY_DATABASE_URL` | `libsql://...` URL |
| `BUNNY_DATABASE_AUTH_TOKEN` | read/write token |

Maak daarna de tabel via de Database Editor:

```sql
CREATE TABLE IF NOT EXISTS counts (
    id INTEGER PRIMARY KEY,
    message TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    client_ip TEXT NOT NULL
);
```

### 2. Magic Container aanmaken met de GHCR image

De image wordt automatisch gebouwd en gepusht via `.github/workflows/docker-publish.yml`.

Gebruik als image:

```text
ghcr.io/stensel8/mooindagcounter:latest
```

Bij een fork: vervang `stensel8` door jouw GitHub gebruikersnaam.

Zet deze environment variables op de container:

| Variabele | Waarde |
|---|---|
| `BUNNY_DATABASE_URL` | `libsql://...` (uit stap 1) |
| `BUNNY_DATABASE_AUTH_TOKEN` | read/write token (uit stap 1) |
| `DISCORD_WEBHOOK_URL` | optioneel |
| `GUNICORN_WORKERS` | optioneel, standaard `2` |

Health check:
- Pad: `GET /healthz`
- Poort: `8080`

### 3. Pull Zone koppelen

Wijs de Pull Zone naar de Magic Container als origin.

Cachingadvies:
- Wel cachen: `/static/*`
- Niet cachen: `/`, `/increment`, `/overview`, `/api/*`

### 4. Edge Script (optioneel)

Maak een Edge Script en plak `edge-script/rate-limit.js`. Koppel het script aan de Pull Zone.

## Kan ik app + database als 2 containers in Bunny draaien?

Ja, Bunny Magic Containers ondersteunt multi-container apps (2 samenwerkende containers in 1 app).

Maar:
- Dat is **niet** hetzelfde als 1 image met 2 containers.
- Je gebruikt dan minimaal 2 images (bijv. app image + aparte database image).
- De huidige `bunny/` app verwacht Bunny Database (libSQL), niet MariaDB.

Wil je direct app + MariaDB als set draaien zonder code-aanpassingen, gebruik `self-hosted/`.
