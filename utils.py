import mariadb
import os


def connect_db():
    conn = mariadb.connect(
        host="localhost",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return conn

def message_exists(message):
    # Connect to database
    conn = connect_db()
    cursor = conn.cursor()

    # Check if message already exists
    query = "SELECT message FROM counts WHERE message = ? LIMIT 1"
    cursor.execute(query, (message,))

    result = cursor.fetchone()
    
    # Return if message exists
    return result is not None