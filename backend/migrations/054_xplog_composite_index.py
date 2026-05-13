"""
Migration 054 — Add composite index on xp_logs(action, earned_date)

Problem: award_xp() daily-dedup check queries
    WHERE action = ? AND earned_date = ?
Without an index this scans the full xp_logs table on every XP award.
As the log grows (every lesson, review, streak day, arcade game) this
becomes an increasingly hot full-table scan called multiple times per
study session.

Fix: CREATE INDEX IF NOT EXISTS on (action, earned_date).
     Also covers the _DETAIL_DEDUP variant that adds AND detail = ?
     because SQLite can use the partial key prefix.

Idempotent: IF NOT EXISTS makes re-running safe.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_xplog_action_date "
            "ON xp_logs (action, earned_date)"
        )
        conn.commit()
        print("054: ix_xplog_action_date created (or already existed)")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
