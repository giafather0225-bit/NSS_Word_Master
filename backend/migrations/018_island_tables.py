"""
migrations/018_island_tables.py — Replace legacy tables with Island system
Section: Island
Idempotent — safe to run repeatedly.

Drops  : rewards, schedules, growth_theme_progress
Creates: 10 island tables
Seeds  : island_zone_status (5 rows), island_shop_items (55 items),
         island_characters (25 rows — 5 per zone × 5 zones),
         app_config island keys

Note: ISLAND_SPEC.md section 11 says "30 characters" but the character
roster (sections 3.1–3.5) defines exactly 5 per zone × 5 zones = 25.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# ─────────────────────────────────────────────────────────────────────────────
# DDL — CREATE TABLE IF NOT EXISTS (all idempotent)
# ─────────────────────────────────────────────────────────────────────────────

_DDL = [
    # 1. character catalog
    """
    CREATE TABLE IF NOT EXISTS island_characters (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        name                        TEXT    NOT NULL,
        zone                        TEXT    NOT NULL,
        subject                     TEXT    NOT NULL,
        order_index                 INTEGER NOT NULL DEFAULT 1,
        description                 TEXT    NOT NULL DEFAULT '',
        images                      TEXT    NOT NULL DEFAULT '{}',
        lumi_production             INTEGER NOT NULL DEFAULT 5,
        xp_boost_pct                REAL    NOT NULL DEFAULT 1.5,
        xp_boost_a_pct              REAL    NOT NULL DEFAULT 3.0,
        xp_boost_b_pct              REAL    NOT NULL DEFAULT 3.0,
        is_legend                   INTEGER NOT NULL DEFAULT 0,
        unlock_requires_character_id INTEGER REFERENCES island_characters(id),
        is_available                INTEGER NOT NULL DEFAULT 0,
        evo_first_xp                INTEGER NOT NULL DEFAULT 750,
        evo_second_xp               INTEGER NOT NULL DEFAULT 1900
    )
    """,
    # 2. Gia's character progress (no UNIQUE — can adopt same char twice for A/B)
    """
    CREATE TABLE IF NOT EXISTS island_character_progress (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        character_id                INTEGER NOT NULL REFERENCES island_characters(id),
        nickname                    TEXT    NOT NULL DEFAULT '',
        stage                       TEXT    NOT NULL DEFAULT 'baby',
        level                       INTEGER NOT NULL DEFAULT 1,
        current_xp                  INTEGER NOT NULL DEFAULT 0,
        hunger                      INTEGER NOT NULL DEFAULT 80,
        happiness                   INTEGER NOT NULL DEFAULT 80,
        is_completed                INTEGER NOT NULL DEFAULT 0,
        is_active                   INTEGER NOT NULL DEFAULT 1,
        is_legend_type              INTEGER NOT NULL DEFAULT 0,
        boost_active                INTEGER NOT NULL DEFAULT 0,
        boost_subject               TEXT    NOT NULL DEFAULT '',
        last_production_date        TEXT,
        last_decay_date             TEXT,
        pos_x                       INTEGER NOT NULL DEFAULT 0,
        pos_y                       INTEGER NOT NULL DEFAULT 0,
        adopted_at                  TEXT    NOT NULL DEFAULT (datetime('now')),
        completed_at                TEXT
    )
    """,
    # 3. care log (auto-delete after 30 days — handled by daily batch)
    """
    CREATE TABLE IF NOT EXISTS island_care_log (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        character_progress_id       INTEGER NOT NULL REFERENCES island_character_progress(id),
        action                      TEXT    NOT NULL,
        hunger_change               INTEGER NOT NULL DEFAULT 0,
        happiness_change            INTEGER NOT NULL DEFAULT 0,
        source                      TEXT    NOT NULL DEFAULT '',
        logged_at                   TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    # 4. shop catalog
    """
    CREATE TABLE IF NOT EXISTS island_shop_items (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        name                TEXT    NOT NULL,
        category            TEXT    NOT NULL,
        sub_category        TEXT,
        zone                TEXT    NOT NULL DEFAULT 'all',
        evolution_type      TEXT,
        price               INTEGER NOT NULL DEFAULT 0,
        is_legend_currency  INTEGER NOT NULL DEFAULT 0,
        image               TEXT    NOT NULL DEFAULT '',
        is_active           INTEGER NOT NULL DEFAULT 1,
        description         TEXT    NOT NULL DEFAULT ''
    )
    """,
    # 5. owned items
    """
    CREATE TABLE IF NOT EXISTS island_inventory (
        id                              INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_item_id                    INTEGER NOT NULL REFERENCES island_shop_items(id),
        item_type                       TEXT    NOT NULL,
        quantity                        INTEGER NOT NULL DEFAULT 1,
        used_on_character_progress_id   INTEGER REFERENCES island_character_progress(id),
        purchased_at                    TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    # 6. placed decorations
    """
    CREATE TABLE IF NOT EXISTS island_placed_items (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_item_id    INTEGER NOT NULL UNIQUE REFERENCES island_shop_items(id),
        zone            TEXT    NOT NULL,
        pos_x           INTEGER NOT NULL DEFAULT 0,
        pos_y           INTEGER NOT NULL DEFAULT 0,
        is_placed       INTEGER NOT NULL DEFAULT 1,
        placed_at       TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    # 7. lumi balance (single row id=1)
    """
    CREATE TABLE IF NOT EXISTS island_currency (
        id              INTEGER PRIMARY KEY,
        lumi            INTEGER NOT NULL DEFAULT 0 CHECK (lumi >= 0),
        legend_lumi     INTEGER NOT NULL DEFAULT 0 CHECK (legend_lumi >= 0),
        total_earned    INTEGER NOT NULL DEFAULT 0,
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    # 8. lumi transaction log (auto-delete after 90 days)
    """
    CREATE TABLE IF NOT EXISTS island_lumi_log (
        id                          INTEGER PRIMARY KEY AUTOINCREMENT,
        currency_type               TEXT    NOT NULL DEFAULT 'lumi',
        action                      TEXT    NOT NULL,
        amount                      INTEGER NOT NULL,
        source                      TEXT    NOT NULL DEFAULT '',
        balance_after               INTEGER NOT NULL DEFAULT 0,
        legend_balance_after        INTEGER NOT NULL DEFAULT 0,
        character_progress_id       INTEGER REFERENCES island_character_progress(id),
        earned_date                 TEXT,
        created_at                  TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    # 9. legend character streak tracking
    """
    CREATE TABLE IF NOT EXISTS island_legend_progress (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        character_id        INTEGER NOT NULL REFERENCES island_characters(id),
        consecutive_days    INTEGER NOT NULL DEFAULT 0,
        total_days          INTEGER NOT NULL DEFAULT 0,
        last_completed_date TEXT,
        is_unlocked         INTEGER NOT NULL DEFAULT 0,
        is_completed        INTEGER NOT NULL DEFAULT 0,
        completed_at        TEXT
    )
    """,
    # 10. zone unlock status
    """
    CREATE TABLE IF NOT EXISTS island_zone_status (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        zone                TEXT    NOT NULL UNIQUE,
        is_unlocked         INTEGER NOT NULL DEFAULT 0,
        unlocked_at         TEXT,
        first_completed_at  TEXT
    )
    """,
]

# ─────────────────────────────────────────────────────────────────────────────
# Seed data
# ─────────────────────────────────────────────────────────────────────────────

_ZONE_STATUS_SEED = [
    # (zone, is_unlocked)
    ("forest",  1),
    ("ocean",   1),
    ("savanna", 1),
    ("space",   1),
    ("legend",  0),
]

# island_characters — 5 zones × 5 characters = 25 rows
# Columns: name, zone, subject, order_index, description, lumi_production,
#          xp_boost_pct, xp_boost_a_pct, xp_boost_b_pct, is_legend,
#          unlock_requires_order, is_available, evo_first_xp, evo_second_xp
#
# unlock_requires_order: None = no requirement; otherwise = order_index of
# the prerequisite character in the same zone (resolved to FK after insert)

_CHARACTER_SEED = [
    # ── Forest / English ──────────────────────────────────────────────────
    ("Sprout",  "forest",  "english", 1, "A small green sprout full of potential",    5, 1.5, 3.0, 3.0, 0, None, 1, 750, 1900),
    ("Clover",  "forest",  "english", 2, "A lucky three-leaf clover spirit",          5, 1.5, 3.0, 3.0, 0,    1, 0, 750, 1900),
    ("Mossy",   "forest",  "english", 3, "A moss-covered stone spirit",               5, 1.5, 3.0, 3.0, 0,    2, 0, 750, 1900),
    ("Fernlie", "forest",  "english", 4, "A fern fairy from the ancient grove",       5, 1.5, 3.0, 3.0, 0,    3, 0, 750, 1900),
    ("Blossie", "forest",  "english", 5, "A gentle flower bud ready to bloom",        5, 1.5, 3.0, 3.0, 0,    4, 0, 750, 1900),
    # ── Ocean / Math ──────────────────────────────────────────────────────
    ("Axie",    "ocean",   "math",    1, "A pink axolotl with feathery gills",        5, 1.5, 3.0, 3.0, 0, None, 1, 750, 1900),
    ("Finn",    "ocean",   "math",    2, "A clownfish with bright orange stripes",    5, 1.5, 3.0, 3.0, 0,    1, 0, 750, 1900),
    ("Delphi",  "ocean",   "math",    3, "A playful dolphin with a white belly",      5, 1.5, 3.0, 3.0, 0,    2, 0, 750, 1900),
    ("Bubbles", "ocean",   "math",    4, "A round pufferfish who loves numbers",      5, 1.5, 3.0, 3.0, 0,    3, 0, 750, 1900),
    ("Starla",  "ocean",   "math",    5, "A five-pointed starfish connected to math", 5, 1.5, 3.0, 3.0, 0,    4, 0, 750, 1900),
    # ── Savanna / Diary ───────────────────────────────────────────────────
    ("Mane",    "savanna", "diary",   1, "A baby horse with no mane yet",             5, 1.5, 3.0, 3.0, 0, None, 1, 750, 1900),
    ("Ellie",   "savanna", "diary",   2, "A baby elephant with wide curious eyes",    5, 1.5, 3.0, 3.0, 0,    1, 0, 750, 1900),
    ("Leo",     "savanna", "diary",   3, "A fluffy baby lion without a mane yet",     5, 1.5, 3.0, 3.0, 0,    2, 0, 750, 1900),
    ("Zuri",    "savanna", "diary",   4, "A baby giraffe with a short neck",          5, 1.5, 3.0, 3.0, 0,    3, 0, 750, 1900),
    ("Rhino",   "savanna", "diary",   5, "A baby rhino with one tiny horn",           5, 1.5, 3.0, 3.0, 0,    4, 0, 750, 1900),
    # ── Space / Review ────────────────────────────────────────────────────
    ("Lumie",   "space",   "review",  1, "A small alien with big eyes and an antenna",5, 1.5, 3.0, 3.0, 0, None, 1, 750, 1900),
    ("Twinkle", "space",   "review",  2, "A five-pointed star creature with a face",  5, 1.5, 3.0, 3.0, 0,    1, 0, 750, 1900),
    ("Orbee",   "space",   "review",  3, "A planet spirit with tiny Saturn rings",    5, 1.5, 3.0, 3.0, 0,    2, 0, 750, 1900),
    ("Nova",    "space",   "review",  4, "A comet fairy trailing a glowing tail",     5, 1.5, 3.0, 3.0, 0,    3, 0, 750, 1900),
    ("Cosmo",   "space",   "review",  5, "A retro robot / space probe explorer",      5, 1.5, 3.0, 3.0, 0,    4, 0, 750, 1900),
    # ── Legend / All ──────────────────────────────────────────────────────
    ("Dragon",   "legend", "all",     1, "A legendary dragon of flame and ice",      20, 3.0, 2.0, 8.0, 1, None, 0, 0, 0),
    ("Unicorn",  "legend", "all",     2, "A radiant unicorn of light and moon",      20, 3.0, 2.0, 8.0, 1, None, 0, 0, 0),
    ("Phoenix",  "legend", "all",     3, "An immortal phoenix reborn from the storm",20, 3.0, 2.0, 8.0, 1, None, 0, 0, 0),
    ("Gumiho",   "legend", "all",     4, "A mystical nine-tailed fox of gold and shadow",20,3.0,2.0,8.0,1,None,0,0,0),
    ("Qilin",    "legend", "all",     5, "A sacred qilin of sky and earth",          20, 3.0, 2.0, 8.0, 1, None, 0, 0, 0),
]

# island_shop_items — 55 items
# Columns: name, category, sub_category, zone, evolution_type,
#          price, is_legend_currency, description

_SHOP_SEED = [
    # ── Evolution stones (6) ──────────────────────────────────────────────
    ("1st Evolution Stone A",   "evolution", None, "all", "first_a",        50, 0, "Triggers 1st evolution on A branch"),
    ("1st Evolution Stone B",   "evolution", None, "all", "first_b",        50, 0, "Triggers 1st evolution on B branch"),
    ("2nd Evolution Stone",     "evolution", None, "all", "second",         80, 0, "Triggers 2nd evolution (follows 1st branch)"),
    ("Legend 1st Stone A",      "evolution", None, "legend", "legend_first_a", 10, 1, "Legend character 1st evolution — A branch"),
    ("Legend 1st Stone B",      "evolution", None, "legend", "legend_first_b", 10, 1, "Legend character 1st evolution — B branch"),
    ("Legend 2nd Stone",        "evolution", None, "legend", "legend_second",  20, 1, "Legend character 2nd evolution"),
    # ── Food items (3) ────────────────────────────────────────────────────
    ("Small Food",   "food", None, "all", None, 20, 0, "Character XP +50. Limit: 1x per character per day"),
    ("Big Food",     "food", None, "all", None, 50, 0, "Character XP +150. Limit: 1x per character per day"),
    ("Special Food", "food", None, "all", None, 90, 0, "Character XP +300. Limit: 1x per character per day"),
    # ── Forest decorations (9) ───────────────────────────────────────────
    ("Mushroom Lantern", "decoration", "prop",      "forest", None, 30,  0, "A glowing mushroom lantern for the forest path"),
    ("Signpost",         "decoration", "prop",      "forest", None, 40,  0, "A friendly wooden signpost"),
    ("Honey Jar",        "decoration", "prop",      "forest", None, 50,  0, "A big jar of forest honey"),
    ("Cabin",            "decoration", "building",  "forest", None, 60,  0, "A cozy wooden cabin in the trees"),
    ("Fairy Gate",       "decoration", "building",  "forest", None, 80,  0, "An enchanted gate woven from branches"),
    ("Treehouse",        "decoration", "building",  "forest", None, 120, 0, "A multi-level treehouse retreat"),
    ("Firefly Effect",   "decoration", "special",   "forest", None, 100, 0, "Floating fireflies that light up the night"),
    ("Flower Rain",      "decoration", "special",   "forest", None, 150, 0, "Petals drift down endlessly"),
    ("Forest Mist",      "decoration", "special",   "forest", None, 200, 0, "Ethereal mist rolls through the trees"),
    # ── Ocean decorations (9) ────────────────────────────────────────────
    ("Treasure Chest",    "decoration", "prop",      "ocean", None, 30,  0, "A barnacle-covered treasure chest"),
    ("Shell Chime",       "decoration", "prop",      "ocean", None, 40,  0, "A wind chime made of sea shells"),
    ("Coral Lantern",     "decoration", "prop",      "ocean", None, 50,  0, "A lantern shaped from glowing coral"),
    ("Underwater Garden", "decoration", "building",  "ocean", None, 60,  0, "A flourishing garden of sea plants"),
    ("Sea Cave",          "decoration", "building",  "ocean", None, 80,  0, "A mysterious cave beneath the waves"),
    ("Underwater Palace", "decoration", "building",  "ocean", None, 120, 0, "A majestic palace on the ocean floor"),
    ("Bubble Effect",     "decoration", "special",   "ocean", None, 100, 0, "Giant bubbles rise from the deep"),
    ("Light Pillar",      "decoration", "special",   "ocean", None, 150, 0, "A pillar of light shines through the water"),
    ("Aurora",            "decoration", "special",   "ocean", None, 200, 0, "A shimmering aurora dances underwater"),
    # ── Savanna decorations (9) ──────────────────────────────────────────
    ("Baobab Tree",      "decoration", "landscape", "savanna", None, 30,  0, "An ancient baobab tree stands tall"),
    ("Pride Rock",       "decoration", "landscape", "savanna", None, 40,  0, "A mighty rock overlooking the plains"),
    ("Oasis",            "decoration", "landscape", "savanna", None, 50,  0, "A cool oasis with palm trees"),
    ("Waterfall",        "decoration", "nature",    "savanna", None, 60,  0, "A cascade of water off the cliff edge"),
    ("Cliff",            "decoration", "nature",    "savanna", None, 80,  0, "A dramatic cliff with sweeping views"),
    ("Cave",             "decoration", "nature",    "savanna", None, 120, 0, "A deep cave shelter in the hillside"),
    ("Sunset Effect",    "decoration", "special",   "savanna", None, 100, 0, "A golden sunset paints the sky"),
    ("Great Migration",  "decoration", "special",   "savanna", None, 150, 0, "Herds move across the plains"),
    ("Starry Sky",       "decoration", "special",   "savanna", None, 200, 0, "A dazzling canopy of stars overhead"),
    # ── Space decorations (9) ────────────────────────────────────────────
    ("Meteorite",      "decoration", "landscape", "space", None, 30,  0, "A glowing meteorite fragment"),
    ("Crater",         "decoration", "landscape", "space", None, 40,  0, "A vast crater on the surface"),
    ("Nebula",         "decoration", "landscape", "space", None, 50,  0, "A colorful cloud of cosmic dust"),
    ("Black Hole",     "decoration", "nature",    "space", None, 60,  0, "A swirling black hole in the distance"),
    ("Asteroid Belt",  "decoration", "nature",    "space", None, 80,  0, "A ring of tumbling asteroids"),
    ("Star Cloud",     "decoration", "nature",    "space", None, 120, 0, "A dense cluster of shimmering stars"),
    ("Meteor Shower",  "decoration", "special",   "space", None, 100, 0, "Meteors streak across the night sky"),
    ("Space Aurora",   "decoration", "special",   "space", None, 150, 0, "Cosmic auroras ripple through space"),
    ("Wormhole",       "decoration", "special",   "space", None, 200, 0, "A portal to another dimension"),
    # ── Legend decorations (10 — Legend Lumi) ────────────────────────────
    ("Dragon's Nest",       "decoration", "dragon",   "legend", None,  5, 1, "The lair of the legendary dragon"),
    ("Rainbow Bridge",      "decoration", "unicorn",  "legend", None,  5, 1, "A bridge woven from rainbow light"),
    ("Phoenix Flame Tree",  "decoration", "phoenix",  "legend", None,  5, 1, "A tree forever ablaze with phoenix fire"),
    ("Gumiho Shrine",       "decoration", "gumiho",   "legend", None,  5, 1, "A shrine honoring the nine-tailed fox"),
    ("Qilin's Footprints",  "decoration", "qilin",    "legend", None,  5, 1, "Sacred hoofprints left by the Qilin"),
    ("Sacred Tree",         "decoration", "common",   "legend", None,  8, 1, "A tree rooted in legend lore"),
    ("Magic Circle",        "decoration", "common",   "legend", None,  8, 1, "An ancient circle of glowing runes"),
    ("Golden Aura Effect",  "decoration", "common",   "legend", None, 10, 1, "A divine golden glow fills the air"),
    ("Rainbow Waterfall",   "decoration", "common",   "legend", None, 10, 1, "A waterfall that flows in all colors"),
    ("Star Altar",          "decoration", "common",   "legend", None, 12, 1, "An altar lit by the light of stars"),
]

# app_config island keys: (key, value)
_APP_CONFIG_KEYS = [
    ("island_initialized",      "false"),
    ("island_on",               "true"),
    ("lumi_exchange_rate",      "100"),
    ("lumi_rule_english_stage", "3"),
    ("lumi_rule_english_final", "15"),
    ("lumi_rule_math_lesson",   "10"),
    ("lumi_rule_math_unit",     "20"),
    ("lumi_rule_diary",         "8"),
    ("lumi_rule_review",        "5"),
    ("lumi_rule_streak",        "5"),
    ("lumi_boost_total",        "0"),
    ("lumi_boost_english",      "0"),
    ("lumi_boost_math",         "0"),
    ("lumi_boost_diary",        "0"),
    ("lumi_boost_review",       "0"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Migration runner
# ─────────────────────────────────────────────────────────────────────────────

def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 018] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        _drop_legacy_tables(conn)
        _create_island_tables(conn)
        _seed_zone_status(conn)
        _seed_characters(conn)
        _seed_shop_items(conn)
        _seed_currency_row(conn)
        _seed_app_config(conn)
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

    print("[migration 018] complete.")


def _drop_legacy_tables(conn: sqlite3.Connection) -> None:
    for table in ("rewards", "schedules", "growth_theme_progress"):
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if exists:
            conn.execute(f"DROP TABLE {table}")
            print(f"[migration 018] Dropped table: {table}")
        else:
            print(f"[migration 018] Table '{table}' not found — skipped.")


def _create_island_tables(conn: sqlite3.Connection) -> None:
    for ddl in _DDL:
        conn.execute(ddl)
    conn.commit()
    print("[migration 018] Created 10 island tables.")


def _seed_zone_status(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM island_zone_status").fetchone()[0]
    if existing:
        print(f"[migration 018] island_zone_status already has {existing} rows — skipped.")
        return
    conn.executemany(
        "INSERT INTO island_zone_status (zone, is_unlocked) VALUES (?, ?)",
        _ZONE_STATUS_SEED,
    )
    print(f"[migration 018] Seeded {len(_ZONE_STATUS_SEED)} zone status rows.")


def _seed_characters(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM island_characters").fetchone()[0]
    if existing:
        print(f"[migration 018] island_characters already has {existing} rows — skipped.")
        return

    # First pass: insert without FK (unlock_requires_order used as placeholder).
    # We track (zone, order_index) → assigned id to resolve FKs in second pass.
    zone_order_to_id: dict[tuple[str, int], int] = {}

    for row in _CHARACTER_SEED:
        (name, zone, subject, order_index, description,
         lumi_production, xp_boost_pct, xp_boost_a_pct, xp_boost_b_pct,
         is_legend, _unlock_req_order, is_available,
         evo_first_xp, evo_second_xp) = row

        cur = conn.execute(
            """
            INSERT INTO island_characters
                (name, zone, subject, order_index, description,
                 lumi_production, xp_boost_pct, xp_boost_a_pct, xp_boost_b_pct,
                 is_legend, is_available, evo_first_xp, evo_second_xp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, zone, subject, order_index, description,
             lumi_production, xp_boost_pct, xp_boost_a_pct, xp_boost_b_pct,
             is_legend, is_available, evo_first_xp, evo_second_xp),
        )
        zone_order_to_id[(zone, order_index)] = cur.lastrowid

    # Second pass: resolve unlock_requires_character_id FK.
    for row in _CHARACTER_SEED:
        (name, zone, subject, order_index, description,
         lumi_production, xp_boost_pct, xp_boost_a_pct, xp_boost_b_pct,
         is_legend, unlock_req_order, is_available,
         evo_first_xp, evo_second_xp) = row
        if unlock_req_order is not None:
            prereq_id = zone_order_to_id.get((zone, unlock_req_order))
            char_id   = zone_order_to_id[(zone, order_index)]
            if prereq_id:
                conn.execute(
                    "UPDATE island_characters SET unlock_requires_character_id=? WHERE id=?",
                    (prereq_id, char_id),
                )

    conn.commit()
    print(f"[migration 018] Seeded {len(_CHARACTER_SEED)} characters.")


def _seed_shop_items(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM island_shop_items").fetchone()[0]
    if existing:
        print(f"[migration 018] island_shop_items already has {existing} rows — skipped.")
        return

    conn.executemany(
        """
        INSERT INTO island_shop_items
            (name, category, sub_category, zone, evolution_type,
             price, is_legend_currency, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        _SHOP_SEED,
    )
    print(f"[migration 018] Seeded {len(_SHOP_SEED)} shop items.")


def _seed_currency_row(conn: sqlite3.Connection) -> None:
    exists = conn.execute("SELECT id FROM island_currency WHERE id=1").fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO island_currency (id, lumi, legend_lumi, total_earned) VALUES (1, 0, 0, 0)"
        )
        print("[migration 018] Seeded island_currency row (id=1).")
    else:
        print("[migration 018] island_currency row already exists — skipped.")


def _seed_app_config(conn: sqlite3.Connection) -> None:
    # Check if app_config table exists (created by migration 001).
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='app_config'"
    ).fetchone()
    if not exists:
        print("[migration 018] app_config table not found — skipping config seed.")
        return

    added = []
    for key, value in _APP_CONFIG_KEYS:
        row = conn.execute("SELECT 1 FROM app_config WHERE key=?", (key,)).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO app_config (key, value) VALUES (?, ?)", (key, value)
            )
            added.append(key)

    if added:
        print(f"[migration 018] Added {len(added)} app_config keys: {', '.join(added)}")
    else:
        print("[migration 018] All app_config island keys already present.")


if __name__ == "__main__":
    migrate()
