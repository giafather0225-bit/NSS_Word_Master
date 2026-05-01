"""
routers/parent_ckla.py — Parent Dashboard: CKLA progress summary
Section: Parent
Dependencies: models/ckla, models/gamification (XPLog)
API:
  GET /api/parent/ckla-summary — CKLA overview for parent dashboard
"""

import logging
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
def ckla_summary(grade: int = Query(3), db: Session = Depends(get_db)):
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

    all_lesson_ids: list[int] = []
    domain_lesson_map: dict[int, list[int]] = {}  # domain.id → [lesson_id]
    for d in domains:
        ids = [r.id for r in db.query(CKLALesson.id).filter_by(domain_id=d.id, is_active=True).all()]
        domain_lesson_map[d.id] = ids
        all_lesson_ids.extend(ids)

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

    # ── Domain test consecutive fail counts (from AppConfig) ───
    fail_configs: dict[int, int] = {}
    for d in domains:
        key = f"ckla_domain_test_consec_fails_d{d.domain_num}_g{grade}"
        cfg = db.query(AppConfig).filter_by(key=key).first()
        if cfg and cfg.value:
            try:
                fail_configs[d.domain_num] = int(cfg.value)
            except ValueError:
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
    }
