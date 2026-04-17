"""
routers/parent.py — Parent Dashboard API
Section: Parent
Dependencies: models.py (AppConfig, TaskSetting, AcademySchedule, DayOffRequest,
              RewardItem, LearningLog, WordAttempt),
              services/xp_engine.py, services/streak_engine.py
API: GET /api/parent/overview, GET /api/parent/word-stats,
     PUT /api/parent/task-settings/{key},
     POST /api/parent/academy-schedule,
     POST /api/parent/config,
     GET /api/parent/day-off-requests,
     PUT /api/parent/day-off-requests/{id}
"""

import logging
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import (AppConfig, TaskSetting, AcademySchedule,
                          DayOffRequest, RewardItem, LearningLog, WordAttempt,
                          Progress, StudyItem, XPLog,
                          MathProgress, MathAttempt, MathWrongReview,
                          MathFactFluency, MathDailyChallenge,
                          MathKangarooProgress)
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import (AppConfig, TaskSetting, AcademySchedule,
                        DayOffRequest, RewardItem, LearningLog, WordAttempt,
                        Progress, StudyItem, XPLog,
                        MathProgress, MathAttempt, MathWrongReview,
                        MathFactFluency, MathDailyChallenge,
                        MathKangarooProgress)
    from services import xp_engine, streak_engine

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_PIN = "0000"
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ─── Schemas ──────────────────────────────────────────────────

class TaskSettingUpdate(BaseModel):
    is_required: bool | None = None
    xp_value:    int  | None = None
    is_active:   bool | None = None


class AcademyScheduleIn(BaseModel):
    days: list[int]   # 0=Mon … 6=Sun
    memo: str = ""


class ConfigIn(BaseModel):
    key:   str
    value: str


class DayOffDecisionIn(BaseModel):
    status:          str   # "approved" | "denied"
    parent_response: str = ""


class PinVerifyIn(BaseModel):
    pin: str


# ─── PIN verification ──────────────────────────────────────────

def _get_stored_pin(db: Session) -> str:
    """Read the active parent PIN from AppConfig, falling back to DEFAULT_PIN."""
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    return row.value if (row and row.value) else DEFAULT_PIN


# @tag PARENT PIN
def require_parent_pin(
    x_parent_pin: str | None = Header(default=None, alias="X-Parent-Pin"),
    db: Session = Depends(get_db),
) -> bool:
    """
    FastAPI dependency that guards parent mutation endpoints.

    Frontend MUST send the verified PIN in the `X-Parent-Pin` request header
    on every mutating call (PUT/POST). The PIN is checked against AppConfig
    and rejected with 403 if missing or wrong. Read-only GET endpoints can
    still be called without a PIN — only mutations require it.

    This closes the gap where /api/parent/config etc. previously accepted
    any unauthenticated caller and could even let the child reset their own
    parent PIN via the browser console.
    """
    correct = _get_stored_pin(db)
    if not x_parent_pin or x_parent_pin != correct:
        raise HTTPException(status_code=403, detail="Parent PIN required")
    return True


@router.post("/api/parent/verify-pin")
def parent_verify_pin(body: PinVerifyIn, db: Session = Depends(get_db)):
    """
    Verify the parent PIN. Returns ok:true on success.
    @tag PARENT PIN
    """
    if body.pin != _get_stored_pin(db):
        raise HTTPException(status_code=403, detail="Wrong PIN")
    return {"ok": True}


# ─── Overview ─────────────────────────────────────────────────

