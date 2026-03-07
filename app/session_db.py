import sqlite3
import time
from pathlib import Path

DB_PATH = Path("session_state.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            last_seen REAL NOT NULL
        )
    """)
    return c

def touch_session(session_id: str):
    now = time.time()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO sessions(session_id, last_seen) VALUES(?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET last_seen=excluded.last_seen",
            (session_id, now),
        )


def get_expired_sessions(ttl_seconds: int) -> list[str]:
    cutoff = time.time() - ttl_seconds
    with _conn() as conn:
        rows = conn.execute(
            "SELECT session_id FROM sessions WHERE last_seen < ?",
            (cutoff,),
        ).fetchall()
    return [r[0] for r in rows]


def remove_session(session_id: str):
    with _conn() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))