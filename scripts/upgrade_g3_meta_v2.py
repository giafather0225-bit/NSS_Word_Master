"""
G3 metadata enhancement in bulk — main schema v2 compatibility.
==============================================================================
Add verification metadata on top of standardized Phase 1-3 / 4-A·E schema:

1. Per item:
   - Add cpa_stage (sync with cpa_phase)
   - verification string → 3-source dict (preserve original_ref)
   - feedback_correct (extract from feedback.correct)
   - math_note empty string default

2. Top level:
   - vertical_alignment (prerequisite / current / successor)
   - metadata.upgraded = True
   - metadata.upgrade_version = "2.0-on-main"

Automatically process 119 files (106 lessons + 13 unit tests) × 3,690 items.

Usage:
    python3 scripts/upgrade_g3_meta_v2.py            # full run
    python3 scripts/upgrade_g3_meta_v2.py --unit U1  # single unit
    python3 scripts/upgrade_g3_meta_v2.py --dry-run  # preview

idempotent: re-running produces no changes.
"""

import argparse
import json
import pathlib
import re
import sys
from collections import OrderedDict


ROOT = pathlib.Path(__file__).parent.parent
G3_DIR = ROOT / "backend" / "data" / "math" / "G3"


# Per-unit verification source mapping (Go Math Ch.X)
UNIT_TO_CHAPTER = {
    "U1_add_sub_1000": ("Ch.1", "Module 2"),
    "U2_represent_interpret_data": ("Ch.2", "Module 6"),
    "U3_understand_multiplication": ("Ch.3", "Module 1"),
    "U4_multiplication_facts_strategies": ("Ch.4", "Module 3"),
    "U5_use_multiplication_facts": ("Ch.5", "Module 3"),
    "U6_understand_division": ("Ch.6", "Module 1"),
    "U7_division_facts_strategies": ("Ch.7", "Module 3"),
    "U8_understand_fractions": ("Ch.8", "Module 5"),
    "U9_compare_fractions": ("Ch.9", "Module 5"),
    "U10_perimeter": ("Ch.10", "Module 7"),
    "U11_time_mass_volume": ("Ch.11", "Module 2"),
    "U12_area": ("Ch.12", "Module 4"),
    "U13_shapes": ("Ch.13", "Module 7"),
}


def make_verification(unit: str, lesson_id: str, original: str = "") -> dict:
    ch, mod = UNIT_TO_CHAPTER.get(unit, ("Ch.?", "Module ?"))
    return {
        "concept_source": f"Go Math Grade 3 {ch} Lesson — {unit}/{lesson_id}",
        "procedure_source": f"EngageNY Grade 3 {mod} — {unit}",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
        "original_ref": original,
    }


def parse_lesson_num(file_name: str) -> int:
    """L7_xxx.json → 7. unit_test.json → 999."""
    if file_name == "unit_test.json":
        return 999
    m = re.match(r"L(\d+)_", file_name)
    return int(m.group(1)) if m else 0


def parse_unit_num(unit_name: str) -> int:
    m = re.match(r"U(\d+)_", unit_name)
    return int(m.group(1)) if m else 0


def build_lesson_index() -> dict:
    """Build complete unit/lesson catalog."""
    index = OrderedDict()
    units = sorted(
        [p for p in G3_DIR.iterdir() if p.is_dir() and re.match(r"U\d+_", p.name)],
        key=lambda p: parse_unit_num(p.name),
    )
    for u in units:
        lessons = sorted(u.glob("*.json"), key=lambda p: parse_lesson_num(p.name))
        index[u.name] = []
        for ls in lessons:
            try:
                d = json.loads(ls.read_text(encoding="utf-8"))
                title = d.get("title", "?")
                ccss = d.get("ccss", "?")
                if isinstance(ccss, list):
                    ccss = ccss[0] if ccss else "?"
                index[u.name].append({
                    "path": ls,
                    "name": ls.stem,  # L1_number_patterns
                    "title": title,
                    "ccss": ccss,
                })
            except Exception as e:
                print(f"⚠️  parse failed: {ls} — {e}", file=sys.stderr)
    return index


def make_vert_align(index: dict, unit: str, lesson_idx: int) -> dict:
    """Auto-generate prereq/current/successor from the unit/lesson index."""
    lessons = index[unit]
    cur = lessons[lesson_idx]
    unit_order = list(index.keys())
    unit_pos = unit_order.index(unit)

    # previous lesson
    if lesson_idx > 0:
        prev = lessons[lesson_idx - 1]
        prerequisite = f"G3 {unit}/{prev['name']} — {prev['title']} ({prev['ccss']})"
    elif unit_pos > 0:
        prev_unit = unit_order[unit_pos - 1]
        prev_lessons = index[prev_unit]
        # previous unit's unit_test (last) or last lesson
        prev = prev_lessons[-1]
        prerequisite = f"G3 {prev_unit} complete — {prev['title']} ({prev['ccss']})"
    else:
        prerequisite = "G2 — Grade 2 math (place value, add/subtract within 100, basic shapes)"

    current = f"G3 {unit}/{cur['name']} — {cur['title']} ({cur['ccss']})"

    # next lesson
    if lesson_idx + 1 < len(lessons):
        nxt = lessons[lesson_idx + 1]
        successor = f"G3 {unit}/{nxt['name']} — {nxt['title']} ({nxt['ccss']})"
    elif unit_pos + 1 < len(unit_order):
        nxt_unit = unit_order[unit_pos + 1]
        nxt = index[nxt_unit][0]
        successor = f"G3 {nxt_unit}/{nxt['name']} — {nxt['title']} ({nxt['ccss']})"
    else:
        successor = "G4 — Grade 4 math (angles, measurement, extended place value)"

    return {
        "prerequisite": prerequisite,
        "current": current,
        "successor": successor,
    }


