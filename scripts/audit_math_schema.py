#!/usr/bin/env python3
"""
audit_math_schema.py — Validate math content against MATH_SPEC.md schemas.

Usage:
    python3 scripts/audit_math_schema.py            # audit all grades
    python3 scripts/audit_math_schema.py G3         # one grade
    python3 scripts/audit_math_schema.py G3 --strict   # treat warnings as errors

Checks:
  • No Korean text (English-only rule)
  • Lesson schema: required keys, 6 stages present
  • Problem schema: id, type ∈ {mc,input,tf}, type-specific rules
  • mc: choices prefixed "A) ", correct_answer is single letter pointing to a valid index
  • input: correct_answer non-empty, question references unit
  • Unit test: pass_threshold, time_limit_min, count, problems[] present
  • Reports schema bucket (STD / ITEMS / SECTIONS) for each lesson

Exit codes: 0 clean, 1 errors, 2 warnings (with --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent / "backend" / "data" / "math"
HANGUL = re.compile(r"[가-힯]")
STD_STAGES = ("pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3")
LESSON_REQUIRED = {"lesson_id", "grade", "unit", "title"}
PROBLEM_REQUIRED = {"id", "type", "question", "correct_answer"}
PROBLEM_TYPES = {"mc", "input", "tf", "drag_sort"}
LEARN_CARD_TYPES = {"concept_card", "card", "concept", "instruction", "instruction_check", "example", "interactive", "summary"}
UNIT_TEST_REQUIRED = {"unit_id", "title", "grade", "unit", "pass_threshold", "time_limit_min", "count", "problems"}


# ── helpers ─────────────────────────────────────────────────────────


def _bucket(d: dict) -> str:
    """Return schema bucket label for a lesson dict."""
    keys = set(d.keys())
    if STD_STAGES[0] in keys or any(s in keys for s in STD_STAGES):
        return "STD"
    if "items" in keys and isinstance(d.get("items"), list):
        return "ITEMS"
    if "sections" in keys and isinstance(d.get("sections"), dict):
        return "SECTIONS"
    return "OTHER"


_TYPE_ALIASES = {
    "true_false": "tf", "TRUE_FALSE": "tf",
    "MC": "mc", "multiple_choice": "mc", "MULTIPLE_CHOICE": "mc", "compare": "mc",
    "INPUT": "input", "fill_in": "input", "FILL_IN": "input",
    "word_problem": "input", "open_response": "input",
    "DRAG_SORT": "drag_sort", "ordering": "drag_sort",
}


def _normalize_for_audit(p: dict) -> dict:
    """Return a shallow normalized copy applying spec-listed compatibility aliases.

    Mirrors frontend `_normalizeProblem` so the auditor doesn't flag legacy
    files that the runtime already accepts. The auditor still warns when the
    canonical form isn't used (so we can prioritize cleanup).
    """
    n = dict(p)
    if "question" not in n:
        n["question"] = n.get("stem") or n.get("prompt") or n.get("text") or ""
    if "correct_answer" not in n:
        if "answer" in n:
            n["correct_answer"] = n["answer"]
    if "choices" not in n and "options" in n:
        n["choices"] = n["options"]
    # choices dict → list (sorted by key A,B,C,D)
    raw_choices = n.get("choices")
    if isinstance(raw_choices, dict):
        n["choices"] = [raw_choices[k] for k in sorted(raw_choices.keys())]
    if "type" in n:
        n["type"] = _TYPE_ALIASES.get(n["type"], str(n["type"]).lower())
    # Structure-based type inference (mirrors frontend _normalizeProblem)
    if "type" not in n or not n["type"]:
        ans = str(n.get("correct_answer", "")).strip().lower()
        if isinstance(n.get("choices"), list) and len(n["choices"]) >= 2:
            n["type"] = "mc"
        elif ans in ("true", "false"):
            n["type"] = "tf"
        else:
            n["type"] = "input"
    elif n["type"] == "input" and isinstance(n.get("choices"), list) and len(n["choices"]) >= 2:
        n["type"] = "mc"
    return n


def _validate_problem(p: dict, prefix: str, errs: list, warns: list) -> None:
    if not isinstance(p, dict):
        errs.append(f"{prefix}: not a dict")
        return
    # Track legacy alias usage as warnings (non-blocking)
    if "stem" in p and "question" not in p:
        warns.append(f"{prefix}: uses legacy 'stem' (canonical: 'question')")
    if "answer" in p and "correct_answer" not in p:
        warns.append(f"{prefix}: uses legacy 'answer' (canonical: 'correct_answer')")
    if "options" in p and "choices" not in p:
        warns.append(f"{prefix}: uses legacy 'options' (canonical: 'choices')")
    if isinstance(p.get("choices"), dict):
        warns.append(f"{prefix}: choices is dict — canonical is list with 'A) ' prefixes")
    p = _normalize_for_audit(p)
    missing = PROBLEM_REQUIRED - p.keys()
    if missing:
        errs.append(f"{prefix}: missing required keys {sorted(missing)} (after alias normalization)")
        return
    ptype = str(p["type"]).lower()
    if ptype not in PROBLEM_TYPES:
        errs.append(f"{prefix}: type='{p['type']}' not in {sorted(PROBLEM_TYPES)}")
        return
    ans = str(p["correct_answer"]).strip()
    if ptype == "mc":
        choices = p.get("choices")
        if not (isinstance(choices, list) and len(choices) >= 2):
            errs.append(f"{prefix}: mc requires choices[] with ≥2 entries")
            return
        for c in choices:
            if not (isinstance(c, str) and len(c) >= 3 and c[0].isalpha() and c[1] in ").:" ):
                warns.append(f"{prefix}: choice missing 'A) ' or 'A.' prefix: {c!r}")
                break
        if not (len(ans) == 1 and ans.upper() in "ABCDEFGH"):
            warns.append(f"{prefix}: mc correct_answer should be single letter, got {ans!r}")
        else:
            idx = ord(ans.upper()) - 65
            if idx >= len(choices):
                errs.append(f"{prefix}: mc answer {ans!r} indexes beyond {len(choices)} choices")
    elif ptype == "input":
        if not ans:
            errs.append(f"{prefix}: input has empty correct_answer")
        # Only warn when answer is `<number> <unit>` (e.g. "12 cm", "49 sq m").
        # Categorical word answers like "even", "odd", "Yes" are valid input.
        import re as _re
        if _re.match(r"^[\d.,/]+\s+[a-zA-Z]", ans):
            warns.append(f"{prefix}: input answer has number+unit — strip unit, restate in question: {ans!r}")
    elif ptype == "tf":
        if ans.lower() not in ("true", "false"):
            errs.append(f"{prefix}: tf correct_answer must be 'true' or 'false', got {ans!r}")
    # Canonical field is `hints` (array); `hint` (singular string) is a legacy alias.
    has_hints = isinstance(p.get("hints"), list) and len(p["hints"]) > 0
    has_hint_singular = bool(p.get("hint"))
    if not has_hints and not has_hint_singular:
        warns.append(f"{prefix}: missing hints")
    elif has_hint_singular and not has_hints:
        warns.append(f"{prefix}: uses legacy 'hint' (canonical: 'hints' array)")
    if not isinstance(p.get("feedback"), dict):
        warns.append(f"{prefix}: missing feedback{{correct, incorrect}}")


def _validate_lesson(path: Path, errs: list, warns: list) -> str:
    rel = path.relative_to(ROOT)
    try:
        d = json.loads(path.read_text("utf-8"))
    except Exception as e:
        errs.append(f"{rel}: invalid JSON ({e})")
        return "INVALID"

    txt = json.dumps(d, ensure_ascii=False)
    if HANGUL.search(txt):
        n = len(HANGUL.findall(txt))
        errs.append(f"{rel}: contains {n} Hangul characters (English-only rule)")

    bucket = _bucket(d)

    missing = LESSON_REQUIRED - d.keys()
    if missing:
        warns.append(f"{rel}: missing lesson meta {sorted(missing)}")

    # Validate problems where they live (learn[] uses LearnCard schema separately)
    if bucket == "STD":
        for stage in STD_STAGES:
            for i, p in enumerate(d.get(stage, []) or []):
                if stage == "learn":
                    _validate_learn_card(p, f"{rel}:learn[{i}]", warns)
                else:
                    _validate_problem(p, f"{rel}:{stage}[{i}]", errs, warns)
    elif bucket == "ITEMS":
        for i, it in enumerate(d.get("items", []) or []):
            section = it.get("section", "?")
            if section == "learn":
                _validate_learn_card(it, f"{rel}:items[{i}](learn)", warns)
            else:
                _validate_problem(it, f"{rel}:items[{i}]({section})", errs, warns)
    elif bucket == "SECTIONS":
        for stage, lst in (d.get("sections") or {}).items():
            if stage == "learn":
                for i, c in enumerate(lst or []):
                    _validate_learn_card(c, f"{rel}:sections.learn[{i}]", warns)
                continue
            for i, p in enumerate(lst or []):
                _validate_problem(p, f"{rel}:sections.{stage}[{i}]", errs, warns)

    return bucket


def _validate_learn_card(c: dict, prefix: str, warns: list) -> None:
    """Learn cards are not problems — looser validation, warnings only."""
    if not isinstance(c, dict):
        warns.append(f"{prefix}: not a dict")
        return
    ctype = str(c.get("type", "")).lower()
    if ctype and ctype not in LEARN_CARD_TYPES:
        warns.append(f"{prefix}: learn card type='{ctype}' not in {sorted(LEARN_CARD_TYPES)}")
    if not c.get("title") and not c.get("content"):
        warns.append(f"{prefix}: learn card missing title and content")
    if ctype not in ("concept_card", "concept") and ctype:
        warns.append(f"{prefix}: canonical learn card type is 'concept_card' (got '{ctype}')")


def _validate_unit_test(path: Path, errs: list, warns: list) -> None:
    rel = path.relative_to(ROOT)
    try:
        d = json.loads(path.read_text("utf-8"))
    except Exception as e:
        errs.append(f"{rel}: invalid JSON ({e})")
        return

    txt = json.dumps(d, ensure_ascii=False)
    if HANGUL.search(txt):
        n = len(HANGUL.findall(txt))
        errs.append(f"{rel}: contains {n} Hangul characters")

    missing = UNIT_TEST_REQUIRED - d.keys()
    if missing:
        errs.append(f"{rel}: missing required keys {sorted(missing)}")
        return

    if d.get("pass_threshold") != 0.8:
        warns.append(f"{rel}: pass_threshold={d.get('pass_threshold')} (standard 0.8)")
    if d.get("time_limit_min") != 30:
        warns.append(f"{rel}: time_limit_min={d.get('time_limit_min')} (standard 30)")
    problems = d.get("problems") or []
    if len(problems) < 15:
        errs.append(f"{rel}: only {len(problems)} problems (minimum 15)")
    elif len(problems) < 20:
        warns.append(f"{rel}: only {len(problems)} problems (G3 typical 20, G4 typical 15)")
    if d.get("count") != len(problems):
        warns.append(f"{rel}: count={d.get('count')} but problems[]={len(problems)}")
    for i, p in enumerate(problems):
        _validate_problem(p, f"{rel}:problems[{i}]", errs, warns)
        if not p.get("lesson_ref"):
            warns.append(f"{rel}:problems[{i}]: missing lesson_ref (drives weak-lesson detection)")


# ── main ────────────────────────────────────────────────────────────


def run(grades: Iterable[str], strict: bool) -> int:
    errs: list[str] = []
    warns: list[str] = []
    bucket_count = {"STD": 0, "ITEMS": 0, "SECTIONS": 0, "OTHER": 0, "INVALID": 0}
    grade_files = {}

    for grade in grades:
        groot = ROOT / grade
        if not groot.is_dir():
            errs.append(f"{grade}: directory not found at {groot}")
            continue
        # Skip deprecated/private subfolders (e.g. `_deprecated/`)
        files = [
            f for f in groot.rglob("*.json")
            if not any(part.startswith("_") for part in f.relative_to(groot).parts)
        ]
        grade_files[grade] = len(files)
        for f in files:
            if f.name == "unit_test.json":
                _validate_unit_test(f, errs, warns)
            else:
                bucket = _validate_lesson(f, errs, warns)
                bucket_count[bucket] = bucket_count.get(bucket, 0) + 1

    # Report
    print(f"Audited grades: {', '.join(grades)}")
    for g, n in grade_files.items():
        print(f"  {g}: {n} JSON files")
    print(f"Lesson buckets: {bucket_count}")
    print(f"Errors: {len(errs)}")
    print(f"Warnings: {len(warns)}")

    # Category summary — substring match on the whole warning line
    from collections import Counter
    cats: Counter = Counter()
    for w in warns:
        if "uses legacy 'stem'" in w or "uses legacy 'answer'" in w or "uses legacy 'options'" in w:
            cats["legacy alias (stem/answer/options)"] += 1
        elif "uses legacy 'hint'" in w:
            cats["legacy 'hint' singular"] += 1
        elif "missing hints" in w:
            cats["missing hints"] += 1
        elif "missing feedback" in w:
            cats["missing feedback"] += 1
        elif "choice missing 'A)" in w:
            cats["choice missing letter prefix"] += 1
        elif "choices is dict" in w:
            cats["choices is dict"] += 1
        elif "mc correct_answer should be single letter" in w:
            cats["mc answer not letter"] += 1
        elif "input answer has number+unit" in w:
            cats["input answer has number+unit"] += 1
        elif "missing lesson_ref" in w:
            cats["missing lesson_ref"] += 1
        elif "learn card" in w:
            cats["learn card warning"] += 1
        elif "missing lesson meta" in w:
            cats["missing lesson meta"] += 1
        else:
            cats["other"] += 1
    if cats:
        print("\n--- WARNING CATEGORIES ---")
        for cat, n in cats.most_common():
            print(f"  {n:5d}  {cat}")
    if errs:
        print("\n--- ERRORS ---")
        for e in errs[:50]:
            print(f"  ✗ {e}")
        if len(errs) > 50:
            print(f"  ... and {len(errs) - 50} more")
    if warns and (strict or len(errs) == 0):
        print("\n--- WARNINGS ---")
        for w in warns[:50]:
            print(f"  ⚠ {w}")
        if len(warns) > 50:
            print(f"  ... and {len(warns) - 50} more")

    if errs:
        return 1
    if warns and strict:
        return 2
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("grade", nargs="*", default=["G3", "G4", "G5", "G6"])
    ap.add_argument("--strict", action="store_true", help="exit non-zero on warnings")
    args = ap.parse_args()
    sys.exit(run(args.grade, args.strict))
