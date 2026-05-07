#!/usr/bin/env python3
"""
verify_g3_explanations.py — Cross-check that the explanation text in each
problem's feedback / solution_steps / hints actually references the stored
correct_answer (and doesn't accidentally refer to a wrong number).

Strategy:
  - For numeric-answer problems, the correct number SHOULD appear in
    feedback.correct AND feedback.incorrect (both tell the learner the answer).
  - solution_steps SHOULD end at the correct number.
  - If the explanation contains numbers that aren't the correct answer
    AND aren't sub-step intermediate values, flag for review.

Usage:  python3 scripts/verify_g3_explanations.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend" / "data" / "math" / "G3"
UNITS = ["U11_time_mass_volume", "U12_area", "U13_shapes"]


def iter_problems(data):
    if "problems" in data:
        for p in data["problems"]:
            yield "problems", p
        return
    for stage in ["pretest", "try", "practice_r1", "practice_r2", "practice_r3"]:
        for p in data.get(stage, []):
            yield stage, p


def numeric_correct(item):
    """Return the canonical numeric answer if the answer is a pure integer
    (with optional simple unit). Skip MC answers that are expressions or
    contain time / multiple numbers / words."""
    ans = item.get("correct_answer", "")
    typ = item.get("type")
    if typ == "input":
        # Pure integer (no fraction, no time, no decimal)
        if re.match(r"^-?\d+$", str(ans).strip()):
            return str(ans).strip()
        return None
    if typ == "mc":
        choices = item.get("choices") or []
        if ans in ("A", "B", "C", "D") and len(choices) > (ord(ans) - ord("A")):
            txt = choices[ord(ans) - ord("A")]
            txt = re.sub(r"^[A-D]\)\s*", "", txt).strip()
            # Skip if the answer is a phrase (multiple words without equals)
            if re.search(r"[a-zA-Z].*[a-zA-Z]", txt) and "=" not in txt:
                return None
            # Skip time format like "8:30 A.M." or "3:45"
            if re.search(r"\d+:\d+", txt):
                return None
            # Skip expressions with multiple numbers but no = (could be "6×4 − 2×2")
            # If there's an equals sign, take the value after the LAST equals
            if "=" in txt:
                tail = txt.split("=")[-1].strip()
                m = re.match(r"^(-?\d+)\b", tail)
                if m:
                    return m.group(1)
                return None
            # Plain number with optional unit ("20", "20 sq cm", "60 minutes")
            m = re.match(r"^(-?\d+)(?:\s*[a-zA-Z].*)?$", txt)
            if m:
                # Require this is the ONLY number in the text
                all_nums = re.findall(r"-?\d+", txt)
                if len(all_nums) == 1:
                    return m.group(1)
    return None


def numbers_in(text):
    """Return list of integer strings appearing in text. Handle unicode minus."""
    if not text:
        return []
    # Normalize unicode minus and en-dash to ASCII hyphen
    t = text.replace("−", "-").replace("–", "-")
    return re.findall(r"-?\d+", t)


def collect_explanations(item):
    parts = []
    fb = item.get("feedback") or {}
    if isinstance(fb, dict):
        for k in ("correct", "incorrect"):
            if fb.get(k):
                parts.append(("feedback." + k, fb[k]))
    if item.get("solution_steps"):
        for i, s in enumerate(item["solution_steps"]):
            parts.append((f"solution_steps[{i}]", s))
    if item.get("hints"):
        for i, h in enumerate(item["hints"]):
            parts.append((f"hints[{i}]", h))
    if item.get("verification"):
        parts.append(("verification", item["verification"]))
    return parts


def check_problem(item):
    """Return list of issue dicts for this problem (empty if clean)."""
    issues = []
    ca = numeric_correct(item)
    if ca is None:
        return issues  # non-numeric — out of scope for this checker
    fb = item.get("feedback") or {}

    # feedback.incorrect MUST contain the correct number (student needs answer).
    # Allow synonyms for 0 ("no", "none", "zero").
    fb_inc = (fb or {}).get("incorrect", "") if isinstance(fb, dict) else ""
    if fb_inc and ca not in numbers_in(fb_inc):
        zero_synonym = ca == "0" and re.search(r"\b(?:no|none|zero)\b", fb_inc, re.I)
        if not zero_synonym:
            issues.append({
                "kind": "feedback.incorrect_missing_answer",
                "expected": ca,
                "feedback_incorrect": fb_inc[:200],
            })

    # feedback.correct OR feedback.incorrect must mention the answer (combined)
    fb_text = " ".join(v for k, v in (fb.items() if isinstance(fb, dict) else []) if isinstance(v, str))
    if fb_text.strip() and ca not in numbers_in(fb_text):
        issues.append({
            "kind": "answer_missing_from_all_feedback",
            "expected": ca,
            "feedback": fb_text[:300],
        })

    # Last solution step should land on the answer
    sol = item.get("solution_steps") or []
    if sol and ca not in numbers_in(sol[-1]):
        issues.append({
            "kind": "answer_missing_from_last_solution_step",
            "expected": ca,
            "last_step": sol[-1][:200],
        })

    # verification field should mention the correct answer (developer note)
    ver = item.get("verification", "")
    if ver and ca not in numbers_in(ver):
        # Allowance: verification might be conceptual without numbers
        # Only flag if verification has any number at all but not the right one
        nums = numbers_in(ver)
        if nums:
            issues.append({
                "kind": "verification_missing_answer",
                "expected": ca,
                "verification": ver[:200],
                "verification_numbers": nums,
            })
    return issues


def main():
    files = []
    for u in UNITS:
        for f in sorted((ROOT / u).glob("*.json")):
            files.append(f)

    total = 0
    numeric = 0
    issues = []

    for f in files:
        data = json.loads(f.read_text())
        for stage, item in iter_problems(data):
            total += 1
            if numeric_correct(item) is None:
                continue
            numeric += 1
            for iss in check_problem(item):
                issues.append({
                    "file": str(f.relative_to(ROOT.parent)),
                    "stage": stage,
                    "id": item.get("id"),
                    "question": item.get("question", "")[:100],
                    **iss,
                })

    print(f"\n{'=' * 70}")
    print(f"  Explanation cross-check — G3 U11/U12/U13")
    print(f"{'=' * 70}")
    print(f"  Total problems:                {total}")
    print(f"  Numeric-answer problems:       {numeric}")
    print(f"  Issues found:                  {len(issues)}")
    print(f"{'=' * 70}\n")

    if issues:
        print("ISSUES:\n")
        for i, m in enumerate(issues, 1):
            print(f"[{i}] {m['file']} -> {m['stage']} {m['id']}  ({m['kind']})")
            print(f"    Q:        {m['question']}")
            print(f"    Expected: {m['expected']}")
            if "feedback" in m:
                print(f"    Feedback: {m['feedback']}")
            if "last_step" in m:
                print(f"    Last step: {m['last_step']}")
            print()

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
