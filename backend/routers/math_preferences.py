"""
routers/math_preferences.py — Math module user preferences
Section: Math
Dependencies: models/system.py (AppConfig), database
API endpoints: GET /api/math/preferences, POST /api/math/preferences
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import AppConfig
except ImportError:
    from database import get_db
    from models import AppConfig

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Config keys ───────────────────────────────────────────────

_KEY_GRADE   = "math_default_grade"
_KEY_FLUENCY = "math_fluency_daily_target"
_KEY_DAILY   = "math_daily_challenge_enabled"

_DEFAULTS = {
    _KEY_GRADE:   "G4",
    _KEY_FLUENCY: "3",
    _KEY_DAILY:   "true",
}


def _get(db: Session, key: str) -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return row.value if row else _DEFAULTS[key]


def _set(db: Session, key: str, value: str) -> None:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    now = datetime.utcnow().isoformat()
    if row:
        row.value = value
        row.updated_at = now
    else:
        db.add(AppConfig(key=key, value=value, updated_at=now))


# ── Schemas ───────────────────────────────────────────────────

class MathPrefsOut(BaseModel):
    default_grade: str
    fluency_daily_target: int
    daily_challenge_enabled: bool


class MathPrefsIn(BaseModel):
    default_grade: Optional[str] = Field(None, pattern="^G[2-6]$")
    fluency_daily_target: Optional[int] = Field(None, ge=1, le=10)
    daily_challenge_enabled: Optional[bool] = None


# ── Endpoints ─────────────────────────────────────────────────

@router.get("/api/math/preferences", response_model=MathPrefsOut)
def get_math_preferences(db: Session = Depends(get_db)):
    """Return current Math module preferences. @tag MATH @tag SETTINGS"""
    return {
        "default_grade": _get(db, _KEY_GRADE),
        "fluency_daily_target": int(_get(db, _KEY_FLUENCY)),
        "daily_challenge_enabled": _get(db, _KEY_DAILY) == "true",
    }


@router.post("/api/math/preferences", response_model=MathPrefsOut)
def save_math_preferences(body: MathPrefsIn, db: Session = Depends(get_db)):
    """Persist Math module preferences. @tag MATH @tag SETTINGS"""
    if body.default_grade is not None:
        _set(db, _KEY_GRADE, body.default_grade)
    if body.fluency_daily_target is not None:
        _set(db, _KEY_FLUENCY, str(body.fluency_daily_target))
    if body.daily_challenge_enabled is not None:
        _set(db, _KEY_DAILY, "true" if body.daily_challenge_enabled else "false")
    db.commit()
    return get_math_preferences(db)
