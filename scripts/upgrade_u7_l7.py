"""
G3 U7 L7 — Divide by 7 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (7 나눗셈 사실 — ×7 역연산 / 일주일 패턴)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L7_divide_by_7.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.C.7.M05"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.C.7.M05"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.C.7.M05"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.4.M01"],
    "R2_03": ["3.OA.C.7.M05"],
    "R2_04": ["3.OA.A.2.M02"],
    "R2_05": ["3.OA.B.5.M05"],
    "R2_06": ["3.OA.A.4.M01"],
    "R2_07": ["3.OA.C.7.M05"],
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
    **{f"PT_0{i}": "divide_by_7" for i in range(1,6)},
    "LEARN_01": "divide_by_7",
    "LEARN_02": "array_seven_rows",
    "LEARN_03": "days_weeks",
    "LEARN_04": "number_line_jumps_7",
    "LEARN_05": "reverse_times_7",
    "LEARN_06": "times_7_inverse",
    "LEARN_07": "seven_decompose_5_2",
    "LEARN_08": "div_7_check",
    **{f"TRY_0{i}": "divide_by_7" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_7" for i in range(1,11)},
    "R2_01": "divide_by_7_inverse",
    "R2_02": "missing_dividend_7",
    "R2_03": "compare_quotients",
    "R2_04": "days_weeks_division",
    "R2_05": "divide_by_self",
    "R2_06": "missing_dividend_7",
    "R2_07": "identify_correct_7_fact",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_count",
    "R3_02": "two_step_unknown_factor",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "missing_dividend_7",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "concrete",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.7 'Divide by 7' pp.289-292",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 7",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_7")
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
        "title": "×7의 역연산 — 가장 어려운 단의 해법",
        "content": (
            "÷7은 가장 까다로운 나눗셈. 핵심: ×7 사실을 곱셈표에서 즉답. "
            "예: 56 ÷ 7 = ? → '몇 × 7 = 56?' → 8. "
            "예: 63 ÷ 7 = ? → '몇 × 7 = 63?' → 9. "
            "권장: 7단 곱셈표를 따로 외우기 (7×3=21, 7×4=28, 7×6=42, 7×7=49, 7×8=56, 7×9=63). "
            "흔한 실수 (M05): 7단을 잘 모르고 답을 추측."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_7_inverse",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "7 = 5 + 2 분해 — 어려울 때 백업",
        "content": (
            "7단을 까먹었을 때: 7 = 5 + 2로 분해. "
            "예: 56 ÷ 7 풀려면 ×7 사실 필요 → 7 × 8 = ? → (5 × 8) + (2 × 8) = 40 + 16 = 56 ✓ → 답 8. "
            "예: 7 × 9 = (5 × 9) + (2 × 9) = 45 + 18 = 63 → 63 ÷ 7 = 9. "
            "팁: ×5와 ×2는 쉬우니 둘을 합쳐 7 만들기. "
            "느리지만 항상 정답."
        ),
        "cpa_stage": "abstract",
        "visual_type": "seven_decompose_5_2",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "÷7 검증 — 답 × 7 = 원래 수?",
        "content": (
            "÷7 답을 구한 뒤 검산: 답 × 7 = 원래 수? "
            "예: 56 ÷ 7 = 8 → 검산: 8 × 7 = 56 ✓. "
            "예: 49 ÷ 7 = 7 → 검산: 7 × 7 = 49 ✓ (정사각형 사실). "
            "🔍 검증 기법: 답 × 7 = (답 × 5) + (답 × 2) — 분해 검산. "
            "흔한 실수 (M05): 7단 추측해서 답 적고 검산 빠뜨림 — "
            "반드시 곱셈으로 확인."
        ),
        "cpa_stage": "abstract",
        "visual_type": "div_7_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 478 + 365.",
        "choices": ["A. 743", "B. 753", "C. 833", "D. 843"],
        "answer": "D",
        "explanation": "478+365: 8+5=13 (carry 1), 7+6+1=14 (carry 1), 4+3+1=8. Result: 843.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 13. Tens: 14. Hundreds: 8."],
        "feedback": {"correct": "Right — 843.", "incorrect": "478+365=843."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 705 − 357.",
        "choices": ["A. 348", "B. 358", "C. 448", "D. 458"],
        "answer": "A",
        "explanation": "705−357: 5−7 borrow → 15−7=8; tens 9−5=4 (after lending across zero); hundreds 6−3=3. Result: 348.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "705−357=348."],
        "feedback": {"correct": "Right — 348.", "incorrect": "705−357=348."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A class had 528 stickers. They gave out 175, then bought 248 more. How many stickers now?",
        "choices": ["A. 353", "B. 458", "C. 601", "D. 753"],
        "answer": "C",
        "explanation": "Step 1: 528−175=353. Step 2: 353+248=601.",
        "difficulty": 3,
        "hints": ["Subtract given out, then add bought.", "528−175=353, 353+248=601."],
        "feedback": {"correct": "Right — 601 stickers.", "incorrect": "528−175=353, then +248=601."},
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
        "prerequisite": "G3 U7 L6 — 6 나눗셈: ÷2→÷3 분해/×6 역연산 (3.OA.C.7)",
        "current":      "G3 — 7 나눗셈 사실: ×7 역연산/7=5+2 분해 (3.OA.C.7)",
        "successor":    "G3 U7 L8 — 8 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l7.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
