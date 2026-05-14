"""Tests for routers/parent_ckla.py — Parent Dashboard CKLA summary + chart.

Covers GET /api/parent/ckla-summary and GET /api/parent/ckla-chart.
StaticPool test DB: autouse fixture wipes CKLA tables + XPLog + AppConfig.
"""
from datetime import date, timedelta

import pytest

from backend.models import (
    CKLADomain, CKLALesson, CKLALessonProgress, CKLAQuestionResponse,
)
from backend.models.gamification import XPLog
from backend.models.system import AppConfig


@pytest.fixture(autouse=True)
def _clean_ckla_tables(db_session):
    """Wipe CKLA + XPLog + AppConfig rows before/after each test."""
    def _wipe():
        for model in (
            CKLAQuestionResponse, CKLALessonProgress, CKLALesson, CKLADomain,
            XPLog, AppConfig,
        ):
            db_session.query(model).delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


def _seed_domain(db, domain_num=1, grade=3, lessons=2):
    """Seed one active domain with `lessons` active lessons. Returns (domain, [lessons])."""
    d = CKLADomain(domain_num=domain_num, title=f"Domain {domain_num}",
                   source_pdf="t.pdf", lesson_count=lessons, is_active=True, grade=grade)
    db.add(d)
    db.flush()
    rows = []
    for i in range(lessons):
        l = CKLALesson(domain_id=d.id, domain_num=domain_num, lesson_num=i + 1,
                       title=f"L{i+1}", passage="x" * 200, passage_chars=200,
                       word_work_word="test", is_active=True, grade=grade)
        db.add(l)
        rows.append(l)
    db.flush()
    db.commit()
    return d, rows


# ── ckla-summary ──────────────────────────────────────────────────

def test_summary_empty_shape(client):
    r = client.get("/api/parent/ckla-summary?grade=3")
    assert r.status_code == 200
    body = r.json()
    for key in (
        "grade", "total_lessons", "completed_lessons", "today_lessons",
        "today_studied", "domains", "qa_accuracy", "qa_total", "needs_review",
        "weekly_chart", "difficulty_breakdown", "estimated_completion_days",
        "domain_test_alerts", "final_test_locked", "start_time_pattern",
    ):
        assert key in body
    assert body["grade"] == 3
    assert body["total_lessons"] == 0
    assert body["domains"] == []
    assert len(body["weekly_chart"]) == 14


@pytest.mark.parametrize("grade", [2, 9])
def test_summary_grade_out_of_range(client, grade):
    assert client.get(f"/api/parent/ckla-summary?grade={grade}").status_code == 422


def test_summary_counts_domains_and_lessons(client, db_session):
    _seed_domain(db_session, domain_num=1, lessons=3)
    body = client.get("/api/parent/ckla-summary?grade=3").json()
    assert body["total_lessons"] == 3
    assert len(body["domains"]) == 1
    assert body["domains"][0]["lesson_count"] == 3
    assert body["domains"][0]["completed_count"] == 0
    assert body["domains"][0]["all_complete"] is False


def test_summary_completed_lesson_counted(client, db_session):
    _, lessons = _seed_domain(db_session, lessons=2)
    today = date.today().isoformat()
    db_session.add(CKLALessonProgress(
        lesson_id=lessons[0].id, completed=True,
        completed_at=f"{today}T10:30:00", difficulty_rating="easy", grade=3,
    ))
    db_session.commit()
    body = client.get("/api/parent/ckla-summary?grade=3").json()
    assert body["completed_lessons"] == 1
    assert body["today_lessons"] == 1
    assert body["today_studied"] is True
    assert body["difficulty_breakdown"]["easy"] == 1
    assert body["domains"][0]["completed_count"] == 1


def test_summary_qa_accuracy_and_needs_review(client, db_session):
    _, lessons = _seed_domain(db_session, lessons=1)
    db_session.add_all([
        CKLAQuestionResponse(question_id=1, user_answer="good", ai_score=2,
                             ai_feedback="ok", needs_parent_review=False),
        CKLAQuestionResponse(question_id=2, user_answer="bad", ai_score=0,
                             ai_feedback="redo", needs_parent_review=True),
    ])
    db_session.commit()
    body = client.get("/api/parent/ckla-summary?grade=3").json()
    assert body["qa_total"] == 2
    assert body["qa_accuracy"] == 50
    assert len(body["needs_review"]) == 1
    assert body["needs_review"][0]["question_id"] == 2


def test_summary_domain_test_passed_from_xplog(client, db_session):
    _seed_domain(db_session, domain_num=1, lessons=1)
    db_session.add(XPLog(action="ckla_domain_test_pass",
                         detail="domain_1_grade_3", xp_amount=30))
    db_session.commit()
    body = client.get("/api/parent/ckla-summary?grade=3").json()
    assert body["domains"][0]["domain_test_passed"] is True


def test_summary_domain_test_alerts(client, db_session):
    _seed_domain(db_session, domain_num=1, lessons=1)
    db_session.add(AppConfig(
        key="ckla_domain_test_consec_fails_d1_g3", value="3"))
    db_session.commit()
    body = client.get("/api/parent/ckla-summary?grade=3").json()
    assert len(body["domain_test_alerts"]) == 1
    assert body["domain_test_alerts"][0]["consec_fails"] == 3


# ── ckla-chart ────────────────────────────────────────────────────

def test_chart_week_returns_7_days(client, db_session):
    _seed_domain(db_session, lessons=1)
    body = client.get("/api/parent/ckla-chart?range=week&grade=3").json()
    assert body["grouped_by"] == "day"
    assert len(body["chart"]) == 7


def test_chart_month_returns_30_days(client, db_session):
    _seed_domain(db_session, lessons=1)
    body = client.get("/api/parent/ckla-chart?range=month&grade=3").json()
    assert len(body["chart"]) == 30


def test_chart_full_empty(client):
    body = client.get("/api/parent/ckla-chart?range=full&grade=3").json()
    assert body == {"chart": [], "grouped_by": "week"}


def test_chart_counts_completion(client, db_session):
    _, lessons = _seed_domain(db_session, lessons=1)
    today = date.today().isoformat()
    db_session.add(CKLALessonProgress(
        lesson_id=lessons[0].id, completed=True,
        completed_at=f"{today}T09:00:00", grade=3,
    ))
    db_session.commit()
    body = client.get("/api/parent/ckla-chart?range=week&grade=3").json()
    assert body["chart"][-1]["count"] == 1


def test_chart_invalid_range_422(client):
    assert client.get("/api/parent/ckla-chart?range=year&grade=3").status_code == 422


def test_chart_grade_out_of_range_422(client):
    assert client.get("/api/parent/ckla-chart?range=week&grade=1").status_code == 422
