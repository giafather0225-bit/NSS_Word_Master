"""
routers/ckla.py — CKLA grade-aware reading curriculum API
Section: Academy
Dependencies: models/ckla, models/us_academy, database, services/ckla_grader
API:
  GET  /api/academy/ckla/grades                       — available grades
  GET  /api/academy/ckla/title                        — localized grade title
  GET  /api/academy/ckla/domains                      — domain list (grade-aware)
  GET  /api/academy/ckla/domains/{domain_num}/lessons — lesson list
  GET  /api/academy/ckla/lessons/{lesson_id}          — lesson detail
  GET  /api/academy/ckla/lessons/{lesson_id}/progress — progress query
  POST /api/academy/ckla/lessons/{lesson_id}/progress — progress update
  POST /api/academy/ckla/lessons/{lesson_id}/difficulty — rate difficulty
  POST /api/academy/ckla/questions/{question_id}/answer — AI graded answer
  GET  /api/academy/ckla/words/{word_id}              — word detail
  GET  /api/academy/ckla/badges                       — badge gallery
  POST /api/academy/ckla/badges/check                 — check + award new badges
  GET  /api/academy/ckla/domain-test/{domain_num}     — domain test questions
  POST /api/academy/ckla/domain-test/{domain_num}/submit — submit domain test
  GET  /api/academy/ckla/grade-final-test             — grade final test questions
  POST /api/academy/ckla/grade-final-test/submit      — submit grade final test

SM-2 review: routers/ckla_review.py
"""

import json
import logging
import random
from datetime import date as _date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models.ckla import (
    CKLADomain, CKLALesson, CKLAQuestion,
    CKLAWordLesson, CKLALessonProgress, CKLAQuestionResponse,
    CKLABadge, CKLAUserBadge,
)
from backend.models.us_academy import USAcademyWord, USAcademyWordProgress
from backend.services.ckla_grader import grade_answer
from backend.services.xp_engine import award_xp
from backend.services.streak_engine import mark_ckla_done

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla"])

NOW = lambda: datetime.now().isoformat(timespec="seconds")

# Grades currently supported (expand as content is added)
_SUPPORTED_GRADES = [3]
_GRADE_TITLES = {3: "Grade 3"}


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ProgressUpdate(BaseModel):
    reading_done:   bool | None = None
    vocab_done:     bool | None = None
    word_work_done: bool | None = None


class AnswerSubmit(BaseModel):
    user_answer: str


class DifficultyRating(BaseModel):
    rating: str = Field(..., pattern="^(easy|neutral|hard)$")


class DomainTestSubmit(BaseModel):
    answers: dict[int, str]   # {question_id: user_answer}


class GradeFinalTestSubmit(BaseModel):
    answers: dict[int, str]


# ── Helpers ───────────────────────────────────────────────────────────────────

# @tag ACADEMY CKLA
def _get_or_create_progress(db: Session, lesson_id: int) -> CKLALessonProgress:
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    if not prog:
        lesson = db.query(CKLALesson).filter_by(id=lesson_id).first()
        prog = CKLALessonProgress(
            lesson_id=lesson_id,
            grade=lesson.grade if lesson else 3,
            started_at=NOW(),
        )
        db.add(prog)
        db.flush()
    return prog


# @tag ACADEMY CKLA
def _progress_dict(p: CKLALessonProgress | None) -> dict:
    if not p:
        return {
            "reading_done": False, "reading_done_at": None,
            "vocab_done": False, "word_work_done": False,
            "questions_attempted": 0, "questions_correct": 0,
            "completed": False, "completed_at": None, "last_active": None,
            "started_at": None, "difficulty_rating": None, "grade": 3,
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
        "started_at":          p.started_at,
        "difficulty_rating":   p.difficulty_rating,
        "grade":               p.grade or 3,
    }


# @tag ACADEMY CKLA
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


