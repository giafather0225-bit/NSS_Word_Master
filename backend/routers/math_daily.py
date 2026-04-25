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
from functools import lru_cache
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

# Daily-keyed cache for the full practice-problem pool.
# Scanning ~435 lesson JSONs on every /submit-answer call was a major
# bottleneck. The pool itself is pure function of on-disk content; we key
# by date so edits picked up once per day (or via clear_caches()).
_pool_cache: dict[str, list[dict]] = {}


# @tag MATH @tag DAILY
def _collect_practice_problems() -> list[dict]:
    """Walk all lesson JSONs and collect every practice problem (flat list).

    Cached for the current day — subsequent calls same-day return the same
    list reference. Call clear_caches() after content edits to force refresh.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    cached = _pool_cache.get(today)
    if cached is not None:
        return cached

    pool: list[dict] = []
    if not _MATH_DIR.is_dir():
        _pool_cache.clear()
        _pool_cache[today] = pool
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
                        if not str(p.get("question", "")).strip():
                            continue  # skip problems with empty question text
                        # choices → options 통합 (list 형식 + dict 형식 모두 처리)
                        opts = p.get("options") or []
                        if not opts:
                            raw = p.get("choices") or []
                            if isinstance(raw, dict):
                                # {"A": "175", "B": "185", ...} → ["175", "185", ...]
                                opts = list(raw.values())
                            elif isinstance(raw, list):
                                # ["A) 175", "B) 185", ...] → ["175", "185", ...]
                                opts = [
                                    c[3:].strip() if len(c) > 2 and c[1] in ".)" else c
                                    for c in raw
                                ]
                        # choices → answer 키→값 변환 (dict형 + list형 모두 처리)
                        raw_choices = p.get("choices")
                        ans_val = str(p.get("answer", "")).strip()
                        if raw_choices and ans_val:
                            if isinstance(raw_choices, dict):
                                # {"A": "175", "B": "185"} 형식
                                ans_key = ans_val.upper()
                                if ans_key in raw_choices:
                                    p = dict(p)
                                    p["answer"] = raw_choices[ans_key]
                            elif isinstance(raw_choices, list):
                                # ["A. 188", "B. 198"] 또는 ["A) 188", "B) 198"] 형식
                                # answer가 단일 레이블("B")이면 해당 항목 값으로 변환
                                if len(ans_val) == 1 and ans_val.upper() in "ABCDEFGH":
                                    label = ans_val.upper()
                                    for c in raw_choices:
                                        c_str = str(c)
                                        if len(c_str) > 2 and c_str[0].upper() == label and c_str[1] in ".)":
                                            p = dict(p)
                                            p["answer"] = c_str[2:].strip()
                                            break
                        # type 정규화
                        _TYPE_MAP = {
                            "MC": "mc", "multiple_choice": "mc",
                            "TRUE_FALSE": "tf", "true_false": "tf",
                            "INPUT": "input", "fill_in": "input",
                            "DRAG_SORT": "drag_sort",
                            "word_problem": "input", "open_response": "input",
                            "compare": "mc", "ordering": "drag_sort",
                        }
                        ptype = _TYPE_MAP.get(p.get("type", "mc"), p.get("type", "mc")).lower()
                        pool.append({
                            "id": f"{grade_dir.name}/{unit_dir.name}/{lesson_file.stem}#{p.get('id','?')}",
                            "type": ptype,
                            "question": p.get("question", ""),
                            "options": opts,
                            "answer": p.get("answer", ""),
                            "concept": p.get("concept", ""),
                            "feedback_correct": p.get("feedback_correct", "Correct!"),
                            "feedback_wrong": p.get("feedback_wrong", ""),
                        })
    _pool_cache.clear()
    _pool_cache[today] = pool
    return pool


# @tag MATH @tag DAILY
def clear_caches() -> None:
    """Drop the cached practice-problem pool (force rescan on next call)."""
    _pool_cache.clear()


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
    # Grade-filter backfill: prefer problems at or below the user's current grade.
    if len(picked) < n:
        grade_filter = None
        if db is not None:
            try:
                latest_prog = (
                    db.query(MathProgress)
                    .order_by(MathProgress.last_accessed.desc().nullslast())
                    .first()
                )
                if latest_prog and latest_prog.grade:
                    grade_filter = latest_prog.grade
            except Exception:
                pass
        if grade_filter:
            grade_pool = [p for p in pool if _parse_problem_id(p["id"])[0] == grade_filter]
            picked.extend(_take(grade_pool, n - len(picked)))
        # Final fallback: unrestricted pool (new user with zero progress)
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

    def _norm(s: str) -> str:
        """정답 비교용 정규화: 공백 제거, 소문자, 분수 단순화."""
        s = str(s).strip().lower().replace(" ", "")
        # "3/6" vs "3" 등 분수 분자만 입력한 경우 대비
        return s

    user_ans = _norm(req.answer)
    correct_ans = _norm(full["answer"])
    # 분수: 분자만 입력 허용 (예: "3/6" 정답에 "3" 입력)
    is_correct = user_ans == correct_ans
    if not is_correct and "/" in correct_ans:
        try:
            num, den = correct_ans.split("/", 1)
            if user_ans == num.strip():
                is_correct = True
        except Exception:
            pass
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
