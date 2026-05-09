"""
G3 U6 L5 — Relate Subtraction and Division 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.3 (반복뺄셈 ↔ 나눗셈 관계)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L5_relate_subtraction_and_division.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.A.2.M01"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.A.2.M01"] for i in range(1,6)},
    "R1_01": ["3.OA.A.2.M06"],
    "R1_02": ["3.OA.A.2.M06"],
    "R1_03": ["3.OA.A.2.M06"],
    "R1_04": ["3.OA.A.2.M01"],
    "R1_05": ["3.OA.A.2.M06"],
    "R1_06": ["3.OA.A.2.M02"],
    "R1_07": ["3.OA.A.2.M06"],
    "R1_08": ["3.OA.A.2.M01"],
    "R1_09": ["3.OA.A.2.M02"],
    "R1_10": ["3.OA.A.2.M01"],
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.2.M01"],
    "R2_03": ["3.OA.A.2.M01"],
    "R2_04": ["3.OA.A.2.M06"],
    "R2_05": ["3.OA.A.2.M06"],
    "R2_06": ["3.OA.A.2.M01"],
    "R2_07": ["3.OA.A.2.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M01"],
    "R3_02": ["3.OA.D.8.M01", "3.OA.A.2.M01"],
    "R3_03": ["3.OA.D.8.M01", "3.OA.A.2.M01"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M01"],
    "R3_05": ["3.OA.A.2.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "repeated_subtraction" for i in range(1,6)},
    "LEARN_01": "repeated_subtraction",
    "LEARN_02": "step_by_step_subtraction",
    "LEARN_03": "number_line_division",
    "LEARN_04": "count_jumps_division",
    "LEARN_05": "subtraction_division_link",
    "LEARN_06": "repeated_subtraction_routine",
    "LEARN_07": "number_line_jumps",
    "LEARN_08": "subtraction_division_check",
    **{f"TRY_0{i}": "repeated_subtraction" for i in range(1,6)},
    "R1_01": "division_basic_fact",
    "R1_02": "division_basic_fact",
    "R1_03": "division_basic_fact",
    "R1_04": "repeated_subtraction",
    "R1_05": "division_basic_fact",
    "R1_06": "rate_division_word",
    "R1_07": "division_basic_fact",
    "R1_08": "repeated_subtraction",
    "R1_09": "rate_division_word",
    "R1_10": "repeated_subtraction",
    "R2_01": "division_basic_fact",
    "R2_02": "number_line_jumps",
    "R2_03": "subtraction_to_equation",
    "R2_04": "how_many_groups",
    "R2_05": "how_many_groups",
    "R2_06": "subtraction_chain",
    "R2_07": "number_line_jumps",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_subtract",
    "R3_02": "number_line_position",
    "R3_03": "reverse_repeated_subtraction",
    "R3_04": "rate_division_word",
    "R3_05": "repeated_subtraction",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "abstract", "LEARN_03": "pictorial",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.5 'Relate Subtraction and Division' pp.237-240",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D — Repeated Subtraction and Division",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "repeated_subtraction")
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
        "title": "반복뺄셈 루틴 — 0이 될 때까지 빼는 횟수",
        "content": (
            "나눗셈은 같은 수를 0이 될 때까지 반복해서 빼는 것. "
            "예: 12 ÷ 4 풀려면 12에서 4를 몇 번 빼야 0이 되나? "
            "  12 − 4 = 8 (1번), 8 − 4 = 4 (2번), 4 − 4 = 0 (3번) → 답 3. "
            "단계 1) 시작값을 적기 (12). "
            "단계 2) 같은 수(4)를 반복해서 빼기. "
            "단계 3) 0에 도달할 때까지 횟수 세기 — 그 횟수가 답. "
            "흔한 실수 (M01): 단순 뺄셈으로 끝내는 학생 (12 − 4 = 8) — 0까지 반복해야 함."
        ),
        "cpa_stage": "abstract",
        "visual_type": "repeated_subtraction_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "수직선으로 점프 — 분배 나눗셈 시각화",
        "content": (
            "수직선에서 시작값에서 0까지 같은 크기로 점프. "
            "예: 30 ÷ 5 → 30에서 시작해 5씩 뒤로 점프 → 25, 20, 15, 10, 5, 0. "
            "점프 횟수 = 6 → 30 ÷ 5 = 6. "
            "팁: 점프마다 손가락 하나씩 — 끝나면 손가락 수가 답. "
            "🔍 검증: 마지막에 정확히 0에 도달하는지 확인 (도달 안 하면 계산 오류)."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "number_line_jumps",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "뺄셈 ↔ 나눗셈 — 같은 답을 두 가지 방법으로",
        "content": (
            "반복뺄셈 횟수 = 나눗셈의 답. "
            "예: 28에서 7을 4번 빼면 0 → 28 ÷ 7 = 4. "
            "예: 36에서 9를 4번 빼면 0 → 36 ÷ 9 = 4. "
            "역으로 풀어도 됨: 28 ÷ 7 = 4 → 7을 4번 빼면 0. "
            "팁: 큰 수(56 ÷ 8)는 곱셈으로 더 빨리 (8 × 7 = 56 → 7). "
            "반복뺄셈은 작은 수에서 의미를 이해하는 도구."
        ),
        "cpa_stage": "abstract",
        "visual_type": "subtraction_division_link",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 528 + 396.",
        "choices": ["A. 814", "B. 824", "C. 914", "D. 924"],
        "answer": "D",
        "explanation": "528+396: 8+6=14 (carry 1), 2+9+1=12 (carry 1), 5+3+1=9. Result: 924.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 14. Tens: 12. Hundreds: 9."],
        "feedback": {"correct": "Right — 924.", "incorrect": "528+396=924."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 805 − 469.",
        "choices": ["A. 336", "B. 346", "C. 436", "D. 446"],
        "answer": "A",
        "explanation": "805−469: 5−9 borrow → 15−9=6; tens 9−6=3 (after lending across zero); hundreds 7−4=3. Result: 336.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "805−469=336."],
        "feedback": {"correct": "Right — 336.", "incorrect": "805−469=336."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 723 books. They donated 256, then received 138 more. How many books now?",
        "choices": ["A. 467", "B. 543", "C. 605", "D. 743"],
        "answer": "C",
        "explanation": "Step 1: 723−256=467. Step 2: 467+138=605.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add received.", "723−256=467, 467+138=605."],
        "feedback": {"correct": "Right — 605 books.", "incorrect": "723−256=467, then +138=605."},
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
        "prerequisite": "G3 U6 L4 — 막대 모델로 나눗셈 표현 (3.OA.A.3)",
        "current":      "G3 — 반복뺄셈과 나눗셈의 관계 (3.OA.A.3)",
        "successor":    "G3 U6 L6 — 배열로 나눗셈 모델링 (3.OA.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
