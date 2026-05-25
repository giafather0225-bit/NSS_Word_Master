"""
routers/ckla_domain_test.py — CKLA domain test endpoints (2 endpoints).
Section: Academy
Dependencies: models/ckla, models/us_academy, models/system, services/ckla_grader, services/xp_engine, services/streak_engine, services/island_care_engine
API endpoints:
  GET  /api/academy/ckla/domain-test/{domain_num}
  POST /api/academy/ckla/domain-test/{domain_num}/submit

Progress / Q&A / Badges → ckla_progress.py
Catalog / content       → ckla.py
Grade Final Test        → ckla_grade_test.py
Shared helpers          → _ckla_common.py
"""
import json
import logging
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.models.ckla import (
    CKLADomain, CKLALesson, CKLAQuestion, CKLAWordLesson,
)
from backend.models.us_academy import USAcademyWord
from backend.models.system import AppConfig
from backend.services.ckla_grader import grade_answer
from backend.services.xp_engine import award_xp
from backend.services.streak_engine import mark_ckla_done
from backend.services.island_care_engine import apply_subject_gain as _island_apply_gain
from backend.routers._ckla_common import (
    _CFG_DOMAIN_PASS_PCT,
    DomainTestSubmit,
)

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla"])


@router.get("/domain-test/{domain_num}")
# @tag ACADEMY CKLA
def get_domain_test(
    domain_num: int, grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)
):
    """Return 10 domain test questions: 3 vocab_mc + 2 vocab_fill + 5 Q&A.

    ID scheme (no schema change needed):
      Q&A        → real question.id  (< 10000)
      vocab_mc   → word_id + 10000
      vocab_fill → word_id + 20000
    """
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    lessons = (
        db.query(CKLALesson)
        .filter_by(domain_id=domain.id, is_active=True)
        .all()
    )
    lesson_ids = [l.id for l in lessons]

    # ── Q&A questions (5) — one per lesson, shuffled ──────────────────────────
    all_qs = (
        db.query(CKLAQuestion)
        .filter(CKLAQuestion.lesson_id.in_(lesson_ids))
        .all()
    ) if lesson_ids else []
    qs_by_lesson: dict[int, list] = {}
    for q in all_qs:
        qs_by_lesson.setdefault(q.lesson_id, []).append(q)

    qa_questions: list[dict] = []
    shuffled_lessons = lessons[:]
    random.shuffle(shuffled_lessons)
    for lesson in shuffled_lessons:
        qs = qs_by_lesson.get(lesson.id, [])
        if qs:
            q = random.choice(qs)
            qa_questions.append({
                "id":            q.id,
                "type":          "qa",
                "lesson_id":     lesson.id,
                "lesson_title":  lesson.title,
                "kind":          q.kind,
                "question_text": q.question_text,
            })
        if len(qa_questions) >= 5:
            break

    # ── Vocab questions (5: 3 MC + 2 fill) ───────────────────────────────────
    word_links = (
        db.query(CKLAWordLesson)
        .filter(CKLAWordLesson.lesson_id.in_(lesson_ids))
        .all()
    ) if lesson_ids else []

    word_ids = list({wl.word_id for wl in word_links})
    domain_words: list = []
    if word_ids:
        domain_words = db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()

    vocab_questions: list[dict] = []
    if domain_words:
        n_vocab = min(5, len(domain_words))
        chosen = random.sample(domain_words, n_vocab)
        distractor_pool = [w for w in domain_words if w.word]

        for i, word in enumerate(chosen):
            q_type = "vocab_fill" if (n_vocab >= 5 and i >= 3) else "vocab_mc"
            base: dict = {
                "lesson_title":  "",
                "question_text": word.definition or "",
                "word":          word.word,
            }
            if q_type == "vocab_mc":
                others = [w for w in distractor_pool if w.id != word.id and w.word]
                distractors = [w.word for w in random.sample(others, min(3, len(others)))]
                choices = distractors + [word.word]
                random.shuffle(choices)
                base.update({
                    "id":             word.id + 10000,
                    "type":           "vocab_mc",
                    "choices":        choices,
                    "correct_answer": word.word,
                })
            else:
                base.update({
                    "id":   word.id + 20000,
                    "type": "vocab_fill",
                })
            vocab_questions.append(base)

    all_questions = qa_questions + vocab_questions
    random.shuffle(all_questions)

    return {
        "domain_num":   domain_num,
        "domain_title": domain.title,
        "grade":        grade,
        "questions":    all_questions,
    }


