"""
Migration 038 — Fix wrong POS tags and improve too-short / low-quality definitions
===================================================================================
Issues fixed:

A) Wrong part_of_speech — adverbs tagged as 'adjective' (8 words):
   anxiously, consciously, effectively, intently, intricately,
   particularly, reluctantly, sparingly

B) Wrong part_of_speech — noun tagged as 'adjective':
   invertebrates

C) Definition quality — single-word synonyms, comma lists, circular, wrong capitalisation:
   estivate, ferocious, frequency, inventive, mended, navigate, quantities,
   raucous, regard, sustenance, tender, tolerant, unerring, wondrous

Idempotent: every UPDATE is guarded by WHERE part_of_speech / definition match.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# ── A + B: POS fixes (word, new_pos, new_definition, guard_pos) ─────────────
POS_FIXES = [
    # adverbs wrongly tagged as adjective
    ("anxiously",    "adverb",
     "in a way that shows worry or nervousness about what might happen",
     "adjective"),
    ("consciously",  "adverb",
     "doing something on purpose while being fully aware of what you are doing",
     "adjective"),
    ("effectively",  "adverb",
     "in a way that works well and produces the result you wanted",
     "adjective"),
    ("intently",     "adverb",
     "with great focus and concentration; paying very close attention",
     "adjective"),
    ("intricately",  "adverb",
     "in a way that involves many small, closely connected parts or details",
     "adjective"),
    ("particularly", "adverb",
     "more than usual; especially; used to single out one thing from others",
     "adjective"),
    ("reluctantly",  "adverb",
     "in a way that shows you do not really want to do something",
     "adjective"),
    ("sparingly",    "adverb",
     "using only a small amount; being careful not to use too much of something",
     "adjective"),
    # noun wrongly tagged as adjective
    ("invertebrates", "noun",
     "animals that do not have a backbone or spine, such as insects, worms, and jellyfish",
     "adjective"),
]

# ── C: Definition quality fixes (word, new_definition, guard_fragment) ───────
DEF_FIXES = [
    ("estivate",    "verb",
     "to spend the summer in a resting or inactive state, as some animals do",
     "Sleep during summer"),

    ("ferocious",   "adjective",
     "very fierce, violent, and frightening",
     "fierce, savage"),

    ("frequency",   "noun",
     "how often something happens or occurs in a period of time",
     "frequent repetition"),

    ("inventive",   "adjective",
     "good at thinking up new and clever ideas; able to create original things",
     "creative"),

    ("mended",      "verb",
     "fixed or repaired something that was broken, torn, or damaged",
     "improve, correct"),

    ("navigate",    "verb",
     "to plan and follow a route to get from one place to another, by land, water, or air",
     "to travel by water"),

    ("quantities",  "noun",
     "amounts or numbers of something, often measured or counted",
     "amount, number"),

    ("raucous",     "adjective",
     "unpleasantly loud, rough, and noisy",
     "loud and harsh"),

    ("regard",      "noun",
     "careful thought or attention given to someone or something; respect",
     "consideration"),

    ("sustenance",  "noun",
     "food and drink needed to keep a person or animal alive and healthy",
     "living, subsistence"),

    ("tender",      "adjective",
     "soft and easy to chew or touch; gentle and kind in feeling",
     "not tough"),

    ("tolerant",    "adjective",
     "willing to accept or respect ideas, beliefs, or behaviors that are different from your own",
     "showing tolerance"),

    ("unerring",    "adjective",
     "always accurate and never making mistakes",
     "Not liable to error"),

    ("wondrous",    "adjective",
     "causing feelings of wonder and amazement; remarkably impressive",
     "wonderful"),
]


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    updated = 0
    skipped = 0

    # A + B: POS fixes
    for word, new_pos, new_def, guard_pos in POS_FIXES:
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word=? AND part_of_speech=?",
            (word, guard_pos),
        )
        if cur.fetchone()[0] == 0:
            skipped += 1
            continue
        cur.execute(
            "UPDATE us_academy_words SET part_of_speech=?, definition=? WHERE word=? AND part_of_speech=?",
            (new_pos, new_def, word, guard_pos),
        )
        updated += cur.rowcount

    # C: Definition quality fixes
    for word, new_pos, new_def, guard_frag in DEF_FIXES:
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word=? AND definition LIKE ?",
            (word, f"%{guard_frag}%"),
        )
        if cur.fetchone()[0] == 0:
            skipped += 1
            continue
        cur.execute(
            "UPDATE us_academy_words SET part_of_speech=?, definition=? WHERE word=? AND definition LIKE ?",
            (new_pos, new_def, word, f"%{guard_frag}%"),
        )
        updated += cur.rowcount

    conn.commit()
    conn.close()
    print(f"[038] Done — {updated} rows updated, {skipped} already fixed / not found.")


if __name__ == "__main__":
    run()
