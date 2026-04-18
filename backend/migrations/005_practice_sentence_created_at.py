"""
migrations/005_practice_sentence_created_at.py — Track sentence creation time.

Adds `created_at` (TEXT, ISO 8601 UTC) to `user_practice_sentences` so the
diary "My Sentences" view can prompt the student to rewrite sentences that
are 2+ weeks old (per Phase 6 spec).

Existing rows are backfilled with NULL. The frontend treats missing
timestamps as "unknown age" and does not show the Rewrite badge for them.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    existing = {row[1] for row in conn.execute("PRAGMA table_info(user_practice_sentences)").fetchall()}

    if "created_at" not in existing:
        conn.execute("ALTER TABLE user_practice_sentences ADD COLUMN created_at TEXT")
        print("[migration] Added user_practice_sentences.created_at")
    else:
        print("[migration] user_practice_sentences.created_at already exists; skipping.")

    conn.commit()
    conn.close()
    print("[migration] 005_practice_sentence_created_at complete.")


if __name__ == "__main__":
    migrate()
