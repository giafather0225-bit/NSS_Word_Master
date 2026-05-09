"""
G3 U6 L3 — Number of Equal Groups 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.2 (측정 모델 — 모둠의 개수 구하기)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L3_number_of_equal_groups.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.A.2.M02"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.A.2.M02"] for i in range(1,6)},
    "R1_01": ["3.OA.A.2.M06"],
    "R1_02": ["3.OA.A.2.M06"],
    "R1_03": ["3.OA.A.2.M06"],
    "R1_04": ["3.OA.A.2.M06"],
    "R1_05": ["3.OA.A.2.M02"],
    "R1_06": ["3.OA.A.2.M06"],
    "R1_07": ["3.OA.A.2.M02"],
    "R1_08": ["3.OA.A.2.M02"],
    "R1_09": ["3.OA.A.2.M02"],
    "R1_10": ["3.OA.A.2.M02"],
    "R2_01": ["3.OA.A.2.M02"],
    "R2_02": ["3.OA.A.2.M06"],
    "R2_03": ["3.OA.A.2.M02"],
    "R2_04": ["3.OA.A.2.M06"],
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
    **{f"PT_0{i}": "number_of_equal_groups" for i in range(1,6)},
    "LEARN_01": "number_of_equal_groups",
    "LEARN_02": "model_with_circles",
    "LEARN_03": "skip_count_up",
    "LEARN_04": "number_line_division",
    "LEARN_05": "division_equation_parts",
    "LEARN_06": "quotative_routine",
    "LEARN_07": "skip_count_strategy",
    "LEARN_08": "partitive_vs_quotative_setup",
    **{f"TRY_0{i}": "number_of_equal_groups" for i in range(1,6)},
    **{f"R1_{i:02d}": "number_of_equal_groups" for i in range(1,11)},
    "R2_01": "number_of_equal_groups",
    "R2_02": "division_basic_fact",
    "R2_03": "number_of_equal_groups",
    "R2_04": "division_basic_fact",
    "R2_05": "number_of_equal_groups",
    "R2_06": "number_of_equal_groups",
    "R2_07": "number_of_equal_groups",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_combine",
    "R3_02": "two_step_division_subtract",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_combine",
    "R3_05": "number_of_equal_groups",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "pictorial", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.3 'Number of Equal Groups' pp.229-232",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D — Division as Measurement (Quotative)",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "number_of_equal_groups")
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
        "title": "측정(묶어 세기) 루틴 — 몇 묶음?",
        "content": (
            "전체 ÷ 모둠당 크기 = 모둠 수. "
            "예: 24개를 6개씩 묶으면? 24 ÷ 6 = 4묶음. "
            "단계 1) 전체와 모둠당 크기 찾기 (전체 24, 한 묶음 6). "
            "단계 2) 전체 ÷ 묶음 크기 식 (24 ÷ 6). "
            "단계 3) 곱셈으로 풀기 (몇 × 6 = 24? → 4). "
            "단계 4) 답의 단위 = '묶음' 또는 '모둠'."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "quotative_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "스킵 카운트로 풀기 — 30 ÷ 5의 빠른 방법",
        "content": (
            "측정 나눗셈은 스킵 카운트와 자연스럽게 어울립니다. "
            "예: 30 ÷ 5 → 5씩 세어 30 도달까지 몇 번? "
            "  5, 10, 15, 20, 25, 30 → 6번 → 답 6묶음. "
            "팁: 손가락으로 한 번씩 세면 정확. "
            "흔한 실수 (M05): 시작 0을 빼먹거나 끝 30을 빠뜨려 한 개 차이로 틀림 — "
            "끝 숫자(30) 셀 때 손가락 잊지 마세요."
        ),
        "cpa_stage": "abstract",
        "visual_type": "skip_count_division",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "분배 vs 측정 — 식 세우기 비교",
        "content": (
            "두 모델 모두 식은 같은 24 ÷ 6이지만 의미가 다름. "
            "분배: '24개를 6명이 나눠 가짐' → 답 4 = 한 명당 개수. "
            "측정: '24개를 6개씩 묶음' → 답 4 = 묶음 수. "
            "🔍 핵심 구분: '나눠지는 사람/그릇 수'가 주어지면 분배, "
            "'한 묶음 크기'가 주어지면 측정. "
            "양쪽 다 곱셈 검산은 같음: 4 × 6 = 24 ✓."
        ),
        "cpa_stage": "abstract",
        "visual_type": "compare_division_models",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 489 + 376.",
        "choices": ["A. 755", "B. 765", "C. 855", "D. 865"],
        "answer": "D",
        "explanation": "489+376: 9+6=15 (carry 1), 8+7+1=16 (carry 1), 4+3+1=8. Result: 865.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 16. Hundreds: 8."],
        "feedback": {"correct": "Right — 865.", "incorrect": "489+376=865."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 712 − 348.",
        "choices": ["A. 364", "B. 374", "C. 464", "D. 474"],
        "answer": "A",
        "explanation": "712−348: 2−8 borrow → 12−8=4; tens 0−4 borrow → 10−4=6; hundreds 6−3=3. Result: 364.",
        "difficulty": 2,
        "hints": ["Two borrows.", "712−348=364."],
        "feedback": {"correct": "Right — 364.", "incorrect": "712−348=364."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bookstore had 758 books. They sold 296 and received 184 more. How many books now?",
        "choices": ["A. 462", "B. 540", "C. 646", "D. 838"],
        "answer": "C",
        "explanation": "Step 1: 758−296=462. Step 2: 462+184=646.",
        "difficulty": 3,
        "hints": ["Subtract sold, then add received.", "758−296=462, 462+184=646."],
        "feedback": {"correct": "Right — 646 books.", "incorrect": "758−296=462, then +184=646."},
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
        "prerequisite": "G3 U6 L2 — 분배 나눗셈: 모둠당 크기 (3.OA.A.2)",
        "current":      "G3 — 측정 나눗셈: 모둠의 개수 구하기 (3.OA.A.2)",
        "successor":    "G3 U6 L4 — 막대 모델로 나눗셈 표현 (3.OA.A.2)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
