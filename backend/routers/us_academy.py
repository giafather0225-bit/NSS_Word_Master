"""
routers/us_academy.py — US Academy (미국학교 대비) API
Section: Academy
Dependencies: database, models/us_academy, sm2
API:
  GET  /api/us-academy/words          — level별 단어 목록
  GET  /api/us-academy/words/{id}     — 단어 상세 (정의/예문/동의어/어원)
  GET  /api/us-academy/session        — 현재 세션 상태
  POST /api/us-academy/session/start  — 세션 시작/재개
  POST /api/us-academy/step/complete  — 단어 스텝 완료 기록
  POST /api/us-academy/quiz/result    — Mini Quiz / Unit Test 결과 저장
  GET  /api/us-academy/review/due     — SM-2 복습 대상 단어
  POST /api/us-academy/review/result  — SM-2 복습 결과
  GET  /api/us-academy/passage/{id}   — 독해 지문
  GET  /api/us-academy/stats          — 전체 진도 통계
"""

import json
import logging
from datetime import date as _date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models import USAcademyWord, USAcademyWordProgress, USAcademyPassage, USAcademySession, USAcademyUnitResult
from backend.sm2 import sm2_calculate, quality_from_result

router = APIRouter()

TODAY = lambda: _date.today().isoformat()


# ── Pydantic Schemas ─────────────────────────────────────────

class StartSessionRequest(BaseModel):
    level: int = 1
    unit_number: int = 1

class StepCompleteRequest(BaseModel):
    word_id: int
    step: str          # MEET_IT | SEE_IT | USE_IT | KNOW_IT | OWN_IT
    is_correct: bool = True

class QuizResultRequest(BaseModel):
    level: int
    unit_number: int
    result_type: str   # mini_quiz | unit_test | reading
    score: int
    total: int
    wrong_word_ids: list[int] = []

class ReviewResultRequest(BaseModel):
    word_id: int
    is_correct: bool
    attempts: int = 1


# ── Helper ───────────────────────────────────────────────────

# @tag ACADEMY
def _word_to_dict(w: USAcademyWord) -> dict:
    return {
        "id":             w.id,
        "word":           w.word,
        "level":          w.level,
        "category":       w.category,
        "sort_order":     w.sort_order,
        "definition":     w.definition or "",
        "part_of_speech": w.part_of_speech or "",
        "audio_url":      w.audio_url or "",
        "example_1":      w.example_1 or "",
        "example_2":      w.example_2 or "",
        "synonyms":       json.loads(w.synonyms_json or "[]"),
        "antonyms":       json.loads(w.antonyms_json or "[]"),
        "morphology":     w.morphology or "",
        "word_family":    w.word_family or "",
    }


# @tag ACADEMY
def _progress_to_dict(p: USAcademyWordProgress | None) -> dict:
    if not p:
        return {"steps_completed": 0, "next_review": None}
    return {
        "steps_completed": p.steps_completed,
        "step_meet_it":    bool(p.step_meet_it),
        "step_see_it":     bool(p.step_see_it),
        "step_use_it":     bool(p.step_use_it),
        "step_know_it":    bool(p.step_know_it),
        "step_own_it":     bool(p.step_own_it),
        "correct_count":   p.correct_count,
        "wrong_count":     p.wrong_count,
        "next_review":     p.next_review,
    }


# @tag ACADEMY
def _get_or_create_progress(db: Session, word_id: int, word: str) -> USAcademyWordProgress:
    prog = db.query(USAcademyWordProgress).filter_by(word_id=word_id).first()
    if not prog:
        prog = USAcademyWordProgress(word_id=word_id, word=word)
        db.add(prog)
        db.flush()
    return prog


# ── Routes ───────────────────────────────────────────────────

