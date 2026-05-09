"""
G3 U6 L4 — Model with Bar Models 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.3 (나눗셈을 막대 모델로 표현)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L4_model_with_bar_models.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.A.2.M02"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.A.2.M02"] for i in range(1,6)},
    "R1_01": ["3.OA.A.2.M02"],
    "R1_02": ["3.OA.A.2.M06"],
    "R1_03": ["3.OA.A.2.M02"],
    "R1_04": ["3.OA.A.2.M06"],
    "R1_05": ["3.OA.A.2.M02"],
    "R1_06": ["3.OA.A.2.M06"],
    "R1_07": ["3.OA.A.2.M02"],
    "R1_08": ["3.OA.A.2.M02"],
    "R1_09": ["3.OA.A.2.M02"],
    "R1_10": ["3.OA.A.2.M02"],
    "R2_01": ["3.OA.A.2.M02"],
    "R2_02": ["3.OA.A.2.M02"],
    "R2_03": ["3.OA.A.4.M01"],
    "R2_04": ["3.OA.A.2.M03"],
    "R2_05": ["3.OA.A.2.M02"],
    "R2_06": ["3.OA.A.2.M03"],
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
    **{f"PT_0{i}": "bar_model_division" for i in range(1,6)},
    "LEARN_01": "bar_model_intro",
    "LEARN_02": "draw_bar_model",
    "LEARN_03": "two_division_types",
    "LEARN_04": "read_bar_model",
    "LEARN_05": "bar_model_equation",
    "LEARN_06": "bar_model_routine",
    "LEARN_07": "bar_model_equation_translation",
    "LEARN_08": "bar_model_total_check",
    **{f"TRY_0{i}": "bar_model_division" for i in range(1,6)},
    **{f"R1_{i:02d}": "bar_model_division" for i in range(1,11)},
    "R2_01": "bar_model_division",
    "R2_02": "rate_division_word",
    "R2_03": "bar_model_missing_divisor",
    "R2_04": "bar_model_to_equation",
    "R2_05": "bar_model_division",
    "R2_06": "bar_model_to_equation",
    "R2_07": "bar_model_division",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_combine",
    "R3_02": "two_step_division_combine",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "bar_model_division",
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "pictorial", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,6)},
    **{f"R1_{i:02d}": "pictorial" for i in range(1,11)},
    **{f"R2_{i:02d}": "pictorial" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.4 'Model with Bar Models' pp.233-236",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D — Bar Models for Division Word Problems",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "bar_model_division")
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
        "title": "막대 모델 그리기 — 3단계 루틴",
        "content": (
            "단계 1) 긴 막대를 그려 전체(예: 24)를 위에 적기. "
            "단계 2) 막대를 똑같은 칸으로 나누기 — 칸 수는 모둠 수(예: 6칸). "
            "단계 3) 한 칸에 ?를 적고 식 세우기: 24 ÷ 6 = ?. "
            "주의: 모든 칸이 같은 크기여야 함 (그렇지 않으면 분배 X). "
            "팁: 자를 사용하거나 점선으로 가지런히 — 깔끔한 그림이 정확한 답으로 이어짐."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "bar_model_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "막대 → 식 — 그림에서 식 읽어내기",
        "content": (
            "막대 모델을 보고 식을 세우는 방법: "
            "① 위쪽 큰 숫자 = 전체(피제수). "
            "② 칸 수 = 모둠 수(제수). "
            "③ 한 칸 안의 ? 또는 숫자 = 답(몫). "
            "예: 위 36, 칸 4개, 한 칸 ? → 식: 36 ÷ 4 = 9. "
            "🔍 검증: 9 × 4 = 36 ✓ (한 칸 × 칸 수 = 전체)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "bar_to_equation",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "전체 검산 — 칸들을 모두 더하면 전체",
        "content": (
            "막대 모델로 답을 구한 뒤 검산: "
            "한 칸의 값 × 칸 수 = 위쪽 전체? "
            "예: 42 ÷ 7 = 6 → 검산: 6 × 7 = 42 ✓. "
            "예: 64 ÷ 8 = 8 → 검산: 8 × 8 = 64 ✓. "
            "흔한 실수 (M03): 위·아래 숫자를 뒤집어 7 ÷ 42를 시도 — "
            "전체(큰 수)는 항상 위, 모둠 수(작은 수)는 칸 수로."
        ),
        "cpa_stage": "abstract",
        "visual_type": "bar_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 458 + 387.",
        "choices": ["A. 735", "B. 745", "C. 835", "D. 845"],
        "answer": "D",
        "explanation": "458+387: 8+7=15 (carry 1), 5+8+1=14 (carry 1), 4+3+1=8. Result: 845.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 14. Hundreds: 8."],
        "feedback": {"correct": "Right — 845.", "incorrect": "458+387=845."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 904 − 568.",
        "choices": ["A. 336", "B. 346", "C. 436", "D. 446"],
        "answer": "A",
        "explanation": "904−568: 4−8 borrow → 14−8=6; tens 9−6=3 (after lending); hundreds 8−5=3. Result: 336.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "904−568=336."],
        "feedback": {"correct": "Right — 336.", "incorrect": "904−568=336."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 645 erasers. They gave out 278, then bought 156 more. How many erasers now?",
        "choices": ["A. 367", "B. 433", "C. 523", "D. 745"],
        "answer": "C",
        "explanation": "Step 1: 645−278=367. Step 2: 367+156=523.",
        "difficulty": 3,
        "hints": ["Subtract given out, then add bought.", "645−278=367, 367+156=523."],
        "feedback": {"correct": "Right — 523 erasers.", "incorrect": "645−278=367, then +156=523."},
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
        "prerequisite": "G3 U6 L3 — 측정 나눗셈: 모둠의 개수 (3.OA.A.2)",
        "current":      "G3 — 막대 모델로 나눗셈 표현 (3.OA.A.3)",
        "successor":    "G3 U6 L5 — 뺄셈과 나눗셈의 관계 (3.OA.A.2)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
