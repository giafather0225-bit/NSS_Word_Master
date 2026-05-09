"""
G3 U6 L2 — Size of Equal Groups 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.2 (분배 모델 — 모둠당 크기 구하기)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L2_size_of_equal_groups.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.A.2.M02"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.A.2.M02"],
    "TRY_02": ["3.OA.A.2.M04"],
    "TRY_03": ["3.OA.A.2.M06"],
    "TRY_04": ["3.OA.A.2.M06"],
    "TRY_05": ["3.OA.A.2.M02"],
    **{f"R1_{i:02d}": ["3.OA.A.2.M02"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M02"],
    "R2_02": ["3.OA.A.2.M02"],
    "R2_03": ["3.OA.A.2.M06"],
    "R2_04": ["3.OA.A.2.M02"],
    "R2_05": ["3.OA.A.2.M02"],
    "R2_06": ["3.OA.A.2.M02"],
    "R2_07": ["3.OA.A.2.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_02": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_03": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_05": ["3.OA.A.2.M02"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "size_of_equal_groups" for i in range(1,6)},
    "LEARN_01": "size_of_equal_groups",
    "LEARN_02": "model_with_counters",
    "LEARN_03": "check_with_multiplication",
    "LEARN_04": "bar_model_group_size",
    "LEARN_05": "division_equation_parts",
    "LEARN_06": "partitive_routine",
    "LEARN_07": "inverse_check_routine",
    "LEARN_08": "size_vs_count_distinction",
    **{f"TRY_0{i}": "size_of_equal_groups" for i in range(1,6)},
    **{f"R1_{i:02d}": "size_of_equal_groups" for i in range(1,11)},
    "R2_01": "size_of_equal_groups",
    "R2_02": "size_of_equal_groups",
    "R2_03": "division_basic_fact",
    "R2_04": "size_of_equal_groups",
    "R2_05": "size_of_equal_groups",
    "R2_06": "size_of_equal_groups",
    "R2_07": "size_of_equal_groups",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_combine",
    "R3_02": "two_step_division_subtract",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "size_of_equal_groups",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "pictorial", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.2 'Size of Equal Groups' pp.225-228",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D — Division as Sharing (Partitive)",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "size_of_equal_groups")
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
        "title": "분배(나누어 주기) 루틴 — 한 명당 몇 개?",
        "content": (
            "전체 ÷ 모둠 수 = 모둠당 크기. "
            "예: 24개를 6명에게 똑같이 나누면? 24 ÷ 6 = 4 → 한 명당 4개. "
            "단계 1) 전체와 모둠 수를 찾기 (전체 24, 모둠 6). "
            "단계 2) 전체 ÷ 모둠 수 식 세우기 (24 ÷ 6). "
            "단계 3) 곱셈으로 풀기 (몇 × 6 = 24? → 4). "
            "단계 4) 답의 단위 = '한 명당' 또는 '한 모둠당'."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "partitive_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "곱셈으로 검산 — 답이 맞는지 확인",
        "content": (
            "분배 나눗셈을 풀고 나면 곱셈으로 검산하세요. "
            "예: 30 ÷ 6 = 5 → 검산: 5 × 6 = 30 ✓. "
            "예: 42 ÷ 7 = 6 → 검산: 6 × 7 = 42 ✓. "
            "검산 결과가 전체와 다르면 답이 틀린 것. "
            "흔한 실수 (M06): 곱셈 사실로 검산하지 않고 그냥 답 적기 — "
            "쉬운 한 단계로 오답을 90% 잡아낼 수 있음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "inverse_check",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "크기 vs 개수 — 답의 단위 구분",
        "content": (
            "분배 모델(이번 레슨)은 모둠당 '크기'를 구함 (한 명당 몇 개). "
            "측정 모델(다음 레슨)은 '모둠의 개수'를 구함 (몇 묶음). "
            "예: '15개를 5명에게 똑같이' → 한 명당 3개 (크기). "
            "예: '15개를 5개씩 묶음' → 3묶음 (개수). "
            "🔍 검증: 답을 적기 전 항상 단위 확인 — '한 명당 ___개' 또는 '___개의 묶음'. "
            "흔한 실수 (M02): 답의 숫자만 맞고 단위가 틀린 경우."
        ),
        "cpa_stage": "abstract",
        "visual_type": "unit_identification",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 367 + 458.",
        "choices": ["A. 715", "B. 725", "C. 815", "D. 825"],
        "answer": "D",
        "explanation": "367+458: 7+8=15 (carry 1), 6+5+1=12 (carry 1), 3+4+1=8. Result: 825.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 12. Hundreds: 8."],
        "feedback": {"correct": "Right — 825.", "incorrect": "367+458=825."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 600 − 234.",
        "choices": ["A. 366", "B. 376", "C. 466", "D. 476"],
        "answer": "A",
        "explanation": "600−234: 0−4 borrow → 10−4=6; tens 9−3=6 (after lending across zeros); hundreds 5−2=3. Result: 366.",
        "difficulty": 2,
        "hints": ["Borrow across two zeros.", "600−234=366."],
        "feedback": {"correct": "Right — 366.", "incorrect": "600−234=366."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A class had 482 stickers. They gave out 175 and the teacher added 264 more. How many stickers now?",
        "choices": ["A. 307", "B. 439", "C. 571", "D. 921"],
        "answer": "C",
        "explanation": "Step 1: 482−175=307. Step 2: 307+264=571.",
        "difficulty": 3,
        "hints": ["Subtract given out, then add added.", "482−175=307, 307+264=571."],
        "feedback": {"correct": "Right — 571 stickers.", "incorrect": "482−175=307, then +264=571."},
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
        "prerequisite": "G3 U6 L1 — 나눗셈의 의미: 분배·측정 모델 (3.OA.A.2)",
        "current":      "G3 — 분배 나눗셈: 모둠당 크기 구하기 (3.OA.A.2)",
        "successor":    "G3 U6 L3 — 측정 나눗셈: 모둠의 개수 구하기 (3.OA.A.2)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
