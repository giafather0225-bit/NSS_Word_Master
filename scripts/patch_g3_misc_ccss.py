"""
G3 패치 스크립트:
1) CCSS 표기 정규화 — 미스컨셉션 라이브러리(파일명·standard·misconception_id)와 일부 항목 코드를 공식 CCSS 표기로 통일.
2) misconception_id 링크 — 각 항목에 candidate ID 리스트 + expected_errors[choice]에 exact match ID 부착.

원칙
- in-place 수정 (라이브러리 파일명은 git mv 수준의 rename).
- idempotent: 두 번 돌려도 변화 없음.
- 백업 없이 git에 의존.
"""
from __future__ import annotations
import json, os, re, sys, glob, shutil
from pathlib import Path
from collections import defaultdict

ROOT = Path('/Users/markjhlee/NSS_Word_Master/backend/data/math/G3')
LIB = ROOT / 'misconceptions'

# === 1. CCSS 정규화 매핑 ===
# 라이브러리·항목 양쪽에서 사용 — 좌변(현재) → 우변(정식)
CCSS_NORMALIZE = {
    # 라이브러리에서 클러스터 문자 누락
    '3.NBT.1':   '3.NBT.A.1',
    '3.NBT.2':   '3.NBT.A.2',
    # 항목에서 하위 표기 비정상
    '3.NF.A.3.A': '3.NF.A.3a',
    '3.NF.A.3.B': '3.NF.A.3b',
    '3.NF.A.3.D': '3.NF.A.3d',
}

def norm(code: str) -> str:
    return CCSS_NORMALIZE.get(code, code)

# === 2. 라이브러리 정규화 ===
def normalize_library():
    renamed = 0
    updated = 0
    for path in sorted(LIB.glob('*.json')):
        stem = path.stem  # "3.NBT.2"
        new_stem = norm(stem)
        d = json.load(open(path, encoding='utf-8'))
        changed = False
        # standard 필드
        if 'standard' in d:
            ns = norm(d['standard'])
            if ns != d['standard']:
                d['standard'] = ns
                changed = True
        # misconception_id prefix 갱신: "3.NBT.2.M01" → "3.NBT.A.2.M01"
        if stem != new_stem:
            for m in d.get('misconceptions', []):
                mid = m.get('misconception_id', '')
                if mid.startswith(stem + '.'):
                    m['misconception_id'] = new_stem + mid[len(stem):]
                    changed = True
        if changed:
            json.dump(d, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            updated += 1
        # 파일 rename
        if stem != new_stem:
            new_path = LIB / f'{new_stem}.json'
            if new_path.exists():
                print(f'  ⚠ skip rename: {new_path.name} already exists')
            else:
                shutil.move(str(path), str(new_path))
                renamed += 1
                print(f'  ↻ rename: {stem}.json → {new_stem}.json')
    print(f'[lib] renamed={renamed}, content-updated={updated}')

# === 3. 라이브러리 인덱스 빌드 ===
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

# === 4. 항목 패치 ===
def resolve_lib_entry(ccss: str, lib_idx: dict):
    """exact match → 부모(말단 소문자/숫자 제거) fallback."""
    if ccss in lib_idx:
        return ccss, lib_idx[ccss]
    # 자식 표준 (예: 3.NF.A.3a, 3.NF.A.2b) → 부모 (3.NF.A.3, 3.NF.A.2)
    # 마지막 문자가 소문자면 그것만 떼고 재시도
    if ccss and ccss[-1].isalpha() and ccss[-1].islower():
        parent = ccss[:-1]
        if parent in lib_idx:
            return parent, lib_idx[parent]
    return None, None


def patch_item(item: dict, lib_idx: dict) -> bool:
    """단일 항목에 candidate IDs + exact-match misconception_id 부착. 변경 여부 반환."""
    if not isinstance(item, dict):
        return False
    ccss_raw = item.get('ccss')
    if not isinstance(ccss_raw, str):
        return False
    ccss = norm(ccss_raw)
    changed = False
    # ccss 자체 정규화
    if ccss != ccss_raw:
        item['ccss'] = ccss
        changed = True
    _, lib_entry = resolve_lib_entry(ccss, lib_idx)
    if not lib_entry:
        return changed  # 라이브러리에 없는 CCSS — 그냥 통과
    # candidate ids (CCSS 단위 soft link)
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
    """재귀적으로 모든 dict를 보며 patch_item 시도."""
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
