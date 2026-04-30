"""
services/island_care_engine.py — Character gauge decay and study-gain logic.
Section: Island
Dependencies: models.island
API endpoints: called by study/math/diary/review routers + main.py lifespan
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.island import IslandCharacter, IslandCharacterProgress, IslandCareLog

# ─────────────────────────────────────────────────────────────────────────────
# Study-gain table (ISLAND_SPEC §5.2)
# ─────────────────────────────────────────────────────────────────────────────

_STUDY_GAINS: dict[str, tuple[int, int]] = {
    # source: (hunger_delta, happiness_delta)
    "english_stage":      (20,  0),
    "english_final_test": (30, 30),
    "math_lesson":        (20,  0),
    "math_unit_test":     (30, 30),
    "diary":              (25, 20),
    "review":             (20, 15),
    "streak":             ( 0, 10),   # applied to all active characters
    "legend_4subject":    ( 0, 20),   # applied to legend characters only
}

_HUNGER_DECAY_PER_DAY = 15
_HAPPINESS_DECAY_PER_NO_STUDY_BLOCK = 20  # once per 2-day block of no study


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _last_study_date(db: Session, character_progress_id: int) -> Optional[date]:
    """Return the date of the most recent feed/play care-log entry, or None."""
    row = (
        db.query(IslandCareLog)
        .filter(
            IslandCareLog.character_progress_id == character_progress_id,
            IslandCareLog.action.in_(["feed", "play"]),
        )
        .order_by(IslandCareLog.logged_at.desc())
        .first()
    )
    if row is None:
        return None
    return row.logged_at.date() if hasattr(row.logged_at, "date") else row.logged_at


def _log_care(
    db: Session,
    character_progress_id: int,
    action: str,
    hunger_change: int,
    happiness_change: int,
    source: str,
) -> None:
    db.add(IslandCareLog(
        character_progress_id=character_progress_id,
        action=action,
        hunger_change=hunger_change,
        happiness_change=happiness_change,
        source=source,
        logged_at=datetime.now(timezone.utc),
    ))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# @tag ISLAND
def apply_decay(db: Session, character_progress_id: int) -> dict:
    """
    Calculate gauge decay since last_decay_date and apply it.

    - Hunger:    elapsed_days × -15  (min 0)
    - Happiness: -20 per 2-day block of no study after the first study-free day
    - Skipped for: is_completed=True or is_legend_type=True characters

    Returns:
        {"hunger": <new>, "happiness": <new>,
         "hunger_change": <delta>, "happiness_change": <delta>,
         "elapsed_days": <int>}
    """
    prog = db.get(IslandCharacterProgress, character_progress_id)
    if prog is None:
        raise ValueError(f"CharacterProgress {character_progress_id} not found")

    today = _today()
    result = {
        "hunger": prog.hunger,
        "happiness": prog.happiness,
        "hunger_change": 0,
        "happiness_change": 0,
        "elapsed_days": 0,
    }

    # Completed or legend characters skip gauge decay.
    if prog.is_completed or prog.is_legend_type:
        prog.last_decay_date = str(today)
        db.flush()
        return result

    # Calculate elapsed days since last decay.
    last_decay = (
        date.fromisoformat(prog.last_decay_date)
        if prog.last_decay_date
        else today
    )
    elapsed_days = (today - last_decay).days
    if elapsed_days <= 0:
        return result

    # ── Hunger decay ──────────────────────────────────────────────────────
    hunger_delta = -(elapsed_days * _HUNGER_DECAY_PER_DAY)
    new_hunger = _clamp(prog.hunger + hunger_delta)
    actual_hunger_change = new_hunger - prog.hunger

    # ── Happiness decay ───────────────────────────────────────────────────
    # Find how many days have passed without any study activity.
    last_study = _last_study_date(db, character_progress_id)
    if last_study is None:
        # Never studied — treat adopted_at as the last "safe" date.
        last_study = prog.adopted_at.date() if hasattr(prog.adopted_at, "date") else today

    no_study_days = (today - last_study).days
    # -20 per complete 2-day block of no study (first day is free).
    happiness_decay_events = max(0, (no_study_days - 1) // 2) if no_study_days >= 2 else 0
    # Only count events within the current elapsed window.
    max_events = elapsed_days // 2
    happiness_decay_events = min(happiness_decay_events, max_events)
    happiness_delta = -(happiness_decay_events * _HAPPINESS_DECAY_PER_NO_STUDY_BLOCK)
    new_happiness = _clamp(prog.happiness + happiness_delta)
    actual_happiness_change = new_happiness - prog.happiness

    # ── Apply ─────────────────────────────────────────────────────────────
    prog.hunger = new_hunger
    prog.happiness = new_happiness
    prog.last_decay_date = str(today)

    if actual_hunger_change != 0 or actual_happiness_change != 0:
        _log_care(
            db,
            character_progress_id=character_progress_id,
            action="decay",
            hunger_change=actual_hunger_change,
            happiness_change=actual_happiness_change,
            source="auto_decay",
        )

    db.flush()

    result.update({
        "hunger": new_hunger,
        "happiness": new_happiness,
        "hunger_change": actual_hunger_change,
        "happiness_change": actual_happiness_change,
        "elapsed_days": elapsed_days,
    })
    return result


# @tag ISLAND
def apply_study_gain(
    db: Session,
    character_progress_id: int,
    source: str,
) -> dict:
    """
    Increase hunger/happiness gauges after a study activity.

    source must be one of: english_stage, english_final_test, math_lesson,
    math_unit_test, diary, review, streak, legend_4subject.

    Returns:
        {"hunger": <new>, "happiness": <new>,
         "hunger_change": <delta>, "happiness_change": <delta>}
    """
    gains = _STUDY_GAINS.get(source)
    if gains is None:
        raise ValueError(f"apply_study_gain: unknown source '{source}'")

    prog = db.get(IslandCharacterProgress, character_progress_id)
    if prog is None:
        raise ValueError(f"CharacterProgress {character_progress_id} not found")

    # Legend characters ignore hunger/happiness — gauge ops are no-ops.
    if prog.is_legend_type:
        return {"hunger": prog.hunger, "happiness": prog.happiness,
                "hunger_change": 0, "happiness_change": 0}

    # Completed characters keep their gauges maxed; gains still apply (no decay).
    hunger_delta, happiness_delta = gains

    new_hunger = _clamp(prog.hunger + hunger_delta)
    new_happiness = _clamp(prog.happiness + happiness_delta)
    actual_hunger_change = new_hunger - prog.hunger
    actual_happiness_change = new_happiness - prog.happiness

    prog.hunger = new_hunger
    prog.happiness = new_happiness

    action = "feed" if hunger_delta > 0 else "play"
    if happiness_delta > 0 and hunger_delta == 0:
        action = "play"

    _log_care(
        db,
        character_progress_id=character_progress_id,
        action=action,
        hunger_change=actual_hunger_change,
        happiness_change=actual_happiness_change,
        source=source,
    )

    db.flush()
    return {
        "hunger": new_hunger,
        "happiness": new_happiness,
        "hunger_change": actual_hunger_change,
        "happiness_change": actual_happiness_change,
    }


# @tag ISLAND @tag XP
def get_xp_multiplier(db: Session, character_progress_id: int) -> float:
    """
    Return XP multiplier based on current gauge levels (ISLAND_SPEC §4.3).

    - Both >= 60:      1.0
    - One < 60:        0.8
    - One < 20:        0.6
    - Both < 20:       0.2
    - Legend type:     1.0 (no gauge penalty)
    - Completed:       1.0 (permanent residents)
    """
    prog = db.get(IslandCharacterProgress, character_progress_id)
    if prog is None:
        return 1.0

    if prog.is_legend_type or prog.is_completed:
        return 1.0

    h, hp = prog.hunger, prog.happiness

    if h < 20 and hp < 20:
        return 0.2
    if h < 20 or hp < 20:
        return 0.6
    if h < 60 or hp < 60:
        return 0.8
    return 1.0


# @tag ISLAND
def run_daily_batch(db: Session) -> dict:
    """
    Run decay for all active, non-completed characters.
    Called at app startup (main.py lifespan).

    Returns:
        {"processed": <count>, "skipped": <count>}
    """
    active_chars = (
        db.query(IslandCharacterProgress)
        .filter(
            IslandCharacterProgress.is_active == True,
            IslandCharacterProgress.is_completed == False,
        )
        .all()
    )

    processed = 0
    skipped = 0
    today_str = str(_today())

    for prog in active_chars:
        # Skip if decay already ran today.
        if prog.last_decay_date == today_str:
            skipped += 1
            continue
        try:
            apply_decay(db, prog.id)
            processed += 1
        except Exception:
            skipped += 1

    db.flush()
    return {"processed": processed, "skipped": skipped}


# @tag ISLAND
def apply_subject_gain(db: Session, subject: str, source: str) -> dict:
    """
    Apply study gain to all active characters matching the given subject.

    Queries characters whose subject matches `subject` or is "all".
    Returns the XP multiplier for the currently-raising (non-completed) character.

    Returns:
        {"xp_multiplier": float}
    """
    try:
        subjects = [subject, "all"] if subject != "all" else ["all"]
        active_progs = (
            db.query(IslandCharacterProgress)
            .join(IslandCharacter, IslandCharacterProgress.character_id == IslandCharacter.id)
            .filter(
                IslandCharacter.subject.in_(subjects),
                IslandCharacterProgress.is_active == True,
            )
            .all()
        )
    except Exception:
        return {"xp_multiplier": 1.0}

    xp_multiplier = 1.0
    for prog in active_progs:
        try:
            apply_study_gain(db, prog.id, source)
        except Exception:
            pass
        if not prog.is_completed and not prog.is_legend_type:
            try:
                xp_multiplier = get_xp_multiplier(db, prog.id)
            except Exception:
                pass

    return {"xp_multiplier": xp_multiplier}
