"""
routers/parent_streak.py — Parent Dashboard Streak endpoints
Section: Parent
Dependencies: models.py (AppConfig, StreakLog, DayOffRequest),
              services/streak_engine.py, routers/parent.py (shared PIN dep)
API: GET  /api/parent/streak
     POST /api/parent/streak-rule (PIN)
     POST /api/parent/streak-recalc (PIN)
"""

from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import AppConfig, StreakLog, DayOffRequest
    from ..services import streak_engine
    from .parent import require_parent_pin, _upsert_app_config
except ImportError:
    from database import get_db
    from models import AppConfig, StreakLog, DayOffRequest
    from services import streak_engine
    from routers.parent import require_parent_pin, _upsert_app_config


router = APIRouter()

_VALID_STREAK_SUBJECTS = {"english", "math", "game"}


class StreakRuleIn(BaseModel):
    subjects: list[str]
    mode:     str


@router.get("/api/parent/streak")
def parent_streak(db: Session = Depends(get_db)):
    """Streak dashboard payload: current, longest, rule, last-30-days. @tag PARENT STREAK"""
    subjects, mode = streak_engine.get_streak_config(db)
    current = streak_engine.get_current_streak(db)

    longest = 0
    run = 0
    for log in db.query(StreakLog).order_by(StreakLog.date.asc()).all():
        if log.streak_maintained:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    today = date.today()
    start = (today - timedelta(days=29)).isoformat()
    rows = db.query(StreakLog).filter(StreakLog.date >= start).all()
    by_date = {r.date: r for r in rows}
    last_30 = []
    for i in range(29, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        r = by_date.get(d)
        day_off = db.query(DayOffRequest).filter(
            DayOffRequest.request_date == d,
            DayOffRequest.status == "approved",
        ).first()
        last_30.append({
            "date": d,
            "maintained": bool(r and r.streak_maintained),
            "day_off": bool(day_off),
            "english": bool(r and (r.review_done and r.daily_words_done)),
            "math":    bool(r and r.math_done),
            "game":    bool(r and r.game_done),
        })

    ym = today.strftime("%Y-%m")
    freeze_count = db.query(DayOffRequest).filter(
        DayOffRequest.status == "approved",
        DayOffRequest.request_date.like(f"{ym}-%"),
    ).count()

    next_7  = 7  - (current % 7)  if current % 7  else 7
    next_30 = 30 - (current % 30) if current % 30 else 30

    return {
        "current": current,
        "longest": longest,
        "rule": {"subjects": sorted(subjects), "mode": mode},
        "last_30d": last_30,
        "freeze_this_month": freeze_count,
        "milestones": {
            "days_to_next_7":  next_7,
            "days_to_next_30": next_30,
        },
    }


@router.post("/api/parent/streak-rule")
def parent_set_streak_rule(
    body: StreakRuleIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Update streak_subjects + streak_mode. PIN-protected. @tag PARENT STREAK"""
    subjects = [s for s in body.subjects if s in _VALID_STREAK_SUBJECTS]
    if not subjects:
        raise HTTPException(status_code=400, detail="At least one subject required")
    if body.mode not in ("all", "any"):
        raise HTTPException(status_code=400, detail="mode must be 'all' or 'any'")
    now = datetime.now().isoformat()
    _upsert_app_config(db, "streak_subjects", ",".join(sorted(subjects)), now)
    _upsert_app_config(db, "streak_mode", body.mode, now)
    db.commit()
    return {"ok": True, "subjects": sorted(subjects), "mode": body.mode}


@router.post("/api/parent/streak-recalc")
def parent_streak_recalc(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Re-evaluate streak maintenance for the last N days after a rule change. @tag PARENT STREAK"""
    n = streak_engine.re_evaluate_range(db, days=days)
    return {"ok": True, "re_evaluated": n}
