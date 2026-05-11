"""
033_math_progress_mastery.py — math_progress에 Mastery Gating 컬럼 추가.

배경
- 35문항/차시는 G3 8-9세 집중 한계(20~30분) 초과 (Singapore 6-12, Eureka 15-25 대비).
- PT 만점 시 R2를 자동 면제해 drill-and-kill 비판 해소. R3는 전이 학습이라 항상 유지.

추가 컬럼
- pretest_mastery   BOOLEAN: PT 100% 시 True (R2 skip 자격)
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
