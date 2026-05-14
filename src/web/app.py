import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import aiomysql
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Laad omgevingsvariabelen uit .env (alleen lokaal; in productie komen ze via Docker env).
load_dotenv("./.env")

logger = logging.getLogger("uvicorn.error")

# Tijdzone voor het opslaan van datum/tijd bij elke increment.
AMS = ZoneInfo(os.getenv("TZ", "Europe/Amsterdam"))

# Maximale berichtlengte om de database te beschermen tegen oversized invoer.
MAX_MESSAGE_LENGTH = 300

# Globale verbindingspool; gedeeld tussen alle requests.
_pool: aiomysql.Pool | None = None
_pool_lock = asyncio.Lock()

# Sterke referenties naar achtergrondtaken zodat de GC ze niet vroegtijdig verwijdert.
_background_tasks: set[asyncio.Task] = set()


# --- Levenscyclus van de applicatie ---

async def _create_pool() -> aiomysql.Pool | None:
    """Maakt de verbindingspool aan. Geeft None terug als de DB niet bereikbaar is."""
    try:
        return await aiomysql.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            db=os.getenv("DB_NAME", "mooindagcounter"),
            autocommit=True,
            cursorclass=aiomysql.DictCursor,
            minsize=2,
            maxsize=10,
        )
    except Exception as e:
        logger.warning("DB-pool aanmaken mislukt: %s", e)
        return None


