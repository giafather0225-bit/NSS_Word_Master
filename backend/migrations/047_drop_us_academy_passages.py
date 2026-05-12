"""
Migration 047 — Drop us_academy_passages table
===============================================
This table was designed for the original "US Academy" flow (CLEAR Corpus
reading passages). That concept was replaced by CKLA, which stores its
passage text directly in us_academy_lessons.passage.

Current state:
  - 0 rows
  - No foreign keys pointing to it
  - No references in any router or service (us_academy router deleted in commit 124236d)
  - USAcademyPassage ORM class in models/us_academy.py also removed below

Idempotent: guarded by IF EXISTS.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check if table exists
    cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='us_academy_passages'"
    )
    if cur.fetchone()[0] == 0:
        print("[047] Done — us_academy_passages already dropped.")
        conn.close()
        return

    cur.execute("SELECT COUNT(*) FROM us_academy_passages")
    row_count = cur.fetchone()[0]

    cur.execute("DROP INDEX IF EXISTS ix_us_academy_passages_clear_id")
    cur.execute("DROP TABLE us_academy_passages")

    conn.commit()
    conn.close()
    print(f"[047] Done — us_academy_passages dropped ({row_count} rows, index removed).")


if __name__ == "__main__":
    run()
