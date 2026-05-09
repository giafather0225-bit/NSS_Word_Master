"""
G3 U5 L5 — Multiply 1-Digit Numbers by Multiples of 10 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NBT.A.3 (한 자리 × 10의 배수 — 결정판)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U5_use_multiplication_facts/L5_multiply_1digit_by_multiples_of_10.json"

ERRORS_MAP = {
    "PT_01": ["3.NBT.A.3.M01"],
    "PT_02": ["3.NBT.A.3.M06"],
    "PT_03": ["3.NBT.A.3.M01"],
    "PT_04": ["3.NBT.A.3.M01"],
    "PT_05": ["3.NBT.A.3.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.NBT.A.3.M06"],
    "TRY_02": ["3.NBT.A.3.M01"],
    "TRY_03": ["3.NBT.A.3.M01"],
    "TRY_04": ["3.NBT.A.3.M04"],
    "TRY_05": ["3.NBT.A.3.M01"],
    "R1_01": ["3.NBT.A.3.M06"],
    "R1_02": ["3.NBT.A.3.M06"],
    "R1_03": ["3.NBT.A.3.M06"],
    "R1_04": ["3.NBT.A.3.M06"],
    "R1_05": ["3.NBT.A.3.M01"],
    "R1_06": ["3.NBT.A.3.M01"],
    "R1_07": ["3.NBT.A.3.M04"],
    "R1_08": ["3.NBT.A.3.M01"],
    "R1_09": ["3.NBT.A.3.M01"],
    "R1_10": ["3.NBT.A.3.M01"],
    "R2_01": ["3.NBT.A.3.M01"],
    "R2_02": ["3.NBT.A.3.M06"],
    "R2_03": ["3.NBT.A.3.M02"],
    "R2_04": ["3.NBT.A.3.M01"],
    "R2_05": ["3.NBT.A.3.M01"],
    "R2_06": ["3.NBT.A.3.M01"],
    "R2_07": ["3.NBT.A.3.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.NBT.A.3.M01"],
    "R3_02": ["3.OA.D.8.M01", "3.NBT.A.3.M01"],
    "R3_03": ["3.OA.A.4.M01", "3.NBT.A.3.M01"],
    "R3_04": ["3.OA.D.8.M01", "3.NBT.A.3.M05"],
    "R3_05": ["3.NBT.A.3.M01"],
}

SKILL_TAGS = {
    "PT_01": "x_multiple_of_10",
    "PT_02": "x_multiple_of_10_left",
    "PT_03": "rate_x10_word",
    "PT_04": "rate_x10_word",
    "PT_05": "rate_x10_word",
    "LEARN_01": "base_ten_blocks",
    "LEARN_02": "basic_fact_place_value",
    "LEARN_03": "vertical_format_x10",
    "LEARN_04": "drawing_base_ten_rods",
    "LEARN_05": "estimation_check_x10",
    "LEARN_06": "zero_attach_routine",
    "LEARN_07": "x10_position_flexibility",
    "LEARN_08": "x10_self_check",
    "TRY_01": "x_multiple_of_10_left",
    "TRY_02": "rate_x10_word",
    "TRY_03": "x_multiple_of_10",
    "TRY_04": "x_multiple_of_10",
    "TRY_05": "rate_x10_word",
    "R1_01": "x_multiple_of_10_left",
    "R1_02": "x_multiple_of_10_left",
    "R1_03": "x_multiple_of_10_left",
    "R1_04": "x_multiple_of_10_left",
    "R1_05": "x_multiple_of_10",
    "R1_06": "x_multiple_of_10",
    "R1_07": "x_multiple_of_10",
    "R1_08": "x_multiple_of_10",
    "R1_09": "rate_x10_word",
    "R1_10": "x_multiple_of_10_left",
    "R2_01": "x_multiple_of_10",
    "R2_02": "compare_x10_products",
    "R2_03": "identify_equal_products",
    "R2_04": "rate_x10_word",
    "R2_05": "x_multiple_of_10",
    "R2_06": "compare_x10_products",
    "R2_07": "x_multiple_of_10",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_x10_combine",
    "R3_02": "two_step_x10_subtract",
    "R3_03": "missing_factor_x10",
    "R3_04": "two_step_x10_subtract",
    "R3_05": "rate_x10_word",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.5 Lesson 5.5 'Multiply 1-Digit Numbers by Multiples of 10' pp.205-208",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic G — Multiplication of Single-Digit Factors and Multiples of 10",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_item(item: dict) -> dict:
    item_id = item["id"]
    if item_id.startswith("LN_"):
        item_id = f"LEARN_{item_id[3:]}"
        item["id"] = item_id
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "x_multiple_of_10")
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
        "type": "concept_card",
        "title": "0 붙이기 루틴 — 가장 빠른 방법",
        "content": (
            "한 자리 × 10의 배수는 두 단계만 거치면 끝: "
            "단계 1) 10의 배수에서 0을 잠시 떼어 기본 사실 계산 — 7 × 80 → 7 × 8 = 56. "
            "단계 2) 떼어둔 0을 답 끝에 다시 붙임 — 56 → 560. "
            "왜 작동하나? 80 = 8 × 10이니까 7 × 80 = 7 × 8 × 10 = 56 × 10 = 560. "
            "흔한 실수 (M01): 0을 다시 붙이지 않아 56이라 답 → 10배 작음. "
            "흔한 실수 (M02): 0을 두 개 붙여 5,600이라 답 → 10배 큼. "
            "팁: '한 자리 곱하기 두 자리(0 끝) → 답은 세 자리(끝 0 1개).'"
        ),
        "cpa_stage": "abstract",
        "visual_type": "zero_attach_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "위치는 무관 — 60 × 7 도 7 × 60 처럼 풀기",
        "content": (
            "10의 배수가 왼쪽이든 오른쪽이든 같은 답: 60 × 7 = 7 × 60 = 420. "
            "전략: 10의 배수를 항상 오른쪽으로 옮긴 뒤 0 붙이기 루틴 적용. "
            "예 1) 60 × 7 → 7 × 60 → 7 × 6 = 42 → 420. "
            "예 2) 90 × 4 → 4 × 90 → 4 × 9 = 36 → 360. "
            "흔한 실수 (M06): 60 × 7과 7 × 60을 다른 문제로 보고 한쪽만 풀 줄 앎 — "
            "교환법칙 한 번 더 떠올리세요."
        ),
        "cpa_stage": "abstract",
        "visual_type": "commutative_x10",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "스스로 검증 — 답이 맞는지 3가지 방법",
        "content": (
            "방법 1 자릿수 점검: 한 자리 × 10의 배수 → 답은 보통 세 자리. "
            "  예: 8 × 70 = 560 (3자리 ✓), 8 × 70 = 56 ❌ 또는 5,600 ❌. "
            "방법 2 어림셈: 9 × 70 ≈ 10 × 70 = 700, 그래서 답은 700보다 약간 작은 630. "
            "방법 3 기본 사실 재확인: 7 × 8 = 56이 맞는지 곱셈표로 검산 (M04 예방). "
            "🔍 검증: 어림셈 ± 10% 안에 답이 들어가는지 항상 확인."
        ),
        "cpa_stage": "abstract",
        "visual_type": "self_check_strategy",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 376 + 489.",
        "choices": ["A. 755", "B. 765", "C. 855", "D. 865"],
        "answer": "D",
        "explanation": "376+489: 6+9=15 (carry 1), 7+8+1=16 (carry 1), 3+4+1=8. Result: 865.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 16. Hundreds: 8."],
        "feedback": {"correct": "Right — 865.", "incorrect": "376+489=865."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 612 − 248.",
        "choices": ["A. 364", "B. 374", "C. 464", "D. 474"],
        "answer": "A",
        "explanation": "612−248: 2−8 borrow → 12−8=4; tens 0−4 borrow → 10−4=6; hundreds 5−2=3. Result: 364.",
        "difficulty": 2,
        "hints": ["Two borrows.", "612−248=364."],
        "feedback": {"correct": "Right — 364.", "incorrect": "612−248=364."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 547 books. They donated 189 and received 235 new ones. How many books now?",
        "choices": ["A. 358", "B. 593", "C. 736", "D. 971"],
        "answer": "B",
        "explanation": "Step 1: 547−189=358. Step 2: 358+235=593.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add received.", "547−189=358, 358+235=593."],
        "feedback": {"correct": "Right — 593 books.", "incorrect": "547−189=358, then +235=593."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 새 7단계 표준으로 업그레이드됨.")
        return

    sections_map = {
        "pretest": d.get("pretest", []),
        "learn": d.get("learn", []),
        "try": d.get("try", []),
        "practice_r1": d.get("practice_r1", []),
        "practice_r2": d.get("practice_r2", []),
        "practice_r3": d.get("practice_r3", []),
    }

    learn_ids = {i["id"].replace("LN_","LEARN_") for i in sections_map["learn"]}
    for new_card in NEW_LEARN_CARDS:
        if new_card["id"] not in learn_ids:
            sections_map["learn"].append(new_card)

    sections_map["practice_r2"] = sections_map["practice_r2"][:7]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key in sections_map:
        sections_map[sec_key] = [normalize_item(it) for it in sections_map[sec_key]]

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
        "prerequisite": "G3 U5 L4 — 10의 배수 곱셈 결합법칙 전략 (3.NBT.A.3)",
        "current":      "G3 — 한 자리 × 10의 배수 결정판: 0 붙이기·자릿값 검산 (3.NBT.A.3)",
        "successor":    "G3 U6 L1 — 나눗셈의 의미 (3.OA.A.2 / 3.OA.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u5_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
