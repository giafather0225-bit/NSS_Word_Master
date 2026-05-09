"""
G3 U4 L4 — Distributive Property 7단계 업그레이드 스크립트
==========================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.5 (분배법칙으로 곱 분해)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L4_distributive_property.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.B.5.M03"],
    "PT_02": ["3.OA.B.5.M03"],
    "PT_03": ["3.OA.B.5.M03"],
    "PT_04": ["3.OA.B.5.M03"],
    "PT_05": ["3.OA.B.5.M03"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.B.5.M03"],
    "TRY_02": ["3.OA.B.5.M03"],
    "TRY_03": ["3.OA.B.5.M03"],
    "TRY_04": ["3.OA.B.5.M03"],
    "TRY_05": ["3.OA.B.5.M03"],
    "R1_01": ["3.OA.B.5.M03"],
    "R1_02": ["3.OA.B.5.M03"],
    "R1_03": ["3.OA.B.5.M03"],
    "R1_04": ["3.OA.B.5.M03"],
    "R1_05": ["3.OA.B.5.M03"],
    "R1_06": ["3.OA.B.5.M03"],
    "R1_07": ["3.OA.B.5.M03"],
    "R1_08": ["3.OA.B.5.M03"],
    "R1_09": ["3.OA.B.5.M03"],
    "R1_10": ["3.OA.B.5.M03"],
    "R2_01": ["3.OA.B.5.M03"],
    "R2_02": ["3.OA.B.5.M03"],
    "R2_03": ["3.OA.B.5.M03"],
    "R2_04": ["3.OA.B.5.M03"],
    "R2_05": ["3.OA.B.5.M03"],
    "R2_06": ["3.OA.B.5.M03"],
    "R2_07": ["3.OA.B.5.M03"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.B.5.M03"],
    "R3_02": ["3.OA.B.5.M03"],
    "R3_03": ["3.OA.B.5.M03"],
    "R3_04": ["3.OA.B.5.M03"],
    "R3_05": ["3.OA.B.5.M03"],
}

SKILL_TAGS = {
    "PT_01": "distributive_addition",
    "PT_02": "identify_property",
    "PT_03": "distributive_addition",
    "PT_04": "distributive_double",
    "PT_05": "distributive_5_plus_2",
    "LEARN_01": "distributive_definition",
    "LEARN_02": "distributive_array_split",
    "LEARN_03": "choose_break_apart",
    "LEARN_04": "distributive_subtraction",
    "LEARN_05": "area_model",
    "LEARN_06": "distribute_to_both",
    "LEARN_07": "distributive_subtraction",
    "LEARN_08": "distributive_strategies",
    "TRY_01": "distributive_addition",
    "TRY_02": "distributive_addition",
    "TRY_03": "distributive_double",
    "TRY_04": "distributive_subtraction",
    "TRY_05": "multiple_valid_splits",
    "R1_01": "distributive_addition",
    "R1_02": "distributive_addition",
    "R1_03": "distributive_5_plus_3",
    "R1_04": "distributive_5_plus_2",
    "R1_05": "distributive_5_plus_1",
    "R1_06": "distributive_addition",
    "R1_07": "distributive_double",
    "R1_08": "distributive_addition",
    "R1_09": "distributive_addition",
    "R1_10": "distributive_addition",
    "R2_01": "distributive_double",
    "R2_02": "multiple_valid_splits",
    "R2_03": "verify_distributive",
    "R2_04": "missing_split_factor",
    "R2_05": "compute_distributive_sum",
    "R2_06": "identify_split_used",
    "R2_07": "distributive_word_problem",
    "R2_08": "addition_3digit",      # U1
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "distributive_subtraction",
    "R3_02": "distributive_word_problem",
    "R3_03": "distributive_subtraction",
    "R3_04": "distributive_word_problem",
    "R3_05": "distributive_subtraction",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "pictorial",
    "LEARN_06": "concrete", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.4 'Distributive Property' pp.151-154",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Distributive Property and Properties of Multiplication",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "distributive_addition")
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
        "title": "두 부분 모두에 곱하기 — 절대 빠뜨리지 마세요",
        "content": (
            "분배법칙의 가장 흔한 실수: 한 부분만 곱하고 멈추기. "
            "예: 8 × 7 = 8 × (5 + 2). "
            "  ❌ 잘못: 8 × 5 = 40 → 답 40 (8 × 2를 빠뜨림). "
            "  ✅ 올바름: 8 × 5 = 40, 8 × 2 = 16, 40 + 16 = 56. "
            "기억법: 분배(distribute)는 '나눠주다' — 두 부분 모두에 곱셈을 나눠줘야 함. "
            "검증: 두 작은 인자가 원래 인자가 되도록 더해야 함 (5 + 2 = 7)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "distribute_diagram",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "뺄셈 분배법칙 — ×9, ×8 빠른 풀이",
        "content": (
            "곱하기 어려운 큰 수는 ×10에서 빼서 풀기: a × (10 − b) = 10a − ab. "
            "예 — ×9: 7 × 9 = 7 × (10 − 1) = 70 − 7 = 63. "
            "예 — ×8: 6 × 8 = 6 × (10 − 2) = 60 − 12 = 48. "
            "장점: ×10은 항상 쉬우므로, 빼기 한 번이면 끝. "
            "주의: 빼는 수도 정확히 곱해야 함 (7 × 1 = 7, NOT 1)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_step_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "분배법칙 활용 4가지 전략",
        "content": (
            "전략 1 5+a 분해: 8 × 7 = 8 × (5 + 2) = 40 + 16 = 56. "
            "전략 2 더블 분해: 6 × 8 = 6 × (4 + 4) = 24 + 24 = 48. "
            "전략 3 ×10 빼기: 9 × 7 = 9 × (10 − 3) = 90 − 27 = 63. "
            "전략 4 같은 수 둘로: 6 × 14 = 6 × (10 + 4) = 60 + 24 = 84. "
            "핵심: 두 부분이 원래 인자로 더해지면 어떤 분해도 정답. 가장 쉬운 분해를 선택!"
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
        "question": "Find the sum: 478 + 365.",
        "choices": ["A. 743", "B. 833", "C. 843", "D. 943"],
        "answer": "C",
        "explanation": "478+365: 8+5=13 (carry 1), 7+6+1=14 (carry 1), 4+3+1=8. Result: 843.",
        "hints": [
            "Two carries.",
            "Ones: 13. Tens: 14. Hundreds: 8.",
        ],
        "feedback": {
            "correct": "Right — 843.",
            "incorrect": "478+365=843.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 902 − 567.",
        "choices": ["A. 335", "B. 345", "C. 435", "D. 445"],
        "answer": "A",
        "explanation": "902−567: 2−7 borrow → 12−7=5; tens 0−6 borrow → 10−7=3 (after lending); hundreds 8−5=3. Result: 335.",
        "hints": [
            "Borrow across the zero in tens.",
            "902−567=335.",
        ],
        "feedback": {
            "correct": "Right — 335.",
            "incorrect": "902−567=335.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A garden had 624 flowers. The gardener picked 247 and then planted 156 new ones. How many flowers now?",
        "choices": ["A. 221", "B. 533", "C. 715", "D. 1027"],
        "answer": "B",
        "explanation": "Step 1: 624−247=377. Step 2: 377+156=533.",
        "hints": [
            "Subtract picked, then add planted.",
            "624−247=377, 377+156=533.",
        ],
        "feedback": {
            "correct": "Right — 533 flowers.",
            "incorrect": "624−247=377, then +156=533.",
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
        "prerequisite": "G3 U4 L1-L3 — ×2/×4/×5/×10/×3/×6 사실 (3.OA.C.7)",
        "current":      "G3 — 분배법칙으로 큰 곱 분해; 두 부분 모두에 곱하기 (3.OA.B.5)",
        "successor":    "G3 U4 L5 — ×7 사실 (분배법칙 활용; 3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
