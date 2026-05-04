# Mooindagcounter

Een simpele teller-app gebouwd met Flask. Één app + één MariaDB database (MariaDB 12.2 LTS).

## Quick Start

```bash
# Copy example env file
cp src/web/.env.example .env

# Edit .env with your settings (DB_PASSWORD, Discord webhook, etc.)
nano .env

# Start with Docker Compose
docker compose up --build
```

Visit `http://localhost:8080`.

## Deployment

**Two-image approach:** `mooindagcounter-web` (Flask) and `mooindagcounter-db` (MariaDB) run as separate containers.

- **Locally:** Use `docker-compose.yml` (included).
- **Production:** Pull `ghcr.io/<owner>/mooindagcounter-web:latest` and `ghcr.io/<owner>/mooindagcounter-db:latest`.

### Environment Variables

- `DB_HOST`: MariaDB host (default: `localhost` or `db` in Docker)
- `DB_PORT`: MariaDB port (default: `3306`)
- `DB_USER`: Database user (default: `mooindagcounter`)
- `DB_PASSWORD`: Database password (required)
- `DB_NAME`: Database name (default: `mooindagcounter`)
- `DISCORD_WEBHOOK_URL`: Optional Discord notifications
- `GUNICORN_WORKERS`: Number of app workers (default: `2`)

## Structure

- `src/web/`: Python Flask app, templates, static assets, Dockerfile
- `src/db/`: MariaDB Dockerfile and schema
- `docker-compose.yml`: Local development setup
- `.github/workflows/`: CI/CD for building and pushing both Docker images

## Optional: Bunny Edge Script

The `src/web/edge-script/rate-limit.js` script provides:
- Rate limiting (5 requests per IP per minute)
- www → apex domain redirect
- Cache-Control headers for dynamic routes

Deploy this script in Bunny CDN if needed.

