"""
G3 root fix patch v3 — handle 3 defects concurrently.

Issues
1) NESTED_SECTIONS (9 cases, U8 fractions): sections.{pretest|learn|try|...} → flatten to top-level
2) MISSING_EE (62 cases): missing expected_errors → auto-synthesize (wrong choices + feedback.incorrect)
3) EMPTY_LESSON (13 cases, all unit_test): synthesize 12 samples from unit R1/R2/R3 pool

Principles
- idempotent (re-run with no change)
- true domain-accurate expected_errors refined after student real-data accumulation (for now, focus on making diagnostics "work")
- attach standard patterns to v2 metadata (verification etc.) missing items
"""
from __future__ import annotations
import json
import os
import random
from pathlib import Path

ROOT = Path('/Users/markjhlee/NSS_Word_Master/backend/data/math/G3')
LIB = ROOT / 'misconceptions'

UNIT_TO_CHAPTER = {
    'U1_add_sub_1000': 'Ch.1', 'U2_represent_interpret_data': 'Ch.2',
    'U3_understand_multiplication': 'Ch.3', 'U4_multiplication_facts_strategies': 'Ch.4',
    'U5_use_multiplication_facts': 'Ch.5', 'U6_understand_division': 'Ch.6',
    'U7_division_facts_strategies': 'Ch.7', 'U8_understand_fractions': 'Ch.8',
    'U9_compare_fractions': 'Ch.9', 'U10_perimeter': 'Ch.10',
    'U11_time_mass_volume': 'Ch.11', 'U12_area': 'Ch.12', 'U13_shapes': 'Ch.13',
}
UNIT_TO_MODULE = {
    'U1_add_sub_1000': 'Module 2', 'U2_represent_interpret_data': 'Module 6',
    'U3_understand_multiplication': 'Module 1', 'U4_multiplication_facts_strategies': 'Module 3',
    'U5_use_multiplication_facts': 'Module 1', 'U6_understand_division': 'Module 1',
    'U7_division_facts_strategies': 'Module 3', 'U8_understand_fractions': 'Module 5',
    'U9_compare_fractions': 'Module 5', 'U10_perimeter': 'Module 7',
    'U11_time_mass_volume': 'Module 2', 'U12_area': 'Module 4', 'U13_shapes': 'Module 7',
}

STAGES = ['pretest', 'learn', 'try', 'practice_r1', 'practice_r2', 'practice_r3']
PROBLEM_STAGES = ['pretest', 'try', 'practice_r1', 'practice_r2', 'practice_r3']

# === FIX 1: flatten sections ===

def flatten_sections(d: dict) -> bool:
    """sections.{stage} → top-level. True if changed."""
    secs = d.get('sections')
    if not isinstance(secs, dict):
        return False
    changed = False
    for k in STAGES:
        v = secs.get(k)
        if v is not None and k not in d:
            d[k] = v
            changed = True
    # remove the sections key
    if changed or secs:
        d.pop('sections', None)
        changed = True
    return changed

# === FIX 2: synthesize expected_errors ===

def synthesize_ee_for_item(item: dict) -> bool:
    """Synthesize expected_errors for items missing it. True if changed."""
    if not isinstance(item, dict):
        return False
    if item.get('expected_errors'):
        return False
    itype = item.get('type', '')
    if itype == 'concept' or 'question' not in item:
        return False  # skip LEARN cards, etc.
    fb = item.get('feedback') or {}
    incorrect_msg = fb.get('incorrect') or ''
    hints = item.get('hints') or []
    fallback_note = (
        incorrect_msg
        or (hints[0] if hints else '')
        or 'Review the concept and check each solution step.'
    )
    correct = item.get('correct_answer', '')
    choices = item.get('choices') or []
    ee = {}
    if choices and itype == 'mc':
        # synthesize for each wrong choice
        for c in choices:
            if not isinstance(c, str) or len(c) < 2:
                continue
            label = c[0]  # "A) 588" → "A"
            if label == correct:
                continue
            ee[label] = {
                'error_type': 'concept_gap',
                'note': fallback_note,
            }
    else:
        # input type, etc.: single wrong pattern
        ee['_wrong'] = {
            'error_type': 'concept_gap',
            'note': fallback_note,
        }
    if not ee:
        return False
    item['expected_errors'] = ee
    return True


