"""
033_math_progress_mastery.py — add Mastery Gating columns to math_progress.

Background
- 35 problems/lesson exceeds the G3 (age 8-9) attention limit (20-30 min)
  (vs. Singapore 6-12, Eureka 15-25).
- A perfect pre-test auto-exempts R2, addressing the drill-and-kill critique.
  R3 is transfer learning, so it is always kept.

Added columns
- pretest_mastery   BOOLEAN: True on a 100% pre-test (qualifies to skip R2)
- skipped_stages    TEXT   : JSON list of skipped stage names

Idempotent.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def column_exists(cur, table: str, col: str) -> bool:
    return any(r[1] == col for r in cur.execute(f"PRAGMA table_info({table})").fetchall())


def main():
    if not DB_PATH.exists():
        print(f"[skip] DB not found: {DB_PATH}")
        return
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    added = 0
    for col, ddl in [
        ("pretest_mastery", "BOOLEAN DEFAULT 0"),
        ("skipped_stages", "TEXT"),
    ]:
        if not column_exists(cur, "math_progress", col):
            cur.execute(f"ALTER TABLE math_progress ADD COLUMN {col} {ddl}")
            added += 1
            print(f"  + math_progress.{col}")
    con.commit()
    con.close()
    print(f"✅ migration 033: {added} column(s) added")


if __name__ == "__main__":
    main()
