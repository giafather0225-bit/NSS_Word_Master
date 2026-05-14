"""
from __future__ import annotations
routers/parent_ckla.py — Parent Dashboard: CKLA progress summary
Section: Parent
Dependencies: models/ckla, models/gamification (XPLog)
API:
  GET /api/parent/ckla-summary — CKLA overview for parent dashboard
  GET /api/parent/ckla-chart   — Lightweight lesson-completion chart (week/month/full)
"""

import json
import logging
from collections import Counter
from datetime import date as _date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.ckla import (
    CKLADomain, CKLALesson, CKLALessonProgress, CKLAQuestionResponse,
)
from backend.models.gamification import XPLog
from backend.models.system import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parent", tags=["parent"])


@router.get("/ckla-summary")
def ckla_summary(grade: int = Query(3, ge=3, le=8), db: Session = Depends(get_db)):
    """Full CKLA progress summary for the parent dashboard."""
    today = _date.today()
    today_str = today.isoformat()

    # ── Domains + lessons ──────────────────────────────────────
    domains = (
        db.query(CKLADomain)
        .filter_by(is_active=True, grade=grade)
        .order_by(CKLADomain.domain_num)
        .all()
    )

    # Bulk-fetch all lessons for this grade's domains in one query (avoids N+1)
    domain_ids = [d.id for d in domains]
    all_lesson_ids: list[int] = []
    domain_lesson_map: dict[int, list[int]] = {}  # domain.id → [lesson_id]
    if domain_ids:
        for lid, did in (
            db.query(CKLALesson.id, CKLALesson.domain_id)
            .filter(CKLALesson.domain_id.in_(domain_ids), CKLALesson.is_active == True)
            .all()
        ):
            domain_lesson_map.setdefault(did, []).append(lid)
            all_lesson_ids.append(lid)

    # Bulk-fetch completed progress
    completed_map: dict[int, CKLALessonProgress] = {}
    if all_lesson_ids:
        for p in (
            db.query(CKLALessonProgress)
            .filter(CKLALessonProgress.lesson_id.in_(all_lesson_ids))
            .all()
        ):
            completed_map[p.lesson_id] = p

    completed_ids = {lid for lid, p in completed_map.items() if p.completed}
    today_ids = {
        lid for lid, p in completed_map.items()
        if p.completed and p.completed_at and p.completed_at.startswith(today_str)
    }

    # ── Domain test passes (from XPLog) ────────────────────────
    domain_test_logs = (
        db.query(XPLog.detail)
        .filter(XPLog.action == "ckla_domain_test_pass")
        .all()
    )
    domain_test_passed: set[str] = {r.detail for r in domain_test_logs if r.detail}

    # ── Domain test consecutive fail counts + history (from AppConfig) ──
    # Bulk-fetch all relevant AppConfig rows in one query (avoids 2×N queries)
    ckla_cfg_prefix = f"ckla_domain_test_"
    ckla_cfg_suffix = f"_g{grade}"
    ckla_cfgs = {
        cfg.key: cfg.value
        for cfg in db.query(AppConfig)
        .filter(
            AppConfig.key.like(f"{ckla_cfg_prefix}%{ckla_cfg_suffix}")
        )
        .all()
        if cfg.value
    }

    fail_configs: dict[int, int] = {}
    domain_test_history: dict[int, list] = {}
    for d in domains:
        fail_key = f"ckla_domain_test_consec_fails_d{d.domain_num}_g{grade}"
        if fail_key in ckla_cfgs:
            try:
                fail_configs[d.domain_num] = int(ckla_cfgs[fail_key])
            except ValueError:
                pass

        hist_key = f"ckla_domain_test_history_d{d.domain_num}_g{grade}"
        if hist_key in ckla_cfgs:
            try:
                domain_test_history[d.domain_num] = json.loads(ckla_cfgs[hist_key])
            except (json.JSONDecodeError, ValueError):
                pass

    # ── Domain breakdown ────────────────────────────────────────
    domain_rows = []
    for d in domains:
        ids = domain_lesson_map[d.id]
        done = sum(1 for lid in ids if lid in completed_ids)
        consec_fails = fail_configs.get(d.domain_num, 0)
        domain_rows.append({
            "domain_num":          d.domain_num,
            "title":               d.title,
            "lesson_count":        len(ids),
            "completed_count":     done,
            "all_complete":        len(ids) > 0 and done == len(ids),
            "domain_test_passed":  f"domain_{d.domain_num}_grade_{grade}" in domain_test_passed,
            "domain_test_consec_fails": consec_fails,
            "domain_test_history": domain_test_history.get(d.domain_num, []),
        })

    # ── Q&A accuracy ───────────────────────────────────────────
    qa_rows = db.query(CKLAQuestionResponse).all()
    qa_total   = len(qa_rows)
    qa_correct = sum(1 for r in qa_rows if r.ai_score >= 1)
    qa_accuracy = round(qa_correct / qa_total * 100) if qa_total else 0

    # ── Needs parent review ────────────────────────────────────
    needs_review = [
        {
            "question_id": r.question_id,
            "answer":      r.user_answer[:120] if r.user_answer else "",
            "feedback":    r.ai_feedback[:120] if r.ai_feedback else "",
            "created_at":  r.created_at,
        }
        for r in qa_rows
        if r.needs_parent_review
    ]

    # ── Weekly chart (last 14 days) ────────────────────────────
    chart_days: list[dict] = []
    for i in range(13, -1, -1):
        d_str = (today - timedelta(days=i)).isoformat()
        count = sum(
            1 for p in completed_map.values()
            if p.completed and p.completed_at and p.completed_at.startswith(d_str)
        )
        chart_days.append({"date": d_str, "count": count})

    # ── Difficulty breakdown ───────────────────────────────────
    diff_counts: dict[str, int] = {"easy": 0, "neutral": 0, "hard": 0}
    for p in completed_map.values():
        if p.difficulty_rating in diff_counts:
            diff_counts[p.difficulty_rating] += 1

    # ── Estimated completion ───────────────────────────────────
    total_lessons    = len(all_lesson_ids)
    completed_count  = len(completed_ids)
    remaining        = total_lessons - completed_count

    # Pace: lessons completed in last 14 days (non-zero to avoid div/0)
    pace_window = sum(d["count"] for d in chart_days)
    lessons_per_day = pace_window / 14 if pace_window else 0
    est_days = round(remaining / lessons_per_day) if lessons_per_day > 0 else None

    # ── Learning start time pattern ────────────────────────────
    # Group completed_at timestamps by hour bucket to find Gia's typical study time
    hour_counts: Counter = Counter()
    for p in completed_map.values():
        if p.completed and p.completed_at:
            try:
                # completed_at is stored as ISO string "YYYY-MM-DDTHH:MM:SS" or "YYYY-MM-DD HH:MM:SS"
                ts_str = p.completed_at.replace(" ", "T")
                hour = int(ts_str[11:13])
                hour_counts[hour] += 1
            except (IndexError, ValueError):
                pass
    # Return top buckets as {label, count, pct}
    total_sessions = sum(hour_counts.values())
    start_time_pattern = []
    if total_sessions > 0:
        for hour, count in sorted(hour_counts.items(), key=lambda x: -x[1])[:4]:
            period = "AM" if hour < 12 else "PM"
            h12 = hour % 12 or 12
            start_time_pattern.append({
                "hour": hour,
                "label": f"{h12} {period}",
                "count": count,
                "pct": round(count / total_sessions * 100),
            })

    # ── Domain test 3-fail alert list ─────────────────────────
    domain_test_alerts = [
        {"domain_num": d.domain_num, "title": d.title, "consec_fails": fail_configs[d.domain_num]}
        for d in domains
        if fail_configs.get(d.domain_num, 0) >= 3
    ]

    # ── Grade Final Test cooldown status ──────────────────────
    final_test_locked = False
    final_test_retry_after = None
    final_cfg = db.query(AppConfig).filter_by(
        key=f"ckla_final_test_last_fail_grade_{grade}"
    ).first()
    if final_cfg and final_cfg.value:
        try:
            from datetime import datetime as _dt
            last_fail = _dt.fromisoformat(final_cfg.value)
            retry_after = last_fail + timedelta(hours=24)
            if _dt.now() < retry_after:
                final_test_locked = True
                final_test_retry_after = retry_after.isoformat(timespec="seconds")
        except ValueError:
            pass

    return {
        "grade":             grade,
        "total_lessons":     total_lessons,
        "completed_lessons": completed_count,
        "today_lessons":     len(today_ids),
        "today_studied":     len(today_ids) > 0,
        "domains":           domain_rows,
        "qa_accuracy":       qa_accuracy,
        "qa_total":          qa_total,
        "needs_review":      needs_review,
        "weekly_chart":      chart_days,
        "difficulty_breakdown": diff_counts,
        "estimated_completion_days": est_days,
        "domain_test_alerts":       domain_test_alerts,
        "final_test_locked":        final_test_locked,
        "final_test_retry_after":   final_test_retry_after,
        "start_time_pattern":       start_time_pattern,
    }


