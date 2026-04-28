"""
routers/math_academy_path.py — Learning-path overview endpoint
Section: Math
Dependencies: models/math.py, models/gamification.py
API: GET /api/math/academy/{grade}/learning-path
"""

import re
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathProgress, MathAttempt
    from ..models.gamification import XPLog, StreakLog
except ImportError:
    from database import get_db
    from models import MathProgress, MathAttempt
    from models.gamification import XPLog, StreakLog

router = APIRouter()
logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data" / "math"


@lru_cache(maxsize=128)
def _list_dirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(d.name for d in path.iterdir() if d.is_dir())


@lru_cache(maxsize=256)
def _list_json_stems(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(f.stem for f in path.iterdir() if f.suffix == ".json")


def _display_name(unit_name: str) -> str:
    return re.sub(r"^U\d+_", "", unit_name).replace("_", " ")


def _calc_streak(db: Session) -> int:
    today = datetime.now().date()
    streak = 0
    for i in range(366):
        d = (today - timedelta(days=i)).isoformat()
        row = db.query(StreakLog).filter_by(date=d).first()
        if row and row.streak_maintained:
            streak += 1
        else:
            break
    return streak


# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/learning-path")
def get_learning_path(grade: str, db: Session = Depends(get_db)):
    """Return unit-level completion overview + aggregate stats for the learning-path view."""
    unit_names = _list_dirs(_DATA_DIR / grade)

    # Batch-query all progress rows for this grade (no N+1).
    all_prog = db.query(MathProgress).filter_by(grade=grade).all()
    prog_idx = {(p.unit, p.lesson): p for p in all_prog}

    units = []
    total_lessons_all = 0
    lessons_mastered_all = 0
    current = None          # most-recently-accessed in-progress lesson

    for unit_name in unit_names:
        lesson_names = [
            l for l in _list_json_stems(_DATA_DIR / grade / unit_name)
            if l != "unit_test"
        ]
        total = len(lesson_names)
        total_lessons_all += total

        completed = 0
        best_accessed = ""
        unit_current = None
        unit_current_stage = None

        for lesson in lesson_names:
            prog = prog_idx.get((unit_name, lesson))
            if prog and prog.is_completed:
                completed += 1
            elif prog and prog.last_accessed:
                if prog.last_accessed > best_accessed:
                    best_accessed = prog.last_accessed
                    unit_current = lesson
                    unit_current_stage = prog.stage

        lessons_mastered_all += completed
        is_mastered = (completed == total and total > 0)
        has_ut = (_DATA_DIR / grade / unit_name / "unit_test.json").exists()

        if unit_current and best_accessed > (current or {}).get("_ts", ""):
            current = {
                "unit": unit_name,
                "lesson": unit_current,
                "stage": unit_current_stage or "pretest",
                "_ts": best_accessed,
            }

        units.append({
            "name": unit_name,
            "display": _display_name(unit_name),
            "total_lessons": total,
            "completed_lessons": completed,
            "is_mastered": is_mastered,
            "unit_test_unlocked": is_mastered and has_ut,
            "current_lesson": unit_current,
            "current_stage": unit_current_stage,
        })

    # Strip internal timestamp before returning.
    if current:
        current = {k: v for k, v in current.items() if k != "_ts"}

    # Aggregate stats
    streak_days = _calc_streak(db)
    total_xp = int(db.query(func.sum(XPLog.xp_amount)).scalar() or 0)

    seven_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
    recent = (
        db.query(MathAttempt)
        .filter(MathAttempt.grade == grade, MathAttempt.attempted_at >= seven_ago)
        .all()
    )
    acc_total = len(recent)
    acc_correct = sum(1 for a in recent if a.is_correct)
    accuracy_pct = round(acc_correct / acc_total * 100) if acc_total else 0

    return {
        "grade": grade,
        "units": units,
        "stats": {
            "lessons_mastered": lessons_mastered_all,
            "total_lessons": total_lessons_all,
            "streak_days": streak_days,
            "total_xp": total_xp,
            "accuracy_pct": accuracy_pct,
        },
        "current": current,
    }
