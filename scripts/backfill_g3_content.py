#!/usr/bin/env python3
"""
backfill_g3_content.py — Fill remaining math content gaps.

Adds educational hint + feedback to every problem still missing them.
Despite the name, accepts a grade arg (default G3) for use across grades.
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
    python3 scripts/backfill_g3_content.py                   # apply to G3
    python3 scripts/backfill_g3_content.py G4                # other grade
    python3 scripts/backfill_g3_content.py G4 --dry-run      # preview
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_DATA_ROOT = Path(__file__).resolve().parent.parent / "backend" / "data" / "math"
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
    # Properties — general "which property" before specific
    (r"which property|\bproperty\b.*(shows?|states?|explains?)|which (?:rule|property) is correct", "Identity: +0 or ×1 keeps number same. Commutative: order doesn't matter. Associative: grouping doesn't matter. Distributive: a×(b+c) = a×b + a×c."),
    (r"commutative.*property", "Commutative means changing the ORDER (a + b = b + a, or a × b = b × a)."),
    (r"associative.*property", "Associative means changing the GROUPING with parentheses — same answer."),
    (r"distributive.*property", "Distributive splits one factor: a × (b + c) = a×b + a×c."),
    (r"identity.*property", "Identity: adding 0 or multiplying by 1 keeps the number unchanged."),
    (r"if\s+\d.*=.*\b,\s*(?:what|then)", "Use the same fact — order or grouping changing keeps the answer the same (commutative/associative)."),
    # Pattern / sequences
    (r"what comes next\??\s*[\d,\s]+___|\bnext (?:number|term)\b", "Find the difference between each pair, then add it again to extend the pattern."),
    (r"(?:multiplication|addition)\s+table.*(?:row|column|diagonal|rule|pattern)", "Look across rows and down columns — each cell equals row × column (or row + column for addition)."),
    (r"a table shows|the table shows|look at the table", "Find the rule connecting the columns. Multiply the input by a constant to find the output."),
    (r"(pattern|next number|missing number|skip count|the rule)", "Find the rule by checking the difference (or factor) between consecutive numbers."),
    # Multiplication / division — relate addition first
    (r"write as multiplication|another way to show.*\+.*\+|equal addends", "Repeated addition of the same number = multiplication. Count groups × items per group."),
    (r"multiplication\s+sentence", "Multiplication means equal groups: groups × items per group."),
    (r"\bequal\s+groups\b|\bgroups of\b", "Equal groups means the same number in each group. Multiply groups × items per group."),
    (r"\barray\b", "An array has rows × columns equal to the total."),
    (r"\bskip count\b", "Add the same number each step."),
    (r"\bfact family\b|related fact", "A fact family uses × and ÷ (or + and −) with the same three numbers."),
    (r"how many times can you subtract", "Repeated subtraction is division. Total ÷ each-step = number of jumps."),
    (r"jumps of \d+|number line.*jumps", "Each jump is the divisor. Total ÷ jump size = number of jumps."),
    (r"\bdivisi\w+|÷|\bdivided\b", "Division splits a total into equal groups. Use the inverse multiplication fact."),
    (r"\bmultiply|×|\bproduct\b", "Multiplication is repeated addition. Use known facts when possible."),
    # Fractions — fraction-notation patterns BEFORE the literal-word "fraction" patterns
    (r"compare:?\s*\d+/\d+|\d+/\d+\s*[○◯<>=]|\d+/\d+\s*(?:vs\.?|or)\s*\d+/\d+|which (?:is )?(?:greater|larger|bigger|smaller|less).*\d+/\d+|who (?:used|ate|filled|drank|read|ran|finished) more.*\d+/\d+|more.*\d+/\d+.*or.*\d+/\d+", "Same denominator → bigger numerator wins. Same numerator → smaller denominator means bigger pieces."),
    (r"\d+/\d+\s*=\s*[_\?□]+/\d+|=\s*\?/\d+|fill in.*\d+/\d+|missing.*\d+/\d+", "Multiply (or divide) numerator AND denominator by the same number to find an equivalent fraction."),
    (r"compare.*fraction|fraction.*compare|[<>=].*fraction|fraction.*[<>=]", "Same denominator → compare numerators. Same numerator → smaller denominator means bigger pieces."),
    (r"equivalent\s+fraction", "Equivalent fractions: multiply (or divide) numerator and denominator by the SAME number."),
    (r"unit\s+fraction", "A unit fraction has 1 on top (1/2, 1/3, 1/4, ...)."),
    (r"how many (?:halves|thirds|fourths|quarters|fifths|sixths|eighths).*in (?:1|a|one) whole|whole number.*equal.*\d+/\d+|\d+/\d+.*equal.*whole", "n/n = 1 whole. Improper fractions (numerator > denominator) equal a whole number when numerator is a multiple of denominator."),
    (r"1/\d+\s+of\s+(?:a|the)\s+(?:group|number|set|bag|class|whole)|whole group", "If 1/n of the whole is X, then the whole is X × n. Multiply to find the total."),
    (r"cut into\s+\d+\s+equal parts|divided into\s+\d+\s+equal", "Equal parts of a whole are fractions: 2 parts = halves, 3 = thirds, 4 = fourths/quarters."),
    (r"number\s+line.*(?:fraction|\d+/\d+)|\d+/\d+.*number\s+line|where is \d+/\d+", "Divide the line from 0 to 1 into equal parts (the denominator). Count numerator ticks from 0."),
    (r"\d+/\d+|\bfraction\b", "Numerator (top) = parts taken. Denominator (bottom) = total equal parts."),
    # Perimeter / area
    (r"perimeter|how far around|distance around|fence around|border around|frame .* (?:window|board|picture)|walk around .* (?:park|garden|yard)", "Perimeter is the distance ALL the way around. Add every side. Rectangle: 2(L+W). Square: 4×side."),
    (r"sides? of \d+|sides .*\d+.*(?:m|cm|ft|in)\b.*(?:m|cm|ft|in)\b", "Add every side length to find the total distance around the shape."),
    (r"\barea\b|square (?:units|inches|feet|cm|m)", "Area = length × width (in square units). Count rows × columns."),
    # Basic arithmetic with zero / one
    (r"\bwhat is\s+\d+\s*\+\s*0\b|\bwhat is\s+0\s*\+\s*\d+|\b\+\s*0\s*=", "Adding 0 keeps the number the same (Identity Property of Addition)."),
    (r"\bwhat is\s+\d+\s*[×x*]\s*1\b|\bwhat is\s+1\s*[×x*]\s*\d+|\b[×x*]\s*1\s*=", "Multiplying by 1 keeps the number the same (Identity Property of Multiplication)."),
    (r"\bwhat is\s+\d+\s*[+\-×÷*/]\s*\d+", "Use what you know — recall the basic fact or count up/back."),
    # Data / graphs
    (r"\bbar graph|tally|picture graph|line plot\b", "Read the scale carefully — each unit on the axis represents a fixed value."),
    # Word problems — division before multiplication so "how many groups/cartons" beats "how many days"
    (r"how many (?:cartons|pages|shelves|boxes|stacks|hands|groups|bags|pieces|rows|columns|tables|teams)", "Divide the total by the size of each group to find the number of groups."),
    (r"how many (?:in (?:each|every)|per (?:group|table|box|row|shelf|page))|share .* equally|split .* equally|divided equally|each (?:gets|child|person)", "Divide the total into equal groups."),
    (r"how many (?:minutes|hours|days|weeks|months|tiles|ounces|crayons|chairs|miles|dollars|cents|points|stickers|apples|cookies)\b.*(?:in|for|after|every)", "Multiply the rate (per day/box/row) by the count to find the total."),
    (r"in (all|total)|\bsum\b|altogether|combined", "Total means add the parts."),
    (r"how many more|how much more|difference", "Compare with subtraction — bigger minus smaller."),
    (r"\beach|share|split equally|divided equally\b", "Divide the total into equal groups."),
    (r"\d+\s*(?:boxes?|bags?|packs?|sets?)\s+of\s+\d+", "Multiply: groups × items per group = total."),
    # Two-step word problems
    (r"\bthen\b.*(?:spends?|gives?|uses?|buys?)|\b(?:earns?|saves?)\b.*\b(?:spends?|buys?)\b|after .* how many", "Step 1: find the total or starting amount. Step 2: add or subtract the change."),
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


_GENERIC_HINT_MARKER = "Read the problem twice"


def process(grade: str, dry_run: bool, upgrade_generic: bool = False) -> int:
    files_changed = 0
    files_total = 0
    total_h = 0
    total_f = 0
    total_u = 0
    seq = 0  # rotating affirmation seed across all problems
    root = _DATA_ROOT / grade
    if not root.is_dir():
        print(f"  ✗ grade dir not found: {root}")
        return 1

    for f in root.rglob("*.json"):
        if any(part.startswith("_") for part in f.relative_to(root).parts):
            continue
        files_total += 1
        try:
            d = json.loads(f.read_text("utf-8"))
        except Exception as e:
            print(f"  ✗ {f.relative_to(root)}: {e}")
            continue

        added_h = 0
        added_f = 0
        upgraded_h = 0

        def fn(p, stage, idx):
            nonlocal added_h, added_f, upgraded_h, seq
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
            elif upgrade_generic and has_hints:
                first = str(p["hints"][0])
                if _GENERIC_HINT_MARKER in first:
                    new_hint = _generate_hint(p.get("question", ""))
                    if _GENERIC_HINT_MARKER not in new_hint:
                        p["hints"][0] = new_hint
                        upgraded_h += 1
            fb = p.get("feedback")
            if not (isinstance(fb, dict) and (fb.get("correct") or fb.get("incorrect"))):
                p["feedback"] = _generate_feedback(p, seq)
                added_f += 1

        _walk(d, fn)

        if added_h or added_f or upgraded_h:
            files_changed += 1
            total_h += added_h
            total_f += added_f
            total_u += upgraded_h
            tag = f"+{added_h}h +{added_f}f" + (f" ↑{upgraded_h}h" if upgraded_h else "")
            if dry_run:
                print(f"  diff {f.relative_to(root)}: {tag}")
            else:
                f.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", "utf-8")
                print(f"  ✓ {f.relative_to(root)}: {tag}")

    print()
    print(f"Files scanned: {files_total}")
    print(f"Files changed: {files_changed}{' (dry-run)' if dry_run else ''}")
    print(f"Hints added:    {total_h}")
    print(f"Hints upgraded: {total_u}")
    print(f"Feedback added: {total_f}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("grade", nargs="?", default="G3")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--upgrade-generic", action="store_true",
                    help="Replace existing generic-fallback hints with newly-matched specific ones")
    args = ap.parse_args()
    sys.exit(process(args.grade, args.dry_run, args.upgrade_generic))
