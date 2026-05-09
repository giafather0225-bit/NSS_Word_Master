"""
G3 U7 L5 — Divide by 4 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (4 나눗셈 사실 — 절반 두 번 / ×4 역연산)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L5_divide_by_4.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.C.7.M01"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.C.7.M01"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.C.7.M01"] for i in range(1,11)},
    "R2_01": ["3.OA.C.7.M01"],
    "R2_02": ["3.OA.A.2.M06"],
    "R2_03": ["3.OA.A.4.M01"],
    "R2_04": ["3.OA.C.7.M01"],
    "R2_05": ["3.OA.B.5.M05"],
    "R2_06": ["3.OA.A.4.M01"],
    "R2_07": ["3.OA.C.7.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_02": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_03": ["3.OA.D.8.M01", "3.OA.A.4.M01"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_05": ["3.OA.A.4.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "divide_by_4" for i in range(1,6)},
    "LEARN_01": "divide_by_4",
    "LEARN_02": "halve_twice_strategy",
    "LEARN_03": "times_4_inverse",
    "LEARN_04": "number_line_jumps_4",
    "LEARN_05": "reverse_times_4",
    "LEARN_06": "halve_twice_routine",
    "LEARN_07": "times_4_inverse_routine",
    "LEARN_08": "div_4_check",
    **{f"TRY_0{i}": "divide_by_4" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_4" for i in range(1,11)},
    "R2_01": "halve_twice_strategy",
    "R2_02": "divide_by_4_inverse",
    "R2_03": "missing_dividend_4",
    "R2_04": "compare_quotients",
    "R2_05": "divide_by_self",
    "R2_06": "missing_dividend_4",
    "R2_07": "identify_correct_4_fact",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_multiply_x4",
    "R3_02": "two_step_division_subtract",
    "R3_03": "two_step_unknown_factor",
    "R3_04": "two_step_division_subtract",
    "R3_05": "missing_dividend_4",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.5 'Divide by 4' pp.281-284",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 4",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_4")
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
        "title": "절반 두 번 루틴 — ÷4 빠른 전략",
        "content": (
            "÷4 = ÷2 두 번. 4 = 2 × 2이니까 4로 나눔 = 2로 두 번 나눔. "
            "예: 24 ÷ 4 → 24 ÷ 2 = 12 → 12 ÷ 2 = 6 → 답 6. "
            "예: 32 ÷ 4 → 32 ÷ 2 = 16 → 16 ÷ 2 = 8 → 답 8. "
            "단계 1) 첫 번째 절반(÷2). "
            "단계 2) 두 번째 절반(다시 ÷2). "
            "팁: 머릿속에서 두 번 절반 구하기는 한 번 ÷4보다 쉬움."
        ),
        "cpa_stage": "abstract",
        "visual_type": "halve_twice_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "×4의 역연산 — 곱셈표로 즉답",
        "content": (
            "×4 사실을 알면 ÷4도 즉답. "
            "예: 4 × 8 = 32 → 32 ÷ 4 = 8. "
            "예: 4 × 9 = 36 → 36 ÷ 4 = 9. "
            "사고 절차: 28 ÷ 4 = ? → '몇 × 4 = 28?' → 7. "
            "팁: ×4 곱셈표 = ×2 두 번 (4 × 7 = (2 × 7) × 2 = 14 × 2 = 28). "
            "흔한 실수 (M01): 더블 한 번에서 멈춰 답 절반(=14)이라 답 — 두 번 해야 함."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_4_inverse",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "÷4 검증 — 답 × 4 = 원래 수?",
        "content": (
            "÷4 답을 구한 뒤 검산: 답 × 4 = 원래 수? "
            "예: 28 ÷ 4 = 7 → 검산: 7 × 4 = 28 ✓ (= 7 × 2 × 2 = 14 × 2). "
            "예: 36 ÷ 4 = 9 → 검산: 9 × 4 = 36 ✓. "
            "🔍 검증: 답 × 4 = 답 더블의 더블 (예: 9 → 18 → 36). "
            "흔한 실수: 절반 두 번 하면서 한 번 빼먹어 답이 두 배 큼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "div_4_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 459 + 376.",
        "choices": ["A. 725", "B. 735", "C. 825", "D. 835"],
        "answer": "D",
        "explanation": "459+376: 9+6=15 (carry 1), 5+7+1=13 (carry 1), 4+3+1=8. Result: 835.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 13. Hundreds: 8."],
        "feedback": {"correct": "Right — 835.", "incorrect": "459+376=835."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 802 − 348.",
        "choices": ["A. 454", "B. 464", "C. 554", "D. 564"],
        "answer": "A",
        "explanation": "802−348: 2−8 borrow → 12−8=4; tens 9−4=5 (after lending across zero); hundreds 7−3=4. Result: 454.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "802−348=454."],
        "feedback": {"correct": "Right — 454.", "incorrect": "802−348=454."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 537 books. They donated 168, then bought 245 more. How many books now?",
        "choices": ["A. 369", "B. 482", "C. 614", "D. 734"],
        "answer": "C",
        "explanation": "Step 1: 537−168=369. Step 2: 369+245=614.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add bought.", "537−168=369, 369+245=614."],
        "feedback": {"correct": "Right — 614 books.", "incorrect": "537−168=369, then +245=614."},
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
        "prerequisite": "G3 U7 L4 — 3 나눗셈: ×3 역연산/스킵 카운트 (3.OA.C.7)",
        "current":      "G3 — 4 나눗셈 사실: 절반 두 번/×4 역연산 (3.OA.C.7)",
        "successor":    "G3 U7 L6 — 6 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
