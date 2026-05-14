"""
Migration 025 — Migrate CKLA SM-2 rows from us_academy_word_progress to word_reviews.

Background:
  Previously, CKLA lesson vocab completion wrote SM-2 tracking rows to
  us_academy_word_progress (USAcademyWordProgress). The routers/ckla_review.py
  router served those rows. Both are now replaced by the unified WordReview
  table (word_reviews) with source='ckla'.

This migration:
  1. Reads all us_academy_word_progress rows whose word_id maps to a CKLA word
     (us_academy_words.domain_num IS NOT NULL AND is_active=1).
  2. For each row not already present in word_reviews (de-dup by source/source_ref/word),
     inserts a new word_reviews row with source='ckla'.
  3. Does NOT delete the old us_academy_word_progress rows (safe rollback).

Idempotent: re-running inserts nothing due to the de-dup check.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Ensure word_reviews has the columns we need (should already exist from migration 004).
    cur.execute("PRAGMA table_info(word_reviews)")
    cols = {row[1] for row in cur.fetchall()}
    required = {"source", "source_ref", "question", "hint", "study_item_id"}
    missing = required - cols
    if missing:
        print(f"[025] SKIP — word_reviews missing columns: {missing}")
        return

    # Fetch CKLA word IDs (domain_num IS NOT NULL AND is_active=1).
    cur.execute("""
        SELECT id, word, definition, example_1
        FROM us_academy_words
        WHERE domain_num IS NOT NULL AND is_active = 1
    """)
    ckla_words = {row[0]: {"word": row[1], "definition": row[2] or "", "example_1": row[3] or ""}
                  for row in cur.fetchall()}

    if not ckla_words:
        print("[025] No CKLA words found — nothing to migrate.")
        return

    ckla_ids = list(ckla_words.keys())
    placeholders = ",".join("?" * len(ckla_ids))

    # Fetch existing us_academy_word_progress rows for CKLA words.
    cur.execute(f"""
        SELECT word_id, sm2_repetitions, sm2_easiness, sm2_interval,
               next_review, correct_count, wrong_count
        FROM us_academy_word_progress
        WHERE word_id IN ({placeholders})
    """, ckla_ids)
    existing_progress = cur.fetchall()

    if not existing_progress:
        print("[025] No us_academy_word_progress rows for CKLA words — nothing to migrate.")
        return

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    migrated = 0
    skipped = 0

    for row in existing_progress:
        word_id, reps, easiness, interval, next_review, correct, wrong = row
        if word_id not in ckla_words:
            continue

        w = ckla_words[word_id]
        word_name = w["word"]
        source_ref = f"migrated_word_{word_id}"
        total_reviews = (correct or 0) + (wrong or 0)
        total_correct = correct or 0

        # De-dup check: skip if already in word_reviews with source='ckla' and same word.
        cur.execute("""
            SELECT id FROM word_reviews
            WHERE source = 'ckla' AND word = ?
            LIMIT 1
        """, (word_name,))
        if cur.fetchone():
            skipped += 1
            continue

        cur.execute("""
            INSERT INTO word_reviews
                (study_item_id, word, subject, textbook, lesson,
                 easiness, interval, repetitions,
                 next_review, last_review,
                 total_reviews, total_correct,
                 source, source_ref, question, hint)
            VALUES
                (NULL, ?, 'English', 'CKLA', '',
                 ?, ?, ?,
                 ?, '',
                 ?, ?,
                 'ckla', ?, ?, ?)
        """, (
            word_name,
            str(round(float(easiness or 2.5), 2)),
            int(interval or 0),
            int(reps or 0),
            next_review or tomorrow,
            total_reviews,
            total_correct,
            source_ref,
            w["definition"],
            w["example_1"],
        ))
        migrated += 1

    conn.commit()
    print(f"[025] Migrated {migrated} CKLA SM-2 rows to word_reviews. Skipped {skipped} duplicates.")


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        run(conn)
