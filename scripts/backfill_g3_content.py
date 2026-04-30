#!/usr/bin/env python3
"""
backfill_g3_content.py — Fill remaining G3 informational gaps.

Adds educational hint + feedback to every G3 problem still missing them.
The 1,153 informational warnings target stages where the UI either hides
the field (pretest hints) or uses a fallback message (practice feedback).
This script gives them substantive defaults so the schema is 100% complete.

Strategy per problem:
  • Hint generation: keyword-driven templates matched against the question
    (e.g. "round" → rounding strategy, "compare" → benchmark hint).
  • Feedback.incorrect: contextual statement of the correct answer plus
    a one-line strategy hint extracted from question keywords.
  • Feedback.correct: rotating short affirmation (Right/Yes/Correct/Great/Nice)
    plus brief recap.

Idempotent: only fills when missing. Won't overwrite existing content.

Usage:
    python3 scripts/backfill_g3_content.py             # apply
    python3 scripts/backfill_g3_content.py --dry-run   # preview
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "backend" / "data" / "math" / "G3"
STD_STAGES = ("pretest", "try", "practice_r1", "practice_r2", "practice_r3")

_AFFIRMATIONS = ["Right!", "Yes!", "Correct!", "Great!", "Nice work!", "Exactly!", "Good job!"]


def _affirmation(seed: int) -> str:
    return _AFFIRMATIONS[seed % len(_AFFIRMATIONS)]


# Keyword → hint template. First match wins. Patterns ordered specific → general.
_HINT_PATTERNS = [
    # Rounding
    (r"round.*nearest ten", "Look at the ones digit. If it's 5 or more, round up; otherwise round down."),
    (r"round.*nearest hundred", "Look at the tens digit. If it's 5 or more, round up; otherwise round down."),
    (r"\b(round|estimate)\b", "Round each number first, then do the operation."),
    # Pattern / sequences
    (r"(pattern|next number|missing number|skip count)", "Find the rule by checking the difference between consecutive numbers."),
    # Properties
    (r"commutative.*property", "Commutative means changing the ORDER (a + b = b + a, or a × b = b × a)."),
    (r"associative.*property", "Associative means changing the GROUPING with parentheses — same answer."),
    (r"distributive.*property", "Distributive splits one factor: a × (b + c) = a×b + a×c."),
    (r"identity.*property", "Identity: adding 0 or multiplying by 1 keeps the number unchanged."),
    # Multiplication / division
    (r"multiplication\s+sentence", "Multiplication means equal groups: groups × items per group."),
    (r"\bequal\s+groups\b", "Equal groups means the same number in each group."),
    (r"\barray\b", "An array has rows × columns equal to the total."),
    (r"\bskip count\b", "Add the same number each step."),
    (r"\bfact family\b", "A fact family uses × and ÷ with the same three numbers."),
    (r"\bdivisi\w+|÷|divided", "Division splits a total into equal groups. Use the inverse multiplication fact."),
    (r"\bmultiply|×|\bproduct\b", "Multiplication is repeated addition. Use known facts when possible."),
    # Fractions
    (r"compare.*fraction|fraction.*compare|[<>=].*fraction|fraction.*[<>=]", "Same denominator → compare numerators. Same numerator → smaller denominator means bigger pieces."),
    (r"equivalent\s+fraction", "Equivalent fractions: multiply (or divide) numerator and denominator by the SAME number."),
    (r"unit\s+fraction", "A unit fraction has 1 on top (1/2, 1/3, 1/4, ...)."),
    (r"number\s+line.*fraction|fraction.*number\s+line", "Each tick equals 1 over the total parts."),
    (r"\bfraction\b", "Numerator (top) = parts taken. Denominator (bottom) = total equal parts."),
    # Perimeter / area
    (r"perimeter", "Perimeter is the distance ALL the way around. Add every side."),
    (r"\barea\b", "Area is rows × columns (in square units)."),
    # Data / graphs
    (r"\bbar graph|tally|picture graph|line plot\b", "Read the scale carefully — each unit on the axis represents a fixed value."),
    # Word problems
    (r"in (all|total)|\bsum\b|altogether|combined", "Total means add the parts."),
    (r"how many more|how much more|difference", "Compare with subtraction — bigger minus smaller."),
    (r"\beach|share|split equally|divided equally\b", "Divide the total into equal groups."),
    (r"true or false|true\??\s*$|false\??\s*$", "Test the statement against what you know about the operation."),
]


def _generate_hint(question: str) -> str:
    q = (question or "").lower()
    for pattern, hint in _HINT_PATTERNS:
        if re.search(pattern, q):
            return hint
    return "Read the problem twice. Identify what's given and what's asked, then choose an operation."


def _resolve_mc_choice(prob: dict) -> str:
    """For mc, return 'B (4 + 7 = 7 + 4)' style display. For others, return raw answer."""
    ans = str(prob.get("correct_answer", "")).strip()
    if not ans:
        return ""
    choices = prob.get("choices") or []
    if len(ans) == 1 and ans.upper() in "ABCDEFGH" and choices:
        idx = ord(ans.upper()) - 65
        if 0 <= idx < len(choices):
            text = str(choices[idx])
            # Strip "A) " / "A. " prefix
            cleaned = re.sub(r"^[A-Za-z][\)\.\:]\s*", "", text).strip()
            return f"{ans} ({cleaned})" if cleaned else ans
    return ans


def _generate_feedback(prob: dict, idx: int) -> dict:
    ans_display = _resolve_mc_choice(prob).rstrip(".")
    affirmation = _affirmation(idx)
    hint_text = _generate_hint(prob.get("question", "")).rstrip(".")
    incorrect = f"The answer is {ans_display}. {hint_text}."
    return {
        "correct": f"{affirmation} The answer is {ans_display}.",
        "incorrect": incorrect,
    }


def _walk(d: dict, fn) -> None:
    """Walk problem-shaped dicts in lesson/unit_test files."""
    for stage in STD_STAGES:
        for i, p in enumerate(d.get(stage, []) or []):
            if stage != "learn":
                fn(p, stage, i)
    for i, it in enumerate(d.get("items", []) or []):
        if isinstance(it, dict):
            sec = it.get("section", "")
            if sec and sec != "learn":
                fn(it, sec, i)
    sections = d.get("sections")
    if isinstance(sections, dict):
        for stage, lst in sections.items():
            if stage == "learn":
                continue
            for i, p in enumerate(lst or []):
                fn(p, stage, i)
    # Unit test
    for i, p in enumerate(d.get("problems", []) or []):
        fn(p, "unit_test", i)


def process(dry_run: bool) -> int:
    files_changed = 0
    files_total = 0
    total_h = 0
    total_f = 0
    seq = 0  # rotating affirmation seed across all problems

    for f in ROOT.rglob("*.json"):
        if any(part.startswith("_") for part in f.relative_to(ROOT).parts):
            continue
        files_total += 1
        try:
            d = json.loads(f.read_text("utf-8"))
        except Exception as e:
            print(f"  ✗ {f.relative_to(ROOT)}: {e}")
            continue

        added_h = 0
        added_f = 0

        def fn(p, stage, idx):
            nonlocal added_h, added_f, seq
            if not isinstance(p, dict):
                return
            if "question" not in p or "correct_answer" not in p:
                return
            seq += 1
            has_hints = isinstance(p.get("hints"), list) and len(p["hints"]) > 0
            has_hint_singular = bool(p.get("hint"))
            if not has_hints and not has_hint_singular:
                p["hints"] = [_generate_hint(p.get("question", ""))]
                added_h += 1
            fb = p.get("feedback")
            if not (isinstance(fb, dict) and (fb.get("correct") or fb.get("incorrect"))):
                p["feedback"] = _generate_feedback(p, seq)
                added_f += 1

        _walk(d, fn)

        if added_h or added_f:
            files_changed += 1
            total_h += added_h
            total_f += added_f
            if dry_run:
                print(f"  diff {f.relative_to(ROOT)}: +{added_h}h +{added_f}f")
            else:
                f.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", "utf-8")
                print(f"  ✓ {f.relative_to(ROOT)}: +{added_h}h +{added_f}f")

    print()
    print(f"Files scanned: {files_total}")
    print(f"Files changed: {files_changed}{' (dry-run)' if dry_run else ''}")
    print(f"Hints added:    {total_h}")
    print(f"Feedback added: {total_f}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    sys.exit(process(ap.parse_args().dry_run))
