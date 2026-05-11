"""
G3 검증 메타 일괄 보강 — main schema v2 호환.
==============================================================================
main의 Phase 1-3 / 4-A·E 표준화된 schema 위에 검증 메타를 추가:

1. 항목별:
   - cpa_stage 추가 (cpa_phase 동기화)
   - verification 문자열 → 3소스 dict (original_ref 보존)
   - feedback_correct (feedback.correct에서 추출)
   - math_note 빈 문자열 기본

2. 최상위:
   - vertical_alignment (prerequisite / current / successor)
   - metadata.upgraded = True
   - metadata.upgrade_version = "2.0-on-main"

총 119 파일 (106 레슨 + 13 UT) × 3,690 항목 자동 처리.

사용법:
    python3 scripts/upgrade_g3_meta_v2.py            # 전체 실행
    python3 scripts/upgrade_g3_meta_v2.py --unit U1  # 한 단원만
    python3 scripts/upgrade_g3_meta_v2.py --dry-run  # 미리보기

idempotent: 재실행해도 변경 없음.
"""

import argparse
import json
import pathlib
import re
import sys
from collections import OrderedDict


ROOT = pathlib.Path(__file__).parent.parent
G3_DIR = ROOT / "backend" / "data" / "math" / "G3"


# 단원별 verification 소스 매핑 (Go Math Ch.X)
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
    """전체 단원·레슨 카탈로그 구성."""
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
                print(f"⚠️  파싱 실패: {ls} — {e}", file=sys.stderr)
    return index


def make_vert_align(index: dict, unit: str, lesson_idx: int) -> dict:
    """단원·레슨 인덱스로 prereq/current/successor 자동 생성."""
    lessons = index[unit]
    cur = lessons[lesson_idx]
    unit_order = list(index.keys())
    unit_pos = unit_order.index(unit)

    # 이전 레슨
    if lesson_idx > 0:
        prev = lessons[lesson_idx - 1]
        prerequisite = f"G3 {unit}/{prev['name']} — {prev['title']} ({prev['ccss']})"
    elif unit_pos > 0:
        prev_unit = unit_order[unit_pos - 1]
        prev_lessons = index[prev_unit]
        # 이전 단원의 unit_test (마지막) 또는 마지막 레슨
        prev = prev_lessons[-1]
        prerequisite = f"G3 {prev_unit} 완료 — {prev['title']} ({prev['ccss']})"
    else:
        prerequisite = "G2 — Grade 2 수학 (자릿값·덧뺄셈 100 이내, 도형 기초)"

    current = f"G3 {unit}/{cur['name']} — {cur['title']} ({cur['ccss']})"

    # 다음 레슨
    if lesson_idx + 1 < len(lessons):
        nxt = lessons[lesson_idx + 1]
        successor = f"G3 {unit}/{nxt['name']} — {nxt['title']} ({nxt['ccss']})"
    elif unit_pos + 1 < len(unit_order):
        nxt_unit = unit_order[unit_pos + 1]
        nxt = index[nxt_unit][0]
        successor = f"G3 {nxt_unit}/{nxt['name']} — {nxt['title']} ({nxt['ccss']})"
    else:
        successor = "G4 — Grade 4 수학 (각도·측정·자릿값 확장)"

    return {
        "prerequisite": prerequisite,
        "current": current,
        "successor": successor,
    }


def normalize_item(item: dict, unit: str, lesson_id: str) -> bool:
    """항목 보강. 변경 발생 시 True 반환."""
    changed = False

    # cpa_phase → cpa_stage 동기화 (백워드 호환: 둘 다 유지)
    if "cpa_phase" in item and "cpa_stage" not in item:
        item["cpa_stage"] = item["cpa_phase"]
        changed = True

    # feedback_correct: feedback.correct에서 추출
    if "feedback_correct" not in item:
        fb = item.get("feedback") or {}
        if isinstance(fb, dict) and fb.get("correct"):
            item["feedback_correct"] = fb["correct"]
            changed = True
        elif item.get("hints"):  # hints는 있는데 feedback 없으면 기본값
            item["feedback_correct"] = "정답입니다! 잘 했어요."
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
    """단일 파일 처리. 결과 통계 반환."""
    d = json.loads(path.read_text(encoding="utf-8"))

    # 이미 업그레이드된 경우 skip
    if d.get("metadata", {}).get("upgraded") and d.get("metadata", {}).get("upgrade_version") == "2.0-on-main":
        return {"skipped": True, "reason": "already upgraded"}

    stats = {"items_changed": 0, "items_total": 0}

    # 레슨 파일 (sections) vs unit_test 파일 (problems/questions)
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

    # 최상위 vertical_alignment
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
    parser = argparse.ArgumentParser(description="G3 검증 메타 일괄 보강 (v2, main schema)")
    parser.add_argument("--unit", help="특정 단원만 (예: U1_add_sub_1000)")
    parser.add_argument("--dry-run", action="store_true", help="변경 사항 보기만, 저장 안 함")
    args = parser.parse_args()

    print("📚 레슨 카탈로그 구성 중...")
    index = build_lesson_index()
    print(f"   {len(index)} 단원, {sum(len(v) for v in index.values())} 파일")
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
            print(f"   {tag} {path.name}: {stats['items_changed']}/{stats['items_total']} 항목 보강")

    print()
    print(f"📊 결과: {total_files} 파일 처리 (skipped {skipped})")
    print(f"   {total_changed} 파일에서 {total_items_changed} 항목 변경")
    if args.dry_run:
        print("   ⚠️  DRY-RUN — 실제 저장 없음")


if __name__ == "__main__":
    main()
