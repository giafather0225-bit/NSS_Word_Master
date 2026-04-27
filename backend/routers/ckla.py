"""
routers/ckla.py — CKLA G3 passage-centric API (학습 흐름)
Section: Academy
Dependencies: models/ckla, models/us_academy, database, services/ckla_grader
API:
  GET  /api/academy/ckla/domains                      — 도메인 목록
  GET  /api/academy/ckla/domains/{domain_num}/lessons — 레슨 목록
  GET  /api/academy/ckla/lessons/{lesson_id}          — 레슨 상세
  GET  /api/academy/ckla/lessons/{lesson_id}/progress — 진행 상태 조회
  POST /api/academy/ckla/lessons/{lesson_id}/progress — 진행 상태 업데이트
  POST /api/academy/ckla/questions/{question_id}/answer — 문제 답변+AI채점
  GET  /api/academy/ckla/words/{word_id}              — 단어 상세

SM-2 복습: routers/ckla_review.py
"""

import json
import logging
from datetime import date as _date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models.ckla import (
    CKLADomain, CKLALesson, CKLAQuestion,
    CKLAWordLesson, CKLALessonProgress, CKLAQuestionResponse,
)
from backend.models.us_academy import USAcademyWord, USAcademyWordProgress
from backend.services.ckla_grader import grade_answer
from backend.services.xp_engine import award_xp

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla"])

NOW = lambda: datetime.now().isoformat(timespec="seconds")


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ProgressUpdate(BaseModel):
    reading_done:   bool | None = None
    vocab_done:     bool | None = None
    word_work_done: bool | None = None


class AnswerSubmit(BaseModel):
    user_answer: str   # AI가 자동 채점 — 점수/피드백은 호출자가 보내지 않음


# ── Helpers ───────────────────────────────────────────────────────────────────

# @tag ACADEMY
def _get_or_create_progress(db: Session, lesson_id: int) -> CKLALessonProgress:
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    if not prog:
        prog = CKLALessonProgress(lesson_id=lesson_id)
        db.add(prog)
        db.flush()
    return prog


# @tag ACADEMY
def _progress_dict(p: CKLALessonProgress | None) -> dict:
    if not p:
        return {
            "reading_done": False, "reading_done_at": None,
            "vocab_done": False, "word_work_done": False,
            "questions_attempted": 0, "questions_correct": 0,
            "completed": False, "completed_at": None, "last_active": None,
        }
    return {
        "reading_done":        bool(p.reading_done),
        "reading_done_at":     p.reading_done_at,
        "vocab_done":          bool(p.vocab_done),
        "word_work_done":      bool(p.word_work_done),
        "questions_attempted": p.questions_attempted or 0,
        "questions_correct":   p.questions_correct or 0,
        "completed":           bool(p.completed),
        "completed_at":        p.completed_at,
        "last_active":         p.last_active,
    }


