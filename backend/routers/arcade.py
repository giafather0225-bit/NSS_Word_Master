"""
routers/arcade.py — Arcade mini-games API
Section: System
Dependencies: services/xp_engine.py, models.py (Word, StudyItem, AppConfig, XPLog)
API:
  GET  /api/arcade/words          — word pool for games
  GET  /api/arcade/best/{game}    — personal best score
  POST /api/arcade/score          — report game result; award tier XP; update best
"""

import json
import logging
import random
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Word, StudyItem, AppConfig, WordReview
from backend.services.xp_engine import (
    award_arcade_xp,
    score_to_arcade_tier,
    ARCADE_DAILY_CAP,
)
from backend.services import streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

_BEST_KEY_PREFIX = "arcade_best_"
_DUE_BOOST = 3  # how many times a due word appears in the weighted pool


def _short_def(text: str) -> str:
    """Return the first clause of a definition, capped to 80 chars."""
    t = text.replace("\n", " ").strip()
    for sep in (";", ". ", " — ", " - "):
        if sep in t:
            t = t.split(sep, 1)[0]
            break
    return t[:80].strip()


def _best_key(game: str, level: str = "") -> str:
    """Compose the AppConfig key for a PB entry, optionally scoped by level."""
    level = (level or "").strip().lower()
    return _BEST_KEY_PREFIX + game + (f"_{level}" if level else "")


def _get_best(db: Session, game: str, level: str = "") -> dict:
    """Read personal-best entry. Returns {score, date} or zeros."""
    row = db.query(AppConfig).filter(AppConfig.key == _best_key(game, level)).first()
    if not row or not row.value:
        return {"score": 0, "date": ""}
    try:
        data = json.loads(row.value)
        return {"score": int(data.get("score", 0)), "date": str(data.get("date", ""))}
    except (ValueError, TypeError):
        return {"score": 0, "date": ""}


def _set_best(db: Session, game: str, score: int, level: str = "") -> None:
    """Persist a new personal-best entry (scoped by level when provided)."""
    key = _best_key(game, level)
    payload = json.dumps({"score": score, "date": date.today().isoformat()})
    now = datetime.now().isoformat()
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if row:
        row.value = payload
        row.updated_at = now
    else:
        db.add(AppConfig(key=key, value=payload, updated_at=now))
    db.commit()


def _fallback_words(db: Session) -> list[dict]:
    """Combined global pool: Word table + StudyItem table (de-duplicated)."""
    out: list[dict] = []
    seen: set[str] = set()
    for r in db.query(Word).filter(Word.word.isnot(None), Word.definition.isnot(None)).all():
        w = (r.word or "").strip()
        d = (r.definition or "").strip()
        if not (w and d) or not w.isascii():
            continue
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"word": w, "definition": _short_def(d)})
    for it in (
        db.query(StudyItem)
        .filter(
            StudyItem.subject == "English",
            StudyItem.answer.isnot(None),
            StudyItem.question.isnot(None),
        )
        .all()
    ):
        w = (it.answer or "").strip()
        d = (it.question or "").strip()
        if not (w and d) or not w.isascii():
            continue
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"word": w, "definition": _short_def(d)})
    return out


def _due_word_set(db: Session) -> set[str]:
    """Lowercase set of words whose SM-2 next_review <= today."""
    today_str = date.today().isoformat()
    rows = (
        db.query(WordReview.word)
        .filter(WordReview.next_review <= today_str, WordReview.word.isnot(None))
        .all()
    )
    return {(w or "").strip().lower() for (w,) in rows if (w or "").strip()}


# @tag ARCADE
@router.get("/api/arcade/words")
def arcade_words(count: int = 40, db: Session = Depends(get_db)) -> dict:
    """Return a weighted, shuffled word pool for arcade games.

    Pool: combined Word + StudyItem (English) global pool, de-duplicated.
    SM-2 due words (WordReview.next_review <= today) are duplicated
    `_DUE_BOOST` times to bias spawn frequency.
    """
    count = max(10, min(200, int(count)))

    # Full pool — include all known words (learned or not) for maximum variety.
    base = _fallback_words(db)

    due = _due_word_set(db) if base else set()
    weighted: list[dict] = []
    due_count = 0
    for entry in base:
        if entry["word"].lower() in due:
            due_count += 1
            for _ in range(_DUE_BOOST):
                weighted.append(entry)
        else:
            weighted.append(entry)

    random.shuffle(weighted)
    return {
        "words": weighted[:count],
        "source": "all",
        "unique_count": len(base),
        "due_count": due_count,
    }


# @tag ARCADE
@router.get("/api/arcade/best/{game}")
def arcade_best(game: str, level: str = "", db: Session = Depends(get_db)) -> dict:
    """Return personal best score for a given arcade game (optionally per level)."""
    return _get_best(db, game, level)


class ScoreRequest(BaseModel):
    """POST /api/arcade/score body."""
    game: str
    score: int
    correct: int
    total: int
    accuracy: float
    level: str = ""


# @tag ARCADE @tag XP
@router.post("/api/arcade/score")
def arcade_score(req: ScoreRequest, db: Session = Depends(get_db)) -> dict:
    """Record a game result; award tier-based XP; update personal best.

    XP tiers: 500+=1, 1000+=2, 2000+=3. Daily cap defined by ARCADE_DAILY_CAP.
    """
    xp_result = award_arcade_xp(db, req.score, game=req.game)

    prev_best = _get_best(db, req.game, req.level)
    new_best = req.score > prev_best["score"]
    if new_best:
        _set_best(db, req.game, req.score, req.level)

    try:
        streak_engine.mark_game_done(db)
    except Exception as e:
        logger.warning("Streak game mark failed: %s", e)

    return {
        "tier": xp_result["tier"],
        "xp_awarded": xp_result["xp_awarded"],
        "daily_total": xp_result["daily_total"],
        "daily_cap": xp_result["daily_cap"],
        "best_score": req.score if new_best else prev_best["score"],
        "new_best": new_best,
        "prev_best": prev_best["score"],
    }
