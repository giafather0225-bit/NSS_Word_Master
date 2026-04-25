"""
migrations/013_diary_entry_columns.py — Add Decorated-diary metadata columns
to diary_entries.

Adds nullable TEXT columns for: title, mode, mood, prompt, style_json,
photos_json. All NULL on existing rows so legacy data keeps loading; the
frontend already falls back gracefully when these are missing.

Idempotent — safe to run repeatedly.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

_NEW_COLUMNS = [
    ("title",        "TEXT"),
    ("mode",         "TEXT"),
    ("mood",         "TEXT"),
    ("prompt",       "TEXT"),
    ("style_json",   "TEXT"),
    ("photos_json",  "TEXT"),
]


def migrate() -> None:
    """Add missing diary_entries columns if they don't already exist."""
    if not DB_PATH.exists():
        print(f"[migration] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(diary_entries)").fetchall()}
        if not existing:
            print("[migration] diary_entries table missing — nothing to do.")
            return

        added = []
        for name, kind in _NEW_COLUMNS:
            if name in existing:
                continue
            conn.execute(f"ALTER TABLE diary_entries ADD COLUMN {name} {kind}")
            added.append(name)

        conn.commit()
        if added:
            print(f"[migration] Added diary_entries columns: {', '.join(added)}")
        else:
            print("[migration] diary_entries already up to date.")
    finally:
        conn.close()
    print("[migration] 013_diary_entry_columns complete.")


if __name__ == "__main__":
    migrate()