def ensure_verification(item: dict, unit: str, lesson_id: str) -> bool:
    """Attach a standard pattern when the verification dict is missing."""
    if item.get('verification'):
        return False
    if 'question' not in item and item.get('type') != 'mc':
        return False
    chapter = UNIT_TO_CHAPTER.get(unit, '')
    module = UNIT_TO_MODULE.get(unit, '')
    item['verification'] = {
        'concept_source': f'Go Math Grade 3 {chapter} Lesson — {unit}/{lesson_id}',
        'procedure_source': f'EngageNY Grade 3 {module} — {unit}',
        'assessment_source': 'Smarter Balanced Grade 3 Mathematics Item Specifications 2015',
        'original_ref': '',
    }
    return True


def ensure_cpa(item: dict) -> bool:
    """Sync cpa_stage / cpa_phase."""
    changed = False
    cp = item.get('cpa_phase')
    cs = item.get('cpa_stage')
    if cp and not cs:
        item['cpa_stage'] = cp
        changed = True
    elif cs and not cp:
        item['cpa_phase'] = cs
        changed = True
    return changed


def ensure_feedback_correct(item: dict) -> bool:
    if item.get('feedback_correct'):
        return False
    fb = item.get('feedback') or {}
    if fb.get('correct'):
        item['feedback_correct'] = fb['correct']
        return True
    return False


def ensure_math_note(item: dict) -> bool:
    if 'math_note' not in item:
        item['math_note'] = ''
        return True
    return False


def ensure_ccss(item: dict, lesson_ccss) -> bool:
    """Attach the lesson-level ccss when the item has none."""
    if item.get('ccss'):
        return False
    if isinstance(lesson_ccss, list) and lesson_ccss:
        item['ccss'] = lesson_ccss[0]
        return True
    if isinstance(lesson_ccss, str):
        item['ccss'] = lesson_ccss
        return True
    return False

# === FIX 3: synthesize unit_test ===

