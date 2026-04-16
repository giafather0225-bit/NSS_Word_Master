"""
routers/collocation.py — Collocation/Chunk Learning bonus stage API
Section: English / Daily Words
Dependencies: models.py (XPLog, DailyWordsProgress), data/daily_words/*.json
API: GET /api/collocation/today, POST /api/collocation/submit
"""

import json
import logging
import random
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import XPLog, DailyWordsProgress
except ImportError:
    from database import get_db
    from models import XPLog, DailyWordsProgress

router = APIRouter()
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "daily_words"

MAX_ITEMS = 5
XP_PER_CORRECT = 3
XP_PERFECT_BONUS = 5


# ─── Helpers ──────────────────────────────────────────────────

def _load_all_words(grade_key: str) -> list[dict]:
    """Flatten all words across weeks from a grade JSON file.

    @tag DAILY_WORDS
    """
    path = DATA_DIR / f"{grade_key}.json"
    if not path.exists():
        logger.warning("Collocation: grade file not found: %s", path)
        return []
    try:
        data = json.loads(path.read_text("utf-8"))
        words: list[dict] = []
        for week in data.get("weeks", []):
            words.extend(week.get("words", []))
        return words
    except Exception as exc:
        logger.error("Collocation: failed to load %s: %s", path, exc)
        return []


# ─── Endpoints ────────────────────────────────────────────────

@router.get("/api/collocation/today")
def collocation_today(grade: int = 0, db: Session = Depends(get_db)):
    """Return up to 5 collocation items drawn from the student's current grade.

    Falls back to DB progress grade; if no progress row exists, uses grade param
    (defaults to 4 when 0).

    @tag DAILY_WORDS
    """
    prog = db.query(DailyWordsProgress).first()
    if prog:
        grade_key = prog.grade          # e.g. "grade_4"
    else:
        effective = grade if grade >= 2 else 4
        grade_key = f"grade_{effective}"

    all_words = _load_all_words(grade_key)
    words_with_col = [w for w in all_words if w.get("collocations")]

    if not words_with_col:
        return {"items": [], "total": 0, "grade": grade_key}

    selected = random.sample(words_with_col, min(MAX_ITEMS, len(words_with_col)))
    items = []
    for w in selected:
        col = random.choice(w["collocations"])
        items.append({
            "word": w["word"],
            "collocation": col,
            "definition": w.get("definition", ""),
            "example": w.get("example", ""),
        })

    return {"items": items, "total": len(items), "grade": grade_key}


# ─── Submit schema ────────────────────────────────────────────

class AnswerItem(BaseModel):
    """Single quiz answer."""
    word: str
    collocation: str
    user_answer: str
    correct: bool


class SubmitIn(BaseModel):
    """POST /api/collocation/submit body."""
    grade: int = 4
    answers: list[AnswerItem]

    def sanitize(self) -> "SubmitIn":
        self.answers = self.answers[:MAX_ITEMS]
        for a in self.answers:
            a.word = a.word.strip()[:80]
            a.collocation = a.collocation.strip()[:200]
            a.user_answer = a.user_answer.strip()[:200]
        return self


@router.post("/api/collocation/submit")
def collocation_submit(body: SubmitIn, db: Session = Depends(get_db)):
    """Grade collocation quiz answers and award XP directly.

    XP: +3 per correct answer (no per-day dedup — bonus stage is replayable).
    Perfect bonus: +5 XP, deduped once per day.

    @tag DAILY_WORDS @tag XP @tag AWARD
    """
    body.sanitize()
    today = date.today().isoformat()
    now = datetime.now().isoformat()

    correct_count = sum(1 for a in body.answers if a.correct)
    total = len(body.answers)
    perfect = (total > 0) and (correct_count == total)

    xp_earned = 0

    # Per-correct XP — no dedup (bonus stage can be replayed)
    for a in body.answers:
        if a.correct:
            db.add(XPLog(
                action="collocation_correct",
                xp_amount=XP_PER_CORRECT,
                detail=a.collocation[:100],
                earned_date=today,
                created_at=now,
            ))
            xp_earned += XP_PER_CORRECT

    # Perfect bonus — deduplicated per day
    if perfect:
        already = db.query(XPLog).filter(
            XPLog.action == "collocation_perfect",
            XPLog.earned_date == today,
        ).first()
        if not already:
            db.add(XPLog(
                action="collocation_perfect",
                xp_amount=XP_PERFECT_BONUS,
                detail="",
                earned_date=today,
                created_at=now,
            ))
            xp_earned += XP_PERFECT_BONUS

    db.commit()

    return {
        "correct_count": correct_count,
        "total": total,
        "xp_earned": xp_earned,
        "perfect": perfect,
    }
