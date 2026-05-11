"""
034_math_attempt_misconception.py — math_attempts에 misconception_id 컬럼 추가.

번호 변경 이력: 원래 032로 작성했으나 원격 main의 032(CKLA round2)와 충돌해
                머지 후 034로 재번호. DB 적용은 이미 완료(idempotent 재실행 안전).

진단 엔진(backend/services/math_diagnostic.py)이 오답을 misconception 라이브러리와
조인한 결과를 attempt 레코드에 영구 저장하기 위함. 후속 분석(코칭/대시보드)이
간단해진다.

Idempotent: 컬럼 존재 여부 체크 후 ALTER.
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
