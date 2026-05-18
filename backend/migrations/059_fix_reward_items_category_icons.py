"""
migrations/059_fix_reward_items_category_icons.py
Fix reward_items: category 'badge' → 'real', emoji icons → Lucide icon names.
"""

SQL = """
UPDATE reward_items SET category = 'real', icon = 'monitor'    WHERE name = 'YouTube 30min';
UPDATE reward_items SET category = 'real', icon = 'gamepad-2'  WHERE name = 'Roblox 30min';
UPDATE reward_items SET category = 'real', icon = 'film'       WHERE name = 'Family Movie';
UPDATE reward_items SET category = 'real', icon = 'utensils'   WHERE name = 'Dinner Out';
UPDATE reward_items SET category = 'real', icon = 'gift'       WHERE name = 'Custom Reward';
"""


def run(conn):
    cur = conn.cursor()
    for stmt in SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    conn.commit()
    print("[migration 059] reward_items category → 'real', icons → Lucide names")