@router.get("/ckla-chart")
def ckla_chart(
    range: str = Query("week", pattern="^(week|month|full)$"),
    grade: int = Query(3, ge=3, le=8),
    db: Session = Depends(get_db),
):
    """Lightweight lesson-completion chart for interactive range toggle.

    range=week  → last 7 days  (daily bars)
    range=month → last 30 days (daily bars)
    range=full  → all weeks since first completion (weekly bars)

    Returns: {"chart": [{"date": str, "label": str, "count": int}], "grouped_by": "day"|"week"}
    """
    today = _date.today()

    # ── Fetch all completed progress for this grade (no N+1) ─────
    domains = (
        db.query(CKLADomain)
        .filter_by(is_active=True, grade=grade)
        .all()
    )
    domain_ids = [d.id for d in domains]
    all_lesson_ids: list[int] = []
    if domain_ids:
        all_lesson_ids = [
            lid for lid, in db.query(CKLALesson.id)
            .filter(CKLALesson.domain_id.in_(domain_ids), CKLALesson.is_active == True)
            .all()
        ]

    completed_progress: list[CKLALessonProgress] = []
    if all_lesson_ids:
        completed_progress = (
            db.query(CKLALessonProgress)
            .filter(
                CKLALessonProgress.lesson_id.in_(all_lesson_ids),
                CKLALessonProgress.completed.is_(True),
                CKLALessonProgress.completed_at.isnot(None),
            )
            .all()
        )

    # ── Build date → count index ───────────────────────────────
    date_counts: Counter = Counter()
    for p in completed_progress:
        if p.completed_at:
            date_counts[p.completed_at[:10]] += 1

    # ── Daily range (week / month) ─────────────────────────────
    if range in ("week", "month"):
        days_back = 7 if range == "week" else 30
        chart = []
        for i in range(days_back - 1, -1, -1):
            d_str = (today - timedelta(days=i)).isoformat()
            label = (today - timedelta(days=i)).strftime("%-m/%-d")
            chart.append({"date": d_str, "label": label, "count": date_counts.get(d_str, 0)})
        return {"chart": chart, "grouped_by": "day"}

    # ── Full range (weekly buckets) ────────────────────────────
    if not date_counts:
        return {"chart": [], "grouped_by": "week"}

    all_dates = [_date.fromisoformat(d) for d in date_counts]
    first_date = min(all_dates)
    # Round down to Monday of first week
    week_start = first_date - timedelta(days=first_date.weekday())
    chart = []
    current = week_start
    while current <= today:
        week_end = current + timedelta(days=6)
        count = sum(
            cnt for d_str, cnt in date_counts.items()
            if current <= _date.fromisoformat(d_str) <= min(week_end, today)
        )
        label = f"{current.month}/{current.day}"
        chart.append({
            "date":  current.isoformat(),
            "label": label,
            "count": count,
        })
        current += timedelta(days=7)

    return {"chart": chart, "grouped_by": "week"}
