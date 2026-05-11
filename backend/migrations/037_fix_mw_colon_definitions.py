"""
Migration 037 — Fix Merriam-Webster colon-style definitions in us_academy_words
=================================================================================
Merriam-Webster uses " : synonym" suffix patterns (e.g., "free from mistakes : right")
that are inappropriate for Grade 3 learners. This migration rewrites ~76 affected entries
with plain, child-friendly American English definitions.

Also fixes:
  - Wrong part_of_speech for adverbs tagged as "adjective" (instinctively, miraculously,
    thoroughly, ultimately)
  - Wrong part_of_speech for nouns tagged as "verb/adjective" (mistreatment, middle ear,
    sound waves, densely populated)
  - Circular definitions (ingenious, curable)
  - Completely wrong definitions copied from another word (sound waves, densely populated)

Idempotent: every UPDATE is guarded by WHERE definition LIKE '%old pattern%'
so re-running is safe.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Each entry: (word, new_pos, new_definition, old_definition_fragment_for_guard)
FIXES = [
    # ── wrong POS + MW colon ────────────────────────────────────────────────
    ("instinctively", "adverb",
     "done automatically without thinking, guided by natural instinct",
     "of or relating to instinct"),

    ("miraculously", "adverb",
     "in a way that seems impossible or amazing, like a miracle",
     "being or being like a miracle"),

    ("mistreatment", "noun",
     "cruel or unfair treatment of a person or animal",
     "to handle, use, or act toward in a harsh way"),

    ("middle ear", "noun",
     "the part of the ear behind the eardrum that carries sound vibrations to the inner ear",
     "equally distant from the ends"),

    ("sound waves", "noun",
     "vibrations that travel through air or water and are heard as sound",
     "free from disease or weakness"),

    ("densely populated", "adjective",
     "having a very large number of people living in a small area",
     "having its parts crowded together"),

    ("thoroughly", "adverb",
     "completely and carefully, without leaving anything out",
     "being such to the fullest degree"),

    ("ultimately", "adverb",
     "in the end, after everything else has happened; finally",
     "last in a series"),

    # ── circular definitions ─────────────────────────────────────────────────
    ("ingenious", "adjective",
     "very clever at thinking of new or creative ideas and solutions",
     "showing ingenuity"),

    ("curable", "adjective",
     "able to be healed or made better with medical treatment",
     "possible to bring about recovery from"),

    # ── MW colon definitions (POS already correct) ───────────────────────────
    ("abounds", "verb",
     "grows or exists in very large numbers or amounts",
     "to be plentiful"),

    ("accurate", "adjective",
     "completely correct and without any mistakes",
     "free from mistakes"),

    ("alarmed", "verb",
     "made someone feel sudden fear or worry about danger",
     "to cause to feel a sense of danger"),

    ("amend", "verb",
     "to make a change or correction to improve something",
     "to change for the better"),

    ("call on", "verb",
     "to ask or invite someone to speak or participate",
     "to speak in a loud clear voice so as to be heard"),

    ("cluster", "noun",
     "a group of similar things that are close together",
     "a number of similar things growing or grouped closely together"),

    ("compelled", "verb",
     "forced to do something; having no choice but to act",
     "to make (as a person) do something by the use of physical"),

    ("complex", "adjective",
     "having many connected parts that make it hard to understand",
     "not easy to understand or explain"),

    ("conducted", "verb",
     "led or carried out an activity or event in an organized way",
     "to plan and put into operation from a position of command"),

    ("conflict", "noun",
     "a serious disagreement or fight between people or groups",
     "an extended struggle"),

    ("conquering", "verb",
     "taking control of a place or defeating an enemy through fighting",
     "to get or gain by force"),

    ("crude", "adjective",
     "in a natural, unrefined state; not processed or finished",
     "in a natural state and not changed by special treatment"),

    ("dense", "adjective",
     "packed tightly together with very little space between",
     "having its parts crowded together"),

    ("discovered", "verb",
     "found or learned about something for the very first time",
     "to find out, see, or learn of especially for the first time"),

    ("diverse", "adjective",
     "made up of many different kinds or types",
     "different from each other"),

    ("enabled", "verb",
     "gave someone the ability or means to do something",
     "to give strength, power, or ability to"),

    ("energy", "noun",
     "the power that allows living things and machines to move and do work",
     "ability to be active"),

    ("established", "verb",
     "started or created something that is meant to last",
     "to bring into being"),

    ("evidence", "noun",
     "facts or signs that show whether something is true",
     "a sign which shows that something exists or is true"),

    ("evident", "adjective",
     "easy to see or understand; very clear and obvious",
     "clear to the sight or to the mind"),

    ("fate", "noun",
     "a power believed to decide what will happen to a person in the future",
     "a power beyond human control that is believed to determine"),

    ("flourished", "verb",
     "grew strongly and did very well",
     "to grow well"),

    ("functions", "noun",
     "the job or purpose that something or someone is meant to do",
     "the action for which a person or thing is designed or used"),

    ("gross", "adjective",
     "very obvious and unacceptable; clearly wrong or very unpleasant",
     "noticeably bad"),

    ("hour", "noun",
     "a unit of time equal to 60 minutes; one of 24 equal parts of a day",
     "one of the 24 divisions of a day"),

    ("illuminates", "verb",
     "lights up a place or object so it can be clearly seen",
     "to supply with light"),

    ("immense", "adjective",
     "very large in size or amount",
     "very great in size or amount"),

    ("inevitable", "adjective",
     "certain to happen; impossible to avoid or prevent",
     "sure to happen"),

    ("infancy", "noun",
     "the earliest period of a baby or young child's life",
     "the first stage of a child's life"),

    ("inhospitable", "adjective",
     "not welcoming or friendly to visitors; difficult or harsh to live in",
     "not friendly or generous"),

    ("internal", "adjective",
     "located inside something; belonging to the inside",
     "being within something"),

    ("international", "adjective",
     "involving or happening between two or more different countries",
     "involving two or more nations"),

    ("irreversible", "adjective",
     "impossible to undo or change back to the way it was before",
     "impossible to change back to a previous condition"),

    ("lowly", "adjective",
     "low in rank, importance, or social position; not highly regarded",
     "of low rank or importance"),

    ("maintain", "verb",
     "to keep something in its current good condition; to continue doing something",
     "to carry on"),

    ("modest", "adjective",
     "not boasting about your abilities or achievements; quietly humble",
     "not overly proud or confident"),

    ("opaque", "adjective",
     "not allowing light to pass through; not see-through",
     "not letting light through"),

    ("optimistic", "adjective",
     "hopeful and expecting that good things will happen",
     "expecting good things to happen"),

    ("outspoken", "adjective",
     "saying what you think honestly and directly, even if it is bold or surprising",
     "talking in a free and honest way"),

    ("possessed", "verb",
     "had or owned something as your own",
     "to have and hold as property"),

    ("posture", "noun",
     "the way you hold or position your body when sitting, standing, or moving",
     "the way in which the body is positioned when sitting or standing"),

    ("potential", "adjective",
     "possible or likely in the future, but not yet real or certain",
     "existing as a possibility"),

    ("propose", "verb",
     "to suggest an idea or plan for others to think about and discuss",
     "to make a suggestion to be thought over"),

    ("pure", "adjective",
     "not mixed with anything else; clean and free from harmful substances",
     "not mixed with anything else"),

    ("pursue", "verb",
     "to follow or chase after someone or something",
     "to follow after in order to catch or destroy"),

    ("pursued", "verb",
     "followed or chased after someone or something",
     "to follow after in order to catch or destroy"),

    ("recollection", "noun",
     "the ability to remember things from the past; a memory of something",
     "the act or power of remembering"),

    ("regulate", "verb",
     "to control or manage something by making and applying rules",
     "to bring under the control of authority"),

    ("reliable", "adjective",
     "able to be trusted to do what is expected, every time",
     "fit to be trusted or relied on"),

    ("reproached", "verb",
     "told someone they did something wrong; blamed or criticized",
     "to find fault with"),

    ("resolve", "verb",
     "to find a solution to a problem or disagreement",
     "to find an answer to"),

    ("rivalries", "noun",
     "competitions between two or more people or groups each trying to be better than the other",
     "the state of trying to defeat or be more successful than another"),

    ("sauntering", "verb",
     "walking slowly and in a relaxed, leisurely way without hurrying",
     "to walk in a slow relaxed way"),

    ("shortage", "noun",
     "a situation where there is not enough of something that is needed",
     "a condition in which there is not enough of something needed"),

    ("slavery", "noun",
     "the cruel practice of one person owning another and forcing them to work without pay",
     "the state of being owned by another person"),

    ("solitary", "adjective",
     "being alone with no others nearby; done or existing by oneself",
     "all alone"),

    ("sound", "adjective",
     "healthy and in good condition; not damaged or weakened",
     "free from disease or weakness"),

    ("summoned", "verb",
     "called or ordered someone to come to a place or person",
     "to call or send for"),

    ("surplus", "noun",
     "an extra amount of something that is more than what is needed",
     "an amount left over"),

    ("surveyed", "verb",
     "looked carefully over an area or situation to examine or study it",
     "to look over"),

    ("tension", "noun",
     "a feeling of worry, nervousness, or stress; tightness between people",
     "the act of straining or stretching"),

    ("thrive", "verb",
     "to grow or develop very well and be healthy or successful",
     "to grow or develop very well"),

    ("transformation", "noun",
     "a complete and major change in how something looks or works",
     "the act or process of changing completely"),

    ("tsunamis", "noun",
     "very large, powerful ocean waves caused by earthquakes or volcanic eruptions under the sea",
     "a large sea wave produced especially by an earthquake"),

    ("unfamiliar", "adjective",
     "not known or recognized; something you have not experienced or seen before",
     "not well-known"),

    ("unjust", "adjective",
     "not fair or right; treating people in an unequal or unfair way",
     "not just"),

    ("venomous", "adjective",
     "able to produce poison that is injected through a bite or sting",
     "having or producing venom"),
]


def run(db_path: str = str(DB_PATH)) -> None:
    """Apply Grade-3-friendly rewrites for MW-colon definitions."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    updated = 0
    skipped = 0

    for word, new_pos, new_def, guard_fragment in FIXES:
        # Check if the row still has the old MW-style definition
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word = ? AND definition LIKE ?",
            (word, f"%{guard_fragment}%"),
        )
        count = cur.fetchone()[0]
        if count == 0:
            skipped += 1
            continue

        cur.execute(
            """
            UPDATE us_academy_words
               SET part_of_speech = ?,
                   definition      = ?
             WHERE word = ?
               AND definition LIKE ?
            """,
            (new_pos, new_def, word, f"%{guard_fragment}%"),
        )
        rows = cur.rowcount
        updated += rows

    conn.commit()
    conn.close()
    print(f"[037] Done — {updated} rows updated, {skipped} already fixed / not found.")


if __name__ == "__main__":
    run()
