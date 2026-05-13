"""
migrations/055_island_evo_food_image_paths.py — Backfill island_shop_items.image
Section: Island
Idempotent — safe to run repeatedly.

Populates the `image` column for evolution stone and food items (id 1-9).
Migration 023 already handled decoration items (id 10-55); this fills the
remaining shop items so the Reward Shop can render real PNG assets for all
categories.

Asset paths are relative to /static/img/island/ (the FastAPI static mount base).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# (id, relative_image_path)  — paths under frontend/static/img/island/
_ITEM_PATHS: list[tuple[int, str]] = [
    (1, "items/evo_stone_a.png"),
    (2, "items/evo_stone_b.png"),
    (3, "items/evo_stone_2.png"),
    (4, "items/legend_stone_a.png"),
    (5, "items/legend_stone_b.png"),
    (6, "items/legend_stone_2.png"),
    (7, "items/food_small.png"),
    (8, "items/food_big.png"),
    (9, "items/food_special.png"),
]


def run() -> None:
    """Apply migration. Idempotent — only updates rows where image is empty."""
    if not DB_PATH.exists():
        print(f"[migration 055] DB not found at {DB_PATH} — skipped.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='island_shop_items'"
        ).fetchone()
        if not row:
            print("[migration 055] island_shop_items table missing — run 018 first.")
            return

        updated = skipped = 0
        for item_id, image_path in _ITEM_PATHS:
            cur = conn.execute(
                "UPDATE island_shop_items SET image=? "
                "WHERE id=? AND (image IS NULL OR image='')",
                (image_path, item_id),
            )
            if cur.rowcount > 0:
                updated += 1
            else:
                skipped += 1
        conn.commit()
        print(f"[migration 055] evo/food image paths — updated {updated}, skipped {skipped}.")
    finally:
        conn.close()


# Allow main.py lifespan runner (which calls migrate()) to auto-execute this.
migrate = run

if __name__ == "__main__":
    run()
