"""
routers/goals.py — Weekly learning goals API
Section: Parent
Dependencies: models/goals.py, models (XPLog, WordAttempt, LearningLog),
              services/streak_engine
API: GET  /api/goals/weekly          — 목표 + 현재 달성도
     PUT  /api/goals/weekly/{key}    — 목표 수정 (PIN)
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import XPLog, WordAttempt, LearningLog
from backend.models.goals import WeeklyGoal
from backend.routers.parent import require_parent_pin
from backend.services import streak_engine

logger = logging.getLogger(__name__)
router = APIRouter()

_KEYS = {"words_correct", "xp_earned", "streak_days", "study_minutes"}


class GoalUpdateIn(BaseModel):
    target:    int
    is_active: bool = True


def _current_progress(db: Session) -> dict[str, int]:
    """이번 주 실제 달성값 계산."""
    today = date.today()
    start = (today - timedelta(days=today.weekday())).isoformat()  # 이번 주 월요일

    # words_correct
    words_correct = int(
        db.query(func.count(func.distinct(WordAttempt.word)))
        .filter(WordAttempt.attempted_at >= start, WordAttempt.is_correct == True)
        .scalar() or 0
    )

    # xp_earned
    xp_earned = int(
        db.query(func.sum(XPLog.xp_amount))
        .filter(XPLog.earned_date >= start)
        .scalar() or 0
    )

    # streak_days (현재 스트릭)
    streak_days = streak_engine.get_current_streak(db)

    # study_minutes
    sec = db.query(func.sum(LearningLog.duration_sec))            .filter(LearningLog.completed_at >= start).scalar() or 0
    study_minutes = round(sec / 60)

    return {
        "words_correct": words_correct,
        "xp_earned":     xp_earned,
        "streak_days":   streak_days,
        "study_minutes": study_minutes,
    }


@router.get("/api/goals/weekly")
def get_weekly_goals(db: Session = Depends(get_db)):
    """이번 주 목표 목록 + 달성 현황 반환. @tag PARENT SETTINGS"""
    goals    = db.query(WeeklyGoal).order_by(WeeklyGoal.id).all()
    progress = _current_progress(db)

    result = []
    for g in goals:
        current = progress.get(g.key, 0)
        pct     = min(round(current * 100 / max(g.target, 1)), 100)
        result.append({
            "key":       g.key,
            "label":     g.label,
            "target":    g.target,
            "current":   current,
            "pct":       pct,
            "achieved":  pct >= 100,
            "is_active": bool(g.is_active),
        })

    total_active   = sum(1 for g in result if g["is_active"])
    total_achieved = sum(1 for g in result if g["is_active"] and g["achieved"])

    return {
        "week_start":     (date.today() - timedelta(days=date.today().weekday())).isoformat(),
        "goals":          result,
        "total_active":   total_active,
        "total_achieved": total_achieved,
    }


@router.put("/api/goals/weekly/{key}")
def update_goal(
    key:  str,
    body: GoalUpdateIn,
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """목표 수치 및 활성 여부 수정 (PIN 필요). @tag PARENT SETTINGS"""
    if key not in _KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown goal key: {key}")
    if body.target < 0 or body.target > 10_000:
        raise HTTPException(status_code=400, detail="target must be 0–10000")

    goal = db.query(WeeklyGoal).filter(WeeklyGoal.key == key).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    from datetime import datetime
    goal.target    = body.target
    goal.is_active = 1 if body.is_active else 0
    goal.updated_at = datetime.now().isoformat()
    db.commit()
    db.refresh(goal)
    return {"ok": True, "key": goal.key, "target": goal.target, "is_active": bool(goal.is_active)}