@router.get("/api/us-academy/words")
# @tag ACADEMY
def get_words(level: int = 1, db: Session = Depends(get_db)):
    """Return all words for a given level, with progress."""
    words = (
        db.query(USAcademyWord)
        .filter_by(level=level, is_active=True)
        .order_by(USAcademyWord.category, USAcademyWord.sort_order)
        .all()
    )
    word_ids = [w.id for w in words]
    progresses = {
        p.word_id: p
        for p in db.query(USAcademyWordProgress)
        .filter(USAcademyWordProgress.word_id.in_(word_ids))
        .all()
    }

    return [
        {**_word_to_dict(w), "progress": _progress_to_dict(progresses.get(w.id))}
        for w in words
    ]


@router.get("/api/us-academy/words/{word_id}")
# @tag ACADEMY
def get_word_detail(word_id: int, db: Session = Depends(get_db)):
    """Return full detail for one word including progress."""
    word = db.query(USAcademyWord).filter_by(id=word_id, is_active=True).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    prog = db.query(USAcademyWordProgress).filter_by(word_id=word_id).first()
    return {**_word_to_dict(word), "progress": _progress_to_dict(prog)}


@router.get("/api/us-academy/session")
# @tag ACADEMY
def get_session(db: Session = Depends(get_db)):
    """Return current active session or None."""
    session = (
        db.query(USAcademySession)
        .filter_by(is_completed=False)
        .order_by(USAcademySession.id.desc())
        .first()
    )
    if not session:
        return {"session": None}
    return {"session": {
        "id":           session.id,
        "level":        session.level,
        "unit_number":  session.unit_number,
        "word_index":   session.word_index,
        "current_step": session.current_step,
        "started_date": session.started_date,
        "last_active":  session.last_active,
    }}


