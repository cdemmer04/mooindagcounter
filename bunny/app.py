from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv("./.env")


# --- LibSQL (HTTP) Database helpers ---
def _db_url():
    url = os.getenv("BUNNY_DATABASE_URL", "").rstrip("/")
    return url.replace("libsql://", "https://") + "/v2/pipeline"


def _token():
    return os.getenv("BUNNY_DATABASE_AUTH_TOKEN")


def _cell(cell):
    t = cell.get("type")
    if t == "null":
        return None
    if t == "integer":
        return int(cell["value"])
    if t == "float":
        return float(cell["value"])
    return cell.get("value")


def _arg(p):
    if isinstance(p, int):
        return {"type": "integer", "value": str(p)}
    return {"type": "text", "value": str(p)}


def db_query(sql, params=()):
    stmt = {"sql": sql, "args": [_arg(p) for p in params]}
    try:
        r = requests.post(
            _db_url(),
            json={"requests": [{"type": "execute", "stmt": stmt}, {"type": "close"}]},
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()["results"][0]["response"]["result"]
        cols = [c["name"] for c in result["cols"]]
        return [dict(zip(cols, [_cell(cell) for cell in row])) for row in result["rows"]]
    except Exception as e:
        print(f"DB query error: {e}")
        return None


def db_execute(sql, params=()):
    stmt = {"sql": sql, "args": [_arg(p) for p in params]}
    try:
        r = requests.post(
            _db_url(),
            json={"requests": [{"type": "execute", "stmt": stmt}, {"type": "close"}]},
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=10,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"DB execute error: {e}")
        return False


# --- App logic ---

def push_to_discord(counter, message, timestamp):
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_webhook_url:
        requests.post(discord_webhook_url, json={
            "content": f"Counter: {counter}\n"
                       f"Datum: {timestamp.strftime('%d-%m-%Y')}\n"
                       f"Tijd: {timestamp.strftime('%H:%M')}\n"
                       f"{message.capitalize()}"
        })

def save_counter(counter, message, date, time, client_ip):
    db_execute(
        "INSERT INTO counts (id, message, date, time, client_ip) VALUES (?, ?, ?, ?, ?)",
        (counter, message, str(date), str(time), client_ip)
    )

def get_counter(id):
    rows = db_query("SELECT * FROM counts WHERE id = ?", (int(id),))
    return rows[0] if rows else None

def get_all_counters():
    return db_query("SELECT id, message, date, time FROM counts ORDER BY id DESC")

def get_latest_counter():
    rows = db_query("SELECT id FROM counts ORDER BY id DESC LIMIT 1")
    if rows is None:
        return None
    return rows[0]["id"] if rows else 0

def message_exists(message):
    rows = db_query("SELECT message FROM counts WHERE message = ? LIMIT 1", (message,))
    return bool(rows)


# --- Routes ---

@app.route('/overview')
def overview():
    data = get_all_counters()
    if data:
        return render_template('overview.html', data=data)
    return redirect(url_for('index'))

@app.route('/increment', methods=['POST'])
def increment():
    timestamp = datetime.now()
    date = timestamp.date()
    time = timestamp.time().replace(microsecond=0)
    counter = get_latest_counter()
    if counter is None:
        return render_template('db_offline.html')
    message = request.form.get("message").lower()

    if message_exists(message):
        return render_template('index.html', counter=counter, error_message=True)

    counter += 1
    client_ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    save_counter(counter, message, date, time, client_ip)
    push_to_discord(counter, message, timestamp)

    return redirect(url_for('index'))

@app.route('/remove/<id>', methods=['GET'])
def remove_item(id):
    return redirect(url_for('overview'))

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/')
def index():
    counter = get_latest_counter()
    if counter is None:
        return render_template('db_offline.html')
    return render_template('index.html', counter=counter)

@app.route('/index')
def index_redirect():
    return redirect(url_for('index'))

@app.route('/healthz')
def healthz():
    rows = db_query("SELECT 1")
    if rows is not None:
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "db_unavailable"}), 503

@app.route('/api/counts', methods=['GET'])
def api_counts():
    counters = get_all_counters() or []
    return jsonify([{"count": c["id"], "message": c["message"], "date": c["date"]} for c in counters])

@app.route('/api/counts/<id>', methods=["GET", "DELETE", "POST"])
def api_remove(id):
    if request.method == 'GET':
        counter = get_counter(id)
        return jsonify(counter) if counter else ("Not found", 404)

    db_execute("DELETE FROM counts WHERE id = ?", (int(id),))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"message": f"Record {id} deleted"}), 200
    return redirect(url_for("overview"))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
