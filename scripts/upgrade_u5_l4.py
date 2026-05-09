"""
G3 U5 L4 — Multiplication Strategies for Multiples of 10 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NBT.A.3 (10의 배수 × 한 자리 — 자릿값 전략, 결합법칙)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U5_use_multiplication_facts/L4_multiplication_strategies_multiples_of_10.json"

ERRORS_MAP = {
    "PT_01": ["3.NBT.A.3.M01"],
    "PT_02": ["3.NBT.A.3.M01"],
    "PT_03": ["3.NBT.A.3.M01"],
    "PT_04": ["3.NBT.A.3.M01"],
    "PT_05": ["3.NBT.A.3.M06"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.NBT.A.3.M01"],
    "TRY_02": ["3.NBT.A.3.M01"],
    "TRY_03": ["3.NBT.A.3.M01"],
    "TRY_04": ["3.NBT.A.3.M01"],
    "TRY_05": ["3.NBT.A.3.M07"],
    "R1_01": ["3.NBT.A.3.M06"],
    "R1_02": ["3.NBT.A.3.M01"],
    "R1_03": ["3.NBT.A.3.M01"],
    "R1_04": ["3.NBT.A.3.M01"],
    "R1_05": ["3.NBT.A.3.M01"],
    "R1_06": ["3.NBT.A.3.M01"],
    "R1_07": ["3.NBT.A.3.M01"],
    "R1_08": ["3.NBT.A.3.M01"],
    "R1_09": ["3.NBT.A.3.M01"],
    "R1_10": ["3.NBT.A.3.M01"],
    "R2_01": ["3.NBT.A.3.M07"],
    "R2_02": ["3.NBT.A.3.M01"],
    "R2_03": ["3.NBT.A.3.M01"],
    "R2_04": ["3.NBT.A.3.M01"],
    "R2_05": ["3.NBT.A.3.M01"],
    "R2_06": ["3.NBT.A.3.M01"],
    "R2_07": ["3.NBT.A.3.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.B.5.M03"],
    "R3_02": ["3.OA.D.8.M01", "3.NBT.A.3.M01"],
    "R3_03": ["3.NBT.A.3.M02"],
    "R3_04": ["3.OA.B.5.M03"],
    "R3_05": ["3.NBT.A.3.M01"],
}

SKILL_TAGS = {
    "PT_01": "x_multiple_of_10",
    "PT_02": "x_multiple_of_10",
    "PT_03": "rate_x10_word",
    "PT_04": "rate_x10_word",
    "PT_05": "x_multiple_of_10_left",
    "LEARN_01": "place_value_strategy",
    "LEARN_02": "associative_x10",
    "LEARN_03": "x10_zero_attach",
    "LEARN_04": "verify_x10",
    "LEARN_05": "x10_word_problem",
    "LEARN_06": "associative_x10",
    "LEARN_07": "commutative_x10_position",
    "LEARN_08": "x_multiple_of_10_strategies",
    "TRY_01": "x_multiple_of_10",
    "TRY_02": "rate_x10_word",
    "TRY_03": "x_multiple_of_10",
    "TRY_04": "x_multiple_of_10",
    "TRY_05": "verify_x10_strategy",
    "R1_01": "x_multiple_of_10_left",
    "R1_02": "x_multiple_of_10",
    "R1_03": "x_multiple_of_10",
    "R1_04": "rate_x10_word",
    "R1_05": "x_multiple_of_10",
    "R1_06": "x_multiple_of_10",
    "R1_07": "x_multiple_of_10",
    "R1_08": "x_multiple_of_10",
    "R1_09": "x_multiple_of_10",
    "R1_10": "rate_x10_word",
    "R2_01": "equivalent_product_x10",
    "R2_02": "x_multiple_of_10",
    "R2_03": "rate_x10_word",
    "R2_04": "x_multiple_of_10",
    "R2_05": "x_multiple_of_10",
    "R2_06": "identify_x10_product",
    "R2_07": "x_multiple_of_10",
    "R2_08": "rate_x10_word",
    "R2_09": "x_multiple_of_10",
    "R2_10": "identify_not_equal",
    "R2_08": "addition_3digit",      # U1
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "extend_pattern_x_mult",
    "R3_02": "two_step_x10_word",
    "R3_03": "identify_not_equal",
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
        "concept_source": "Go Math Grade 3 Ch.5 Lesson 5.4 'Multiplication Strategies for Multiples of 10' pp.201-204",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic G — Place Value Strategies for Multiples of 10",
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
        "title": "결합법칙으로 풀기 — 7 × 60의 마술",
        "content": (
            "10의 배수 곱셈은 결합법칙으로 풀면 깔끔합니다. "
            "예: 7 × 60 = 7 × (6 × 10) = (7 × 6) × 10 = 42 × 10 = 420. "
            "단계 1: 60 = 6 × 10으로 풀어쓰기. "
            "단계 2: 7 × 6 = 42 (기본 사실 — 외운 곱셈표). "
            "단계 3: 42 × 10 = 420 (0 한 개 붙이기). "
            "이 3단계가 머릿속에서는 1초만에 진행됨. "
            "흔한 실수: 결합법칙 없이 답만 외우려다 오류 (M01·M02)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "associative_diagram",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "왼쪽·오른쪽 어디든 같음 — 60 × 7 = 7 × 60",
        "content": (
            "교환법칙으로 위치는 무관: 60 × 7 = 7 × 60 = 420. "
            "10의 배수가 왼쪽이든 오른쪽이든 같은 답. "
            "팁: 10의 배수를 항상 오른쪽으로 옮기고 표준 절차 적용. "
            "예: 90 × 3 → 3 × 90 → 3 × 9 = 27 → 270. "
            "흔한 실수 (M06): 60 × 7과 7 × 60을 다르게 푸는 학생 — "
            "교환법칙으로 같은 답이라는 점을 항상 활용하세요."
        ),
        "cpa_stage": "abstract",
        "visual_type": "commutative_diagram",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "10의 배수 곱셈 — 즉답 전략 4가지",
        "content": (
            "전략 1 결합법칙: a × (b × 10) = (a × b) × 10. "
            "전략 2 0 붙이기: 기본 사실 a × b 하고 0 한 개 첨부. "
            "전략 3 자릿값 검산: 답이 (a × b)의 10배가 되는지 확인. "
            "전략 4 분배법칙 (어려운 경우): 7 × 80 = (5 × 80) + (2 × 80) = 400+160 = 560. "
            "🔍 검증: a × b0 형태에서 답은 항상 끝자리 0. 두 자리/세 자리 곱셈 결과 자릿수 점검."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 458 + 367.",
        "choices": ["A. 715", "B. 825", "C. 715", "D. 825"],
        "answer": "B",
        "explanation": "458+367: 8+7=15 (carry 1), 5+6+1=12 (carry 1), 4+3+1=8. Result: 825.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 12. Hundreds: 8."],
        "feedback": {"correct": "Right — 825.", "incorrect": "458+367=825."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 705 − 358.",
        "choices": ["A. 347", "B. 357", "C. 447", "D. 457"],
        "answer": "A",
        "explanation": "705−358: 5−8 borrow → 15−8=7; tens 9−5=4 (after lending); hundreds 6−3=3. Result: 347.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "705−358=347."],
        "feedback": {"correct": "Right — 347.", "incorrect": "705−358=347."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 836 pencils. Students used 247, then the school bought 195 more. How many pencils now?",
        "choices": ["A. 394", "B. 589", "C. 784", "D. 1278"],
        "answer": "C",
        "explanation": "Step 1: 836−247=589. Step 2: 589+195=784.",
        "difficulty": 3,
        "hints": ["Subtract used, then add bought.", "836−247=589, 589+195=784."],
        "feedback": {"correct": "Right — 784 pencils.", "incorrect": "836−247=589, then +195=784."},
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
        "prerequisite": "G3 U5 L3 — 분배법칙으로 큰 수 곱셈 (3.OA.B.5, 3.NBT.A.3)",
        "current":      "G3 — 10의 배수 곱셈 결합법칙 전략 (3.NBT.A.3)",
        "successor":    "G3 U5 L5 — 한 자리 × 10의 배수 결정판 (3.NBT.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u5_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
