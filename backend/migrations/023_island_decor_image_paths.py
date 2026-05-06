"""
migrations/023_island_decor_image_paths.py — Backfill island_shop_items.image
Section: Island
Idempotent — safe to run repeatedly.

Populates the `image` column of every decoration row with a slug-based path
(`decor/{zone}_{slug}.png`) that the frontend uses to load the corresponding
PNG asset. Items whose `image` is already non-empty are skipped.

Migration 018 inserts decoration items with empty image strings; this fills
them so the Scene-Stage decorate flow can render real assets (or placeholder
fallbacks via `<img onerror>`) keyed off zone + name.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# (id, zone, slug) — slugs match the asset prompt list shipped with the
# decorate feature. Filenames are `decor/{zone}_{slug}.png`.
_DECOR_PATHS: list[tuple[int, str, str]] = [
    # Forest (9)
    (10, "forest", "mushroom_lantern"),
    (11, "forest", "signpost"),
    (12, "forest", "honey_jar"),
    (13, "forest", "cabin"),
    (14, "forest", "fairy_gate"),
    (15, "forest", "treehouse"),
    (16, "forest", "firefly"),
    (17, "forest", "flower_rain"),
    (18, "forest", "mist"),
    # Ocean (9)
    (19, "ocean", "treasure_chest"),
    (20, "ocean", "shell_chime"),
    (21, "ocean", "coral_lantern"),
    (22, "ocean", "garden"),
    (23, "ocean", "sea_cave"),
    (24, "ocean", "palace"),
    (25, "ocean", "bubbles"),
    (26, "ocean", "light_pillar"),
    (27, "ocean", "aurora"),
    # Savanna (9)
    (28, "savanna", "baobab"),
    (29, "savanna", "pride_rock"),
    (30, "savanna", "oasis"),
    (31, "savanna", "waterfall"),
    (32, "savanna", "cliff"),
    (33, "savanna", "cave"),
    (34, "savanna", "sunset"),
    (35, "savanna", "migration"),
    (36, "savanna", "starry_sky"),
    # Space (9)
    (37, "space", "meteorite"),
    (38, "space", "crater"),
    (39, "space", "nebula"),
    (40, "space", "black_hole"),
    (41, "space", "asteroids"),
    (42, "space", "star_cloud"),
    (43, "space", "meteor_shower"),
    (44, "space", "aurora"),
    (45, "space", "wormhole"),
    # Legend (10)
    (46, "legend", "dragon_nest"),
    (47, "legend", "rainbow_bridge"),
    (48, "legend", "phoenix_tree"),
    (49, "legend", "gumiho_shrine"),
    (50, "legend", "qilin_prints"),
    (51, "legend", "sacred_tree"),
    (52, "legend", "magic_circle"),
    (53, "legend", "golden_aura"),
    (54, "legend", "rainbow_waterfall"),
    (55, "legend", "star_altar"),
]


def run() -> None:
    """Apply migration. Idempotent — only updates rows where image is empty."""
    if not DB_PATH.exists():
        print(f"[migration 023] DB not found at {DB_PATH} — skipped.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        # Verify table exists
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='island_shop_items'"
        ).fetchone()
        if not row:
            print("[migration 023] island_shop_items table missing — run 018 first.")
            return

        updated = 0
        skipped = 0
        for item_id, zone, slug in _DECOR_PATHS:
            image_path = f"decor/{zone}_{slug}.png"
            cur = conn.execute(
                "UPDATE island_shop_items SET image=? "
                "WHERE id=? AND category='decoration' "
                "AND (image IS NULL OR image='' OR image LIKE 'decor/%')",
                (image_path, item_id),
            )
            if cur.rowcount > 0:
                updated += 1
            else:
                skipped += 1
        conn.commit()
        print(f"[migration 023] decoration image paths — updated {updated}, skipped {skipped}.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
