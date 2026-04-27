"""
routers/math_academy_stats.py — Math Academy analytics (weekly + today)
Section: Math
Dependencies: models.py (MathAttempt, MathFactFluency, MathDailyChallenge, XPLog)
API: GET /api/math/academy/weekly-stats
     GET /api/math/academy/today-stats
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathAttempt, MathFactFluency, MathDailyChallenge, XPLog
except ImportError:
    from database import get_db
    from models import MathAttempt, MathFactFluency, MathDailyChallenge, XPLog

router = APIRouter()


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/weekly-stats")
def get_weekly_stats(db: Session = Depends(get_db)):
    """Return last-7-day activity summary for the Math home dashboard."""
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=6)

    # ── Per-day problem counts ────────────────────────────────
    days_out = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        d_str = d.isoformat()
        day_rows = (
            db.query(MathAttempt)
            .filter(MathAttempt.attempted_at.like(f"{d_str}%"))
            .all()
        )
        total = len(day_rows)
        correct = sum(1 for r in day_rows if r.is_correct)
        days_out.append({
            "date": d_str,
            "label": d.strftime("%a"),
            "total": total,
            "correct": correct,
        })

    # ── Totals this week ──────────────────────────────────────
    week_attempts = (
        db.query(MathAttempt)
        .filter(MathAttempt.attempted_at >= week_ago.isoformat())
        .all()
    )
    total_problems = len(week_attempts)
    total_correct = sum(1 for a in week_attempts if a.is_correct)
    accuracy_pct = round(total_correct / total_problems * 100) if total_problems else 0

    # ── Fluency rounds this week ──────────────────────────────
    fluency_rows = (
        db.query(MathFactFluency)
        .filter(MathFactFluency.last_played >= week_ago.isoformat())
        .all()
    )
    fluency_rounds = sum(r.total_rounds or 0 for r in fluency_rows)

    # ── Daily challenges completed this week ──────────────────
    daily_done = (
        db.query(func.count(MathDailyChallenge.id))
        .filter(
            MathDailyChallenge.challenge_date >= week_ago.isoformat(),
            MathDailyChallenge.completed == True,
        )
        .scalar() or 0
    )

    # ── Per-unit accuracy (strengths / needs-work) ────────────
    unit_map: dict = {}
    for a in week_attempts:
        u = a.unit or "unknown"
        if u not in unit_map:
            unit_map[u] = {"cnt": 0, "ok": 0}
        unit_map[u]["cnt"] += 1
        if a.is_correct:
            unit_map[u]["ok"] += 1

    strengths, needs_work = [], []
    for unit_name, counts in unit_map.items():
        if counts["cnt"] < 3:
            continue
        pct = counts["ok"] / counts["cnt"] * 100
        label = unit_name.replace("_", " ")
        if pct >= 75:
            strengths.append(label)
        elif pct < 50:
            needs_work.append(label)

    return {
        "days": days_out,
        "totals": {
            "problems": total_problems,
            "correct": total_correct,
            "accuracy_pct": accuracy_pct,
            "fluency_rounds": fluency_rounds,
            "daily_challenges": daily_done,
        },
        "strengths": strengths[:3],
        "needs_work": needs_work[:3],
    }


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/today-stats")
def get_today_stats(db: Session = Depends(get_db)):
    """Return today's activity summary for the Math home stat chips."""
    today = datetime.utcnow().date().isoformat()

    today_attempts = (
        db.query(MathAttempt)
        .filter(MathAttempt.attempted_at.like(f"{today}%"))
        .all()
    )
    problems_today = len(today_attempts)

    total_sec = sum((a.time_spent_sec or 0) for a in today_attempts)
    minutes_today = round(total_sec / 60) if total_sec > 0 else None

    xp_rows = (
        db.query(XPLog)
        .filter(
            XPLog.earned_date == today,
            XPLog.action.like("math%"),
        )
        .all()
    )
    xp_today = sum(r.xp_amount or 0 for r in xp_rows) if xp_rows else None

    return {
        "problems_today": problems_today,
        "minutes_today": minutes_today,
        "xp_today": xp_today,
    }
