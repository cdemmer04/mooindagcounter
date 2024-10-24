from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime 
import time
import sqlite3

app = Flask(__name__)

# Connect with database
def connect_db():
    return sqlite3.connect('mooindagcounter-sqlite.db')

# Laad de meest recente teller en bericht uit de database
def load_counter():
    conn = connect_db()
    cursor = conn.cursor()

    query = "SELECT id, message FROM counts ORDER BY id DESC LIMIT 1"
    cursor.execute(query)

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        return (0, "Eerste count")
    else:
        return result

# Laad alle tellers en berichten uit de database
def load_all_counters():
    conn = connect_db()
    cursor = conn.cursor()

    query = "SELECT id, message, date FROM counts ORDER BY id DESC"
    cursor.execute(query)

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    counters = []

    for row in result:
        id, message, date_str = row
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()  # String omzetten naar datetime.date object
        counters.append((id, message, date_obj))  # Voeg het omgezette object toe aan de lijst

    return counters

# Sla nieuwe teller en bericht op in de database
def save_counter(counter, message, date):
    conn = connect_db()
    cursor = conn.cursor()

    query = "INSERT INTO counts (id, message, date) VALUES (?, ?, ?)"
    cursor.execute(query, (counter, message, date))
    conn.commit()

    cursor.close()
    conn.close()

@app.route('/')
def index():
    data = load_counter()
    counter = data[0]
    return render_template('index.html', counter=counter)

@app.route('/increment', methods=['POST'])
def increment():
    # date
    date = datetime.now().date()

    # Get current counter and increment
    data = load_counter()
    counter = data[0]
    counter += 1

    # Get message from form
    message = request.form.get("message")

    # Save new record to databse
    save_counter(counter, message, date)
    return redirect(url_for('index'))

# Route om alle counts en berichten te bekijken
@app.route('/overview')
def overview():
    # Get all data
    data = load_all_counters()  

    # Only show overview if it contains data
    if data:
        return render_template('overview.html', data=data)
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