@router.post("/api/us-academy/session/start")
# @tag ACADEMY
def start_session(req: StartSessionRequest, db: Session = Depends(get_db)):
    """Start or resume a session for the given level/unit."""
    try:
        existing = (
            db.query(USAcademySession)
            .filter_by(level=req.level, unit_number=req.unit_number, is_completed=False)
            .first()
        )
        if existing:
            existing.last_active = TODAY()
            db.commit()
            return {"session_id": existing.id, "resumed": True}

        session = USAcademySession(
            level=req.level,
            unit_number=req.unit_number,
            word_index=0,
            current_step="MEET_IT",
            started_date=TODAY(),
            last_active=TODAY(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return {"session_id": session.id, "resumed": False}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("start_session failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start session")


@router.post("/api/us-academy/step/complete")
# @tag ACADEMY
def complete_step(req: StepCompleteRequest, db: Session = Depends(get_db)):
    """Record completion of one learning step for a word."""
    word = db.query(USAcademyWord).filter_by(id=req.word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    try:
        prog = _get_or_create_progress(db, req.word_id, word.word)

        step_map = {
            "MEET_IT": "step_meet_it",
            "SEE_IT":  "step_see_it",
            "USE_IT":  "step_use_it",
            "KNOW_IT": "step_know_it",
            "OWN_IT":  "step_own_it",
        }
        col = step_map.get(req.step)
        if col:
            setattr(prog, col, True)

        if req.is_correct:
            prog.correct_count += 1
        else:
            prog.wrong_count += 1

        prog.steps_completed = sum([
            bool(prog.step_meet_it), bool(prog.step_see_it),
            bool(prog.step_use_it), bool(prog.step_know_it), bool(prog.step_own_it),
        ])
        prog.last_studied = TODAY()

        # Register SM-2 queue when all 5 steps complete
        if prog.steps_completed == 5 and not prog.next_review:
            prog.next_review = (_date.today() + timedelta(days=1)).isoformat()

        db.commit()
        return {"steps_completed": prog.steps_completed, "word": word.word}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("complete_step failed for word_id=%s: %s", req.word_id, e)
        raise HTTPException(status_code=500, detail="Failed to save step progress")


@router.post("/api/us-academy/quiz/result")
# @tag ACADEMY
def save_quiz_result(req: QuizResultRequest, db: Session = Depends(get_db)):
    """Save mini quiz / unit test / reading result."""
    passed = req.total > 0 and (req.score / req.total) >= 0.8
    try:
        result = USAcademyUnitResult(
            level=req.level,
            unit_number=req.unit_number,
            result_type=req.result_type,
            score=req.score,
            total=req.total,
            passed=passed,
            wrong_words_json=json.dumps(req.wrong_word_ids),
            completed_at=TODAY(),
        )
        db.add(result)

        # Register wrong words in SM-2 queue with closer review date
        for wid in req.wrong_word_ids:
            w = db.query(USAcademyWord).filter_by(id=wid).first()
            if not w:
                continue
            prog = _get_or_create_progress(db, wid, w.word)
            prog.wrong_count += 1
            prog.next_review = TODAY()  # review tomorrow for wrong answers

        db.commit()
        return {"passed": passed, "score": req.score, "total": req.total}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("save_quiz_result failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save quiz result")


@router.get("/api/us-academy/review/due")
# @tag ACADEMY
def get_due_reviews(db: Session = Depends(get_db)):
    """Return words due for SM-2 review today."""
    today = TODAY()
    due = (
        db.query(USAcademyWordProgress)
        .filter(USAcademyWordProgress.next_review <= today)
        .order_by(USAcademyWordProgress.next_review)
        .all()
    )
    word_ids = [p.word_id for p in due]
    words = {
        w.id: w
        for w in db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()
    }
    prog_map = {p.word_id: p for p in due}

    result = []
    for wid in word_ids:
        w = words.get(wid)
        p = prog_map.get(wid)
        if w and p:
            result.append({**_word_to_dict(w), "progress": _progress_to_dict(p)})
    return {"due_count": len(result), "words": result}


@router.post("/api/us-academy/review/result")
# @tag ACADEMY
def save_review_result(req: ReviewResultRequest, db: Session = Depends(get_db)):
    """Update SM-2 interval after review."""
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
            prog.correct_count += 1
        else:
            prog.wrong_count += 1

        db.commit()
        return {"next_review": prog.next_review, "interval_days": new_interval}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("us_academy save_review_result failed for word_id=%s: %s", req.word_id, e)
        raise HTTPException(status_code=500, detail="Failed to save review result")


@router.get("/api/us-academy/passage/{passage_id}")
# @tag ACADEMY
def get_passage(passage_id: int, db: Session = Depends(get_db)):
    """Return a reading passage with its comprehension questions."""
    p = db.query(USAcademyPassage).filter_by(id=passage_id, is_active=True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Passage not found")
    return {
        "id":             p.id,
        "title":          p.title or "",
        "text":           p.text,
        "genre":          p.genre or "",
        "lexile":         p.lexile,
        "word_count":     p.word_count,
        "grade_level":    p.grade_level,
        "linked_words":   json.loads(p.linked_words_json or "[]"),
        "questions": {
            "q1": {"text": p.q1_text, "options": json.loads(p.q1_options_json or "[]"), "answer": p.q1_answer},
            "q2": {"text": p.q2_text, "options": json.loads(p.q2_options_json or "[]"), "answer": p.q2_answer},
            "q3": {"text": p.q3_text, "type": "short_write"},
        },
    }


@router.get("/api/us-academy/stats")
# @tag ACADEMY
def get_stats(db: Session = Depends(get_db)):
    """Return overall Academy progress statistics."""
    total_words     = db.query(USAcademyWord).filter_by(is_active=True).count()
    completed_words = db.query(USAcademyWordProgress).filter(
        USAcademyWordProgress.steps_completed == 5
    ).count()
    due_reviews     = db.query(USAcademyWordProgress).filter(
        USAcademyWordProgress.next_review <= TODAY()
    ).count()

    by_level = {}
    for lvl in (1, 2, 3):
        total = db.query(USAcademyWord).filter_by(level=lvl, is_active=True).count()
        ids   = [w.id for w in db.query(USAcademyWord).filter_by(level=lvl, is_active=True).all()]
        done  = db.query(USAcademyWordProgress).filter(
            USAcademyWordProgress.word_id.in_(ids),
            USAcademyWordProgress.steps_completed == 5,
        ).count()
        by_level[f"level_{lvl}"] = {"total": total, "completed": done}

    return {
        "total_words":     total_words,
        "completed_words": completed_words,
        "due_reviews":     due_reviews,
        "by_level":        by_level,
    }
