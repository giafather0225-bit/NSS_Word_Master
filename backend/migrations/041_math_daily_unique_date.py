"""
Migration 041 — UNIQUE constraint on math_daily_challenge.challenge_date

Prevents duplicate rows when two concurrent requests both call daily_today
before either has committed. Safe to re-run (IF NOT EXISTS guard).
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def run(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")

        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='math_daily_challenge'"
        ).fetchone()
        if not row:
            logger.warning("Migration 041: math_daily_challenge not found, skipping")
            return

        existing = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_math_daily_challenge_date_unique'"
        ).fetchone()
        if existing:
            logger.info("Migration 041: index already exists, skipping")
            return

        # Deduplicate before adding UNIQUE — keep the row with the highest id
        # (most recent insert) for each challenge_date.
        conn.execute("""
            DELETE FROM math_daily_challenge
            WHERE id NOT IN (
                SELECT MAX(id) FROM math_daily_challenge GROUP BY challenge_date
            )
        """)

        conn.execute(
            "CREATE UNIQUE INDEX idx_math_daily_challenge_date_unique "
            "ON math_daily_challenge (challenge_date)"
        )
        conn.commit()
        logger.info("Migration 041 complete")
    except Exception as exc:
        conn.rollback()
        logger.error("Migration 041 failed: %s", exc)
        raise
    finally:
        conn.close()
