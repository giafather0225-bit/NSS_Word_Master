"""
routers/math_academy.py — Math Academy API (grades, units, lessons, stages, progress)
Section: Math
Dependencies: models.py (MathProgress), services/xp_engine.py
API: GET /api/math/academy/grades, GET /api/math/academy/{grade}/units,
     GET /api/math/academy/{grade}/{unit}/lessons,
     GET /api/math/academy/{grade}/{unit}/{lesson}/{stage},
     GET /api/math/academy/progress/{grade}
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import MathProgress
except ImportError:
    from database import get_db
    from models import MathProgress

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Data directory for Math problem JSON files ──
_DATA_DIR = Path(__file__).parent.parent / "data" / "math"

# ── Pydantic schemas ─────────────────────────────────────────

# ── Helpers ──────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@lru_cache(maxsize=512)
def _read_json_cached(path_str: str, mtime: float) -> dict:
    """Parse JSON keyed by (path, mtime) — file edits auto-invalidate."""
    return json.loads(Path(path_str).read_text("utf-8"))

# @tag MATH @tag ACADEMY
def _load_lesson_json(grade: str, unit: str, lesson: str) -> dict:
    """Load a lesson JSON file from data/math/{grade}/{unit}/{lesson}.json (cached)."""
    path = _DATA_DIR / grade / unit / f"{lesson}.json"
    if not path.exists():
        return {}
    return _read_json_cached(str(path), path.stat().st_mtime)

# @tag MATH @tag ACADEMY
def clear_caches() -> None:
    """Drop cached lesson JSON (call from admin/reload endpoints if added)."""
    _read_json_cached.cache_clear()

# @tag MATH @tag ACADEMY
def _normalize_item(item: dict) -> dict:
    """Normalize item field aliases (U8 uses `question` + lowercase `type`)."""
    if not isinstance(item, dict):
        return item
    out = dict(item)
    if "stem" not in out and "question" in out:
        out["stem"] = out["question"]
    if "answer" not in out and "correct_answer" in out:
        out["answer"] = out["correct_answer"]
    if "correct_answer" not in out and "answer" in out:
        out["correct_answer"] = out["answer"]
    t = out.get("type")
    if isinstance(t, str):
        out["type"] = t.upper() if t.lower() in {"mc", "card"} else t
    return out

# @tag MATH @tag ACADEMY
def _stage_problems(data: dict, stage: str) -> list:
    """Extract stage problems from any lesson schema.

    U1 schema: top-level key per stage (data["pretest"], data["learn"], ...).
    U2 schema: single data["items"] list where each item has a "section" field.
    U8 schema: data["sections"][stage] wrapper with renamed item fields.
    """
    if stage in data and isinstance(data[stage], list):
        return [_normalize_item(it) for it in data[stage]]
    sections = data.get("sections")
    if isinstance(sections, dict) and isinstance(sections.get(stage), list):
        return [_normalize_item(it) for it in sections[stage]]
    items = data.get("items")
    if isinstance(items, list):
        return [_normalize_item(it) for it in items if it.get("section") == stage]
    return []

# @tag MATH @tag ACADEMY
def _list_dirs(parent: Path) -> list[str]:
    """List sorted subdirectory names under parent."""
    if not parent.is_dir():
        return []
    return sorted(
        d.name for d in parent.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )

# @tag MATH @tag ACADEMY
def _list_json_files(parent: Path) -> list[str]:
    """List sorted JSON filenames (without .json) under parent."""
    if not parent.is_dir():
        return []
    return sorted(
        f.stem for f in parent.iterdir()
        if f.suffix == ".json" and not f.name.startswith(".")
    )

# ── Endpoints ────────────────────────────────────────────────

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/grades")
def get_grades() -> dict:
    """Return available grade folders (e.g., G3, G4, G5, G6)."""
    grades = [g for g in _list_dirs(_DATA_DIR) if g.startswith("G")]
    return {"grades": grades}

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/units")
def get_units(grade: str) -> dict:
    """Return available units for a grade."""
    units = _list_dirs(_DATA_DIR / grade)
    return {"grade": grade, "units": units}

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/lessons")
def get_lessons(grade: str, unit: str, db: Session = Depends(get_db)) -> dict:
    """Return available lessons for a unit, with progress info."""
    lesson_names = _list_json_files(_DATA_DIR / grade / unit)
    # Filter out unit_test from lesson list
    lessons = [l for l in lesson_names if l != "unit_test"]

    # Batch progress lookup — avoid N+1 queries (one per lesson).
    prog_rows = (
        db.query(MathProgress)
        .filter(
            MathProgress.grade == grade,
            MathProgress.unit == unit,
            MathProgress.lesson.in_(lessons),
        )
        .all()
    ) if lessons else []
    prog_by_lesson = {p.lesson: p for p in prog_rows}

    result = []
    for l in lessons:
        prog = prog_by_lesson.get(l)
        result.append({
            "name": l,
            "is_completed": prog.is_completed if prog else False,
            "stage": prog.stage if prog else "pretest",
            "pretest_skipped": prog.pretest_skipped if prog else False,
        })

    # Check if unit test is available
    all_done = all(r["is_completed"] for r in result) if result else False
    has_unit_test = (_DATA_DIR / grade / unit / "unit_test.json").exists()

    return {
        "grade": grade,
        "unit": unit,
        "lessons": result,
        "unit_test_unlocked": all_done and has_unit_test,
    }

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/{lesson}/{stage}")
def get_stage_problems(grade: str, unit: str, lesson: str, stage: str) -> dict:
    """Return problems for a specific lesson stage.

    Stages: pretest, learn, try, practice_r1, practice_r2, practice_r3
    """
    valid_stages = {"pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"}
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    data = _load_lesson_json(grade, unit, lesson)
    if not data:
        raise HTTPException(status_code=404, detail="Lesson data not found")

    problems = _stage_problems(data, stage)
    return {
        "grade": grade,
        "unit": unit,
        "lesson": lesson,
        "stage": stage,
        "problems": problems,
        "count": len(problems),
    }

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/{grade}/{unit}/unit-test")
def get_unit_test(grade: str, unit: str) -> dict:
    """Return unit test problems."""
    path = _DATA_DIR / grade / unit / "unit_test.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Unit test not found")
    data = _read_json_cached(str(path), path.stat().st_mtime)
    problems = data.get("problems", data if isinstance(data, list) else [])
    return {"grade": grade, "unit": unit, "problems": problems, "count": len(problems)}

# @tag MATH @tag ACADEMY
@router.get("/api/math/academy/progress/{grade}")
def get_grade_progress(grade: str, db: Session = Depends(get_db)):
    """Return progress overview for all units/lessons in a grade."""
    progs = db.query(MathProgress).filter_by(grade=grade).all()
    result = {}
    for p in progs:
        key = f"{p.unit}/{p.lesson}"
        result[key] = {
            "stage": p.stage,
            "is_completed": p.is_completed,
            "pretest_skipped": p.pretest_skipped,
            "best_score_r1": p.best_score_r1,
            "best_score_r2": p.best_score_r2,
            "best_score_r3": p.best_score_r3,
            "unit_test_passed": p.unit_test_passed,
        }
    return {"grade": grade, "progress": result}
