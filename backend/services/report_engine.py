"""
services/report_engine.py — Weekly parent report: data aggregation + email dispatch
Section: Parent
Dependencies: models (LearningLog, WordAttempt, XPLog, MathAttempt, MathDailyChallenge,
              MathWrongReview, MathFactFluency), services/xp_engine, services/streak_engine,
              services/report_engine_html (HTML builder)
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import case, func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.services.report_engine_html import build_html_report  # noqa: E402


# ─────────────────────────────────────────────────────────
# Data collection
# ─────────────────────────────────────────────────────────

def collect_weekly_data(db: Session, days: int = 7) -> dict:
    """지난 N일 학습 데이터 집계 → 리포트용 dict 반환."""
    from backend.models import (
        LearningLog, WordAttempt, XPLog,
        MathAttempt, MathDailyChallenge, MathWrongReview, MathFactFluency,
    )
    from backend.services import xp_engine, streak_engine

    today      = date.today()
    start      = (today - timedelta(days=days)).isoformat()
    week_label = (
        f"{(today - timedelta(days=days)).strftime('%b %d')} "
        f"– {today.strftime('%b %d, %Y')}"
    )

    # ── XP ──────────────────────────────────────────────
    total_xp = xp_engine.get_total_xp(db)
    week_xp  = int(
        db.query(func.sum(XPLog.xp_amount))
        .filter(XPLog.earned_date >= start)
        .scalar() or 0
    )

    # ── 스트릭 ──────────────────────────────────────────
    streak = streak_engine.get_current_streak(db)

    # ── 학습 시간 / 세션 ─────────────────────────────────
    row = (
        db.query(
            func.count(LearningLog.id).label("cnt"),
            func.sum(LearningLog.duration_sec).label("sec"),
        )
        .filter(LearningLog.completed_at >= start)
        .one()
    )
    total_sessions = row.cnt or 0
    total_minutes  = round((row.sec or 0) / 60)

    # ── 단어 성취 ────────────────────────────────────────
    words_attempted = int(
        db.query(func.count(func.distinct(WordAttempt.word)))
        .filter(WordAttempt.attempted_at >= start)
        .scalar() or 0
    )
    words_correct = int(
        db.query(func.count(func.distinct(WordAttempt.word)))
        .filter(WordAttempt.attempted_at >= start, WordAttempt.is_correct == True)
        .scalar() or 0
    )

    # ── 평균 정답률 ──────────────────────────────────────
    avg_acc = round(
        db.query(
            func.avg(
                LearningLog.correct_count * 100.0
                / func.nullif(LearningLog.word_count, 0)
            )
        )
        .filter(LearningLog.completed_at >= start, LearningLog.word_count > 0)
        .scalar() or 0.0,
        1,
    )

    # ── 스테이지별 정확도 ────────────────────────────────
    _STAGE_ORDER = ["PREVIEW", "A", "B", "C", "D", "exam"]
    _STAGE_LABEL = {
        "PREVIEW": "Preview", "A": "Word Match", "B": "Fill Blank",
        "C": "Spelling",      "D": "Sentence",   "exam": "Final Test",
    }
    stage_rows = (
        db.query(
            LearningLog.stage,
            func.avg(
                LearningLog.correct_count * 100.0
                / func.nullif(LearningLog.word_count, 0)
            ).label("acc"),
            func.count(LearningLog.id).label("cnt"),
        )
        .filter(LearningLog.completed_at >= start, LearningLog.word_count > 0)
        .group_by(LearningLog.stage)
        .all()
    )
    stage_stats = sorted(
        [
            {
                "label":    _STAGE_LABEL.get(r.stage, r.stage or "Unknown"),
                "accuracy": round(r.acc or 0.0, 1),
                "count":    r.cnt,
            }
            for r in stage_rows
        ],
        key=lambda x: _STAGE_ORDER.index(
            next((k for k, v in _STAGE_LABEL.items() if v == x["label"]), "PREVIEW")
        ) if x["label"] in _STAGE_LABEL.values() else 99,
    )

    # ── 취약 단어 TOP 5 ──────────────────────────────────
    correct_expr = func.sum(case((WordAttempt.is_correct == True, 1), else_=0))
    weak_rows = (
        db.query(
            WordAttempt.word,
            func.count(WordAttempt.id).label("attempts"),
            correct_expr.label("correct_cnt"),
        )
        .filter(WordAttempt.attempted_at >= start)
        .group_by(WordAttempt.word)
        .having(func.count(WordAttempt.id) >= 2)
        .order_by((correct_expr * 1.0 / func.count(WordAttempt.id)).asc())
        .limit(5)
        .all()
    )
    weak_words = [
        {
            "word":     r.word,
            "attempts": r.attempts,
            "accuracy": round((r.correct_cnt or 0) * 100.0 / max(r.attempts, 1), 0),
        }
        for r in weak_rows
    ]

    # ── 일별 활동 ────────────────────────────────────────
    daily_rows = (
        db.query(
            func.substr(LearningLog.completed_at, 1, 10).label("day"),
            func.sum(LearningLog.duration_sec).label("sec"),
        )
        .filter(LearningLog.completed_at >= start)
        .group_by(func.substr(LearningLog.completed_at, 1, 10))
        .all()
    )
    xp_rows = (
        db.query(XPLog.earned_date, func.sum(XPLog.xp_amount).label("xp"))
        .filter(XPLog.earned_date >= start)
        .group_by(XPLog.earned_date)
        .all()
    )
    xp_by_date  = {r.earned_date: int(r.xp or 0) for r in xp_rows}
    sec_by_date = {r.day: int(r.sec or 0) for r in daily_rows}
    daily_activity = [
        {
            "date":    (today - timedelta(days=days - 1 - i)).isoformat(),
            "label":   (today - timedelta(days=days - 1 - i)).strftime("%a"),
            "xp":      xp_by_date.get((today - timedelta(days=days - 1 - i)).isoformat(), 0),
            "minutes": round(sec_by_date.get((today - timedelta(days=days - 1 - i)).isoformat(), 0) / 60),
        }
        for i in range(days)
    ]

    # ── 학습 레슨 목록 ───────────────────────────────────
    lesson_rows = (
        db.query(LearningLog.textbook, LearningLog.lesson,
                 func.count(func.distinct(LearningLog.stage)).label("stages"))
        .filter(LearningLog.completed_at >= start)
        .group_by(LearningLog.textbook, LearningLog.lesson)
        .order_by(LearningLog.textbook, LearningLog.lesson)
        .limit(10)
        .all()
    )
    lessons_studied = [
        {"textbook": r.textbook, "lesson": r.lesson, "stages": r.stages}
        for r in lesson_rows
    ]

    # ── Math 데이터 ──────────────────────────────────────
    math_row = (
        db.query(
            func.count(MathAttempt.id).label("total"),
            func.sum(case((MathAttempt.is_correct == True, 1), else_=0)).label("correct"),
        )
        .filter(MathAttempt.attempted_at >= start)
        .one()
    )
    math_total   = math_row.total or 0
    math_correct = math_row.correct or 0
    math_acc     = round(math_correct * 100.0 / max(math_total, 1), 1)

    math_weak = (
        db.query(MathAttempt.lesson, func.count(MathAttempt.id).label("wrong"))
        .filter(MathAttempt.attempted_at >= start, MathAttempt.is_correct == False)
        .group_by(MathAttempt.lesson)
        .order_by(func.count(MathAttempt.id).desc())
        .limit(3)
        .all()
    )

    math_daily = (
        db.query(MathDailyChallenge)
        .filter(MathDailyChallenge.challenge_date >= start)
        .order_by(MathDailyChallenge.challenge_date.desc())
        .all()
    )
    math_daily_done  = sum(1 for r in math_daily if r.completed)
    math_daily_total = len(math_daily)

    math_pending = (
        db.query(func.count(MathWrongReview.id))
        .filter(MathWrongReview.is_mastered == False)
        .scalar() or 0
    )

    fluency_rows = db.query(MathFactFluency).all()
    best_fluency = max((r.best_score or 0 for r in fluency_rows), default=0)

    # ── CKLA 데이터 ──────────────────────────────────────────
    from backend.models.ckla import (
        CKLADomain, CKLALesson, CKLALessonProgress, CKLAQuestionResponse,
    )

    ckla_completed_this_week = (
        db.query(func.count(CKLALessonProgress.id))
        .filter(
            CKLALessonProgress.completed == True,
            func.substr(CKLALessonProgress.completed_at, 1, 10) >= start,
        )
        .scalar() or 0
    )

    # Total and completed lessons for grade 3
    ckla_all_ids = [
        r.id for r in
        db.query(CKLALesson.id)
        .join(CKLADomain, CKLALesson.domain_id == CKLADomain.id)
        .filter(CKLADomain.grade == 3, CKLADomain.is_active == True, CKLALesson.is_active == True)
        .all()
    ]
    ckla_total = len(ckla_all_ids)
    ckla_completed_total = (
        db.query(func.count(CKLALessonProgress.id))
        .filter(CKLALessonProgress.lesson_id.in_(ckla_all_ids), CKLALessonProgress.completed == True)
        .scalar() or 0
    ) if ckla_all_ids else 0
    ckla_pct = round(ckla_completed_total / ckla_total * 100) if ckla_total else 0

    _ckla_rank_thresholds = [(100, "Master"), (76, "Champion"), (51, "Adventurer"), (26, "Explorer"), (0, "Beginner")]
    ckla_rank = next(r for t, r in _ckla_rank_thresholds if ckla_pct >= t)

    # Q&A accuracy this week
    ckla_qa_rows = (
        db.query(
            func.count(CKLAQuestionResponse.id).label("total"),
            func.sum(case((CKLAQuestionResponse.score >= 2, 1), else_=0)).label("correct"),
        )
        .filter(func.substr(CKLAQuestionResponse.created_at, 1, 10) >= start)
        .one()
    )
    ckla_qa_total   = ckla_qa_rows.total or 0
    ckla_qa_correct = ckla_qa_rows.correct or 0
    ckla_qa_acc = round(ckla_qa_correct * 100.0 / max(ckla_qa_total, 1), 1) if ckla_qa_total else None

    # Days with at least one lesson this week
    ckla_days_studied = (
        db.query(func.count(func.distinct(func.substr(CKLALessonProgress.completed_at, 1, 10))))
        .filter(
            CKLALessonProgress.completed == True,
            func.substr(CKLALessonProgress.completed_at, 1, 10) >= start,
        )
        .scalar() or 0
    )

    return {
        "week_label":      week_label,
        "total_xp":        total_xp,
        "week_xp":         week_xp,
        "streak":          streak,
        "total_sessions":  total_sessions,
        "total_minutes":   total_minutes,
        "words_attempted": words_attempted,
        "words_correct":   words_correct,
        "avg_accuracy":    avg_acc,
        "stage_stats":     stage_stats,
        "weak_words":      weak_words,
        "daily_activity":  daily_activity,
        "lessons_studied": lessons_studied,
        "ckla": {
            "lessons_this_week": int(ckla_completed_this_week),
            "completed_total":   ckla_completed_total,
            "total_lessons":     ckla_total,
            "grade_pct":         ckla_pct,
            "rank":              ckla_rank,
            "qa_accuracy":       ckla_qa_acc,
            "days_studied":      int(ckla_days_studied),
        },
        "math": {
            "total_attempts":   math_total,
            "correct_attempts": math_correct,
            "accuracy_pct":     math_acc,
            "weak_areas":       [{"lesson": r.lesson, "wrong": r.wrong} for r in math_weak],
            "daily_done":       math_daily_done,
            "daily_total":      math_daily_total,
            "wrong_pending":    math_pending,
            "best_fluency":     best_fluency,
        },
    }


# Send
# ─────────────────────────────────────────────────────────

def send_weekly_report(db: Session, to_email: str, child_name: str = "Gia") -> bool:
    """데이터 집계 → HTML 생성 → SMTP 발송."""
    from backend.services.email_sender import _smtp_config

    try:
        data    = collect_weekly_data(db)
        html    = build_html_report(data, child_name)
        today   = date.today().strftime("%b %d, %Y")
        subject = f"{child_name}'s Weekly Learning Report — {today}"

        cfg = _smtp_config()
        if cfg is None:
            logger.info("send_weekly_report: SMTP not configured")
            return False

        msg = MIMEMultipart("alternative")
        msg["From"]    = cfg["from"]
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(
            f"Weekly report for {child_name} — {today}\n"
            "Please view this in an HTML-capable email client.", "plain"
        ))
        msg.attach(MIMEText(html, "html"))

        ctx = ssl.create_default_context()
        if cfg["use_ssl"]:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ctx, timeout=15) as s:
                s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.ehlo()
                s.login(cfg["user"], cfg["password"])
                s.send_message(msg)

        logger.info("send_weekly_report: sent to %s", to_email)
        return True

    except Exception as exc:
        logger.warning("send_weekly_report failed: %s", exc)
        return False
