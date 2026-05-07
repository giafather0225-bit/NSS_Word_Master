"""
migrations/024_island_decor_extension.py — Add new decoration items
Section: Island
Idempotent — safe to run repeatedly.

Extension point for adding decoration items beyond the original 46 seeded
in migration 018. Append new items to `_NEW_DECOR_ITEMS` and re-run; rows
matching an existing name are skipped, so the migration is fully replayable
on fresh DBs and on already-seeded ones.

Each new item is inserted into `island_shop_items` with auto-assigned id
(starts at 56, since 018 seeded 1–55) and its `image` column is pre-filled
to `decor/{zone}_{slug}.png` so the Scene-Stage decorate flow renders the
asset (or the placeholder fallback when the PNG isn't present yet).

Adding a new decoration:
1. Append a tuple to `_NEW_DECOR_ITEMS` below.
2. Drop `frontend/static/img/island/decor/{zone}_{slug}.png` (or rely on
   the placeholder until the PNG ships).
3. Re-run: `python3 backend/migrations/024_island_decor_extension.py`.
4. (Optional) Run `scripts/check_decor_assets.py` to confirm asset coverage
   — note: that script reads migration 023's canonical list, so update it
   too when shipping new PNG slugs that you want tracked.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Tuple schema (matches island_shop_items columns minus auto id):
#   (name, sub_category, zone, price, slug, description)
#
# - `name`           : Display name (used as the idempotency key — must be unique).
# - `sub_category`   : "prop" | "building" | "nature" | "landscape" | "special"
# - `zone`           : "forest" | "ocean" | "savanna" | "space" | "legend"
# - `price`          : Lumi cost (integer). Legend zone items also flip
#                      `is_legend_currency` automatically below.
# - `slug`           : snake_case asset slug → `decor/{zone}_{slug}.png`.
# - `description`    : Short shop blurb.
#
# Leave the list empty for a no-op run (useful as a baseline migration on
# fresh DBs that already have the original 55 from 018).
_NEW_DECOR_ITEMS: list[tuple[str, str, str, int, str, str]] = [
    # Example — uncomment and adapt when adding a real item:
    # ("Glow Pond", "nature", "forest", 90, "glow_pond",
    #  "A pond that softly glows at dusk."),
]


def _name_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM island_shop_items WHERE name=? LIMIT 1", (name,)
    ).fetchone()
    return row is not None


def run() -> None:
    """Apply migration. Idempotent — only inserts items whose name is new."""
    if not DB_PATH.exists():
        print(f"[migration 024] DB not found at {DB_PATH} — skipped.")
        return

    if not _NEW_DECOR_ITEMS:
        print("[migration 024] no new decoration items defined — no-op.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        # Verify table exists (depends on 018).
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='island_shop_items'"
        ).fetchone()
        if not row:
            print("[migration 024] island_shop_items missing — run 018 first.")
            return

        inserted = 0
        skipped = 0
        for name, sub_category, zone, price, slug, description in _NEW_DECOR_ITEMS:
            if _name_exists(conn, name):
                skipped += 1
                continue
            image_path = f"decor/{zone}_{slug}.png"
            is_legend_currency = 1 if zone == "legend" else 0
            conn.execute(
                """
                INSERT INTO island_shop_items
                    (name, category, sub_category, zone, evolution_type,
                     price, is_legend_currency, description, image)
                VALUES (?, 'decoration', ?, ?, NULL, ?, ?, ?, ?)
                """,
                (name, sub_category, zone, price, is_legend_currency,
                 description, image_path),
            )
            inserted += 1
        conn.commit()
        print(f"[migration 024] decoration extension — inserted {inserted}, skipped {skipped}.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
