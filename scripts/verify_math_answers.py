#!/usr/bin/env python3
"""
verify_math_answers.py — Programmatically verify correct_answer values in math content.

For arithmetic questions where the math is unambiguous, compute the expected
answer from the question text and flag mismatches with the stored correct_answer.

Patterns recognized:
  • "X + Y = ?"               (addition)
  • "X - Y = ?"               (subtraction)
  • "X × Y = ?" / "X * Y"     (multiplication)
  • "X ÷ Y = ?" / "X / Y"     (division — integer)
  • "X + Y + Z = ?"           (3-term addition)
  • Rectangle perimeter: "rectangle is L long and W wide" + "perimeter"
  • Square perimeter: "square has a side of S" + "perimeter"
  • Rectangle area: "rectangle ... L by W" + "area"
  • "1/n of M" fraction-of-quantity
  • "round X to the nearest ten/hundred"

Skipped (too varied or context-dependent):
  • Word problems with named entities (handled manually if needed)
  • Geometry classification, properties, true/false reasoning
  • Multi-step problems

Usage:
    python3 scripts/verify_math_answers.py G3              # verify G3
    python3 scripts/verify_math_answers.py G3 --verbose    # show per-problem
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "backend" / "data" / "math"


def _normalize(s) -> str:
    return str(s).strip().lower().replace(",", "").replace(" ", "")


_UNIT_STRIP = re.compile(r"\s*(sq\s+\w+|cubic\s+\w+|cm|mm|km|ft|in|inches|feet|meters?|m|units?|hours?|minutes?|seconds?|days?)\b\.?", re.I)


def _strip_unit(s) -> str:
    return _UNIT_STRIP.sub("", str(s)).strip()


def _equiv(a, b) -> bool:
    """Loose numeric equivalence: 28 == '28' == '28.0' == '28 cm'."""
    a_stripped = _strip_unit(a)
    b_stripped = _strip_unit(b)
    try:
        return abs(float(a_stripped) - float(b_stripped)) < 1e-6
    except (ValueError, TypeError):
        return _normalize(a_stripped) == _normalize(b_stripped)


def _resolve_answer(prob: dict) -> str:
    """Get the actual answer text, resolving mc letter → choice text."""
    ans = str(prob.get("correct_answer", "")).strip()
    if not ans:
        return ""
    choices = prob.get("choices") or []
    if len(ans) == 1 and ans.upper() in "ABCDEFGH" and choices:
        idx = ord(ans.upper()) - 65
        if 0 <= idx < len(choices):
            return re.sub(r"^[A-Za-z][\)\.\:]\s*", "", str(choices[idx])).strip()
    return ans


# Pattern → expected-answer-fn. Each fn takes the match groups and returns the expected answer.
def _try_arithmetic(q: str):
    qn = q.replace("?", "").replace(" ", "").replace("×", "*").replace("÷", "/").replace("−", "-")
    # n-term addition (any number of terms, all `+`): "2+2+2+2+2=" or "47+86+53="
    m = re.fullmatch(r".*?((?:\d+\+)+\d+)=.*", qn)
    if m:
        terms = [int(x) for x in m.group(1).split("+")]
        return sum(terms)
    # 2-term other ops (subtraction, multiplication, division): exactly one operator
    m = re.fullmatch(r".*?\b(\d+)([\-*/])(\d+)=.*", qn)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/" and b != 0 and a % b == 0: return a // b
    return None


def _try_rectangle_perimeter(q: str):
    """Match 'rectangle ... L ... long ... W ... wide' + 'perimeter'."""
    if "perimeter" not in q.lower():
        return None
    m = re.search(r"(\d+)\s*(?:cm|m|ft|in|inches|meters?|feet|km|units?)?\s*long\s*and\s*(\d+)\s*(?:cm|m|ft|in|inches|meters?|feet|km|units?)?\s*wide", q, re.I)
    if m:
        L, W = int(m.group(1)), int(m.group(2))
        return 2 * (L + W)
    # alt: "L by W"
    m = re.search(r"is\s*(\d+)\s*(?:cm|m|ft)?\s*(?:by|×|x)\s*(\d+)\s*(?:cm|m|ft)?", q, re.I)
    if m and "perimeter" in q.lower():
        L, W = int(m.group(1)), int(m.group(2))
        return 2 * (L + W)
    return None


def _try_square_perimeter(q: str):
    if "perimeter" not in q.lower() or "square" not in q.lower():
        return None
    m = re.search(r"side\s*(?:length\s*)?(?:of\s*)?(\d+)", q, re.I)
    if m:
        return 4 * int(m.group(1))
    return None


def _try_rectangle_area(q: str):
    if "area" not in q.lower():
        return None
    m = re.search(r"(\d+)\s*(?:cm|m|ft|in)?\s*long\s*and\s*(\d+)\s*(?:cm|m|ft|in)?\s*wide", q, re.I)
    if m:
        return int(m.group(1)) * int(m.group(2))
    m = re.search(r"is\s*(\d+)\s*(?:cm|m|ft)?\s*(?:by|×|x)\s*(\d+)\s*(?:cm|m|ft)?", q, re.I)
    if m:
        return int(m.group(1)) * int(m.group(2))
    return None


def _try_round_nearest(q: str):
    qn = q.replace(",", "")
    m = re.search(r"(?:round\w*|rounded)\s+(\d+)\s+to\s+the\s+nearest\s+(ten|hundred|thousand)", qn, re.I)
    if not m:
        m = re.search(r"what\s+is\s+(\d+)\s+rounded\s+to\s+the\s+nearest\s+(ten|hundred|thousand)", qn, re.I)
    if m:
        n = int(m.group(1))
        unit = m.group(2).lower()
        base = {"ten": 10, "hundred": 100, "thousand": 1000}[unit]
        return ((n + base // 2) // base) * base
    return None


def _try_fraction_of_quantity(q: str):
    # "1/n of M" → M / n
    m = re.search(r"\b1/(\d+)\s+of\s+(\d+)\b", q, re.I)
    if m and int(m.group(1)) > 0:
        n, M = int(m.group(1)), int(m.group(2))
        if M % n == 0:
            return M // n
    return None


_VERIFIERS = [
    ("arithmetic", _try_arithmetic),
    ("rectangle_perimeter", _try_rectangle_perimeter),
    ("square_perimeter", _try_square_perimeter),
    ("rectangle_area", _try_rectangle_area),
    ("round_nearest", _try_round_nearest),
    ("fraction_of_quantity", _try_fraction_of_quantity),
]


def verify_problem(prob: dict) -> tuple[str, str, str] | None:
    """Returns (rule_name, expected, actual) on mismatch; None if verified-correct or skipped."""
    if not isinstance(prob, dict): return None
    q = prob.get("question") or ""
    actual = _resolve_answer(prob)
    if not actual: return None

    # Skip questions where stored answer is intentionally an EXPRESSION,
    # not a final computed value. Common patterns:
    #  - Distributive Property questions accept the distributed form
    #  - True/False questions answer "true"/"false", not the computation
    #  - Property classification ("Commutative", "Associative", "Identity")
    #  - Word "what does this equal" with explanatory choices
    q_lower = q.lower()
    if any(kw in q_lower for kw in (
        "distributive", "true or false", "associative property",
        "commutative property", "identity property",
        "which property", "this equals:", "this equals?",
        "fill in the blank", "fill the blank", "fill in:",
        "estimate", "compatible numbers", "round",
        "which two properties", "explain",
        "which bar model", "which picture", "which model", "which shape",
        "which has the", "which has greater", "which has greatest",
        "which has the least", "which has smallest",
        "write the product",  # "X+X+X=? (Write the product)" expects multiplication form
    )):
        return None
    # Skip questions with fill-in blanks (multi-step where stored answer fills a slot, not final)
    if "___" in q or "□" in q or "?" in q.split("=")[-1]:
        # Multiple equals signs = multi-step intermediate; allow only if exactly one '=' before '?'
        if q.count("=") >= 2:
            return None
    actual_lower = str(actual).lower().strip()
    if actual_lower in ("true", "false"):
        return None
    # If answer itself contains operators (e.g. "70 + 14"), skip — it's a form, not a value
    if re.search(r"\d\s*[+\-×÷*/]\s*\d", str(actual)):
        return None
    # Skip multi-part compound answers (commas mean two values, e.g. "P=20, Area=25")
    if "," in str(actual):
        return None
    # Skip questions asking for AREA when only perimeter pattern exists
    # (rectangle_perimeter rule fires too eagerly when L×W appears in an area question)
    if "area" in q_lower and ("perimeter" in q_lower or "fence" in q_lower):
        # Multi-aspect question — different rules might apply per part. Skip.
        return None

    for name, fn in _VERIFIERS:
        try: expected = fn(q)
        except Exception: continue
        if expected is not None:
            if _equiv(expected, actual):
                return ("ok", str(expected), actual)
            return ("mismatch:" + name, str(expected), actual)
    return None


def walk(d: dict, fn) -> None:
    for stage in ("pretest", "try", "practice_r1", "practice_r2", "practice_r3"):
        for i, p in enumerate(d.get(stage, []) or []):
            fn(p, stage, i)
    for i, it in enumerate(d.get("items", []) or []):
        if isinstance(it, dict):
            sec = it.get("section", "")
            if sec and sec != "learn":
                fn(it, sec, i)
    for stage, lst in (d.get("sections") or {}).items():
        if stage == "learn": continue
        for i, p in enumerate(lst or []): fn(p, stage, i)
    for i, p in enumerate(d.get("problems", []) or []):
        fn(p, "unit_test", i)


def run(grade: str, verbose: bool) -> int:
    root = ROOT / grade
    if not root.is_dir():
        print(f"Grade dir not found: {root}"); return 1
    verified = 0
    mismatches = []
    skipped = 0
    for f in root.rglob("*.json"):
        if any(part.startswith("_") for part in f.relative_to(root).parts): continue
        try: d = json.loads(f.read_text("utf-8"))
        except: continue
        rel = f.relative_to(root)
        def chk(p, stage, idx):
            nonlocal verified, skipped
            r = verify_problem(p)
            if r is None: skipped += 1; return
            tag, exp, act = r
            if tag == "ok":
                verified += 1
                if verbose: print(f"  ✓ {rel} {stage}[{idx}]: {p.get('question','')[:50]} = {act}")
            else:
                mismatches.append((rel, stage, idx, p.get("id"), p.get("question",""), exp, act, tag))
        walk(d, chk)
    print(f"\n=== {grade} verification ===")
    print(f"  Verified correct: {verified}")
    print(f"  Mismatches:       {len(mismatches)}")
    print(f"  Skipped (no rule): {skipped}")
    if mismatches:
        print(f"\n--- MISMATCHES ---")
        for rel, stage, idx, pid, q, exp, act, tag in mismatches[:30]:
            print(f"\n  [{tag}] {rel} {stage}[{idx}] ({pid})")
            print(f"    Q: {q[:100]}")
            print(f"    Stored answer: {act!r}")
            print(f"    Expected:      {exp!r}")
        if len(mismatches) > 30:
            print(f"\n  ... and {len(mismatches) - 30} more")
    return 1 if mismatches else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("grade", default="G3", nargs="?")
    ap.add_argument("--verbose", action="store_true")
    sys.exit(run(ap.parse_args().grade, ap.parse_args().verbose))
