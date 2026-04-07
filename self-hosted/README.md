# Mooindagcounter — Self-hosted

Flask app met MariaDB, draait via Docker Compose.

## Starten

```sh
cp .env.example .env
# Stel een sterk wachtwoord in voor DB_PASSWORD in .env

docker compose up -d
```

App draait op `http://localhost:8080`.

## Stoppen

```sh
docker compose down        # behoudt data
docker compose down -v     # verwijdert ook alle data
```
