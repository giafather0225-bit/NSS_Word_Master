"""
migrations/001_add_new_tables.py — Phase 1 DB migration: add 15 new tables
Section: System
Dependencies: database.py, models.py
API: none (run directly)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import engine, Base, SessionLocal
import backend.models  # noqa: F401 — ensure all models are registered

# @tag SYSTEM @tag BACKUP
def run_migration():
    """
    Create all new tables that don't exist yet.
    Safe to run multiple times (uses CREATE TABLE IF NOT EXISTS via checkfirst=True).
    """
    print("Running migration 001: add new tables...")

    new_tables = [
        "app_config",
        "xp_logs",
        "streak_logs",
        "task_settings",
        "reward_items",
        "purchased_rewards",
        "daily_words_progress",
        "diary_entries",
        "growth_events",
        "day_off_requests",
        "academy_sessions",
        "learning_logs",
        "word_attempts",
        "academy_schedules",
        "growth_theme_progress",
    ]

    Base.metadata.create_all(engine, checkfirst=True)
    print(f"Migration complete. Ensured {len(new_tables)} new tables exist.")

    # Seed default task settings
    from backend.models import TaskSetting, RewardItem
    from datetime import datetime

    db = SessionLocal()
    try:
        if db.query(TaskSetting).count() == 0:
            defaults = [
                TaskSetting(task_key="review", is_required=True, xp_value=2, is_active=True),
                TaskSetting(task_key="daily_words", is_required=False, xp_value=5, is_active=True),
                TaskSetting(task_key="academy", is_required=False, xp_value=10, is_active=True),
                TaskSetting(task_key="journal", is_required=False, xp_value=10, is_active=True),
                TaskSetting(task_key="creative_writing", is_required=False, xp_value=10, is_active=False),
            ]
            db.add_all(defaults)
            print("Seeded default task settings.")

        if db.query(RewardItem).count() == 0:
            now = datetime.now().isoformat()
            rewards = [
                RewardItem(name="YouTube 30min", icon="📺", price=300, discount_pct=0, is_active=True, created_at=now),
                RewardItem(name="Roblox 30min", icon="🎮", price=300, discount_pct=0, is_active=True, created_at=now),
                RewardItem(name="Family Movie", icon="🎬", price=500, discount_pct=0, is_active=True, created_at=now),
                RewardItem(name="Dinner Out", icon="🍽️", price=500, discount_pct=0, is_active=True, created_at=now),
                RewardItem(name="Custom Reward", icon="🎁", price=300, discount_pct=0, is_active=True, created_at=now),
            ]
            db.add_all(rewards)
            print("Seeded default reward items.")

        db.commit()
    finally:
        db.close()

    print("Migration 001 complete.")

if __name__ == "__main__":
    run_migration()
