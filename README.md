# Mooindagcounter

Een simpele teller-app gebouwd met Flask. Één app + één MariaDB database (MariaDB 12.2 LTS).

## Quick Start

```bash
# Copy example env file
cp src/.env.example .env

# Edit .env with your settings (DB_PASSWORD, Discord webhook, etc.)
nano .env

# Start with Docker Compose
docker compose up --build
```

Visit `http://localhost:8080`.

## Deployment

**Single image approach:** App + MariaDB runnen samen als containers.

- **Locally:** Use `docker-compose.yml` (included).
- **Bunny Magic Containers:** Use the same image (`ghcr.io/<owner>/mooindagcounter:latest`) with a separate MariaDB container or any managed database.

### Environment Variables

- `DB_HOST`: MariaDB host (default: `localhost` or `db` in Docker)
- `DB_PORT`: MariaDB port (default: `3306`)
- `DB_USER`: Database user (default: `mooindagcounter`)
- `DB_PASSWORD`: Database password (required)
- `DB_NAME`: Database name (default: `mooindagcounter`)
- `DISCORD_WEBHOOK_URL`: Optional Discord notifications
- `GUNICORN_WORKERS`: Number of app workers (default: `2`)

## Structure

- `src/`: Python Flask app, templates, static assets, Dockerfile
- `docker-compose.yml`: Local development setup
- `.github/workflows/`: CI/CD for building and pushing Docker images

## Optional: Bunny Edge Script

The `src/edge-script/rate-limit.js` script provides:
- Rate limiting (5 requests per IP per minute)
- www → apex domain redirect
- Cache-Control headers for dynamic routes

Deploy this script in Bunny CDN if needed.
