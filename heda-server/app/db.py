import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        cursor_factory=RealDictCursor,
    )

def init_db(retries: int = 10, delay: float = 1.0):
    for attempt in range(retries):
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    repo_url TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            """)

            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully")
            return

        except OperationalError as e:
            print(f"Database not ready (attempt {attempt + 1}/{retries}), retrying...")
            time.sleep(delay)

    raise RuntimeError("Could not connect to Postgres after multiple retries")
