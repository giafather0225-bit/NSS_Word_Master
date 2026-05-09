"""
G3 U7 L3 — Divide by 5 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (5 나눗셈 사실 — 5의 패턴, 니켈 전략)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L3_divide_by_5.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.C.7.M03"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.C.7.M03"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.C.7.M03"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.4.M01"],
    "R2_03": ["3.OA.C.7.M01"],
    "R2_04": ["3.OA.C.7.M03"],
    "R2_05": ["3.OA.A.4.M01"],
    "R2_06": ["3.OA.C.7.M03"],
    "R2_07": ["3.OA.A.4.M01"],
    "R2_08": ["3.OA.A.2.M02"],
    "R2_09": ["3.OA.A.2.M06"],
    "R2_10": ["3.OA.A.2.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_02": ["3.OA.A.2.M02"],
    "R3_03": ["3.OA.D.8.M01", "3.OA.A.4.M01"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_05": ["3.OA.A.4.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "divide_by_5" for i in range(1,6)},
    "LEARN_01": "divide_by_5",
    "LEARN_02": "use_times_5_facts",
    "LEARN_03": "nickels_strategy",
    "LEARN_04": "number_line_divide_5",
    "LEARN_05": "five_pattern_division",
    "LEARN_06": "halve_then_tenth",
    "LEARN_07": "times_5_inverse",
    "LEARN_08": "five_pattern_check",
    **{f"TRY_0{i}": "divide_by_5" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_5" for i in range(1,11)},
    "R2_01": "divide_by_5_inverse",
    "R2_02": "missing_dividend_5",
    "R2_03": "compare_quotients_5",
    "R2_04": "nickels_division",
    "R2_05": "divide_by_5_inverse",
    "R2_06": "identify_correct_5_fact",
    "R2_07": "missing_dividend_5",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_with_money",
    "R3_02": "rate_division_word",
    "R3_03": "two_step_unknown_factor",
    "R3_04": "two_step_division_combine",
    "R3_05": "missing_dividend_5",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "concrete",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.3 'Divide by 5' pp.273-276",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 5",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_5")
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
        "title": "÷10 한 다음 × 2 — ÷5 빠른 전략",
        "content": (
            "÷5 = ÷10 한 다음 × 2 (반대도 가능: × 2 한 다음 ÷ 10). "
            "예: 30 ÷ 5 → 30 ÷ 10 = 3 → 3 × 2 = 6. "
            "예: 45 ÷ 5 → 45 ÷ 10 (조금 어렵지만) ≈ 4.5 → × 2 = 9. "
            "왜? 10 = 5 × 2이니까 ÷10은 ÷5의 두 배 뺀 것. "
            "다른 전략: ×5 사실(5×9=45)을 알면 즉답 (45÷5=9)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "halve_tenth_strategy",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "×5의 역연산 — 끝자리 0/5 패턴",
        "content": (
            "÷5 사실은 끝자리가 0 또는 5인 수에 적용: "
            "  10, 15, 20, 25, 30, 35, 40, 45, 50… (5의 배수). "
            "예: 35 ÷ 5 = ? → '몇 × 5 = 35?' → 7. "
            "예: 50 ÷ 5 = ? → '몇 × 5 = 50?' → 10. "
            "팁: 5 × 짝수 = 끝 0, 5 × 홀수 = 끝 5. "
            "흔한 실수 (M03): 5의 패턴을 이해 못 하고 다른 곱셈 사실로 시도."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_5_pattern",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "5의 패턴 검증 — 끝자리로 빠른 점검",
        "content": (
            "÷5의 답은 항상 정수 (피제수가 5의 배수일 때). "
            "검증: 답 × 5 = 원래 수? "
            "예: 35 ÷ 5 = 7 → 7 × 5 = 35 ✓. "
            "예: 45 ÷ 5 = 9 → 9 × 5 = 45 ✓. "
            "🔍 패턴 확인: 답 × 5 끝자리는 0(답 짝수일 때) 또는 5(답 홀수일 때). "
            "흔한 실수 (M03): 30 ÷ 5 = 5 (답 6과 헷갈림) — 곱셈 검산으로 잡기."
        ),
        "cpa_stage": "abstract",
        "visual_type": "five_pattern_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 376 + 458.",
        "choices": ["A. 724", "B. 734", "C. 824", "D. 834"],
        "answer": "D",
        "explanation": "376+458: 6+8=14 (carry 1), 7+5+1=13 (carry 1), 3+4+1=8. Result: 834.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 14. Tens: 13. Hundreds: 8."],
        "feedback": {"correct": "Right — 834.", "incorrect": "376+458=834."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 803 − 367.",
        "choices": ["A. 436", "B. 446", "C. 536", "D. 546"],
        "answer": "A",
        "explanation": "803−367: 3−7 borrow → 13−7=6; tens 9−6=3 (after lending across zero); hundreds 7−3=4. Result: 436.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "803−367=436."],
        "feedback": {"correct": "Right — 436.", "incorrect": "803−367=436."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 538 books. They donated 175, then bought 217 more. How many books now?",
        "choices": ["A. 363", "B. 470", "C. 580", "D. 755"],
        "answer": "C",
        "explanation": "Step 1: 538−175=363. Step 2: 363+217=580.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add bought.", "538−175=363, 363+217=580."],
        "feedback": {"correct": "Right — 580 books.", "incorrect": "538−175=363, then +217=580."},
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
        "prerequisite": "G3 U7 L2 — 10 나눗셈: 0 떼기 전략 (3.OA.C.7)",
        "current":      "G3 — 5 나눗셈 사실: 5의 패턴/니켈 전략 (3.OA.C.7)",
        "successor":    "G3 U7 L4 — 3 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
