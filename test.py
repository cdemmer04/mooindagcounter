import os
import mariadb

def get_all_counters():
    # Only run query and return results if the connection is successfull
    if conn := connect_db():
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, message, date, time FROM counts ORDER BY id DESC"
        cursor.execute(query)

        result = cursor.fetchall()
        cursor.close()
        conn.close()

        return result
    else:
        # If the initial connection with the DB is unsuccessfull, return nothing
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
        return mariadb.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
        
        )
    except mariadb.Error as e:
        # Log database error
        print(f"Fout bij het verbinden met de database: {e}")
        return None


test = [
    {
        "name": "chiel",
        "age": 21
    }, {
        "name": "twan",
        "age": 21
    }
]
print(type(test[0]['name']))