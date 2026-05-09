"""
G3 U3 L5 — Model with Arrays 7단계 업그레이드 스크립트
======================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.3 (배열 행×열로 곱셈 모델링)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U3_understand_multiplication/L5_model_with_arrays.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.A.3.M02"],
    "PT_02": ["3.OA.A.3.M02"],
    "PT_03": ["3.OA.A.3.M02"],
    "PT_04": ["3.OA.A.3.M02"],
    "PT_05": ["3.OA.A.3.M02"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.A.3.M02"],
    "TRY_02": ["3.OA.A.3.M02"],
    "TRY_03": ["3.OA.A.3.M02"],
    "TRY_04": ["3.OA.A.3.M02"],
    "TRY_05": ["3.OA.A.3.M02"],
    "R1_01": ["3.OA.A.3.M02"],
    "R1_02": ["3.OA.A.3.M02"],
    "R1_03": ["3.OA.A.3.M02"],
    "R1_04": ["3.OA.A.3.M02"],
    "R1_05": ["3.OA.A.3.M02"],
    "R1_06": ["3.OA.A.3.M02"],
    "R1_07": ["3.OA.A.3.M02"],
    "R1_08": ["3.OA.A.3.M02"],
    "R1_09": ["3.OA.A.3.M02"],
    "R1_10": ["3.OA.A.3.M07"],
    "R2_01": ["3.OA.A.3.M02"],
    "R2_02": ["3.OA.A.3.M02"],
    "R2_03": ["3.OA.A.3.M07"],
    "R2_04": ["3.OA.A.3.M02"],
    "R2_05": ["3.OA.A.3.M02"],
    "R2_06": ["3.OA.A.3.M02"],
    "R2_07": ["3.OA.A.3.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.A.3.M07"],
    "R3_02": ["3.OA.A.3.M02"],
    "R3_03": ["3.OA.A.3.M02"],
    "R3_04": ["3.OA.A.3.M02", "3.OA.A.3.M06"],
    "R3_05": ["3.OA.A.3.M07"],
}

SKILL_TAGS = {
    "PT_01": "rows_to_multiplication",
    "PT_02": "array_to_multiplication",
    "PT_03": "rows_to_multiplication",
    "PT_04": "multiplication_to_array",
    "PT_05": "rows_to_multiplication",
    "LEARN_01": "array_definition",
    "LEARN_02": "read_array",
    "LEARN_03": "array_to_multiplication",
    "LEARN_04": "rotate_array",
    "LEARN_05": "word_problem_to_array",
    "LEARN_06": "row_column_convention",
    "LEARN_07": "rotate_array",
    "LEARN_08": "array_strategies",
    "TRY_01": "rows_to_multiplication",
    "TRY_02": "word_problem_to_array",
    "TRY_03": "array_growth",
    "TRY_04": "rows_to_multiplication",
    "TRY_05": "multiplication_to_array",
    "R1_01": "rows_to_multiplication",
    "R1_02": "rows_to_multiplication",
    "R1_03": "multiplication_to_array",
    "R1_04": "rows_to_multiplication",
    "R1_05": "word_problem_to_array",
    "R1_06": "rows_to_multiplication",
    "R1_07": "array_to_multiplication",
    "R1_08": "rows_to_multiplication",
    "R1_09": "rows_to_multiplication",
    "R1_10": "find_factors",
    "R2_01": "rows_to_multiplication",
    "R2_02": "two_step_array",
    "R2_03": "missing_factor",
    "R2_04": "rows_to_multiplication",
    "R2_05": "commutative_array",
    "R2_06": "rows_to_multiplication",
    "R2_07": "word_problem_to_array",
    "R2_08": "addition_3digit",         # U1
    "R2_09": "subtraction_3digit",      # U1
    "R2_10": "two_step_add_sub",        # U1
    "R3_01": "find_factors",
    "R3_02": "commutative_array",
    "R3_03": "word_problem_to_array",
    "R3_04": "two_step_array",
    "R3_05": "find_factors",
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "concrete", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,5)}, "TRY_05": "abstract",
    **{f"R1_0{i}": "pictorial" for i in range(1,8)},
    "R1_08": "pictorial", "R1_09": "pictorial", "R1_10": "abstract",
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.3 Lesson 3.5 'Model with Arrays' pp.119-122",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D — Multiplication and Arrays",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "rows_to_multiplication")
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
        "title": "행과 열 — 어느 쪽이 가로인가?",
        "content": (
            "약속: 행(row)은 가로(좌→우), 열(column)은 세로(위→아래). "
            "배열 a × b를 읽을 때 — 첫 번째 인자 a = 행의 개수, "
            "두 번째 인자 b = 한 행에 있는 점 개수(=열의 개수). "
            "예: 4 × 6 → 4행 6열 (가로 4개 줄, 각 줄에 6개). "
            "흔한 실수: 행과 열을 뒤바꿈 → 모델 오류 (곱은 같지만 '몇 행?' 물으면 틀림)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "manipulative",
        "visual_data": {"tool": "array_grid", "config": {"rows": 4, "cols": 6}},
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "배열을 90° 회전하면?",
        "content": (
            "3×6 배열을 90° 돌리면 6×3 배열이 됩니다. "
            "점의 개수는 그대로 18개! "
            "이것이 교환법칙(Commutative Property): a × b = b × a. "
            "배열은 이 법칙을 눈으로 보여주는 가장 강력한 도구입니다. "
            "팁: '회전해도 점의 총 개수는 변하지 않는다' — 곱셈의 핵심 직관."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "manipulative",
        "visual_data": {"tool": "array_grid", "config": {"rows": 3, "cols": 6}},
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "배열로 푸는 3가지 전략 요약",
        "content": (
            "전략 1 그리기: 행수만큼 줄을 긋고 각 줄에 열수만큼 점 찍기. "
            "전략 2 곱셈: 행수 × 열수 = 곱(product). "
            "전략 3 인수 찾기: 곱이 주어지면, '? × ? = product' 가능한 행/열 조합 찾기. "
            "예: product=24 → (1,24)(2,12)(3,8)(4,6)(6,4)(8,3)(12,2)(24,1). "
            "검증: 같은 점 개수의 다른 배열은 모두 같은 곱을 갖습니다."
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
        "question": "Find the sum: 568 + 274.",
        "choices": ["A. 732", "B. 742", "C. 832", "D. 842"],
        "answer": "D",
        "explanation": "568+274: 8+4=12 (carry 1), 6+7+1=14 (carry 1), 5+2+1=8. Result: 842.",
        "hints": [
            "Two carries needed.",
            "Ones: 8+4=12. Tens: 6+7+1=14. Hundreds: 5+2+1=8.",
        ],
        "feedback": {
            "correct": "Right — 842.",
            "incorrect": "568+274=842.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 905 − 348.",
        "choices": ["A. 547", "B. 553", "C. 557", "D. 647"],
        "answer": "C",
        "explanation": "905−348: 5−8 borrow → 15−8=7; tens 0−4 borrow → 10−5=5 (after lending); hundreds 8−3=5. Result: 557.",
        "hints": [
            "Borrow across the zero in the tens.",
            "905−348=557.",
        ],
        "feedback": {
            "correct": "Right — 557.",
            "incorrect": "905−348=557. Watch the zero borrow.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A bakery had 425 muffins. They sold 198, then baked 156 more. How many muffins now?",
        "choices": ["A. 227", "B. 383", "C. 423", "D. 779"],
        "answer": "B",
        "explanation": "Step 1: 425−198=227. Step 2: 227+156=383.",
        "hints": [
            "Subtract first (sold), then add (baked more).",
            "425−198=227, 227+156=383.",
        ],
        "feedback": {
            "correct": "Right — 383 muffins.",
            "incorrect": "425−198=227, then +156=383.",
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
    print("섹션별 문항 수:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U3 L1-L4 — 등량 그룹·반복 덧셈·수직선·바 모델 (3.OA.A.1, 3.OA.A.3)",
        "current":      "G3 — 배열 행·열로 곱셈 모델링; 회전과 교환법칙 시각화 (3.OA.A.3)",
        "successor":    "G3 U3 L6 — 곱셈의 교환법칙 형식화 (3.OA.B.5)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u3_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
