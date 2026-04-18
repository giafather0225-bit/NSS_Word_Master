"""
routers/math_daily.py — Math Daily Challenge API
Section: Math
Dependencies: models.py (MathDailyChallenge), services/xp_engine.py
API: GET  /api/math/daily/today
     POST /api/math/daily/submit-answer
     POST /api/math/daily/complete
"""

import hashlib
import json
import logging
import random
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathDailyChallenge, MathProgress, MathWrongReview
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import MathDailyChallenge, MathProgress, MathWrongReview
    from services import xp_engine, streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

_MATH_DIR = Path(__file__).parent.parent / "data" / "math"
_DAILY_COUNT = 5
# Composition per MATH_SPEC §Daily Challenge: 50% current + 30% spaced + 20% spiral.
_MIX_CURRENT_PCT = 0.50
_MIX_SPACED_PCT = 0.30
_MIX_SPIRAL_PCT = 0.20


# ── Problem pool ─────────────────────────────────────────────

# @tag MATH @tag DAILY
def _collect_practice_problems() -> list[dict]:
    """Walk all lesson JSONs and collect every practice problem (flat list)."""
    pool: list[dict] = []
    if not _MATH_DIR.is_dir():
        return pool
    for grade_dir in sorted(_MATH_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("G"):
            continue
        for unit_dir in sorted(grade_dir.iterdir()):
            if not unit_dir.is_dir():
                continue
            for lesson_file in sorted(unit_dir.glob("*.json")):
                try:
                    data = json.loads(lesson_file.read_text("utf-8"))
                except Exception:
                    continue
                for key in ("practice_r1", "practice_r2", "practice_r3"):
                    for p in data.get(key) or []:
                        if not isinstance(p, dict) or "answer" not in p:
                            continue
                        pool.append({
                            "id": f"{grade_dir.name}/{unit_dir.name}/{lesson_file.stem}#{p.get('id','?')}",
                            "type": p.get("type", "mc"),
                            "question": p.get("question", ""),
                            "options": p.get("options", []),
                            "answer": p.get("answer", ""),
                            "concept": p.get("concept", ""),
                            "feedback_correct": p.get("feedback_correct", "Correct!"),
                            "feedback_wrong": p.get("feedback_wrong", ""),
                        })
    return pool


def _parse_problem_id(pid: str) -> tuple[str, str, str]:
    """Parse 'G3/U1_xxx/L2_yyy#p_01' -> (grade, unit, lesson). Returns '' on malformed."""
    try:
        path, _ = pid.split("#", 1)
        g, u, l = path.split("/", 2)
        return g, u, l
    except Exception:
        return "", "", ""


# @tag MATH @tag DAILY
def _pick_daily_problems(date_str: str, db: Session | None = None) -> list[dict]:
    """Compose daily challenge per spec: 50% current unit + 30% spaced + 20% spiral.

    Falls back gracefully when a bucket is empty (e.g., new user with no
    progress or no wrong-review items): remaining slots are filled from a
    deterministic random pool so the challenge is never short.
    """
    pool = _collect_practice_problems()
    if not pool:
        return []
    seed = int(hashlib.sha256(date_str.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)

    n = min(_DAILY_COUNT, len(pool))
    target_current = round(n * _MIX_CURRENT_PCT)
    target_spaced  = round(n * _MIX_SPACED_PCT)
    target_spiral  = n - target_current - target_spaced  # remainder absorbs rounding

    pool_by_id = {p["id"]: p for p in pool}
    picked: list[dict] = []
    used_ids: set[str] = set()

    def _take(items: list[dict], k: int) -> list[dict]:
        fresh = [p for p in items if p["id"] not in used_ids]
        if not fresh or k <= 0:
            return []
        rng.shuffle(fresh)
        out = fresh[:k]
        for p in out:
            used_ids.add(p["id"])
        return out

    # Current unit: problems from the lesson the user is most recently working on.
    # Fallback to any unit with in-progress MathProgress if last_accessed missing.
    current_items: list[dict] = []
    completed_keys: set[tuple[str, str]] = set()  # (grade, unit) for spiral
    if db is not None:
        try:
            latest = (
                db.query(MathProgress)
                .order_by(MathProgress.last_accessed.desc().nullslast())
                .first()
            )
            if latest and latest.grade and latest.unit:
                current_items = [
                    p for p in pool
                    if _parse_problem_id(p["id"])[:2] == (latest.grade, latest.unit)
                ]
            for row in db.query(MathProgress).filter_by(is_completed=True).all():
                if row.grade and row.unit:
                    completed_keys.add((row.grade, row.unit))
        except Exception as e:
            logger.warning("Daily current-unit lookup failed: %s", e)

    picked.extend(_take(current_items, target_current))

    # Spaced review: wrong items due today (or overdue), not yet mastered.
    spaced_items: list[dict] = []
    if db is not None:
        try:
            due = (
                db.query(MathWrongReview)
                .filter(
                    MathWrongReview.is_mastered == False,  # noqa: E712
                    MathWrongReview.next_review_date <= date_str,
                )
                .all()
            )
            for r in due:
                p = pool_by_id.get(r.problem_id)
                if p and p["id"] not in used_ids:
                    spaced_items.append(p)
        except Exception as e:
            logger.warning("Daily spaced-review lookup failed: %s", e)

    picked.extend(_take(spaced_items, target_spaced))

    # Spiral: problems from completed units other than the current one.
    spiral_items: list[dict] = []
    if completed_keys:
        latest_key = None
        if current_items:
            latest_key = _parse_problem_id(current_items[0]["id"])[:2]
        spiral_items = [
            p for p in pool
            if _parse_problem_id(p["id"])[:2] in completed_keys
            and _parse_problem_id(p["id"])[:2] != latest_key
        ]

    picked.extend(_take(spiral_items, target_spiral))

    # Backfill any shortfall from the full pool so the challenge always
    # has _DAILY_COUNT problems even when buckets are empty (new users).
    if len(picked) < n:
        picked.extend(_take(pool, n - len(picked)))

    # Strip answer before sending to client
    return [{
        "index": i,
        "id": p["id"],
        "type": p["type"],
        "question": p["question"],
        "options": p["options"],
        "concept": p["concept"],
    } for i, p in enumerate(picked)]


# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag DAILY
@router.get("/api/math/daily/today")
def daily_today(db: Session = Depends(get_db)):
    """Return today's daily challenge (generate problems if first call today)."""
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.query(MathDailyChallenge).filter_by(challenge_date=today).first()

    if not row:
        problems = _pick_daily_problems(today, db)
        if not problems:
            return {"date": today, "exists": False, "completed": False, "problems": []}
        row = MathDailyChallenge(
            challenge_date=today,
            problems_json=json.dumps(problems, ensure_ascii=False),
            score=0,
            total=len(problems),
            completed=False,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

    return {
        "date": today,
        "exists": True,
        "completed": row.completed,
        "score": row.score,
        "total": row.total,
        "problems": json.loads(row.problems_json) if row.problems_json else [],
    }


class DailyAnswerIn(BaseModel):
    index: int
    answer: str


# @tag MATH @tag DAILY
@router.post("/api/math/daily/submit-answer")
def daily_submit_answer(req: DailyAnswerIn, db: Session = Depends(get_db)):
    """Score a single daily-challenge answer. Answer key resolved server-side.

    Uses the problem set persisted at first-call time (daily_today). Re-picking
    on every submit is unsafe: if the lesson pool changes mid-day (new JSON,
    edited file) the random sample can shift, scoring against a problem the
    user never saw.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.query(MathDailyChallenge).filter_by(challenge_date=today).first()
    if not row or not row.problems_json:
        raise HTTPException(status_code=400, detail="Daily challenge not started")

    try:
        stored = json.loads(row.problems_json)
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupt daily challenge data")

    if req.index < 0 or req.index >= len(stored):
        raise HTTPException(status_code=400, detail="Invalid problem index")

    problem_id = stored[req.index].get("id")
    full_pool = {p["id"]: p for p in _collect_practice_problems()}
    full = full_pool.get(problem_id)
    if not full:
        raise HTTPException(status_code=404, detail="Problem not found")

    is_correct = str(req.answer).strip().lower() == str(full["answer"]).strip().lower()
    return {
        "is_correct": is_correct,
        "correct_answer": full["answer"],
        "feedback": full["feedback_correct"] if is_correct else full["feedback_wrong"],
    }


class DailyCompleteIn(BaseModel):
    score: int
    total: int


# @tag MATH @tag DAILY
@router.post("/api/math/daily/complete")
def daily_complete(req: DailyCompleteIn, db: Session = Depends(get_db)):
    """Mark today's daily challenge as complete and award XP."""
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.query(MathDailyChallenge).filter_by(challenge_date=today).first()
    if not row:
        row = MathDailyChallenge(
            challenge_date=today, score=req.score, total=req.total, completed=True,
        )
        db.add(row)
    else:
        row.score = req.score
        row.total = req.total
        row.completed = True

    awarded = 0
    try:
        xp_engine.award_xp(db, "math_daily_complete", 5, f"Math Daily {today}")
        awarded += 5
        if req.total > 0 and req.score == req.total:
            xp_engine.award_xp(db, "math_daily_perfect", 3, f"Math Daily Perfect {today}")
            awarded += 3
    except Exception as e:
        logger.warning("XP award failed: %s", e)
    try:
        streak_engine.mark_math_done(db)
    except Exception as e:
        logger.warning("Streak math mark failed: %s", e)

    db.commit()
    return {"status": "completed", "score": req.score, "total": req.total, "xp": awarded}
