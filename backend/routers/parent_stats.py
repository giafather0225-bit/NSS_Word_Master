"""
routers/parent_stats.py — Parent Dashboard read-only stats endpoints
Section: Parent
Dependencies: models.py (LearningLog, WordAttempt, XPLog, Progress),
              services/xp_engine.py, services/streak_engine.py
API: GET /api/parent/overview
     GET /api/parent/summary
     GET /api/parent/activity
     GET /api/parent/stage-stats
     GET /api/parent/word-stats
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import LearningLog, WordAttempt, XPLog, Progress
    from ..services import xp_engine, streak_engine
except ImportError:
    from database import get_db
    from models import LearningLog, WordAttempt, XPLog, Progress
    from services import xp_engine, streak_engine


router = APIRouter()


# ─── Overview ─────────────────────────────────────────────────

@router.get("/api/parent/overview")
def parent_overview(db: Session = Depends(get_db)):
    """Summary stats for the parent overview screen. @tag PARENT WORD_STATS"""
    total_xp  = xp_engine.get_total_xp(db)
    today_xp  = xp_engine.get_today_xp(db)
    streak    = streak_engine.get_current_streak(db)
    words_known = xp_engine.get_words_known(db)

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
    """Comprehensive stats for the parent dashboard summary cards. @tag PARENT"""
    total_xp = xp_engine.get_total_xp(db)
    streak = streak_engine.get_current_streak(db)
    words_known = xp_engine.get_words_known(db)

    total_words_learned = (
        db.query(func.count(func.distinct(WordAttempt.word)))
        .filter(WordAttempt.is_correct == True)
        .scalar() or 0
    )

    total_sessions = db.query(func.count(LearningLog.id)).scalar() or 0
    total_sec = db.query(func.sum(LearningLog.duration_sec)).scalar() or 0
    total_minutes = round(total_sec / 60)

    lessons_completed = (
        db.query(func.count(func.distinct(
            LearningLog.textbook + '/' + LearningLog.lesson
        )))
        .filter(LearningLog.stage.in_(["PREVIEW", "A", "B", "C", "D"]))
        .scalar() or 0
    )

    tests_passed = (
        db.query(func.count(XPLog.id))
        .filter(XPLog.action == "final_test_pass")
        .scalar() or 0
    )

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

    longest_streak = db.query(func.max(Progress.best_streak)).scalar() or 0

    return {
        "total_words_learned":  total_words_learned,
        "total_xp":             total_xp,
        "current_level":        total_xp // 100 + 1,
        "current_streak":       streak,
        "longest_streak":       longest_streak,
        "total_study_sessions": total_sessions,
        "total_study_minutes":  total_minutes,
        "lessons_completed":    lessons_completed,
        "tests_passed":         tests_passed,
        "average_test_score":   average_test_score,
        "words_known":          words_known,
    }


# ─── Activity (daily aggregated) ─────────────────────────────

@router.get("/api/parent/activity")
def parent_activity(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Daily aggregated learning activity for the last N days. @tag PARENT"""
    start_date = (date.today() - timedelta(days=days - 1)).isoformat()

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

    xp_rows = (
        db.query(XPLog.earned_date, func.sum(XPLog.xp_amount).label("xp"))
        .filter(XPLog.earned_date >= start_date)
        .group_by(XPLog.earned_date)
        .all()
    )
    xp_by_date = {r.earned_date: int(r.xp or 0) for r in xp_rows}

    daily = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        match = next((r for r in rows if r.day == d), None)
        daily.append({
            "date":     d,
            "words":    match.words if match else 0,
            "xp":       xp_by_date.get(d, 0),
            "minutes":  round((match.minutes or 0) / 60) if match else 0,
            "sessions": match.sessions if match else 0,
        })

    return {"daily": daily}


# ─── Stage Stats ──────────────────────────────────────────────

_STAGE_LABELS = {
    "PREVIEW": "preview", "A": "word_match", "B": "fill_blank",
    "C": "spelling", "D": "sentence", "exam": "final_test",
}


@router.get("/api/parent/stage-stats")
def parent_stage_stats(db: Session = Depends(get_db)):
    """Average time and accuracy per learning stage. @tag PARENT"""
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

    stages = {}
    for row in rows:
        key = _STAGE_LABELS.get(row.stage, row.stage or "unknown")
        stages[key] = {
            "avg_time_sec": round(row.avg_time or 0),
            "avg_accuracy": round(row.avg_accuracy or 0, 1),
            "completions":  row.completions,
        }

    return {"stages": stages}


# ─── Word Stats ───────────────────────────────────────────────

@router.get("/api/parent/word-stats")
def parent_word_stats(db: Session = Depends(get_db)):
    """Top wrong words (error pattern analysis). @tag PARENT WORD_STATS"""
    # SQLite has no native bool→int cast, so use CASE.
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
        # Backward compat
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
