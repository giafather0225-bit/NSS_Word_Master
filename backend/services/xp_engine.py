"""
services/xp_engine.py — XP calculation and award logic
Section: System
Dependencies: models.py (XPLog, WordReview)
API: called by routers/xp.py
"""
from typing import Optional

import logging
import time
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend.models import XPLog, WordReview, AppConfig

logger = logging.getLogger(__name__)

# ── AppConfig TTL cache ──────────────────────────────────────────
# get_xp_rules() and get_arcade_daily_cap() are called on every XP award.
# Caching for 30 s avoids repeated full-table scans of app_config on the
# hot study path. Cache is module-level (shared across requests in the
# same process) and is invalidated when the parent changes XP rules via
# the Settings UI (the PUT endpoint calls invalidate_xp_cache()).
_XP_RULES_TTL   = 30.0   # seconds
_xp_rules_cache: Optional[dict] = None
_xp_rules_at:    float  = 0.0

_ARCADE_CAP_TTL  = 30.0
_arcade_cap_cache: Optional[int] = None
_arcade_cap_at:    float      = 0.0

_LUMI_RULES_TTL  = 30.0
_lumi_rules_cache: Optional[dict[str, int]] = None
_lumi_rules_at:    float               = 0.0

_BOOST_TTL  = 30.0
_boost_cache: Optional[dict[str, float]] = None
_boost_at:    float                   = 0.0


def invalidate_xp_cache() -> None:
    """Drop cached XP rules, arcade cap, lumi rules, and boost (call from Settings PUT endpoints)."""
    global _xp_rules_cache, _xp_rules_at, _arcade_cap_cache, _arcade_cap_at
    global _lumi_rules_cache, _lumi_rules_at, _boost_cache, _boost_at
    _xp_rules_cache  = None
    _xp_rules_at     = 0.0
    _arcade_cap_cache = None
    _arcade_cap_at    = 0.0
    _lumi_rules_cache = None
    _lumi_rules_at    = 0.0
    _boost_cache      = None
    _boost_at         = 0.0

# XP awarded per action — defaults. Parent can override via app_config
# keys of the form `xp_rule_<action>`. See get_xp_rules().
# Lumi awarded per XP action — config key → (app_config_key, earn_source)
_LUMI_ACTION_MAP: dict[str, tuple[str, str]] = {
    "stage_complete":       ("lumi_rule_english_stage", "english_stage"),
    "final_test_pass":      ("lumi_rule_english_final", "english_final_test"),
    "math_lesson_complete": ("lumi_rule_math_lesson",   "math_lesson"),
    "math_unit_test_pass":  ("lumi_rule_math_unit",     "math_unit_test"),
    "journal_complete":     ("lumi_rule_diary",          "diary"),
    "review_complete":      ("lumi_rule_review",         "review"),
}
_LUMI_DEFAULTS: dict[str, int] = {
    "lumi_rule_english_stage": 3,
    "lumi_rule_english_final": 15,
    "lumi_rule_math_lesson":   10,
    "lumi_rule_math_unit":     20,
    "lumi_rule_diary":          8,
    "lumi_rule_review":         5,
    "lumi_rule_streak":         5,
}


def _get_lumi_rules(db: Session) -> dict[str, int]:
    """Return all lumi_rule_* AppConfig values, cached for _LUMI_RULES_TTL seconds.

    Falls back to _LUMI_DEFAULTS for any key not present in app_config.
    Cache is invalidated by invalidate_xp_cache() (called from parent Settings PUT).
    """
    global _lumi_rules_cache, _lumi_rules_at
    if _lumi_rules_cache is not None and time.monotonic() - _lumi_rules_at < _LUMI_RULES_TTL:
        return _lumi_rules_cache
    rows = (
        db.query(AppConfig)
        .filter(AppConfig.key.like("lumi_rule_%"))
        .all()
    )
    merged = dict(_LUMI_DEFAULTS)
    for row in rows:
        try:
            merged[row.key] = max(0, int(row.value))
        except (TypeError, ValueError):
            pass
    _lumi_rules_cache = merged
    _lumi_rules_at    = time.monotonic()
    return merged


def _get_boost_pct(db: Session) -> dict[str, float]:
    """Return cached lumi_boost_* percentages from app_config.

    Keys: english, math, diary, review, total.
    All default to 0.0 if not set. Cache TTL = _BOOST_TTL seconds.
    Invalidated by invalidate_xp_cache().
    """
    global _boost_cache, _boost_at
    if _boost_cache is not None and time.monotonic() - _boost_at < _BOOST_TTL:
        return _boost_cache
    keys = ("lumi_boost_total", "lumi_boost_english", "lumi_boost_math",
            "lumi_boost_diary", "lumi_boost_review")
    rows = db.query(AppConfig).filter(AppConfig.key.in_(keys)).all()
    result: dict[str, float] = {
        "total": 0.0, "english": 0.0, "math": 0.0, "diary": 0.0, "review": 0.0,
    }
    for row in rows:
        short = row.key.replace("lumi_boost_", "")
        try:
            result[short] = float(row.value)
        except (TypeError, ValueError):
            pass
    _boost_cache = result
    _boost_at    = time.monotonic()
    return result


