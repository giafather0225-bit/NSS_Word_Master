"""
G3 U4 L2 — Multiply with 5 and 10 7단계 업그레이드 스크립트
============================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (×5/×10 — 끝자리 패턴, ×5는 ×10의 절반)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L2_multiply_with_5_and_10.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.C.7.M03"],
    "PT_02": ["3.OA.C.7.M07"],
    "PT_03": ["3.OA.C.7.M03"],
    "PT_04": ["3.OA.C.7.M07"],
    "PT_05": ["3.OA.C.7.M03"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.C.7.M07"],
    "TRY_02": ["3.OA.C.7.M03"],
    "TRY_03": ["3.OA.C.7.M07"],
    "TRY_04": ["3.OA.C.7.M02"],
    "TRY_05": ["3.OA.C.7.M07"],
    "R1_01": ["3.OA.C.7.M03"],
    "R1_02": ["3.OA.C.7.M07"],
    "R1_03": ["3.OA.C.7.M03"],
    "R1_04": ["3.OA.C.7.M07"],
    "R1_05": ["3.OA.C.7.M03"],
    "R1_06": ["3.OA.C.7.M07"],
    "R1_07": ["3.OA.C.7.M03"],
    "R1_08": ["3.OA.C.7.M07"],
    "R1_09": ["3.OA.C.7.M03"],
    "R1_10": ["3.OA.C.7.M07"],
    "R2_01": ["3.OA.C.7.M03"],
    "R2_02": ["3.OA.C.7.M07"],
    "R2_03": ["3.OA.C.7.M03"],
    "R2_04": ["3.OA.C.7.M02"],
    "R2_05": ["3.OA.C.7.M02"],
    "R2_06": ["3.OA.C.7.M07"],
    "R2_07": ["3.OA.C.7.M03"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.C.7.M03", "3.OA.C.7.M07"],
    "R3_02": ["3.OA.C.7.M03"],
    "R3_03": ["3.OA.C.7.M07"],
    "R3_04": ["3.OA.C.7.M03"],
    "R3_05": ["3.OA.C.7.M07"],
}

SKILL_TAGS = {
    "PT_01": "x5_pattern",
    "PT_02": "x10_pattern",
    "PT_03": "x5_pattern",
    "PT_04": "x10_pattern",
    "PT_05": "x5_pattern",
    "LEARN_01": "x5_end_digit",
    "LEARN_02": "x10_zero_attach",
    "LEARN_03": "x5_half_of_x10",
    "LEARN_04": "array_x5_x10",
    "LEARN_05": "money_x5_x10",
    "LEARN_06": "x5_pattern_rule",
    "LEARN_07": "x10_zero_attach",
    "LEARN_08": "x5_x10_strategies",
    "TRY_01": "x10_zero_attach",
    "TRY_02": "x5_half_of_x10",
    "TRY_03": "x10_word_problem",
    "TRY_04": "missing_factor_x5",
    "TRY_05": "x10_word_problem",
    "R1_01": "x5_pattern",
    "R1_02": "x10_zero_attach",
    "R1_03": "x5_half_of_x10",
    "R1_04": "x10_zero_attach",
    "R1_05": "x5_pattern",
    "R1_06": "x10_zero_attach",
    "R1_07": "x5_pattern",
    "R1_08": "x10_zero_attach",
    "R1_09": "x5_pattern",
    "R1_10": "x10_zero_attach",
    "R2_01": "verify_x5_pattern",
    "R2_02": "verify_x10_pattern",
    "R2_03": "x5_half_of_x10",
    "R2_04": "missing_factor_x5",
    "R2_05": "skip_count_pattern_x5",
    "R2_06": "missing_factor_x10",
    "R2_07": "compare_x5_x10",
    "R2_08": "addition_3digit",        # U1
    "R2_09": "subtraction_3digit",     # U1
    "R2_10": "two_step_add_sub",       # U1
    "R3_01": "two_step_combined",
    "R3_02": "missing_factor_chain",
    "R3_03": "two_step_x5_x10",
    "R3_04": "money_combined",
    "R3_05": "two_step_x5_x10",
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
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.2 'Multiply with 5 and 10' pp.143-146",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D & Module 3 — Multiplying with Units of 5 and 10",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "x5_pattern")
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
        "title": "×5 끝자리 규칙 — 0 또는 5",
        "content": (
            "×5 곱은 항상 0 또는 5로 끝납니다. "
            "짝수 × 5 → 0으로 끝남 (예: 6 × 5 = 30, 8 × 5 = 40). "
            "홀수 × 5 → 5로 끝남 (예: 7 × 5 = 35, 9 × 5 = 45). "
            "또 다른 빠른 방법: 다른 인자의 절반을 십의 자리, 그리고 0(짝수) 또는 5(홀수)를 일의 자리에. "
            "흔한 실수: 끝자리는 맞추지만 십의 자리를 잘못 넣음 (예: 6×5=35로 답)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "rule_card",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×10은 단순히 0 붙이기",
        "content": (
            "×10의 가장 빠른 방법: 다른 인자 뒤에 0을 한 개 붙이기. "
            "예: 10 × 7 = 70, 10 × 9 = 90. "
            "이 규칙은 1자리 수에 한해 항상 작동 (10진법의 마법). "
            "거꾸로도: 10 × ? = 90 → 90에서 0을 떼면 9가 미지수. "
            "주의: 모든 0이 끝나는 수가 ×10 곱은 아님 (예: 80은 ×10이 맞지만 70도, 90도 모두 ×10임)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "shortcut_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×5·×10 즉답 전략 요약",
        "content": (
            "전략 1 ×10 = 0 붙이기: 10 × n = n0. "
            "전략 2 ×5 = ×10의 절반: 5 × n = (10 × n) ÷ 2. "
            "  예: 5 × 8 → 10 × 8 = 80 → 80 ÷ 2 = 40. "
            "전략 3 끝자리 점검: 짝수×5는 0, 홀수×5는 5로 끝. "
            "전략 4 동전 모델: nickel=5¢, dime=10¢. "
            "  6 nickels = 30¢, 6 dimes = 60¢ — dime은 nickel의 두 배."
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
        "question": "Find the sum: 463 + 158.",
        "choices": ["A. 511", "B. 521", "C. 611", "D. 621"],
        "answer": "D",
        "explanation": "463+158: 3+8=11 (carry 1), 6+5+1=12 (carry 1), 4+1+1=6. Result: 621.",
        "hints": [
            "Two carries.",
            "Ones: 11. Tens: 12. Hundreds: 6.",
        ],
        "feedback": {
            "correct": "Right — 621.",
            "incorrect": "463+158=621.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 821 − 467.",
        "choices": ["A. 354", "B. 364", "C. 444", "D. 454"],
        "answer": "A",
        "explanation": "821−467: 1−7 borrow → 11−7=4; tens 1−6 borrow → 11−6=5; hundreds 7−4=3. Result: 354.",
        "hints": [
            "Two borrows.",
            "821−467=354.",
        ],
        "feedback": {
            "correct": "Right — 354.",
            "incorrect": "821−467=354.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A bakery had 348 cookies. They sold 169, then baked 285 more. How many cookies now?",
        "choices": ["A. 248", "B. 364", "C. 464", "D. 802"],
        "answer": "C",
        "explanation": "Step 1: 348−169=179. Step 2: 179+285=464.",
        "hints": [
            "Two steps: subtract sold, then add baked.",
            "348−169=179, 179+285=464.",
        ],
        "feedback": {
            "correct": "Right — 464 cookies.",
            "incorrect": "348−169=179, then +285=464.",
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
        "prerequisite": "G3 U4 L1 — ×2/×4 더블 전략 (3.OA.C.7)",
        "current":      "G3 — ×5(끝자리 0/5)·×10(0 붙이기) 사실 유창성 (3.OA.C.7)",
        "successor":    "G3 U4 L3 — ×3/×6 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
