import sqlite3
from datetime import datetime
import pytz
import time

def connect_db():
    return sqlite3.connect('mooindagcounter-sqlite.db')

def load_counter():
    conn = connect_db()
    cursor = conn.cursor()

    query = "select id, message from counts order by id desc limit 1"
    cursor.execute(query)

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result


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

data = load_all_counters()
data = data[0]
print(type(data[2]))
    