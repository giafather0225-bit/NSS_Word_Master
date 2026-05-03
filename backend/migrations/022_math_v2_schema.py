"""
migrations/022_math_v2_schema.py — MATH_SPEC v2.0 schema additions
Section: Math
Idempotent — safe to run repeatedly.

Changes:
  math_progress      — add exit_quiz_score, exit_quiz_passed, exit_quiz_attempts, completed_at
  math_wrong_review  — add source_stage, attempt_count, consecutive_correct
  math_spaced_review — new table (spaced repetition per lesson)
  math_unit_test     — new table (unit test attempt history)
  math_placement_test— new table (v2.0 placement; separate from legacy math_placement_results)
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def _columns(conn: sqlite3.Connection, table: str) -> set:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 022] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        # ── 1. math_progress: add v2.0 columns ───────────────────────────────
        mp_cols = _columns(conn, "math_progress")
        added = []
        for col, defn in [
            ("exit_quiz_score",    "INTEGER"),
            ("exit_quiz_passed",   "BOOLEAN DEFAULT 0"),
            ("exit_quiz_attempts", "INTEGER DEFAULT 0"),
            ("completed_at",       "TEXT"),
        ]:
            if col not in mp_cols:
                conn.execute(f"ALTER TABLE math_progress ADD COLUMN {col} {defn}")
                added.append(col)
        if added:
            print(f"[migration 022] math_progress: added {added}")
        else:
            print("[migration 022] math_progress: all v2.0 columns already present")

        # ── 2. math_wrong_review: add v2.0 columns ───────────────────────────
        wr_cols = _columns(conn, "math_wrong_review")
        added = []
        for col, defn in [
            ("source_stage",        "TEXT"),
            ("attempt_count",       "INTEGER DEFAULT 0"),
            ("consecutive_correct", "INTEGER DEFAULT 0"),
        ]:
            if col not in wr_cols:
                conn.execute(f"ALTER TABLE math_wrong_review ADD COLUMN {col} {defn}")
                added.append(col)
        if added:
            print(f"[migration 022] math_wrong_review: added {added}")
        else:
            print("[migration 022] math_wrong_review: all v2.0 columns already present")

        # ── 3. math_spaced_review (new) ───────────────────────────────────────
        if not _table_exists(conn, "math_spaced_review"):
            conn.execute("""
                CREATE TABLE math_spaced_review (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id        TEXT    NOT NULL,
                    unit_id          TEXT    NOT NULL,
                    grade            TEXT    NOT NULL DEFAULT 'G3',
                    exit_quiz_score  INTEGER NOT NULL,
                    next_review_date TEXT    NOT NULL,
                    interval_days    INTEGER NOT NULL,
                    interval_index   INTEGER DEFAULT 0,
                    last_reviewed_at TEXT,
                    created_at       TEXT    DEFAULT (datetime('now'))
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_msr_next_review "
                "ON math_spaced_review(next_review_date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_msr_lesson "
                "ON math_spaced_review(lesson_id)"
            )
            print("[migration 022] math_spaced_review: table created")
        else:
            print("[migration 022] math_spaced_review: already exists")

        # ── 4. math_unit_test (new) ───────────────────────────────────────────
        if not _table_exists(conn, "math_unit_test"):
            conn.execute("""
                CREATE TABLE math_unit_test (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id        TEXT    NOT NULL,
                    grade          TEXT    NOT NULL DEFAULT 'G3',
                    attempt_number INTEGER DEFAULT 1,
                    score          INTEGER NOT NULL,
                    total          INTEGER NOT NULL DEFAULT 10,
                    passed         BOOLEAN DEFAULT 0,
                    xp_awarded     INTEGER DEFAULT 0,
                    taken_at       TEXT    DEFAULT (datetime('now'))
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_mut_unit_id "
                "ON math_unit_test(unit_id)"
            )
            print("[migration 022] math_unit_test: table created")
        else:
            print("[migration 022] math_unit_test: already exists")

        # ── 5. math_placement_test (new — v2.0 unit-based; separate from legacy) ──
        if not _table_exists(conn, "math_placement_test"):
            conn.execute("""
                CREATE TABLE math_placement_test (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    grade       TEXT    NOT NULL,
                    score       INTEGER NOT NULL,
                    total       INTEGER NOT NULL DEFAULT 20,
                    unit_scores TEXT    NOT NULL DEFAULT '{}',
                    taken_at    TEXT    DEFAULT (datetime('now'))
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_mpt_grade "
                "ON math_placement_test(grade)"
            )
            print("[migration 022] math_placement_test: table created")
        else:
            print("[migration 022] math_placement_test: already exists")

        conn.commit()
        print("[migration 022] complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
