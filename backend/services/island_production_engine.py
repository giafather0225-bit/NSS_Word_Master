"""
services/island_production_engine.py — Completed character daily Lumi production.
Section: Island
Dependencies: models.island, services.lumi_engine
API endpoints: called by main.py lifespan (alongside island_care_engine.run_daily_batch)
"""

from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.island import (
    IslandCharacter,
    IslandCharacterProgress,
    IslandLumiLog,
)
from backend.services.lumi_engine import earn_lumi


def _today() -> date:
    return datetime.now(timezone.utc).date()


# @tag ISLAND @tag AWARD
def run_daily_production(db: Session) -> dict:
    """
    Award Lumi from all completed characters that haven't produced today.

    Runs as a single transaction (called from main.py lifespan after
    island_care_engine.run_daily_batch). Uses island_characters.lumi_production
    from the DB — legend characters already have 20 seeded there.

    Returns:
        {"produced": <total_lumi>, "characters": <count_processed>, "skipped": <count>}
    """
    today_str = str(_today())
    today_date = _today()

    # Join progress → character to get lumi_production in one query.
    rows = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(
            IslandCharacter,
            IslandCharacterProgress.character_id == IslandCharacter.id,
        )
        .filter(
            IslandCharacterProgress.is_completed == True,
            IslandCharacterProgress.is_active == True,
        )
        .all()
    )

    total_lumi = 0
    processed = 0
    skipped = 0

    for prog, char in rows:
        if prog.last_production_date == today_str:
            skipped += 1
            continue

        amount = char.lumi_production
        if amount <= 0:
            skipped += 1
            continue

        earn_lumi(
            db,
            source="production",
            amount=amount,
            character_progress_id=prog.id,
            earned_date=today_date,
        )

        prog.last_production_date = today_str
        total_lumi += amount
        processed += 1

    db.flush()
    return {"produced": total_lumi, "characters": processed, "skipped": skipped}


# @tag ISLAND
def get_production_summary(db: Session) -> dict:
    """
    Return total Lumi produced today from completed characters.

    Returns:
        {"today": <lumi_total>, "date": "<YYYY-MM-DD>"}
    """
    today = _today()

    total = (
        db.query(func.sum(IslandLumiLog.amount))
        .filter(
            IslandLumiLog.source == "production",
            IslandLumiLog.earned_date == today,
            IslandLumiLog.amount > 0,
        )
        .scalar()
    ) or 0

    return {"today": total, "date": str(today)}
