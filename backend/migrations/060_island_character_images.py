"""
Migration 060 — Fill island_characters.images JSON from on-disk PNG files
"""
import json, sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

CHAR_MAP = {
    "sprout":("Forest","Sprout"),"clover":("Forest","clover"),"mossy":("Forest","mossy"),
    "fernlie":("Forest","fernlie"),"blossie":("Forest","blossie"),
    "axie":("Ocean","axie"),"finn":("Ocean","finn"),"delphi":("Ocean","delphi"),
    "bubbles":("Ocean","bubbles"),"starla":("Ocean","starla"),
    "mane":("Savanna","mane"),"ellie":("Savanna","ellie"),"leo":("Savanna","leo"),
    "zuri":("Savanna","zuri"),"rhino":("Savanna","rhino"),
    "lumie":("Space","lumie"),"twinkle":("Space","twinkle"),"orbee":("Space","orbee"),
    "nova":("Space","nova"),"cosmo":("Space","cosmo"),
    "dragon":("Legend","dragon"),"unicorn":("Legend","unicorn"),"phoenix":("Legend","phoenix"),
    "gumiho":("Legend","gumiho"),"qilin":("Legend","qilin"),
}
STAGES = ["baby","mid_a","mid_b","final_a","final_b"]

def run(db_path=str(DB_PATH)):
    if not Path(db_path).exists():
        print("060: DB not found; skipping."); return
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT id, name FROM island_characters WHERE images IS NULL OR images = '{}'").fetchall()
        if not rows:
            print("060: Already done."); return
        updated = 0
        for char_id, name in rows:
            key = name.lower()
            if key not in CHAR_MAP: continue
            zone, prefix = CHAR_MAP[key]
            imgs = json.dumps({s: f"{zone}/{prefix}_{s}.png" for s in STAGES})
            conn.execute("UPDATE island_characters SET images=? WHERE id=?", (imgs, char_id))
            updated += 1
            print(f"060: [OK] {name}")
        conn.commit()
        print(f"060: Done — updated {updated}.")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
