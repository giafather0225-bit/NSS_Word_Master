"""
065_missing_table_indexes.py — Add the one missing index on island_lumi_log.

island_lumi_log had zero indexes. It is queried repeatedly by
(source, earned_date) for daily-attendance dedup checks in routers/island.py
(e.g. source == "daily_attendance" AND earned_date == today). A composite
index on (source, earned_date) covers those lookups directly.

Note: CKLA question responses (table us_academy_question_responses) are
already covered by migration 061 (ix_ckla_response_question_score,
ix_ckla_response_created_at), so no CKLA index is added here.
"""

_INDEXES = [
    ("island_lumi_log", "ix_island_lumi_log_source_date",
     "CREATE INDEX IF NOT EXISTS ix_island_lumi_log_source_date ON island_lumi_log (source, earned_date)"),
]


def run(conn):
    # Guard against fresh/test DBs where the table may not exist yet.
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for table, _name, sql in _INDEXES:
        if table in existing:
            conn.execute(sql)
