"""
Migration 045 — Expand 54 short definitions (P2)
=================================================
54 definitions are under 25 characters — too brief for Grade-3 learners.
Most are bare synonyms (e.g., cranium → "skull", spine → "backbone",
consequently → "as a result") or MW-one-phrase entries.

Also fixes two bugs caught during review:
  - deafening : tagged 'verb' / wrong definition → adjective + correct def
  - imprisoned: example sentence never uses the word 'imprisoned'
                → replaced with a sentence that uses the word

Idempotent: every UPDATE guarded by the current (short) definition text.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# (word, new_pos, new_definition, new_example, guard_fragment)
# new_pos=None means keep existing POS
# new_example=None means keep existing example
FIXES = [
    # ── Adjectives ──────────────────────────────────────────────────────────
    (
        "boisterous", None,
        "loud, energetic, and full of wild activity; describing someone who is rough and noisy in an uncontrolled way",
        "The boisterous children ran and shouted on the playground during recess.",
        "being rough and noisy",
    ),
    (
        "brutal", None,
        "extremely cruel and harsh, causing great pain or suffering without any mercy",
        "The brutal winter storm knocked out power for thousands of homes across the region.",
        "cruel and harsh",
    ),
    (
        "confirmed", None,
        "firmly settled in a habit, belief, or way of life that is unlikely to change",
        "She was a confirmed reader who never went anywhere without a book.",
        "unlikely to change",
    ),
    (
        "conical", None,
        "having the shape of a cone, with a round base that narrows to a point at the top",
        "The conical hill rose sharply above the flat land surrounding it.",
        "shaped like a cone",
    ),
    (
        "finite", None,
        "having a definite end or limit; not going on forever",
        "The scientist reminded us that Earth has a finite amount of fresh water.",
        "having definite limits",
    ),
    (
        "frigid", None,
        "extremely cold; describing weather or a place where the temperature is dangerously or uncomfortably low",
        "The explorers bundled up in thick coats before venturing into the frigid Arctic air.",
        "freezing cold",
    ),
    (
        "interdependent", None,
        "describing two or more things or people that each rely on the others to survive or function",
        "The plants and insects in the forest are interdependent — the bees pollinate the flowers and the flowers feed the bees.",
        "depending on one another",
    ),
    (
        "laborious", None,
        "requiring a great deal of time, effort, and hard work; slow and tiring to do",
        "Rebuilding the stone wall after the flood was a slow and laborious task.",
        "requiring much effort",
    ),
    (
        "laden", None,
        "carrying a very heavy load; weighed down with something heavy",
        "The truck was laden with gravel and moved slowly down the mountain road.",
        "heavily loaded",
    ),
    (
        "magnetic", None,
        "having the ability to attract objects or attention in a powerful way, just as a magnet attracts metal",
        "The speaker had such a magnetic personality that the whole crowd leaned in to listen.",
        "acting like a magnet",
    ),
    (
        "public", None,
        "available or open for everyone to use or see; belonging to all people and not privately owned",
        "The town built a public library so that every child could borrow books for free.",
        "open to all",
    ),
    (
        "scarce", None,
        "in very short supply; hard to find because there is not enough for everyone who needs it",
        "During the long drought, food became scarce and families had to ration every meal.",
        "not plentiful",
    ),
    (
        "sophisticated", None,
        "highly developed, complex, or advanced; showing a high level of skill or knowledge",
        "The ancient Romans built sophisticated aqueducts that carried water to cities miles away.",
        "very complicated",
    ),
    (
        "subtle", None,
        "not obvious or easy to notice; slight and delicate, requiring careful attention to detect",
        "There was a subtle change in Miss Lavendar's voice that told Anne something was wrong.",
        "difficult to perceive",
    ),
    (
        "uninhabited", None,
        "having no people living there; empty of any human residents",
        "The explorers landed on an uninhabited island where no one had ever built a home.",
        "not lived in or on",
    ),
    # ── Adverb ───────────────────────────────────────────────────────────────
    (
        "consequently", None,
        "as a direct result of something that happened before; used to show that one event caused another",
        "She missed the bus and consequently arrived late to her first class.",
        "as a result",
    ),
    # ── Nouns ────────────────────────────────────────────────────────────────
    (
        "archipelago", None,
        "a large group or chain of islands scattered across an area of water",
        "The archipelago was made up of dozens of beautiful islands covered in lush green forests.",
        "a group of islands",
    ),
    (
        "barbarians", None,
        "people from ancient times who were considered wild and uncivilized; groups that attacked and destroyed more advanced civilizations",
        "The barbarians attacked the city with swords and shields, breaking through the outer walls.",
        "an uncivilized person",
    ),
    (
        "contract", None,
        "a written or spoken agreement between two or more people that is legally binding and must be honored",
        "The two merchants signed a contract agreeing on the price and delivery date.",
        "a legal agreement",
    ),
    (
        "counsel", None,
        "wise advice or guidance given to help someone make a decision or solve a problem",
        "My grandfather's counsel was to be patient and think carefully before speaking.",
        "advice given",
    ),
    (
        "cranium", None,
        "the rounded bony case that forms the upper part of the skull and surrounds and protects the brain",
        "The hard cranium acts like a helmet that protects your brain from injury.",
        "skull",
    ),
    (
        "debtors", None,
        "people who owe money or something of value to another person or organization",
        "The debtors were struggling to pay back what they owed before the deadline.",
        "a person who owes a debt",
    ),
    (
        "favors", None,
        "kind acts done to help someone, usually without expecting anything in return",
        "She was always doing favors for her neighbors, like helping carry groceries.",
        "an act of kindness",
    ),
    (
        "grievances", None,
        "formal complaints about something that is believed to be unfair or unjust",
        "The colonists listed their grievances against the king in a letter demanding fair treatment.",
        "a reason for complaining",
    ),
    (
        "intensity", None,
        "the strength, power, or forcefulness of something, such as a feeling, light, or physical force",
        "The athletes trained with great intensity, pushing themselves to improve every day.",
        "strength or force",
    ),
    (
        "peaks", None,
        "the pointed tops of mountains; also the highest points or moments of something",
        "The snow-covered peaks of the mountains could be seen from miles away.",
        "a prominent mountain",
    ),
    (
        "planks", None,
        "long, flat, thick pieces of wood used in building floors, walls, decks, or furniture",
        "The workers laid down sturdy wooden planks to build the floor of the cabin.",
        "a heavy thick board",
    ),
    (
        "sagas", None,
        "long stories or legends about the adventurous deeds and heroic journeys of brave warriors or legendary figures",
        "The Viking sagas were passed down for generations, telling of brave warriors and distant lands.",
        "a story of heroic deeds",
    ),
    (
        "serpent", None,
        "a large snake, especially one that appears in myths and stories as a symbol of danger or evil",
        "A large serpent slithered through the tall grass, its dark scales glinting in the sunlight.",
        "a usually large snake",
    ),
    (
        "spinal column", None,
        "the long column of small bones running down the center of the back that supports the body and protects the spinal cord; the backbone",
        "Without a strong spinal column, our bodies would not be able to stand upright.",
        "backbone",
    ),
    (
        "spine", None,
        "the long column of small bones running down the back that supports the body and protects the spinal cord; the backbone",
        "The giraffe's spine is long and flexible, allowing it to reach leaves high in the trees.",
        "backbone",
    ),
    (
        "tragedy", None,
        "a very sad event or situation in which something terrible happens, causing great suffering or loss",
        "The sinking of the great ship was a tragedy that shocked people all around the world.",
        "a disastrous event",
    ),
    (
        "voice box", None,
        "the part of the throat that contains the vocal cords and produces sound when you speak or sing; also called the larynx",
        "The voice box, located in your throat, is what allows you to speak, whisper, and sing.",
        "larynx",
    ),
    (
        "blues", None,
        "feelings of sadness, loneliness, or low spirits that make it hard to feel cheerful",
        "After his best friend moved away, he had a bad case of the blues.",
        "low spirits",
    ),
    # ── Verbs ────────────────────────────────────────────────────────────────
    (
        "absorbed", None,
        "soaked up or took in a liquid, substance, or information; became completely involved in something",
        "The dry sponge absorbed the spilled water almost instantly.",
        "to take in or swallow up",
    ),
    (
        "advance", None,
        "to move forward toward a goal; to make progress or to help something grow or improve",
        "The troops began to advance toward the enemy's position just after sunrise.",
        "to move forward",
    ),
    (
        "blazed", None,
        "burned intensely and brightly; also meant to lead the way through unknown land by marking a path",
        "A fire blazed in the fireplace, casting a warm glow across the room.",
        "to burn brightly",
    ),
    (
        "boarded", None,
        "got onto a ship, plane, train, or other vehicle to begin a journey",
        "The passengers boarded the ship early in the morning and found their cabins.",
        "to go aboard",
    ),
    (
        "command", None,
        "to give orders to others with authority; to be in charge and direct what people do",
        "The general gave the command for the troops to move forward.",
        "to order with authority",
    ),
    (
        "conserve", None,
        "to protect something from being wasted or used up by using it carefully and wisely",
        "The rangers worked hard to conserve water during the long dry summer.",
        "to prevent the waste of",
    ),
    (
        "devoured", None,
        "ate something quickly and hungrily; also read or experienced something with great eagerness",
        "The hungry traveler devoured the entire meal in just a few minutes.",
        "to eat up hungrily",
    ),
    (
        "dispersed", None,
        "spread out or scattered in different directions; caused a group to break up and go separate ways",
        "After the storm, the dark clouds finally dispersed and the sun came out.",
        "to break up and scatter",
    ),
    (
        "extinguish", None,
        "to put out a fire completely; also to end or destroy something permanently",
        "Firefighters worked through the night to extinguish the forest fire.",
        "to cause to stop burning",
    ),
    (
        "extracted", None,
        "removed or pulled out something from a larger material, often with effort or special tools",
        "The dentist carefully extracted the broken tooth without hurting the patient.",
        "to remove by pulling",
    ),
    (
        "founding", None,
        "establishing or creating something new for the first time, such as a town, organization, or nation",
        "The founding of Jamestown in 1607 marked the beginning of permanent English settlement in America.",
        "to begin or create",
    ),
    (
        "harassed", None,
        "repeatedly bothered, annoyed, or intimidated someone in an aggressive or threatening way",
        "He was harassed by bullies at school, and the teacher stepped in to put a stop to it.",
        "to annoy again and again",
    ),
    (
        "interrogate", None,
        "to question someone very carefully and persistently, often under pressure, to get information",
        "The detective sat down to interrogate the witness about what he had seen that night.",
        "to question thoroughly",
    ),
    (
        "preach", None,
        "to deliver a religious speech or sermon; also to strongly urge others to follow a particular belief",
        "The minister would preach every Sunday about kindness and helping those in need.",
        "to give a sermon",
    ),
    (
        "released", None,
        "set free or allowed to go after being held; also made something available to the public",
        "After three months, the rescued eagle was released back into the wild.",
        "to set free or let go of",
    ),
    (
        "shed", None,
        "to let something fall off naturally or release it; animals shed fur or skin, trees shed leaves",
        "In autumn, the oak tree began to shed its golden leaves onto the path below.",
        "to give off in drops",
    ),
    (
        "teeming", None,
        "filled with a very large number of living things that are all moving and active",
        "The rain forest was teeming with colorful birds, insects, and small animals.",
        "to be full of something",
    ),
    (
        "transformed", None,
        "changed completely in form, appearance, or nature into something different",
        "After months of work, the run-down building was transformed into a beautiful community center.",
        "to change completely",
    ),
    # ── POS bug fixes (caught during review) ─────────────────────────────────
    # deafening: tagged 'verb' with wrong definition; should be adjective
    (
        "deafening", "adjective",
        "extremely loud; so loud that it is almost impossible to hear anything else",
        "The crowd let out a deafening cheer when the home team scored the winning goal.",
        "to make unable to hear",
    ),
    # imprisoned: example sentence never uses the word 'imprisoned'
    # guard on the bad example rather than definition
    (
        "imprisoned", None,
        "put in prison as punishment for a crime; kept confined so that a person cannot move freely",
        "The king imprisoned anyone who spoke against his rule, filling the castle dungeons.",
        "to put in prison",
    ),
]


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    updated = 0
    skipped = 0

    for word, new_pos, new_def, new_ex, guard in FIXES:
        # Check current state
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word=? AND (definition LIKE ? OR example_1 LIKE ?)",
            (word, f"%{guard}%", f"%{guard}%"),
        )
        if cur.fetchone()[0] == 0:
            skipped += 1
            continue

        if new_pos:
            cur.execute(
                """UPDATE us_academy_words
                   SET part_of_speech=?, definition=?, example_1=?
                   WHERE word=? AND (definition LIKE ? OR example_1 LIKE ?)""",
                (new_pos, new_def, new_ex, word, f"%{guard}%", f"%{guard}%"),
            )
        else:
            cur.execute(
                """UPDATE us_academy_words
                   SET definition=?, example_1=?
                   WHERE word=? AND (definition LIKE ? OR example_1 LIKE ?)""",
                (new_def, new_ex, word, f"%{guard}%", f"%{guard}%"),
            )
        updated += cur.rowcount

    conn.commit()
    conn.close()
    print(f"[045] Done — {updated} definitions expanded, {skipped} already fixed / not found.")


if __name__ == "__main__":
    run()
