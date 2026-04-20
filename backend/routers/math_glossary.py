"""
routers/math_glossary.py — Math Glossary API
Section: Math
Dependencies: none (static JSON)
API: GET /api/math/glossary/grades
     GET /api/math/glossary/{grade}
     GET /api/math/glossary/{grade}/{term_id}
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

_GLOSSARY_DIR = Path(__file__).parent.parent / "data" / "math" / "glossary"


@lru_cache(maxsize=32)
def _read_json_cached(path_str: str, mtime: float) -> dict:
    """Parse glossary JSON keyed by (path, mtime)."""
    return json.loads(Path(path_str).read_text("utf-8"))


def _load_grade(grade: str) -> dict:
    path = _GLOSSARY_DIR / f"{grade.lower()}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Glossary for {grade} not found")
    return _read_json_cached(str(path), path.stat().st_mtime)


def clear_caches() -> None:
    """Drop cached glossary JSONs."""
    _read_json_cached.cache_clear()


# @tag MATH @tag GLOSSARY
@router.get("/api/math/glossary/grades")
def glossary_grades():
    """List available glossary grades."""
    if not _GLOSSARY_DIR.is_dir():
        return {"grades": []}
    grades = []
    for f in sorted(_GLOSSARY_DIR.glob("*.json")):
        try:
            data = _read_json_cached(str(f), f.stat().st_mtime)
        except Exception:
            continue
        grades.append({
            "grade": data.get("grade", f.stem.upper()),
            "title": data.get("title", f.stem),
            "term_count": len(data.get("terms", [])),
        })
    return {"grades": grades}


# @tag MATH @tag GLOSSARY
@router.get("/api/math/glossary/{grade}")
def glossary_list(grade: str):
    """Return all terms for a grade, grouped by category."""
    data = _load_grade(grade)
    terms = data.get("terms", [])
    categories: dict[str, list[dict]] = {}
    for t in terms:
        cat = t.get("category", "other")
        categories.setdefault(cat, []).append({
            "id": t.get("id"),
            "term": t.get("term", ""),
            "kid_friendly": t.get("kid_friendly", ""),
        })
    return {
        "grade": data.get("grade", grade.upper()),
        "title": data.get("title", ""),
        "categories": [{"name": k, "terms": v} for k, v in sorted(categories.items())],
        "total": len(terms),
    }


# @tag MATH @tag GLOSSARY
@router.get("/api/math/glossary/{grade}/{term_id}")
def glossary_term(grade: str, term_id: str):
    """Return full details for a single term."""
    data = _load_grade(grade)
    for t in data.get("terms", []):
        if t.get("id") == term_id:
            return t
    raise HTTPException(status_code=404, detail=f"Term {term_id} not found in {grade}")
