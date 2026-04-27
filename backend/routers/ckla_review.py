"""
routers/ckla_review.py — CKLA 단어 SM-2 복습 엔드포인트
Section: Academy
Dependencies: models/us_academy, database, sm2
API:
  GET  /api/academy/ckla/review/due    — 오늘 복습 대상 CKLA 단어
  POST /api/academy/ckla/review/result — SM-2 복습 결과 저장
"""

import json
import logging
from datetime import date as _date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models.us_academy import USAcademyWord, USAcademyWordProgress
from backend.sm2 import sm2_calculate, quality_from_result

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla-review"])

TODAY = lambda: _date.today().isoformat()


class ReviewResult(BaseModel):
    word_id:    int
    is_correct: bool
    attempts:   int = 1


# @tag ACADEMY
def _ckla_word_ids(db: Session) -> list[int]:
    """domain_num IS NOT NULL인 CKLA 단어 id 목록 (raw SQL — 모델에 없는 컬럼)."""
    rows = db.execute(
        text("SELECT id FROM us_academy_words WHERE domain_num IS NOT NULL AND is_active=1")
    ).fetchall()
    return [r[0] for r in rows]


# @tag ACADEMY
def _word_dict(w: USAcademyWord) -> dict:
    return {
        "id":             w.id,
        "word":           w.word,
        "definition":     w.definition or "",
        "part_of_speech": w.part_of_speech or "",
        "audio_url":      w.audio_url or "",
        "example_1":      w.example_1 or "",
        "all_defs":       json.loads(w.synonyms_json or "[]"),
    }


@router.get("/review/due")
# @tag ACADEMY @tag SM2
def get_due_reviews(db: Session = Depends(get_db)):
    """오늘 SM-2 복습 대상 CKLA 단어."""
    today    = TODAY()
    ckla_ids = _ckla_word_ids(db)
    if not ckla_ids:
        return {"due_count": 0, "words": []}

    due = (
        db.query(USAcademyWordProgress)
        .filter(
            USAcademyWordProgress.word_id.in_(ckla_ids),
            USAcademyWordProgress.next_review <= today,
        )
        .order_by(USAcademyWordProgress.next_review)
        .all()
    )
    word_map = {
        w.id: w
        for w in db.query(USAcademyWord)
        .filter(USAcademyWord.id.in_([p.word_id for p in due]))
        .all()
    }
    return {
        "due_count": len(due),
        "words": [
            {**_word_dict(word_map[p.word_id]), "next_review": p.next_review}
            for p in due
            if p.word_id in word_map
        ],
    }


@router.post("/review/result")
# @tag ACADEMY @tag SM2
def save_review_result(req: ReviewResult, db: Session = Depends(get_db)):
    """SM-2 복습 결과 저장 → 다음 복습일 계산."""
    prog = db.query(USAcademyWordProgress).filter_by(word_id=req.word_id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Progress not found")

    quality = quality_from_result(req.is_correct, req.attempts)
    new_interval, new_easiness, new_reps = sm2_calculate(
        quality, prog.sm2_repetitions, prog.sm2_easiness, prog.sm2_interval
    )

    try:
        prog.sm2_interval    = new_interval
        prog.sm2_easiness    = new_easiness
        prog.sm2_repetitions = new_reps
        prog.next_review     = (_date.today() + timedelta(days=new_interval)).isoformat()

        if req.is_correct:
            prog.correct_count = (prog.correct_count or 0) + 1
        else:
            prog.wrong_count = (prog.wrong_count or 0) + 1

        db.commit()
        return {"next_review": prog.next_review, "interval_days": new_interval}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("ckla save_review_result failed for word_id=%s: %s", req.word_id, e)
        raise HTTPException(status_code=500, detail="Failed to save review result")