# @tag ACADEMY
def _word_dict(w: USAcademyWord) -> dict:
    """단어 직렬화. synonyms_json에 MW all_defs 저장돼 있음."""
    return {
        "id":             w.id,
        "word":           w.word,
        "definition":     w.definition or "",
        "part_of_speech": w.part_of_speech or "",
        "audio_url":      w.audio_url or "",
        "example_1":      w.example_1 or "",
        "all_defs":       json.loads(w.synonyms_json or "[]"),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/domains")
# @tag ACADEMY
def get_domains(db: Session = Depends(get_db)):
    """11개 CKLA 도메인 목록."""
    domains = (
        db.query(CKLADomain)
        .filter_by(is_active=True)
        .order_by(CKLADomain.domain_num)
        .all()
    )
    return [
        {
            "id":           d.id,
            "domain_num":   d.domain_num,
            "title":        d.title,
            "lesson_count": d.lesson_count,
        }
        for d in domains
    ]


@router.get("/domains/{domain_num}/lessons")
# @tag ACADEMY
def get_lessons(domain_num: int, db: Session = Depends(get_db)):
    """도메인 내 레슨 목록 (passage 제외, 진행 상태 포함)."""
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    lessons = (
        db.query(CKLALesson)
        .filter_by(domain_id=domain.id, is_active=True)
        .order_by(CKLALesson.lesson_num)
        .all()
    )
    lesson_ids = [l.id for l in lessons]
    prog_map = {
        p.lesson_id: p
        for p in db.query(CKLALessonProgress)
        .filter(CKLALessonProgress.lesson_id.in_(lesson_ids))
        .all()
    }

    return {
        "domain": {"id": domain.id, "domain_num": domain_num, "title": domain.title},
        "lessons": [
            {
                "id":             l.id,
                "lesson_num":     l.lesson_num,
                "title":          l.title,
                "passage_chars":  l.passage_chars,
                "word_work_word": l.word_work_word or "",
                "progress":       _progress_dict(prog_map.get(l.id)),
            }
            for l in lessons
        ],
    }


@router.get("/lessons/{lesson_id}")
# @tag ACADEMY
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """레슨 상세: passage + vocab(정의 포함) + 문제."""
    lesson = db.query(CKLALesson).filter_by(id=lesson_id, is_active=True).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    domain = db.query(CKLADomain).filter_by(id=lesson.domain_id).first()

    # 단어: word_lesson 링크 경유
    word_ids = [
        wl.word_id
        for wl in db.query(CKLAWordLesson).filter_by(lesson_id=lesson_id).all()
    ]
    words = (
        db.query(USAcademyWord)
        .filter(USAcademyWord.id.in_(word_ids))
        .order_by(USAcademyWord.word)
        .all()
    ) if word_ids else []

    questions = (
        db.query(CKLAQuestion)
        .filter_by(lesson_id=lesson_id)
        .order_by(CKLAQuestion.question_num)
        .all()
    )
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()

    return {
        "id":             lesson.id,
        "domain_num":     lesson.domain_num,
        "domain_title":   domain.title if domain else "",
        "lesson_num":     lesson.lesson_num,
        "title":          lesson.title,
        "passage":        lesson.passage,
        "passage_chars":  lesson.passage_chars,
        "word_work_word": lesson.word_work_word or "",
        "vocab": [_word_dict(w) for w in words],
        "questions": [
            {
                "id":           q.id,
                "num":          q.question_num,
                "kind":         q.kind,
                "question":     q.question_text,
                "model_answer": q.model_answer or "",
            }
            for q in questions
        ],
        "progress": _progress_dict(prog),
    }


@router.get("/lessons/{lesson_id}/progress")
# @tag ACADEMY
def get_lesson_progress(lesson_id: int, db: Session = Depends(get_db)):
    """레슨 진행 상태 조회."""
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    return _progress_dict(prog)


@router.post("/lessons/{lesson_id}/progress")
# @tag ACADEMY @tag XP @tag SM2
def update_lesson_progress(
    lesson_id: int, req: ProgressUpdate, db: Session = Depends(get_db)
):
    """읽기/단어/Word Work 완료 기록.
    - vocab_done 최초 True → 레슨 단어 SM-2 큐 등록 + XP
    - reading_done 최초 True → XP
    - 세 항목 모두 완료 → 레슨 완료 XP 보너스
    """
    if not db.query(CKLALesson).filter_by(id=lesson_id).first():
        raise HTTPException(status_code=404, detail="Lesson not found")

    try:
        prog = _get_or_create_progress(db, lesson_id)
        now  = NOW()

        if req.reading_done is True and not prog.reading_done:
            prog.reading_done    = True
            prog.reading_done_at = now
            award_xp(db, "ckla_reading_done", detail=str(lesson_id))

        if req.vocab_done is True and not prog.vocab_done:
            prog.vocab_done = True
            award_xp(db, "ckla_vocab_done", detail=str(lesson_id))
            # ── SM-2 연동: 레슨 단어 전체를 내일 복습 대상으로 등록 ──
            word_links = db.query(CKLAWordLesson).filter_by(lesson_id=lesson_id).all()
            word_ids   = [wl.word_id for wl in word_links]
            tomorrow   = (_date.today() + timedelta(days=1)).isoformat()
            today_str  = _date.today().isoformat()

            # 이미 progress 있는 word_id 제외
            existing_ids = {
                p.word_id for p in
                db.query(USAcademyWordProgress)
                .filter(USAcademyWordProgress.word_id.in_(word_ids))
                .all()
            }
            word_map = {
                w.id: w for w in
                db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()
            }
            for wid in word_ids:
                if wid not in existing_ids and wid in word_map:
                    db.add(USAcademyWordProgress(
                        word_id=wid,
                        word=word_map[wid].word,
                        next_review=tomorrow,
                        last_studied=today_str,
                    ))

        if req.word_work_done is True and not prog.word_work_done:
            prog.word_work_done = True

        prog.last_active = now

        # 전체 완료 체크
        if (prog.reading_done and prog.vocab_done and prog.word_work_done
                and not prog.completed):
            prog.completed    = True
            prog.completed_at = now
            award_xp(db, "ckla_lesson_complete", detail=str(lesson_id))

        db.commit()
        return _progress_dict(prog)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("update_lesson_progress failed for lesson_id=%s: %s", lesson_id, e)
        raise HTTPException(status_code=500, detail="Failed to update lesson progress")


@router.post("/questions/{question_id}/answer")
# @tag ACADEMY @tag AI
async def submit_answer(
    question_id: int, req: AnswerSubmit, db: Session = Depends(get_db)
):
    """문제 답변 제출 → AI 자동 채점 → 결과 저장 + 즉시 반환.

    AI (Ollama → Gemini 폴백) 가 Socratic 피드백과 점수(0-2)를 생성.
    Evaluative 1점 답변 및 AI 오류 시 needs_parent_review=True.
    """
    question = db.query(CKLAQuestion).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 지문 로드 (채점 컨텍스트용)
    lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
    passage = lesson.passage if lesson else ""

    try:
        # AI 채점
        result = await grade_answer(
            question_text=question.question_text,
            kind=question.kind,
            model_answer=question.model_answer or "",
            passage=passage,
            user_answer=req.user_answer,
        )
    except Exception as e:
        logger.error("CKLA grade_answer failed for question_id=%s: %s", question_id, e)
        raise HTTPException(status_code=503, detail="Grading service unavailable")

    try:
        # 진행 상태 업데이트
        prog = _get_or_create_progress(db, question.lesson_id)

        response = CKLAQuestionResponse(
            question_id=question_id,
            lesson_progress_id=prog.id,
            user_answer=req.user_answer,
            ai_score=result.score,
            ai_feedback=result.feedback,
            needs_parent_review=result.needs_parent_review,
            created_at=NOW(),
        )
        db.add(response)

        prog.questions_attempted = (prog.questions_attempted or 0) + 1
        if result.score == 2:
            prog.questions_correct = (prog.questions_correct or 0) + 1
        prog.last_active = NOW()

        db.commit()
        db.refresh(response)
        return {
            "id":                  response.id,
            "ai_score":            response.ai_score,
            "ai_feedback":         response.ai_feedback or "",
            "needs_parent_review": bool(response.needs_parent_review),
            "provider":            result.provider,
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("submit_answer DB save failed for question_id=%s: %s", question_id, e)
        raise HTTPException(status_code=500, detail="Failed to save answer")


@router.get("/words/{word_id}")
# @tag ACADEMY
def get_word(word_id: int, db: Session = Depends(get_db)):
    """CKLA 단어 상세 (definition + audio + all_defs)."""
    word = db.query(USAcademyWord).filter_by(id=word_id, is_active=True).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return _word_dict(word)


