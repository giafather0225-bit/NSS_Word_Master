"""
routers/math_fluency.py — Fact Fluency API
Section: Math
Dependencies: models.py (MathFactFluency), services/xp_engine.py
API: GET /api/math/fluency/status, POST /api/math/fluency/submit-round,
     GET /api/math/fluency/summary
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathFactFluency
    from ..services import xp_engine
except ImportError:
    from database import get_db
    from models import MathFactFluency
    from services import xp_engine

router = APIRouter()
logger = logging.getLogger(__name__)


class RoundResultIn(BaseModel):
    """Submit result of one fluency round."""
    fact_set: str
    score: int
    total: int
    time_sec: int


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag FLUENCY
@router.get("/api/math/fluency/status")
def fluency_status(db: Session = Depends(get_db)):
    """Return fluency progress for all fact sets."""
    rows = db.query(MathFactFluency).all()
    return {
        "fact_sets": [
            {
                "fact_set": r.fact_set,
                "current_phase": r.current_phase,
                "best_score": r.best_score,
                "best_time_sec": r.best_time_sec,
                "accuracy_pct": r.accuracy_pct,
                "total_rounds": r.total_rounds,
                "last_played": r.last_played,
            }
            for r in rows
        ]
    }


# @tag MATH @tag FLUENCY
@router.post("/api/math/fluency/submit-round")
def submit_round(req: RoundResultIn, db: Session = Depends(get_db)):
    """Submit result of one fact fluency round."""
    now = datetime.now().isoformat()
    accuracy = round(req.score / req.total * 100, 1) if req.total else 0

    row = db.query(MathFactFluency).filter_by(fact_set=req.fact_set).first()
    new_best = False
    if not row:
        row = MathFactFluency(
            fact_set=req.fact_set,
            current_phase="A",
            best_score=req.score,
            best_time_sec=req.time_sec,
            accuracy_pct=accuracy,
            total_rounds=1,
            last_played=now,
        )
        db.add(row)
    else:
        row.total_rounds += 1
        row.last_played = now
        if req.score > row.best_score:
            row.best_score = req.score
            new_best = True
        if req.time_sec < row.best_time_sec or row.best_time_sec == 0:
            row.best_time_sec = req.time_sec
        row.accuracy_pct = max(row.accuracy_pct, accuracy)

        # Phase progression
        if row.current_phase == "A" and req.score >= 10 and req.total == 10:
            row.current_phase = "B"
        elif row.current_phase == "B" and req.score >= 10 and req.total == 10:
            row.current_phase = "C"

    # XP for personal best
    if new_best:
        try:
            xp_engine.award_xp(db, "math_fluency_best", 2, f"Fluency {req.fact_set}")
        except Exception as e:
            logger.warning("XP award failed: %s", e)

    # Check mastery (Phase C, 95%+)
    mastered = row.current_phase == "C" and accuracy >= 95.0

    db.commit()

    return {
        "accuracy": accuracy,
        "new_best": new_best,
        "current_phase": row.current_phase,
        "total_rounds": row.total_rounds,
        "mastered": mastered,
    }


# @tag MATH @tag FLUENCY
@router.get("/api/math/fluency/summary")
def fluency_summary(db: Session = Depends(get_db)):
    """Return overall fluency summary."""
    rows = db.query(MathFactFluency).all()
    total_mastered = sum(1 for r in rows if r.current_phase == "C" and r.accuracy_pct >= 95)
    total_sets = len(rows)
    today = datetime.now().strftime("%Y-%m-%d")
    today_rounds = sum(
        1 for r in rows
        if r.last_played and r.last_played.startswith(today)
    )
    return {
        "total_sets": total_sets,
        "mastered_sets": total_mastered,
        "today_rounds": today_rounds,
        "daily_target": 3,
    }
