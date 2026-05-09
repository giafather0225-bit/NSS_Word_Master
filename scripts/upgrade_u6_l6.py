"""
G3 U6 L6 — Model with Arrays 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.3 (배열로 나눗셈 표현)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L6_model_with_arrays.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.A.3.M02"],
    "PT_02": ["3.OA.A.2.M02"],
    "PT_03": ["3.OA.A.3.M02"],
    "PT_04": ["3.OA.A.2.M02"],
    "PT_05": ["3.OA.A.2.M03"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.A.2.M02"],
    "TRY_02": ["3.OA.A.3.M02"],
    "TRY_03": ["3.OA.A.2.M06"],
    "TRY_04": ["3.OA.A.2.M06"],
    "TRY_05": ["3.OA.A.2.M02"],
    "R1_01": ["3.OA.A.2.M02"],
    "R1_02": ["3.OA.A.2.M02"],
    "R1_03": ["3.OA.A.2.M02"],
    "R1_04": ["3.OA.A.2.M02"],
    "R1_05": ["3.OA.A.2.M02"],
    "R1_06": ["3.OA.A.2.M02"],
    "R1_07": ["3.OA.A.2.M03"],
    "R1_08": ["3.OA.A.2.M06"],
    "R1_09": ["3.OA.A.3.M02"],
    "R1_10": ["3.OA.A.2.M06"],
    "R2_01": ["3.OA.A.2.M02"],
    "R2_02": ["3.OA.B.5.M02"],
    "R2_03": ["3.OA.A.4.M01"],
    "R2_04": ["3.OA.A.3.M02"],
    "R2_05": ["3.OA.A.2.M06"],
    "R2_06": ["3.OA.A.2.M02"],
    "R2_07": ["3.OA.A.2.M06"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_02": ["3.OA.A.2.M02"],
    "R3_03": ["3.OA.A.2.M02"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_05": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
}

SKILL_TAGS = {
    "PT_01": "array_total",
    "PT_02": "array_division_size",
    "PT_03": "array_total",
    "PT_04": "array_division_count",
    "PT_05": "array_to_division",
    "LEARN_01": "array_division_intro",
    "LEARN_02": "build_array",
    "LEARN_03": "array_two_equations",
    "LEARN_04": "read_division_array",
    "LEARN_05": "array_division_rule",
    "LEARN_06": "array_division_routine",
    "LEARN_07": "array_fact_family",
    "LEARN_08": "array_dimension_check",
    "TRY_01": "array_division_size",
    "TRY_02": "array_total",
    "TRY_03": "array_to_division",
    "TRY_04": "array_to_division",
    "TRY_05": "array_division_count",
    "R1_01": "array_division_size",
    "R1_02": "array_division_size",
    "R1_03": "array_division_count",
    "R1_04": "array_division_size",
    "R1_05": "array_division_count",
    "R1_06": "array_division_size",
    "R1_07": "array_to_division",
    "R1_08": "array_to_division",
    "R1_09": "array_to_equations",
    "R1_10": "array_to_division",
    "R2_01": "array_division_size",
    "R2_02": "array_to_equations",
    "R2_03": "array_missing_dimension",
    "R2_04": "identify_array_total",
    "R2_05": "array_to_division",
    "R2_06": "array_division_count",
    "R2_07": "array_to_division",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "array_grow_columns",
    "R3_02": "square_array",
    "R3_03": "compare_array_dimensions",
    "R3_04": "array_grow_rows",
    "R3_05": "array_remove_row",
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "concrete", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "pictorial", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,6)},
    **{f"R1_{i:02d}": "pictorial" for i in range(1,11)},
    **{f"R2_{i:02d}": "pictorial" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "pictorial" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.6 'Model with Arrays' pp.241-244",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D — Arrays for Multiplication and Division",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "array_division_size")
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
        "title": "배열로 나눗셈 풀기 — 3단계 루틴",
        "content": (
            "배열은 행과 열로 정렬된 직사각형 모양의 점/타일. "
            "단계 1) 전체 개수와 한 차원(행 수 또는 열 수) 확인. "
            "단계 2) 식 세우기: 전체 ÷ 알고있는차원 = 모르는차원. "
            "  예: 24개를 4행으로 → 24 ÷ 4 = 6 → 한 행에 6개. "
            "단계 3) 곱셈으로 검산: 4 × 6 = 24 ✓. "
            "흔한 실수 (M02): '몇 행' 묻는데 '한 행에 몇 개'라고 답."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "array_division_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "하나의 배열 = 4개의 식 — 패밀리 만들기",
        "content": (
            "한 배열(예: 4행 × 6열 = 24개)로 4가지 식을 모두 쓸 수 있음: "
            "곱셈 2개: 4 × 6 = 24, 6 × 4 = 24. "
            "나눗셈 2개: 24 ÷ 4 = 6, 24 ÷ 6 = 4. "
            "이를 '패밀리'라 부름. 한 배열을 보면 4식이 즉시 보여야 함. "
            "팁: 곱셈을 알면 나눗셈도 자동으로 알 수 있음 (역연산)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "array_fact_family",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "차원 검산 — 행 수 × 열 수 = 전체",
        "content": (
            "배열 답을 적은 뒤 검산: 행 수 × 열 수 = 위에서 본 전체? "
            "예: 7행 × 8열 → 56? 7 × 8 = 56 ✓. "
            "예: 9행 × 4열 → 36? 9 × 4 = 36 ✓. "
            "🔍 검증: 차원 두 개를 곱해서 전체와 일치해야 함. "
            "흔한 실수 (M02): 차원을 헷갈려 답 단위가 틀림 — "
            "'행'을 묻는지 '열'을 묻는지 항상 확인."
        ),
        "cpa_stage": "abstract",
        "visual_type": "array_dimension_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 467 + 358.",
        "choices": ["A. 715", "B. 725", "C. 815", "D. 825"],
        "answer": "D",
        "explanation": "467+358: 7+8=15 (carry 1), 6+5+1=12 (carry 1), 4+3+1=8. Result: 825.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 12. Hundreds: 8."],
        "feedback": {"correct": "Right — 825.", "incorrect": "467+358=825."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 706 − 348.",
        "choices": ["A. 358", "B. 368", "C. 458", "D. 468"],
        "answer": "A",
        "explanation": "706−348: 6−8 borrow → 16−8=8; tens 9−4=5 (after lending across zero); hundreds 6−3=3. Result: 358.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "706−348=358."],
        "feedback": {"correct": "Right — 358.", "incorrect": "706−348=358."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bakery had 568 cookies. They sold 274, then baked 189 more. How many cookies now?",
        "choices": ["A. 294", "B. 359", "C. 483", "D. 631"],
        "answer": "C",
        "explanation": "Step 1: 568−274=294. Step 2: 294+189=483.",
        "difficulty": 3,
        "hints": ["Subtract sold, then add baked.", "568−274=294, 294+189=483."],
        "feedback": {"correct": "Right — 483 cookies.", "incorrect": "568−274=294, then +189=483."},
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
        "prerequisite": "G3 U6 L5 — 반복뺄셈과 나눗셈의 관계 (3.OA.A.3)",
        "current":      "G3 — 배열로 나눗셈 모델링 (3.OA.A.3)",
        "successor":    "G3 U6 L7 — 곱셈과 나눗셈의 관계 (3.OA.B.6)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l6.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
