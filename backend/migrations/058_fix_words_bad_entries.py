"""
migrations/058_fix_words_bad_entries.py — Remove test entries and fill missing POS in words table.

Issues found in the words table:
  id=1   word='testword'   — placeholder test row, delete
  id=5   word='capable'    — POS empty, set 'adjective'
  id=6   word='impossible' — POS empty, set 'adjective'
  id=7   word='gable'      — POS empty, set 'noun'
  id=8   word='accessible' — POS empty, set 'adjective'
  id=14  word='nr'         — OCR artifact (garbled 'interest'), delete

Idempotent: checks word value before acting so re-running is safe.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Rows to delete (word value used as safety check, not just id)
DELETE_WORDS = {
    1: "testword",
    14: "nr",
}

# Rows missing POS: id → (expected_word, correct_pos)
FIX_POS = {
    5:  ("capable",    "adjective"),
    6:  ("impossible", "adjective"),
    7:  ("gable",      "noun"),
    8:  ("accessible", "adjective"),
    9:  ("publicly",   "adverb"),
}


def run(db_path: Path = DB_PATH) -> None:
    if not Path(db_path).exists():
        print(f"058: DB not found at {db_path}; skipping.")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "words" not in tables:
            print("058: words table absent; skipping.")
            return

        deleted = 0
        for row_id, expected_word in DELETE_WORDS.items():
            row = conn.execute(
                "SELECT word FROM words WHERE id=?", (row_id,)
            ).fetchone()
            if row and row[0] == expected_word:
                conn.execute("DELETE FROM words WHERE id=?", (row_id,))
                deleted += 1

        fixed = 0
        for row_id, (expected_word, correct_pos) in FIX_POS.items():
            row = conn.execute(
                "SELECT word, pos FROM words WHERE id=?", (row_id,)
            ).fetchone()
            if row and row[0] == expected_word and not (row[1] or "").strip():
                conn.execute(
                    "UPDATE words SET pos=? WHERE id=?",
                    (correct_pos, row_id),
                )
                fixed += 1

        conn.commit()
        print(f"058: words table — {deleted} rows deleted, {fixed} POS fields filled")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
