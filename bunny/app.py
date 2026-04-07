from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from datetime import datetime
import time
import pymysql
import pymysql.cursors
import os
import requests
from dotenv import load_dotenv

# Global Variables
app = Flask(__name__)

load_dotenv("./.env")

# Help Functions
def push_to_discord(counter, message, timestamp):
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if discord_webhook_url:
        discord_data = {
            "content": f"Counter: {counter}\n"
               f"Datum: {timestamp.strftime('%d-%m-%Y')}\n"
               f"Tijd: {timestamp.strftime('%H:%M')}\n"
               f"{message.capitalize()}"
        }
        requests.post(discord_webhook_url, json=discord_data)

def save_counter(counter, message, date, time, client_ip):
    conn = connect_db()
    cursor = conn.cursor()

    query = "INSERT INTO counts (id, message, date, time, client_ip) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (counter, message, date, time, client_ip))
    conn.commit()

    cursor.close()
    conn.close()

def get_counter(id):
    conn = connect_db()
    cursor = conn.cursor()

    query = "SELECT * FROM counts WHERE id = %s"
    cursor.execute(query, (id,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result

def get_all_counters():
    conn = connect_db()

    if conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT id, message, date, time FROM counts ORDER BY id DESC"
        cursor.execute(query)

        result = cursor.fetchall()
        cursor.close()
        conn.close()

        return result
    else:
        return None

def get_latest_counter():
    if (conn := connect_db()):
        cursor = conn.cursor()

        query = "SELECT id FROM counts ORDER BY id DESC LIMIT 1"
        cursor.execute(query)

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return 0
        else:
            return result[0]
    else:
        return "Database not connected!"

def connect_db():
    try:
        return pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            autocommit=False,
        )
    except pymysql.Error as e:
        print(f"Fout bij het verbinden met de database: {e}")
        return None

def message_exists(message):
    conn = connect_db()
    cursor = conn.cursor()

    query = "SELECT message FROM counts WHERE message = %s LIMIT 1"
    cursor.execute(query, (message,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result is not None

# Route Functions
@app.route('/overview')
def overview():
    data = get_all_counters()

    if data:
        return render_template('overview.html', data=data)
    else:
        return redirect(url_for('index'))

@app.route('/increment', methods=['POST'])
def increment():
    timestamp = datetime.now()
    date = timestamp.date()
    time = timestamp.time().replace(microsecond=0)

    counter = get_latest_counter()

    message = request.form.get("message").lower()

    if message_exists(message):
        return render_template('index.html', counter=counter, error_message=True)

    counter += 1

    if not (client_ip := request.headers.get('X-Forwarded-For')):
        client_ip = request.remote_addr

    save_counter(counter, message, date, time, client_ip)

    push_to_discord(counter, message, timestamp)

    return redirect(url_for('index'))

@app.route('/remove/<id>', methods=['GET'])
def remove_item(id):
    print(id)
    return redirect(url_for('overview'))

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/')
def index():
    counter = get_latest_counter()
    return render_template('index.html', counter=counter)

@app.route('/index')
def index_redirect():
    return redirect(url_for('index'))

@app.route('/healthz')
def healthz():
    conn = connect_db()
    if conn:
        conn.close()
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "db_unavailable"}), 503

# API Methods
@app.route('/api/counts', methods=['GET'])
def api_counts():
    counters = get_all_counters()

    formatted_counters = [
        {
            "count": counter[0],
            "message": counter[1],
            "date": counter[2]
        }
        for counter in counters
    ]
    return jsonify(formatted_counters)

@app.route('/api/counts/<id>', methods=["GET", "DELETE", "POST"])
def api_remove(id):

    if request.method == 'GET':
        if counter := get_counter(id):
            return jsonify(get_counter(id))
        else:
            return "There are no counters in the database or the database is not connected!"
    else:
        conn = connect_db()
        cursor = conn.cursor()

        query = "DELETE FROM counts WHERE id = %s"
        cursor.execute(query, (id,))

        query = "ALTER TABLE counts AUTO_INCREMENT = 1"
        cursor.execute(query)

        conn.commit()

        cursor.close()
        conn.close()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"message": f"Record {id} deleted"}), 200
        else:
            return redirect(url_for("overview"))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
