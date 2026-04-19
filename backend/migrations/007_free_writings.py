"""
migrations/007_free_writings.py — Add FreeWriting table.

Creates the `free_writings` table backing the diary "Free Writing" section
(open-ended creative entries, no date constraint, optional AI feedback).
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='free_writings'"
    ).fetchone()

    if not exists:
        conn.execute("""
            CREATE TABLE free_writings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT,
                content     TEXT,
                ai_feedback TEXT,
                created_at  TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_free_writings_created_at ON free_writings(created_at)")
        print("[migration] Created free_writings table + index.")
    else:
        print("[migration] free_writings table already exists; skipping.")

    conn.commit()
    conn.close()
    print("[migration] 007_free_writings complete.")


if __name__ == "__main__":
    migrate()
