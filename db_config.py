import os
import mysql.connector

def get_db_connection():
    # Railway provides these variables automatically.
    # On your laptop, it falls back to "localhost", "root", etc.
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "anshitdassdA2"), # <--- PUT YOUR LOCAL PASSWORD HERE
        port=int(os.environ.get("DB_PORT", 3307)),
        database=os.environ.get("DB_NAME", "tida")
    )