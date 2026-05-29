"""Tests for backend/services/island_care_engine.py — run_daily_batch().

Covers:
  - Hunger decay applied on first run
  - Idempotency: two calls on the same day decay only once
  - Completed characters are skipped (no decay)
  - Legend-type characters are skipped (no gauge decay)
  - run_daily_batch() return value shape
"""

from datetime import datetime, timedelta, timezone

# island_care_engine uses UTC dates internally via _today() = datetime.now(timezone.utc).date()
# Tests must use the same reference to avoid off-by-one errors in UTC+N timezones.
def _utc_today():
    return datetime.now(timezone.utc).date()

def _utc_yesterday():
    return _utc_today() - timedelta(days=1)

import pytest

from backend.models.island import IslandCharacter, IslandCharacterProgress
from backend.services.island_care_engine import apply_decay, run_daily_batch


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_character(db_session, zone: str = "forest") -> IslandCharacter:
    """Insert a minimal IslandCharacter catalog row and return it."""
    char = IslandCharacter(
        name=f"TestChar_{zone}",
        zone=zone,
        subject="english",
        order_index=1,
        description="test",
        is_available=True,
    )
    db_session.add(char)
    db_session.flush()
    return char


def _make_progress(
    db_session,
    *,
    hunger: int = 80,
    happiness: int = 80,
    is_completed: bool = False,
    is_legend_type: bool = False,
    is_active: bool = True,
    last_decay_date: str | None = None,
) -> IslandCharacterProgress:
    """Create an IslandCharacterProgress row with sensible defaults."""
    char = _make_character(db_session)
    prog = IslandCharacterProgress(
        character_id=char.id,
        nickname="Tester",
        stage="baby",
        hunger=hunger,
        happiness=happiness,
        is_active=is_active,
        is_completed=is_completed,
        is_legend_type=is_legend_type,
        last_decay_date=last_decay_date,
    )
    db_session.add(prog)
    db_session.flush()
    return prog


# ── run_daily_batch return shape ──────────────────────────────────────────────

def test_run_daily_batch_returns_expected_keys(db_session):
    result = run_daily_batch(db_session)
    for key in ("processed", "skipped", "legend_streak_broken"):
        assert key in result, f"Missing key: {key}"


def test_run_daily_batch_empty_db_returns_zeros(db_session):
    result = run_daily_batch(db_session)
    assert result["processed"] == 0
    assert result["skipped"] == 0


# ── Hunger decay ──────────────────────────────────────────────────────────────

def test_hunger_decays_after_one_day_gap(db_session):
    """Character with last_decay_date = yesterday should lose hunger today."""
    yesterday = _utc_yesterday().isoformat()
    prog = _make_progress(db_session, hunger=80, last_decay_date=yesterday)

    result = run_daily_batch(db_session)
    db_session.refresh(prog)

    assert result["processed"] >= 1
    # Hunger should have decreased (exact amount depends on stage/form config)
    assert prog.hunger < 80, f"Expected hunger < 80 after decay, got {prog.hunger}"


def test_hunger_does_not_go_below_zero(db_session):
    """Gauge must be clamped at 0, never negative."""
    yesterday = _utc_yesterday().isoformat()
    prog = _make_progress(db_session, hunger=5, last_decay_date=yesterday)

    run_daily_batch(db_session)
    db_session.refresh(prog)

    assert prog.hunger >= 0


# ── Idempotency ───────────────────────────────────────────────────────────────

def test_run_daily_batch_idempotent_same_day(db_session):
    """Calling run_daily_batch twice in the same day must decay only once."""
    yesterday = _utc_yesterday().isoformat()
    prog = _make_progress(db_session, hunger=80, last_decay_date=yesterday)

    run_daily_batch(db_session)
    db_session.refresh(prog)
    hunger_after_first = prog.hunger

    # Second call — last_decay_date is now today, so this character is skipped
    result2 = run_daily_batch(db_session)
    db_session.refresh(prog)

    assert prog.hunger == hunger_after_first, (
        f"Hunger changed on second run: {hunger_after_first} → {prog.hunger}"
    )
    assert result2["skipped"] >= 1


def test_run_daily_batch_no_decay_when_already_today(db_session):
    """Character whose last_decay_date is already today is counted as skipped."""
    today_str = _utc_today().isoformat()
    _make_progress(db_session, hunger=80, last_decay_date=today_str)

    result = run_daily_batch(db_session)
    assert result["skipped"] >= 1
    assert result["processed"] == 0


# ── Completed character — no decay ────────────────────────────────────────────

def test_completed_character_skips_decay(db_session):
    """is_completed=True characters must not lose gauges."""
    yesterday = _utc_yesterday().isoformat()
    prog = _make_progress(
        db_session, hunger=80, is_completed=True, last_decay_date=yesterday
    )

    run_daily_batch(db_session)
    db_session.refresh(prog)

    # Completed characters are filtered out by run_daily_batch (is_completed=False filter)
    assert prog.hunger == 80


# ── Legend-type character — no gauge decay ────────────────────────────────────

def test_legend_type_character_skips_gauge_decay(db_session):
    """is_legend_type=True characters are not subject to hunger/happiness decay."""
    yesterday = _utc_yesterday().isoformat()
    prog = _make_progress(
        db_session,
        hunger=80,
        happiness=80,
        is_legend_type=True,
        last_decay_date=yesterday,
    )

    run_daily_batch(db_session)
    db_session.refresh(prog)

    # apply_decay returns early for legend-type; gauges unchanged
    assert prog.hunger == 80
    assert prog.happiness == 80


# ── Inactive character — not queried ──────────────────────────────────────────

def test_inactive_character_not_processed(db_session):
    """is_active=False characters must not appear in the decay batch."""
    yesterday = _utc_yesterday().isoformat()
    _make_progress(db_session, hunger=80, is_active=False, last_decay_date=yesterday)

    result = run_daily_batch(db_session)
    # Inactive characters are excluded from the query — 0 processed, 0 skipped
    assert result["processed"] == 0
    assert result["skipped"] == 0


# ── apply_decay directly ──────────────────────────────────────────────────────

def test_apply_decay_updates_last_decay_date(db_session):
    """apply_decay must stamp last_decay_date = today."""
    yesterday = _utc_yesterday().isoformat()
    prog = _make_progress(db_session, hunger=80, last_decay_date=yesterday)

    apply_decay(db_session, prog.id)
    db_session.refresh(prog)

    assert prog.last_decay_date == _utc_today().isoformat()
