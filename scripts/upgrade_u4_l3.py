"""
G3 U4 L3 — Multiply with 3 and 6 7단계 업그레이드 스크립트
==========================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (×3 — 3번 더하기, ×6 — ×3 더블)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L3_multiply_with_3_and_6.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.C.7.M02"],
    "PT_02": ["3.OA.C.7.M07"],
    "PT_03": ["3.OA.C.7.M02"],
    "PT_04": ["3.OA.C.7.M02"],
    "PT_05": ["3.OA.C.7.M02"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.C.7.M02"],
    "TRY_02": ["3.OA.C.7.M02"],
    "TRY_03": ["3.OA.C.7.M02"],
    "TRY_04": ["3.OA.C.7.M02"],
    "TRY_05": ["3.OA.C.7.M02"],
    "R1_01": ["3.OA.C.7.M02"],
    "R1_02": ["3.OA.C.7.M07"],
    "R1_03": ["3.OA.C.7.M02"],
    "R1_04": ["3.OA.C.7.M02"],
    "R1_05": ["3.OA.C.7.M07"],
    "R1_06": ["3.OA.C.7.M02"],
    "R1_07": ["3.OA.C.7.M02"],
    "R1_08": ["3.OA.C.7.M07"],
    "R1_09": ["3.OA.C.7.M02"],
    "R1_10": ["3.OA.C.7.M02"],
    "R2_01": ["3.OA.C.7.M02"],
    "R2_02": ["3.OA.C.7.M02"],
    "R2_03": ["3.OA.B.5.M03"],
    "R2_04": ["3.OA.C.7.M02"],
    "R2_05": ["3.OA.C.7.M02"],
    "R2_06": ["3.OA.C.7.M02"],
    "R2_07": ["3.OA.C.7.M07"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.C.7.M02"],
    "R3_02": ["3.OA.B.5.M03"],
    "R3_03": ["3.OA.C.7.M02"],
    "R3_04": ["3.OA.C.7.M02"],
    "R3_05": ["3.OA.C.7.M02"],
}

SKILL_TAGS = {
    "PT_01": "x3_skip_count",
    "PT_02": "x6_double_x3",
    "PT_03": "x3_skip_count",
    "PT_04": "x6_double_x3",
    "PT_05": "x6_double_x3",
    "LEARN_01": "x3_skip_count",
    "LEARN_02": "x6_double_x3",
    "LEARN_03": "x6_skip_count",
    "LEARN_04": "array_x3_x6",
    "LEARN_05": "split_6_into_3_plus_3",
    "LEARN_06": "x3_skip_count",
    "LEARN_07": "x6_double_x3",
    "LEARN_08": "x3_x6_strategies",
    "TRY_01": "x3_skip_count",
    "TRY_02": "x6_double_x3",
    "TRY_03": "x6_double_x3",
    "TRY_04": "x6_word_problem",
    "TRY_05": "missing_factor_x3",
    "R1_01": "x3_skip_count",
    "R1_02": "x6_double_x3",
    "R1_03": "x3_skip_count",
    "R1_04": "x6_double_x3",
    "R1_05": "x3_skip_count",
    "R1_06": "x3_skip_count",
    "R1_07": "x6_double_x3",
    "R1_08": "x3_skip_count",
    "R1_09": "x6_double_x3",
    "R1_10": "x3_skip_count",
    "R2_01": "missing_factor_chain",
    "R2_02": "x6_word_problem",
    "R2_03": "split_6_into_3_plus_3",
    "R2_04": "missing_factor_x3",
    "R2_05": "skip_count_pattern_x3",
    "R2_06": "missing_factor_x6",
    "R2_07": "compare_x3_x6",
    "R2_08": "addition_3digit",       # U1
    "R2_09": "subtraction_3digit",    # U1
    "R2_10": "two_step_add_sub",      # U1
    "R3_01": "three_step_x3_x6",
    "R3_02": "split_6_into_3_plus_3",
    "R3_03": "two_step_x6",
    "R3_04": "combined_x3_x6",
    "R3_05": "missing_factor_chain",
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
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.3 'Multiply with 3 and 6' pp.147-150",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic E & Module 3 — Multiplying with Units of 3 and 6",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "x3_skip_count")
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
        "title": "×3 — 손가락 추적으로 미스카운트 방지",
        "content": (
            "×3 사실은 건너뛰기 셈으로 풀지만, 6번~9번 점프에서 자주 미스카운트. "
            "방지법: 손가락 하나에 한 번 점프 — 손가락 개수 = 다른 인자. "
            "예: 3 × 7 → 손가락 7개 펴고 '3, 6, 9, 12, 15, 18, 21' (각 손가락마다). "
            "검증: 손가락 다 폈을 때의 마지막 값이 답. "
            "흔한 실수: 한 번 더 (4×8=27 대신 24) 또는 한 번 덜 (3×7=18 대신 21)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "finger_tracking",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×6 = ×3 더블 (가장 빠른 방법)",
        "content": (
            "6 = 2 × 3이므로, ×6 = ×3 결과를 두 배. "
            "예: 6 × 7 = (3 × 7) × 2 = 21 × 2 = 42. "
            "단계 1: ×3을 먼저 (이미 외운 사실 사용). "
            "단계 2: 그 결과를 더블. "
            "장점: ×6 사실을 따로 외울 필요 없음. ×3만 알면 ×6도 즉답. "
            "다른 방법: ×6 = ×5 + ×1 (예: 6×7 = 5×7 + 7 = 35+7 = 42)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_step_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×3·×6 즉답 전략 요약",
        "content": (
            "전략 1 ×3 = 3번 더하기: a + a + a. "
            "전략 2 ×6 = ×3 더블: 6 × n = 2 × (3 × n). "
            "전략 3 분배법칙 — 6 × n = 3 × n + 3 × n. "
            "전략 4 ×6 = ×5 + ×1 (×5 강한 학생용): 6 × 8 = 40 + 8 = 48. "
            "검증: ×3 곱은 항상 3의 배수. ×6 곱은 짝수 (6 = 2 × 3이므로)."
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
        "question": "Find the sum: 367 + 248.",
        "choices": ["A. 505", "B. 515", "C. 605", "D. 615"],
        "answer": "D",
        "explanation": "367+248: 7+8=15 (carry 1), 6+4+1=11 (carry 1), 3+2+1=6. Result: 615.",
        "hints": [
            "Two carries needed.",
            "Ones: 15. Tens: 11. Hundreds: 6.",
        ],
        "feedback": {
            "correct": "Right — 615.",
            "incorrect": "367+248=615.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 803 − 416.",
        "choices": ["A. 387", "B. 397", "C. 487", "D. 497"],
        "answer": "A",
        "explanation": "803−416: 3−6 borrow → 13−6=7; tens 0−1 borrow → 10−2=8 (after lending); hundreds 7−4=3. Result: 387.",
        "hints": [
            "Borrow across the zero in tens.",
            "803−416=387.",
        ],
        "feedback": {
            "correct": "Right — 387.",
            "incorrect": "803−416=387.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A school had 524 markers. Students used 187, then the school bought 256 more. How many markers now?",
        "choices": ["A. 337", "B. 481", "C. 593", "D. 967"],
        "answer": "C",
        "explanation": "Step 1: 524−187=337. Step 2: 337+256=593.",
        "hints": [
            "Subtract used, then add bought.",
            "524−187=337, 337+256=593.",
        ],
        "feedback": {
            "correct": "Right — 593 markers.",
            "incorrect": "524−187=337, then +256=593.",
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
        "prerequisite": "G3 U4 L1-L2 — ×2/×4/×5/×10 사실 (3.OA.C.7)",
        "current":      "G3 — ×3(건너뛰기)·×6(×3 더블) 사실 유창성 (3.OA.C.7)",
        "successor":    "G3 U4 L4 — 분배법칙으로 더 큰 곱 분해 (3.OA.B.5)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
