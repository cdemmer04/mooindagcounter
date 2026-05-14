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

### `GET /` — Teller pagina

Toont de huidige tellerstand en het invoerformulier.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/
```

</details>

---

### `POST /increment` — Nieuwe count toevoegen

Formulierveld `message` is verplicht (max 300 tekens, uniek). Stuurt na opslaan een `303 See Other` redirect naar `/`. Valideert op leeg, te lang en duplicaat.

<details>
<summary>Voorbeeld</summary>

```bash
curl -X POST https://mooindagcounter.nl/increment \
  -d "message=mooie+dag"
```

</details>

---

### `GET /overview` — Overzicht (web UI)

Toont een tabel van alle counts, van nieuwste naar oudste, met een verwijderknop per rij.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/overview
```

</details>

---

### `POST /remove/{id}` — Count verwijderen (web UI)

Verwijdert een count op basis van ID en stuurt door naar `/overview`. Wordt aangeroepen via de verwijderknop in het overzicht.

<details>
<summary>Voorbeeld</summary>

```bash
curl -X POST https://mooindagcounter.nl/remove/5
```

</details>

---

### `GET /api/counts` — Alle counts (JSON)

Geeft alle counts terug als JSON-array, gesorteerd van nieuwste naar oudste.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/api/counts
```

Respons:
```json
[
  { "count": 15, "message": "kanusje", "date": "2026-05-14" },
  { "count": 14, "message": "kanus",   "date": "2026-05-14" }
]
```

</details>

---

### `GET /api/counts/{id}` — Specifieke count (JSON)

Geeft een volledige count terug op basis van ID, inclusief tijdstip en IP-adres.

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

### `DELETE /api/counts/{id}` — Count verwijderen (API)

Verwijdert een count via de API. Equivalent van `POST /remove/{id}` in de web UI.

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

### `GET /healthz` — Statuscheck

Retourneert `{"status": "ok"}` als de database bereikbaar is, anders `{"status": "db_unavailable"}` met HTTP 503.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/healthz
```

Respons:
```json
{ "status": "ok" }
```

</details>

---

### `GET /index` — Redirect

Permanente `301` redirect naar `/` voor achterwaartse compatibiliteit.

---

### `GET /robots.txt`

Serveert `static/robots.txt` op het verwachte root-pad.

---

## Deployment

Het Docker image (`mooindagcounter-web`) wordt gebouwd vanuit deze map en gepusht naar GHCR via GitHub Actions. Combineer met het `mooindagcounter-db` image voor de database.

De app draait als Gunicorn-proces met UvicornWorker (ASGI). Protocolonderhandeling met de browser loopt via Bunny.net (CDN). De interne verbinding van Bunny naar de container is HTTP/1.1, wat standaard is en niet gewijzigd hoeft te worden.