def _apply_boost(xp: int, action: str, db: Session) -> int:
    """Return XP after applying completed-character boost for this action's subject.

    Boost = floor(xp × (1 + (subject_pct + total_pct) / 100)).
    No-op if island is off or no completed characters boosting.
    """
    try:
        boosts  = _get_boost_pct(db)
        subject = _infer_source(action)  # english/math/diary/review/""
        pct     = boosts.get(subject, 0.0) + boosts.get("total", 0.0)
        if pct <= 0:
            return xp
        return int(xp * (1.0 + pct / 100.0))
    except Exception:
        return xp


def _award_lumi_for_action(db: Session, action: str) -> None:
    """Award Lumi alongside XP for supported study actions. Silent on any error.

    Uses a TTL-cached bulk fetch of all lumi_rule_* AppConfig rows instead
    of one query per action — avoids repeated round-trips on the hot study path.
    """
    entry = _LUMI_ACTION_MAP.get(action)
    if entry is None:
        return
    cfg_key, earn_source = entry
    try:
        rules  = _get_lumi_rules(db)
        amount = rules.get(cfg_key, _LUMI_DEFAULTS.get(cfg_key, 0))
    except Exception:
        amount = _LUMI_DEFAULTS.get(cfg_key, 0)
    if amount <= 0:
        return
    try:
        from backend.services.lumi_engine import earn_lumi
        earn_lumi(db, source=earn_source, amount=amount)
    except Exception as exc:
        logger.warning("lumi award failed for action=%s source=%s: %s", action, earn_source, exc)


XP_RULES_DEFAULT: dict[str, int] = {
    "word_correct":           1,
    "stage_complete":         5,
    "final_test_pass":       20,
    "unit_test_pass":         5,
    "daily_words_complete":  10,
    "weekly_test_pass":      10,
    "mywords_weekly_test_pass": 10,
    "review_complete":        5,
    "journal_complete":      15,
    "must_do_bonus":         10,
    "all_complete_bonus":    25,
    "streak_7_bonus":        30,
    "streak_30_bonus":       200,
    "streak_maintain":       10,
    "math_lesson_complete":     15,
    "math_unit_test_pass":      15,
    "math_spaced_review":        3,
    "math_problem_mastered":     5,
    "math_fluency_complete":    10,
    "math_fluency_best":         2,
    "math_placement_complete":  20,
    "math_daily_complete":       5,
    "math_daily_perfect":        3,
    "math_kangaroo_complete":  5,
    "math_kangaroo_80":        5,
    "math_kangaroo_perfect":  10,
    # CKLA — dedup by action+date+detail(lesson_id or domain_num or grade)
    "ckla_lesson_complete":   15,  # lesson fully complete (Read+Words+WordWork)
    "ckla_domain_test_pass":  30,  # domain test passed
    "ckla_grade_final_pass": 100,  # grade final test passed
    "ckla_daily_goal":        10,  # daily lesson goal reached
}
# Back-compat alias: callers that imported XP_RULES still see defaults.
XP_RULES = XP_RULES_DEFAULT

# Arcade daily cap default. Override via app_config key `arcade_daily_cap`.
ARCADE_DAILY_CAP_DEFAULT = 10
ARCADE_DAILY_CAP = ARCADE_DAILY_CAP_DEFAULT  # back-compat alias


# @tag XP @tag SETTINGS
def get_xp_rules(db: Session) -> dict[str, int]:
    """Merge XP_RULES_DEFAULT with app_config overrides keyed `xp_rule_<action>`.

    Result is cached for _XP_RULES_TTL seconds to avoid a DB round-trip on
    every XP award. Call invalidate_xp_cache() after the parent saves new rules.
    """
    global _xp_rules_cache, _xp_rules_at
    if _xp_rules_cache is not None and time.monotonic() - _xp_rules_at < _XP_RULES_TTL:
        return _xp_rules_cache
    rules = dict(XP_RULES_DEFAULT)
    rows = (
        db.query(AppConfig)
        .filter(AppConfig.key.like("xp_rule_%"))
        .all()
    )
    for r in rows:
        action = r.key[len("xp_rule_"):]
        if action in rules:
            try:
                rules[action] = int(r.value)
            except (TypeError, ValueError):
                pass
    _xp_rules_cache = rules
    _xp_rules_at    = time.monotonic()
    return rules


