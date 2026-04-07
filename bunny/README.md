# Mooindagcounter — Bunny

Flask app volledig gehost op [Bunny.net](https://bunny.net).

## Benodigde Bunny diensten

| Dienst | Gebruik |
|---|---|
| **Database** | MySQL-compatibele database voor de teller |
| **Magic Containers** | Draait de Flask app als Docker container |
| **Edge Scripts** | Rate limiting, www-redirect, cache headers |

## Setup

### 1. Database

Maak een database aan via het Bunny dashboard en voer het schema uit:

```bash
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < create_db.sql
```

> De `CREATE USER` en `GRANT` regels in `create_db.sql` kun je overslaan — Bunny beheert gebruikers via het dashboard.

### 2. Magic Container

1. Bouw en push de Docker image naar je Bunny container registry.
2. Maak een Magic Container aan en stel de omgevingsvariabelen in (zie `.env.example`).
3. Stel de health check in op `GET /healthz` en poort `8080`.

### 3. Edge Script

Maak een nieuw Edge Script aan in het Bunny dashboard en plak de inhoud van `edge-script/rate-limit.js`. Koppel het aan de Pull Zone die voor je container staat.

### 4. Pull Zone

Wijs de Pull Zone naar je Magic Container als origin. Stel caching in:
- Wel cachen: `/static/*`
- Niet cachen: `/`, `/increment`, `/overview`, `/api/*`
