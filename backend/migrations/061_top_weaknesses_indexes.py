"""
Migration 061 — Composite/range indexes for parent Top Weaknesses queries

Problem: /api/parent/weaknesses (parent_stats.parent_weaknesses) runs three
GROUP BY aggregations that each scan their full attempt tables on every
parent-home load:
  - word_attempts:                 GROUP BY (word, lesson)
  - math_attempts:                 GROUP BY (lesson)
  - us_academy_question_responses: JOIN on question_id, GROUP BY lesson_id

Activity/time-window queries elsewhere in parent_stats also filter on
attempted_at / created_at >= start_date with no supporting index.

Fix: Add composite + range indexes covering these access patterns. All
CREATE INDEX IF NOT EXISTS, so re-running is safe.

Notes:
  - xp_logs (action, earned_date) was already covered by migration 054.
  - WordAttempt.word and MathAttempt.problem_id already have single-column
    indexes — the composites here extend them for GROUP BY use.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_word_attempts_word_lesson ON word_attempts (word, lesson)",
    "CREATE INDEX IF NOT EXISTS ix_word_attempts_attempted_at ON word_attempts (attempted_at)",
    "CREATE INDEX IF NOT EXISTS ix_math_attempts_lesson ON math_attempts (lesson)",
    "CREATE INDEX IF NOT EXISTS ix_math_attempts_attempted_at ON math_attempts (attempted_at)",
    "CREATE INDEX IF NOT EXISTS ix_ckla_response_question_score ON us_academy_question_responses (question_id, ai_score)",
    "CREATE INDEX IF NOT EXISTS ix_ckla_response_created_at ON us_academy_question_responses (created_at)",
]


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for sql in _INDEXES:
            conn.execute(sql)
        conn.commit()
        print(f"061: {len(_INDEXES)} indexes created (or already existed)")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
