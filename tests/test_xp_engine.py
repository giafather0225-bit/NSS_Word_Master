"""Tests for backend/services/xp_engine.py."""
from datetime import date, datetime

import pytest

from backend.models import AppConfig, WordReview, XPLog
from backend.services import xp_engine
from backend.services.xp_engine import (
    ARCADE_DAILY_CAP_DEFAULT,
    XP_RULES_DEFAULT,
    award_arcade_xp,
    award_xp,
    get_today_xp,
    get_total_xp,
    get_words_known,
    get_xp_rules,
    score_to_arcade_tier,
    spend_xp,
)


@pytest.fixture(autouse=True)
def _clean_xp_tables(db_session):
    """xp_engine commits to the shared in-memory DB; wipe tables each test."""
    for model in (XPLog, AppConfig, WordReview):
        db_session.query(model).delete()
    db_session.commit()
    yield
    for model in (XPLog, AppConfig, WordReview):
        db_session.query(model).delete()
    db_session.commit()


def _set_config(db, key: str, value: str) -> None:
    db.add(AppConfig(key=key, value=value, updated_at=datetime.now().isoformat()))
    db.commit()


def test_xp_rules_default(db_session):
    rules = get_xp_rules(db_session)
    assert set(rules.keys()) == set(XP_RULES_DEFAULT.keys())
    for k, v in XP_RULES_DEFAULT.items():
        assert rules[k] == v


def test_xp_rules_override(db_session):
    _set_config(db_session, "xp_rule_word_correct", "5")
    rules = get_xp_rules(db_session)
    assert rules["word_correct"] == 5
    # Other rules stay at defaults
    assert rules["stage_complete"] == XP_RULES_DEFAULT["stage_complete"]


def test_award_xp_basic(db_session):
    awarded = award_xp(db_session, "word_correct", detail="apple")
    assert awarded == XP_RULES_DEFAULT["word_correct"]
    log = db_session.query(XPLog).filter(XPLog.action == "word_correct").one()
    assert log.xp_amount == XP_RULES_DEFAULT["word_correct"]
    assert log.detail == "apple"
    assert log.earned_date == date.today().isoformat()


def test_award_xp_dedup(db_session):
    first = award_xp(db_session, "stage_complete")
    second = award_xp(db_session, "stage_complete")
    assert first == XP_RULES_DEFAULT["stage_complete"]
    assert second == 0
    count = db_session.query(XPLog).filter(XPLog.action == "stage_complete").count()
    assert count == 1


def test_award_xp_word_correct_no_dedup(db_session):
    a = award_xp(db_session, "word_correct", detail="apple")
    b = award_xp(db_session, "word_correct", detail="banana")
    c = award_xp(db_session, "word_correct", detail="cherry")
    assert a == b == c == XP_RULES_DEFAULT["word_correct"]
    count = db_session.query(XPLog).filter(XPLog.action == "word_correct").count()
    assert count == 3


def test_award_xp_unknown_action(db_session):
    assert award_xp(db_session, "not_a_real_action") == 0
    assert db_session.query(XPLog).count() == 0


def test_get_total_xp(db_session):
    award_xp(db_session, "stage_complete")            # +2
    award_xp(db_session, "final_test_pass")           # +10
    award_xp(db_session, "word_correct", detail="a")  # +1
    award_xp(db_session, "word_correct", detail="b")  # +1
    expected = (
        XP_RULES_DEFAULT["stage_complete"]
        + XP_RULES_DEFAULT["final_test_pass"]
        + 2 * XP_RULES_DEFAULT["word_correct"]
    )
    assert get_total_xp(db_session) == expected


def test_get_today_xp(db_session):
    # Past-dated entry should not count
    db_session.add(XPLog(
        action="stage_complete",
        xp_amount=99,
        detail="old",
        earned_date="2000-01-01",
        created_at=datetime.now().isoformat(),
    ))
    db_session.commit()

    award_xp(db_session, "final_test_pass")  # today, +10
    award_xp(db_session, "unit_test_pass")   # today, +5
    expected = XP_RULES_DEFAULT["final_test_pass"] + XP_RULES_DEFAULT["unit_test_pass"]
    assert get_today_xp(db_session) == expected


def test_spend_xp_success(db_session):
    award_xp(db_session, "final_test_pass")  # +10
    award_xp(db_session, "unit_test_pass")   # +5  => 15 total
    ok = spend_xp(db_session, 10, detail="YouTube 30min")
    assert ok is True
    assert get_total_xp(db_session) == 5
    purchase = db_session.query(XPLog).filter(XPLog.action == "shop_purchase").one()
    assert purchase.xp_amount == -10
    assert purchase.detail == "YouTube 30min"


def test_spend_xp_insufficient(db_session):
    award_xp(db_session, "stage_complete")  # +2
    ok = spend_xp(db_session, 100, detail="too expensive")
    assert ok is False
    assert get_total_xp(db_session) == XP_RULES_DEFAULT["stage_complete"]
    assert db_session.query(XPLog).filter(XPLog.action == "shop_purchase").count() == 0


@pytest.mark.parametrize("score,tier", [
    (0, 0),
    (499, 0),
    (500, 1),
    (999, 1),
    (1000, 2),
    (1999, 2),
    (2000, 3),
    (5000, 3),
])
def test_score_to_arcade_tier(score, tier):
    assert score_to_arcade_tier(score) == tier


def test_award_arcade_xp_basic(db_session):
    result = award_arcade_xp(db_session, score=600)
    assert result["tier"] == 1
    assert result["xp_awarded"] == 1
    assert result["daily_total"] == 1
    assert result["daily_cap"] == ARCADE_DAILY_CAP_DEFAULT
    log = db_session.query(XPLog).filter(XPLog.action == "arcade_play").one()
    assert log.xp_amount == 1


def test_award_arcade_xp_daily_cap(db_session):
    # Lower cap to make hitting it fast
    _set_config(db_session, "arcade_daily_cap", "4")

    r1 = award_arcade_xp(db_session, score=2000)  # tier 3 → +3, total 3
    assert r1["xp_awarded"] == 3
    assert r1["daily_total"] == 3

    r2 = award_arcade_xp(db_session, score=2000)  # tier 3, but only 1 remaining
    assert r2["tier"] == 3
    assert r2["xp_awarded"] == 1
    assert r2["daily_total"] == 4
    assert r2["daily_cap"] == 4

    r3 = award_arcade_xp(db_session, score=2000)  # cap exhausted
    assert r3["xp_awarded"] == 0
    assert r3["daily_total"] == 4


def test_get_words_known(db_session):
    today_iso = date.today().isoformat()

    def mk(word: str, interval: int) -> WordReview:
        return WordReview(
            word=word,
            subject="English",
            textbook="Voca_8000",
            lesson="Lesson_01",
            easiness=2.5,
            interval=interval,
            repetitions=1,
            next_review=today_iso,
            last_review=today_iso,
            total_reviews=1,
            total_correct=1,
            source="manual",
        )

    db_session.add_all([
        mk("a", 0),
        mk("b", 6),
        mk("c", 7),
        mk("d", 14),
        mk("e", 30),
    ])
    db_session.commit()

    assert get_words_known(db_session) == 3
