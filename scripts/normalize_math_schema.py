#!/usr/bin/env python3
"""
normalize_math_schema.py — Idempotent migration of math content to canonical schema.

Usage:
    python3 scripts/normalize_math_schema.py G3              # rewrite G3 in place
    python3 scripts/normalize_math_schema.py G3 --dry-run    # show diffs only
    python3 scripts/normalize_math_schema.py G3 G4           # multiple grades

Transforms applied to every problem-shaped object (in stages, items[], or sections.<stage>[]):

  Field aliases:
    stem        → question
    answer      → correct_answer
    options     → choices

  choices shape:
    dict {"A": "...", ...}  →  list [...]   (sorted by key)
    list ["3", "5"]         →  list ["A) 3", "B) 5"]   (letter prefix added)

  type:
    multiple_choice / MC / compare      → mc
    true_false / TRUE_FALSE             → tf
    fill_in / FILL_IN / word_problem    → input
    open_response                       → input
    DRAG_SORT / ordering                → drag_sort
    <missing>                            → inferred (mc if choices, tf if true/false ans, else input)

  mc correct_answer:
    "3"          (matches choice "A) 3")  →  "A"
    "C (25)"     (letter prefix style)    →  "C"
    Already a single letter A–H            →  unchanged

  tf correct_answer:
    case-normalized to lowercase "true"|"false"

Learn cards: type 'card' → 'concept_card'. Other learn types (instruction_check, example, etc.) preserved
because the renderer dispatches on them.

Idempotent: re-running on already-normalized data should produce no diffs.

Validation: every output passes scripts/audit_math_schema.py with 0 errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "backend" / "data" / "math"

STD_STAGES = ("pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3")

_TYPE_ALIASES_PROBLEM = {
    "multiple_choice": "mc", "MULTIPLE_CHOICE": "mc", "MC": "mc", "compare": "mc",
    "true_false": "tf", "TRUE_FALSE": "tf",
    "fill_in": "input", "FILL_IN": "input", "INPUT": "input",
    "word_problem": "input", "open_response": "input",
    "DRAG_SORT": "drag_sort", "ordering": "drag_sort",
}

_LEARN_TYPE_ALIASES = {
    "card": "concept_card",
    # 'concept', 'instruction', 'instruction_check', 'example', 'interactive', 'summary'
    # are preserved — renderer dispatches on them.
}

# A choice already has a letter prefix if it starts with `A`–`H` followed by `)`, `.`, or `:`.
_HAS_LETTER_PREFIX = re.compile(r"^[A-Ha-h][\).\:]\s*")


# ── helpers ─────────────────────────────────────────────────────────


def _is_problem_like(obj) -> bool:
    """A dict that looks like a problem (has a question/stem AND an answer field)."""
    if not isinstance(obj, dict):
        return False
    has_q = bool(obj.get("question") or obj.get("stem") or obj.get("prompt"))
    has_a = "correct_answer" in obj or "answer" in obj
    return has_q and has_a


def _is_learn_card_like(obj) -> bool:
    """A dict that looks like a learn card (no answer; has title/content)."""
    if not isinstance(obj, dict):
        return False
    if "correct_answer" in obj or "answer" in obj:
        return False
    return bool(obj.get("title") or obj.get("content") or obj.get("type"))


def _normalize_choices(p: dict, stats: dict) -> None:
    """Normalize choices in place: dict→list, ensure letter prefixes."""
    raw = p.get("choices")
    if raw is None and "options" in p:
        p["choices"] = p.pop("options")
        stats["alias_options"] = stats.get("alias_options", 0) + 1
        raw = p["choices"]
    if isinstance(raw, dict):
        # Sort by uppercase key so A,B,C,D ordering is canonical
        keys = sorted(raw.keys(), key=lambda k: str(k).upper())
        p["choices"] = [raw[k] for k in keys]
        stats["choices_dict_to_list"] = stats.get("choices_dict_to_list", 0) + 1
        raw = p["choices"]
    if isinstance(raw, list) and len(raw) > 0:
        # Add letter prefixes if missing
        new_choices = []
        added_prefix = False
        for i, c in enumerate(raw):
            cs = str(c)
            if _HAS_LETTER_PREFIX.match(cs):
                # Normalize separator to ") " for canonical form
                # e.g. "A. 3" -> "A) 3", "A: 3" -> "A) 3"
                m = _HAS_LETTER_PREFIX.match(cs)
                letter = cs[0].upper()
                rest = cs[m.end():]
                normalized = f"{letter}) {rest}".rstrip()
                if normalized != cs:
                    added_prefix = True
                new_choices.append(normalized)
            else:
                new_choices.append(f"{chr(65 + i)}) {cs}")
                added_prefix = True
        if added_prefix:
            stats["choice_prefix_added"] = stats.get("choice_prefix_added", 0) + 1
        p["choices"] = new_choices


_SOCRATIC_HINT = re.compile(r'^([^.!?]*\?)\s*(.*)', re.DOTALL)


def _hint_from_explanation(expl: str) -> str | None:
    """Extract a Socratic-style hint from explanation: first sentence ending in '?'.

    Returns None if no question-form opener is present (caller should not auto-fill;
    explanation belongs in feedback.incorrect instead).
    """
    if not isinstance(expl, str) or not expl.strip():
        return None
    m = _SOCRATIC_HINT.match(expl.strip())
    if not m:
        return None
    first = m.group(1).strip()
    # Sanity: must be a real prompt, not a one-letter "?" question
    if len(first) < 8 or len(first) > 120:
        return None
    return first


def _normalize_problem(p: dict, stats: dict) -> dict:
    """In-place mutate p, returning it. Idempotent."""
    # Field aliases
    if "question" not in p:
        for k in ("stem", "prompt", "text"):
            if k in p:
                p["question"] = p.pop(k)
                stats[f"alias_{k}"] = stats.get(f"alias_{k}", 0) + 1
                break
    elif "stem" in p:
        # canonical present + alias also present → drop alias
        p.pop("stem", None)
        stats["alias_stem_dropped"] = stats.get("alias_stem_dropped", 0) + 1

    if "correct_answer" not in p and "answer" in p:
        p["correct_answer"] = p.pop("answer")
        stats["alias_answer"] = stats.get("alias_answer", 0) + 1
    elif "answer" in p:
        p.pop("answer", None)
        stats["alias_answer_dropped"] = stats.get("alias_answer_dropped", 0) + 1

    _normalize_choices(p, stats)

    # type normalization
    raw_type = p.get("type", "")
    new_type = _TYPE_ALIASES_PROBLEM.get(raw_type, str(raw_type).lower() if raw_type else "")
    if new_type != raw_type:
        stats["type_aliased"] = stats.get("type_aliased", 0) + 1
    if not new_type:
        ans = str(p.get("correct_answer", "")).strip().lower()
        if isinstance(p.get("choices"), list) and len(p["choices"]) >= 2:
            new_type = "mc"
        elif ans in ("true", "false"):
            new_type = "tf"
        else:
            new_type = "input"
        stats["type_inferred"] = stats.get("type_inferred", 0) + 1
    elif new_type == "input" and isinstance(p.get("choices"), list) and len(p["choices"]) >= 2:
        # input but has choices → it's mc
        new_type = "mc"
        stats["type_input_to_mc"] = stats.get("type_input_to_mc", 0) + 1
    p["type"] = new_type

    # MC: ensure correct_answer is a single uppercase letter
    if new_type == "mc":
        choices = p.get("choices") or []
        ans = str(p.get("correct_answer", "")).strip()
        # Already a letter?
        if len(ans) == 1 and ans.upper() in "ABCDEFGH":
            if ans != ans.upper():
                p["correct_answer"] = ans.upper()
                stats["mc_ans_uppercased"] = stats.get("mc_ans_uppercased", 0) + 1
        else:
            # "C (25 sq cm)" style → "C"
            m = re.match(r"^([A-Ha-h])\s*[\)\.\:\(]", ans)
            if m and ans[0].upper() in [chr(65 + i) for i in range(len(choices))]:
                p["correct_answer"] = m.group(1).upper()
                stats["mc_ans_letter_extracted"] = stats.get("mc_ans_letter_extracted", 0) + 1
            else:
                # Match by choice text: strip prefix from each choice and compare
                for i, c in enumerate(choices):
                    cs = str(c)
                    m2 = _HAS_LETTER_PREFIX.match(cs)
                    cleaned = cs[m2.end():].strip() if m2 else cs.strip()
                    if cleaned.lower() == ans.lower():
                        p["correct_answer"] = chr(65 + i)
                        stats["mc_ans_resolved_by_text"] = stats.get("mc_ans_resolved_by_text", 0) + 1
                        break
                # If still not a single letter, leave it (will appear as warning)

    # tf: lowercase
    if new_type == "tf":
        ans = str(p.get("correct_answer", "")).strip().lower()
        if ans in ("true", "false") and p["correct_answer"] != ans:
            p["correct_answer"] = ans
            stats["tf_ans_lowercased"] = stats.get("tf_ans_lowercased", 0) + 1

    # hint (singular string) → hints (array). Canonical is plural array.
    if "hint" in p:
        existing = p.get("hints")
        if not isinstance(existing, list) or not existing:
            v = p["hint"]
            if isinstance(v, str) and v.strip():
                p["hints"] = [v.strip()]
                stats["hint_to_hints"] = stats.get("hint_to_hints", 0) + 1
        # Drop redundant singular field once captured
        p.pop("hint", None)
        stats["hint_singular_dropped"] = stats.get("hint_singular_dropped", 0) + 1

    # Auto-fill hint from explanation IF Socratic-style first sentence available
    if not (isinstance(p.get("hints"), list) and p["hints"]):
        socratic = _hint_from_explanation(p.get("explanation", ""))
        if socratic:
            p["hints"] = [socratic]
            stats["hint_socratic_extracted"] = stats.get("hint_socratic_extracted", 0) + 1

    # Coalesce flat feedback_correct/feedback_wrong fields into the canonical
    # feedback object (frontend supports both, but spec says object).
    flat_correct = p.pop("feedback_correct", None)
    flat_wrong = p.pop("feedback_wrong", None)
    if flat_correct or flat_wrong:
        fb = p.get("feedback")
        if not isinstance(fb, dict):
            fb = {}
        if flat_correct and not fb.get("correct"):
            fb["correct"] = flat_correct
        if flat_wrong and not fb.get("incorrect"):
            fb["incorrect"] = flat_wrong
        p["feedback"] = fb
        stats["feedback_flat_to_object"] = stats.get("feedback_flat_to_object", 0) + 1

    # Auto-fill feedback from explanation when missing.
    fb = p.get("feedback")
    has_fb_obj = isinstance(fb, dict) and (fb.get("correct") or fb.get("incorrect"))
    expl = p.get("explanation")
    if not has_fb_obj and isinstance(expl, str) and expl.strip():
        p["feedback"] = {
            "correct": "Correct!",
            "incorrect": expl.strip(),
        }
        stats["feedback_from_explanation"] = stats.get("feedback_from_explanation", 0) + 1
    elif isinstance(fb, dict):
        # Partial fill: maybe only one side present
        changed = False
        if not fb.get("incorrect") and isinstance(expl, str) and expl.strip():
            fb["incorrect"] = expl.strip()
            changed = True
        if not fb.get("correct"):
            fb["correct"] = "Correct!"
            changed = True
        if changed:
            stats["feedback_partial_filled"] = stats.get("feedback_partial_filled", 0) + 1

    return p


def _normalize_learn_card(c: dict, stats: dict) -> dict:
    """Normalize learn card type: 'card' → 'concept_card'. Other types preserved."""
    if not isinstance(c, dict):
        return c
    raw_type = str(c.get("type", "")).lower()
    if raw_type in _LEARN_TYPE_ALIASES:
        c["type"] = _LEARN_TYPE_ALIASES[raw_type]
        stats["learn_type_aliased"] = stats.get("learn_type_aliased", 0) + 1
    return c


def _normalize_lesson_meta(d: dict, path: Path, stats: dict) -> None:
    """Fill missing top-level lesson metadata from path + legacy fields.

    Infers `grade` (from path), `unit` (from parent folder), `title`
    (from `lesson_title`), and `lesson_id` (`g{N}_u{M}_l{K}`) when these
    canonical fields are absent. Idempotent.
    """
    parts = path.parts
    # Find ".../math/{grade}/{unit}/{lesson}.json"
    grade = unit = lesson_stem = None
    for i, p in enumerate(parts):
        if p == "math" and i + 2 < len(parts):
            grade = parts[i + 1]
            unit = parts[i + 2]
            if i + 3 < len(parts):
                lesson_stem = Path(parts[i + 3]).stem
            break
    if grade and not d.get("grade"):
        d["grade"] = grade
        stats["meta_grade_inferred"] = stats.get("meta_grade_inferred", 0) + 1
    if unit and not d.get("unit"):
        d["unit"] = unit
        stats["meta_unit_inferred"] = stats.get("meta_unit_inferred", 0) + 1

    # title: prefer canonical, fall back to lesson_title
    if not d.get("title") and d.get("lesson_title"):
        d["title"] = d["lesson_title"]
        stats["meta_title_from_lesson_title"] = stats.get("meta_title_from_lesson_title", 0) + 1

    # lesson_id: derive from chapter+lesson numbers, or from filename's L{K} pattern
    if not d.get("lesson_id"):
        chap = d.get("chapter")
        less = d.get("lesson")
        if isinstance(chap, int) and isinstance(less, int) and grade:
            g_num = grade.lstrip("Gg")
            d["lesson_id"] = f"g{g_num}_u{chap}_l{less}"
            stats["meta_lesson_id_from_chapter_lesson"] = stats.get("meta_lesson_id_from_chapter_lesson", 0) + 1
        elif lesson_stem and unit and grade:
            # Parse U9 from "U9_compare_fractions" and L3 from "L3_..."
            import re as _re
            um = _re.match(r"U(\d+)", unit, _re.I)
            lm = _re.match(r"L(\d+)", lesson_stem, _re.I)
            if um and lm:
                g_num = grade.lstrip("Gg")
                d["lesson_id"] = f"g{g_num}_u{int(um.group(1))}_l{int(lm.group(1))}"
                stats["meta_lesson_id_from_path"] = stats.get("meta_lesson_id_from_path", 0) + 1


def _normalize_lesson(d: dict, stats: dict) -> dict:
    """Walk all problem-shaped objects in a lesson and normalize them."""
    # STD bucket: stages as top-level keys
    for stage in STD_STAGES:
        if stage in d and isinstance(d[stage], list):
            for i, p in enumerate(d[stage]):
                if stage == "learn":
                    _normalize_learn_card(p, stats)
                elif _is_problem_like(p):
                    _normalize_problem(p, stats)
    # ITEMS bucket
    if isinstance(d.get("items"), list):
        for it in d["items"]:
            if not isinstance(it, dict):
                continue
            section = it.get("section", "")
            if section == "learn":
                _normalize_learn_card(it, stats)
            elif _is_problem_like(it):
                _normalize_problem(it, stats)
    # SECTIONS bucket
    sections = d.get("sections")
    if isinstance(sections, dict):
        for section, lst in sections.items():
            if not isinstance(lst, list):
                continue
            for it in lst:
                if section == "learn":
                    _normalize_learn_card(it, stats)
                elif _is_problem_like(it):
                    _normalize_problem(it, stats)
    return d


def _normalize_unit_test(d: dict, stats: dict) -> dict:
    """Normalize the problems[] of a unit_test.json."""
    for p in d.get("problems", []) or []:
        if _is_problem_like(p):
            _normalize_problem(p, stats)
    return d


# ── main ────────────────────────────────────────────────────────────


def run(grades: list[str], dry_run: bool) -> int:
    overall_stats: dict[str, int] = {}
    files_changed = 0
    files_total = 0

    for grade in grades:
        groot = ROOT / grade
        if not groot.is_dir():
            print(f"  skip: {grade} directory not found")
            continue
        for f in groot.rglob("*.json"):
            # Skip deprecated/private subfolders (e.g. `_deprecated/`)
            if any(part.startswith("_") for part in f.relative_to(groot).parts):
                continue
            files_total += 1
            try:
                original = f.read_text("utf-8")
                d = json.loads(original)
            except Exception as e:
                print(f"  ✗ {f.relative_to(ROOT)}: {e}")
                continue

            # Take stats snapshot
            file_stats: dict[str, int] = {}
            if f.name == "unit_test.json":
                _normalize_unit_test(d, file_stats)
            else:
                _normalize_lesson_meta(d, f, file_stats)
                _normalize_lesson(d, file_stats)

            # Only write when an actual transform fired. If file_stats is empty,
            # any text diff is just JSON re-formatting — leave the original alone.
            if file_stats:
                new_text = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
                if new_text != original:
                    files_changed += 1
                    if dry_run:
                        print(f"  diff {f.relative_to(ROOT)}: {file_stats}")
                    else:
                        f.write_text(new_text, "utf-8")
                        print(f"  ✓ {f.relative_to(ROOT)}: {file_stats}")
                    for k, v in file_stats.items():
                        overall_stats[k] = overall_stats.get(k, 0) + v

    print()
    print(f"Files scanned: {files_total}")
    print(f"Files changed: {files_changed}{' (dry-run, no writes)' if dry_run else ''}")
    print("Transform totals:")
    for k, v in sorted(overall_stats.items(), key=lambda x: -x[1]):
        print(f"  {v:6d}  {k}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("grade", nargs="+", help="grades to normalize, e.g. G3 G4")
    ap.add_argument("--dry-run", action="store_true", help="show diffs without writing")
    args = ap.parse_args()
    sys.exit(run(args.grade, args.dry_run))
