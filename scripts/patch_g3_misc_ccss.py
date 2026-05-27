"""
G3 patch script:
1) CCSS notation normalization — unify misconception library (filenames, standard, misconception_id) and item codes to official CCSS notation.
2) misconception_id linking — attach candidate ID list to each item + exact match ID to expected_errors[choice].

Principles:
- In-place modification (library filenames use git mv level rename).
- Idempotent: running twice produces no changes.
- Backup-free; relies on git.
"""
from __future__ import annotations
import json, os, re, sys, glob, shutil
from pathlib import Path
from collections import defaultdict

ROOT = Path('/Users/markjhlee/NSS_Word_Master/backend/data/math/G3')
LIB = ROOT / 'misconceptions'

# === 1. CCSS normalization mapping ===
# Used in both library and items — left side (current) → right side (official)
CCSS_NORMALIZE = {
    # cluster letter missing in the library
    '3.NBT.1':   '3.NBT.A.1',
    '3.NBT.2':   '3.NBT.A.2',
    # malformed sub-notation in items
    '3.NF.A.3.A': '3.NF.A.3a',
    '3.NF.A.3.B': '3.NF.A.3b',
    '3.NF.A.3.D': '3.NF.A.3d',
}

def norm(code: str) -> str:
    return CCSS_NORMALIZE.get(code, code)

# === 2. Library normalization ===
def normalize_library():
    renamed = 0
    updated = 0
    for path in sorted(LIB.glob('*.json')):
        stem = path.stem  # "3.NBT.2"
        new_stem = norm(stem)
        d = json.load(open(path, encoding='utf-8'))
        changed = False
        # standard field
        if 'standard' in d:
            ns = norm(d['standard'])
            if ns != d['standard']:
                d['standard'] = ns
                changed = True
        # update misconception_id prefix: "3.NBT.2.M01" → "3.NBT.A.2.M01"
        if stem != new_stem:
            for m in d.get('misconceptions', []):
                mid = m.get('misconception_id', '')
                if mid.startswith(stem + '.'):
                    m['misconception_id'] = new_stem + mid[len(stem):]
                    changed = True
        if changed:
            json.dump(d, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            updated += 1
        # rename file
        if stem != new_stem:
            new_path = LIB / f'{new_stem}.json'
            if new_path.exists():
                print(f'  ⚠ skip rename: {new_path.name} already exists')
            else:
                shutil.move(str(path), str(new_path))
                renamed += 1
                print(f'  ↻ rename: {stem}.json → {new_stem}.json')
    print(f'[lib] renamed={renamed}, content-updated={updated}')

# === 3. Build library index ===
def build_library_index() -> dict:
    """ccss → {error_types: {et: mid}, all_ids: [mid,...]}"""
    idx = {}
    for path in sorted(LIB.glob('*.json')):
        d = json.load(open(path, encoding='utf-8'))
        ccss = d.get('standard') or path.stem
        et_map = {}
        ids = []
        for m in d.get('misconceptions', []):
            mid = m.get('misconception_id')
            et = m.get('error_type')
            if mid and et:
                et_map[et] = mid
                ids.append(mid)
        idx[ccss] = {'error_types': et_map, 'all_ids': ids}
    return idx

# === 4. Item patching ===
def resolve_lib_entry(ccss: str, lib_idx: dict):
    """exact match → parent fallback (strip trailing lowercase/digit)."""
    if ccss in lib_idx:
        return ccss, lib_idx[ccss]
    # child standard (e.g. 3.NF.A.3a, 3.NF.A.2b) → parent (3.NF.A.3, 3.NF.A.2)
    # if the last char is lowercase, drop just that and retry
    if ccss and ccss[-1].isalpha() and ccss[-1].islower():
        parent = ccss[:-1]
        if parent in lib_idx:
            return parent, lib_idx[parent]
    return None, None


def patch_item(item: dict, lib_idx: dict) -> bool:
    """Attach candidate IDs + an exact-match misconception_id to a single item. Returns whether it changed."""
    if not isinstance(item, dict):
        return False
    ccss_raw = item.get('ccss')
    if not isinstance(ccss_raw, str):
        return False
    ccss = norm(ccss_raw)
    changed = False
    # normalize ccss itself
    if ccss != ccss_raw:
        item['ccss'] = ccss
        changed = True
    _, lib_entry = resolve_lib_entry(ccss, lib_idx)
    if not lib_entry:
        return changed  # CCSS not in the library — just pass through
    # candidate ids (CCSS-level soft link)
    new_cands = lib_entry['all_ids']
    if item.get('misconception_candidates') != new_cands:
        item['misconception_candidates'] = new_cands
        changed = True
    # expected_errors exact match
    ee = item.get('expected_errors')
    if isinstance(ee, dict):
        et_map = lib_entry['error_types']
        for choice, info in ee.items():
            if not isinstance(info, dict):
                continue
            et = info.get('error_type')
            if et and et in et_map:
                mid = et_map[et]
                if info.get('misconception_id') != mid:
                    info['misconception_id'] = mid
                    changed = True
    return changed

def walk_and_patch(obj, lib_idx, stats):
    """Recursively walk every dict and attempt patch_item."""
    if isinstance(obj, dict):
        if patch_item(obj, lib_idx):
            stats['items_patched'] += 1
        for v in obj.values():
            walk_and_patch(v, lib_idx, stats)
    elif isinstance(obj, list):
        for x in obj:
            walk_and_patch(x, lib_idx, stats)

def patch_all_units():
    lib_idx = build_library_index()
    print(f'[lib] indexed {len(lib_idx)} CCSS standards, '
          f'{sum(len(v["all_ids"]) for v in lib_idx.values())} misconceptions total')
    files_changed = 0
    items_total = 0
    items_with_match = 0
    for unit_dir in sorted(ROOT.iterdir()):
        if not unit_dir.is_dir() or unit_dir.name == 'misconceptions':
            continue
        for path in sorted(unit_dir.glob('*.json')):
            try:
                d = json.load(open(path, encoding='utf-8'))
            except Exception as e:
                print(f'  ⚠ skip {path}: {e}')
                continue
            stats = {'items_patched': 0}
            walk_and_patch(d, lib_idx, stats)
            if stats['items_patched']:
                json.dump(d, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                files_changed += 1
                items_total += stats['items_patched']
    print(f'[items] files_changed={files_changed}, items_patched={items_total}')

if __name__ == '__main__':
    print('=== STEP 1: normalize library ===')
    normalize_library()
    print('\n=== STEP 2: patch all G3 unit items ===')
    patch_all_units()
    print('\n✅ done')
