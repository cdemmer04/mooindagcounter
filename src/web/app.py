from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from datetime import datetime
import os
import threading
import requests
from dotenv import load_dotenv
import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB

app = Flask(__name__)
load_dotenv("./.env")


# --- Connection pool ---
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = PooledDB(
            creator=pymysql,
            maxconnections=10,
            mincached=2,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "mooindagcounter"),
            cursorclass=DictCursor,
            autocommit=True,
        )
    return _pool


def get_connection():
    return get_pool().connection()


# --- Database helpers ---

def db_query(sql, params=()):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    except Exception as e:
        app.logger.error("DB query error: %s", e)
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def db_execute(sql, params=()):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
        return True
    except Exception as e:
        app.logger.error("DB execute error: %s", e)
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


# --- App logic ---

def push_to_discord(counter, message, timestamp):
    """Send Discord notification in a background thread so it never blocks the request."""
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return

    def _send():
        try:
            requests.post(
                url,
                json={
                    "content": (
                        f"Counter: {counter}\n"
                        f"Datum: {timestamp.strftime('%d-%m-%Y')}\n"
                        f"Tijd: {timestamp.strftime('%H:%M')}\n"
                        f"{message.capitalize()}"
                    )
                },
                timeout=5,
            )
        except requests.RequestException as e:
            app.logger.warning("Discord webhook failed: %s", e)

    threading.Thread(target=_send, daemon=True).start()


def save_counter(counter, message, date, time, client_ip):
    db_execute(
        "INSERT INTO counts (id, message, date, time, client_ip) VALUES (%s, %s, %s, %s, %s)",
        (counter, message, str(date), str(time), client_ip),
    )


def get_counter(entry_id):
    rows = db_query("SELECT * FROM counts WHERE id = %s", (int(entry_id),))
    return rows[0] if rows else None


def get_all_counters():
    return db_query("SELECT id, message, date, time FROM counts ORDER BY id DESC")


def get_latest_counter():
    rows = db_query("SELECT id FROM counts ORDER BY id DESC LIMIT 1")
    if rows is None:
        return None
    return rows[0]["id"] if rows else 0


def message_exists(message):
    rows = db_query("SELECT message FROM counts WHERE message = %s LIMIT 1", (message,))
    return bool(rows)


# --- Routes ---

@app.route("/overview")
def overview():
    data = get_all_counters()
    if data:
        return render_template("overview.html", data=data)
    return redirect(url_for("index"))


@app.route("/increment", methods=["POST"])
def increment():
    timestamp = datetime.now()
    date = timestamp.date()
    time = timestamp.time().replace(microsecond=0)
    counter = get_latest_counter()
    if counter is None:
        return render_template("db_offline.html")
    message = request.form.get("message", "").strip().lower()
    if not message:
        return render_template("index.html", counter=counter, error_message=True)

    if message_exists(message):
        return render_template("index.html", counter=counter, error_message=True)

    counter += 1
    client_ip = request.headers.get("X-Forwarded-For") or request.remote_addr
    save_counter(counter, message, date, time, client_ip)
    push_to_discord(counter, message, timestamp)

    return redirect(url_for("index"))


@app.route("/remove/<int:id>", methods=["POST"])
def remove_item(id):
    """Delete a count entry. Requires a POST to prevent accidental deletion via GET."""
    db_execute("DELETE FROM counts WHERE id = %s", (id,))
    return redirect(url_for("overview"))


@app.route("/robots.txt")
def robots_txt():
    return send_from_directory("static", "robots.txt", mimetype="text/plain")


@app.route("/")
def index():
    counter = get_latest_counter()
    if counter is None:
        return render_template("db_offline.html")
    return render_template("index.html", counter=counter)


@app.route("/index")
def index_redirect():
    return redirect(url_for("index"))


@app.route("/healthz")
def healthz():
    rows = db_query("SELECT 1")
    if rows is not None:
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "db_unavailable"}), 503


@app.route("/api/counts", methods=["GET"])
def api_counts():
    counters = get_all_counters() or []
    return jsonify(
        [{"count": c["id"], "message": c["message"], "date": c["date"]} for c in counters]
    )


@app.route("/api/counts/<int:id>", methods=["GET", "DELETE", "POST"])
def api_remove(id):
    if request.method == "GET":
        counter = get_counter(id)
        return jsonify(counter) if counter else (jsonify({"error": "Not found"}), 404)

    db_execute("DELETE FROM counts WHERE id = %s", (id,))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"message": f"Record {id} deleted"}), 200
    return redirect(url_for("overview"))


if __name__ == "__main__":
    # debug=False — production uses Gunicorn via entrypoint.sh
    app.run(debug=False, host="0.0.0.0", port=8080)
