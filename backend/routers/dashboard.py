"""
routers/dashboard.py — Parent dashboard aggregate stats + analytics.
Section: Parent
Dependencies: models.py (StudyItem, Progress), database.py (LEARNING_ROOT)
API: GET /api/dashboard/stats, GET /api/dashboard/textbook/{textbook},
     GET /api/dashboard/analytics
"""

import json as _json
from datetime import date as _date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.database import LEARNING_ROOT, get_db
from backend.models import Progress, StudyItem

router = APIRouter()


# @tag DASHBOARD
@router.get("/api/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    """Return aggregate stats for the parent dashboard (DB + filesystem)."""
    rows = db.query(
        StudyItem.textbook,
        StudyItem.lesson,
        func.count(StudyItem.id).label("cnt"),
    ).group_by(StudyItem.textbook, StudyItem.lesson).all()

    textbook_map: dict = {}
    total_words = 0
    for tb, _lesson, cnt in rows:
        tb_name = tb if tb else "(default)"
        if tb_name not in textbook_map:
            textbook_map[tb_name] = {"name": tb_name, "lessons": 0, "words": 0}
        textbook_map[tb_name]["lessons"] += 1
        textbook_map[tb_name]["words"]   += cnt
        total_words += cnt

    english_dir = LEARNING_ROOT / "English"
    if english_dir.is_dir():
        for tb_dir in sorted(english_dir.iterdir()):
            if not tb_dir.is_dir() or tb_dir.name.startswith("."):
                continue
            tb_name = tb_dir.name
            if tb_name not in textbook_map:
                lessons_count = 0
                words_count   = 0
                for lesson_dir in sorted(tb_dir.iterdir()):
                    if not lesson_dir.is_dir() or lesson_dir.name.startswith("."):
                        continue
                    lessons_count += 1
                    data_json = lesson_dir / "data.json"
                    if data_json.is_file():
                        try:
                            words_count += len(_json.loads(data_json.read_text("utf-8")))
                        except Exception:
                            pass
                textbook_map[tb_name] = {"name": tb_name, "lessons": lessons_count, "words": words_count}
                total_words += words_count

    best = db.query(func.max(Progress.best_streak)).scalar() or 0
    textbooks = list(textbook_map.values())
    return {
        "total_words":      total_words,
        "words_detail":     f"across {len(textbooks)} textbook(s)",
        "textbook_count":   len(textbooks),
        "textbooks_detail": ", ".join(t["name"] for t in textbooks),
        "lesson_count":     sum(t["lessons"] for t in textbooks),
        "lessons_detail":   f"{total_words} total words",
        "best_streak":      best,
        "streak_detail":    "across all lessons",
        "textbooks":        textbooks,
    }


# @tag DASHBOARD
@router.get("/api/dashboard/textbook/{textbook}")
def dashboard_textbook_detail(textbook: str, db: Session = Depends(get_db)):
    """Return lesson list and word counts for a specific textbook."""
    rows = db.query(
        StudyItem.lesson,
        func.count(StudyItem.id).label("cnt"),
    ).filter(
        StudyItem.textbook == textbook,
    ).group_by(StudyItem.lesson).order_by(StudyItem.lesson).all()

    lessons = [{"lesson": r.lesson, "words": r.cnt} for r in rows]
    return {"textbook": textbook, "lessons": lessons}


# @tag DASHBOARD @tag ANALYTICS
@router.get("/api/dashboard/analytics")
def dashboard_analytics(db: Session = Depends(get_db)):
    """Return full analytics data for the parent dashboard."""
    recent = [dict(r) for r in db.execute(text(
        "SELECT * FROM learning_logs ORDER BY completed_at DESC LIMIT 20"
    )).mappings().all()]

    weak = [dict(r) for r in db.execute(text("""
        SELECT word, textbook, lesson,
               COUNT(*) as total_attempts,
               SUM(CASE WHEN is_correct=0 THEN 1 ELSE 0 END) as wrong_count,
               ROUND(100.0 * SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) / COUNT(*), 0) as accuracy
        FROM word_attempts
        GROUP BY word, textbook, lesson
        HAVING COUNT(*) >= 2
        ORDER BY accuracy ASC, wrong_count DESC
        LIMIT 15
    """)).mappings().all()]

    stage_stats = [dict(r) for r in db.execute(text("""
        SELECT stage, COUNT(*) as completions,
               AVG(correct_count * 100.0 / NULLIF(word_count, 0)) as avg_accuracy,
               AVG(duration_sec) as avg_duration
        FROM learning_logs
        WHERE word_count > 0
        GROUP BY stage
        ORDER BY stage
    """)).mappings().all()]

    lesson_progress = [dict(r) for r in db.execute(text("""
        SELECT textbook, lesson,
               GROUP_CONCAT(DISTINCT stage) as completed_stages,
               COUNT(*) as total_sessions,
               SUM(duration_sec) as total_time,
               MAX(completed_at) as last_studied
        FROM learning_logs
        GROUP BY textbook, lesson
        ORDER BY last_studied DESC
        LIMIT 50
    """)).mappings().all()]

    total_time = db.execute(text(
        "SELECT COALESCE(SUM(duration_sec),0) FROM learning_logs"
    )).scalar() or 0

    today_time = db.execute(text(
        "SELECT COALESCE(SUM(duration_sec),0) FROM learning_logs WHERE date(completed_at)=date('now','localtime')"
    )).scalar() or 0

    days = [r[0] for r in db.execute(text(
        "SELECT DISTINCT date(completed_at) FROM learning_logs WHERE completed_at!='' ORDER BY date(completed_at) DESC LIMIT 365"
    )).fetchall()]

    streak_days = 0
    if days:
        today = _date.today()
        for i, d in enumerate(days):
            try:
                if _date.fromisoformat(d) == today - timedelta(days=i):
                    streak_days += 1
                else:
                    break
            except Exception:
                break

    return {
        "recent_activity":  recent,
        "weak_words":       weak,
        "stage_stats":      stage_stats,
        "lesson_progress":  lesson_progress,
        "total_study_sec":  total_time,
        "today_study_sec":  today_time,
        "study_streak_days": streak_days,
    }
