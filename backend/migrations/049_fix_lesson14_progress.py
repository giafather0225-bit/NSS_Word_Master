"""
Migration 049 — Restore missing lesson_progress row for lesson 14
==================================================================
On 2026-05-11 Gia completed CKLA lesson 14 ("Cold-Blooded and Warm-Blooded
Animals").  Evidence:
  - xp_logs: ckla_lesson_complete (+15) and ckla_daily_goal (+10) at
    2026-05-11T10:41:21 with detail="14"
  - streak_logs: ckla_done=1 on 2026-05-11
  - us_academy_word_progress: 8 words (IDs 72-79) created 2026-05-11

The us_academy_lesson_progress row was lost (likely a manual DB reset during
development).  This migration recreates it so the CKLA UI reflects the real
completion state.

Idempotent: skips if a row for lesson_id=14 already exists.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Reconstructed from xp_logs created_at
COMPLETED_AT = "2026-05-11T10:41:21"


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Idempotent guard
    cur.execute(
        "SELECT id FROM us_academy_lesson_progress WHERE lesson_id = 14"
    )
    row = cur.fetchone()
    if row:
        print(f"[049] Skip — lesson_progress for lesson 14 already exists (id={row[0]}).")
        conn.close()
        return

    cur.execute(
        """
        INSERT INTO us_academy_lesson_progress (
            lesson_id,
            reading_done, reading_done_at,
            vocab_done,
            questions_attempted, questions_correct,
            qa_done,
            word_work_done,
            completed, completed_at,
            last_active,
            grade,
            started_at,
            difficulty_rating
        ) VALUES (
            14,
            1, :ts,
            1,
            0, 0,
            1,
            1,
            1, :ts,
            :ts,
            3,
            :ts,
            NULL
        )
        """,
        {"ts": COMPLETED_AT},
    )

    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    print(
        f"[049] Done — lesson_progress row created for lesson 14 "
        f"(id={new_id}, completed_at={COMPLETED_AT})."
    )


if __name__ == "__main__":
    run()
