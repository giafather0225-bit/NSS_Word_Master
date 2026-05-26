"""
services/xp_lumi_bridge.py — Lumi / Island-boost bridge for the XP engine
Section: System
Dependencies: services/lumi_engine.py, models (AppConfig)

Internal module imported by xp_engine.py. Not intended for direct import
by routers — use xp_engine.award_xp() which calls these helpers automatically.
"""

import logging
import time
from typing import Optional

from sqlalchemy.orm import Session

from backend.models import AppConfig

logger = logging.getLogger(__name__)

# ── Lumi / boost TTL caches ──────────────────────────────────────────────────
_LUMI_RULES_TTL    = 30.0
_lumi_rules_cache: Optional[dict[str, int]] = None
_lumi_rules_at:    float = 0.0

_BOOST_TTL    = 30.0
_boost_cache: Optional[dict[str, float]] = None
_boost_at:    float = 0.0

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

_SOURCE_MAP: dict[str, str] = {
    "ckla_lesson_complete":    "ckla",
    "ckla_domain_test_pass":   "ckla",
    "ckla_grade_final_pass":   "ckla",
    "ckla_daily_goal":         "ckla",
    "math_lesson_complete":    "math",
    "math_unit_test_pass":     "math",
    "math_spaced_review":      "math",
    "math_problem_mastered":   "math",
    "math_fluency_complete":   "math",
    "math_fluency_best":       "math",
    "math_placement_complete": "math",
    "math_daily_complete":     "math",
    "math_daily_perfect":      "math",
    "math_kangaroo_complete":  "math",
    "math_kangaroo_80":        "math",
    "math_kangaroo_perfect":   "math",
    "journal_complete":        "diary",
    "review_complete":         "review",
    "daily_words_complete":    "english",
    "stage_complete":          "english",
    "final_test_pass":         "english",
    "unit_test_pass":          "english",
    "word_correct":            "english",
    "arcade_play":             "english",
}


def invalidate_lumi_cache() -> None:
    """Drop lumi_rules and boost TTL caches. Called by xp_engine.invalidate_xp_cache()."""
    global _lumi_rules_cache, _lumi_rules_at, _boost_cache, _boost_at
    _lumi_rules_cache = None
    _lumi_rules_at    = 0.0
    _boost_cache      = None
    _boost_at         = 0.0


def infer_source(action: str) -> str:
    """Map an XP action key to its subject source string (e.g. 'math', 'ckla')."""
    return _SOURCE_MAP.get(action, "")


def _get_lumi_rules(db: Session) -> dict[str, int]:
    """Return all lumi_rule_* AppConfig values, cached for _LUMI_RULES_TTL seconds."""
    global _lumi_rules_cache, _lumi_rules_at
    if _lumi_rules_cache is not None and time.monotonic() - _lumi_rules_at < _LUMI_RULES_TTL:
        return _lumi_rules_cache
    rows = db.query(AppConfig).filter(AppConfig.key.like("lumi_rule_%")).all()
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

    Keys: english, math, diary, review, total. All default to 0.0 if not set.
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


def apply_boost(xp: int, action: str, db: Session) -> int:
    """Return XP after applying completed-character Lumi boost for this action's subject.

    Boost = floor(xp × (1 + (subject_pct + total_pct) / 100)).
    """
    try:
        boosts  = _get_boost_pct(db)
        subject = infer_source(action)
        pct     = boosts.get(subject, 0.0) + boosts.get("total", 0.0)
        if pct <= 0:
            return xp
        return int(xp * (1.0 + pct / 100.0))
    except Exception as exc:
        logger.warning("apply_boost failed for action=%s: %s", action, exc)
        return xp


def award_lumi_for_action(db: Session, action: str) -> None:
    """Award Lumi alongside XP for supported study actions. Silent on any error."""
    entry = _LUMI_ACTION_MAP.get(action)
    if entry is None:
        return
    cfg_key, earn_source = entry
    try:
        rules  = _get_lumi_rules(db)
        amount = rules.get(cfg_key, _LUMI_DEFAULTS.get(cfg_key, 0))
    except Exception as exc:
        logger.warning("Failed to read lumi rules for action=%s: %s", action, exc)
        amount = _LUMI_DEFAULTS.get(cfg_key, 0)
    if amount <= 0:
        return
    try:
        from backend.services.lumi_engine import earn_lumi
        earn_lumi(db, source=earn_source, amount=amount)
    except Exception as exc:
        logger.warning("lumi award failed for action=%s source=%s: %s", action, earn_source, exc)
