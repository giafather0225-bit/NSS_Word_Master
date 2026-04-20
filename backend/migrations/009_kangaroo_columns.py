"""
migrations/009_kangaroo_columns.py — Math Kangaroo progress extension
Section: Math
Dependencies: database.py
API: none (run directly)

Adds level, max_score, time_spent_seconds, answers_json to
math_kangaroo_progress. Idempotent. Does NOT drop data.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


# @tag MATH @tag SYSTEM
def migrate() -> None:
    """Add missing Kangaroo progress columns if absent."""
    if not DB_PATH.exists():
        print(f"[migration 009] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cols = {row[1] for row in conn.execute(
        "PRAGMA table_info(math_kangaroo_progress)"
    ).fetchall()}

    added = []
    if "level" not in cols:
        conn.execute("ALTER TABLE math_kangaroo_progress ADD COLUMN level TEXT DEFAULT ''")
        added.append("level")
    if "max_score" not in cols:
        conn.execute("ALTER TABLE math_kangaroo_progress ADD COLUMN max_score INTEGER DEFAULT 0")
        added.append("max_score")
    if "time_spent_seconds" not in cols:
        conn.execute("ALTER TABLE math_kangaroo_progress ADD COLUMN time_spent_seconds INTEGER")
        added.append("time_spent_seconds")
    if "answers_json" not in cols:
        conn.execute("ALTER TABLE math_kangaroo_progress ADD COLUMN answers_json TEXT")
        added.append("answers_json")

    conn.commit()
    conn.close()
    if added:
        print(f"[migration 009] Added columns: {', '.join(added)}")
    else:
        print("[migration 009] No changes needed.")


if __name__ == "__main__":
    migrate()
