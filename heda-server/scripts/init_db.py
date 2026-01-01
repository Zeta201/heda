from app.db import get_connection

def main():
    conn = get_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS experiments (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        repo_url TEXT NOT NULL,
        workspace_path TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("experiments table created (if it didn't exist)")

if __name__ == "__main__":
    main()
