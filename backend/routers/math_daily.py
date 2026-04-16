"""
routers/math_daily.py — Math Daily Challenge API
Section: Math
Dependencies: models.py (MathDailyChallenge), services/xp_engine.py
API: GET /api/math/daily/today, POST /api/math/daily/submit-answer
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathDailyChallenge
    from ..services import xp_engine
except ImportError:
    from database import get_db
    from models import MathDailyChallenge
    from services import xp_engine

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag DAILY
@router.get("/api/math/daily/today")
def daily_today(db: Session = Depends(get_db)):
    """Return today's daily challenge status."""
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.query(MathDailyChallenge).filter_by(challenge_date=today).first()
    if not row:
        return {
            "date": today,
            "exists": False,
            "completed": False,
            "score": 0,
            "total": 0,
        }
    return {
        "date": today,
        "exists": True,
        "completed": row.completed,
        "score": row.score,
        "total": row.total,
        "problems": json.loads(row.problems_json) if row.problems_json else [],
    }


# @tag MATH @tag DAILY
@router.post("/api/math/daily/complete")
def daily_complete(score: int, total: int, db: Session = Depends(get_db)):
    """Mark today's daily challenge as complete."""
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.query(MathDailyChallenge).filter_by(challenge_date=today).first()
    if not row:
        row = MathDailyChallenge(
            challenge_date=today,
            score=score,
            total=total,
            completed=True,
        )
        db.add(row)
    else:
        row.score = score
        row.total = total
        row.completed = True

    # XP
    try:
        xp_engine.award_xp(db, "math_daily_complete", 5, f"Math Daily {today}")
        if total > 0 and score == total:
            xp_engine.award_xp(db, "math_daily_perfect", 3, f"Math Daily Perfect {today}")
    except Exception as e:
        logger.warning("XP award failed: %s", e)

    db.commit()
    return {"status": "completed", "score": score, "total": total}
