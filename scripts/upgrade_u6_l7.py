"""
G3 U6 L7 — Relate Multiplication and Division 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.6 (나눗셈을 미지수 곱셈으로 — 역연산)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L7_relate_multiplication_and_division.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.A.2.M06"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.A.2.M06"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.A.2.M06"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.2.M06"],
    "R2_03": ["3.OA.A.2.M06"],
    "R2_04": ["3.OA.A.2.M06"],
    "R2_05": ["3.OA.A.2.M06"],
    "R2_06": ["3.OA.A.2.M06"],
    "R2_07": ["3.OA.A.2.M06"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.A.2.M06"],
    "R3_02": ["3.OA.D.8.M01", "3.OA.A.2.M06"],
    "R3_03": ["3.OA.A.2.M06"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M06"],
    "R3_05": ["3.OA.D.8.M01", "3.OA.A.4.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "use_multiplication_for_division" for i in range(1,6)},
    "LEARN_01": "inverse_operations",
    "LEARN_02": "think_multiplication",
    "LEARN_03": "division_unknown_factor",
    "LEARN_04": "fact_family_triangle",
    "LEARN_05": "inverse_rule",
    "LEARN_06": "think_multiplication_routine",
    "LEARN_07": "fact_family_four",
    "LEARN_08": "missing_factor_strategy",
    **{f"TRY_0{i}": "use_multiplication_for_division" for i in range(1,6)},
    **{f"R1_{i:02d}": "use_multiplication_for_division" for i in range(1,11)},
    "R2_01": "identify_related_facts",
    "R2_02": "use_multiplication_for_division",
    "R2_03": "fact_family_two_divisions",
    "R2_04": "array_to_multiplication",
    "R2_05": "use_multiplication_for_division",
    "R2_06": "use_multiplication_for_division",
    "R2_07": "use_multiplication_for_division",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "extend_pattern_division",
    "R3_02": "two_step_division_multiply",
    "R3_03": "fact_family_validation",
    "R3_04": "two_step_division_subtract",
    "R3_05": "two_step_unknown_factor",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.7 'Relate Multiplication and Division' pp.245-248",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic E — Division as Unknown-Factor Problem",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "use_multiplication_for_division")
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
        "title": "곱셈으로 나눗셈 풀기 — 사고 절차",
        "content": (
            "나눗셈 문제를 만나면 무조건 곱셈으로 바꿔 생각하세요. "
            "예: 56 ÷ 8 = ? → '몇 × 8 = 56?' → 7 → 답 7. "
            "예: 42 ÷ 6 = ? → '몇 × 6 = 42?' → 7 → 답 7. "
            "단계 1) 나눗셈 식을 본다 (피제수 ÷ 제수). "
            "단계 2) 곱셈 미지수 식으로 바꾼다 (? × 제수 = 피제수). "
            "단계 3) 곱셈표로 ?를 찾는다. "
            "흔한 실수 (M06): 곱셈 사실을 외워놓고도 나눗셈 풀 때 다시 그림 그림."
        ),
        "cpa_stage": "abstract",
        "visual_type": "think_multiplication",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "패밀리 4식 — 한 사실로 4가지",
        "content": (
            "곱셈 1개를 알면 4식이 모두 풀림. "
            "예: 7 × 8 = 56을 알면 자동으로: "
            "  7 × 8 = 56 (곱셈 1) "
            "  8 × 7 = 56 (곱셈 2 — 교환법칙) "
            "  56 ÷ 7 = 8 (나눗셈 1 — 역연산) "
            "  56 ÷ 8 = 7 (나눗셈 2 — 역연산) "
            "패밀리 삼각형: 위 56, 아래 7과 8 → 한 모서리 가리면 그 자리가 답."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "fact_family_four",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "미지수 인수 전략 — 시각적 흐름",
        "content": (
            "나눗셈 a ÷ b = ? 를 풀 때: "
            "  ? × b = a 로 다시 쓰기 → b의 곱셈표에서 a를 찾기 → ?는 그 자리 행/열 수. "
            "예: 36 ÷ 4 → ? × 4 = 36 → 4의 곱셈표에서 36 → 9번째 → ? = 9. "
            "🔍 검증: 9 × 4 = 36 ✓. "
            "팁: 곱셈표를 머릿속에 그림으로 두면 모든 나눗셈을 1초만에 해결."
        ),
        "cpa_stage": "abstract",
        "visual_type": "missing_factor_table",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 387 + 458.",
        "choices": ["A. 735", "B. 745", "C. 835", "D. 845"],
        "answer": "D",
        "explanation": "387+458: 7+8=15 (carry 1), 8+5+1=14 (carry 1), 3+4+1=8. Result: 845.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 14. Hundreds: 8."],
        "feedback": {"correct": "Right — 845.", "incorrect": "387+458=845."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 815 − 467.",
        "choices": ["A. 348", "B. 358", "C. 448", "D. 458"],
        "answer": "A",
        "explanation": "815−467: 5−7 borrow → 15−7=8; tens 0−6 borrow → 10−6=4; hundreds 7−4=3. Result: 348.",
        "difficulty": 2,
        "hints": ["Two borrows.", "815−467=348."],
        "feedback": {"correct": "Right — 348.", "incorrect": "815−467=348."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 692 markers. They gave out 285 and bought 168 more. How many markers now?",
        "choices": ["A. 407", "B. 539", "C. 575", "D. 745"],
        "answer": "C",
        "explanation": "Step 1: 692−285=407. Step 2: 407+168=575.",
        "difficulty": 3,
        "hints": ["Subtract given out, then add bought.", "692−285=407, 407+168=575."],
        "feedback": {"correct": "Right — 575 markers.", "incorrect": "692−285=407, then +168=575."},
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
        "prerequisite": "G3 U6 L6 — 배열로 나눗셈 모델링 (3.OA.A.3)",
        "current":      "G3 — 곱셈과 나눗셈의 관계 (3.OA.B.6 — 미지수 인수)",
        "successor":    "G3 U6 L8 — 관련된 사실 쓰기 (3.OA.B.6)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l7.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
