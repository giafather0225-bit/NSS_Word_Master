"""DB 마이그레이션 스크립트 — lessons 테이블 추가 및 study_items 컬럼 확장.

실행: python -m backend.migrate_db
"""
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from backend.database import DB_PATH


def column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def run_migration() -> None:
    print(f"[migrate] DB path: {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # ── 1. lessons 테이블 생성 ──────────────────────────────────────────────
    if not table_exists(cur, "lessons"):
        print("[migrate] Creating table: lessons")
        cur.execute("""
            CREATE TABLE lessons (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject     TEXT    NOT NULL,
                textbook    TEXT    NOT NULL DEFAULT '',
                lesson_name TEXT    NOT NULL,
                source_type TEXT    NOT NULL DEFAULT 'ocr',
                description TEXT             DEFAULT '',
                created_at  TEXT    NOT NULL
            )
        """)
        cur.execute("CREATE INDEX ix_lessons_id          ON lessons (id)")
        cur.execute("CREATE INDEX ix_lessons_subject     ON lessons (subject)")
        cur.execute("CREATE INDEX ix_lessons_textbook    ON lessons (textbook)")
        cur.execute("CREATE INDEX ix_lessons_lesson_name ON lessons (lesson_name)")
        con.commit()
        print("[migrate] Table 'lessons' created.")
    else:
        print("[migrate] Table 'lessons' already exists — skipped.")

    # ── 2. study_items 에 lesson_id 컬럼 추가 ──────────────────────────────
    if not column_exists(cur, "study_items", "lesson_id"):
        print("[migrate] Adding column: study_items.lesson_id")
        cur.execute("ALTER TABLE study_items ADD COLUMN lesson_id INTEGER REFERENCES lessons(id)")
        cur.execute("CREATE INDEX ix_study_items_lesson_id ON study_items (lesson_id)")
        con.commit()
        print("[migrate] Column 'lesson_id' added.")
    else:
        print("[migrate] Column 'study_items.lesson_id' already exists — skipped.")

    # ── 3. study_items 에 source_type 컬럼 추가 ────────────────────────────
    if not column_exists(cur, "study_items", "source_type"):
        print("[migrate] Adding column: study_items.source_type")
        cur.execute("ALTER TABLE study_items ADD COLUMN source_type TEXT DEFAULT 'ocr'")
        con.commit()
        print("[migrate] Column 'source_type' added.")
    else:
        print("[migrate] Column 'study_items.source_type' already exists — skipped.")

    # ── 4. 기존 study_items → lessons 데이터 이전 ──────────────────────────
    # (subject, textbook, lesson) 조합마다 Lesson 레코드 하나씩 생성
    cur.execute("""
        SELECT DISTINCT subject, textbook, lesson
        FROM study_items
        WHERE lesson_id IS NULL
    """)
    groups = cur.fetchall()

    if groups:
        print(f"[migrate] Migrating {len(groups)} lesson group(s) into 'lessons' table...")
        now = datetime.now(timezone.utc).isoformat()
        for subject, textbook, lesson_name in groups:
            # 이미 lessons 에 동일 항목이 있으면 재사용
            cur.execute(
                "SELECT id FROM lessons WHERE subject=? AND textbook=? AND lesson_name=?",
                (subject, textbook, lesson_name),
            )
            row = cur.fetchone()
            if row:
                lesson_id = row[0]
            else:
                cur.execute(
                    "INSERT INTO lessons (subject, textbook, lesson_name, source_type, description, created_at)"
                    " VALUES (?, ?, ?, 'ocr', '', ?)",
                    (subject, textbook, lesson_name, now),
                )
                lesson_id = cur.lastrowid

            # study_items.lesson_id 업데이트
            cur.execute(
                "UPDATE study_items SET lesson_id=?, source_type='ocr'"
                " WHERE subject=? AND textbook=? AND lesson=? AND lesson_id IS NULL",
                (lesson_id, subject, textbook, lesson_name),
            )
        con.commit()
        print("[migrate] Lesson data migration complete.")
    else:
        print("[migrate] No unlinked study_items found — data migration skipped.")

    con.close()
    print("[migrate] Done.")


if __name__ == "__main__":
    run_migration()
