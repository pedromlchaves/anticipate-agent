import sqlite3
import json
import threading
import time
from typing import Optional, Any
import os

_DB_PATH = "/tmp/agent_data.sqlite3"
_DB_LOCK = threading.Lock()

# Ensure the directory exists
os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)

# Ensure the table exists
with _DB_LOCK:
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            timestamp REAL
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS session_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            timestamp REAL,
            UNIQUE(user_id, session_id, key)
        )
    """
    )
    conn.commit()
    conn.close()


def save_agent_data(key: str, value: Any) -> bool:
    """
    Save a value (as JSON) under a key. Overwrites if key exists.
    """
    with _DB_LOCK:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        value_json = json.dumps(value)
        ts = time.time()
        c.execute(
            """
            INSERT INTO agent_data (key, value, timestamp) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, timestamp=excluded.timestamp
        """,
            (key, value_json, ts),
        )
        conn.commit()
        conn.close()
    return True


def load_agent_data(key: str) -> Optional[Any]:
    """
    Load a value by key. Returns None if not found.
    """
    with _DB_LOCK:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM agent_data WHERE key=?", (key,))
        row = c.fetchone()
        conn.close()
    if row:
        return json.loads(row[0])
    return None


def save_session_data(user_id: str, session_id: str, key: str, value: Any) -> bool:
    """
    Save a value (as JSON) under a key for a user/session. Overwrites if exists.
    """
    with _DB_LOCK:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        value_json = json.dumps(value)
        ts = time.time()
        c.execute(
            """
            INSERT INTO session_data (user_id, session_id, key, value, timestamp)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, session_id, key) DO UPDATE SET value=excluded.value, timestamp=excluded.timestamp
        """,
            (user_id, session_id, key, value_json, ts),
        )
        conn.commit()
        conn.close()
    return True


def load_session_data(user_id: str, session_id: str, key: str) -> Optional[Any]:
    """
    Load a value by user/session/key. Returns None if not found.
    """
    with _DB_LOCK:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT value FROM session_data WHERE user_id=? AND session_id=? AND key=?",
            (user_id, session_id, key),
        )
        row = c.fetchone()
        conn.close()
    if row:
        return json.loads(row[0])
    return None
