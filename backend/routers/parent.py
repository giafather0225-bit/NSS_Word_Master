"""
routers/parent.py — Parent Dashboard API
Section: Parent
Dependencies: models.py (AppConfig, TaskSetting, AcademySchedule, DayOffRequest,
              RewardItem, LearningLog, WordAttempt),
              services/xp_engine.py, services/streak_engine.py
API: GET /api/parent/overview, GET /api/parent/word-stats,
     PUT /api/parent/task-settings/{key},
     POST /api/parent/academy-schedule,
     POST /api/parent/config,
     GET /api/parent/day-off-requests,
     PUT /api/parent/day-off-requests/{id}
"""

import logging
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import (AppConfig, TaskSetting, AcademySchedule,
                          DayOffRequest, RewardItem, LearningLog, WordAttempt)
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import (AppConfig, TaskSetting, AcademySchedule,
                        DayOffRequest, RewardItem, LearningLog, WordAttempt)
    from services import xp_engine, streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_PIN = "0000"
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ─── Schemas ──────────────────────────────────────────────────

class TaskSettingUpdate(BaseModel):
    is_required: bool | None = None
    xp_value:    int  | None = None
    is_active:   bool | None = None


class AcademyScheduleIn(BaseModel):
    days: list[int]   # 0=Mon … 6=Sun
    memo: str = ""


class ConfigIn(BaseModel):
    key:   str
    value: str


class DayOffDecisionIn(BaseModel):
    status:          str   # "approved" | "denied"
    parent_response: str = ""


class PinVerifyIn(BaseModel):
    pin: str


# ─── PIN verification ──────────────────────────────────────────

def _get_stored_pin(db: Session) -> str:
    """Read the active parent PIN from AppConfig, falling back to DEFAULT_PIN."""
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    return row.value if (row and row.value) else DEFAULT_PIN


# @tag PARENT PIN
def require_parent_pin(
    x_parent_pin: str | None = Header(default=None, alias="X-Parent-Pin"),
    db: Session = Depends(get_db),
) -> bool:
    """
    FastAPI dependency that guards parent mutation endpoints.

    Frontend MUST send the verified PIN in the `X-Parent-Pin` request header
    on every mutating call (PUT/POST). The PIN is checked against AppConfig
    and rejected with 403 if missing or wrong. Read-only GET endpoints can
    still be called without a PIN — only mutations require it.

    This closes the gap where /api/parent/config etc. previously accepted
    any unauthenticated caller and could even let the child reset their own
    parent PIN via the browser console.
    """
    correct = _get_stored_pin(db)
    if not x_parent_pin or x_parent_pin != correct:
        raise HTTPException(status_code=403, detail="Parent PIN required")
    return True


@router.post("/api/parent/verify-pin")
def parent_verify_pin(body: PinVerifyIn, db: Session = Depends(get_db)):
    """
    Verify the parent PIN. Returns ok:true on success.
    @tag PARENT PIN
    """
    if body.pin != _get_stored_pin(db):
        raise HTTPException(status_code=403, detail="Wrong PIN")
    return {"ok": True}


# ─── Overview ─────────────────────────────────────────────────