@router.get("/api/parent/overview")
def parent_overview(db: Session = Depends(get_db)):
    """
    Return summary stats for the parent overview screen.
    @tag PARENT WORD_STATS
    """
    total_xp  = xp_engine.get_total_xp(db)
    today_xp  = xp_engine.get_today_xp(db)
    streak    = streak_engine.get_current_streak(db)
    words_known = xp_engine.get_words_known(db)

    # Recent 7-day learning activity
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    recent_logs = (
        db.query(LearningLog)
        .filter(LearningLog.completed_at >= week_ago)
        .order_by(LearningLog.completed_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_xp":    total_xp,
        "today_xp":    today_xp,
        "streak":      streak,
        "words_known": words_known,
        "recent_logs": [
            {
                "lesson":        log.lesson,
                "stage":         log.stage,
                "correct_count": log.correct_count,
                "word_count":    log.word_count,
                "duration_sec":  log.duration_sec,
                "completed_at":  (log.completed_at or "")[:10],
            }
            for log in recent_logs
        ],
    }


# ─── Summary (enhanced stats) ─────────────────────────────────

@router.get("/api/parent/summary")
def parent_summary(db: Session = Depends(get_db)):
    """
    Return comprehensive stats for the parent dashboard summary cards.
    @tag PARENT
    """
    total_xp = xp_engine.get_total_xp(db)
    streak = streak_engine.get_current_streak(db)
    words_known = xp_engine.get_words_known(db)

    # Total words learned (distinct words with at least one correct attempt)
    total_words_learned = (
        db.query(func.count(func.distinct(WordAttempt.word)))
        .filter(WordAttempt.is_correct == True)
        .scalar() or 0
    )

    # Study sessions and time
    total_sessions = db.query(func.count(LearningLog.id)).scalar() or 0
    total_sec = db.query(func.sum(LearningLog.duration_sec)).scalar() or 0
    total_minutes = round(total_sec / 60)

    # Lessons completed (distinct lessons with all 5 stages in learning_logs)
    lessons_completed = (
        db.query(func.count(func.distinct(
            LearningLog.textbook + '/' + LearningLog.lesson
        )))
        .filter(LearningLog.stage.in_(["PREVIEW", "A", "B", "C", "D"]))
        .scalar() or 0
    )

    # Tests passed (final_test_pass XP logs)
    tests_passed = (
        db.query(func.count(XPLog.id))
        .filter(XPLog.action == "final_test_pass")
        .scalar() or 0
    )

    # Average test score (from learning_logs where stage is EXAM)
    exam_logs = (
        db.query(
            func.avg(
                LearningLog.correct_count * 100.0 /
                func.nullif(LearningLog.word_count, 0)
            )
        )
        .filter(LearningLog.word_count > 0)
        .scalar()
    )
    average_test_score = round(exam_logs or 0, 1)

    # Longest streak
    longest_streak = db.query(func.max(Progress.best_streak)).scalar() or 0

    return {
        "total_words_learned": total_words_learned,
        "total_xp": total_xp,
        "current_level": total_xp // 100 + 1,
        "current_streak": streak,
        "longest_streak": longest_streak,
        "total_study_sessions": total_sessions,
        "total_study_minutes": total_minutes,
        "lessons_completed": lessons_completed,
        "tests_passed": tests_passed,
        "average_test_score": average_test_score,
        "words_known": words_known,
    }


# ─── Activity (daily aggregated) ─────────────────────────────

@router.get("/api/parent/activity")
def parent_activity(days: int = Query(default=7, ge=1, le=90), db: Session = Depends(get_db)):
    """
    Return daily aggregated learning activity for the last N days.
    @tag PARENT
    """
    start_date = (date.today() - timedelta(days=days - 1)).isoformat()

    # Query daily aggregated stats from learning_logs
    rows = (
        db.query(
            func.substr(LearningLog.completed_at, 1, 10).label("day"),
            func.count(func.distinct(WordAttempt.word)).label("words"),
            func.count(LearningLog.id).label("sessions"),
            func.sum(LearningLog.duration_sec).label("minutes"),
        )
        .outerjoin(
            WordAttempt,
            (WordAttempt.lesson == LearningLog.lesson) &
            (WordAttempt.is_correct == True) &
            (func.substr(WordAttempt.attempted_at, 1, 10) == func.substr(LearningLog.completed_at, 1, 10))
        )
        .filter(LearningLog.completed_at >= start_date)
        .group_by(func.substr(LearningLog.completed_at, 1, 10))
        .all()
    )

    # Also get XP per day
    xp_rows = (
        db.query(
            XPLog.earned_date,
            func.sum(XPLog.xp_amount).label("xp"),
        )
        .filter(XPLog.earned_date >= start_date)
        .group_by(XPLog.earned_date)
        .all()
    )
    xp_by_date = {r.earned_date: int(r.xp or 0) for r in xp_rows}

    # Build daily array with all days (fill zeros for missing days)
    daily = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        match = next((r for r in rows if r.day == d), None)
        daily.append({
            "date": d,
            "words": match.words if match else 0,
            "xp": xp_by_date.get(d, 0),
            "minutes": round((match.minutes or 0) / 60) if match else 0,
            "sessions": match.sessions if match else 0,
        })

    return {"daily": daily}


# ─── Stage Stats ──────────────────────────────────────────────

@router.get("/api/parent/stage-stats")
def parent_stage_stats(db: Session = Depends(get_db)):
    """
    Return average time and accuracy per learning stage.
    @tag PARENT
    """
    rows = (
        db.query(
            LearningLog.stage,
            func.avg(LearningLog.duration_sec).label("avg_time"),
            func.avg(
                LearningLog.correct_count * 100.0 /
                func.nullif(LearningLog.word_count, 0)
            ).label("avg_accuracy"),
            func.count(LearningLog.id).label("completions"),
        )
        .filter(LearningLog.word_count > 0)
        .group_by(LearningLog.stage)
        .all()
    )

    STAGE_LABELS = {
        "PREVIEW": "preview", "A": "word_match", "B": "fill_blank",
        "C": "spelling", "D": "sentence", "exam": "final_test",
    }

    stages = {}
    for row in rows:
        key = STAGE_LABELS.get(row.stage, row.stage or "unknown")
        stages[key] = {
            "avg_time_sec": round(row.avg_time or 0),
            "avg_accuracy": round(row.avg_accuracy or 0, 1),
            "completions": row.completions,
        }

    return {"stages": stages}


# ─── Math Summary ──────────────────────────────────────────────

@router.get("/api/parent/math-summary")
def parent_math_summary(db: Session = Depends(get_db)):
    """
    Return aggregated Math stats for the parent dashboard.
    @tag PARENT MATH
    """
    # Academy progress
    progress_rows = db.query(MathProgress).all()
    total_lessons = len(progress_rows)
    completed = sum(1 for r in progress_rows if r.is_completed)
    pretest_passed = sum(1 for r in progress_rows if r.pretest_passed)
    unit_tests_passed = sum(1 for r in progress_rows if r.unit_test_passed)

    # Attempts — last 7 days
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    recent_attempts = (
        db.query(MathAttempt)
        .filter(MathAttempt.attempted_at >= week_ago)
        .all()
    )
    total_attempts = len(recent_attempts)
    correct_attempts = sum(1 for a in recent_attempts if a.is_correct)
    accuracy_7d = round(correct_attempts * 100 / total_attempts, 1) if total_attempts else 0.0

    # Weak concepts (top 5 by wrong count)
    concept_rows = (
        db.query(MathAttempt.lesson, func.count(MathAttempt.id).label("wrong"))
        .filter(MathAttempt.is_correct.is_(False))
        .group_by(MathAttempt.lesson)
        .order_by(func.count(MathAttempt.id).desc())
        .limit(5)
        .all()
    )
    weak_areas = [{"lesson": r.lesson, "wrong_count": r.wrong} for r in concept_rows]

    # Wrong-review queue
    today_str = date.today().isoformat()
    wrong_pending = db.query(MathWrongReview).filter(
        MathWrongReview.is_mastered.is_(False),
        MathWrongReview.next_review_date <= today_str,
    ).count()
    wrong_mastered = db.query(MathWrongReview).filter(
        MathWrongReview.is_mastered.is_(True)
    ).count()

    # Fact fluency per set
    fluency_rows = db.query(MathFactFluency).all()
    fluency = [{
        "fact_set": r.fact_set,
        "phase": r.current_phase,
        "best_score": r.best_score,
        "best_time_sec": r.best_time_sec,
        "accuracy_pct": round(r.accuracy_pct or 0, 1),
        "total_rounds": r.total_rounds,
    } for r in fluency_rows]

    # Daily challenge — last 7 days
    daily_rows = (
        db.query(MathDailyChallenge)
        .filter(MathDailyChallenge.challenge_date >= week_ago)
        .order_by(MathDailyChallenge.challenge_date.desc())
        .all()
    )
    daily_recent = [{
        "date": r.challenge_date,
        "score": r.score,
        "total": r.total,
        "completed": r.completed,
    } for r in daily_rows]

    # Kangaroo sets completed
    kang_rows = db.query(MathKangarooProgress).all()
    kangaroo = [{
        "set_id": r.set_id,
        "score": r.score,
        "total": r.total,
        "completed_at": (r.completed_at or "")[:10],
    } for r in kang_rows]

    return {
        "academy": {
            "total_lessons": total_lessons,
            "completed": completed,
            "pretest_passed": pretest_passed,
            "unit_tests_passed": unit_tests_passed,
        },
        "recent_7d": {
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy_pct": accuracy_7d,
        },
        "weak_areas": weak_areas,
        "wrong_review": {
            "pending": wrong_pending,
            "mastered": wrong_mastered,
        },
        "fluency": fluency,
        "daily_recent": daily_recent,
        "kangaroo": kangaroo,
    }


# ─── Word Stats ────────────────────────────────────────────────

@router.get("/api/parent/word-stats")
def parent_word_stats(db: Session = Depends(get_db)):
    """
    Return top wrong words from word_attempts (error pattern analysis).
    @tag PARENT WORD_STATS
    """
    # Top 20 most-missed words. SQLite has no native bool→int cast, so use CASE.
    correct_expr = func.sum(case((WordAttempt.is_correct == True, 1), else_=0))  # noqa: E712
    top_wrong = (
        db.query(
            WordAttempt.word,
            WordAttempt.lesson,
            func.count(WordAttempt.id).label("attempts"),
            correct_expr.label("correct_count"),
            func.max(WordAttempt.attempted_at).label("last_seen"),
        )
        .group_by(WordAttempt.word, WordAttempt.lesson)
        .having(func.count(WordAttempt.id) >= 2)
        .order_by((correct_expr * 100.0 / func.count(WordAttempt.id)).asc())
        .limit(20)
        .all()
    )

    return {
        "words": [
            {
                "word":      row.word,
                "lesson":    row.lesson,
                "attempts":  row.attempts,
                "correct":   row.correct_count,
                "accuracy":  round(row.correct_count * 100.0 / max(row.attempts, 1), 1),
                "last_seen": (row.last_seen or "")[:10],
            }
            for row in top_wrong
        ],
        # Keep backward compat
        "top_wrong": [
            {
                "word":        row.word,
                "lesson":      row.lesson,
                "attempts":    row.attempts,
                "wrong_count": row.attempts - row.correct_count,
                "accuracy":    round(row.correct_count / max(row.attempts, 1), 2),
            }
            for row in top_wrong
        ],
    }


# ─── Task Settings ────────────────────────────────────────────

@router.get("/api/parent/task-settings")
def parent_task_settings(db: Session = Depends(get_db)):
    """Return all task settings. @tag PARENT SETTINGS"""
    tasks = db.query(TaskSetting).order_by(TaskSetting.id).all()
    return {"tasks": [{"task_key": t.task_key, "is_required": t.is_required,
                        "xp_value": t.xp_value, "is_active": t.is_active} for t in tasks]}


@router.put("/api/parent/task-settings/{key}")
def parent_update_task(
    key: str,
    body: TaskSettingUpdate,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Update a task setting. PIN-protected. @tag PARENT SETTINGS"""
    task = db.query(TaskSetting).filter(TaskSetting.task_key == key).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if body.is_required is not None: task.is_required = body.is_required
    if body.xp_value    is not None: task.xp_value    = body.xp_value
    if body.is_active   is not None: task.is_active   = body.is_active
    db.commit()
    return {"ok": True}


# ─── Academy Schedule ─────────────────────────────────────────

@router.get("/api/parent/academy-schedule")
def parent_get_schedule(db: Session = Depends(get_db)):
    """Return active academy schedule days. @tag PARENT SCHEDULE"""
    rows = db.query(AcademySchedule).filter(AcademySchedule.is_active == True).all()
    return {"days": [{"day_of_week": r.day_of_week, "memo": r.memo or ""} for r in rows]}


@router.post("/api/parent/academy-schedule")
def parent_set_schedule(
    body: AcademyScheduleIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Replace academy schedule with new day list. PIN-protected. @tag PARENT SCHEDULE"""
    db.query(AcademySchedule).update({"is_active": False})
    for day in body.days:
        existing = db.query(AcademySchedule).filter(AcademySchedule.day_of_week == day).first()
        if existing:
            existing.is_active = True
            existing.memo = body.memo
        else:
            db.add(AcademySchedule(day_of_week=day, memo=body.memo, is_active=True))
    db.commit()
    return {"ok": True}


# ─── Config (PIN, email) ──────────────────────────────────────

@router.post("/api/parent/config")
def parent_set_config(
    body: ConfigIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Set an AppConfig key/value (e.g. PIN). PIN-protected. @tag PARENT SETTINGS PIN"""
    if body.key == "pin" and (not body.value.isdigit() or len(body.value) != 4):
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")
    row = db.query(AppConfig).filter(AppConfig.key == body.key).first()
    now = datetime.now().isoformat()
    if row:
        row.value = body.value
        row.updated_at = now
    else:
        db.add(AppConfig(key=body.key, value=body.value, updated_at=now))
    db.commit()
    return {"ok": True}


# ─── Day Off Requests ─────────────────────────────────────────

@router.get("/api/parent/day-off-requests")
def parent_day_off_list(db: Session = Depends(get_db)):
    """Return all day-off requests ordered by date DESC. @tag PARENT DAY_OFF"""
    rows = db.query(DayOffRequest).order_by(DayOffRequest.request_date.desc()).all()
    return {"requests": [
        {"id": r.id, "request_date": r.request_date, "reason": r.reason,
         "status": r.status, "parent_response": r.parent_response or ""}
        for r in rows
    ]}


@router.put("/api/parent/day-off-requests/{req_id}")
def parent_decide_day_off(
    req_id: int,
    body: DayOffDecisionIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Approve or deny a day-off request. PIN-protected. @tag PARENT DAY_OFF"""
    if body.status not in ("approved", "denied"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'denied'")
    row = db.query(DayOffRequest).filter(DayOffRequest.id == req_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    row.status = body.status
    row.parent_response = body.parent_response
    db.commit()
    return {"ok": True}
