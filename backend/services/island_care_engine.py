"""
services/island_care_engine.py — Character gauge decay and study-gain logic.
Section: Island
Dependencies: models.island
API endpoints: called by study/math/diary/review routers + main.py lifespan
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func as sqla_func, update as sqla_update
from sqlalchemy.orm import Session

from backend.models.island import (
    IslandCharacter, IslandCharacterProgress, IslandCareLog, IslandLegendProgress,
)

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

# Character XP awarded per study activity (ISLAND_SPEC §4.3).
# Legend characters use consecutive_days instead of XP → 0 here.
_CHAR_XP_GAINS: dict[str, int] = {
    "english_stage":       10,
    "english_final_test":  30,
    "math_lesson":         20,
    "math_unit_test":      50,
    "diary":               15,
    "review":              10,
    "streak":              10,
    "legend_4subject":      0,
}

# Cumulative XP thresholds per level (ISLAND_SPEC §4.2).
# Index i → Level (i+1). Lv5 = evo_first ready; Lv10 = evo_second ready.
_LEVEL_XP_THRESHOLDS: list[int] = [0, 100, 250, 450, 750, 850, 1000, 1200, 1500, 1900]

_HUNGER_DECAY_PER_DAY = 15
_HAPPINESS_DECAY_PER_NO_STUDY_BLOCK = 20  # once per 2-day block of no study

# A-form (mid_a/final_a) → hunger decay 20% slower (ISLAND_SPEC §3.6)
# B-form (mid_b/final_b) → happiness decay 20% slower (ISLAND_SPEC §3.6)
# Spec says "slower" without a specific %; 0.8 multiplier chosen as a balanced value.
_BRANCH_DECAY_MULTIPLIER = 0.8


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _calc_level(current_xp: int) -> int:
    """Return character level (1-10) for the given cumulative XP."""
    level = 1
    for i, threshold in enumerate(_LEVEL_XP_THRESHOLDS):
        if current_xp >= threshold:
            level = i + 1
        else:
            break
    return level


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _last_study_date(db: Session, character_progress_id: int) -> Optional[date]:
    """Return the date of the most recent feed/play care-log entry, or None."""
    row = (
        db.query(IslandCareLog)
        .filter(
            IslandCareLog.character_progress_id == character_progress_id,
            IslandCareLog.action.in_(["feed", "play"]),
            # Exclude shop-food events: they log action="feed" with source="food_{id}_xp{n}".
            # Those are XP boosts from inventory, not study-based feeding → must not count
            # as a "study happened" signal for happiness decay purposes.
            ~IslandCareLog.source.like("food_%"),
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

    # ── Branch-aware decay rates (ISLAND_SPEC §3.6) ───────────────────────
    # A-form: hunger decays slower; B-form: happiness decays slower.
    stage = prog.stage or "baby"
    hunger_decay_rate = (
        _HUNGER_DECAY_PER_DAY * _BRANCH_DECAY_MULTIPLIER
        if stage in ("mid_a", "final_a")
        else float(_HUNGER_DECAY_PER_DAY)
    )
    happiness_decay_rate = (
        _HAPPINESS_DECAY_PER_NO_STUDY_BLOCK * _BRANCH_DECAY_MULTIPLIER
        if stage in ("mid_b", "final_b")
        else float(_HAPPINESS_DECAY_PER_NO_STUDY_BLOCK)
    )

    # ── Hunger decay ──────────────────────────────────────────────────────
    hunger_delta = -int(elapsed_days * hunger_decay_rate)

    # ── Happiness decay ───────────────────────────────────────────────────
    # Find how many days have passed without any study activity.
    last_study = _last_study_date(db, character_progress_id)
    if last_study is None:
        # Never studied — treat adopted_at as the last "safe" date.
        last_study = prog.adopted_at.date() if hasattr(prog.adopted_at, "date") else today

    no_study_days = (today - last_study).days
    # decay_rate per complete 2-day block of no study (first day is free).
    happiness_decay_events = max(0, (no_study_days - 1) // 2) if no_study_days >= 2 else 0
    # Only count events within the current elapsed window.
    max_events = elapsed_days // 2
    happiness_decay_events = min(happiness_decay_events, max_events)
    happiness_delta = -int(happiness_decay_events * happiness_decay_rate)

    # Snapshot before-state for accurate delta calculation (guard against NULL columns).
    old_hunger    = prog.hunger    or 0
    old_happiness = prog.happiness or 0

    # ── Apply (atomic UPDATE to prevent lost-write race) ──────────────────
    db.execute(
        sqla_update(IslandCharacterProgress)
        .where(IslandCharacterProgress.id == character_progress_id)
        .values(
            hunger=sqla_func.min(100, sqla_func.max(0, IslandCharacterProgress.hunger + hunger_delta)),
            happiness=sqla_func.min(100, sqla_func.max(0, IslandCharacterProgress.happiness + happiness_delta)),
            last_decay_date=str(today),
        )
        .execution_options(synchronize_session=False)
    )
    db.refresh(prog)
    new_hunger = prog.hunger
    new_happiness = prog.happiness
    actual_hunger_change = new_hunger - old_hunger
    actual_happiness_change = new_happiness - old_happiness

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
                "hunger_change": 0, "happiness_change": 0,
                "xp_gained": 0, "level_up": False, "new_level": prog.level or 1}

    # Completed characters keep their gauges maxed; gains still apply (no decay).
    hunger_delta, happiness_delta = gains

    # Snapshot before-state for accurate delta calculation (guard against NULL columns).
    old_hunger    = prog.hunger    or 0
    old_happiness = prog.happiness or 0

    # Atomic clamped UPDATE — prevents lost-update race with concurrent requests.
    db.execute(
        sqla_update(IslandCharacterProgress)
        .where(IslandCharacterProgress.id == character_progress_id)
        .values(
            hunger=sqla_func.min(100, sqla_func.max(0, IslandCharacterProgress.hunger + hunger_delta)),
            happiness=sqla_func.min(100, sqla_func.max(0, IslandCharacterProgress.happiness + happiness_delta)),
        )
        .execution_options(synchronize_session=False)
    )
    db.refresh(prog)

    actual_hunger_change = prog.hunger - old_hunger
    actual_happiness_change = prog.happiness - old_happiness

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

    # ── Character XP update (ISLAND_SPEC §4.3) ───────────────────────────
    # Completed characters are permanent residents — no further XP needed.
    xp_gained = 0
    level_up = False
    new_level = prog.level or 1

    if not prog.is_completed:
        char_xp = _CHAR_XP_GAINS.get(source, 0)
        if char_xp > 0:
            old_level = _calc_level(prog.current_xp or 0)
            prog.current_xp = (prog.current_xp or 0) + char_xp
            xp_gained = char_xp
            new_level = _calc_level(prog.current_xp)
            if new_level > old_level:
                level_up = True
                prog.level = new_level

    db.flush()
    return {
        "hunger": prog.hunger,
        "happiness": prog.happiness,
        "hunger_change": actual_hunger_change,
        "happiness_change": actual_happiness_change,
        "xp_gained": xp_gained,
        "level_up": level_up,
        "new_level": new_level,
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

    h  = prog.hunger    or 0
    hp = prog.happiness or 0

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
    today = _today()
    today_str = str(today)

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

    # ── Legend streak break detection (ISLAND_SPEC §Legend) ──────────────────
    # If a legend character's last_completed_date was > 1 day ago, the
    # consecutive_days counter resets to 0 and happiness drops by 10.
    # This mirrors the normal-character gauge decay, but for legend chars.
    legend_broken: list[dict] = []
    yesterday = _today() - timedelta(days=1)

    legend_progs = (
        db.query(IslandLegendProgress)
        .filter(
            IslandLegendProgress.consecutive_days > 0,
            IslandLegendProgress.last_completed_date.isnot(None),
            IslandLegendProgress.last_completed_date < yesterday,
        )
        .all()
    )
    for lp in legend_progs:
        days_missed = (today - lp.last_completed_date).days - 1 if lp.last_completed_date else 0
        if days_missed <= 0:
            continue
        lp.consecutive_days = 0
        # Apply happiness -10 to the associated legend character progress row.
        char_prog = (
            db.query(IslandCharacterProgress)
            .filter(
                IslandCharacterProgress.character_id == lp.character_id,
                IslandCharacterProgress.is_legend_type == True,
                IslandCharacterProgress.is_active == True,
            )
            .first()
        )
        if char_prog:
            new_hp = max(0, (char_prog.happiness or 0) - 10)
            char_prog.happiness = new_hp
            _log_care(
                db,
                character_progress_id=char_prog.id,
                action="decay",
                hunger_change=0,
                happiness_change=-10,
                source="legend_streak_break",
            )
        legend_broken.append({
            "character_id": lp.character_id,
            "days_missed": days_missed,
        })

    if legend_broken:
        db.flush()

    return {"processed": processed, "skipped": skipped, "legend_streak_broken": legend_broken}


# @tag ISLAND
def apply_subject_gain(db: Session, subject: str, source: str) -> dict:
    """
    Apply study gain to all active characters matching the given subject.

    Queries characters whose subject matches `subject` or is "all".
    Returns the XP multiplier for the currently-raising (non-completed) character.

    Returns:
        {"xp_multiplier": float, "level_up": bool, "new_level": int}
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
        return {"xp_multiplier": 1.0, "level_up": False, "new_level": 1}

    xp_multiplier = 1.0
    aggregated_level_up = False
    aggregated_new_level = 1
    aggregated_char_xp = 0

    for prog in active_progs:
        try:
            result = apply_study_gain(db, prog.id, source)
            aggregated_char_xp += result.get("xp_gained", 0)
            if result.get("level_up"):
                aggregated_level_up = True
                aggregated_new_level = result.get("new_level", 1)
        except Exception:
            pass
        if not prog.is_completed and not prog.is_legend_type:
            try:
                xp_multiplier = get_xp_multiplier(db, prog.id)
                if not aggregated_level_up:
                    aggregated_new_level = prog.level or 1
            except Exception:
                pass

    return {
        "xp_multiplier": xp_multiplier,
        "level_up": aggregated_level_up,
        "new_level": aggregated_new_level,
        "char_xp_gained": aggregated_char_xp,
    }
