"""
routers/math_kangaroo.py — Math Kangaroo Practice API
Section: Math
Dependencies: models.py (MathKangarooProgress), services/xp_engine.py
API: GET /api/math/kangaroo/sets, GET /api/math/kangaroo/set/{set_id},
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
    from ..services import xp_engine
except ImportError:
    from database import get_db
    from models import MathKangarooProgress
    from services import xp_engine

router = APIRouter()
logger = logging.getLogger(__name__)

_KANGAROO_DIR = Path(__file__).parent.parent / "data" / "math" / "kangaroo"


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/sets")
def kangaroo_sets(db: Session = Depends(get_db)):
    """Return available Kangaroo practice sets."""
    sets = []
    if _KANGAROO_DIR.is_dir():
        for f in sorted(_KANGAROO_DIR.glob("*.json")):
            data = json.loads(f.read_text("utf-8"))
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
            })
    return {"sets": sets}


# @tag MATH @tag KANGAROO
@router.get("/api/math/kangaroo/set/{set_id}")
def kangaroo_set(set_id: str):
    """Return problems for a specific Kangaroo set."""
    path = _KANGAROO_DIR / f"{set_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")
    data = json.loads(path.read_text("utf-8"))
    return {
        "set_id": set_id,
        "title": data.get("title", set_id),
        "category": data.get("category", ""),
        "problems": data.get("problems", []),
    }


# @tag MATH @tag KANGAROO
@router.post("/api/math/kangaroo/submit")
def kangaroo_submit(set_id: str, score: int, total: int, db: Session = Depends(get_db)):
    """Submit Kangaroo set results."""
    now = datetime.now().isoformat()
    row = db.query(MathKangarooProgress).filter_by(set_id=set_id).first()
    if not row:
        row = MathKangarooProgress(
            set_id=set_id, score=score, total=total, completed_at=now,
        )
        db.add(row)
    else:
        row.score = max(row.score, score)
        row.completed_at = now

    # XP
    try:
        xp_engine.award_xp(db, "math_kangaroo_complete", 5, f"Kangaroo {set_id}")
        if score == total and total > 0:
            xp_engine.award_xp(db, "math_kangaroo_perfect", 5, f"Kangaroo Perfect {set_id}")
    except Exception as e:
        logger.warning("XP award failed: %s", e)

    db.commit()
    return {"score": score, "total": total, "perfect": score == total}
