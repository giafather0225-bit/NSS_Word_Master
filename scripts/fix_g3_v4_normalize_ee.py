"""
G3 v4 — normalize expected_errors data + recover meaning.

Processing
1) 182 list-shape EE entries → dict form (`_wrong` key)
2) 2,697 generic concept_gap-only entries → re-synthesize by distributing library vocab
   - attach a different misconception_id per choice (heuristic, marked synthesized=True)
   - round-robin distribute the item's CCSS library misconceptions across wrong choices
   - leave CCSS without a library entry unchanged

Principles
- does not guarantee domain correctness (needs refinement from real learner data)
- but restores the infrastructure so the diagnostic engine receives a concrete
  misconception_id instead of "concept_gap", giving learners varied diagnostic results
- idempotent: if the same misconception_id is already present, leave it alone
"""
from __future__ import annotations
import json, os
from pathlib import Path

ROOT = Path('/Users/markjhlee/NSS_Word_Master/backend/data/math/G3')
LIB_DIR = ROOT / 'misconceptions'

# === Library index ===
def build_lib_idx() -> dict:
    out: dict = {}
    for p in LIB_DIR.glob('*.json'):
        d = json.load(open(p, encoding='utf-8'))
        ccss = d.get('standard') or p.stem
        miscs = []
        for m in d.get('misconceptions', []) or []:
            mid = m.get('misconception_id')
            if mid:
                miscs.append((mid, m))
        if miscs:
            out[ccss] = miscs
    return out


def resolve(ccss: str, lib_idx: dict):
    if not ccss:
        return None
    if ccss in lib_idx:
        return lib_idx[ccss]
    if ccss[-1].isalpha() and ccss[-1].islower():
        parent = ccss[:-1]
        if parent in lib_idx:
            return lib_idx[parent]
    return None


def is_generic_ee(ee: dict) -> bool:
    """Identify only genuine generic noise:
       - every wrong choice has error_type='concept_gap'
       - every wrong choice has an identical note (trace of auto-synth)
       - no misconception_id
       Preserve cases where the original author labeled 'careless' with a different specific note per choice.
    """
    if not isinstance(ee, dict) or not ee:
        return False
    types = set()
    notes = set()
    for v in ee.values():
        if isinstance(v, dict):
            if v.get('misconception_id') or v.get('synthesized'):
                return False
            types.add(v.get('error_type', ''))
            notes.add(v.get('note', ''))
    # generic = single concept_gap label + single (or blank) note
    return types == {'concept_gap'} and len(notes) <= 1


# === Transform functions ===

def fix_list_ee(item: dict) -> bool:
    ee = item.get('expected_errors')
    if not isinstance(ee, list):
        return False
    notes = [str(x).strip() for x in ee if x]
    fb_incorrect = (item.get('feedback') or {}).get('incorrect', '')
    note = '; '.join(notes) or fb_incorrect or 'Review the concept'
    item['expected_errors'] = {
        '_wrong': {
            'error_type': 'concept_gap',
            'note': note,
        }
    }
    return True


def reseed_generic(item: dict, lib_idx: dict) -> bool:
    ee = item.get('expected_errors')
    if not is_generic_ee(ee):
        return False
    ccss = item.get('ccss')
    if isinstance(ccss, list):
        ccss = ccss[0] if ccss else None
    if not ccss:
        return False
    miscs = resolve(ccss, lib_idx)
    if not miscs:
        return False
    correct = str(item.get('correct_answer', '') or '').upper()
    # collect wrong-choice keys to fill (A/B/C/D or _wrong)
    choice_keys = [k for k in ee.keys() if k.upper() != correct]
    if not choice_keys:
        return False
    new_ee = {}
    for i, ch_key in enumerate(sorted(choice_keys)):
        mid, m = miscs[i % len(miscs)]
        new_ee[ch_key] = {
            'error_type': m.get('error_type', 'concept_gap'),
            'note': m.get('short_label', '') or (m.get('description', '')[:140]),
            'misconception_id': mid,
            'synthesized': True,  # heuristic — needs refinement from real learner data
        }
    item['expected_errors'] = new_ee
    return True


# === Main ===

def main():
    lib_idx = build_lib_idx()
    print(f'[lib] {len(lib_idx)} CCSS')

    list_fixed = 0
    reseeded = 0
    files_changed = 0

    for unit_dir in sorted(ROOT.iterdir()):
        if not unit_dir.is_dir() or unit_dir.name == 'misconceptions':
            continue
        for path in sorted(unit_dir.glob('*.json')):
            try:
                d = json.load(open(path, encoding='utf-8'))
            except Exception as e:
                print(f'  ⚠ {path}: {e}')
                continue
            changed = False
            for stg in ['pretest', 'try', 'practice_r1', 'practice_r2', 'practice_r3']:
                for it in d.get(stg, []) or []:
                    if not isinstance(it, dict):
                        continue
                    if fix_list_ee(it):
                        list_fixed += 1
                        changed = True
                    if reseed_generic(it, lib_idx):
                        reseeded += 1
                        changed = True
            if changed:
                json.dump(d, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                files_changed += 1

    print(f'\n  list-shape EE → dict:    {list_fixed}')
    print(f'  generic → re-seeded:     {reseeded}')
    print(f'  files changed:           {files_changed}')
    print('✅ v4 done')


if __name__ == '__main__':
    main()
