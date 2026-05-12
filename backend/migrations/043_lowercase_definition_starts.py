"""
Migration 043 — Lowercase first character of definitions
=========================================================
62 definitions start with an uppercase letter (e.g., "A man-made object…",
"The force of gravity…", "Having the earth as the center").

All English definitions in us_academy_words should start with a lowercase
letter for consistency. No entries require special-case protection:
  - nasa / polaris / mayflower compact all start with "An …" / "The …" (articles)
  - No definition literally begins with a proper noun

Strategy: single SQL UPDATE using
  lower(substr(definition,1,1)) || substr(definition,2)
guarded by the uppercase condition so the migration is idempotent.

Idempotent: second run finds 0 rows matching the uppercase condition.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Count before
    cur.execute(
        """
        SELECT COUNT(*) FROM us_academy_words
        WHERE substr(definition,1,1) = upper(substr(definition,1,1))
          AND substr(definition,1,1) != lower(substr(definition,1,1))
        """
    )
    before = cur.fetchone()[0]

    # Bulk lowercase first character
    cur.execute(
        """
        UPDATE us_academy_words
        SET definition = lower(substr(definition,1,1)) || substr(definition,2)
        WHERE substr(definition,1,1) = upper(substr(definition,1,1))
          AND substr(definition,1,1) != lower(substr(definition,1,1))
        """
    )
    updated = cur.rowcount

    conn.commit()
    conn.close()
    print(
        f"[043] Done — {updated} definitions lowercased "
        f"(was {before} uppercase-start rows)."
    )


if __name__ == "__main__":
    run()
