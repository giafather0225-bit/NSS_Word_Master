"""
routers/growth_theme.py — Growth Theme progress API
Section: Growth Theme
Dependencies: models.py (GrowthThemeProgress, GrowthEvent),
              services/xp_engine.py
API: GET /api/growth/theme, GET /api/growth/theme/all,
     POST /api/growth/theme/select, POST /api/growth/theme/advance
"""

import logging
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import GrowthThemeProgress, GrowthEvent
    from ..services import xp_engine
except ImportError:
    from database import get_db
    from models import GrowthThemeProgress, GrowthEvent
    from services import xp_engine

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────

THEMES = ["space", "tree", "city", "animal", "ocean"]
VARIATIONS = [1, 2, 3]
MAX_STEPS = 6  # steps 0–5

# Total XP required to reach each step (index = step number)
XP_THRESHOLDS = [0, 100, 300, 600, 1000, 1500]

THEME_LABELS = {
    "space":  "🚀 Space Explorer",
    "tree":   "🌳 Growing Tree",
    "city":   "🏙️ My City",
    "animal": "🦁 Animal Kingdom",
    "ocean":  "🌊 Ocean World",
}

EVENT_ICONS = {
    "space": "🚀", "tree": "🌳", "city": "🏙️",
    "animal": "🦁", "ocean": "🌊",
}


# ─── Schemas ──────────────────────────────────────────────────

class SelectThemeIn(BaseModel):
    theme:     str
    variation: int = 1  # 1, 2, or 3


# ─── Helpers ──────────────────────────────────────────────────

def _get_active(db: Session) -> GrowthThemeProgress | None:
    """Return the currently active theme row. @tag GROWTH_THEME"""
    return db.query(GrowthThemeProgress).filter(GrowthThemeProgress.is_active == True).first()


def _target_step(total_xp: int) -> int:
    """Return the step the user should be on given their total XP. @tag GROWTH_THEME"""
    step = 0
    for i, threshold in enumerate(XP_THRESHOLDS):
        if total_xp >= threshold:
            step = i
    return min(step, MAX_STEPS - 1)


def _theme_dict(t: GrowthThemeProgress) -> dict:
    """Serialize a GrowthThemeProgress row. @tag GROWTH_THEME"""
    next_xp = XP_THRESHOLDS[t.current_step + 1] if t.current_step < MAX_STEPS - 1 else None
    return {
        "id":           t.id,
        "theme":        t.theme,
        "label":        THEME_LABELS.get(t.theme, t.theme),
        "variation":    t.variation,
        "current_step": t.current_step,
        "is_completed": t.is_completed,
        "is_active":    t.is_active,
        "started_at":   t.started_at,
        "completed_at": t.completed_at,
        "img_url":      f"/static/img/themes/{t.theme}/step_{t.current_step}_v{t.variation}.svg",
        "next_xp_threshold": next_xp,
        "xp_thresholds": XP_THRESHOLDS,
    }


# ─── Endpoints ────────────────────────────────────────────────

@router.get("/api/growth/theme")
def get_active_theme(db: Session = Depends(get_db)):
    """
    Return the currently active theme with XP progress info.
    @tag GROWTH_THEME
    """
    active = _get_active(db)
    total_xp = xp_engine.get_total_xp(db)

    if not active:
        return {
            "active": None,
            "total_xp": total_xp,
            "xp_thresholds": XP_THRESHOLDS,
            "themes": THEMES,
        }

    return {
        "active":   _theme_dict(active),
        "total_xp": total_xp,
        "xp_thresholds": XP_THRESHOLDS,
        "themes":   THEMES,
    }


@router.get("/api/growth/theme/all")
def get_all_themes(db: Session = Depends(get_db)):
    """
    Return all theme rows with progress. Used in My Worlds (Diary).
    @tag GROWTH_THEME
    """
    rows = db.query(GrowthThemeProgress).all()
    existing = {r.theme: r for r in rows}
    result = []
    for theme in THEMES:
        if theme in existing:
            result.append(_theme_dict(existing[theme]))
        else:
            result.append({
                "theme": theme, "label": THEME_LABELS.get(theme, theme),
                "variation": 1, "current_step": 0,
                "is_completed": False, "is_active": False,
                "img_url": f"/static/img/themes/{theme}/step_0_v1.svg",
                "xp_thresholds": XP_THRESHOLDS,
            })
    return {"themes": result}


@router.post("/api/growth/theme/select")
def select_theme(body: SelectThemeIn, db: Session = Depends(get_db)):
    """
    Activate a theme (create row if first time, deactivate others).
    @tag GROWTH_THEME
    """
    if body.theme not in THEMES:
        raise HTTPException(status_code=400, detail=f"Unknown theme. Valid: {THEMES}")
    if body.variation not in VARIATIONS:
        raise HTTPException(status_code=400, detail="Variation must be 1, 2, or 3")

    # Deactivate all
    db.query(GrowthThemeProgress).update({"is_active": False})

    # Find or create
    existing = db.query(GrowthThemeProgress).filter(
        GrowthThemeProgress.theme == body.theme
    ).first()

    now = datetime.now().isoformat()
    if existing:
        existing.is_active  = True
        existing.variation  = body.variation
    else:
        existing = GrowthThemeProgress(
            theme=body.theme, variation=body.variation,
            current_step=0, is_completed=False, is_active=True,
            started_at=now, completed_at=None,
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return {"ok": True, "theme": _theme_dict(existing)}


@router.post("/api/growth/theme/advance")
def advance_theme(db: Session = Depends(get_db)):
    """
    Check XP and advance the active theme to the correct step.
    Creates GrowthEvent on each new step and on completion.
    @tag GROWTH_THEME XP
    """
    active = _get_active(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active theme. Select one first.")

    total_xp   = xp_engine.get_total_xp(db)
    target     = _target_step(total_xp)
    advanced   = []
    now_str    = datetime.now().isoformat()
    today_str  = date.today().isoformat()

    while active.current_step < target:
        active.current_step += 1
        new_step = active.current_step
        advanced.append(new_step)

        # GrowthEvent for each step gained
        db.add(GrowthEvent(
            event_type=f"theme_step_{new_step}",
            title=f"{THEME_LABELS.get(active.theme, active.theme)} — Step {new_step} reached!",
            detail="",
            event_date=today_str,
            created_at=now_str,
        ))

        # Theme complete at step 5
        if new_step == MAX_STEPS - 1 and not active.is_completed:
            active.is_completed = True
            active.completed_at = now_str
            db.add(GrowthEvent(
                event_type="theme_complete",
                title=f"🎉 {THEME_LABELS.get(active.theme, active.theme)} Complete!",
                detail="",
                event_date=today_str,
                created_at=now_str,
            ))

    db.commit()
    db.refresh(active)

    return {
        "ok":           True,
        "advanced":     advanced,
        "theme":        _theme_dict(active),
        "total_xp":     total_xp,
    }
