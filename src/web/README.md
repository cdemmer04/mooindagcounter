# Mooindagcounter - Web

Mooindag! FastAPI-gebaseerde teller-app met MariaDB als backend.

## Structuur

- `app.py`: FastAPI-app en databaselaag
- `requirements.txt`: Python-afhankelijkheden
- `Dockerfile`: Container definitie voor `mooindagcounter-web`
- `.env.example`: Voorbeeld omgevingsvariabelen
- `templates/`: HTML-templates (Jinja2)
- `static/`: CSS, afbeeldingen, manifest, robots.txt

## Lokaal draaien

```bash
# Vanuit de repo root:
cp src/web/.env.example .env
# Vul je waarden in (in elk geval DB_PASSWORD en MARIADB_ROOT_PASSWORD)
docker compose up --build
```

App draait op `http://localhost:8080`.

## Omgevingsvariabelen

```
DB_HOST=localhost          # MariaDB hostnaam
DB_PORT=3306               # MariaDB poort
DB_USER=mooindagcounter    # DB gebruiker
DB_PASSWORD=               # DB wachtwoord (verplicht)
DB_NAME=mooindagcounter    # Databasenaam
DISCORD_WEBHOOK_URL=       # Optioneel: Discord meldingen
GUNICORN_WORKERS=2         # Aantal Gunicorn+Uvicorn workers
```

## Database

De app verwacht een `counts` tabel, automatisch aangemaakt via `src/db/create_db.sql` bij eerste opstart.

| Kolom | Type |
|---|---|
| `id` | INT AUTO_INCREMENT PRIMARY KEY |
| `message` | TEXT NOT NULL |
| `date` | TEXT NOT NULL |
| `time` | TEXT NOT NULL |
| `client_ip` | TEXT NOT NULL |

## Routes

Alle HTML-responses sturen `Cache-Control: no-store` zodat CDN's en browsers dynamische pagina's nooit cachen.

---

### `GET /`
Teller pagina.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/
```

</details>

---

### `POST /increment`
Nieuwe count toevoegen. Formulierveld `message` verplicht (max 300 tekens, uniek).

<details>
<summary>Voorbeeld</summary>

```bash
curl -X POST https://mooindagcounter.nl/increment \
  -d "message=mooie+dag"
```

</details>

---

### `GET /overview`
Overzicht van alle counts met verwijderknop per rij.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/overview
```

</details>

---

### `POST /remove/{id}`
Count verwijderen (via formulier in de web UI).

<details>
<summary>Voorbeeld</summary>

```bash
curl -X POST https://mooindagcounter.nl/remove/5
```

</details>

---

### `GET /healthz`
Statuscheck. Retourneert `{"status": "ok"}` als de database bereikbaar is.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/healthz
```

</details>

---

### `GET /api/counts`
Alle counts ophalen als JSON-array.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/api/counts
```

Respons:
```json
[
  { "count": 15, "date": "2026-05-14", "message": "kanusje" },
  { "count": 14, "date": "2026-05-14", "message": "kanus" }
]
```

</details>

---

### `GET /api/counts/{id}`
Een count ophalen op basis van ID.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/api/counts/15
```

Respons:
```json
{ "id": 15, "message": "kanusje", "date": "2026-05-14", "time": "19:58:42", "client_ip": "1.2.3.4" }
```

</details>

---

### `DELETE /api/counts/{id}`
Count verwijderen via de API.

<details>
<summary>Voorbeeld</summary>

```bash
curl -X DELETE https://mooindagcounter.nl/api/counts/15
```

Respons:
```json
{ "message": "Record 15 deleted" }
```

</details>

---

## Deployment

Het Docker image (`mooindagcounter-web`) wordt gebouwd vanuit deze map en gepusht naar GHCR via GitHub Actions. Combineer met het `mooindagcounter-db` image voor de database.

De app draait als Gunicorn-proces met UvicornWorker (ASGI). Protocolonderhandeling met de browser loopt via Bunny.net (CDN). De interne verbinding van Bunny naar de container is HTTP/1.1, wat standaard is en niet gewijzigd hoeft te worden.
