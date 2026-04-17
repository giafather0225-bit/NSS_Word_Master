"""
routers/math_placement.py — Math Placement Test API
Section: Math
Dependencies: models.py (MathPlacementResult)
API: GET /api/math/placement/status, GET /api/math/placement/start,
     POST /api/math/placement/save, GET /api/math/placement/results
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
    from ..models import MathPlacementResult
except ImportError:
    from database import get_db
    from models import MathPlacementResult

router = APIRouter()
logger = logging.getLogger(__name__)

_BANK_PATH = Path(__file__).resolve().parents[1] / "data" / "math" / "placement" / "bank.json"


def _load_bank():
    if not _BANK_PATH.exists():
        raise HTTPException(status_code=500, detail="Placement bank not found")
    return json.loads(_BANK_PATH.read_text("utf-8"))


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
@router.get("/api/math/placement/start")
def placement_start():
    """Return placement test bank: domains x questions. Answers stripped."""
    bank = _load_bank()
    domains = []
    for d in bank.get("domains", []):
        qs = []
        for q in d.get("questions", []):
            qs.append({
                "id": q["id"],
                "grade": q["grade"],
                "type": q.get("type", "input"),
                "question": q["question"],
                "options": q.get("options"),
            })
        domains.append({
            "domain": d["domain"],
            "label": d["label"],
            "questions": qs,
        })
    return {
        "version": bank.get("version", 1),
        "domains": domains,
    }


# @tag MATH @tag PLACEMENT
class DomainResultIn(BaseModel):
    domain: str
    answers: dict  # {question_id: user_answer}


class SaveResultsIn(BaseModel):
    results: list[DomainResultIn]


def _score_domain(domain_spec: dict, answers: dict):
    """Grade each question; estimate grade as highest level with >=70% correct."""
    by_grade = {}  # grade -> [correct, total]
    detail = []
    for q in domain_spec["questions"]:
        correct_ans = str(q.get("answer", "")).strip().lower()
        user = str(answers.get(q["id"], "")).strip().lower()
        is_correct = user != "" and user == correct_ans
        g = q["grade"]
        by_grade.setdefault(g, [0, 0])
        by_grade[g][1] += 1
        if is_correct:
            by_grade[g][0] += 1
        detail.append({"id": q["id"], "grade": g, "user": user, "correct": is_correct})

    # Highest grade with >= 70% correct
    grade_order = ["G2", "G3", "G4", "G5", "G6"]
    estimated = "G2"
    for g in grade_order:
        if g in by_grade:
            c, t = by_grade[g]
            pct = (c / t) if t else 0
            if pct >= 0.7:
                estimated = g

    total_correct = sum(x[0] for x in by_grade.values())
    total_q = sum(x[1] for x in by_grade.values())
    return {
        "estimated_grade": estimated,
        "raw_score": total_correct,
        "total_questions": total_q,
        "by_grade": {g: {"correct": v[0], "total": v[1]} for g, v in by_grade.items()},
        "detail": detail,
    }


# @tag MATH @tag PLACEMENT
@router.post("/api/math/placement/save")
def save_placement_results(req: SaveResultsIn, db: Session = Depends(get_db)):
    """Score domains server-side and persist results."""
    bank = _load_bank()
    domains_by_key = {d["domain"]: d for d in bank["domains"]}
    now = datetime.now().strftime("%Y-%m-%d")

    # Clear previous results — this is a fresh placement
    db.query(MathPlacementResult).delete()

    saved = []
    overall = []
    for r in req.results:
        spec = domains_by_key.get(r.domain)
        if not spec:
            continue
        scored = _score_domain(spec, r.answers or {})
        row = MathPlacementResult(
            test_date=now,
            domain=r.domain,
            estimated_grade=scored["estimated_grade"],
            rit_estimate=None,
            raw_score=scored["raw_score"],
            total_questions=scored["total_questions"],
            detail_json=json.dumps({
                "by_grade": scored["by_grade"],
                "detail": scored["detail"],
            }),
        )
        db.add(row)
        saved.append(r.domain)
        overall.append({
            "domain": r.domain,
            "label": spec["label"],
            "estimated_grade": scored["estimated_grade"],
            "raw_score": scored["raw_score"],
            "total_questions": scored["total_questions"],
            "by_grade": scored["by_grade"],
        })
    db.commit()

    # Suggested starting grade = min of domain estimates (weakest → start there)
    grade_order = ["G2", "G3", "G4", "G5", "G6"]
    if overall:
        suggested = min(overall, key=lambda o: grade_order.index(o["estimated_grade"]))["estimated_grade"]
    else:
        suggested = "G3"

    return {"saved_domains": saved, "results": overall, "suggested_grade": suggested}


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
