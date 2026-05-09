"""
G3 U4 L8 — Multiply with 8 7단계 업그레이드 스크립트
====================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (×8 — double-double-double, ×4 더블, ×10−×2)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L8_multiply_with_8.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.C.7.M06"],
    "PT_02": ["3.OA.C.7.M06"],
    "PT_03": ["3.OA.C.7.M06"],
    "PT_04": ["3.OA.C.7.M06"],
    "PT_05": ["3.OA.C.7.M06", "3.OA.C.7.M07"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.C.7.M06"],
    "TRY_02": ["3.OA.C.7.M06"],
    "TRY_03": ["3.OA.C.7.M06"],
    "TRY_04": ["3.OA.C.7.M06"],
    "TRY_05": ["3.OA.C.7.M07"],
    "R1_01": ["3.OA.C.7.M01"],
    "R1_02": ["3.OA.C.7.M06"],
    "R1_03": ["3.OA.C.7.M03"],
    "R1_04": ["3.OA.B.5.M05"],
    "R1_05": ["3.OA.C.7.M06"],
    "R1_06": ["3.OA.C.7.M06"],
    "R1_07": ["3.OA.B.5.M01"],
    "R1_08": ["3.OA.C.7.M06"],
    "R1_09": ["3.OA.C.7.M06"],
    "R1_10": ["3.OA.B.5.M06"],
    "R2_01": ["3.OA.C.7.M06"],
    "R2_02": ["3.OA.C.7.M06"],
    "R2_03": ["3.OA.C.7.M06"],
    "R2_04": ["3.OA.B.5.M03"],
    "R2_05": ["3.OA.C.7.M03"],
    "R2_06": ["3.OA.C.7.M06"],
    "R2_07": ["3.OA.C.7.M06"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.C.7.M06"],
    "R3_02": ["3.OA.C.7.M06"],
    "R3_03": ["3.OA.B.5.M03"],
    "R3_04": ["3.OA.C.7.M06"],
    "R3_05": ["3.OA.C.7.M06"],
}

SKILL_TAGS = {
    "PT_01": "x8_double_x4",
    "PT_02": "x8_with_x5",
    "PT_03": "x8_double_x4",
    "PT_04": "x8_squared",
    "PT_05": "x8_decompose",
    "LEARN_01": "x8_skip_count",
    "LEARN_02": "x8_double_x4",
    "LEARN_03": "double_double_double",
    "LEARN_04": "x8_array",
    "LEARN_05": "x8_real_world",
    "LEARN_06": "double_double_double",
    "LEARN_07": "x8_decompose",
    "LEARN_08": "x8_strategies",
    "TRY_01": "x8_double_x4",
    "TRY_02": "x8_double_x4",
    "TRY_03": "double_double_double",
    "TRY_04": "x8_word_problem",
    "TRY_05": "x8_one_more_group",
    "R1_01": "x8_with_x2",
    "R1_02": "x8_double_x4",
    "R1_03": "x8_with_x10",
    "R1_04": "x8_with_x1",
    "R1_05": "x8_double_x4",
    "R1_06": "x8_with_x9",
    "R1_07": "x8_commutative",
    "R1_08": "x8_squared",
    "R1_09": "x8_identify_product",
    "R1_10": "x8_with_x0",
    "R2_01": "x8_word_problem",
    "R2_02": "missing_factor_x8",
    "R2_03": "x8_decompose",
    "R2_04": "best_split_x8",
    "R2_05": "x8_with_x5_pattern",
    "R2_06": "x8_squared",
    "R2_07": "missing_factor_x8",
    "R2_08": "identify_x8_decomposition",
    "R2_09": "x8_decompose",
    "R2_10": "associative_x8",
    "R2_08": "addition_3digit",      # U1 (override)
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "two_step_x8",
    "R3_02": "two_step_x8",
    "R3_03": "distributive_x8_subtraction",
    "R3_04": "two_step_x8_word",
    "R3_05": "combined_x8_x4",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "concrete", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.8 'Multiply with 8' pp.167-170",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic E — Multiplying with the Unit of 8",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def add_item_fields(item: dict) -> dict:
    item_id = item["id"]
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "x8_double_x4")
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )
    item["expected_errors"] = ERRORS_MAP.get(item_id, [])
    item.setdefault("math_note", "")
    item["verification"] = make_verification(item_id)
    return item


NEW_LEARN_CARDS = [
    {
        "id": "LEARN_06",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "Double-Double-Double — ×8 가장 강력한 전략",
        "content": (
            "8 = 2 × 2 × 2이므로 ×8 = 더블 세 번. "
            "예: 8 × 6 = 6 → 12 → 24 → 48 (더블 3회). "
            "단계: 다른 인자 a를 골라 — 더블(2a) → 더블(4a) → 더블(8a). "
            "장점: 작은 더블 3번이 큰 ×8 한 번보다 정확함. "
            "예: 8 × 7 = 7 → 14 → 28 → 56. "
            "흔한 실수: 두 번만 더블해서 ×4 답 (28)을 ×8 답으로 잘못 보고."
        ),
        "cpa_stage": "concrete",
        "visual_type": "triple_double_diagram",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×8 = ×10 − ×2 (큰 수에 빠른 방법)",
        "content": (
            "9에 가까운 큰 수와 곱할 때: 8 = 10 − 2 분해. "
            "예: 8 × 9 = 9 × (10 − 2) = 90 − 18 = 72. "
            "예: 8 × 7 = 7 × (10 − 2) = 70 − 14 = 56. "
            "장점: ×10은 즉답, ×2는 더블이라 둘 다 쉬움. "
            "검증: 두 부분 모두 빼야 함 (분배법칙) — 한 부분만 빼면 오류."
        ),
        "cpa_stage": "abstract",
        "visual_type": "decomposition_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×8 즉답 전략 4가지",
        "content": (
            "전략 1 더블의 더블의 더블: a → 2a → 4a → 8a. "
            "전략 2 ×4 더블: 8 × n = 2 × (4 × n). 예 8×7 = 2×28 = 56. "
            "전략 3 ×10 빼기: 8 × n = 10n − 2n. 예 8×9 = 90−18 = 72. "
            "전략 4 분해 5+3: 8 × 7 = (5×7) + (3×7) = 35+21 = 56. "
            "검증: ×8 곱은 항상 8의 배수, 짝수, 끝자리가 0/2/4/6/8 중 하나."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]

U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the sum: 386 + 459.",
        "choices": ["A. 745", "B. 825", "C. 845", "D. 945"],
        "answer": "C",
        "explanation": "386+459: 6+9=15 (carry 1), 8+5+1=14 (carry 1), 3+4+1=8. Result: 845.",
        "hints": [
            "Two carries.",
            "Ones: 15. Tens: 14. Hundreds: 8.",
        ],
        "feedback": {
            "correct": "Right — 845.",
            "incorrect": "386+459=845.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 712 − 364.",
        "choices": ["A. 348", "B. 358", "C. 448", "D. 458"],
        "answer": "A",
        "explanation": "712−364: 2−4 borrow → 12−4=8; tens 0−6 borrow → 10−6=4 (after lending); hundreds 6−3=3. Result: 348.",
        "hints": [
            "Borrow across the zero in tens.",
            "712−364=348.",
        ],
        "feedback": {
            "correct": "Right — 348.",
            "incorrect": "712−364=348.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A factory had 567 boxes. They shipped 248 boxes, then received 195 more. How many boxes now?",
        "choices": ["A. 319", "B. 433", "C. 514", "D. 762"],
        "answer": "C",
        "explanation": "Step 1: 567−248=319. Step 2: 319+195=514.",
        "hints": [
            "Subtract shipped, then add received.",
            "567−248=319, 319+195=514.",
        ],
        "feedback": {
            "correct": "Right — 514 boxes.",
            "incorrect": "567−248=319, then +195=514.",
        },
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "pretest" in d:
        print("⚠️  이미 업그레이드됨.")
        return

    raw_items = d.pop("items", [])
    for item in raw_items:
        if item["id"].startswith("LN_"):
            item["id"] = f"LEARN_{item['id'][3:]}"

    sections_map: dict = {
        "pretest": [], "learn": [], "try": [],
        "practice_r1": [], "practice_r2": [], "practice_r3": [],
    }
    for item in raw_items:
        sec = item.get("section", "")
        if sec in sections_map:
            sections_map[sec].append(item)

    sections_map["learn"].extend(NEW_LEARN_CARDS)
    r2_keep = {f"R2_0{i}" for i in range(1,8)}
    sections_map["practice_r2"] = [i for i in sections_map["practice_r2"] if i["id"] in r2_keep]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key, items in sections_map.items():
        sections_map[sec_key] = [add_item_fields(item) for item in items]

    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U4 L1-L7 — ×2~×7, 분배·결합법칙, 곱셈표 패턴 (3.OA.C.7, 3.OA.B.5, 3.OA.D.9)",
        "current":      "G3 — ×8 사실 (double-double-double, ×4 더블, ×10−×2) (3.OA.C.7)",
        "successor":    "G3 U4 L9 — ×9 사실 (자릿수 합 9 패턴) (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l8.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