# @tag XP @tag ARCADE @tag SETTINGS
def get_arcade_daily_cap(db: Session) -> int:
    """Read arcade daily cap from app_config, falling back to default.

    Cached for _ARCADE_CAP_TTL seconds; invalidated by invalidate_xp_cache().
    """
    global _arcade_cap_cache, _arcade_cap_at
    if _arcade_cap_cache is not None and time.monotonic() - _arcade_cap_at < _ARCADE_CAP_TTL:
        return _arcade_cap_cache
    row = db.query(AppConfig).filter(AppConfig.key == "arcade_daily_cap").first()
    cap = ARCADE_DAILY_CAP_DEFAULT
    if row:
        try:
            cap = max(0, int(row.value))
        except (TypeError, ValueError):
            pass
    _arcade_cap_cache = cap
    _arcade_cap_at    = time.monotonic()
    return cap


_SOURCE_MAP: dict[str, str] = {
    "ckla_lesson_complete": "ckla",
    "ckla_domain_test_pass": "ckla",
    "ckla_grade_final_pass": "ckla",
    "ckla_daily_goal": "ckla",
    "math_lesson_complete": "math",
    "math_unit_test_pass": "math",
    "math_spaced_review": "math",
    "math_problem_mastered": "math",
    "math_fluency_complete": "math",
    "math_fluency_best": "math",
    "math_placement_complete": "math",
    "math_daily_complete": "math",
    "math_daily_perfect": "math",
    "math_kangaroo_complete": "math",
    "math_kangaroo_80": "math",
    "math_kangaroo_perfect": "math",
    "journal_complete": "diary",
    "review_complete": "review",
    "daily_words_complete": "english",
    "stage_complete": "english",
    "final_test_pass": "english",
    "unit_test_pass": "english",
    "word_correct": "english",
}


def _infer_source(action: str) -> str:
    return _SOURCE_MAP.get(action, "")


# Dedup policy for award_xp():
#   _NO_DEDUP    — no dedup at all (action allowed multiple times per day, e.g. individual words)
#   _DETAIL_DEDUP — dedup by (action + date + detail) so the same item can't be awarded twice
#                   but different items of the same action type can each earn once
#   all others   — dedup by (action + date) — awarded at most once per day globally
_NO_DEDUP: frozenset[str] = frozenset({"word_correct"})
_DETAIL_DEDUP: frozenset[str] = frozenset({
    "ckla_lesson_complete",   # once per lesson (detail = lesson_id)
    "ckla_domain_test_pass",  # once per domain (detail = domain_num)
    "ckla_grade_final_pass",  # once per grade (detail = grade)
    "ckla_daily_goal",        # once per goal threshold hit (detail = target count)
    "math_unit_test_pass",    # once per unit (detail = grade/unit), not per day globally
})


# @tag XP @tag AWARD
def award_xp(
    db: Session,
    action: str,
    detail: str = "",
    earned_date: Optional[str] = None,
    source: str = "",
    commit: bool = True,
) -> int:
    """Award XP for an action. Returns actual XP awarded (0 if already awarded today).

    Daily dedup: same action + same earned_date = skip.
    For word_correct, detail should be the word string (allows multiple per day).

    Args:
        db: SQLAlchemy session.
        action: Key from XP_RULES (e.g. "stage_complete").
        detail: Optional extra context (word string for word_correct).
        earned_date: ISO date string override; defaults to today.
        source: Module that triggered the award (e.g. "ckla", "math", "english").
        commit: If False, only db.add() — caller is responsible for db.commit().
                Use commit=False when award_xp is called inside a larger transaction
                so that XP and the surrounding changes are committed atomically.

    Returns:
        XP points actually inserted, or 0 if deduped / unknown action.
    """
    today = earned_date or date.today().isoformat()
    xp_amount = get_xp_rules(db).get(action, 0)
    if xp_amount == 0:
        return 0
    # Apply completed-character XP boost (ISLAND_SPEC §4.6).
    # word_correct is excluded — per-word micro-awards should not compound.
    if action not in _NO_DEDUP:
        xp_amount = _apply_boost(xp_amount, action, db)

    if action not in _NO_DEDUP:
        filters = [XPLog.action == action, XPLog.earned_date == today]
        if action in _DETAIL_DEDUP:
            filters.append(XPLog.detail == detail)
        if db.query(XPLog).filter(*filters).first():
            return 0

    log = XPLog(
        action=action,
        xp_amount=xp_amount,
        detail=detail,
        earned_date=today,
        created_at=datetime.now().isoformat(),
        source=source or _infer_source(action),
    )
    db.add(log)
    _award_lumi_for_action(db, action)
    if commit:
        db.commit()
    return xp_amount


