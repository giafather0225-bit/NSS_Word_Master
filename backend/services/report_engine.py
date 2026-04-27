"""
services/report_engine.py — Weekly parent report: data aggregation + HTML email builder
Section: Parent
Dependencies: models (LearningLog, WordAttempt, XPLog, MathAttempt, MathDailyChallenge,
              MathWrongReview, MathFactFluency), services/xp_engine, services/streak_engine
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

# ── Email palette (theme.css hex equivalents — CSS vars not allowed in email) ──
_C = {
    "page":         "#FAF6EF",
    "card":         "#FFFFFF",
    "surface":      "#EFE8DB",
    "text":         "#2B2722",
    "text_sub":     "#706659",
    "text_hint":    "#A79A89",
    "text_on":      "#FFFFFF",
    "border":       "#DCD2C2",
    "border_sub":   "#EBE3D5",
    # sections
    "eng":          "#7FA8CC",
    "eng_light":    "#EEF4FA",
    "eng_soft":     "#CFE0EE",
    "eng_ink":      "#345A80",
    "math":         "#8AC4A8",
    "math_light":   "#EEF7F2",
    "math_soft":    "#CFE6D9",
    "math_ink":     "#3A6A54",
    "diary":        "#E09AAE",
    "arcade":       "#EEC770",
    "arcade_light": "#FBF3DE",
    "arcade_ink":   "#7A5A1E",
    "rewards":      "#B8A4DC",
    "rewards_light":"#F2ECFA",
    # state
    "success":      "#8FBF87",
    "success_light":"#E8F5E4",
    "success_ink":  "#4E7A46",
    "error":        "#D97A7A",
    "error_light":  "#FAEAEA",
    "error_ink":    "#8A4538",
    "warning":      "#EEC770",
    "warning_light":"#FBF3DE",
    # brand
    "primary":      "#E09AAE",
}


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


# ─────────────────────────────────────────────────────────
# HTML builder
# ─────────────────────────────────────────────────────────

def _bar(value: int, max_val: int, color: str, height: int = 40) -> str:
    pct = int(value / max_val * 100) if max_val else 0
    bg  = _C["border_sub"]
    return (
        f'<td style="text-align:center;vertical-align:bottom;padding:0 3px;">' +
        f'<div style="background:{color};width:30px;height:{max(pct * height // 100, 2)}px;' +
        f'border-radius:4px 4px 0 0;margin:0 auto;"></div></td>'
    )


def _acc_row(label: str, acc: float, count: int) -> str:
    color = _C["success"] if acc >= 80 else (_C["warning"] if acc >= 60 else _C["error"])
    w     = int(acc)
    return f"""
    <tr>
      <td style="font-size:12px;color:{_C['text']};width:100px;padding:5px 0;">{label}</td>
      <td style="padding:5px 8px;">
        <div style="background:{_C['border_sub']};border-radius:4px;height:7px;">
          <div style="background:{color};width:{w}%;height:7px;border-radius:4px;"></div>
        </div>
      </td>
      <td style="font-size:12px;font-weight:700;color:{color};width:40px;">{acc}%</td>
      <td style="font-size:11px;color:{_C['text_hint']};padding-left:6px;">{count}x</td>
    </tr>"""


def _section_header(title: str, color: str, light: str, ink: str) -> str:
    return f"""
    <tr>
      <td style="padding:24px 0 12px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="width:4px;background:{color};border-radius:2px;">&nbsp;</td>
            <td style="padding-left:12px;">
              <span style="font-size:11px;font-weight:700;letter-spacing:0.08em;
                color:{ink};text-transform:uppercase;">{title}</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def build_html_report(data: dict, child_name: str = "Gia") -> str:
    """HTML 이메일 템플릿 생성. 이모지 없음, 컬러 바로 섹션 구분."""
    c = _C

    # 일별 XP 바
    max_xp  = max((d["xp"] for d in data["daily_activity"]), default=1) or 1
    day_bars = ""
    for d in data["daily_activity"]:
        pct   = int(d["xp"] / max_xp * 100)
        color = c["eng"] if pct > 0 else c["border_sub"]
        h     = max(pct * 48 // 100, 2)
        day_bars += f"""
        <td style="text-align:center;vertical-align:bottom;padding:0 3px;">
          <div style="background:{color};width:30px;height:{h}px;
               border-radius:4px 4px 0 0;margin:0 auto;"></div>
          <div style="font-size:10px;color:{c['text_hint']};margin-top:4px;">{d['label']}</div>
          <div style="font-size:9px;color:{c['text_hint']};margin-top:1px;">{d['xp']}xp</div>
        </td>"""

    # 스테이지 정확도 행
    stage_rows = "".join(_acc_row(s["label"], s["accuracy"], s["count"]) for s in data["stage_stats"])
    if not stage_rows:
        stage_rows = f'<tr><td colspan="4" style="color:{c["text_hint"]};font-size:13px;padding:8px 0;">No stage data this week.</td></tr>'

    # 취약 단어 행
    weak_rows = ""
    for w in data["weak_words"]:
        acc   = w["accuracy"]
        color = c["error"] if acc < 50 else c["warning"]
        weak_rows += f"""
        <tr>
          <td style="font-size:13px;font-weight:700;color:{c['text']};padding:5px 0;">{w['word']}</td>
          <td style="font-size:12px;color:{c['text_sub']};padding:5px 12px;">{w['attempts']} attempts</td>
          <td style="font-size:13px;font-weight:700;color:{color};">{int(acc)}%</td>
        </tr>"""
    if not weak_rows:
        weak_rows = f'<tr><td colspan="3" style="font-size:13px;color:{c["success_ink"]};padding:8px 0;">No weak words this week — great work!</td></tr>'

    # 레슨 태그
    lesson_tags = ""
    for l in data["lessons_studied"][:6]:
        lesson_tags += (
            f'<span style="display:inline-block;background:{c["eng_light"]};' +
            f'color:{c["eng_ink"]};border-radius:99px;padding:3px 12px;' +
            f'font-size:12px;margin:3px 3px 3px 0;">{l["lesson"]}</span>'
        )
    if not lesson_tags:
        lesson_tags = f'<span style="color:{c["text_hint"]};font-size:13px;">No lessons this week.</span>'

    # Math 취약 개념
    math_weak_rows = ""
    for w in data["math"]["weak_areas"]:
        math_weak_rows += f"""
        <tr>
          <td style="font-size:13px;color:{c['text']};padding:4px 0;">{w['lesson']}</td>
          <td style="font-size:12px;color:{c['error']};font-weight:700;
              padding:4px 0 4px 12px;">{w['wrong']} wrong</td>
        </tr>"""
    if not math_weak_rows:
        math_weak_rows = f'<tr><td colspan="2" style="font-size:13px;color:{c["success_ink"]};padding:4px 0;">No weak areas this week!</td></tr>'

    # Math daily progress bar
    math_d_done  = data["math"]["daily_done"]
    math_d_total = max(data["math"]["daily_total"], 1)
    math_d_pct   = int(math_d_done / math_d_total * 100)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weekly Report — {child_name}</title>
</head>
<body style="margin:0;padding:0;background:{c['page']};
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0"
  style="background:{c['page']};padding:32px 16px;">
<tr><td>
<table width="600" cellpadding="0" cellspacing="0" align="center"
  style="background:{c['card']};border-radius:16px;overflow:hidden;
         border:1px solid {c['border']};
         box-shadow:0 2px 8px rgba(120,90,60,0.08);">

  <!-- ── Header ───────────────────────────────── -->
  <tr>
    <td style="background:{c['primary']};padding:28px 40px;text-align:center;">
      <div style="font-size:11px;font-weight:700;letter-spacing:0.1em;
           color:rgba(255,255,255,0.8);text-transform:uppercase;margin-bottom:6px;">
        Weekly Learning Report
      </div>
      <div style="font-size:26px;font-weight:700;color:{c['text_on']};margin-bottom:4px;">
        {child_name}'s Progress
      </div>
      <div style="font-size:13px;color:rgba(255,255,255,0.75);">
        {data['week_label']}
      </div>
    </td>
  </tr>

  <!-- ── Summary cards ────────────────────────── -->
  <tr>
    <td style="padding:28px 40px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="text-align:center;padding:16px 6px;
              background:{c['eng_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['eng']};">{data['week_xp']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">XP This Week</div>
          </td>
          <td width="8"></td>
          <td style="text-align:center;padding:16px 6px;
              background:{c['success_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['success_ink']};">{data['words_correct']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">Words Mastered</div>
          </td>
          <td width="8"></td>
          <td style="text-align:center;padding:16px 6px;
              background:{c['arcade_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['arcade_ink']};">{data['streak']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">Day Streak</div>
          </td>
          <td width="8"></td>
          <td style="text-align:center;padding:16px 6px;
              background:{c['rewards_light']};border-radius:12px;">
            <div style="font-size:26px;font-weight:700;color:{c['rewards']};">{data['total_minutes']}</div>
            <div style="font-size:11px;color:{c['text_sub']};margin-top:4px;">Min Studied</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ── Body ─────────────────────────────────── -->
  <tr><td style="padding:0 40px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0">

      <!-- Daily activity chart -->
      {_section_header("Daily Activity", c['eng'], c['eng_light'], c['eng_ink'])}
      <tr>
        <td>
          <table cellpadding="0" cellspacing="0" style="height:80px;">
            <tr style="vertical-align:bottom;">{day_bars}</tr>
          </table>
        </td>
      </tr>

      <!-- English section -->
      {_section_header("English — Stage Performance", c['eng'], c['eng_light'], c['eng_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            {stage_rows}
          </table>
        </td>
      </tr>

      <!-- Weak words -->
      {_section_header("Words Needing Practice", c['error'], c['error_light'], c['error_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            {weak_rows}
          </table>
        </td>
      </tr>

      <!-- Lessons studied -->
      {_section_header("Lessons Studied", c['eng'], c['eng_light'], c['eng_ink'])}
      <tr><td style="padding-bottom:8px;">{lesson_tags}</td></tr>

      <!-- Math section -->
      {_section_header("Math", c['math'], c['math_light'], c['math_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:4px 0;font-size:13px;color:{c['text_sub']};">Accuracy (7 days)</td>
              <td style="padding:4px 0;font-size:13px;font-weight:700;
                  color:{c['math_ink']};text-align:right;">{data['math']['accuracy_pct']}%</td>
            </tr>
            <tr>
              <td style="padding:4px 0;font-size:13px;color:{c['text_sub']};">Daily Challenge</td>
              <td style="padding:4px 0;font-size:13px;font-weight:700;
                  color:{c['math_ink']};text-align:right;">
                {math_d_done} / {data['math']['daily_total']} days
              </td>
            </tr>
            <tr>
              <td colspan="2" style="padding:6px 0 2px;">
                <div style="background:{c['border_sub']};border-radius:4px;height:6px;">
                  <div style="background:{c['math']};width:{math_d_pct}%;
                       height:6px;border-radius:4px;"></div>
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0 4px;font-size:13px;color:{c['text_sub']};">
                Wrong Review pending</td>
              <td style="padding:8px 0 4px;font-size:13px;font-weight:700;
                  color:{c['error']};text-align:right;">
                {data['math']['wrong_pending']} items
              </td>
            </tr>
            <tr>
              <td style="padding:4px 0;font-size:13px;color:{c['text_sub']};">
                Fact Fluency best</td>
              <td style="padding:4px 0;font-size:13px;font-weight:700;
                  color:{c['math_ink']};text-align:right;">
                {data['math']['best_fluency']} pts
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Math weak areas -->
      {_section_header("Math — Weak Areas", c['math'], c['math_light'], c['math_ink'])}
      <tr>
        <td>
          <table width="100%" cellpadding="0" cellspacing="0">
            {math_weak_rows}
          </table>
        </td>
      </tr>

      <!-- Overall stats -->
      {_section_header("Overall Progress", c['primary'], c['rewards_light'], c['text'])}
      <tr>
        <td style="background:{c['surface']};border-radius:12px;padding:16px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="font-size:13px;color:{c['text_sub']};padding:3px 0;">Total XP</td>
              <td style="font-size:13px;font-weight:700;color:{c['text']};
                  text-align:right;">{data['total_xp']:,} XP</td>
            </tr>
            <tr>
              <td style="font-size:13px;color:{c['text_sub']};padding:3px 0;">
                Avg Accuracy</td>
              <td style="font-size:13px;font-weight:700;color:{c['text']};
                  text-align:right;">{data['avg_accuracy']}%</td>
            </tr>
            <tr>
              <td style="font-size:13px;color:{c['text_sub']};padding:3px 0;">Sessions</td>
              <td style="font-size:13px;font-weight:700;color:{c['text']};
                  text-align:right;">{data['total_sessions']}</td>
            </tr>
          </table>
        </td>
      </tr>

    </table>
  </td></tr>

  <!-- ── Footer ───────────────────────────────── -->
  <tr>
    <td style="background:{c['surface']};padding:16px 40px;text-align:center;
        border-top:1px solid {c['border_sub']};">
      <div style="font-size:11px;color:{c['text_hint']};">
        NSS Word Master · Weekly Report · Auto-generated
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return html


# ─────────────────────────────────────────────────────────
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
