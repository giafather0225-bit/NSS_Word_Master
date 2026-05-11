"""
Migration 040 — UNIQUE constraints for math tables (idempotent)

Adds:
  - math_fact_fluency(fact_set) UNIQUE
  - math_wrong_review(problem_id) UNIQUE
  - math_spaced_review(grade, lesson_id) UNIQUE
  - math_unit_test(grade, unit) UNIQUE

These prevent duplicate-insert race conditions on concurrent requests
or rapid retries. All operations are IF NOT EXISTS — safe to re-run.
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def run(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")

        _create_unique_index(conn, "idx_math_fact_fluency_fact_set",
                             "math_fact_fluency", "fact_set")
        _create_unique_index(conn, "idx_math_wrong_review_problem_id",
                             "math_wrong_review", "problem_id")
        _create_unique_index(conn, "idx_math_spaced_review_grade_lesson",
                             "math_spaced_review", "grade, lesson_id")
        _create_unique_index(conn, "idx_math_unit_test_grade_unit_id",
                             "math_unit_test", "grade, unit_id")

        conn.commit()
        logger.info("Migration 040 complete")
    except Exception as exc:
        conn.rollback()
        logger.error("Migration 040 failed: %s", exc)
        raise
    finally:
        conn.close()


def _create_unique_index(conn: sqlite3.Connection, index_name: str,
                          table: str, columns: str) -> None:
    """Create UNIQUE index if the table exists and the index does not."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    if not row:
        logger.warning("Migration 040: table %s not found, skipping index", table)
        return

    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    ).fetchone()
    if existing:
        logger.info("Migration 040: index %s already exists, skipping", index_name)
        return

    conn.execute(
        f"CREATE UNIQUE INDEX {index_name} ON {table} ({columns})"
    )
    logger.info("Migration 040: created %s", index_name)
