"""
Migration 036 — Fix single-word synonym definitions and broken examples
Targets ~16 entries where:
  - definition is a single word / synonym (e.g. dejected: "sad")
  - definition is factually wrong for lesson context (big bang, extended family, culture)
  - example_1 is a noun-phrase fragment instead of a full sentence
  - part_of_speech is wrong (warily: adjective → adverb; extended family: verb → noun)
All replacements use Grade-3-appropriate American English.
Idempotent: only updates rows whose current value differs from the new value.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

FIXES: list[tuple[str, str, str]] = [
    # ── big bang ──────────────────────────────────────────────────────────────
    ("big bang", "part_of_speech", "noun"),
    ("big bang", "definition",
     "The enormous explosion about 14 billion years ago that scientists believe "
     "created the universe and all matter, energy, space, and time."),
    ("big bang", "example_1",
     "According to the Big Bang theory, the universe started from a single tiny "
     "point and has been expanding ever since."),

    # ── extended family ───────────────────────────────────────────────────────
    ("extended family", "part_of_speech", "noun"),
    ("extended family", "definition",
     "A family group that includes not just parents and children, but also "
     "grandparents, aunts, uncles, and cousins living together or nearby."),
    ("extended family", "example_1",
     "My extended family gathers every Thanksgiving, including grandparents, "
     "aunts, uncles, and all my cousins."),

    # ── culture (lesson context: human/social culture, not plant cultivation) ─
    ("culture", "definition",
     "The customs, arts, beliefs, and way of life shared by a group of people "
     "at a particular time and place."),
    ("culture", "example_1",
     "Ancient Roman culture influenced art, architecture, and language throughout "
     "the world for thousands of years."),

    # ── conceited ─────────────────────────────────────────────────────────────
    ("conceited", "definition",
     "Having an exaggerated opinion of yourself and your abilities; thinking "
     "you are better or more important than you really are."),

    # ── deities ───────────────────────────────────────────────────────────────
    ("deities", "definition",
     "Gods or goddesses that people worship; divine beings believed to have "
     "special powers over nature and human life."),
    ("deities", "example_1",
     "The ancient Romans worshipped many deities, including Jupiter, the king of the gods."),

    # ── dejected ──────────────────────────────────────────────────────────────
    ("dejected", "definition",
     "Feeling very sad and disappointed, especially because something did not "
     "go the way you hoped."),

    # ── intolerable ───────────────────────────────────────────────────────────
    ("intolerable", "definition",
     "So bad, painful, or unpleasant that it is impossible to put up with."),
    ("intolerable", "example_1",
     "The summer heat in the stadium was intolerable — we had to leave early."),

    # ── invaluable ────────────────────────────────────────────────────────────
    ("invaluable", "definition",
     "Extremely useful and important; so valuable that its worth cannot be measured."),
    ("invaluable", "example_1",
     "My grandmother's stories about growing up in the 1950s are invaluable to our family history."),

    # ── raucous (fragment example) ───────────────────────────────────────────
    ("raucous", "example_1",
     "The raucous crowd cheered so loudly that we could hear them from two blocks away."),

    # ── sentinels ─────────────────────────────────────────────────────────────
    ("sentinels", "definition",
     "People or things that stand guard and watch for danger or enemies; lookouts "
     "posted to protect a place."),

    # ── slither ───────────────────────────────────────────────────────────────
    ("slither", "definition",
     "To move smoothly and quietly by sliding the body from side to side, the "
     "way a snake moves along the ground."),

    # ── slumber ───────────────────────────────────────────────────────────────
    ("slumber", "definition",
     "A peaceful, restful sleep, often a deep or long one."),

    # ── valiant ───────────────────────────────────────────────────────────────
    ("valiant", "definition",
     "Very brave and determined, especially when facing danger or difficulty."),
    ("valiant", "example_1",
     "The valiant firefighters rushed into the burning building to save the family inside."),

    # ── warily ────────────────────────────────────────────────────────────────
    ("warily", "part_of_speech", "adverb"),
    ("warily", "definition",
     "In a cautious and watchful way, ready for possible danger or problems."),
    ("warily", "example_1",
     "The deer stepped warily out of the forest, looking around for any sign of danger."),

    # ── brutal (fragment example) ─────────────────────────────────────────────
    ("brutal", "example_1",
     "The brutal winter storm knocked out power for thousands of homes across the state."),

    # ── embellish ─────────────────────────────────────────────────────────────
    ("embellish", "definition",
     "To make something more beautiful or interesting by adding decorative details "
     "or extra information, sometimes more than is strictly true."),
    ("embellish", "example_1",
     "The storyteller loved to embellish his tales with dramatic details to keep the audience entertained."),
]


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    updated = 0
    skipped = 0

    for word, field, new_value in FIXES:
        cur.execute(
            f"SELECT {field} FROM us_academy_words WHERE word = ?",
            (word,),
        )
        row = cur.fetchone()
        if row is None:
            print(f"  SKIP (not found): {word}")
            skipped += 1
            continue
        current = (row[0] or "").strip()
        if current == new_value.strip():
            skipped += 1
            continue
        cur.execute(
            f"UPDATE us_academy_words SET {field} = ? WHERE word = ?",
            (new_value, word),
        )
        updated += 1
        print(f"  [{word}].{field} → {new_value[:65]}")

    conn.commit()
    conn.close()
    print(f"\nMigration 036 complete: {updated} fields updated, {skipped} skipped.")


if __name__ == "__main__":
    run()
