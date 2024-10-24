import mysql.connector
from datetime import datetime
import pytz
import time

def connect_db():
    conn = mysql.connector.connect(
            host="localhost",
            user="mooindagcounter",
            password="7J3JcTG3v[G2T4]]",
            database="mooindagcounter"
        )
    return conn

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

    return result

data = load_all_counters()
for item in data:
    print(item[0])
    
