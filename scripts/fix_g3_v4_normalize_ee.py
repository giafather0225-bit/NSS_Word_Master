"""
G3 v4 — expected_errors 데이터 정규화 + 의미 회복.

처리
1) list-shape EE 182건 → dict 형태 (`_wrong` 키)
2) generic concept_gap-only 2,697건 → 라이브러리 vocab 분배 재합성
   - choice마다 다른 misconception_id 부착 (heuristic, synthesized=True 마크)
   - 항목 CCSS의 라이브러리 misconception들을 wrong choices에 순환 분배
   - 라이브러리 없는 CCSS는 그대로 둠

원칙
- 도메인 정답을 보장하지 않음 (학습자 실 데이터로 정련 필요)
- 그러나 진단 엔진이 "concept_gap"이 아닌 구체적 misconception_id를 받아
  학습자에게 다양한 진단 결과를 제공하는 인프라 회복
- idempotent: 같은 misconception_id가 이미 있으면 건드리지 않음
"""
from __future__ import annotations
import json, os
from pathlib import Path

ROOT = Path('/Users/markjhlee/NSS_Word_Master/backend/data/math/G3')
LIB_DIR = ROOT / 'misconceptions'

# === 라이브러리 인덱스 ===
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
    """진짜 generic 노이즈만 식별:
       - 모든 wrong choice가 error_type='concept_gap'
       - 모든 wrong choice의 note가 동일 (auto-synth 흔적)
       - misconception_id 없음
       원본 작성자가 'careless'로 라벨링하고 choice별로 다른 specific note를 넣은 경우는 보존.
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
    # generic = 단일 concept_gap 라벨 + 단일 (또는 공백) note
    return types == {'concept_gap'} and len(notes) <= 1


# === 변환 함수 ===

def fix_list_ee(item: dict) -> bool:
    ee = item.get('expected_errors')
    if not isinstance(ee, list):
        return False
    notes = [str(x).strip() for x in ee if x]
    fb_incorrect = (item.get('feedback') or {}).get('incorrect', '')
    note = '; '.join(notes) or fb_incorrect or '개념 재확인'
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
    # 채울 wrong choice 키 모음 (A/B/C/D 또는 _wrong)
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
            'synthesized': True,  # heuristic — 학습자 실데이터로 정련 필요
        }
    item['expected_errors'] = new_ee
    return True


# === 메인 ===

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
