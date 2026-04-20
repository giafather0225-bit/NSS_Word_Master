"""Tests for backend/services/streak_engine.py."""
from datetime import date, datetime, timedelta

import pytest

from backend.models import AppConfig, DayOffRequest, StreakLog, WordReview
from backend.services.streak_engine import (
    check_streak_bonus,
    get_current_streak,
    get_or_create_streak_log,
    mark_daily_words_done,
    mark_game_done,
    mark_math_done,
    mark_review_done,
)


@pytest.fixture(autouse=True)
def _clean_streak_tables(db_session):
    """streak_engine commits to the shared in-memory DB; wipe tables each test."""
    for model in (StreakLog, DayOffRequest, AppConfig, WordReview):
        db_session.query(model).delete()
    db_session.commit()
    yield
    for model in (StreakLog, DayOffRequest, AppConfig, WordReview):
        db_session.query(model).delete()
    db_session.commit()


def _make_maintained_log(db, day: str) -> StreakLog:
    log = StreakLog(
        date=day,
        review_done=True,
        daily_words_done=True,
        math_done=True,
        game_done=True,
        streak_maintained=True,
    )
    db.add(log)
    db.commit()
    return log


def test_get_or_create_streak_log(db_session):
    day = date.today().isoformat()
    log1 = get_or_create_streak_log(db_session, day)
    assert log1.id is not None
    assert log1.date == day
    assert log1.review_done is False
    assert log1.streak_maintained is False

    log2 = get_or_create_streak_log(db_session, day)
    assert log2.id == log1.id
    assert db_session.query(StreakLog).count() == 1


def test_mark_review_done(db_session):
    day = date.today().isoformat()
    mark_review_done(db_session, day)
    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.review_done is True


def test_mark_daily_words_done(db_session):
    day = date.today().isoformat()
    mark_daily_words_done(db_session, day)
    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.daily_words_done is True


def test_mark_math_done(db_session):
    day = date.today().isoformat()
    mark_math_done(db_session, day)
    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.math_done is True


def test_mark_game_done(db_session):
    day = date.today().isoformat()
    mark_game_done(db_session, day)
    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.game_done is True


def test_evaluate_streak_all_done(db_session):
    """Default config requires english(review+daily_words) + math + game."""
    day = date.today().isoformat()
    mark_review_done(db_session, day)
    mark_daily_words_done(db_session, day)
    mark_math_done(db_session, day)
    mark_game_done(db_session, day)

    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.streak_maintained is True


def test_evaluate_streak_partial(db_session):
    day = date.today().isoformat()
    mark_review_done(db_session, day)
    mark_daily_words_done(db_session, day)
    # No math, no game → default mode="all" fails

    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.streak_maintained is False


def test_evaluate_streak_no_reviews_due_daily_words_only(db_session):
    """English is satisfied by daily_words alone when no SM-2 reviews are due."""
    day = date.today().isoformat()
    # Seed a future-dated review so no reviews are due on `day`.
    future = (date.today() + timedelta(days=3)).isoformat()
    db_session.add(WordReview(word="apple", next_review=future))
    db_session.commit()

    mark_daily_words_done(db_session, day)
    mark_math_done(db_session, day)
    mark_game_done(db_session, day)

    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.streak_maintained is True


def test_evaluate_streak_reviews_due_requires_review_done(db_session):
    """When a review is due, daily_words alone is insufficient for english."""
    day = date.today().isoformat()
    past = (date.today() - timedelta(days=1)).isoformat()
    db_session.add(WordReview(word="apple", next_review=past))
    db_session.commit()

    mark_daily_words_done(db_session, day)
    mark_math_done(db_session, day)
    mark_game_done(db_session, day)

    log = db_session.query(StreakLog).filter(StreakLog.date == day).one()
    assert log.streak_maintained is False


def test_get_current_streak(db_session):
    today = date.today()
    # 5 consecutive maintained days ending today
    for i in range(5):
        _make_maintained_log(db_session, (today - timedelta(days=i)).isoformat())

    assert get_current_streak(db_session) == 5


def test_streak_break(db_session):
    today = date.today()
    # Maintained today + yesterday, gap 2 days ago, maintained 3 days ago
    _make_maintained_log(db_session, today.isoformat())
    _make_maintained_log(db_session, (today - timedelta(days=1)).isoformat())
    # Explicit unmaintained log 2 days ago (the gap)
    db_session.add(StreakLog(
        date=(today - timedelta(days=2)).isoformat(),
        review_done=False,
        daily_words_done=False,
        math_done=False,
        game_done=False,
        streak_maintained=False,
    ))
    db_session.commit()
    _make_maintained_log(db_session, (today - timedelta(days=3)).isoformat())

    # Only today + yesterday count; the break resets the count
    assert get_current_streak(db_session) == 2


def test_check_streak_bonus(db_session):
    assert check_streak_bonus(db_session, 0) is None
    assert check_streak_bonus(db_session, 1) is None
    assert check_streak_bonus(db_session, 6) is None
    assert check_streak_bonus(db_session, 7) == "streak_7_bonus"
    assert check_streak_bonus(db_session, 14) == "streak_7_bonus"
    assert check_streak_bonus(db_session, 29) is None
    assert check_streak_bonus(db_session, 30) == "streak_30_bonus"
    assert check_streak_bonus(db_session, 60) == "streak_30_bonus"
