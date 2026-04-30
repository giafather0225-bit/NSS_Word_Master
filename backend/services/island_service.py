"""
services/island_service.py — Evolution validation, execution, and zone unlock logic.
Section: Island
Dependencies: models.island, models.system, services.lumi_engine
API endpoints: called by routers/island.py
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.island import (
    IslandCharacter,
    IslandCharacterProgress,
    IslandCareLog,
    IslandInventory,
    IslandShopItem,
)
from backend.models.system import AppConfig


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Which stages may use which stone_type.
_STONE_ALLOWED_STAGES: dict[str, list[str]] = {
    "first_a":        ["baby"],
    "first_b":        ["baby"],
    "second":         ["mid_a", "mid_b"],
    "legend_first_a": ["baby"],
    "legend_first_b": ["baby"],
    "legend_second":  ["mid_a", "mid_b"],
}

# Resulting stage after evolution.
_NEXT_STAGE: dict[tuple[str, str], str] = {
    ("baby",  "first_a"):        "mid_a",
    ("baby",  "first_b"):        "mid_b",
    ("mid_a", "second"):         "final_a",
    ("mid_b", "second"):         "final_b",
    ("baby",  "legend_first_a"): "mid_a",
    ("baby",  "legend_first_b"): "mid_b",
    ("mid_a", "legend_second"):  "final_a",
    ("mid_b", "legend_second"):  "final_b",
}

# Minimum level required before using each stone group.
_MIN_LEVEL: dict[str, int] = {
    "first_a":        5,
    "first_b":        5,
    "second":         10,
    "legend_first_a": 5,
    "legend_first_b": 5,
    "legend_second":  10,
}

_FINAL_STAGES = {"final_a", "final_b"}
_LEGEND_STONES = {"legend_first_a", "legend_first_b", "legend_second"}


class EvolutionError(Exception):
    """Raised when evolution validation fails."""


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_inventory_stone(
    db: Session, stone_type: str
) -> Optional[IslandInventory]:
    """Return the first inventory row for this stone_type with quantity > 0."""
    return (
        db.query(IslandInventory)
        .join(IslandShopItem, IslandInventory.shop_item_id == IslandShopItem.id)
        .filter(
            IslandShopItem.evolution_type == stone_type,
            IslandInventory.item_type == "evolution",
            IslandInventory.quantity > 0,
        )
        .first()
    )


def _rebuild_boost_cache(db: Session) -> None:
    """Recalculate XP boost percentages from all completed characters and cache in app_config."""
    rows = (
        db.query(IslandCharacterProgress, IslandCharacter)
        .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
        .filter(
            IslandCharacterProgress.is_completed == True,
            IslandCharacterProgress.boost_active == True,
        )
        .all()
    )

    boosts: dict[str, float] = {"english": 0.0, "math": 0.0, "diary": 0.0, "review": 0.0}

    for prog, char in rows:
        # A-branch: base + a_pct bonus. B-branch: base only (b_pct = extra lumi, not XP).
        boost = char.xp_boost_pct + (char.xp_boost_a_pct if prog.stage == "final_a" else 0.0)
        subject = char.subject
        if subject == "all":
            for s in boosts:
                boosts[s] += boost
        elif subject in boosts:
            boosts[subject] += boost

    total = sum(boosts.values())

    for key, value in [
        ("lumi_boost_total",   total),
        ("lumi_boost_english", boosts["english"]),
        ("lumi_boost_math",    boosts["math"]),
        ("lumi_boost_diary",   boosts["diary"]),
        ("lumi_boost_review",  boosts["review"]),
    ]:
        cfg = db.query(AppConfig).filter_by(key=key).first()
        if cfg:
            cfg.value = str(value)
        else:
            db.add(AppConfig(key=key, value=str(value)))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
def validate_evolution(
    db: Session, character_progress_id: int, stone_type: str
) -> dict:
    """
    Validate whether the character can evolve with the given stone.

    Checks (in order):
      1. stone_type is recognized
      2. Current stage is compatible with stone_type
      3. Level meets minimum requirement
      4. Gauge condition (hunger AND happiness >= 20) — skipped for legend types
      5. Branch mismatch (mid_a + *_b stone or mid_b + *_a stone)
      6. Legend type uses legend stone, normal uses normal stone
      7. Inventory contains at least one matching stone

    Returns:
        {"valid": True, "next_stage": "<stage>", "message": "OK"}

    Raises:
        EvolutionError: with a human-readable message describing the failure
    """
    if stone_type not in _STONE_ALLOWED_STAGES:
        raise EvolutionError(f"Unknown stone type: '{stone_type}'")

    prog = db.get(IslandCharacterProgress, character_progress_id)
    if prog is None:
        raise EvolutionError("Character progress not found.")

    # 1. Stage compatibility.
    allowed_stages = _STONE_ALLOWED_STAGES[stone_type]
    if prog.stage not in allowed_stages:
        raise EvolutionError(
            f"This stone requires the character to be in stage "
            f"{' or '.join(allowed_stages)}, but it is currently '{prog.stage}'."
        )

    # 2. Level requirement.
    min_level = _MIN_LEVEL[stone_type]
    if prog.level < min_level:
        raise EvolutionError(
            f"Character must reach Level {min_level} before evolving "
            f"(currently Level {prog.level})."
        )

    # 3. Gauge condition (non-legend only).
    if not prog.is_legend_type:
        if prog.hunger < 20 or prog.happiness < 20:
            low = []
            if prog.hunger < 20:
                low.append(f"Hunger ({prog.hunger})")
            if prog.happiness < 20:
                low.append(f"Happiness ({prog.happiness})")
            raise EvolutionError(
                f"Both gauges must be at least 20 to evolve. "
                f"Low: {', '.join(low)}."
            )

    # 4. Branch mismatch (relevant for mid-stage + first_* stones — already
    #    caught by stage check above, but guard against mid_a/mid_b + wrong branch).
    if prog.stage == "mid_a" and stone_type in ("first_b", "legend_first_b"):
        raise EvolutionError(
            "This character evolved on the A branch. Use the 2nd Evolution Stone to continue."
        )
    if prog.stage == "mid_b" and stone_type in ("first_a", "legend_first_a"):
        raise EvolutionError(
            "This character evolved on the B branch. Use the 2nd Evolution Stone to continue."
        )

    # 5. Legend type ↔ stone family check.
    if prog.is_legend_type and stone_type not in _LEGEND_STONES:
        raise EvolutionError("Legend characters require Legend Evolution Stones.")
    if not prog.is_legend_type and stone_type in _LEGEND_STONES:
        raise EvolutionError("Regular characters cannot use Legend Evolution Stones.")

    # 6. Inventory check.
    inv_row = _get_inventory_stone(db, stone_type)
    if inv_row is None:
        raise EvolutionError(
            f"You don't have a {stone_type.replace('_', ' ').title()} in your inventory."
        )

    next_stage = _NEXT_STAGE[(prog.stage, stone_type)]
    return {"valid": True, "next_stage": next_stage, "message": "OK"}


# @tag ISLAND
def execute_evolution(
    db: Session, character_progress_id: int, stone_type: str
) -> dict:
    """
    Execute evolution after passing validation.

    Steps:
      1. validate_evolution (raises EvolutionError on failure)
      2. Advance stage
      3. Consume one stone from inventory
      4. If final stage: set is_completed, boost_active, boost_subject; rebuild boost cache
      5. Log "evolve" action to island_care_log
      6. db.flush()

    Returns:
        {
            "character_progress_id": int,
            "previous_stage": str,
            "new_stage": str,
            "is_completed": bool,
            "boost_subject": str,
        }
    """
    result = validate_evolution(db, character_progress_id, stone_type)
    next_stage = result["next_stage"]

    prog = db.get(IslandCharacterProgress, character_progress_id)
    char = db.get(IslandCharacter, prog.character_id)

    previous_stage = prog.stage
    prog.stage = next_stage

    # Consume stone from inventory.
    inv_row = _get_inventory_stone(db, stone_type)
    inv_row.quantity -= 1
    inv_row.used_on_character_progress_id = character_progress_id

    # Handle completion.
    is_completed = next_stage in _FINAL_STAGES
    if is_completed:
        prog.is_completed = True
        prog.completed_at = datetime.now(timezone.utc)
        prog.boost_active = True
        prog.boost_subject = char.subject
        _rebuild_boost_cache(db)

    # Care-log entry.
    db.add(IslandCareLog(
        character_progress_id=character_progress_id,
        action="evolve",
        hunger_change=0,
        happiness_change=0,
        source="evolution",
        logged_at=datetime.now(timezone.utc),
    ))

    db.flush()

    return {
        "character_progress_id": character_progress_id,
        "previous_stage": previous_stage,
        "new_stage": next_stage,
        "is_completed": is_completed,
        "boost_subject": prog.boost_subject,
    }


# @tag ISLAND
def get_next_unlock(db: Session, zone: str) -> Optional[dict]:
    """
    Return the next adoptable character in the zone.

    A character is adoptable when:
    - Its prerequisite character (unlock_requires_character_id) has at least
      one completed progress row (or has no prerequisite)
    - It has no currently active (non-completed) progress row

    Returns None when all characters in the zone are either active or fully adopted.
    """
    chars = (
        db.query(IslandCharacter)
        .filter(
            IslandCharacter.zone == zone,
            IslandCharacter.is_available == True,
        )
        .order_by(IslandCharacter.order_index)
        .all()
    )

    for char in chars:
        # Check prerequisite.
        if char.unlock_requires_character_id is not None:
            prereq_done = (
                db.query(IslandCharacterProgress)
                .filter(
                    IslandCharacterProgress.character_id == char.unlock_requires_character_id,
                    IslandCharacterProgress.is_completed == True,
                )
                .first()
            )
            if prereq_done is None:
                continue  # prerequisite not yet met

        # Skip if this character already has an active in-progress row.
        active = (
            db.query(IslandCharacterProgress)
            .filter(
                IslandCharacterProgress.character_id == char.id,
                IslandCharacterProgress.is_active == True,
                IslandCharacterProgress.is_completed == False,
            )
            .first()
        )
        if active is not None:
            continue

        return {
            "character_id": char.id,
            "name": char.name,
            "zone": char.zone,
            "subject": char.subject,
            "order_index": char.order_index,
            "description": char.description,
            "lumi_production": char.lumi_production,
        }

    return None
