# Mooindagcounter

Mooindag! FastAPI-teller met MariaDB als backend, draait op Bunny.net Magic Containers.

## Lokaal draaien

Kopieer het env-bestand en vul je waarden in:

```bash
cp src/web/.env.example .env
```

Start de app:

```bash
docker compose up --build
```

App draait op `http://localhost:8080`.

## Omgevingsvariabelen

| Variabele | Standaard | Omschrijving |
|---|---|---|
| `DB_HOST` | `localhost` | MariaDB hostnaam |
| `DB_PORT` | `3306` | MariaDB poort |
| `DB_USER` | `mooindagcounter` | DB gebruiker |
| `DB_PASSWORD` | _(verplicht)_ | DB wachtwoord |
| `DB_NAME` | `mooindagcounter` | Databasenaam |
| `DISCORD_WEBHOOK_URL` | _(leeg)_ | Optioneel: Discord meldingen |
| `GUNICORN_WORKERS` | `2` | Aantal Gunicorn+Uvicorn workers |

## Database

Tabel `counts`, automatisch aangemaakt via `src/db/create_db.sql` bij eerste opstart.

| Kolom | Type |
|---|---|
| `id` | INT AUTO_INCREMENT PRIMARY KEY |
| `message` | TEXT NOT NULL |
| `date` | TEXT NOT NULL |
| `time` | TEXT NOT NULL |
| `client_ip` | TEXT NOT NULL |

## Routes

HTML-responses sturen `Cache-Control: no-store` zodat CDN's en browsers niets cachen.

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

Formulierveld `message` is verplicht (max 300 tekens, uniek). Redirect naar `/` na opslaan.

<details>
<summary>Voorbeeld</summary>

```bash
curl -X POST https://mooindagcounter.nl/increment \
  -d "message=mooie+dag"
```

</details>

---

### `GET /overview` — Overzicht (web UI)

Tabel van alle counts, nieuwste eerst, met verwijderknop per rij.

<details>
<summary>Voorbeeld</summary>

```bash
curl https://mooindagcounter.nl/overview
```

</details>

---

### `POST /remove/{id}` — Count verwijderen (web UI)

Verwijdert een count en stuurt door naar `/overview`.

<details>
<summary>Voorbeeld</summary>

```bash
curl -X POST https://mooindagcounter.nl/remove/5
```

</details>

---

### `GET /api/counts` — Alle counts (JSON)

Geeft alle counts terug als JSON-array, nieuwste eerst.

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

Equivalent van `POST /remove/{id}` in de web UI.

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

Geeft `{"status": "ok"}` als de database bereikbaar is, anders HTTP 503.

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

Permanente `301` redirect naar `/`.

---

### `GET /robots.txt`

Serveert `static/robots.txt` op het root-pad.

---

## Deployment

Image wordt gebouwd en gepusht naar GHCR via GitHub Actions. Combineer met het `mooindagcounter-db` image voor de database. De app draait als Gunicorn+UvicornWorker (ASGI), HTTP/2 en HTTP/3 lopen via Bunny.net.
