"""
G3 U7 L11 — Order of Operations 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.D.8 (연산 순서 — 괄호 → ×÷ → +−)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L11_order_of_operations.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.D.8.M02"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.D.8.M02"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.D.8.M02"] for i in range(1,11)},
    "R2_01": ["3.OA.D.8.M02"],
    "R2_02": ["3.OA.D.8.M02"],
    "R2_03": ["3.OA.D.8.M02"],
    "R2_04": ["3.OA.D.8.M02"],
    "R2_05": ["3.OA.D.8.M02"],
    "R2_06": ["3.OA.D.8.M02"],
    "R2_07": ["3.OA.D.8.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M02"],
    "R3_02": ["3.OA.D.8.M02"],
    "R3_03": ["3.OA.D.8.M02"],
    "R3_04": ["3.OA.D.8.M02"],
    "R3_05": ["3.OA.D.8.M02"],
}

SKILL_TAGS = {
    "PT_01": "multiply_before_add",
    "PT_02": "parentheses_first",
    "PT_03": "divide_before_subtract",
    "PT_04": "parentheses_first",
    "PT_05": "multiply_before_add_subtract",
    "LEARN_01": "order_of_operations_intro",
    "LEARN_02": "multiply_before_add",
    "LEARN_03": "parentheses_change",
    "LEARN_04": "divide_before_subtract",
    "LEARN_05": "label_each_step",
    "LEARN_06": "ooo_routine",
    "LEARN_07": "parentheses_priority",
    "LEARN_08": "ooo_check",
    "TRY_01": "multiply_before_add",
    "TRY_02": "parentheses_first",
    "TRY_03": "divide_before_add",
    "TRY_04": "parentheses_first",
    "TRY_05": "divide_before_subtract",
    "R1_01": "multiply_before_add",
    "R1_02": "multiply_before_subtract",
    "R1_03": "parentheses_first",
    "R1_04": "divide_before_add",
    "R1_05": "multiply_before_subtract",
    "R1_06": "parentheses_first",
    "R1_07": "ooo_word_translation",
    "R1_08": "parentheses_first",
    "R1_09": "divide_before_subtract",
    "R1_10": "multiply_before_add",
    "R2_01": "ooo_three_step",
    "R2_02": "parentheses_then_divide",
    "R2_03": "ooo_match_value",
    "R2_04": "ooo_three_step",
    "R2_05": "multiply_before_subtract",
    "R2_06": "parentheses_first",
    "R2_07": "ooo_match_value",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "add_parentheses",
    "R3_02": "ooo_validate_answer",
    "R3_03": "ooo_compare",
    "R3_04": "add_parentheses",
    "R3_05": "remove_parentheses_compare",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.11 'Order of Operations' pp.305-308",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic G — Order of Operations Without Exponents",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "order_of_operations")
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
        "title": "연산 순서 루틴 — 3단계 우선순위",
        "content": (
            "연산 순서 (3학년판): "
            "  1단계 괄호 ( ) — 가장 먼저. "
            "  2단계 ×와 ÷ — 왼쪽에서 오른쪽으로. "
            "  3단계 +와 − — 왼쪽에서 오른쪽으로. "
            "예: 3 + 2 × 4 → 2×4=8 먼저 → 3+8=11. "
            "예: (3 + 2) × 4 → 괄호 5 먼저 → 5×4=20. "
            "흔한 실수 (M02): 왼쪽부터 차례로만 풀어 3+2=5 → 5×4=20 (잘못 — 정답 11). "
            "팁: 머릿속으로 ×÷ 부분에 동그라미 치기."
        ),
        "cpa_stage": "abstract",
        "visual_type": "ooo_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "괄호의 힘 — 답을 완전히 바꿈",
        "content": (
            "괄호 ( )가 있으면 그 안을 무조건 먼저. "
            "예: 3 + 2 × 4 = 11 (괄호 없음 → 곱셈 먼저). "
            "예: (3 + 2) × 4 = 20 (괄호 → 덧셈 먼저). "
            "같은 숫자·기호인데 답이 다름! "
            "팁: 괄호 표시 = '이걸 먼저 해라'는 명령. "
            "흔한 실수: 괄호 무시하고 표준 순서만 적용."
        ),
        "cpa_stage": "abstract",
        "visual_type": "parentheses_priority",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "단계별 검산 — 한 줄씩 답 옮기기",
        "content": (
            "복잡한 식은 한 단계씩 다음 줄로 옮겨 적기. "
            "예: 3 × (4 + 5) − 7 "
            "  단계 1) 괄호: 4+5 = 9 → 식: 3 × 9 − 7. "
            "  단계 2) 곱셈: 3×9 = 27 → 식: 27 − 7. "
            "  단계 3) 뺄셈: 27 − 7 = 20. "
            "🔍 검증: 각 단계가 정확한지 별도 검산. "
            "흔한 실수 (M02): 머릿속만 의지해 한 단계 빠뜨리거나 순서 뒤바뀜 — 종이에 적기."
        ),
        "cpa_stage": "abstract",
        "visual_type": "ooo_step_by_step",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 467 + 285.",
        "choices": ["A. 642", "B. 652", "C. 742", "D. 752"],
        "answer": "D",
        "explanation": "467+285: 7+5=12 (carry 1), 6+8+1=15 (carry 1), 4+2+1=7. Result: 752.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 12. Tens: 15. Hundreds: 7."],
        "feedback": {"correct": "Right — 752.", "incorrect": "467+285=752."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 802 − 367.",
        "choices": ["A. 435", "B. 445", "C. 535", "D. 545"],
        "answer": "A",
        "explanation": "802−367: 2−7 borrow → 12−7=5; tens 9−6=3 (after lending across zero); hundreds 7−3=4. Result: 435.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "802−367=435."],
        "feedback": {"correct": "Right — 435.", "incorrect": "802−367=435."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 564 books. They donated 178, then bought 245 more. How many books now?",
        "choices": ["A. 386", "B. 487", "C. 631", "D. 743"],
        "answer": "C",
        "explanation": "Step 1: 564−178=386. Step 2: 386+245=631.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add bought.", "564−178=386, 386+245=631."],
        "feedback": {"correct": "Right — 631 books.", "incorrect": "564−178=386, then +245=631."},
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
        "prerequisite": "G3 U7 L10 — 두 단계 문장제 (3.OA.D.8)",
        "current":      "G3 — 연산 순서: 괄호 → ×÷ → +− (3.OA.D.8)",
        "successor":    "G3 U8 L1 — 분수의 의미 (3.NF.A.1)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l11.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
