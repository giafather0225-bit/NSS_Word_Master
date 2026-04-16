"""
routers/math_fluency.py — Fact Fluency API
Section: Math
Dependencies: models.py (MathFactFluency), services/xp_engine.py
API: GET /api/math/fluency/status, GET /api/math/fluency/catalog,
     GET /api/math/fluency/start-round, POST /api/math/fluency/submit-round,
     GET /api/math/fluency/summary
"""

import logging
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
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


# ── Fact set catalog ─────────────────────────────────────────
# Each entry: label, operation, operand ranges. Generators below build 10 qs.

_FACT_SETS = {
    "add_within_10":   {"label": "Addition within 10",     "op": "+", "a": (0, 10),  "b": (0, 10),  "grade": "G2"},
    "sub_within_10":   {"label": "Subtraction within 10",  "op": "-", "a": (0, 10),  "b": (0, 10),  "grade": "G2"},
    "add_within_20":   {"label": "Addition within 20",     "op": "+", "a": (0, 20),  "b": (0, 20),  "grade": "G2"},
    "sub_within_20":   {"label": "Subtraction within 20",  "op": "-", "a": (0, 20),  "b": (0, 20),  "grade": "G3"},
    "mul_0_5":         {"label": "Multiplication 0–5",      "op": "×", "a": (0, 5),   "b": (0, 10),  "grade": "G3"},
    "mul_6_10":        {"label": "Multiplication 6–10",     "op": "×", "a": (6, 10),  "b": (0, 10),  "grade": "G3"},
    "mul_0_12":        {"label": "Multiplication 0–12",     "op": "×", "a": (0, 12),  "b": (0, 12),  "grade": "G4"},
    "div_0_10":        {"label": "Division 0–10",           "op": "÷", "a": (0, 10),  "b": (1, 10),  "grade": "G4"},
}


def _generate_question(fact_set: str):
    """Return (question, answer) for one problem."""
    spec = _FACT_SETS.get(fact_set)
    if not spec:
        return None
    op = spec["op"]
    a_lo, a_hi = spec["a"]
    b_lo, b_hi = spec["b"]
    a = random.randint(a_lo, a_hi)
    b = random.randint(b_lo, b_hi)
    if op == "+":
        return f"{a} + {b}", a + b
    if op == "-":
        # Ensure non-negative
        if b > a: a, b = b, a
        return f"{a} - {b}", a - b
    if op == "×":
        return f"{a} × {b}", a * b
    if op == "÷":
        # Build divisible pair: pick divisor then quotient
        divisor = max(1, b)
        quotient = a
        dividend = divisor * quotient
        return f"{dividend} ÷ {divisor}", quotient
    return None


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag FLUENCY
@router.get("/api/math/fluency/catalog")
def fluency_catalog(db: Session = Depends(get_db)):
    """List all fact sets with current progress."""
    rows = {r.fact_set: r for r in db.query(MathFactFluency).all()}
    out = []
    for key, spec in _FACT_SETS.items():
        r = rows.get(key)
        out.append({
            "fact_set": key,
            "label": spec["label"],
            "op": spec["op"],
            "grade": spec["grade"],
            "current_phase": r.current_phase if r else "A",
            "best_score": r.best_score if r else 0,
            "best_time_sec": r.best_time_sec if r else 0,
            "accuracy_pct": r.accuracy_pct if r else 0.0,
            "total_rounds": r.total_rounds if r else 0,
        })
    return {"fact_sets": out}


# @tag MATH @tag FLUENCY
@router.get("/api/math/fluency/start-round")
def start_round(fact_set: str, count: int = 10):
    """Generate a new fluency round (not persisted until submit)."""
    if fact_set not in _FACT_SETS:
        raise HTTPException(status_code=404, detail=f"Unknown fact_set: {fact_set}")
    count = max(5, min(int(count or 10), 20))
    spec = _FACT_SETS[fact_set]
    questions = []
    seen = set()
    tries = 0
    while len(questions) < count and tries < count * 6:
        tries += 1
        q, a = _generate_question(fact_set)
        if q in seen:
            continue
        seen.add(q)
        questions.append({"question": q, "answer": a})
    return {
        "fact_set": fact_set,
        "label": spec["label"],
        "op": spec["op"],
        "time_limit_sec": 60,
        "questions": questions,
    }


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