async def get_pool() -> aiomysql.Pool | None:
    """
    Geeft de verbindingspool terug, of maakt hem aan als die er nog niet is.
    Lazy initialisatie zodat de app blijft werken als de DB trager opstart
    dan de webcontainer (o.a. bij Bunny Magic Containers met gedeelde namespace).
    """
    global _pool
    if _pool:
        return _pool
    async with _pool_lock:
        if not _pool:
            _pool = await _create_pool()
    return _pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Probeert de pool bij opstart aan te maken; sluit hem netjes af bij afsluiten."""
    await get_pool()
    yield
    if _pool:
        _pool.close()
        await _pool.wait_closed()


app = FastAPI(lifespan=lifespan, docs_url=None, openapi_url=None, redoc_url=None)
templates = Jinja2Templates(directory="templates")

# Serveer bestanden uit de static/-map op het /static/-pad (CSS, afbeeldingen, favicon).
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Cache-middleware ---

class NoCacheHTMLMiddleware(BaseHTTPMiddleware):
    """
    Voegt 'Cache-Control: no-store' toe aan elke HTML-response.
    Zonder deze header slaat Bunny.net (en andere CDN's/browsers) pagina's op,
    waardoor de teller een verouderde stand toont na een nieuwe invoer.
    JSON- en statische bestanden worden niet geraakt door deze middleware.
    """
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if "text/html" in response.headers.get("content-type", ""):
            response.headers["cache-control"] = "no-store"
        return response


app.add_middleware(NoCacheHTMLMiddleware)


# --- Database hulpfuncties --- Mooindag!

async def db_query(sql: str, params: tuple = ()) -> list | None:
    """
    Voert een SELECT-query uit en geeft alle rijen terug als lijst van dicts.
    Geeft None terug bij een DB-fout of onbereikbare DB.
    """
    pool = await get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                return await cur.fetchall()
    except Exception as e:
        logger.error("DB query fout: %s", e)
        return None


async def db_execute(sql: str, params: tuple = ()) -> bool:
    """Voert een niet-SELECT statement uit. Geeft True terug bij succes."""
    pool = await get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
        return True
    except Exception as e:
        logger.error("DB execute fout: %s", e)
        return False


async def db_insert(sql: str, params: tuple = ()) -> int | None:
    """Voert een INSERT uit en geeft het nieuwe rij-ID terug."""
    pool = await get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                return cur.lastrowid
    except Exception as e:
        logger.error("DB insert fout: %s", e)
        return None


# --- Foutafhandeling --- Mooindag...

@app.exception_handler(StarletteHTTPException)
async def http_exception(request: Request, exc: StarletteHTTPException):
    """Vangt HTTP-fouten op en geeft altijd JSON terug."""
    return JSONResponse(
        {"error": exc.detail or "HTTP error"},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    """
    Vangnet voor alle onverwachte fouten die niet als HTTP-uitzondering zijn afgehandeld.
    Logt de fout en toont de offline-pagina met een 500-status.
    """
    logger.error("Onverwachte fout: %s", exc)
    return templates.TemplateResponse(
        request, "db_offline.html", {}, status_code=500
    )


# --- Applicatielogica --- Mooindag!

async def push_to_discord(counter: int, message: str, timestamp: datetime) -> None:
    """
    Stuurt een melding naar het Discord-webhook na een succesvolle increment.
    Wordt aangeroepen via asyncio.create_task() zodat de gebruiker niet hoeft
    te wachten op de Discord-response voordat de redirect plaatsvindt.
    """
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                url,
                json={
                    "content": (
                        f"Counter: {counter}\n"
                        f"Datum: {timestamp.strftime('%d-%m-%Y')}\n"
                        f"Tijd: {timestamp.strftime('%H:%M')}\n"
                        f"{message.capitalize()}"
                    )
                },
            )
    except httpx.RequestError as e:
        logger.warning("Discord webhook mislukt: %s", e)


def get_client_ip(request: Request) -> str:
    """
    Haalt het echte IP-adres van de bezoeker op.
    Bunny.net stuurt de keten van proxies mee in X-Forwarded-For;
    de eerste waarde daarin is het originele client-IP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def save_counter(message: str, date, time, client_ip: str) -> int | None:
    """Sla een nieuwe count op en geef het automatisch toegewezen ID terug."""
    return await db_insert(
        "INSERT INTO counts (message, date, time, client_ip) VALUES (%s, %s, %s, %s)",
        (message, str(date), str(time), client_ip),
    )


async def get_counter(entry_id: int) -> dict | None:
    """Haal een specifieke count op via ID, of None als die niet bestaat."""
    rows = await db_query("SELECT * FROM counts WHERE id = %s", (entry_id,))
    return rows[0] if rows else None


async def get_all_counters() -> list | None:
    """Haal alle counts op, gesorteerd van nieuwste naar oudste."""
    return await db_query("SELECT id, message, date, time FROM counts ORDER BY id DESC")


async def get_latest_counter() -> int | None:
    """
    Geeft de huidige tellerstand terug: het hoogste ID in de tabel.
    Geeft 0 terug als de tabel leeg is, None als de DB niet bereikbaar is.
    """
    rows = await db_query("SELECT id FROM counts ORDER BY id DESC LIMIT 1")
    if rows is None:
        return None
    return rows[0]["id"] if rows else 0


async def message_exists(message: str) -> bool:
    """Controleert of een bericht al eerder is ingevoerd (duplicaatbeveiliging)."""
    rows = await db_query("SELECT 1 FROM counts WHERE message = %s LIMIT 1", (message,))
    return bool(rows)


# --- Routes --- Mooindag...

@app.get("/")
async def index(request: Request):
    """Toont de hoofdpagina met de huidige tellerstand."""
    counter = await get_latest_counter()
    if counter is None:
        return templates.TemplateResponse(request, "db_offline.html", {}, status_code=503)
    return templates.TemplateResponse(request, "index.html", {"counter": counter})


@app.post("/increment")
async def increment(request: Request, message: str = Form("")):
    """
    Verwerkt een nieuwe increment-invoer vanuit het formulier.
    Valideert het bericht (niet leeg, niet te lang, niet al eerder ingevoerd),
    slaat het op in de DB en stuurt een Discord-melding op de achtergrond.
    Gebruik status 303 (See Other) zodat de browser na de redirect een GET doet
    in plaats van de POST te herhalen bij het verversen van de pagina.
    """
    timestamp = datetime.now(tz=AMS)
    counter = await get_latest_counter()
    if counter is None:
        return templates.TemplateResponse(request, "db_offline.html", {}, status_code=503)

    message = message.strip().lower()

    # Valideer invoer voordat de DB wordt benaderd.
    if not message:
        return templates.TemplateResponse(
            request, "index.html", {"counter": counter, "error_message": "empty"}
        )
    if len(message) > MAX_MESSAGE_LENGTH:
        return templates.TemplateResponse(
            request, "index.html", {"counter": counter, "error_message": "too_long"}
        )
    if await message_exists(message):
        return templates.TemplateResponse(
            request, "index.html", {"counter": counter, "error_message": "duplicate"}
        )

    new_id = await save_counter(
        message,
        timestamp.date(),
        timestamp.time().replace(microsecond=0),
        get_client_ip(request),
    )
    if new_id is None:
        return templates.TemplateResponse(request, "db_offline.html", {}, status_code=503)

    # Stuur Discord-melding op de achtergrond; blokkeer de response niet.
    task = asyncio.create_task(push_to_discord(new_id, message, timestamp))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return RedirectResponse(url="/", status_code=303)


@app.get("/overview")
async def overview(request: Request):
    """Toont een tabel met alle counts, van nieuwste naar oudste."""
    data = await get_all_counters()
    if data is None:
        return templates.TemplateResponse(request, "db_offline.html", {}, status_code=503)
    return templates.TemplateResponse(request, "overview.html", {"data": data})


@app.get("/robots.txt")
async def robots_txt():
    """Serveert robots.txt vanuit de static/-map op het verwachte root-pad."""
    return FileResponse("static/robots.txt", media_type="text/plain")


@app.get("/healthz")
async def healthz():
    """
    Statuscheck voor de loadbalancer en uptime-monitor.
    Geeft 200 + {"status": "ok"} als de DB bereikbaar is, anders 503.
    """
    rows = await db_query("SELECT 1")
    if rows is not None:
        return JSONResponse({"status": "ok"})
    return JSONResponse({"status": "db_unavailable"}, status_code=503)


# --- JSON API --- Mooindag!

@app.get("/api/counts")
async def api_counts():
    """Geeft alle counts terug als JSON-array, gesorteerd van nieuwste naar oudste."""
    counters = await get_all_counters()
    if counters is None:
        return JSONResponse({"error": "Database unavailable"}, status_code=503)
    return JSONResponse(
        [{"id": c["id"], "message": c["message"], "date": c["date"]} for c in counters]
    )


@app.get("/api/counts/{id}")
async def get_api_count(id: int):
    """Geeft een specifieke count terug als JSON op basis van ID."""
    entry = await get_counter(id)
    if not entry:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(dict(entry))


@app.delete("/api/counts/{id}")
async def delete_api_count(id: int):
    """Verwijdert een count via de API. Geeft 503 terug als de DB niet bereikbaar is."""
    ok = await db_execute("DELETE FROM counts WHERE id = %s", (id,))
    if not ok:
        return JSONResponse({"error": "Database unavailable"}, status_code=503)
    return JSONResponse({"message": f"Record {id} deleted"})
