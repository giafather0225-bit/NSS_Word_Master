"""
066_add_missing_query_indexes.py — Add indexes for parent-dashboard and report queries.

Without these indexes the following hot paths do full table scans:

  word_attempts (attempted_at, is_correct)
    - parent_stats.py  GET /api/parent/overview  (Top Weaknesses query)
    - goals.py         GET /api/goals/weekly     (word accuracy calculation)
    - report_engine.py weekly email report        (last-7d word stats)

  math_attempts (attempted_at, is_correct)
    - report_engine.py weekly email report        (last-7d math stats)
    - parent_math.py   GET /api/parent/math-summary

  island_character_progress (is_active)
    - island_care_engine.py  run_daily_batch()   (app-startup decay loop)

The composite index on word_attempts covers both single-column lookups
(WHERE is_correct = ?) and range-plus-filter queries
(WHERE attempted_at >= ? AND is_correct = ?).
"""

_INDEXES = [
    # word_attempts ──────────────────────────────────────────────────────────
    # Composite covers (attempted_at) alone and (attempted_at, is_correct).
    (
        "word_attempts",
        "ix_word_attempts_attempted_correct",
        "CREATE INDEX IF NOT EXISTS ix_word_attempts_attempted_correct "
        "ON word_attempts (attempted_at, is_correct)",
    ),
    # is_correct-only lookups (Top Weaknesses sorts by accuracy ASC).
    (
        "word_attempts",
        "ix_word_attempts_is_correct",
        "CREATE INDEX IF NOT EXISTS ix_word_attempts_is_correct "
        "ON word_attempts (is_correct)",
    ),
    # math_attempts ──────────────────────────────────────────────────────────
    (
        "math_attempts",
        "ix_math_attempts_attempted_at",
        "CREATE INDEX IF NOT EXISTS ix_math_attempts_attempted_at "
        "ON math_attempts (attempted_at)",
    ),
    (
        "math_attempts",
        "ix_math_attempts_is_correct",
        "CREATE INDEX IF NOT EXISTS ix_math_attempts_is_correct "
        "ON math_attempts (is_correct)",
    ),
    # island_character_progress ──────────────────────────────────────────────
    (
        "island_character_progress",
        "ix_island_char_progress_is_active",
        "CREATE INDEX IF NOT EXISTS ix_island_char_progress_is_active "
        "ON island_character_progress (is_active)",
    ),
]


def run(conn):
    """Execute all CREATE INDEX IF NOT EXISTS statements idempotently."""
    existing_tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    for table, _name, sql in _INDEXES:
        if table in existing_tables:
            conn.execute(sql)
