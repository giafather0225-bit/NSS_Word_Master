"""
migrations/002_fix_learning_log_columns.py
Phase 7 hotfix: add `subject` column to learning_logs and word_attempts,
and rename learning_logs.wrong_words → wrong_words_json so the schema
matches backend/models.py.

Idempotent — safe to run multiple times.

Usage:
    python3 migrations/002_fix_learning_log_columns.py
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def _columns(cur, table: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def main() -> int:
    if not DB_PATH.exists():
        print(f"❌ DB not found at {DB_PATH}")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    changed = []

    # ── learning_logs ──────────────────────────────────────────
    if "learning_logs" in {r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}:
        cols = _columns(cur, "learning_logs")
        if "subject" not in cols:
            cur.execute(
                "ALTER TABLE learning_logs ADD COLUMN subject TEXT DEFAULT 'English'"
            )
            changed.append("learning_logs.subject added")
        if "wrong_words" in cols and "wrong_words_json" not in cols:
            try:
                cur.execute(
                    "ALTER TABLE learning_logs RENAME COLUMN wrong_words TO wrong_words_json"
                )
                changed.append("learning_logs.wrong_words → wrong_words_json")
            except sqlite3.OperationalError as e:
                conn.rollback()
                print(f"❌ RENAME COLUMN failed (requires SQLite ≥ 3.25): {e}")
                conn.close()
                return 2

    # ── word_attempts ──────────────────────────────────────────
    if "word_attempts" in {r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}:
        cols = _columns(cur, "word_attempts")
        if "subject" not in cols:
            cur.execute(
                "ALTER TABLE word_attempts ADD COLUMN subject TEXT DEFAULT 'English'"
            )
            changed.append("word_attempts.subject added")

    conn.commit()
    conn.close()

    if changed:
        print("✅ Migration 002 applied:")
        for c in changed:
            print(f"  • {c}")
    else:
        print("✅ Migration 002: no changes needed (already up to date)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
