"""
G3 U7 L4 — Divide by 3 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (3 나눗셈 사실 — ×3 역연산 / 9의 자릿수 합 패턴)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L4_divide_by_3.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.A.2.M06"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.A.2.M06"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.A.2.M06"] for i in range(1,11)},
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
    **{f"PT_0{i}": "divide_by_3" for i in range(1,6)},
    "LEARN_01": "divide_by_3",
    "LEARN_02": "array_three_rows",
    "LEARN_03": "distribute_three",
    "LEARN_04": "number_line_jumps_3",
    "LEARN_05": "reverse_times_3",
    "LEARN_06": "times_3_inverse",
    "LEARN_07": "skip_count_3_division",
    "LEARN_08": "divide_by_3_check",
    **{f"TRY_0{i}": "divide_by_3" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_3" for i in range(1,11)},
    "R2_01": "divide_by_3_inverse",
    "R2_02": "missing_dividend_3",
    "R2_03": "compare_quotients",
    "R2_04": "rate_division_word",
    "R2_05": "divide_by_self",
    "R2_06": "missing_dividend_3",
    "R2_07": "identify_correct_3_fact",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_subtract",
    "R3_02": "two_step_unknown_factor",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "missing_dividend_3",
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
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.4 'Divide by 3' pp.277-280",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 3",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_3")
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
        "title": "×3의 역연산 — ÷3는 곱셈으로 즉답",
        "content": (
            "÷3 풀려면 ×3 사실을 곱셈으로 사고. "
            "예: 24 ÷ 3 = ? → '몇 × 3 = 24?' → 8. "
            "예: 27 ÷ 3 = ? → '몇 × 3 = 27?' → 9. "
            "팁: ×3 곱셈표를 떠올려 24 위치에서 짝꿍 인수 8 찾기. "
            "흔한 실수 (M06): 곱셈으로 풀 줄 알면서 다시 그림 그림."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_3_inverse",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "3씩 스킵 카운트 — 작은 수에서 효과적",
        "content": (
            "÷3 사실을 까먹었을 때 백업: 3씩 세기. "
            "예: 18 ÷ 3 → 3, 6, 9, 12, 15, 18 → 6번 → 답 6. "
            "예: 21 ÷ 3 → 3, 6, 9, 12, 15, 18, 21 → 7번 → 답 7. "
            "팁: 손가락으로 한 번씩 세기 (한 번 = 3씩). "
            "단점: 큰 수(예 30 ÷ 3)에는 시간이 많이 걸림 — 곱셈 사실 외우는 게 빠름."
        ),
        "cpa_stage": "abstract",
        "visual_type": "skip_count_3",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "÷3 검증 — 답 × 3 = 원래 수?",
        "content": (
            "÷3 답을 구한 뒤 검산: 답 × 3 = 원래 수? "
            "예: 21 ÷ 3 = 7 → 검산: 7 × 3 = 21 ✓. "
            "예: 30 ÷ 3 = 10 → 검산: 10 × 3 = 30 ✓. "
            "🔍 검증: 답 × 3은 머릿속 더블 + 한 번 더 더하기. "
            "  예: 7 × 3 = (7 × 2) + 7 = 14 + 7 = 21. "
            "흔한 실수: 답을 외워놓고도 곱셈 검산 빠뜨림."
        ),
        "cpa_stage": "abstract",
        "visual_type": "div_3_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 487 + 376.",
        "choices": ["A. 753", "B. 763", "C. 853", "D. 863"],
        "answer": "D",
        "explanation": "487+376: 7+6=13 (carry 1), 8+7+1=16 (carry 1), 4+3+1=8. Result: 863.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 13. Tens: 16. Hundreds: 8."],
        "feedback": {"correct": "Right — 863.", "incorrect": "487+376=863."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 705 − 268.",
        "choices": ["A. 437", "B. 447", "C. 537", "D. 547"],
        "answer": "A",
        "explanation": "705−268: 5−8 borrow → 15−8=7; tens 9−6=3 (after lending across zero); hundreds 6−2=4. Result: 437.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "705−268=437."],
        "feedback": {"correct": "Right — 437.", "incorrect": "705−268=437."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 614 erasers. They gave out 287, then bought 158 more. How many erasers now?",
        "choices": ["A. 327", "B. 412", "C. 485", "D. 743"],
        "answer": "C",
        "explanation": "Step 1: 614−287=327. Step 2: 327+158=485.",
        "difficulty": 3,
        "hints": ["Subtract given out, then add bought.", "614−287=327, 327+158=485."],
        "feedback": {"correct": "Right — 485 erasers.", "incorrect": "614−287=327, then +158=485."},
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
        "prerequisite": "G3 U7 L3 — 5 나눗셈: 5의 패턴/니켈 (3.OA.C.7)",
        "current":      "G3 — 3 나눗셈 사실: ×3 역연산/스킵 카운트 (3.OA.C.7)",
        "successor":    "G3 U7 L5 — 4 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
