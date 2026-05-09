"""
G3 U7 L2 — Divide by 10 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (10 나눗셈 사실 — '0 떼기' 전략)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L2_divide_by_10.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NBT.A.3.M01"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.NBT.A.3.M01"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NBT.A.3.M01"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.4.M01"],
    "R2_03": ["3.OA.C.7.M01"],
    "R2_04": ["3.NBT.A.3.M01"],
    "R2_05": ["3.OA.A.4.M01"],
    "R2_06": ["3.NBT.A.3.M01"],
    "R2_07": ["3.OA.A.4.M01"],
    "R2_08": ["3.NBT.A.3.M01"],
    "R2_09": ["3.OA.A.2.M06"],
    "R2_10": ["3.OA.D.8.M01", "3.OA.A.4.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.NBT.A.3.M01"],
    "R3_02": ["3.NBT.A.3.M01"],
    "R3_03": ["3.OA.D.8.M01", "3.NBT.A.3.M01"],
    "R3_04": ["3.OA.D.8.M01", "3.NBT.A.3.M01"],
    "R3_05": ["3.OA.A.4.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "divide_by_10" for i in range(1,6)},
    "LEARN_01": "divide_by_10",
    "LEARN_02": "use_times_10_facts",
    "LEARN_03": "skip_count_back_10",
    "LEARN_04": "number_line_divide_10",
    "LEARN_05": "drop_zero_rule",
    "LEARN_06": "drop_zero_routine",
    "LEARN_07": "times_10_inverse",
    "LEARN_08": "place_value_check_10",
    **{f"TRY_0{i}": "divide_by_10" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_10" for i in range(1,11)},
    "R2_01": "divide_by_10_inverse",
    "R2_02": "missing_dividend_10",
    "R2_03": "compare_quotients_10",
    "R2_04": "rate_division_word",
    "R2_05": "divide_by_10_inverse",
    "R2_06": "divide_by_10",
    "R2_07": "missing_dividend_10",
    "R2_08": "identify_quotient_10",
    "R2_09": "divide_by_10_inverse",
    "R2_10": "rate_division_word",
    "R3_01": "two_step_division_subtract",
    "R3_02": "divide_by_10_pattern",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "missing_dividend_10",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.2 'Divide by 10' pp.269-272",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 10",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_10")
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
        "title": "0 떼기 루틴 — ÷10은 끝 0 떼기",
        "content": (
            "10의 배수를 10으로 나누면 끝의 0 한 개를 떼면 답. "
            "예: 30 ÷ 10 = 3 (30에서 0 떼면 3). "
            "예: 80 ÷ 10 = 8, 100 ÷ 10 = 10. "
            "왜 작동? 30 = 3 × 10이니까 30 ÷ 10 = 3. "
            "단계 1) 끝자리가 0인지 확인 (이번 단원은 모두 0). "
            "단계 2) 끝 0 한 개만 떼면 답. "
            "흔한 실수 (M01): 0을 안 떼고 30이라 답하거나 두 개 떼서 0이라 답."
        ),
        "cpa_stage": "abstract",
        "visual_type": "drop_zero_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "×10의 역연산 — 곱셈 알면 즉답",
        "content": (
            "×10 사실을 알면 ÷10도 즉답. "
            "예: 10 × 6 = 60 → 60 ÷ 10 = 6. "
            "예: 10 × 9 = 90 → 90 ÷ 10 = 9. "
            "사고 절차: 60 ÷ 10 = ? → '몇 × 10 = 60?' → 6. "
            "팁: ×10 사실 = 한 자리 곱셈에 0 한 개 더한 것 (3×10=30). "
            "역으로 ÷10은 그 0을 다시 떼는 것."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_10_inverse",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "자릿값 검산 — 답 × 10 = 원래 수?",
        "content": (
            "÷10 답을 구한 뒤 검산: 답 × 10 = 원래 수? "
            "예: 70 ÷ 10 = 7 → 검산: 7 × 10 = 70 ✓. "
            "예: 100 ÷ 10 = 10 → 검산: 10 × 10 = 100 ✓. "
            "🔍 검증: 답 한 자리(또는 두 자리) → 곱 두 자리(또는 세 자리)인지 확인. "
            "흔한 실수 (M01): 60 ÷ 10 = 60(0 안 뗌) 또는 = 0(두 자리 다 뗌) — "
            "정답은 끝 0 정확히 한 개만 떼는 것."
        ),
        "cpa_stage": "abstract",
        "visual_type": "place_value_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 547 + 386.",
        "choices": ["A. 823", "B. 833", "C. 923", "D. 933"],
        "answer": "D",
        "explanation": "547+386: 7+6=13 (carry 1), 4+8+1=13 (carry 1), 5+3+1=9. Result: 933.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 13. Tens: 13. Hundreds: 9."],
        "feedback": {"correct": "Right — 933.", "incorrect": "547+386=933."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 604 − 247.",
        "choices": ["A. 357", "B. 367", "C. 457", "D. 467"],
        "answer": "A",
        "explanation": "604−247: 4−7 borrow → 14−7=7; tens 9−4=5 (after lending across zero); hundreds 5−2=3. Result: 357.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "604−247=357."],
        "feedback": {"correct": "Right — 357.", "incorrect": "604−247=357."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A store had 482 candles. They sold 167, then bought 295 more. How many candles now?",
        "choices": ["A. 315", "B. 482", "C. 610", "D. 944"],
        "answer": "C",
        "explanation": "Step 1: 482−167=315. Step 2: 315+295=610.",
        "difficulty": 3,
        "hints": ["Subtract sold, then add bought.", "482−167=315, 315+295=610."],
        "feedback": {"correct": "Right — 610 candles.", "incorrect": "482−167=315, then +295=610."},
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
        "prerequisite": "G3 U7 L1 — 2 나눗셈 사실: 절반/더블 (3.OA.C.7)",
        "current":      "G3 — 10 나눗셈 사실: 0 떼기 전략 (3.OA.C.7)",
        "successor":    "G3 U7 L3 — 5 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
