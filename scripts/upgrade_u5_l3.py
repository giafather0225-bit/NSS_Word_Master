"""
G3 U5 L3 — Use Distributive Property 7단계 재마이그레이션
==========================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.5, 3.NBT.A.3 (분배법칙으로 큰 수 곱셈)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U5_use_multiplication_facts/L3_use_distributive_property.json"

ERRORS_MAP = {
    "PT_01": ["3.NBT.A.3.M01"],
    "PT_02": ["3.NBT.A.3.M01"],
    "PT_03": ["3.NBT.A.3.M01"],
    "PT_04": ["3.NBT.A.3.M01"],
    "PT_05": ["3.NBT.A.3.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.NBT.A.3.M01"],
    "TRY_02": ["3.OA.A.4.M02"],
    "TRY_03": ["3.OA.B.5.M03"],
    "TRY_04": ["3.NBT.A.3.M01"],
    "TRY_05": ["3.OA.B.5.M03"],
    "R1_01": ["3.NBT.A.3.M01"],
    "R1_02": ["3.NBT.A.3.M01"],
    "R1_03": ["3.NBT.A.3.M01"],
    "R1_04": ["3.NBT.A.3.M01"],
    "R1_05": ["3.NBT.A.3.M01"],
    "R1_06": ["3.NBT.A.3.M01"],
    "R1_07": ["3.NBT.A.3.M01"],
    "R1_08": ["3.NBT.A.3.M01"],
    "R1_09": ["3.NBT.A.3.M01"],
    "R1_10": ["3.NBT.A.3.M01"],
    "R2_01": ["3.OA.A.1.M01"],
    "R2_02": ["3.OA.B.5.M03"],
    "R2_03": ["3.NBT.A.3.M01"],
    "R2_04": ["3.OA.B.5.M03"],
    "R2_05": ["3.NBT.A.3.M01"],
    "R2_06": ["3.OA.B.5.M03"],
    "R2_07": ["3.NBT.A.3.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.B.5.M03"],
    "R3_02": ["3.OA.D.8.M01"],
    "R3_03": ["3.NBT.A.3.M02"],
    "R3_04": ["3.OA.B.5.M03"],
    "R3_05": ["3.NBT.A.3.M01"],
}

SKILL_TAGS = {
    "PT_01": "x_multiple_of_10",
    "PT_02": "rate_x10_word",
    "PT_03": "rate_x10_word",
    "PT_04": "rate_x10_word",
    "PT_05": "rate_x10_word",
    "LEARN_01": "x_multiple_of_10_concept",
    "LEARN_02": "place_value_strategy",
    "LEARN_03": "distributive_with_multiples",
    "LEARN_04": "split_multiple",
    "LEARN_05": "verify_x10",
    "LEARN_06": "x_multiple_of_10_concept",
    "LEARN_07": "distributive_with_multiples",
    "LEARN_08": "x10_strategies",
    "TRY_01": "x_multiple_of_10",
    "TRY_02": "x10_word_division_inverse",
    "TRY_03": "distributive_with_multiples",
    "TRY_04": "x_multiple_of_10",
    "TRY_05": "distributive_chain",
    "R1_01": "x_multiple_of_10",
    "R1_02": "x_multiple_of_10",
    "R1_03": "x_multiple_of_10",
    "R1_04": "x_multiple_of_10",
    "R1_05": "rate_x10_word",
    "R1_06": "rate_x10_word",
    "R1_07": "x_multiple_of_10",
    "R1_08": "x_multiple_of_10",
    "R1_09": "x_multiple_of_10",
    "R1_10": "rate_x10_word",
    "R2_01": "repeated_addition",
    "R2_02": "distributive_basic",
    "R2_03": "x_multiple_of_10",
    "R2_04": "distributive_with_multiples",
    "R2_05": "x_multiple_of_10",
    "R2_06": "distributive_with_multiples",
    "R2_07": "rate_x10_word",
    "R2_08": "verify_distributive",
    "R2_09": "distributive_chain",
    "R2_10": "rate_x10_word",
    "R2_08": "addition_3digit",      # U1
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "extend_pattern_x_mult",
    "R3_02": "two_step_x10_word",
    "R3_03": "compare_products",
    "R3_04": "verify_distributive",
    "R3_05": "rate_x10_word",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "concrete", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.5 Lesson 5.3 'Use Distributive Property' pp.197-200",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic G — Distributive Property with Multiples of 10",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "x_multiple_of_10")
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
        "title": "한 자리 × 10의 배수 = 기본 사실 + 0 붙이기",
        "content": (
            "3 × 40 같은 식의 핵심 직관: 40 = 4 × 10 이므로, "
            "3 × 40 = 3 × (4 × 10) = (3 × 4) × 10 = 12 × 10 = 120. "
            "단계 1: 기본 사실 계산 (3 × 4 = 12). "
            "단계 2: 0을 한 개 붙이기 (12 → 120). "
            "흔한 실수 1: M01 — 0 붙이기 잊음 (답을 12로). "
            "흔한 실수 2: M02 — 0을 두 개 붙임 (답을 1200으로). "
            "기억법: '인자에 0이 한 개 → 곱에도 0이 한 개'."
        ),
        "cpa_stage": "concrete",
        "visual_type": "place_value_diagram",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "분배법칙으로 더 쪼개기 (어려운 곱셈 풀기)",
        "content": (
            "큰 수의 곱셈도 분배로 작은 부분으로 나눌 수 있음. "
            "예: 6 × 70 = 6 × (50 + 20) = (6 × 50) + (6 × 20) = 300 + 120 = 420. "
            "예: 7 × 30 = 7 × (10 + 20) = 70 + 140 = 210. "
            "단계 1: 10의 배수를 두 친한 부분으로 분해. "
            "단계 2: 각 부분에 곱하기 (모두에). "
            "단계 3: 두 결과 더하기. "
            "흔한 실수 (M03): 한 부분만 곱하고 멈춤."
        ),
        "cpa_stage": "abstract",
        "visual_type": "distribute_diagram",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "한 자리 × 10의 배수 — 풀이 4단계 + 검증",
        "content": (
            "단계 1 식 인식: a × b0 형태? 또는 분배 필요? "
            "단계 2 분리: 40 = 4 × 10 (덧셈 분리 ❌, 곱셈 분리 ✓). "
            "단계 3 기본 사실 + 0 붙이기. "
            "단계 4 결과 검증: 답이 a × b의 10배인지 확인. "
            "🔍 분배 형태인 경우: 두 부분 모두에 곱했는지 확인 (M03 방지). "
            "🔍 자릿수 검증: 한 자리 × 두 자리 = 일반적으로 두~세 자리 곱."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 326 + 487.",
        "choices": ["A. 703", "B. 713", "C. 803", "D. 813"],
        "answer": "D",
        "explanation": "326+487: 6+7=13 (carry 1), 2+8+1=11 (carry 1), 3+4+1=8. Result: 813.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 13. Tens: 11. Hundreds: 8."],
        "feedback": {"correct": "Right — 813.", "incorrect": "326+487=813."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 803 − 256.",
        "choices": ["A. 547", "B. 557", "C. 647", "D. 657"],
        "answer": "A",
        "explanation": "803−256: 3−6 borrow → 13−6=7; tens 9−5=4 (after lending); hundreds 7−2=5. Result: 547.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "803−256=547."],
        "feedback": {"correct": "Right — 547.", "incorrect": "803−256=547."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A warehouse had 624 boxes. They shipped 287 boxes, then received 195 more. How many boxes now?",
        "choices": ["A. 142", "B. 337", "C. 532", "D. 1106"],
        "answer": "C",
        "explanation": "Step 1: 624−287=337. Step 2: 337+195=532.",
        "difficulty": 3,
        "hints": ["Subtract shipped, then add received.", "624−287=337, 337+195=532."],
        "feedback": {"correct": "Right — 532 boxes.", "incorrect": "624−287=337, then +195=532."},
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
        "prerequisite": "G3 U4 L4 — 분배법칙 기초; G3 U5 L1-L2 — 함수표·미지수 (3.OA.B.5, 3.OA.A.4)",
        "current":      "G3 — 분배법칙으로 한 자리 × 10의 배수 풀기 (3.OA.B.5, 3.NBT.A.3)",
        "successor":    "G3 U5 L4 — 10의 배수 곱셈 전략 (3.NBT.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u5_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
