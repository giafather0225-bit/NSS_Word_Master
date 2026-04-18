"""
routers/math_kangaroo.py — Math Kangaroo Practice API
Section: Math
Dependencies: models.py (MathKangarooProgress), services/xp_engine.py
API: GET  /api/math/kangaroo/sets
     GET  /api/math/kangaroo/set/{set_id}
     POST /api/math/kangaroo/submit-answer
     POST /api/math/kangaroo/submit
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathKangarooProgress
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import MathKangarooProgress
    from services import xp_engine, streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

_KANGAROO_DIR = Path(__file__).parent.parent / "data" / "math" / "kangaroo"


# ── Helpers ─────────────────────────────────────────────────

def _load_set(set_id: str) -> dict:
    path = _KANGAROO_DIR / f"{set_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")
    return json.loads(path.read_text("utf-8"))


def _strip_answers(problems: list[dict]) -> list[dict]:
    return [{
        "id": p.get("id"),
        "type": p.get("type", "mc"),
        "question": p.get("question", ""),
        "options": p.get("options", []),
    } for p in problems]


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/sets")
def kangaroo_sets(db: Session = Depends(get_db)):
    """Return available Kangaroo practice sets."""
    sets = []
    if _KANGAROO_DIR.is_dir():
        for f in sorted(_KANGAROO_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text("utf-8"))
            except Exception:
                continue
            set_id = f.stem
            prog = db.query(MathKangarooProgress).filter_by(set_id=set_id).first()
            sets.append({
                "set_id": set_id,
                "title": data.get("title", set_id),
                "category": data.get("category", ""),
                "difficulty_level": data.get("difficulty_level", "pre_ecolier"),
                "problem_count": len(data.get("problems", [])),
                "completed": prog.completed_at is not None if prog else False,
                "score": prog.score if prog else None,
                "total": prog.total if prog else None,
            })
    return {"sets": sets}


# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/set/{set_id}")
def kangaroo_set(set_id: str):
    """Return problems for a specific Kangaroo set (answers stripped)."""
    data = _load_set(set_id)
    return {
        "set_id": set_id,
        "title": data.get("title", set_id),
        "category": data.get("category", ""),
        "difficulty_level": data.get("difficulty_level", "pre_ecolier"),
        "problems": _strip_answers(data.get("problems", [])),
    }


class KangarooAnswerIn(BaseModel):
    set_id: str
    problem_id: str
    answer: str


# @tag MATH @tag KANGAROO
@router.post("/api/math/kangaroo/submit-answer")
def kangaroo_submit_answer(req: KangarooAnswerIn):
    """Score a single Kangaroo problem answer (answer key resolved server-side)."""
    data = _load_set(req.set_id)
    problems = data.get("problems", [])
    target = next((p for p in problems if str(p.get("id")) == req.problem_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Problem not found in set")
    correct = str(target.get("answer", "")).strip().lower()
    is_correct = str(req.answer).strip().lower() == correct
    return {
        "is_correct": is_correct,
        "correct_answer": target.get("answer", ""),
        "feedback": target.get("feedback_wrong") or "Not quite — take another look!" if not is_correct else "Correct!",
    }


class KangarooCompleteIn(BaseModel):
    set_id: str
    score: int
    total: int


# @tag MATH @tag KANGAROO
@router.post("/api/math/kangaroo/submit")
def kangaroo_submit(req: KangarooCompleteIn, db: Session = Depends(get_db)):
    """Submit Kangaroo set results (best score kept, XP awarded)."""
    now = datetime.now().isoformat()
    row = db.query(MathKangarooProgress).filter_by(set_id=req.set_id).first()
    data = _load_set(req.set_id)
    if not row:
        row = MathKangarooProgress(
            set_id=req.set_id,
            category=data.get("category", ""),
            difficulty_level=data.get("difficulty_level", "pre_ecolier"),
            score=req.score,
            total=req.total,
            completed_at=now,
        )
        db.add(row)
    else:
        # Keep best score but only when compared against the same total, so
        # score/total stays internally consistent.
        if req.total != row.total:
            row.score = req.score
            row.total = req.total
        elif req.score > row.score:
            row.score = req.score
        row.completed_at = now

    awarded = 0
    try:
        xp_engine.award_xp(db, "math_kangaroo_complete", 5, f"Kangaroo {req.set_id}")
        awarded += 5
        if req.score == req.total and req.total > 0:
            xp_engine.award_xp(db, "math_kangaroo_perfect", 5, f"Kangaroo Perfect {req.set_id}")
            awarded += 5
    except Exception as e:
        logger.warning("XP award failed: %s", e)
    try:
        streak_engine.mark_math_done(db)
    except Exception as e:
        logger.warning("Streak math mark failed: %s", e)

    db.commit()
    return {"score": req.score, "total": req.total, "perfect": req.score == req.total, "xp": awarded}
