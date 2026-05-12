"""
Migration 046 — Fill sort_order for all us_academy_words
=========================================================
All 684 words have sort_order = NULL.

Strategy: within each lesson, assign sort_order = 1, 2, 3, …
in word_id ascending order (matches original ingestion order,
which follows the textbook's word sequence per lesson).

A word belongs to exactly one lesson (enforced after migration 044
removed the 18 duplicate word_lesson rows), so we JOIN
us_academy_word_lesson to derive the rank.

SQL: ROW_NUMBER() OVER (PARTITION BY lesson_id ORDER BY word_id)
     applied via a WITH (CTE) + correlated subquery UPDATE.

Idempotent: guarded by WHERE sort_order IS NULL.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Count words still needing sort_order
    cur.execute("SELECT COUNT(*) FROM us_academy_words WHERE sort_order IS NULL")
    before = cur.fetchone()[0]

    if before == 0:
        print("[046] Done — sort_order already filled, 0 rows updated.")
        conn.close()
        return

    # Assign sort_order = rank within each lesson (word_id ascending)
    # Uses a CTE to compute ranks then updates via correlated subquery.
    cur.executescript(
        """
        WITH ranked AS (
            SELECT
                wl.word_id,
                ROW_NUMBER() OVER (
                    PARTITION BY wl.lesson_id
                    ORDER BY wl.word_id
                ) AS rn
            FROM us_academy_word_lesson wl
        )
        UPDATE us_academy_words
        SET sort_order = (
            SELECT rn FROM ranked WHERE ranked.word_id = us_academy_words.id
        )
        WHERE sort_order IS NULL
          AND EXISTS (
              SELECT 1 FROM us_academy_word_lesson WHERE word_id = us_academy_words.id
          );
        """
    )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM us_academy_words WHERE sort_order IS NULL")
    after = cur.fetchone()[0]
    updated = before - after

    # Sanity: show min/max sort_order per lesson (sample 5 lessons)
    cur.execute(
        """
        SELECT wl.lesson_id, MIN(w.sort_order), MAX(w.sort_order), COUNT(*) as cnt
        FROM us_academy_word_lesson wl
        JOIN us_academy_words w ON w.id = wl.word_id
        GROUP BY wl.lesson_id
        ORDER BY wl.lesson_id
        LIMIT 5
        """
    )
    samples = cur.fetchall()

    conn.close()
    print(f"[046] Done — {updated} sort_order values filled (was {before} NULL).")
    print("      Sample (lesson_id, min_order, max_order, word_count):")
    for row in samples:
        print(f"        lesson {row[0]}: {row[1]}~{row[2]}, {row[3]} words")


if __name__ == "__main__":
    run()
