from app.db import get_connection
from datetime import datetime
import uuid

conn = get_connection()

now = datetime.utcnow().isoformat()

conn.execute(
    """
    INSERT INTO experiments (
        id,
        name,
        status,
        workspace_path,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        str(uuid.uuid4()),
        "My first experiment",
        "created",
        "/tmp/heda/exp1",
        now,
        now,
    )
)

conn.commit()
conn.close()
