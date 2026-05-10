"""
G3 U11 L1 — Tell Time to Nearest Minute 검증 메타 정합화
==============================================================================
이미 43문항 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5) 구조 보유.
보강: cpa_stage(=cpa_phase 동기화), verification 3소스 dict, math_note,
feedback_correct, vertical_alignment, metadata.upgraded.
표준: 3.MD.A.1 (시간 — 가장 가까운 분까지 읽기)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U11_time_mass_volume/L1_tell_time_nearest_minute.json"


def make_verification(item_id: str, original: str = "") -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Lesson 10.1 'Time to the Minute'",
        "procedure_source": "EngageNY Grade 3 Module 2 Topic A — Time Measurement",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
        "original_ref": original,
    }


def normalize_item(item: dict) -> dict:
    if "cpa_phase" in item and "cpa_stage" not in item:
        item["cpa_stage"] = item["cpa_phase"]
    item.setdefault("math_note", "")
    if (item.get("hints") or item.get("feedback")) and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            (item.get("feedback") or {}).get("correct")
            or "정답입니다! 잘 했어요."
        )
    orig_ver = item.get("verification") if isinstance(item.get("verification"), str) else ""
    item["verification"] = make_verification(item["id"], orig_ver)
    return item


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("metadata", {}).get("upgraded"):
        print("⚠️  이미 업그레이드됨.")
        return

    sections = ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"]
    counts = {}
    for k in sections:
        d[k] = [normalize_item(it) for it in d.get(k, [])]
        counts[k] = len(d[k])

    expected = {"pretest":5, "learn":8, "try":5, "practice_r1":10, "practice_r2":10, "practice_r3":5}
    print("섹션별:", counts)
    assert counts == expected, f"카운트 불일치: {counts}"

    # ID uniqueness
    all_ids = [it["id"] for k in sections for it in d[k]]
    assert len(all_ids) == len(set(all_ids)), "ID 중복"

    d["vertical_alignment"] = {
        "prerequisite": "G3 U10 — 둘레 (3.MD.D.8)",
        "current":      "G3 U11 L1 — 시간 읽기: 가장 가까운 분까지 (3.MD.A.1)",
        "successor":    "G3 U11 L2 — 경과 시간 수직선 (3.MD.A.1)",
    }
    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u11_l1.py"

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
