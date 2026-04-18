"""
routers/xp.py — XP system, Streak, and Today's Tasks API
Section: System
Dependencies: services/xp_engine.py, services/streak_engine.py,
              models.py (XPLog, StreakLog, TaskSetting, DiaryEntry, DailyWordsProgress)
API:
  GET  /api/xp/summary
  POST /api/xp/award
  GET  /api/streak/status
  GET  /api/tasks/today
"""

from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import (
    TaskSetting,
    DiaryEntry,
    DailyWordsProgress,
    StreakLog,
    XPLog,
    WordReview,
)
from backend.services.xp_engine import (
    award_xp,
    get_total_xp,
    get_today_xp,
    get_words_known,
    XP_RULES,
)
from backend.services.streak_engine import (
    get_or_create_streak_log,
    get_current_streak,
    mark_review_done,
    mark_daily_words_done,
    check_streak_bonus,
)

router = APIRouter()


class AwardXPRequest(BaseModel):
    """Request body for POST /api/xp/award."""

    action: str
    detail: str = ""


# @tag XP
@router.get("/api/xp/summary")
def xp_summary(db: Session = Depends(get_db)) -> dict:
    """Return total XP, today's XP, current streak, and mastered word count.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        Dict with total_xp, today_xp, streak_days, words_known.
    """
    streak = get_current_streak(db)
    total = get_total_xp(db)
    return {
        "total_xp": total,
        "today_xp": get_today_xp(db),
        "level": total // 100 + 1,
        "streak_days": streak,
        "words_known": get_words_known(db),
    }


# @tag XP @tag AWARD
@router.post("/api/xp/award")
def award_xp_endpoint(
    body: AwardXPRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Award XP for an action. Returns xp_awarded (0 if already awarded today).

    Also checks for streak milestone bonuses.
    Side-effects: may also award streak_7_bonus or streak_30_bonus.

    Args:
        body: AwardXPRequest with action and optional detail.
        db: Injected SQLAlchemy session.

    Returns:
        Dict with xp_awarded, bonus_xp, total_xp, streak_days.

    Raises:
        HTTPException 400: if action is not in XP_RULES.
    """
    if body.action not in XP_RULES:
        raise HTTPException(status_code=400, detail=f"Unknown action: {body.action}")

    xp = award_xp(db, body.action, body.detail)

    # Handle side-effects
    today = date.today().isoformat()
    if body.action == "review_complete":
        mark_review_done(db, today)
    elif body.action == "daily_words_complete":
        mark_daily_words_done(db, today)

    # Check streak bonus
    bonus_xp = 0
    streak = get_current_streak(db)
    bonus_action = check_streak_bonus(db, streak)
    if bonus_action:
        bonus_xp = award_xp(db, bonus_action)

    total = get_total_xp(db)
    return {
        "xp_awarded": xp,
        "bonus_xp": bonus_xp,
        "total_xp": total,
        "level": total // 100 + 1,
        "streak_days": streak,
    }


# @tag STREAK
@router.get("/api/streak/status")
def streak_status(db: Session = Depends(get_db)) -> dict:
    """Return current streak info and today's completion status.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        Dict with streak_days, today_review_done, today_daily_words_done,
        today_streak_maintained.
    """
    today = date.today().isoformat()
    log = db.query(StreakLog).filter(StreakLog.date == today).first()
    streak = get_current_streak(db)
    return {
        "streak_days": streak,
        "today_review_done": log.review_done if log else False,
        "today_daily_words_done": log.daily_words_done if log else False,
        "today_streak_maintained": log.streak_maintained if log else False,
    }


def _make_task(
    key: str,
    label: str,
    detail: str,
    is_done: bool,
    settings: dict,
) -> dict:
    """Build a single task dict from settings and completion state.

    Args:
        key: Task key (e.g. "review", "daily_words").
        label: Human-readable label.
        detail: Progress string (e.g. "5/10").
        is_done: Whether task is completed today.
        settings: Dict mapping task_key → TaskSetting row.

    Returns:
        Task dict with key, label, detail, xp, is_required, is_done.
    """
    s = settings.get(key)
    return {
        "key": key,
        "label": label,
        "detail": detail,
        "xp": s.xp_value if s else XP_RULES.get(key.replace("-", "_"), 0),
        "is_required": s.is_required if s else False,
        "is_done": is_done,
    }


# @tag TODAY_TASKS @tag XP
@router.get("/api/tasks/today")
def tasks_today(db: Session = Depends(get_db)) -> list:
    """Return today's task list with completion status.

    Task completion is derived from:
    - review: StreakLog.review_done
    - daily_words: StreakLog.daily_words_done
    - academy: any XPLog with action='stage_complete' today
    - journal: DiaryEntry for today

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        List of task dicts (key, label, detail, xp, is_required, is_done).
    """
    today = date.today().isoformat()
    streak_log = db.query(StreakLog).filter(StreakLog.date == today).first()

    # Check completions
    academy_done = (
        db.query(XPLog)
        .filter(XPLog.action == "stage_complete", XPLog.earned_date == today)
        .first()
    ) is not None

    journal_done = (
        db.query(DiaryEntry).filter(DiaryEntry.entry_date == today).first()
    ) is not None

    daily_words_progress = (
        db.query(DailyWordsProgress)
        .filter(DailyWordsProgress.last_study_date == today)
        .first()
    )
    daily_words_done = streak_log.daily_words_done if streak_log else False
    daily_words_count = (
        daily_words_progress.daily_learned if daily_words_progress else 0
    )

    settings: dict[str, TaskSetting] = {
        s.task_key: s
        for s in db.query(TaskSetting).filter(TaskSetting.is_active == True).all()
    }

    tasks: list[dict] = []

    if "review" in settings:
        review_due_count = (
            db.query(WordReview)
            .filter(WordReview.next_review <= today)
            .count()
        )
        tasks.append(
            _make_task(
                "review",
                "Review",
                f"{review_due_count} words" if review_due_count else "No words due",
                streak_log.review_done if streak_log else False,
                settings,
            )
        )
    if "daily_words" in settings:
        tasks.append(
            _make_task(
                "daily_words",
                "Daily Words",
                f"{daily_words_count}/10",
                daily_words_done,
                settings,
            )
        )
    if "academy" in settings:
        tasks.append(
            _make_task("academy", "Academy", "", academy_done, settings)
        )
    if "journal" in settings:
        tasks.append(
            _make_task("journal", "Daily Journal", "", journal_done, settings)
        )

    # Any other active task keys not handled above
    handled = {"review", "daily_words", "academy", "journal"}
    for key, s in settings.items():
        if key not in handled and s.is_active:
            tasks.append(
                _make_task(
                    key,
                    key.replace("_", " ").title(),
                    "",
                    False,
                    settings,
                )
            )

    # Auto-award daily bonuses (XPLog daily-dedup makes this idempotent).
    # Why: bonus rules existed in XP_RULES but no caller wired them in.
    if tasks:
        required = [t for t in tasks if t["is_required"]]
        if required and all(t["is_done"] for t in required):
            award_xp(db, "must_do_bonus")
        if all(t["is_done"] for t in tasks):
            award_xp(db, "all_complete_bonus")

    return tasks
