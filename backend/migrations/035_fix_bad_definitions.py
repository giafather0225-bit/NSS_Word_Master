"""
Migration 035 — Fix bad definitions, wrong POS labels, and broken example sentences
Corrects 15 word entries identified in the data-quality audit:
  - 5 wrong/circular definitions (food webs, ear canal, plane, galaxy, gravitational pull)
  - 5 wrong part-of-speech labels (axial bones, dismally, perilously, unconsciously, white light)
  - 4 wrong example sentences (dismally, envisioned, perilously, unconsciously, white light)
  - 1 typo in example_1 (reproached → repraoached)
  - interconnected and dissenter both need POS + definition fixes
  - marrow needs definition fix (circular)
Idempotent: checks current value before updating to avoid double-runs.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Each entry: (word, field, new_value)
# field is one of: "definition", "part_of_speech", "example_1"
FIXES: list[tuple[str, str, str]] = [
    # ── axial bones (id 135) ──────────────────────────────────────────────────
    ("axial bones", "part_of_speech", "noun"),
    ("axial bones", "definition",
     "The bones that form the central axis of the body, including the skull, spine, and ribcage."),
    ("axial bones", "example_1",
     "The axial bones protect your brain, spinal cord, and heart."),

    # ── dismally (id 34) ──────────────────────────────────────────────────────
    ("dismally", "part_of_speech", "adverb"),
    ("dismally", "definition",
     "In a very sad, gloomy, or hopeless way."),
    ("dismally", "example_1",
     "The team performed dismally and lost the game by twenty points."),

    # ── dissenter (id 596) ────────────────────────────────────────────────────
    ("dissenter", "part_of_speech", "noun"),
    ("dissenter", "definition",
     "A person who disagrees with or refuses to accept an established opinion, rule, or belief."),
    ("dissenter", "example_1",
     "One dissenter in the group refused to vote in favor of the new rule."),

    # ── ear canal (id 180) ────────────────────────────────────────────────────
    ("ear canal", "definition",
     "The tube-shaped passage that leads from the outer ear to the eardrum."),
    ("ear canal", "example_1",
     "Never put small objects in your ear canal, as they can damage your hearing."),

    # ── envisioned (id 544) ───────────────────────────────────────────────────
    ("envisioned", "example_1",
     "She envisioned herself crossing the finish line as she trained for the race."),

    # ── food webs (id 647) ────────────────────────────────────────────────────
    ("food webs", "definition",
     "A system of interconnected food chains that shows how energy and nutrients "
     "pass from one living thing to another in an ecosystem."),

    # ── galaxy (id 382) ───────────────────────────────────────────────────────
    ("galaxy", "definition",
     "A very large group of billions of stars, gas, and dust held together by gravity in outer space."),

    # ── gravitational pull (id 389) ───────────────────────────────────────────
    ("gravitational pull", "definition",
     "The force of gravity that attracts objects toward one another, especially "
     "the pull that keeps planets and people from floating off into space."),

    # ── interconnected (id 131) ───────────────────────────────────────────────
    ("interconnected", "part_of_speech", "adjective"),
    ("interconnected", "definition",
     "Connected to each other so that each part depends on or works with the others."),
    ("interconnected", "example_1",
     "All living things in an ecosystem are interconnected — if one disappears, others are affected."),

    # ── marrow (id 138) ───────────────────────────────────────────────────────
    ("marrow", "definition",
     "The soft, spongy tissue found inside bones that produces red and white blood cells."),

    # ── perilously (id 562) ───────────────────────────────────────────────────
    ("perilously", "part_of_speech", "adverb"),
    ("perilously", "definition",
     "In a very dangerous or risky way."),
    ("perilously", "example_1",
     "The hiker walked perilously close to the edge of the cliff."),

    # ── plane (id 272) ────────────────────────────────────────────────────────
    ("plane", "definition",
     "A flat, two-dimensional surface that extends in all directions without any curves."),

    # ── reproached (id 29) — typo only ───────────────────────────────────────
    ("reproached", "example_1",
     "The teacher reproached the students for not completing their assignments."),

    # ── unconsciously (id 162) ───────────────────────────────────────────────
    ("unconsciously", "part_of_speech", "adverb"),
    ("unconsciously", "definition",
     "Without being aware of what you are doing; without thinking about it on purpose."),
    ("unconsciously", "example_1",
     "She unconsciously began humming her favorite song while she was reading."),

    # ── white light (id 289) ─────────────────────────────────────────────────
    ("white light", "part_of_speech", "noun"),
    ("white light", "definition",
     "Light that appears white because it contains all the colors of the visible "
     "spectrum mixed together, such as sunlight or light from a lamp."),
    ("white light", "example_1",
     "When white light passes through a prism, it separates into all the colors of the rainbow."),
]


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    updated = 0
    skipped = 0

    for word, field, new_value in FIXES:
        # Only update if current value is actually different (idempotency)
        cur.execute(
            f"SELECT {field} FROM us_academy_words WHERE word = ?",
            (word,),
        )
        row = cur.fetchone()
        if row is None:
            print(f"  SKIP (not found): {word}")
            skipped += 1
            continue
        current = row[0] or ""
        if current.strip() == new_value.strip():
            skipped += 1
            continue
        cur.execute(
            f"UPDATE us_academy_words SET {field} = ? WHERE word = ?",
            (new_value, word),
        )
        updated += 1
        print(f"  [{word}].{field} → {new_value[:60]}")

    conn.commit()
    conn.close()
    print(f"\nMigration 035 complete: {updated} fields updated, {skipped} skipped.")


if __name__ == "__main__":
    run()
