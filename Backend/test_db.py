import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'projectdna'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgresql123'),
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432')
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("Extension 'vector' created successfully!")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