@router.get("/api/parent/overview")
def parent_overview(db: Session = Depends(get_db)):
    """
    Return summary stats for the parent overview screen.
    @tag PARENT WORD_STATS
    """
    total_xp  = xp_engine.get_total_xp(db)
    today_xp  = xp_engine.get_today_xp(db)
    streak    = streak_engine.get_current_streak(db)
    words_known = xp_engine.get_words_known(db)

    # Recent 7-day learning activity
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    recent_logs = (
        db.query(LearningLog)
        .filter(LearningLog.completed_at >= week_ago)
        .order_by(LearningLog.completed_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_xp":    total_xp,
        "today_xp":    today_xp,
        "streak":      streak,
        "words_known": words_known,
        "recent_logs": [
            {
                "lesson":        log.lesson,
                "stage":         log.stage,
                "correct_count": log.correct_count,
                "word_count":    log.word_count,
                "duration_sec":  log.duration_sec,
                "completed_at":  (log.completed_at or "")[:10],
            }
            for log in recent_logs
        ],
    }


# ─── Word Stats ────────────────────────────────────────────────

@router.get("/api/parent/word-stats")
def parent_word_stats(db: Session = Depends(get_db)):
    """
    Return top wrong words from word_attempts (error pattern analysis).
    @tag PARENT WORD_STATS
    """
    # Top 20 most-missed words. SQLite has no native bool→int cast, so use CASE.
    wrong_expr = func.sum(case((WordAttempt.is_correct == False, 1), else_=0))  # noqa: E712
    top_wrong = (
        db.query(
            WordAttempt.word,
            WordAttempt.lesson,
            func.count(WordAttempt.id).label("attempts"),
            wrong_expr.label("wrong_count"),
        )
        .group_by(WordAttempt.word, WordAttempt.lesson)
        .having(wrong_expr > 0)
        .order_by(wrong_expr.desc())
        .limit(20)
        .all()
    )

    return {
        "top_wrong": [
            {
                "word":        row.word,
                "lesson":      row.lesson,
                "attempts":    row.attempts,
                "wrong_count": row.wrong_count,
                "accuracy":    round((row.attempts - row.wrong_count) / max(row.attempts, 1), 2),
            }
            for row in top_wrong
        ]
    }


# ─── Task Settings ────────────────────────────────────────────

@router.get("/api/parent/task-settings")
def parent_task_settings(db: Session = Depends(get_db)):
    """Return all task settings. @tag PARENT SETTINGS"""
    tasks = db.query(TaskSetting).order_by(TaskSetting.id).all()
    return {"tasks": [{"task_key": t.task_key, "is_required": t.is_required,
                        "xp_value": t.xp_value, "is_active": t.is_active} for t in tasks]}


@router.put("/api/parent/task-settings/{key}")
def parent_update_task(
    key: str,
    body: TaskSettingUpdate,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Update a task setting. PIN-protected. @tag PARENT SETTINGS"""
    task = db.query(TaskSetting).filter(TaskSetting.task_key == key).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if body.is_required is not None: task.is_required = body.is_required
    if body.xp_value    is not None: task.xp_value    = body.xp_value
    if body.is_active   is not None: task.is_active   = body.is_active
    db.commit()
    return {"ok": True}


# ─── Academy Schedule ─────────────────────────────────────────

@router.get("/api/parent/academy-schedule")
def parent_get_schedule(db: Session = Depends(get_db)):
    """Return active academy schedule days. @tag PARENT SCHEDULE"""
    rows = db.query(AcademySchedule).filter(AcademySchedule.is_active == True).all()
    return {"days": [{"day_of_week": r.day_of_week, "memo": r.memo or ""} for r in rows]}


@router.post("/api/parent/academy-schedule")
def parent_set_schedule(
    body: AcademyScheduleIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Replace academy schedule with new day list. PIN-protected. @tag PARENT SCHEDULE"""
    db.query(AcademySchedule).update({"is_active": False})
    for day in body.days:
        existing = db.query(AcademySchedule).filter(AcademySchedule.day_of_week == day).first()
        if existing:
            existing.is_active = True
            existing.memo = body.memo
        else:
            db.add(AcademySchedule(day_of_week=day, memo=body.memo, is_active=True))
    db.commit()
    return {"ok": True}


# ─── Config (PIN, email) ──────────────────────────────────────

@router.post("/api/parent/config")
def parent_set_config(
    body: ConfigIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Set an AppConfig key/value (e.g. PIN). PIN-protected. @tag PARENT SETTINGS PIN"""
    if body.key == "pin" and (not body.value.isdigit() or len(body.value) != 4):
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")
    row = db.query(AppConfig).filter(AppConfig.key == body.key).first()
    now = datetime.now().isoformat()
    if row:
        row.value = body.value
        row.updated_at = now
    else:
        db.add(AppConfig(key=body.key, value=body.value, updated_at=now))
    db.commit()
    return {"ok": True}


# ─── Day Off Requests ─────────────────────────────────────────

@router.get("/api/parent/day-off-requests")
def parent_day_off_list(db: Session = Depends(get_db)):
    """Return all day-off requests ordered by date DESC. @tag PARENT DAY_OFF"""
    rows = db.query(DayOffRequest).order_by(DayOffRequest.request_date.desc()).all()
    return {"requests": [
        {"id": r.id, "request_date": r.request_date, "reason": r.reason,
         "status": r.status, "parent_response": r.parent_response or ""}
        for r in rows
    ]}


@router.put("/api/parent/day-off-requests/{req_id}")
def parent_decide_day_off(
    req_id: int,
    body: DayOffDecisionIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Approve or deny a day-off request. PIN-protected. @tag PARENT DAY_OFF"""
    if body.status not in ("approved", "denied"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'denied'")
    row = db.query(DayOffRequest).filter(DayOffRequest.id == req_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    row.status = body.status
    row.parent_response = body.parent_response
    db.commit()
    return {"ok": True}
