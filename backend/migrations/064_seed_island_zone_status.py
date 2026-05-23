"""
064_seed_island_zone_status.py — Repair island_zone_status and app_config for DBs
                                  where migration 018 seed was not applied.

Section: System / Island
Dependencies: island_zone_status table, app_config table (both created by migration 018)

What this migration does (all idempotent):
  1. Seeds island_zone_status with 5 rows if missing
     (forest=unlocked, ocean/savanna/space/legend=locked)
  2. Inserts island_initialized=false into app_config if the key is absent
     (so onboarding flow triggers correctly on first open)
  3. Inserts lumi_exchange_rate=100 if absent (used by exchange UI)

Why needed: migration 018 seeded these rows via a helper function that was
skipped on some existing DBs (table existed but had 0 rows). Every call to
/api/island/onboarding/status would return initialized=false in a loop, and
onboarding_complete would set the flag but unlock no zones (UPDATE WHERE → 0 rows).
"""

from datetime import datetime, timezone


def run(conn):
    now = datetime.now(timezone.utc).isoformat()

    # ── 1. island_zone_status ──────────────────────────────────────────────────
    ZONES = [
        ("forest",  1, now),
        ("ocean",   0, None),
        ("savanna", 0, None),
        ("space",   0, None),
        ("legend",  0, None),
    ]
    for zone, unlocked, unlocked_at in ZONES:
        existing = conn.execute(
            "SELECT id FROM island_zone_status WHERE zone = ?", (zone,)
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO island_zone_status (zone, is_unlocked, unlocked_at) "
                "VALUES (?, ?, ?)",
                (zone, unlocked, unlocked_at),
            )

    # ── 2. island_initialized app_config key ──────────────────────────────────
    existing_init = conn.execute(
        "SELECT id FROM app_config WHERE key = 'island_initialized'"
    ).fetchone()
    if existing_init is None:
        conn.execute(
            "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, ?)",
            ("island_initialized", "false", now),
        )

    # ── 3. lumi_exchange_rate app_config key ──────────────────────────────────
    existing_rate = conn.execute(
        "SELECT id FROM app_config WHERE key = 'lumi_exchange_rate'"
    ).fetchone()
    if existing_rate is None:
        conn.execute(
            "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, ?)",
            ("lumi_exchange_rate", "100", now),
        )
