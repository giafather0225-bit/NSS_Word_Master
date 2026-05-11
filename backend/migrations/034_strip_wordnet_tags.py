"""
Migration 034 — Strip [wordnet] source tags from word definitions
- Removes '[wordnet] ' prefix from 40 word definitions
- Strips stray attribution suffixes like '; -G.G.Coulton', '; - Henry Kissinger'
- Fixes two completely wrong definitions (invasive species, mayflower compact)
- Capitalises first letter of cleaned definitions
Idempotent: re-running is safe (tags already gone → no change)
"""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Manual overrides for definitions that WordNet matched to the wrong sense
MANUAL_FIXES: dict[str, str] = {
    "invasive species": (
        "A species that is not native to an ecosystem and whose introduction "
        "causes or is likely to cause harm to the environment or economy."
    ),
    "mayflower compact": (
        "The first governing document of Plymouth Colony, signed in 1620 by "
        "the Pilgrim colonists aboard the Mayflower, establishing self-governance."
    ),
}

# Attribution patterns to strip from the end of a definition
_ATTR_RE = re.compile(r"\s*;?\s*-\s*[A-Z][A-Za-z .]+$")


def _clean(word: str, definition: str) -> str:
    """Remove [tag] prefix, strip attribution suffixes, capitalise."""
    if word in MANUAL_FIXES:
        return MANUAL_FIXES[word]

    # Remove leading [tag] block
    cleaned = re.sub(r"^\[.*?\]\s*", "", definition).strip()

    # Strip trailing attribution like '; -G.G.Coulton' or '; - Henry Kissinger'
    cleaned = _ATTR_RE.sub("", cleaned).strip()

    # Ensure sentence starts with capital letter
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, word, definition FROM us_academy_words "
        "WHERE definition LIKE '[%]%'"
    )
    rows = cur.fetchall()

    if not rows:
        print("Migration 034: nothing to update (already clean).")
        conn.close()
        return

    updated = 0
    for wid, word, definition in rows:
        cleaned = _clean(word, definition)
        if cleaned != definition:
            cur.execute(
                "UPDATE us_academy_words SET definition = ? WHERE id = ?",
                (cleaned, wid),
            )
            updated += 1
            print(f"  [{word}] → {cleaned[:70]}")

    conn.commit()
    conn.close()
    print(f"Migration 034 complete: {updated} definitions cleaned.")


if __name__ == "__main__":
    run()
