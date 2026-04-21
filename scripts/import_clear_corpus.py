"""
scripts/import_clear_corpus.py — CLEAR Corpus 필터링 및 DB 임포트
Section: Academy
Dependencies: pandas, sqlite3, pathlib
API: none (run directly)

CLEAR Corpus (MIT License):
  https://github.com/scrosseye/CLEAR-Corpus
  https://www.kaggle.com/datasets/verracodeguacas/clear-corpus

Usage:
    1. Download CLEAR_Corpus.csv from GitHub or Kaggle
    2. Place at: NSS_Word_Master/data/academy/CLEAR_Corpus.csv
    3. Run: python3 scripts/import_clear_corpus.py

Filter criteria:
    - BT_easiness (grade difficulty): 3.0 ~ 4.9  (3rd-4th grade)
    - excerpt length: 200 ~ 400 words
    - licence: MIT-compatible (public domain / CC0 / open)

Inserts filtered passages into us_academy_passages table.
"""

import csv
import json
import sqlite3
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH      = Path.home() / "NSS_Learning" / "database" / "voca.db"
CORPUS_CSV   = PROJECT_ROOT / "data" / "academy" / "CLEAR_Corpus.csv"

# Grade range filter (BT_easiness column = teacher-rated grade difficulty)
MIN_GRADE = 3.0
MAX_GRADE = 4.9

# Word count filter
MIN_WORDS = 150
MAX_WORDS = 450


# @tag ACADEMY
def count_words(text: str) -> int:
    return len(text.split())


# @tag ACADEMY
def detect_genre(row: dict) -> str:
    """Map CLEAR Corpus genre/source to fiction|nonfiction."""
    source = row.get("Source", "").lower()
    genre  = row.get("Genre", "").lower()
    if any(k in genre for k in ["fiction", "narrative", "story", "literature"]):
        return "fiction"
    if any(k in source for k in ["gutenberg", "wikipedia"]):
        return "nonfiction" if "wikipedia" in source else "fiction"
    return "nonfiction"  # default for educational passages


# @tag ACADEMY
def import_corpus() -> None:
    if not CORPUS_CSV.exists():
        print(f"[import_clear] CSV not found at {CORPUS_CSV}")
        print("Download from: https://github.com/scrosseye/CLEAR-Corpus")
        print("Place at: data/academy/CLEAR_Corpus.csv")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    # Clear existing imported passages
    existing = conn.execute(
        "SELECT COUNT(*) FROM us_academy_passages WHERE clear_id IS NOT NULL"
    ).fetchone()[0]
    if existing > 0:
        print(f"[import_clear] {existing} passages already imported. Skipping.")
        conn.close()
        return

    inserted = 0
    skipped  = 0

    with open(CORPUS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Grade filter
            try:
                grade = float(row.get("BT_easiness", 0) or 0)
            except ValueError:
                grade = 0.0

            if not (MIN_GRADE <= grade <= MAX_GRADE):
                skipped += 1
                continue

            text = (row.get("excerpt") or row.get("Excerpt") or "").strip()
            if not text:
                skipped += 1
                continue

            wc = count_words(text)
            if not (MIN_WORDS <= wc <= MAX_WORDS):
                skipped += 1
                continue

            clear_id = row.get("ID") or row.get("id") or ""
            title    = row.get("Title") or row.get("title") or ""
            lexile   = None
            try:
                lexile = int(float(row.get("Flesch_Kincaid", 0) or 0))
            except Exception:
                pass
            genre = detect_genre(row)

            conn.execute(
                """INSERT INTO us_academy_passages
                   (clear_id, title, text, genre, lexile, word_count,
                    grade_level, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (clear_id, title, text, genre, lexile, wc, grade),
            )
            inserted += 1

    conn.commit()
    conn.close()
    print(f"[import_clear] Inserted {inserted} passages. Skipped {skipped}.")


if __name__ == "__main__":
    import_corpus()
