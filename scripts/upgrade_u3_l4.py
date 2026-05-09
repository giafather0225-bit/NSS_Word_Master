"""
G3 U3 L4 — Problem Solving: Model Multiplication 7단계 업그레이드 스크립트
==========================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.3 (그리기·바 모델로 곱셈 워드프로블럼 모델링)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U3_understand_multiplication/L4_model_multiplication.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.A.3.M01", "3.OA.A.3.M05"],
    "PT_02": ["3.OA.A.3.M01"],
    "PT_03": ["3.OA.A.3.M01", "3.OA.A.3.M06"],
    "PT_04": ["3.OA.A.3.M01", "3.OA.A.3.M05"],
    "PT_05": ["3.OA.A.3.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.A.3.M01"],
    "TRY_02": ["3.OA.A.3.M02"],
    "TRY_03": ["3.OA.A.3.M01", "3.OA.A.3.M06"],
    "TRY_04": ["3.OA.A.3.M01"],
    "TRY_05": ["3.OA.A.3.M02"],
    "R1_01": ["3.OA.A.3.M01"],
    "R1_02": ["3.OA.A.3.M01", "3.OA.A.3.M05"],
    "R1_03": ["3.OA.A.3.M01", "3.OA.A.3.M05"],
    "R1_04": ["3.OA.A.3.M01"],
    "R1_05": ["3.OA.A.3.M01", "3.OA.A.3.M05"],
    "R1_06": ["3.OA.A.3.M02"],
    "R1_07": ["3.OA.A.3.M01"],
    "R1_08": ["3.OA.A.3.M02"],
    "R1_09": ["3.OA.A.3.M02"],
    "R1_10": ["3.OA.A.3.M07"],
    "R2_01": ["3.OA.A.3.M01", "3.OA.A.3.M05"],
    "R2_02": ["3.OA.A.3.M07"],
    "R2_03": ["3.OA.A.3.M01"],
    "R2_04": ["3.OA.A.3.M01"],
    "R2_05": ["3.OA.A.3.M01", "3.OA.A.3.M06"],
    "R2_06": ["3.OA.A.3.M07"],
    "R2_07": ["3.OA.A.3.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.A.3.M01", "3.OA.A.3.M06"],
    "R3_02": ["3.OA.A.3.M01", "3.OA.A.3.M06"],
    "R3_03": ["3.OA.A.3.M01", "3.OA.A.3.M06"],
    "R3_04": ["3.OA.A.3.M01", "3.OA.A.3.M06"],
    "R3_05": ["3.OA.A.3.M02"],
}

SKILL_TAGS = {
    "PT_01": "word_problem_to_multiplication",
    "PT_02": "draw_equal_groups",
    "PT_03": "two_step_multiplication",
    "PT_04": "word_problem_to_multiplication",
    "PT_05": "word_problem_to_multiplication",
    "LEARN_01": "draw_equal_groups",
    "LEARN_02": "bar_model",
    "LEARN_03": "two_step_multiplication",
    "LEARN_04": "model_selection",
    "LEARN_05": "keyword_clue_reading",
    "LEARN_06": "draw_equal_groups",
    "LEARN_07": "bar_model",
    "LEARN_08": "two_step_multiplication",
    "TRY_01": "draw_equal_groups",
    "TRY_02": "rows_to_multiplication",
    "TRY_03": "two_step_multiplication",
    "TRY_04": "bar_model",
    "TRY_05": "commutative_model",
    "R1_01": "draw_equal_groups",
    "R1_02": "word_problem_to_multiplication",
    "R1_03": "word_problem_to_multiplication",
    "R1_04": "bar_model",
    "R1_05": "draw_equal_groups",
    "R1_06": "model_to_multiplication",
    "R1_07": "word_problem_to_multiplication",
    "R1_08": "commutative_model",
    "R1_09": "rows_to_multiplication",
    "R1_10": "missing_factor",
    "R2_01": "word_problem_to_multiplication",
    "R2_02": "missing_factor",
    "R2_03": "picture_graph_to_multiplication",
    "R2_04": "draw_equal_groups",
    "R2_05": "two_step_multiplication",
    "R2_06": "missing_factor",
    "R2_07": "bar_model",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_multiplication",
    "R3_02": "two_step_multiplication",
    "R3_03": "two_step_multiplication",
    "R3_04": "three_step_multiplication",
    "R3_05": "commutative_model",
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "concrete", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,5)}, "TRY_05": "abstract",
    **{f"R1_0{i}": "pictorial" for i in range(1,8)},
    "R1_08": "abstract", "R1_09": "pictorial", "R1_10": "abstract",
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.3 Lesson 3.4 'Problem Solving: Model Multiplication' pp.115-118",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic B — Equal Groups: Drawing and Modeling",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "draw_equal_groups")
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
        "title": "단계별 그리기 — 동그라미와 점",
        "content": (
            "워드프로블럼을 그림으로 옮기는 4단계: "
            "1) 그룹 수만큼 동그라미를 그리기 (예: 4 boxes → 4개 동그라미). "
            "2) 'each' 뒤의 숫자만큼 각 동그라미 안에 점 찍기. "
            "3) 모든 점을 세거나 곱셈 식 쓰기. "
            "4) 답에 단위 적기 (apples, students 등). "
            "흔한 실수: 'each' 키워드를 놓치고 그룹/크기를 뒤바꿈."
        ),
        "cpa_stage": "concrete",
        "visual_type": "manipulative",
        "visual_data": {"tool": "array_grid", "config": {"rows": 4, "cols": 3}},
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "바 모델 — 칸과 칸 값",
        "content": (
            "바 모델은 길쭉한 직사각형을 같은 크기의 칸으로 나눕니다. "
            "칸 개수 = 그룹 수, 한 칸의 값 = 한 그룹의 크기. "
            "전체 바의 길이 = 곱(product). "
            "활용 팁: 미지수 문제에 강함. "
            "예: '7칸 바의 전체가 35' → 한 칸 = ?, 7 × ? = 35 → ? = 5."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "manipulative",
        "visual_data": {"tool": "array_grid", "config": {"rows": 1, "cols": 7}},
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "두 단계 문제 — 곱셈 먼저, 그 다음에",
        "content": (
            "'몇 개씩 N묶음, 그 후 ±M' 패턴은 항상 곱셈 먼저, 그 다음 ±M. "
            "1단계: 그룹 총합 계산 (G × S). "
            "2단계: 추가/제거된 양만큼 더하거나 빼기. "
            "예: '3 trays × 5 cookies, 2 burned' → 3×5=15, 15−2=13. "
            "흔한 실수: G+M을 먼저 곱하기 (3×5−2 vs (3×5)−2=13). "
            "괄호처럼 곱셈을 먼저 묶어서 생각하세요."
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
        "question": "Find the sum: 175 + 489.",
        "choices": ["A. 554", "B. 654", "C. 664", "D. 754"],
        "answer": "C",
        "explanation": "175+489: 5+9=14 (carry 1), 7+8+1=16 (carry 1), 1+4+1=6. Result: 664.",
        "hints": [
            "Watch the carries — two of them.",
            "Ones: 5+9=14. Tens: 7+8+1=16. Hundreds: 1+4+1=6.",
        ],
        "feedback": {
            "correct": "Right — 664.",
            "incorrect": "175+489=664.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 803 − 256.",
        "choices": ["A. 547", "B. 553", "C. 647", "D. 657"],
        "answer": "A",
        "explanation": "803−256: 3−6 borrow → 13−6=7; tens 0−5 borrow → 10−6=4 (after lending); hundreds 7−2=5. Result: 547.",
        "hints": [
            "Borrow across the zero in the tens place.",
            "Result: 547.",
        ],
        "feedback": {
            "correct": "Right — 547.",
            "incorrect": "803−256=547. Borrow across the zero.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A bookstore had 384 books. They sold 127 books, then received 215 new ones. How many books now?",
        "choices": ["A. 257", "B. 472", "C. 482", "D. 502"],
        "answer": "B",
        "explanation": "Step 1: 384−127=257. Step 2: 257+215=472.",
        "hints": [
            "Subtract first (sold), then add (received).",
            "384−127=257, 257+215=472.",
        ],
        "feedback": {
            "correct": "Right — 472 books.",
            "incorrect": "384−127=257, then +215=472.",
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
        "prerequisite": "G3 U3 L1-L3 — 등량 그룹·반복 덧셈·수직선 곱셈 (3.OA.A.1, 3.OA.A.3)",
        "current":      "G3 — 그리기·바 모델로 곱셈 워드프로블럼 모델링 (3.OA.A.3)",
        "successor":    "G3 U3 L5 — 배열로 곱셈 모델링 (3.OA.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u3_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