def normalize_item(item: dict, unit: str, lesson_id: str) -> bool:
    """Enrich an item. Returns True if changed."""
    changed = False

    # sync cpa_phase → cpa_stage (backward compatible: keep both)
    if "cpa_phase" in item and "cpa_stage" not in item:
        item["cpa_stage"] = item["cpa_phase"]
        changed = True

    # feedback_correct: extract from feedback.correct
    if "feedback_correct" not in item:
        fb = item.get("feedback") or {}
        if isinstance(fb, dict) and fb.get("correct"):
            item["feedback_correct"] = fb["correct"]
            changed = True
        elif item.get("hints"):  # has hints but no feedback → default
            item["feedback_correct"] = "Correct! Well done."
            changed = True

    # math_note
    if "math_note" not in item:
        item["math_note"] = ""
        changed = True

    # verification: string → 3-source dict
    v = item.get("verification")
    if isinstance(v, str):
        item["verification"] = make_verification(unit, lesson_id, v)
        changed = True
    elif not isinstance(v, dict):
        item["verification"] = make_verification(unit, lesson_id, "")
        changed = True

    return changed


def upgrade_file(path: pathlib.Path, unit: str, vert_align: dict, dry_run: bool) -> dict:
    """Process a single file. Returns result stats."""
    d = json.loads(path.read_text(encoding="utf-8"))

    # skip if already upgraded
    if d.get("metadata", {}).get("upgraded") and d.get("metadata", {}).get("upgrade_version") == "2.0-on-main":
        return {"skipped": True, "reason": "already upgraded"}

    stats = {"items_changed": 0, "items_total": 0}

    # lesson file (sections) vs unit_test file (problems/questions)
    sections = ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"]
    has_sections = any(k in d for k in sections)

    if has_sections:
        for sec in sections:
            for item in d.get(sec, []):
                stats["items_total"] += 1
                if normalize_item(item, unit, path.stem):
                    stats["items_changed"] += 1
    else:
        # unit_test
        for key in ["problems", "questions"]:
            for item in d.get(key, []):
                stats["items_total"] += 1
                if normalize_item(item, unit, "unit_test"):
                    stats["items_changed"] += 1

    # top-level vertical_alignment
    if "vertical_alignment" not in d:
        d["vertical_alignment"] = vert_align

    # metadata
    d.setdefault("metadata", {})
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_version"] = "2.0-on-main"
    d["metadata"]["upgrade_script"] = "scripts/upgrade_g3_meta_v2.py"

    if not dry_run:
        path.write_text(
            json.dumps(d, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return stats


def main():
    parser = argparse.ArgumentParser(description="Batch-enrich G3 verification metadata (v2, main schema)")
    parser.add_argument("--unit", help="a specific unit only (e.g. U1_add_sub_1000)")
    parser.add_argument("--dry-run", action="store_true", help="preview changes only, do not save")
    args = parser.parse_args()

    print("📚 Building lesson catalog...")
    index = build_lesson_index()
    print(f"   {len(index)} units, {sum(len(v) for v in index.values())} files")
    print()

    total_files = 0
    total_changed = 0
    total_items_changed = 0
    skipped = 0

    for unit_name, lessons in index.items():
        if args.unit and args.unit != unit_name:
            continue
        print(f"📦 {unit_name}")
        for idx, lesson_info in enumerate(lessons):
            path = lesson_info["path"]
            vert_align = make_vert_align(index, unit_name, idx)
            stats = upgrade_file(path, unit_name, vert_align, args.dry_run)
            total_files += 1
            if stats.get("skipped"):
                skipped += 1
                continue
            total_changed += 1 if stats["items_changed"] > 0 else 0
            total_items_changed += stats["items_changed"]
            tag = "🔍 DRY" if args.dry_run else "✓"
            print(f"   {tag} {path.name}: enriched {stats['items_changed']}/{stats['items_total']} items")

    print()
    print(f"📊 Result: processed {total_files} files (skipped {skipped})")
    print(f"   changed {total_items_changed} items across {total_changed} files")
    if args.dry_run:
        print("   ⚠️  DRY-RUN — nothing saved")


if __name__ == "__main__":
    main()
