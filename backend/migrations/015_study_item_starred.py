"""
migrations/015_study_item_starred.py — Add is_starred column to study_items
Section: English
Idempotent — safe to run repeatedly.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 015] DB not found at {DB_PATH}; skipping.")
        return
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(study_items)").fetchall()}
        if "is_starred" not in cols:
            conn.execute("ALTER TABLE study_items ADD COLUMN is_starred INTEGER NOT NULL DEFAULT 0")
            conn.commit()
            print("[migration 015] Added study_items.is_starred")
        else:
            print("[migration 015] is_starred already exists — skipping.")
    finally:
        conn.close()
    print("[migration 015] complete.")


if __name__ == "__main__":
    migrate()
