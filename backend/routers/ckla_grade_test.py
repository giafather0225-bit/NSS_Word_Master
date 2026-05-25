"""
routers/ckla_grade_test.py — CKLA grade final test endpoints (3 endpoints).
Section: Academy
Dependencies: models/ckla, models/us_academy, models/system, services/ckla_grader, services/xp_engine, services/island_care_engine
API endpoints:
  GET  /api/academy/ckla/grade-final-test
  GET  /api/academy/ckla/grade-final-test/status
  POST /api/academy/ckla/grade-final-test/submit

Progress / Q&A / Badges → ckla_progress.py
Catalog / content       → ckla.py
Domain Test             → ckla_domain_test.py
Shared helpers          → _ckla_common.py
"""
import logging
import random
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional

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
from backend.services.island_care_engine import apply_subject_gain as _island_apply_gain
from backend.routers._ckla_common import (
    _CFG_GRADE_PASS_PCT,
    GradeFinalTestSubmit,
)

router = APIRouter(prefix="/api/academy/ckla", tags=["ckla"])


@router.get("/grade-final-test")
# @tag ACADEMY CKLA
def get_grade_final_test(grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Return 27 grade final test questions: 15 vocab_mc + 10 Q&A + 2 word_work.

    ID scheme (no schema change):
      Q&A        < 10000  → real CKLAQuestion.id
      vocab_mc   = word_id + 10000
      word_work  = word_id + 30000
    """
    domains = (
        db.query(CKLADomain)
        .filter_by(grade=grade, is_active=True)
        .order_by(CKLADomain.domain_num)
        .all()
    )
    if not domains:
        return {"grade": grade, "questions": []}

    domain_ids = [d.id for d in domains]
    domain_map = {d.id: d for d in domains}

    all_lessons = db.query(CKLALesson).filter(
        CKLALesson.domain_id.in_(domain_ids), CKLALesson.is_active == True
    ).all()
    lesson_map = {ls.id: ls for ls in all_lessons}
    lesson_ids = [ls.id for ls in all_lessons]

    # ── 10 Q&A: 1 per domain, balanced Literal/Inferential/Evaluative ─────────
    all_questions_raw = (
        db.query(CKLAQuestion)
        .filter(CKLAQuestion.lesson_id.in_(lesson_ids))
        .all()
    ) if lesson_ids else []

    qs_by_lesson_kind: dict[tuple, list] = {}
    for q in all_questions_raw:
        key = (q.lesson_id, q.kind)
        qs_by_lesson_kind.setdefault(key, []).append(q)

    qa_questions: list[dict] = []
    kind_counts: dict[str, int] = {"Literal": 0, "Inferential": 0, "Evaluative": 0}
    for domain in domains:
        d_lessons = [ls for ls in all_lessons if ls.domain_id == domain.id]
        if kind_counts.get("Evaluative", 0) < 2:
            preferred = ["Evaluative", "Inferential", "Literal"]
        elif kind_counts.get("Inferential", 0) < 4:
            preferred = ["Inferential", "Literal", "Evaluative"]
        else:
            preferred = ["Literal", "Inferential", "Evaluative"]

        picked = None
        for kind in preferred:
            candidates = [
                q for ls in d_lessons
                for q in qs_by_lesson_kind.get((ls.id, kind), [])
            ]
            if candidates:
                picked_q = random.choice(candidates)
                picked_lesson = lesson_map.get(picked_q.lesson_id)
                picked = {
                    "id":            picked_q.id,
                    "type":          "qa",
                    "kind":          picked_q.kind,
                    "domain_num":    domain.domain_num,
                    "domain_title":  domain.title,
                    "lesson_title":  picked_lesson.title if picked_lesson else "",
                    "question_text": picked_q.question_text,
                }
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
                break
        if picked:
            qa_questions.append(picked)
        if len(qa_questions) >= 10:
            break

    # ── Gather all vocab words for this grade ─────────────────────────────────
    word_links = db.query(CKLAWordLesson).filter(
        CKLAWordLesson.lesson_id.in_(lesson_ids)
    ).all()
    word_ids = list({wl.word_id for wl in word_links})
    all_words = db.query(USAcademyWord).filter(USAcademyWord.id.in_(word_ids)).all()
    random.shuffle(all_words)

    # ── 15 vocab_mc ───────────────────────────────────────────────────────────
    vocab_mc_words = all_words[:15] if len(all_words) >= 15 else all_words
    vocab_mc_questions: list[dict] = []
    for w in vocab_mc_words:
        distractors = random.sample(
            [x for x in all_words if x.id != w.id],
            min(3, len(all_words) - 1),
        )
        choices = [x.word for x in distractors] + [w.word]
        random.shuffle(choices)
        vocab_mc_questions.append({
            "id":            w.id + 10000,
            "type":          "vocab_mc",
            "domain_num":    None,
            "domain_title":  "",
            "lesson_title":  "",
            "question_text": w.definition or w.word,
            "word":          w.word,
            "choices":       choices,
        })

    # ── 2 word_work ───────────────────────────────────────────────────────────
    ww_pool = all_words[15:] if len(all_words) > 15 else all_words
    if len(ww_pool) < 2:
        ww_pool = all_words
    ww_words = random.sample(ww_pool, min(2, len(ww_pool)))
    word_work_questions: list[dict] = []
    for w in ww_words:
        word_work_questions.append({
            "id":            w.id + 30000,
            "type":          "word_work",
            "domain_num":    None,
            "domain_title":  "",
            "lesson_title":  "",
            "question_text": f'Write a sentence using the word "{w.word}".',
            "word":          w.word,
            "hint":          w.definition or "",
        })

    questions = vocab_mc_questions + qa_questions + word_work_questions

    return {
        "grade":     grade,
        "questions": questions,
    }


@router.get("/grade-final-test/status")
# @tag ACADEMY CKLA
def get_grade_final_test_status(grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Check if grade final test is locked (24h cooldown after a failed attempt)."""
    test_mode_cfg = db.query(AppConfig).filter_by(key="test_mode").first()
    if test_mode_cfg and test_mode_cfg.value == "true":
        return {"locked": False, "retry_after": None}

    cooldown_key = f"ckla_final_test_last_fail_grade_{grade}"
    row = db.query(AppConfig).filter_by(key=cooldown_key).first()
    if row and row.value:
        try:
            last_fail = datetime.fromisoformat(row.value)
            retry_after = last_fail + timedelta(hours=24)
            if datetime.now() < retry_after:
                return {"locked": True, "retry_after": retry_after.isoformat(timespec="seconds")}
        except ValueError:
            pass
    return {"locked": False, "retry_after": None}


@router.post("/grade-final-test/submit")
# @tag ACADEMY CKLA XP
async def submit_grade_final_test(
    req: GradeFinalTestSubmit,
    grade: int = Query(3, ge=3, le=8),
    db: Session = Depends(get_db),
):
    """Grade 27 final test answers by ID range, award XP on pass (>=80%).

    ID routing:
      qid < 10000          → Q&A       → AI graded (score 0/1/2; correct = 2)
      10000 <= qid < 20000 → vocab_mc  → local exact match
      qid >= 30000         → word_work → difflib similarity >= 0.80 = copied hint = fail
    """
    cooldown_key = f"ckla_final_test_last_fail_grade_{grade}"
    cfg = db.query(AppConfig).filter_by(key=cooldown_key).first()
    if cfg and cfg.value:
        try:
            last_fail = datetime.fromisoformat(cfg.value)
            retry_after = last_fail + timedelta(hours=24)
            if datetime.now() < retry_after:
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait until {retry_after.isoformat(timespec='seconds')} before retrying.",
                )
        except ValueError:
            pass

    total = len(req.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    correct = 0
    results: list[dict] = []
    wrong_questions: list[dict] = []

    for qid_str, user_ans in req.answers.items():
        user_ans = (user_ans or "")[:2000]
        try:
            qid = int(qid_str)
        except ValueError:
            continue

        user_ans_stripped = user_ans.strip()

        if qid >= 30000:
            # word_work — reject if answer copies the hint (>= 80% similarity) or too short
            word = db.query(USAcademyWord).filter_by(id=qid - 30000).first()
            if not word:
                results.append({"question_id": qid, "score": 0, "type": "word_work"})
                continue
            hint_texts = [
                p.strip() for p in [word.definition or "", word.example_1 or ""]
                if p.strip()
            ]
            ans_lower = user_ans_stripped.lower()
            copied_hint = any(
                SequenceMatcher(None, ans_lower, h.lower()).ratio() >= 0.6
                for h in hint_texts
            )
            is_correct = (not copied_hint) and len(user_ans_stripped) >= 8
            score = 2 if is_correct else 0
            if score == 2:
                correct += 1
            else:
                wrong_questions.append({
                    "type":           "word_work",
                    "lesson_title":   "Vocabulary",
                    "question_text":  f'Write a sentence using "{word.word}".',
                    "correct_answer": word.definition or word.word,
                })
            results.append({"question_id": qid, "score": score, "type": "word_work"})

        elif qid >= 10000:
            # vocab_mc — case-insensitive exact match
            word = db.query(USAcademyWord).filter_by(id=qid - 10000).first()
            is_correct = bool(word and user_ans_stripped.lower() == (word.word or "").lower())
            score = 2 if is_correct else 0
            if score == 2:
                correct += 1
            else:
                wrong_questions.append({
                    "type":           "vocab_mc",
                    "lesson_title":   "Vocabulary",
                    "question_text":  word.definition if word else "",
                    "correct_answer": word.word if word else "",
                })
            results.append({"question_id": qid, "score": score, "type": "vocab_mc"})

        else:
            # Q&A — AI graded
            question = db.query(CKLAQuestion).filter_by(id=qid).first()
            if not question:
                results.append({"question_id": qid, "score": 0, "type": "qa"})
                continue
            lesson = db.query(CKLALesson).filter_by(id=question.lesson_id).first()
            passage = lesson.passage if lesson else ""
            try:
                result = await grade_answer(
                    question_text=question.question_text,
                    kind=question.kind,
                    model_answer=question.model_answer or "",
                    passage=passage,
                    user_answer=user_ans_stripped,
                )
                score = result.score
            except Exception:
                score = 0
            if score == 2:
                correct += 1
            else:
                wrong_questions.append({
                    "type":           "qa",
                    "lesson_title":   lesson.title if lesson else "",
                    "question_text":  question.question_text,
                    "correct_answer": question.model_answer or "",
                })
            results.append({"question_id": qid, "score": score, "type": "qa"})

    pct = round(correct / total * 100) if total else 0
    _gpct_cfg = db.query(AppConfig).filter_by(key=_CFG_GRADE_PASS_PCT).first()
    _grade_pass_pct = int(_gpct_cfg.value) if _gpct_cfg and _gpct_cfg.value else 80
    passed = pct >= _grade_pass_pct

    xp_awarded = 0
    retry_after_str: Optional[str] = None
    if passed:
        xp_awarded = award_xp(db, "ckla_grade_final_pass", detail=f"grade_{grade}", commit=False)
        try:
            _island_apply_gain(db, "english", "english_final_test")
        except Exception:
            pass
        if cfg:
            cfg.value = ""
    else:
        now_str = datetime.now().isoformat(timespec="seconds")
        if cfg:
            cfg.value = now_str
        else:
            db.add(AppConfig(key=cooldown_key, value=now_str))
        retry_after_str = (datetime.now() + timedelta(hours=24)).isoformat(timespec="seconds")

    db.commit()

    return {
        "grade":           grade,
        "total":           total,
        "correct":         correct,
        "score_pct":       pct,
        "passed":          passed,
        "xp_awarded":      xp_awarded,
        "results":         results,
        "retry_after":     retry_after_str,
        "wrong_questions": wrong_questions,
    }