@router.post("/domain-test/{domain_num}/submit")
# @tag ACADEMY CKLA XP
async def submit_domain_test(
    domain_num: int,
    req: DomainTestSubmit,
    grade: int = Query(3, ge=3, le=8),
    db: Session = Depends(get_db),
):
    """Grade domain test answers. Vocab (MC/fill) graded locally; Q&A via AI.

    ID ranges:
      < 10000     → Q&A       (AI graded, score 0/1/2 → correct if score >= 1)
      10000–19999 → vocab_mc  (correct_answer exact match)
      >= 20000    → vocab_fill (case-insensitive word match)
    """
    domain = db.query(CKLADomain).filter_by(domain_num=domain_num, grade=grade, is_active=True).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    total = len(req.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    correct = 0
    results: list[dict] = []

    for qid_str, user_ans in req.answers.items():
        user_ans = (user_ans or "")[:2000]
        try:
            qid = int(qid_str)
        except ValueError:
            continue

        if qid >= 20000:
            # vocab_fill — case-insensitive exact word match
            word = db.query(USAcademyWord).filter_by(id=qid - 20000).first()
            is_correct = bool(
                word and user_ans.strip().lower() == (word.word or "").lower()
            )
            correct += int(is_correct)
            results.append({"question_id": qid, "score": 2 if is_correct else 0})

        elif qid >= 10000:
            # vocab_mc — submitted answer should equal the correct word
            word = db.query(USAcademyWord).filter_by(id=qid - 10000).first()
            is_correct = bool(
                word and user_ans.strip().lower() == (word.word or "").lower()
            )
            correct += int(is_correct)
            results.append({"question_id": qid, "score": 2 if is_correct else 0})

        else:
            # Q&A — AI graded
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
            except Exception as exc:
                logger.warning("CKLA domain-test: AI grading failed for qid=%s, defaulting score=0: %s", qid, exc)
                score = 0
            if score >= 1:  # score 1 (partial) and 2 (full) both count as correct
                correct += 1
            results.append({"question_id": qid, "score": score})

    pct = round(correct / total * 100) if total else 0
    _dpct_cfg = db.query(AppConfig).filter_by(key=_CFG_DOMAIN_PASS_PCT).first()
    _domain_pass_pct = int(_dpct_cfg.value) if _dpct_cfg and _dpct_cfg.value else 80
    passed = pct >= _domain_pass_pct

    xp_awarded = 0
    fail_key = f"ckla_domain_test_consec_fails_d{domain_num}_g{grade}"
    fail_cfg = db.query(AppConfig).filter_by(key=fail_key).first()
    if passed:
        xp_awarded = award_xp(db, "ckla_domain_test_pass", detail=f"domain_{domain_num}_grade_{grade}", commit=False)
        try:
            _island_apply_gain(db, "english", "english_final_test")
        except Exception as exc:
            logger.warning("CKLA domain-test: island gain failed (non-fatal): %s", exc)
        try:
            mark_ckla_done(db, commit=False)
        except Exception as exc:
            logger.warning("CKLA domain-test: mark_ckla_done failed (non-fatal): %s", exc)
        if fail_cfg:
            fail_cfg.value = "0"
    else:
        new_count = int(fail_cfg.value) + 1 if fail_cfg else 1
        if fail_cfg:
            fail_cfg.value = str(new_count)
        else:
            db.add(AppConfig(key=fail_key, value=str(new_count)))

    if req.time_taken_seconds is not None:
        time_key = f"ckla_domain_test_time_d{domain_num}_g{grade}"
        time_cfg = db.query(AppConfig).filter_by(key=time_key).first()
        if time_cfg:
            time_cfg.value = str(req.time_taken_seconds)
        else:
            db.add(AppConfig(key=time_key, value=str(req.time_taken_seconds)))

    history_key = f"ckla_domain_test_history_d{domain_num}_g{grade}"
    history_cfg = db.query(AppConfig).filter_by(key=history_key).first()
    history: list = []
    if history_cfg and history_cfg.value:
        try:
            history = json.loads(history_cfg.value)
        except (json.JSONDecodeError, ValueError):
            history = []
    history.insert(0, {
        "score_pct": pct,
        "correct":   correct,
        "total":     total,
        "passed":    passed,
        "date":      datetime.now().date().isoformat(),
    })
    history = history[:10]
    if history_cfg:
        history_cfg.value = json.dumps(history)
    else:
        db.add(AppConfig(key=history_key, value=json.dumps(history)))

    db.commit()

    return {
        "domain_num":         domain_num,
        "grade":              grade,
        "total":              total,
        "correct":            correct,
        "score_pct":          pct,
        "passed":             passed,
        "xp_awarded":         xp_awarded,
        "results":            results,
        "time_taken_seconds": req.time_taken_seconds,
    }
