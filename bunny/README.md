# Mooindagcounter — Bunny

Flask app volledig gehost op [Bunny.net](https://bunny.net).

## Stack

| Dienst | Gebruik |
|---|---|
| **Database** | Bunny Database (libSQL) |
| **Magic Containers** | Draait de Flask app als Docker container |
| **Edge Scripts** | Rate limiting, www-redirect, cache headers |

## Setup

### 1. Database

Maak een database aan via **Edge Platform → Database** in het Bunny dashboard.

Sla deze twee waarden op uit de credentials die Bunny geeft:

| Veld | Variabele |
|---|---|
| `BUNNY_DATABASE_URL` | de `libsql://...` URL |
| `BUNNY_DATABASE_AUTH_TOKEN` | de read/write token |

Maak daarna de tabel aan via de **Database Editor**:

```sql
CREATE TABLE IF NOT EXISTS counts (
    id INTEGER PRIMARY KEY,
    message TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    client_ip TEXT NOT NULL
);
```

### 2. Magic Container

1. Push de Docker image naar je Bunny container registry.
2. Maak een Magic Container aan met deze omgevingsvariabelen:

| Variabele | Waarde |
|---|---|
| `BUNNY_DATABASE_URL` | `libsql://...` (uit stap 1) |
| `BUNNY_DATABASE_AUTH_TOKEN` | read/write token (uit stap 1) |
| `DISCORD_WEBHOOK_URL` | *(optioneel)* |
| `GUNICORN_WORKERS` | *(optioneel, standaard 2)* |

3. Health check: `GET /healthz`, poort `8080`.

### 3. Edge Script

Maak een nieuw Edge Script aan en plak de inhoud van `edge-script/rate-limit.js`. Koppel het aan de Pull Zone die voor de container staat.

### 4. Pull Zone

Wijs de Pull Zone naar de Magic Container als origin. Caching:
- Wel: `/static/*`
- Niet: `/`, `/increment`, `/overview`, `/api/*`
