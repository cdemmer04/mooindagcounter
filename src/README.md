# Mooindagcounter - App

Flask-based counter application with MariaDB backend.

## Structure

- `app.py`: Main Flask application and database layer
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container definition
- `create_db.sql`: Database schema (run on first startup)
- `.env.example`: Example environment variables
- `templates/`: HTML templates (Jinja2)
- `static/`: CSS, images, manifest, robots.txt
- `edge-script/`: Optional Bunny CDN edge script for rate limiting

## Running Locally

```bash
# From repo root:
cp src/.env.example .env
# Edit .env with your values (especially DB_PASSWORD)
docker compose up --build
```

App runs on `http://localhost:8080`.

## Environment Variables

```
DB_HOST=localhost          # MariaDB hostname
DB_PORT=3306              # MariaDB port
DB_USER=mooindagcounter   # DB user
DB_PASSWORD=              # DB password (required)
DB_NAME=mooindagcounter   # Database name
DISCORD_WEBHOOK_URL=      # Optional: Discord notifications
GUNICORN_WORKERS=2        # Number of app workers
```

## Database

The app expects a `counts` table with columns:
- `id` (INT, PRIMARY KEY)
- `message` (TEXT)
- `date` (TEXT)
- `time` (TEXT)
- `client_ip` (TEXT)

This is created automatically via `create_db.sql` on first startup.

## API Routes

- `GET /` - Main counter page
- `POST /increment` - Increment counter with message
- `GET /overview` - List all counts
- `DELETE /api/counts/<id>` - Delete a count
- `GET /healthz` - Health check
- `GET /api/counts` - JSON API list all

## Deployment Notes

- The Docker image is built from this folder and pushed to GHCR via GitHub Actions.
- Use a containerized MariaDB (locally or via Bunny) as the database.
- For Bunny Magic Containers: deploy this image + a MariaDB container, ensure `DB_HOST` points to the MariaDB service.
- Static assets are served by Flask (in production, consider a CDN or reverse proxy).
