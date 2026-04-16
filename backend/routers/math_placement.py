"""
routers/math_placement.py — Math Placement Test API
Section: Math
Dependencies: models.py (MathPlacementResult)
API: GET /api/math/placement/status, POST /api/math/placement/start,
     POST /api/math/placement/submit-answer, GET /api/math/placement/results
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathPlacementResult
except ImportError:
    from database import get_db
    from models import MathPlacementResult

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag PLACEMENT
@router.get("/api/math/placement/status")
def placement_status(db: Session = Depends(get_db)):
    """Check if placement test has been taken."""
    results = db.query(MathPlacementResult).all()
    return {
        "taken": len(results) > 0,
        "domains_tested": len(results),
    }


# @tag MATH @tag PLACEMENT
@router.get("/api/math/placement/results")
def placement_results(db: Session = Depends(get_db)):
    """Return all placement test results by domain."""
    results = db.query(MathPlacementResult).all()
    if not results:
        raise HTTPException(status_code=404, detail="No placement test results found")
    return {
        "results": [
            {
                "domain": r.domain,
                "estimated_grade": r.estimated_grade,
                "rit_estimate": r.rit_estimate,
                "raw_score": r.raw_score,
                "total_questions": r.total_questions,
                "test_date": r.test_date,
            }
            for r in results
        ]
    }


# @tag MATH @tag PLACEMENT
@router.post("/api/math/placement/save")
def save_placement_results(
    results: list[dict],
    db: Session = Depends(get_db),
):
    """Save placement test results (called after test completion).

    Expects list of: {domain, estimated_grade, rit_estimate, raw_score, total_questions}
    """
    now = datetime.now().strftime("%Y-%m-%d")
    saved = []
    for r in results:
        row = MathPlacementResult(
            test_date=now,
            domain=r.get("domain", ""),
            estimated_grade=r.get("estimated_grade", "G3"),
            rit_estimate=r.get("rit_estimate"),
            raw_score=r.get("raw_score", 0),
            total_questions=r.get("total_questions", 0),
            detail_json=json.dumps(r.get("detail", {})),
        )
        db.add(row)
        saved.append(row.domain)
    db.commit()
    return {"saved_domains": saved, "count": len(saved)}
