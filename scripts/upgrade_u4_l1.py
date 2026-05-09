"""
G3 U4 L1 — Multiply with 2 and 4 7단계 업그레이드 스크립트
==========================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (×2/×4 — 두 배·두 배의 두 배 전략)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L1_multiply_with_2_and_4.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.C.7.M01"],
    "PT_02": ["3.OA.C.7.M01"],
    "PT_03": ["3.OA.C.7.M01"],
    "PT_04": ["3.OA.C.7.M07"],
    "PT_05": ["3.OA.C.7.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.C.7.M01"],
    "TRY_02": ["3.OA.C.7.M01"],
    "TRY_03": ["3.OA.C.7.M01"],
    "TRY_04": ["3.OA.C.7.M01"],
    "TRY_05": ["3.OA.C.7.M02"],
    "R1_01": ["3.OA.C.7.M01"],
    "R1_02": ["3.OA.C.7.M01"],
    "R1_03": ["3.OA.C.7.M01"],
    "R1_04": ["3.OA.C.7.M01", "3.OA.C.7.M07"],
    "R1_05": ["3.OA.C.7.M01"],
    "R1_06": ["3.OA.C.7.M01"],
    "R1_07": ["3.OA.C.7.M01"],
    "R1_08": ["3.OA.C.7.M01"],
    "R1_09": ["3.OA.C.7.M01"],
    "R1_10": ["3.OA.C.7.M01"],
    "R2_01": ["3.OA.B.5.M03"],
    "R2_02": ["3.OA.C.7.M07"],
    "R2_03": ["3.OA.B.5.M03"],
    "R2_04": ["3.OA.C.7.M02"],
    "R2_05": ["3.OA.C.7.M01"],
    "R2_06": ["3.OA.A.3.M02"],
    "R2_07": ["3.OA.C.7.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.C.7.M07"],
    "R3_02": ["3.OA.C.7.M02"],
    "R3_03": ["3.OA.C.7.M01"],
    "R3_04": ["3.OA.C.7.M01"],
    "R3_05": ["3.OA.C.7.M01"],
}

SKILL_TAGS = {
    "PT_01": "double_for_x2",
    "PT_02": "double_double_for_x4",
    "PT_03": "double_double_for_x4",
    "PT_04": "double_double_for_x4",
    "PT_05": "double_double_for_x4",
    "LEARN_01": "double_for_x2",
    "LEARN_02": "double_double_for_x4",
    "LEARN_03": "skip_count_2_4",
    "LEARN_04": "array_x2_x4",
    "LEARN_05": "build_x4_from_x2",
    "LEARN_06": "double_for_x2",
    "LEARN_07": "double_double_for_x4",
    "LEARN_08": "x2_x4_strategies",
    "TRY_01": "double_for_x2",
    "TRY_02": "double_double_for_x4",
    "TRY_03": "double_for_x2",
    "TRY_04": "double_double_for_x4",
    "TRY_05": "missing_factor_x4",
    "R1_01": "double_for_x2",
    "R1_02": "double_double_for_x4",
    "R1_03": "double_for_x2",
    "R1_04": "double_double_for_x4",
    "R1_05": "double_double_for_x4",
    "R1_06": "double_for_x2",
    "R1_07": "double_for_x2",
    "R1_08": "double_double_for_x4",
    "R1_09": "double_double_for_x4",
    "R1_10": "double_for_x2",
    "R2_01": "decompose_x4",
    "R2_02": "verify_product",
    "R2_03": "decompose_x4",
    "R2_04": "missing_factor_x2",
    "R2_05": "word_problem_x4",
    "R2_06": "array_to_multiplication",
    "R2_07": "skip_count_pattern",
    "R2_08": "compare_products",
    "R2_09": "two_step_x4",
    "R2_10": "build_x4_from_x2",
    "R2_08": "addition_3digit",       # U1 (overrides above)
    "R2_09": "subtraction_3digit",    # U1
    "R2_10": "two_step_add_sub",      # U1
    "R3_01": "two_step_x4",
    "R3_02": "missing_factor_chain",
    "R3_03": "three_step_x4",
    "R3_04": "two_step_x4_half",
    "R3_05": "combined_x2_x4",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
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
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.1 'Multiply with 2 and 4' pp.139-142",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D & Module 3 — Multiplying with Units of 2 and 4",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "double_for_x2")
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
        "title": "×2 = 더블 — '+2'가 아니다!",
        "content": (
            "×2를 만나면 '+2'로 잘못 계산하지 마세요. "
            "×2는 같은 수를 한 번 더 더하는 '더블(double)'입니다. "
            "예: 7 × 2 = 7 + 7 = 14 (NOT 7 + 2 = 9). "
            "흔한 실수: '×2'를 '+2'로 자동 변환 → 7 × 2 = 9. "
            "기억법: '곱하기 2 = 자기 자신을 한 번 더'."
        ),
        "cpa_stage": "concrete",
        "visual_type": "comparison_chart",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×4 = 더블의 더블 — 두 단계로 풀기",
        "content": (
            "×4 사실은 ×2를 두 번 한 것과 같습니다 (×4 = ×2 × ×2). "
            "예: 6 × 4 = 6 × 2 × 2 = 12 × 2 = 24. "
            "단계 1: 다른 인자를 더블 (6 → 12). "
            "단계 2: 그 결과를 또 더블 (12 → 24). "
            "장점: 외울 사실이 줄어듦. ×2만 잘 하면 ×4가 공짜로 따라옴."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_step_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×2·×4 즉답 전략 요약",
        "content": (
            "전략 1: ×2를 보면 → 같은 수를 두 번 더한다 (a + a). "
            "전략 2: ×4를 보면 → 더블의 더블 (a → 2a → 4a). "
            "전략 3: 분배법칙 — 4 × 7 = (2 × 7) + (2 × 7) = 14 + 14 = 28. "
            "전략 4: 미지수 — 2 × ? = 14 → ?는 14의 절반 = 7. "
            "검증: 짝수 × 짝수 = 짝수, 짝수 × 홀수 = 짝수 (×2와 ×4의 답은 항상 짝수)."
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
        "question": "Find the sum: 256 + 387.",
        "choices": ["A. 533", "B. 633", "C. 643", "D. 743"],
        "answer": "C",
        "explanation": "256+387: 6+7=13 (carry 1), 5+8+1=14 (carry 1), 2+3+1=6. Result: 643.",
        "hints": [
            "Two carries.",
            "Ones: 13. Tens: 14. Hundreds: 6.",
        ],
        "feedback": {
            "correct": "Right — 643.",
            "incorrect": "256+387=643.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 504 − 167.",
        "choices": ["A. 327", "B. 337", "C. 347", "D. 437"],
        "answer": "B",
        "explanation": "504−167: 4−7 borrow → 14−7=7; tens 0−6 borrow → 10−7=3 (after lending); hundreds 4−1=3. Result: 337.",
        "hints": [
            "Borrow across the zero in tens.",
            "504−167=337.",
        ],
        "feedback": {
            "correct": "Right — 337.",
            "incorrect": "504−167=337.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A library had 412 books. They lent out 175 books, then bought 238 new books. How many books does the library have now?",
        "choices": ["A. 237", "B. 475", "C. 525", "D. 825"],
        "answer": "B",
        "explanation": "Step 1: 412−175=237. Step 2: 237+238=475.",
        "hints": [
            "Two steps: subtract lent, then add bought.",
            "412−175=237, 237+238=475.",
        ],
        "feedback": {
            "correct": "Right — 475 books.",
            "incorrect": "412−175=237, then +238=475.",
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
        "prerequisite": "G3 U3 — 등량 그룹·반복 덧셈·교환법칙 (3.OA.A.1, 3.OA.B.5)",
        "current":      "G3 — ×2(더블)·×4(더블의 더블) 사실 유창성 (3.OA.C.7)",
        "successor":    "G3 U4 L2 — ×5와 ×10 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
