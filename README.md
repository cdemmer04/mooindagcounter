# Mooindagcounter

Een teller-app gebouwd met Flask en een MySQL-compatibele database. Volledig te hosten op [Bunny.net](https://bunny.net).

## Stack

| Onderdeel | Dienst |
|---|---|
| Flask + Gunicorn | Bunny Magic Container |
| Database | Bunny Database (MySQL-compatible) |
| Statische bestanden | BunnyCDN Pull Zone |
| SSL | Bunny Edge SSL (automatisch) |
| DNS | BunnyDNS |
| Rate limiting / routing | Bunny Edge Scripting |

## Deployen op Bunny

### 1. Docker image bouwen en pushen

```bash
docker build -t mooindagcounter .
docker tag mooindagcounter storage.bunnycdn.com/<jouw-registry>/mooindagcounter:latest
docker push storage.bunnycdn.com/<jouw-registry>/mooindagcounter:latest
```

### 2. Bunny Database inrichten

1. Maak een Bunny Database instance aan via het Bunny dashboard.
2. Voer het schema-script uit:
   ```bash
   mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < create_db.sql
   ```
   > **Let op:** De `CREATE USER` en `GRANT` statements in `create_db.sql` zijn optioneel — Bunny Database beheert gebruikers via het dashboard.

### 3. Magic Container aanmaken

1. Ga naar **Magic Containers** in het Bunny dashboard.
2. Kies de gepushte Docker image.
3. Stel de volgende omgevingsvariabelen in (zie ook `.env.example`):

   | Variable | Waarde |
   |---|---|
   | `DB_HOST` | Host van de Bunny Database |
   | `DB_USER` | Database gebruikersnaam |
   | `DB_PASSWORD` | Database wachtwoord |
   | `DB_NAME` | `mooindagcounter` |
   | `DISCORD_WEBHOOK_URL` | *(optioneel)* Discord webhook URL |

4. Stel containerpoort in op **8080**.

### 4. BunnyCDN Pull Zone

1. Maak een Pull Zone aan met de Magic Container als origin.
2. Voeg cache-regels toe:
   - Cache: `/static/*`
   - Geen cache: `/increment`, `/api/*`, `/overview`

### 5. Edge Script (optioneel)

Kopieer de inhoud van `edge-script/rate-limit.js` naar een nieuw Edge Script in het Bunny dashboard. Dit script biedt:
- Rate limiting op `POST /increment` (max 5 per minuut per IP)
- `www` → apex redirect
- `Cache-Control: no-store` headers op dynamische routes

### 6. DNS

Wijs het domein `mooindagcounter.nl` via BunnyDNS naar de Pull Zone URL.

## Lokaal ontwikkelen

Kopieer `.env.example` naar `.env` en vul de waarden in:

```bash
cp .env.example .env
```

Start de app lokaal:

```bash
pip install -r requirements.txt
gunicorn app:app --bind 0.0.0.0:8080
```