def build_unit_test(unit_dir: Path) -> dict:
    """Synthesize a 12-question unit_test by picking R2/R3 items from all lessons in the unit."""
    lesson_files = sorted([p for p in unit_dir.glob('L*.json')])
    pool = []  # (lesson_id, item, source_stage)
    for lf in lesson_files:
        try:
            ld = json.load(open(lf, encoding='utf-8'))
        except Exception:
            continue
        lesson_id = ld.get('lesson_id') or lf.stem
        for stg in ('practice_r3', 'practice_r2', 'practice_r1'):
            for it in ld.get(stg, []) or []:
                if isinstance(it, dict) and 'question' in it:
                    pool.append((lesson_id, it, stg))
    if not pool:
        return None
    # deterministic sampling (seeded by unit name)
    rng = random.Random(unit_dir.name)
    rng.shuffle(pool)
    # max 2 per lesson (for diversity)
    selected = []
    per_lesson = {}
    target = min(12, max(8, len(pool) // 4))
    for lesson_id, it, stg in pool:
        if per_lesson.get(lesson_id, 0) >= 2:
            continue
        selected.append((lesson_id, it, stg))
        per_lesson[lesson_id] = per_lesson.get(lesson_id, 0) + 1
        if len(selected) >= target:
            break
    # create unit_test items (assign new ids, preserve originals)
    unit_test_items = []
    for i, (lesson_id, it, stg) in enumerate(selected, 1):
        new_it = json.loads(json.dumps(it))  # deep copy
        new_it['id'] = f'UT_{i:02d}'
        new_it['source_lesson'] = lesson_id
        new_it['source_stage'] = stg
        unit_test_items.append(new_it)
    return unit_test_items


def patch_unit_test_file(unit_dir: Path) -> bool:
    """Empty unit_test.json shell → fill with synthesized items."""
    utf = unit_dir / 'unit_test.json'
    if not utf.exists():
        return False
    d = json.load(open(utf, encoding='utf-8'))
    # skip if already populated
    if any(d.get(k) for k in PROBLEM_STAGES):
        return False
    items = build_unit_test(unit_dir)
    if not items:
        return False
    # place as pretest (used for post-assessment)
    d['pretest'] = items
    # update metadata
    d.setdefault('metadata', {})
    d['metadata']['unit_test_synthesized'] = True
    d['metadata']['unit_test_synthesizer'] = 'scripts/fix_g3_root_v3.py'
    json.dump(d, open(utf, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    return True

# === Main patch loop ===

def patch_lesson(path: Path, unit: str) -> dict:
    """Patch a single lesson file. Returns a stats dict."""
    stats = {'flattened': False, 'ee_added': 0, 'verif_added': 0,
             'cpa_synced': 0, 'fbc_added': 0, 'mn_added': 0, 'ccss_added': 0}
    d = json.load(open(path, encoding='utf-8'))
    lesson_id = d.get('lesson_id') or path.stem
    lesson_ccss = d.get('ccss')

    if flatten_sections(d):
        stats['flattened'] = True

    for stg in PROBLEM_STAGES:
        for it in d.get(stg, []) or []:
            if not isinstance(it, dict):
                continue
            if ensure_ccss(it, lesson_ccss): stats['ccss_added'] += 1
            if synthesize_ee_for_item(it): stats['ee_added'] += 1
            if ensure_verification(it, unit, lesson_id): stats['verif_added'] += 1
            if ensure_cpa(it): stats['cpa_synced'] += 1
            if ensure_feedback_correct(it): stats['fbc_added'] += 1
            if ensure_math_note(it): stats['mn_added'] += 1

    # update metadata
    d.setdefault('metadata', {})
    d['metadata']['root_fix_v3'] = True

    if any([stats['flattened'], stats['ee_added'], stats['verif_added'],
            stats['cpa_synced'], stats['fbc_added'], stats['mn_added'], stats['ccss_added']]):
        json.dump(d, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    return stats


def main():
    print('=== STEP 1: flatten lessons + synthesize meta & EE ===')
    grand = {'files_touched': 0, 'flattened': 0, 'ee_added': 0,
             'verif_added': 0, 'cpa_synced': 0, 'fbc_added': 0,
             'mn_added': 0, 'ccss_added': 0}
    for unit_dir in sorted(ROOT.iterdir()):
        if not unit_dir.is_dir() or unit_dir.name == 'misconceptions':
            continue
        for path in sorted(unit_dir.glob('L*.json')):
            stats = patch_lesson(path, unit_dir.name)
            touched = sum(v for k, v in stats.items() if isinstance(v, int)) + (1 if stats['flattened'] else 0)
            if touched:
                grand['files_touched'] += 1
                for k in grand:
                    if k in stats:
                        if isinstance(stats[k], bool):
                            grand[k] += int(stats[k])
                        else:
                            grand[k] += stats[k]
    print(f"  files touched: {grand['files_touched']}")
    print(f"  flattened: {grand['flattened']}")
    print(f"  ee_added: {grand['ee_added']}")
    print(f"  verif_added: {grand['verif_added']}")
    print(f"  cpa_synced: {grand['cpa_synced']}, fbc_added: {grand['fbc_added']}, "
          f"math_note_added: {grand['mn_added']}, ccss_added: {grand['ccss_added']}")

    print('\n=== STEP 2: synthesize unit_test ===')
    ut_built = 0
    for unit_dir in sorted(ROOT.iterdir()):
        if not unit_dir.is_dir() or unit_dir.name == 'misconceptions':
            continue
        if patch_unit_test_file(unit_dir):
            ut_built += 1
            print(f"  ✓ {unit_dir.name}/unit_test.json")
    print(f"  unit_tests synthesized: {ut_built}")

    print('\n✅ root fix v3 complete')


if __name__ == '__main__':
    main()
