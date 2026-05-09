"""
G3 U7 L6 — Divide by 6 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (6 나눗셈 사실 — ÷2 → ÷3 분해 / ×6 역연산)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L6_divide_by_6.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.C.7.M02"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.C.7.M02"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.C.7.M02"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.4.M01"],
    "R2_03": ["3.OA.C.7.M02"],
    "R2_04": ["3.OA.A.2.M02"],
    "R2_05": ["3.OA.B.5.M05"],
    "R2_06": ["3.OA.A.4.M01"],
    "R2_07": ["3.OA.C.7.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_02": ["3.OA.D.8.M01", "3.OA.A.4.M01"],
    "R3_03": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_05": ["3.OA.A.4.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "divide_by_6" for i in range(1,6)},
    "LEARN_01": "divide_by_6",
    "LEARN_02": "array_six_rows",
    "LEARN_03": "decompose_div_2_3",
    "LEARN_04": "number_line_jumps_6",
    "LEARN_05": "reverse_times_6",
    "LEARN_06": "decompose_2_3_routine",
    "LEARN_07": "times_6_inverse",
    "LEARN_08": "div_6_check",
    **{f"TRY_0{i}": "divide_by_6" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_6" for i in range(1,11)},
    "R2_01": "divide_by_6_inverse",
    "R2_02": "missing_dividend_6",
    "R2_03": "compare_quotients",
    "R2_04": "rate_division_word",
    "R2_05": "divide_by_self",
    "R2_06": "missing_dividend_6",
    "R2_07": "identify_correct_6_fact",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_multiply",
    "R3_02": "two_step_unknown_factor",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "missing_dividend_6",
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
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.6 'Divide by 6' pp.285-288",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 6",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_6")
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
        "title": "÷2 후 ÷3 루틴 — ÷6 분해 전략",
        "content": (
            "÷6 = ÷2 후 ÷3. 6 = 2 × 3이니까 6으로 나눔 = 2로 나누고 3으로 나눔. "
            "예: 36 ÷ 6 → 36 ÷ 2 = 18 → 18 ÷ 3 = 6 → 답 6. "
            "예: 42 ÷ 6 → 42 ÷ 2 = 21 → 21 ÷ 3 = 7 → 답 7. "
            "단계 1) 절반 구하기 (÷2). "
            "단계 2) 결과를 3으로 나누기 (÷3). "
            "팁: 순서 바꿔도 가능 (먼저 ÷3 후 ÷2). 큰 수에 효과적."
        ),
        "cpa_stage": "abstract",
        "visual_type": "decompose_2_3_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "×6의 역연산 — 곱셈표로 즉답",
        "content": (
            "×6 사실을 알면 ÷6도 즉답. "
            "예: 6 × 7 = 42 → 42 ÷ 6 = 7. "
            "예: 6 × 9 = 54 → 54 ÷ 6 = 9. "
            "사고 절차: 48 ÷ 6 = ? → '몇 × 6 = 48?' → 8. "
            "팁: ×6 사실 = ×5 사실 + 한 번 더 (예: 6×8 = 5×8 + 8 = 40+8 = 48). "
            "흔한 실수 (M02): 6단을 안 외워 스킵 카운트로 시간 낭비."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_6_inverse",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "÷6 검증 — 답 × 6 = 원래 수?",
        "content": (
            "÷6 답을 구한 뒤 검산: 답 × 6 = 원래 수? "
            "예: 48 ÷ 6 = 8 → 검산: 8 × 6 = 48 ✓. "
            "예: 54 ÷ 6 = 9 → 검산: 9 × 6 = 54 ✓. "
            "🔍 검증 기법: 답 × 6 = (답 × 5) + 답 (예: 8×6 = 40+8 = 48). "
            "흔한 실수 (M02): ÷6 답을 외우지 않고 큰 수에서 시간 낭비 — "
            "÷2→÷3 분해 또는 ×6 역연산 둘 다 효과적."
        ),
        "cpa_stage": "abstract",
        "visual_type": "div_6_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 358 + 487.",
        "choices": ["A. 735", "B. 745", "C. 835", "D. 845"],
        "answer": "D",
        "explanation": "358+487: 8+7=15 (carry 1), 5+8+1=14 (carry 1), 3+4+1=8. Result: 845.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 14. Hundreds: 8."],
        "feedback": {"correct": "Right — 845.", "incorrect": "358+487=845."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 803 − 459.",
        "choices": ["A. 344", "B. 354", "C. 444", "D. 454"],
        "answer": "A",
        "explanation": "803−459: 3−9 borrow → 13−9=4; tens 9−5=4 (after lending across zero); hundreds 7−4=3. Result: 344.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "803−459=344."],
        "feedback": {"correct": "Right — 344.", "incorrect": "803−459=344."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bakery had 654 cookies. They sold 248, then baked 175 more. How many cookies now?",
        "choices": ["A. 406", "B. 502", "C. 581", "D. 754"],
        "answer": "C",
        "explanation": "Step 1: 654−248=406. Step 2: 406+175=581.",
        "difficulty": 3,
        "hints": ["Subtract sold, then add baked.", "654−248=406, 406+175=581."],
        "feedback": {"correct": "Right — 581 cookies.", "incorrect": "654−248=406, then +175=581."},
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
        "prerequisite": "G3 U7 L5 — 4 나눗셈: 절반 두 번/×4 역연산 (3.OA.C.7)",
        "current":      "G3 — 6 나눗셈 사실: ÷2→÷3 분해/×6 역연산 (3.OA.C.7)",
        "successor":    "G3 U7 L7 — 7 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l6.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
