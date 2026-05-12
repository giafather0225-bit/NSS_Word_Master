"""
Migration 040 — Fix compound nouns wrongly tagged as 'adjective'
=================================================================
13 multi-word entries are tagged as adjective with modifier-style definitions
(e.g., "cardiac muscle → adjective, 'of, relating to, or affecting the heart'").
These are all nouns and need both correct POS and proper Grade-3 definitions.

Also fixes example_1 sentences where the example illustrates the modifier word
rather than the compound term (e.g., "natural disaster" example was "That's her
natural hair color." — which is wrong in every way).

Idempotent: guarded by WHERE part_of_speech = 'adjective'.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# (word, new_pos, new_definition, new_example)
FIXES = [
    (
        "appendicular bones",
        "noun",
        "the bones of the limbs, shoulders, and hips that are attached to the central skeleton",
        "The appendicular bones include the arms, legs, and the bones of the hips and shoulders.",
    ),
    (
        "cardiac muscle",
        "noun",
        "the special type of muscle found only in the heart that pumps blood throughout the body",
        "The cardiac muscle works every second of the day to keep blood moving through your body.",
    ),
    (
        "celestial bodies",
        "noun",
        "natural objects found in outer space, such as stars, planets, moons, and comets",
        "The sun, Earth, and moon are all celestial bodies that travel through space.",
    ),
    (
        "cerebral cortex",
        "noun",
        "the outer layer of the brain that controls thinking, memory, language, and movement",
        "The cerebral cortex helps us think, solve problems, and understand what we read.",
    ),
    (
        "cultural identity",
        "noun",
        "a person's sense of belonging to a group that shares the same customs, beliefs, language, or history",
        "Her cultural identity was shaped by the food, music, and traditions her family shared.",
    ),
    (
        "indentured servants",
        "noun",
        "people who agreed to work for someone for a set number of years, often in exchange for travel costs or to pay off a debt",
        "Indentured servants worked without pay for several years before they were free to live on their own.",
    ),
    (
        "invasive species",
        "noun",
        "a plant or animal brought into a new area where it spreads quickly and harms the local environment and native wildlife",
        "The zebra mussel is an invasive species that spread through American lakes and crowded out native animals.",
    ),
    (
        "involuntary muscle",
        "noun",
        "a muscle in the body that moves on its own without you thinking about it, such as the heart or the muscles in your stomach",
        "The heart is an involuntary muscle because it keeps beating even while you sleep.",
    ),
    (
        "natural disaster",
        "noun",
        "a sudden, destructive event caused by nature, such as an earthquake, flood, tornado, or hurricane",
        "The powerful earthquake was a natural disaster that damaged hundreds of buildings in the city.",
    ),
    (
        "outer ear",
        "noun",
        "the visible part of the ear on the outside of your head that collects sounds and directs them toward the eardrum",
        "The outer ear is the curved part you can see and feel on the side of your head.",
    ),
    (
        "safe haven",
        "noun",
        "a place where a person or animal is protected from danger and can feel completely safe",
        "The wildlife sanctuary was a safe haven for injured animals to heal and recover.",
    ),
    (
        "voluntary muscles",
        "noun",
        "muscles you can control on purpose, such as the ones you use to move your arms, legs, and face",
        "When you wave hello, you are using voluntary muscles to lift and move your arm.",
    ),
    (
        "woolly mammoths",
        "noun",
        "large, shaggy-furred animals related to elephants that lived during the Ice Age and are now extinct",
        "Woolly mammoths roamed frozen lands thousands of years ago and used their curved tusks to dig through snow for food.",
    ),
]


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    updated = 0
    skipped = 0

    for word, new_pos, new_def, new_ex in FIXES:
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word=? AND part_of_speech='adjective'",
            (word,),
        )
        if cur.fetchone()[0] == 0:
            skipped += 1
            continue
        cur.execute(
            """UPDATE us_academy_words
               SET part_of_speech=?, definition=?, example_1=?
             WHERE word=? AND part_of_speech='adjective'""",
            (new_pos, new_def, new_ex, word),
        )
        updated += cur.rowcount

    conn.commit()
    conn.close()
    print(f"[040] Done — {updated} rows updated, {skipped} already fixed / not found.")


if __name__ == "__main__":
    run()
