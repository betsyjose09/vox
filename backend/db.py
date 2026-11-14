import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from backend.config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.database_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    conn = sqlite3.connect(str(settings.database_path), timeout=30.0)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        account_id TEXT,
        role TEXT NOT NULL DEFAULT 'public',
        display_name TEXT NOT NULL DEFAULT 'Guest',
        kit_token TEXT,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        revoked_at TEXT
    );

    CREATE TABLE IF NOT EXISTS conversation_turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        account_id TEXT,
        user_text TEXT NOT NULL,
        assistant_text TEXT NOT NULL,
        intent TEXT,
        module TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE TABLE IF NOT EXISTS conversation_state (
        session_id TEXT PRIMARY KEY,
        state_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE TABLE IF NOT EXISTS pending_actions (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        intent TEXT NOT NULL,
        slots_json TEXT NOT NULL,
        summary TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        status TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        result_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        account_id TEXT,
        event_type TEXT NOT NULL,
        tool_name TEXT,
        outcome TEXT NOT NULL,
        metadata_json TEXT,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_turns_session ON conversation_turns(session_id);
    CREATE INDEX IF NOT EXISTS idx_turns_account ON conversation_turns(account_id);
    CREATE INDEX IF NOT EXISTS idx_pending_session ON pending_actions(session_id);
    CREATE INDEX IF NOT EXISTS idx_pending_account ON pending_actions(account_id);
    """)
    conn.close()

# Auto-initialize DB on module import
init_db()