# @tag ACADEMY CKLA
def _badge_dict(b: CKLABadge, earned_at: str | None = None) -> dict:
    return {
        "badge_key":       b.badge_key,
        "badge_name":      b.badge_name,
        "description":     b.description,
        "condition_type":  b.condition_type,
        "condition_value": b.condition_value,
        "image_path":      b.image_path,
        "earned":          earned_at is not None,
        "earned_at":       earned_at,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/grades")
# @tag ACADEMY CKLA
def get_grades(db: Session = Depends(get_db)):
    """Available CKLA grades with lesson counts."""
    result = []
    for g in _SUPPORTED_GRADES:
        count = (
            db.query(CKLALesson)
            .join(CKLADomain, CKLALesson.domain_id == CKLADomain.id)
            .filter(CKLADomain.grade == g, CKLADomain.is_active == True, CKLALesson.is_active == True)
            .count()
        )
        result.append({"grade": g, "title": _GRADE_TITLES.get(g, f"Grade {g}"), "lesson_count": count})
    return result


@router.get("/title")
# @tag ACADEMY CKLA
def get_title(grade: int = Query(3), db: Session = Depends(get_db)):
    """Return localized title string for the given grade."""
    if grade not in _SUPPORTED_GRADES:
        raise HTTPException(status_code=404, detail="Grade not available")
    return {"grade": grade, "title": _GRADE_TITLES.get(grade, f"Grade {grade}")}


@router.get("/domains")
# @tag ACADEMY CKLA
def get_domains(grade: int = Query(3), db: Session = Depends(get_db)):
    """Domain list for the given grade."""
    domains = (
        db.query(CKLADomain)
        .filter_by(is_active=True, grade=grade)
        .order_by(CKLADomain.domain_num)
        .all()
    )
    return [
        {
            "id":           d.id,
            "domain_num":   d.domain_num,
            "title":        d.title,
            "lesson_count": d.lesson_count,
            "grade":        d.grade,
        }
        for d in domains
    ]


@router.get("/domains/{domain_num}/lessons")
# @tag ACADEMY CKLA
def get_lessons(domain_num: int, grade: int = Query(3), db: Session = Depends(get_db)):
    """Lesson list for domain (passage excluded, progress included)."""
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
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
        "domain": {"id": domain.id, "domain_num": domain_num, "title": domain.title, "grade": grade},
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
# @tag ACADEMY CKLA
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """Lesson detail: passage + vocab + questions + progress."""
    lesson = db.query(CKLALesson).filter_by(id=lesson_id, is_active=True).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    domain = db.query(CKLADomain).filter_by(id=lesson.domain_id).first()

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
        "grade":          lesson.grade,
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
# @tag ACADEMY CKLA
def get_lesson_progress(lesson_id: int, db: Session = Depends(get_db)):
    """Progress state for a lesson."""
    prog = db.query(CKLALessonProgress).filter_by(lesson_id=lesson_id).first()
    return _progress_dict(prog)


@router.post("/lessons/{lesson_id}/progress")
# @tag ACADEMY CKLA XP STREAK
def update_lesson_progress(
    lesson_id: int, req: ProgressUpdate, db: Session = Depends(get_db)
):
    """Record reading / vocab / Word Work completion.
    - All three done (first time) → XP ckla_lesson_complete + mark_ckla_done (streak)
    """
    lesson = db.query(CKLALesson).filter_by(id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    try:
        prog = _get_or_create_progress(db, lesson_id)
        now  = NOW()

        if req.reading_done is True and not prog.reading_done:
            prog.reading_done    = True
            prog.reading_done_at = now

        if req.vocab_done is True and not prog.vocab_done:
            prog.vocab_done = True
            # Register lesson words in SM-2 queue for tomorrow
            word_links = db.query(CKLAWordLesson).filter_by(lesson_id=lesson_id).all()
            word_ids   = [wl.word_id for wl in word_links]
            tomorrow   = (_date.today() + timedelta(days=1)).isoformat()
            today_str  = _date.today().isoformat()

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

        # Lesson complete: all three tabs done for the first time
        if (prog.reading_done and prog.vocab_done and prog.word_work_done
                and not prog.completed):
            prog.completed    = True
            prog.completed_at = now
            award_xp(db, "ckla_lesson_complete", detail=str(lesson_id))
            mark_ckla_done(db)

        db.commit()
        return _progress_dict(prog)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("update_lesson_progress failed lesson_id=%s: %s", lesson_id, e)
        raise HTTPException(status_code=500, detail="Failed to update lesson progress")


@router.post("/lessons/{lesson_id}/difficulty")
# @tag ACADEMY CKLA
def rate_difficulty(
    lesson_id: int, req: DifficultyRating, db: Session = Depends(get_db)
):
    """Save student difficulty rating (easy / neutral / hard) for a lesson."""
    lesson = db.query(CKLALesson).filter_by(id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    try:
        prog = _get_or_create_progress(db, lesson_id)
        prog.difficulty_rating = req.rating
        db.commit()
        return {"lesson_id": lesson_id, "difficulty_rating": req.rating}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("rate_difficulty failed lesson_id=%s: %s", lesson_id, e)
        raise HTTPException(status_code=500, detail="Failed to save difficulty rating")


@router.post("/questions/{question_id}/answer")
# @tag ACADEMY CKLA AI
async def submit_answer(
    question_id: int, req: AnswerSubmit, db: Session = Depends(get_db)
):
    """Submit an answer → AI grading → save result."""
    question = db.query(CKLAQuestion).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
    passage = lesson.passage if lesson else ""

    try:
        result = await grade_answer(
            question_text=question.question_text,
            kind=question.kind,
            model_answer=question.model_answer or "",
            passage=passage,
            user_answer=req.user_answer,
        )
    except Exception as e:
        logger.error("CKLA grade_answer failed question_id=%s: %s", question_id, e)
        raise HTTPException(status_code=503, detail="Grading service unavailable")

    try:
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
        logger.error("submit_answer DB save failed question_id=%s: %s", question_id, e)
        raise HTTPException(status_code=500, detail="Failed to save answer")


@router.get("/words/{word_id}")
# @tag ACADEMY CKLA
def get_word(word_id: int, db: Session = Depends(get_db)):
    """CKLA word detail."""
    word = db.query(USAcademyWord).filter_by(id=word_id, is_active=True).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return _word_dict(word)


# ── Badges ────────────────────────────────────────────────────────────────────

@router.get("/badges")
# @tag ACADEMY CKLA
def get_badges(grade: int = Query(3), db: Session = Depends(get_db)):
    """Badge gallery: all badges (earned flag included)."""
    badges = db.query(CKLABadge).order_by(CKLABadge.condition_value).all()
    earned_map = {
        ub.badge_key: ub.earned_at
        for ub in db.query(CKLAUserBadge).all()
    }
    return [_badge_dict(b, earned_map.get(b.badge_key)) for b in badges]


@router.post("/badges/check")
# @tag ACADEMY CKLA XP
def check_and_award_badges(grade: int = Query(3), db: Session = Depends(get_db)):
    """Check progress against badge conditions and award any newly earned badges.

    Returns list of newly awarded badge_keys (empty if none new).
    """
    newly_earned: list[str] = []
    now = NOW()

    earned_keys = {ub.badge_key for ub in db.query(CKLAUserBadge).all()}
    badges = db.query(CKLABadge).all()

    for badge in badges:
        if badge.badge_key in earned_keys:
            continue

        earned = False
        if badge.condition_type == "domain_complete":
            domain_num = badge.condition_value
            domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade).first()
            if domain:
                lesson_ids = [
                    l.id for l in
                    db.query(CKLALesson).filter_by(domain_id=domain.id, is_active=True).all()
                ]
                if lesson_ids:
                    completed_count = (
                        db.query(CKLALessonProgress)
                        .filter(
                            CKLALessonProgress.lesson_id.in_(lesson_ids),
                            CKLALessonProgress.completed == True,
                        )
                        .count()
                    )
                    earned = (completed_count == len(lesson_ids))

        elif badge.condition_type == "grade_complete":
            target_grade = badge.condition_value
            domains = db.query(CKLADomain).filter_by(grade=target_grade, is_active=True).all()
            if domains:
                all_lesson_ids = []
                for d in domains:
                    all_lesson_ids.extend(
                        l.id for l in
                        db.query(CKLALesson).filter_by(domain_id=d.id, is_active=True).all()
                    )
                if all_lesson_ids:
                    completed_count = (
                        db.query(CKLALessonProgress)
                        .filter(
                            CKLALessonProgress.lesson_id.in_(all_lesson_ids),
                            CKLALessonProgress.completed == True,
                        )
                        .count()
                    )
                    earned = (completed_count == len(all_lesson_ids))

        if earned:
            db.add(CKLAUserBadge(badge_key=badge.badge_key, earned_at=now))
            award_xp(db, "ckla_domain_test_pass", detail=badge.badge_key)
            newly_earned.append(badge.badge_key)

    if newly_earned:
        db.commit()

    return {"newly_earned": newly_earned}


# ── Domain Test ───────────────────────────────────────────────────────────────

@router.get("/domain-test/{domain_num}")
# @tag ACADEMY CKLA
def get_domain_test(
    domain_num: int, grade: int = Query(3), db: Session = Depends(get_db)
):
    """Return a set of comprehension questions for a domain test (up to 10, one per lesson)."""
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    lessons = (
        db.query(CKLALesson)
        .filter_by(domain_id=domain.id, is_active=True)
        .all()
    )
    questions: list[dict] = []
    for lesson in lessons:
        qs = db.query(CKLAQuestion).filter_by(lesson_id=lesson.id).all()
        if qs:
            q = random.choice(qs)
            questions.append({
                "id":           q.id,
                "lesson_id":    lesson.id,
                "lesson_title": lesson.title,
                "kind":         q.kind,
                "question":     q.question_text,
            })
        if len(questions) >= 10:
            break

    return {
        "domain_num": domain_num,
        "domain_title": domain.title,
        "grade": grade,
        "questions": questions,
    }


@router.post("/domain-test/{domain_num}/submit")
# @tag ACADEMY CKLA XP
async def submit_domain_test(
    domain_num: int,
    req: DomainTestSubmit,
    grade: int = Query(3),
    db: Session = Depends(get_db),
):
    """Grade domain test answers via AI and award XP on pass (>=70%)."""
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    total = len(req.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    correct = 0
    results: list[dict] = []

    for qid_str, user_ans in req.answers.items():
        try:
            qid = int(qid_str)
        except ValueError:
            continue
        question = db.query(CKLAQuestion).filter_by(id=qid).first()
        if not question:
            continue
        lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
        passage = lesson.passage if lesson else ""
        try:
            result = await grade_answer(
                question_text=question.question_text,
                kind=question.kind,
                model_answer=question.model_answer or "",
                passage=passage,
                user_answer=user_ans,
            )
            score = result.score
        except Exception:
            score = 0
        if score == 2:
            correct += 1
        results.append({"question_id": qid, "score": score})

    pct = round(correct / total * 100) if total else 0
    passed = pct >= 70

    xp_awarded = 0
    if passed:
        xp_awarded = award_xp(db, "ckla_domain_test_pass", detail=f"domain_{domain_num}_grade_{grade}")

    return {
        "domain_num":  domain_num,
        "grade":       grade,
        "total":       total,
        "correct":     correct,
        "score_pct":   pct,
        "passed":      passed,
        "xp_awarded":  xp_awarded,
        "results":     results,
    }


# ── Grade Final Test ──────────────────────────────────────────────────────────

@router.get("/grade-final-test")
# @tag ACADEMY CKLA
def get_grade_final_test(grade: int = Query(3), db: Session = Depends(get_db)):
    """Return a set of questions for the grade final test (up to 20, one per domain)."""
    domains = (
        db.query(CKLADomain)
        .filter_by(grade=grade, is_active=True)
        .order_by(CKLADomain.domain_num)
        .all()
    )
    questions: list[dict] = []
    for domain in domains:
        lessons = db.query(CKLALesson).filter_by(domain_id=domain.id, is_active=True).all()
        for lesson in lessons:
            qs = db.query(CKLAQuestion).filter_by(lesson_id=lesson.id).all()
            if qs:
                q = random.choice(qs)
                questions.append({
                    "id":             q.id,
                    "lesson_id":      lesson.id,
                    "domain_num":     domain.domain_num,
                    "domain_title":   domain.title,
                    "lesson_title":   lesson.title,
                    "kind":           q.kind,
                    "question":       q.question_text,
                })
                break
        if len(questions) >= 20:
            break

    return {
        "grade":     grade,
        "questions": questions,
    }


@router.post("/grade-final-test/submit")
# @tag ACADEMY CKLA XP
async def submit_grade_final_test(
    req: GradeFinalTestSubmit,
    grade: int = Query(3),
    db: Session = Depends(get_db),
):
    """Grade final test answers via AI and award XP on pass (>=80%)."""
    total = len(req.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    correct = 0
    results: list[dict] = []

    for qid_str, user_ans in req.answers.items():
        try:
            qid = int(qid_str)
        except ValueError:
            continue
        question = db.query(CKLAQuestion).filter_by(id=qid).first()
        if not question:
            continue
        lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
        passage = lesson.passage if lesson else ""
        try:
            result = await grade_answer(
                question_text=question.question_text,
                kind=question.kind,
                model_answer=question.model_answer or "",
                passage=passage,
                user_answer=user_ans,
            )
            score = result.score
        except Exception:
            score = 0
        if score == 2:
            correct += 1
        results.append({"question_id": qid, "score": score})

    pct = round(correct / total * 100) if total else 0
    passed = pct >= 80

    xp_awarded = 0
    if passed:
        xp_awarded = award_xp(db, "ckla_grade_final_pass", detail=f"grade_{grade}")

    return {
        "grade":      grade,
        "total":      total,
        "correct":    correct,
        "score_pct":  pct,
        "passed":     passed,
        "xp_awarded": xp_awarded,
        "results":    results,
    }
