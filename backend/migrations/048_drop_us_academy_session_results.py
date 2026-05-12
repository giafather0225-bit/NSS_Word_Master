"""
Migration 048 — Drop us_academy_sessions and us_academy_unit_results tables
============================================================================
Both tables belonged to the original "US Academy" word-first flow
(level/unit/word-index tracking + mini-quiz / unit-test results).
That flow was never used in production:
  - us_academy_sessions:    0 rows, no router/service references
  - us_academy_unit_results: 0 rows, no router/service references

The router (routers/us_academy.py) was deleted in the same cleanup batch.
The ORM classes (USAcademySession, USAcademyUnitResult) were removed from
models/us_academy.py in the same commit.

Idempotent: guarded by IF EXISTS.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    dropped = []

    for table in ("us_academy_sessions", "us_academy_unit_results"):
        cur.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        if cur.fetchone()[0] == 0:
            print(f"[048] Skip — {table} already dropped.")
            continue

        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cur.fetchone()[0]
        cur.execute(f"DROP TABLE {table}")
        dropped.append((table, row_count))

    conn.commit()
    conn.close()

    if dropped:
        for table, row_count in dropped:
            print(f"[048] Done — {table} dropped ({row_count} rows).")
    else:
        print("[048] Done — both tables already absent.")


if __name__ == "__main__":
    run()
