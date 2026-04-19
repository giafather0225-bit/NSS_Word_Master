"""
migrations/006_academy_session_active.py
Adds last_active_date column to academy_sessions for 2-day auto-reset logic.
Idempotent: safe to re-run.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cols = {row[1] for row in cur.execute("PRAGMA table_info(academy_sessions)").fetchall()}
        if "last_active_date" not in cols:
            cur.execute("ALTER TABLE academy_sessions ADD COLUMN last_active_date TEXT")
            cur.execute(
                "UPDATE academy_sessions SET last_active_date = started_date "
                "WHERE last_active_date IS NULL"
            )
            print("Added academy_sessions.last_active_date (backfilled from started_date)")
        else:
            print("academy_sessions.last_active_date already exists — skip")

        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_academy_sessions_last_active "
            "ON academy_sessions(last_active_date)"
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    run()
