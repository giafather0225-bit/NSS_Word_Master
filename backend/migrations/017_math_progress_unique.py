"""
migrations/017_math_progress_unique.py — Add UNIQUE(grade, unit, lesson) on math_progress
Section: Math
Idempotent — safe to run repeatedly.

Why: MathProgress lookups in routers/math_academy.py rely on .first() with
filter_by(grade, unit, lesson). Without a unique constraint, concurrent first-time
inserts (race between two requests for the same lesson) can create duplicate rows
and silent state divergence (one row updated, the other left stale). The migration
de-duplicates existing rows (keeping the row with highest id — most recent state)
before adding the unique index.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 017] DB not found at {DB_PATH}; skipping.")
        return
    conn = sqlite3.connect(str(DB_PATH))
    try:
        # Already-applied check: skip if the unique index exists.
        idx_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='math_progress'"
        ).fetchall()
        idx_names = {r[0] for r in idx_rows}
        if "ux_math_progress_grade_unit_lesson" in idx_names:
            print("[migration 017] Unique index already present — skipping.")
            return

        # De-dupe: keep the row with MAX(id) per (grade, unit, lesson).
        dupes = conn.execute("""
            SELECT grade, unit, lesson, COUNT(*) AS n
            FROM math_progress
            GROUP BY grade, unit, lesson
            HAVING n > 1
        """).fetchall()
        removed = 0
        for grade, unit, lesson, _n in dupes:
            keep_row = conn.execute(
                "SELECT MAX(id) FROM math_progress WHERE grade=? AND unit=? AND lesson=?",
                (grade, unit, lesson),
            ).fetchone()
            keep_id = keep_row[0] if keep_row else None
            if keep_id is None:
                continue
            cur = conn.execute(
                "DELETE FROM math_progress WHERE grade=? AND unit=? AND lesson=? AND id<>?",
                (grade, unit, lesson, keep_id),
            )
            removed += cur.rowcount

        if removed:
            print(f"[migration 017] Removed {removed} duplicate math_progress rows.")

        # Add the unique index. (SQLite has no ALTER TABLE ADD CONSTRAINT for UNIQUE,
        # but a UNIQUE INDEX is functionally identical.)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_math_progress_grade_unit_lesson "
            "ON math_progress(grade, unit, lesson)"
        )
        conn.commit()
        print("[migration 017] Added UNIQUE(grade, unit, lesson) on math_progress.")
    finally:
        conn.close()
    print("[migration 017] complete.")


if __name__ == "__main__":
    migrate()