# @tag XP
def get_total_xp(db: Session) -> int:
    """Return sum of all XP ever earned.

    Args:
        db: SQLAlchemy session.

    Returns:
        Total XP as an integer (0 if no records).
    """
    from sqlalchemy import func
    result = db.query(func.sum(XPLog.xp_amount)).scalar()
    return int(result or 0)


# @tag XP
def get_today_xp(db: Session) -> int:
    """Return sum of XP earned today.

    Args:
        db: SQLAlchemy session.

    Returns:
        Today's XP total as an integer (0 if no records).
    """
    from sqlalchemy import func
    today = date.today().isoformat()
    result = (
        db.query(func.sum(XPLog.xp_amount))
        .filter(XPLog.earned_date == today)
        .scalar()
    )
    return int(result or 0)


# @tag XP @tag SHOP
def spend_xp(db: Session, amount: int, detail: str = "") -> bool:
    """Deduct XP for a shop purchase. Returns False if insufficient balance.

    Atomicity: wrapped in `BEGIN IMMEDIATE` so two concurrent callers (e.g.
    a double-clicked Buy button during network lag) cannot both pass the
    balance check before either writes. In SQLite WAL mode, plain
    read→insert→commit lets the second request observe the pre-insert
    balance and over-spend. `BEGIN IMMEDIATE` serializes writers here.

    Args:
        db: SQLAlchemy session.
        amount: XP to deduct (positive number).
        detail: Purchase description.

    Returns:
        True if deduction succeeded, False if not enough XP.
    """
    if amount <= 0:
        return False

    from sqlalchemy import text

    # Ensure we're not already in a transaction before asking for IMMEDIATE.
    # SQLAlchemy auto-begins on first read; roll it back so we can upgrade.
    if db.in_transaction():
        db.rollback()

    db.execute(text("BEGIN IMMEDIATE"))
    try:
        current = get_total_xp(db)
        if current < amount:
            db.rollback()
            return False
        log = XPLog(
            action="shop_purchase",
            xp_amount=-amount,
            detail=detail,
            earned_date=date.today().isoformat(),
            created_at=datetime.now().isoformat(),
        )
        db.add(log)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


# @tag XP @tag ARCADE
def score_to_arcade_tier(score: int) -> int:
    """Map arcade score to XP tier (0/1/2/3)."""
    if score >= 2000:
        return 3
    if score >= 1000:
        return 2
    if score >= 500:
        return 1
    return 0


# @tag XP @tag ARCADE
def get_arcade_xp_today(db: Session) -> int:
    """Return total arcade XP earned today."""
    from sqlalchemy import func
    today = date.today().isoformat()
    result = (
        db.query(func.sum(XPLog.xp_amount))
        .filter(XPLog.action == "arcade_play", XPLog.earned_date == today)
        .scalar()
    )
    return int(result or 0)


# @tag XP @tag ARCADE
def award_arcade_xp(
    db: Session,
    score: int,
    game: str = "word_invaders",
    commit: bool = True,
) -> dict:
    """Award tier-based arcade XP, respecting ARCADE_DAILY_CAP.

    Tiers: 500+ = 1 XP, 1000+ = 2 XP, 2000+ = 3 XP. Partial awards allowed
    (e.g. if 2 XP remaining in cap and tier grants 3, award 2).

    Args:
        db: SQLAlchemy session.
        score: Round score.
        game: Game identifier (logged in detail field).
        commit: Whether to call db.commit() after inserting the XPLog row.
                Set to False when called inside a larger transaction so the
                caller can bundle XP + best-score + streak into one commit.

    Returns:
        {"tier": int, "xp_awarded": int, "daily_total": int, "daily_cap": int}
    """
    tier = score_to_arcade_tier(score)
    earned_today = get_arcade_xp_today(db)
    cap = get_arcade_daily_cap(db)
    remaining = max(0, cap - earned_today)
    to_award = min(tier, remaining)

    if to_award > 0:
        log = XPLog(
            action="arcade_play",
            xp_amount=to_award,
            detail=f"{game}:score={score}:tier={tier}",
            earned_date=date.today().isoformat(),
            created_at=datetime.now().isoformat(),
        )
        db.add(log)
        if commit:
            db.commit()

    return {
        "tier": tier,
        "xp_awarded": to_award,
        "daily_total": earned_today + to_award,
        "daily_cap": cap,
    }


# @tag XP
def get_words_known(db: Session) -> int:
    """Return count of WordReview entries with interval >= 7 (mastered words).

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of words with SM-2 interval >= 7 days.
    """
    return db.query(WordReview).filter(WordReview.interval >= 7).count()
