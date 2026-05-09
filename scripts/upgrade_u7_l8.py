"""
G3 U7 L8 — Divide by 8 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (8 나눗셈 사실 — 절반 세 번 / ×8 역연산)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L8_divide_by_8.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.C.7.M06"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.C.7.M06"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.C.7.M06"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.4.M01"],
    "R2_03": ["3.OA.C.7.M06"],
    "R2_04": ["3.OA.A.2.M02"],
    "R2_05": ["3.OA.B.5.M05"],
    "R2_06": ["3.OA.A.4.M01"],
    "R2_07": ["3.OA.C.7.M06"],
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
    **{f"PT_0{i}": "divide_by_8" for i in range(1,6)},
    "LEARN_01": "divide_by_8",
    "LEARN_02": "halve_three_times_strategy",
    "LEARN_03": "array_eight_rows",
    "LEARN_04": "number_line_jumps_8",
    "LEARN_05": "reverse_times_8",
    "LEARN_06": "halve_three_times_routine",
    "LEARN_07": "times_8_inverse",
    "LEARN_08": "div_8_check",
    **{f"TRY_0{i}": "divide_by_8" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_8" for i in range(1,11)},
    "R2_01": "divide_by_8_inverse",
    "R2_02": "missing_dividend_8",
    "R2_03": "compare_quotients",
    "R2_04": "rate_division_word",
    "R2_05": "divide_by_self",
    "R2_06": "missing_dividend_8",
    "R2_07": "identify_correct_8_fact",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_with_money",
    "R3_02": "two_step_unknown_factor",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "missing_dividend_8",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "abstract", "LEARN_03": "pictorial",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.8 'Divide by 8' pp.293-296",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 8",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_8")
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
        "title": "절반 세 번 루틴 — ÷8 핵심 전략",
        "content": (
            "÷8 = ÷2 세 번. 8 = 2 × 2 × 2이니까 8로 나눔 = 2로 세 번 나눔. "
            "예: 56 ÷ 8 → 56 ÷ 2 = 28 → 28 ÷ 2 = 14 → 14 ÷ 2 = 7 → 답 7. "
            "예: 64 ÷ 8 → 64 ÷ 2 = 32 → 32 ÷ 2 = 16 → 16 ÷ 2 = 8 → 답 8. "
            "단계 1) 첫 번째 절반(÷2). "
            "단계 2) 두 번째 절반(다시 ÷2). "
            "단계 3) 세 번째 절반(또다시 ÷2). "
            "흔한 실수 (M06): 두 번에서 멈춰 답이 두 배 큼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "halve_three_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "×8의 역연산 — 더블의 더블의 더블",
        "content": (
            "×8 = (×2) 세 번 = 더블의 더블의 더블. "
            "예: 56 ÷ 8 = ? → '몇 × 8 = 56?' → 7 (왜냐: 7→14→28→56 더블 세 번). "
            "예: 72 ÷ 8 = ? → '몇 × 8 = 72?' → 9 (9→18→36→72). "
            "사고 절차: 64 ÷ 8 = ? → 64 ÷ 2 ÷ 2 ÷ 2 = 32 → 16 → 8. "
            "팁: 더블 세 번이 곱셈 사실로 자연스럽게 외워지면 즉답."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_8_inverse",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "÷8 검증 — 답 × 8 = 원래 수?",
        "content": (
            "÷8 답을 구한 뒤 검산: 답 × 8 = 원래 수? "
            "예: 56 ÷ 8 = 7 → 검산: 7 × 8 = 56 ✓ (= 7 × 2 × 2 × 2 = 14 × 2 × 2 = 28 × 2). "
            "예: 64 ÷ 8 = 8 → 검산: 8 × 8 = 64 ✓ (정사각형 사실). "
            "🔍 검증 기법: 답 × 8 = 답 더블의 더블의 더블 (예: 7→14→28→56). "
            "흔한 실수 (M06): 절반 세 번 하다가 한 번 빼먹어 답이 두 배 큼 — 끝까지 셋 번 확실히."
        ),
        "cpa_stage": "abstract",
        "visual_type": "div_8_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 567 + 286.",
        "choices": ["A. 743", "B. 753", "C. 843", "D. 853"],
        "answer": "D",
        "explanation": "567+286: 7+6=13 (carry 1), 6+8+1=15 (carry 1), 5+2+1=8. Result: 853.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 13. Tens: 15. Hundreds: 8."],
        "feedback": {"correct": "Right — 853.", "incorrect": "567+286=853."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 906 − 479.",
        "choices": ["A. 427", "B. 437", "C. 527", "D. 537"],
        "answer": "A",
        "explanation": "906−479: 6−9 borrow → 16−9=7; tens 9−7=2 (after lending across zero); hundreds 8−4=4. Result: 427.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "906−479=427."],
        "feedback": {"correct": "Right — 427.", "incorrect": "906−479=427."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 728 books. They donated 256, then bought 184 more. How many books now?",
        "choices": ["A. 472", "B. 528", "C. 656", "D. 800"],
        "answer": "C",
        "explanation": "Step 1: 728−256=472. Step 2: 472+184=656.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add bought.", "728−256=472, 472+184=656."],
        "feedback": {"correct": "Right — 656 books.", "incorrect": "728−256=472, then +184=656."},
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
        "prerequisite": "G3 U7 L7 — 7 나눗셈: ×7 역연산/7=5+2 분해 (3.OA.C.7)",
        "current":      "G3 — 8 나눗셈 사실: 절반 세 번/×8 역연산 (3.OA.C.7)",
        "successor":    "G3 U7 L9 — 9 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l8.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
