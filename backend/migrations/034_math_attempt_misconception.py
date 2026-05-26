"""
034_math_attempt_misconception.py — add a misconception_id column to math_attempts.

Renumbering history: originally written as 032, but it collided with remote
                     main's 032 (CKLA round2), so it was renumbered to 034
                     after merging. The DB change is already applied
                     (idempotent — safe to re-run).

Purpose: the diagnostic engine (backend/services/math_diagnostic.py) joins a
wrong answer against the misconception library and permanently stores the
result on the attempt record. This simplifies downstream analysis
(coaching/dashboard).

Idempotent: checks whether the column exists before ALTER.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def column_exists(cur, table: str, col: str) -> bool:
    rows = cur.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == col for r in rows)


def main():
    if not DB_PATH.exists():
        print(f"[skip] DB not found: {DB_PATH}")
        return
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    added = 0
    for col, ddl in [
        ("misconception_id", "TEXT"),
        ("diagnostic_note", "TEXT"),
    ]:
        if not column_exists(cur, "math_attempts", col):
            cur.execute(f"ALTER TABLE math_attempts ADD COLUMN {col} {ddl}")
            added += 1
            print(f"  + math_attempts.{col} ({ddl})")
    con.commit()
    con.close()
    print(f"✅ migration 034: {added} column(s) added")


if __name__ == "__main__":
    main()
