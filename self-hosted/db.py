import os
from dotenv import load_dotenv
import pymysql
import pymysql.cursors
from datetime import datetime

load_dotenv("./.env")

def connect_db():
    try:
        return pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
        )
    except pymysql.Error as e:
        return f"Fout bij het verbinden met de database: {e}"

def get_all_counters():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = "SELECT id, message, date, time FROM counts ORDER BY id DESC"
    cursor.execute(query)

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return result

if __name__ == "__main__":
    counters = get_all_counters()
    time = datetime.now()
    date = time.date()
    onlytime = time.time().replace(microsecond=0)
    print(date)
    print(onlytime)
