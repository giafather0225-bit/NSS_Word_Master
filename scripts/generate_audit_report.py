#!/usr/bin/env python3
"""
G3 Math Lesson 7-Stage Audit Report Generator
Usage: python3 scripts/generate_audit_report.py G3 U1 L1
Output: per-stage pass/fail details + suggested next actions
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Repository root
REPO_ROOT = Path(__file__).parent.parent
G3_ROOT = REPO_ROOT / "backend" / "data" / "math" / "G3"
MISCONCEPTION_DIR = G3_ROOT / "misconceptions"

# ─────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────

def load_lesson(grade: str, unit_num: str, lesson_num: str) -> tuple[dict, Path]:
    """Load the JSON file. Returns (lesson_data, file_path)."""
    unit_dirs = [d for d in G3_ROOT.iterdir() if d.is_dir() and d.name.startswith(f"U{unit_num}_")]
    if not unit_dirs:
        raise FileNotFoundError(f"Unit U{unit_num} folder not found: {G3_ROOT}")
    unit_dir = unit_dirs[0]

    lesson_files = list(unit_dir.glob(f"L{lesson_num}_*.json"))
    if not lesson_files:
        raise FileNotFoundError(f"Lesson L{lesson_num} JSON not found: {unit_dir}")
    lesson_path = lesson_files[0]

    with open(lesson_path, encoding="utf-8") as f:
        return json.load(f), lesson_path


def load_misconception_pool(ccss_code: str) -> list[dict]:
    """Load misconceptions/[CCSS_CODE].json."""
    pool_path = MISCONCEPTION_DIR / f"{ccss_code}.json"
    if not pool_path.exists():
        return []
    with open(pool_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("misconceptions", [])


def all_items(lesson: dict) -> list[dict]:
    """Collect all items from pretest + learn + try + practice_r1/r2/r3."""
    items = []
    # JSON key is "try" (not try_problems)
    for section in ("pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"):
        items.extend(lesson.get(section, []))
    return items


# ─────────────────────────────────────────────
# Stage 1 — Standards Alignment
# ─────────────────────────────────────────────

def check_stage1(lesson: dict) -> dict:
    """Check CCSS code validity and presence of vertical_alignment fields."""
    issues = []

    # lesson-level CCSS
    lesson_ccss = lesson.get("ccss", [])
    if not lesson_ccss:
        issues.append("lesson.ccss field missing")

    # lesson-level vertical_alignment
    va = lesson.get("vertical_alignment")
    if not va:
        issues.append("lesson.vertical_alignment field missing")
    else:
        if not va.get("prerequisite"):
            issues.append("vertical_alignment.prerequisite missing")
        if not va.get("successor"):
            issues.append("vertical_alignment.successor missing")

    # tier field
    if not lesson.get("tier"):
        issues.append("lesson.tier field missing (A/B/C required)")

    # essential_question
    if not lesson.get("essential_question"):
        issues.append("lesson.essential_question missing")

    # ccss tag on each item
    item_missing_ccss = []
    for item in all_items(lesson):
        item_id = item.get("id", "?")
        if not item.get("ccss"):
            item_missing_ccss.append(item_id)
    if item_missing_ccss:
        issues.append(f"items missing ccss: {item_missing_ccss[:5]}{'...' if len(item_missing_ccss) > 5 else ''}")

    passed = len(issues) == 0
    return {"stage": 1, "name": "Standards Alignment", "passed": passed, "issues": issues}


# ─────────────────────────────────────────────
# Stage 2 — Triple-Source Verification
# ─────────────────────────────────────────────

def check_stage2(lesson: dict) -> dict:
    """Whether each item fills concept_source, procedure_source, assessment_source."""
    issues = []
    missing_sources: dict[str, list[str]] = {"concept": [], "procedure": [], "assessment": []}

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        v = item.get("verification", {})
        if isinstance(v, str):
            # old format (string) — not yet upgraded
            missing_sources["concept"].append(item_id)
            missing_sources["procedure"].append(item_id)
            missing_sources["assessment"].append(item_id)
            continue

        if not v.get("concept_source", {}).get("url"):
            missing_sources["concept"].append(item_id)
        if not v.get("procedure_source", {}).get("url"):
            missing_sources["procedure"].append(item_id)
        # assessment_source is optional but we still check its presence
        # (S2 passes without it — concept+procedure is enough)

    # Two-or-more sources met: pass if both concept + procedure exist
    for src_type, ids in missing_sources.items():
        if src_type == "assessment":
            continue  # assessment is a warning only
        if ids:
            short = ids[:5]
            suffix = "..." if len(ids) > 5 else ""
            issues.append(f"{src_type}_source missing ({len(ids)}): {short}{suffix}")

    # assessment_source missing is only a warning
    warnings = []
    if missing_sources["assessment"]:
        warnings.append(f"assessment_source missing ({len(missing_sources['assessment'])}) — recommended")

    passed = len(issues) == 0
    return {"stage": 2, "name": "Triple-Source Verification", "passed": passed,
            "issues": issues, "warnings": warnings}


# ─────────────────────────────────────────────
# Stage 3 — Mathematical Correctness
# ─────────────────────────────────────────────

def check_stage3(lesson: dict) -> dict:
    """Verify answers with sympy. Auto-checks only basic-arithmetic MC items."""
    issues = []
    skipped = []

    try:
        import sympy
    except ImportError:
        return {"stage": 3, "name": "Mathematical Correctness",
                "passed": False, "issues": ["sympy not installed — pip install sympy"],
                "skipped": []}

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        q = item.get("question", "")
        correct = item.get("correct_answer", item.get("answer", ""))
        choices = item.get("choices", [])

        # Auto-check only "X op Y (op Z ...) = ?" format (skip estimation/compatible-number items)
        import re
        if re.search(r'estim|compatible', q, re.IGNORECASE):
            skipped.append(item_id)
            continue

        # Skip bar-model-selection / concept items: an expression inside quotes is descriptive, not auto-checkable
        # e.g. "Which bar model shows '348 + 156 = ?'?" → skip
        if re.search(r"['\"][\d\s\+\-\×\*\/x]+(?:\s*=\s*\?)?\s*['\"]", q):
            skipped.append(item_id)
            continue

        # Multi-operand add/subtract: extract the whole "a + b + c (+ d) = ?"
        ma = re.search(r'([\d]+(?:\s*[\+\-\×\*\/x]\s*[\d]+)+)\s*=\s*\?', q)
        if not ma:
            skipped.append(item_id)
            continue
        expr_str = ma.group(1)
        # convert × → *
        expr_str = re.sub(r'[×x]', '*', expr_str)

        try:
            expected = int(sympy.sympify(expr_str))
        except Exception:
            skipped.append(item_id)
            continue

        # MC: correct_answer is a label like "B" — extract the actual value from choices
        # choices supports both a list and a {"A": ..., "B": ...} dict
        actual_val = None
        if choices and len(correct) == 1 and correct.upper() in "ABCD":
            key = correct.upper()
            if isinstance(choices, dict):
                choice_text = choices.get(key, "")
            else:
                idx = ord(key) - ord("A")
                choice_text = choices[idx] if idx < len(choices) else ""
            nums = re.findall(r'\d+', choice_text)
            if nums:
                actual_val = int(nums[-1])
        elif correct.lstrip("-").isdigit():
            actual_val = int(correct)

        if actual_val is not None and actual_val != expected:
            issues.append(f"{item_id}: expected={expected}, JSON answer={actual_val} (question: '{q}')")

    passed = len(issues) == 0
    return {"stage": 3, "name": "Mathematical Correctness", "passed": passed,
            "issues": issues, "skipped": skipped}


# ─────────────────────────────────────────────
# Stage 4 — Solution-Explanation Consistency
# ─────────────────────────────────────────────

def check_stage4(lesson: dict) -> dict:
    """Basic pattern check that hints and feedback share a solution path consistent with the answer."""
    issues = []

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        correct = str(item.get("correct_answer", item.get("answer", "")))
        hints = item.get("hints", [])
        feedback_correct = item.get("feedback_correct", "")
        feedback_wrong = item.get("feedback_wrong", "")

        # has hints but no feedback_correct
        if hints and not feedback_correct:
            issues.append(f"{item_id}: has hints but no feedback_correct")

        # feedback_wrong never mentions the correct answer (simple text-contains check)
        # — not a full AI check, just a basic pattern
        if feedback_wrong and len(feedback_wrong) < 10:
            issues.append(f"{item_id}: feedback_wrong too short ('{feedback_wrong}')")

        # when solution_steps exist, check at least 1 common keyword with hints (optional)
        # Phase 1 only flags for manual review
        solution_steps = item.get("solution_steps", [])
        if hints and solution_steps:
            pass  # TODO Phase 2: compute a consistency score via AI pattern matching

    passed = len(issues) == 0
    return {"stage": 4, "name": "Solution-Explanation Consistency",
            "passed": passed, "issues": issues,
            "note": "AI pattern matching will be enabled in Phase 2. For now, only structural completeness is checked."}


# ─────────────────────────────────────────────
# Stage 5 — Pedagogical Validity (7 sub-items)
# ─────────────────────────────────────────────

def check_stage5(lesson: dict) -> dict:
    """Check the 7 pedagogy criteria."""
    sub_results = {}
    issues = []
    warnings = []

    learn_cards = lesson.get("learn", [])
    try_items = lesson.get("try", [])  # JSON key is "try"
    pretest = lesson.get("pretest", [])
    r2 = lesson.get("practice_r2", [])

    # 1. CPA order: do the LEARN cards have all of concrete, pictorial, abstract
    cpa_stages = [c.get("cpa_stage") or c.get("cpa_phase") for c in learn_cards]
    has_concrete = "concrete" in cpa_stages
    has_pictorial = "pictorial" in cpa_stages
    has_abstract = "abstract" in cpa_stages
    cpa_ok = has_concrete and has_pictorial and has_abstract
    sub_results["cpa_order"] = cpa_ok
    if not cpa_ok:
        missing = [s for s, present in [("concrete", has_concrete), ("pictorial", has_pictorial), ("abstract", has_abstract)] if not present]
        issues.append(f"CPA order incomplete — missing stages: {missing}")

    # 2. Bloom distribution: pretest difficulty increases 1→3
    if pretest:
        diffs = [item.get("difficulty", 0) for item in pretest]
        bloom_ok = len(diffs) >= 3 and diffs[0] <= diffs[-1]
        sub_results["bloom_distribution"] = bloom_ok
        if not bloom_ok:
            issues.append(f"Pretest Bloom level not increasing: {diffs}")
    else:
        sub_results["bloom_distribution"] = False
        issues.append("no pretest (cannot check Bloom distribution)")

    # 3. Worked Example fade: TRY card hint_level decreases (full→weak→independent)
    if try_items and len(try_items) >= 3:
        hint_levels = [t.get("hint_level", t.get("scaffold_level", None)) for t in try_items]
        valid_levels = [h for h in hint_levels if h is not None]
        if valid_levels:
            fade_ok = valid_levels == sorted(valid_levels, reverse=True)
            if not fade_ok:
                issues.append(f"TRY hint_level not in decreasing order: {valid_levels}")
        else:
            # no hint_level field at all → check by structure (refine later)
            fade_ok = True  # pass if field absent (warning only)
            warnings.append("TRY items have no hint_level field — Worked Example fade needs manual check [REVIEW NEEDED]")
        sub_results["worked_example_fade"] = fade_ok
    else:
        sub_results["worked_example_fade"] = False
        issues.append(f"too few TRY items ({len(try_items)}, at least 3 required)")

    # 4. Math Talk: ≥1 LEARN card with type="explain" or an explain keyword
    explain_cards = [c for c in learn_cards if c.get("type") == "explain" or "explain" in str(c.get("interaction", "")).lower()]
    math_talk_ok = len(explain_cards) >= 1
    sub_results["math_talk"] = math_talk_ok
    if not math_talk_ok:
        issues.append("no Math Talk (type='explain') LEARN card")

    # 5. Interleaving: any review_from item in the last 25% of R2
    review_from = lesson.get("review_from_units", [])
    if r2:
        cutoff = max(1, len(r2) * 3 // 4)
        tail = r2[cutoff:]
        tail_has_review = any(item.get("review_from") or item.get("from_unit") for item in tail)
        interleave_ok = tail_has_review if review_from else True  # pass if no review_from specified
        sub_results["interleaving"] = interleave_ok
        if review_from and not tail_has_review:
            issues.append(f"no interleave item in last 25% of R2 (review_from_units={review_from})")
    else:
        sub_results["interleaving"] = False
        issues.append("no practice_r2 (cannot check interleave)")

    # 6. Lesson Summary card: the last LEARN card is type="summary"
    if learn_cards:
        last_card = learn_cards[-1]
        summary_ok = last_card.get("type") == "summary"
        sub_results["lesson_summary"] = summary_ok
        if not summary_ok:
            issues.append(f"last LEARN card type!=summary (current: '{last_card.get('type')}')")
    else:
        sub_results["lesson_summary"] = False
        issues.append("no LEARN cards")

    # 7. Unit messages: essential_question + unit_intro_message + unit_close_message
    eq_ok = bool(lesson.get("essential_question"))
    ui_ok = bool(lesson.get("unit_intro_message"))
    uc_ok = bool(lesson.get("unit_close_message"))
    messages_ok = eq_ok and ui_ok and uc_ok
    sub_results["unit_messages"] = messages_ok
    if not eq_ok:
        issues.append("no essential_question")
    if not ui_ok:
        issues.append("no unit_intro_message")
    if not uc_ok:
        issues.append("no unit_close_message")

    passed = len(issues) == 0
    return {"stage": 5, "name": "Pedagogical Validity",
            "passed": passed, "issues": issues, "warnings": warnings, "sub_results": sub_results}


# ─────────────────────────────────────────────
# Stage 6 — Misconception Validity
# ─────────────────────────────────────────────

def check_stage6(lesson: dict) -> dict:
    """Check that every expected_errors entry has a misconception_id + citation."""
    issues = []

    # Load the misconception pool by the lesson's CCSS codes
    lesson_ccss = lesson.get("ccss", [])
    pool_ids: set[str] = set()
    for ccss in lesson_ccss:
        pool = load_misconception_pool(ccss)
        for m in pool:
            pool_ids.add(m["misconception_id"])

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        expected_errors = item.get("expected_errors", {})

        # expected_errors is a dict (old format) or a list (new format)
        if isinstance(expected_errors, dict):
            error_list = list(expected_errors.values())
        elif isinstance(expected_errors, list):
            error_list = expected_errors
        else:
            continue

        for err in error_list:
            if not isinstance(err, dict):
                continue
            # pure careless errors don't need a misconception_id
            if err.get("error_type") == "careless":
                continue
            mid = err.get("misconception_id")
            citation = err.get("citation")
            if not mid:
                # old format (only error_type/note) — needs upgrade
                if "error_type" in err:
                    issues.append(f"{item_id}: old-format expected_error — needs misconception_id + citation")
                else:
                    issues.append(f"{item_id}: expected_error has no misconception_id")
            elif pool_ids and mid not in pool_ids:
                issues.append(f"{item_id}: misconception_id '{mid}' not in pool")
            if mid and not citation:
                issues.append(f"{item_id}: expected_error has no citation (mid={mid})")

    passed = len(issues) == 0
    return {"stage": 6, "name": "Misconception Validity", "passed": passed, "issues": issues,
            "pool_size": len(pool_ids)}


# ─────────────────────────────────────────────
# Stage 7 — Learner Validation (manual)
# ─────────────────────────────────────────────

def check_stage7(lesson: dict) -> dict:
    """Pending until the pilot. Only checks stage_status.s7."""
    s7_values = []
    for item in all_items(lesson):
        v = item.get("verification", {})
        if isinstance(v, dict):
            ss = v.get("stage_status", {})
            s7_values.append(ss.get("s7"))

    all_pending = all(v is None for v in s7_values)
    all_passed = all(v is True for v in s7_values) if s7_values else False

    return {
        "stage": 7,
        "name": "Learner Validation",
        "passed": all_passed,
        "pending": all_pending,
        "note": "Measured after the 2026-06-13~19 pilot or First Pass completion. Pending is normal for now."
    }


# ─────────────────────────────────────────────
# Report output
# ─────────────────────────────────────────────

def print_report(lesson: dict, lesson_path: Path, results: list[dict]) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    tier = lesson.get("tier", "?")
    title = lesson.get("title", lesson.get("lesson_id", "?"))

    print("\n" + "=" * 60)
    print(f"  G3 Math 7-Stage Audit Report")
    print(f"  Lesson : {lesson_path.parent.name} / {lesson_path.name}")
    print(f"  Title  : {title}   [Tier {tier}]")
    print(f"  Date   : {now}")
    print("=" * 60)

    overall_pass = True
    for r in results:
        stage_num = r["stage"]
        name = r["name"]
        passed = r.get("passed", False)
        pending = r.get("pending", False)

        if pending:
            icon = "⏳"
            status = "PENDING"
        elif passed:
            icon = "✅"
            status = "PASS"
        else:
            icon = "❌"
            status = "FAIL"
            if stage_num != 7:
                overall_pass = False

        print(f"\nStage {stage_num} — {name}")
        print(f"  {icon} {status}")

        for issue in r.get("issues", []):
            print(f"    ⚠  {issue}")
        for warn in r.get("warnings", []):
            print(f"    💡 {warn}")
        if r.get("note"):
            print(f"    ℹ  {r['note']}")

        # Stage 5 sub-results
        if stage_num == 5 and "sub_results" in r:
            print("  Sub-items:")
            labels = {
                "cpa_order": "CPA order",
                "bloom_distribution": "Bloom distribution",
                "worked_example_fade": "Worked Example fade",
                "math_talk": "Math Talk",
                "interleaving": "Interleaving",
                "lesson_summary": "Lesson Summary card",
                "unit_messages": "Unit messages",
            }
            for key, label in labels.items():
                ok = r["sub_results"].get(key, False)
                print(f"    {'✅' if ok else '❌'} {label}")

        # Stage 3 skipped
        if stage_num == 3 and r.get("skipped"):
            print(f"    ℹ  {len(r['skipped'])} items not auto-checkable (no expression or complex format)")

        # Stage 6 pool size
        if stage_num == 6:
            print(f"    ℹ  Misconception pool size: {r.get('pool_size', 0)}")

    print("\n" + "=" * 60)
    print(f"  Final result: {'✅ PASS (Stage 7 pending)' if overall_pass else '❌ FAIL — actions needed below'}")
    print("=" * 60)

    # Suggested next actions
    failed_stages = [r["stage"] for r in results if not r.get("passed") and not r.get("pending") and r["stage"] != 7]
    if failed_stages:
        print("\nNext actions:")
        action_map = {
            1: "add tier, vertical_alignment, essential_question, and per-item ccss fields to the lesson JSON",
            2: "add concept_source + procedure_source URLs to each item's verification object",
            3: "fix answer mismatches (per sympy verification)",
            4: "review hints/feedback: confirm they use the same solution path as the answer",
            5: "add LEARN card CPA order, Math Talk, Summary card, unit_intro/close_message",
            6: "add misconception_id + citation to expected_errors (see the misconceptions/ pool)",
        }
        for s in failed_stages:
            print(f"  Stage {s}: {action_map.get(s, 'manual check needed')}")

    if overall_pass:
        print("\nCommit commands:")
        lesson_name = lesson_path.stem
        unit_name = lesson_path.parent.name
        print(f"  git add backend/data/math/G3/{unit_name}/{lesson_name}.json")
        print(f"  git commit -m 'verify: G3 {unit_name} {lesson_name} 7-stage pass'")
        print(f"  git push")
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/generate_audit_report.py G3 U<N> L<N>")
        print("Example: python3 scripts/generate_audit_report.py G3 U1 L1")
        sys.exit(1)

    grade = sys.argv[1]
    unit_arg = sys.argv[2].lstrip("Uu")
    lesson_arg = sys.argv[3].lstrip("Ll")

    try:
        lesson, lesson_path = load_lesson(grade, unit_arg, lesson_arg)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    results = [
        check_stage1(lesson),
        check_stage2(lesson),
        check_stage3(lesson),
        check_stage4(lesson),
        check_stage5(lesson),
        check_stage6(lesson),
        check_stage7(lesson),
    ]

    print_report(lesson, lesson_path, results)

    # exit code 1 if any stage failed
    failed = [r for r in results if not r.get("passed") and not r.get("pending") and r["stage"] != 7]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
