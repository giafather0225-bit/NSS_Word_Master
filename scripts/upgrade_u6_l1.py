"""
G3 U6 L1 — Model Division 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.2 / 3.OA.A.3 (나눗셈의 의미 — 분배·측정 모델)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L1_model_division.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.A.2.M02"],
    "PT_02": ["3.OA.A.2.M02"],
    "PT_03": ["3.OA.A.2.M02"],
    "PT_04": ["3.OA.A.2.M04"],
    "PT_05": ["3.OA.A.2.M04"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.A.2.M02"],
    "TRY_02": ["3.OA.A.2.M02"],
    "TRY_03": ["3.OA.A.2.M01"],
    "TRY_04": ["3.OA.A.2.M06"],
    "TRY_05": ["3.OA.A.2.M04"],
    "R1_01": ["3.OA.A.2.M01"],
    "R1_02": ["3.OA.A.2.M06"],
    "R1_03": ["3.OA.A.2.M06"],
    "R1_04": ["3.OA.A.2.M04"],
    "R1_05": ["3.OA.A.2.M06"],
    "R1_06": ["3.OA.A.2.M02"],
    "R1_07": ["3.OA.A.2.M06"],
    "R1_08": ["3.OA.A.2.M01"],
    "R1_09": ["3.OA.A.2.M04"],
    "R1_10": ["3.OA.A.2.M06"],
    "R2_01": ["3.OA.A.2.M02"],
    "R2_02": ["3.OA.A.2.M06"],
    "R2_03": ["3.OA.A.2.M04"],
    "R2_04": ["3.OA.A.2.M04"],
    "R2_05": ["3.OA.A.2.M06"],
    "R2_06": ["3.OA.A.2.M06"],
    "R2_07": ["3.OA.A.2.M06"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_02": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_03": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_05": ["3.OA.A.2.M04"],
}

SKILL_TAGS = {
    "PT_01": "partition_division_word",
    "PT_02": "quotative_division_word",
    "PT_03": "partition_division_word",
    "PT_04": "partition_division_word",
    "PT_05": "partition_division_word",
    "LEARN_01": "division_meaning",
    "LEARN_02": "model_with_counters",
    "LEARN_03": "division_multiplication_inverse",
    "LEARN_04": "bar_model_division",
    "LEARN_05": "division_equation_parts",
    "LEARN_06": "partition_vs_quotative",
    "LEARN_07": "fact_family_division",
    "LEARN_08": "equal_share_check",
    "TRY_01": "quotative_division_word",
    "TRY_02": "partition_division_word",
    "TRY_03": "division_basic_fact",
    "TRY_04": "division_basic_fact",
    "TRY_05": "partition_division_word",
    "R1_01": "division_basic_fact",
    "R1_02": "division_basic_fact",
    "R1_03": "division_basic_fact",
    "R1_04": "partition_division_word",
    "R1_05": "division_basic_fact",
    "R1_06": "partition_division_word",
    "R1_07": "division_basic_fact",
    "R1_08": "division_basic_fact",
    "R1_09": "partition_division_word",
    "R1_10": "division_basic_fact",
    "R2_01": "quotative_division_word",
    "R2_02": "division_basic_fact",
    "R2_03": "partition_division_word",
    "R2_04": "partition_division_word",
    "R2_05": "division_basic_fact",
    "R2_06": "fact_family_division",
    "R2_07": "division_basic_fact",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_combine",
    "R3_02": "two_step_division_subtract",
    "R3_03": "two_step_division_subtract",
    "R3_04": "two_step_division_subtract",
    "R3_05": "partition_division_word",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "pictorial", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.1 'Model Division' pp.221-224",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic D — Division as Sharing and Measurement",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "division_basic_fact")
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
        "title": "두 가지 나눗셈 — 나누어 주기 vs 묶어 세기",
        "content": (
            "나눗셈에는 두 가지 상황이 있습니다. "
            "① 분배 (partitive — 나누어 주기): 24개를 4명에게 똑같이 나누면 한 명당 몇 개? "
            "  → 24 ÷ 4 = 6 (한 명당 6개). "
            "② 측정 (quotative — 묶어 세기): 24개를 4개씩 묶으면 몇 묶음? "
            "  → 24 ÷ 4 = 6 (6묶음). "
            "두 상황 모두 같은 식 24 ÷ 4지만 의미가 다름! "
            "흔한 실수 (M02): 두 상황을 헷갈려 답의 단위를 잘못 말함."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "partition_vs_quotative",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "곱셈으로 나눗셈 풀기 — 패밀리 삼각형",
        "content": (
            "나눗셈은 곱셈의 역연산. 24 ÷ 6 = ? 풀려면 '몇 × 6 = 24?'를 떠올려라. "
            "패밀리 삼각형: 위쪽=곱(24), 아래 두 모서리=인수(4와 6). "
            "한 모서리를 가리면 그 자리가 답: 4 × 6 = 24, 6 × 4 = 24, 24 ÷ 6 = 4, 24 ÷ 4 = 6. "
            "이렇게 하나의 사실로 4가지 식을 모두 풀 수 있음. "
            "흔한 실수 (M06): 곱셈 사실 외워놓고도 나눗셈에서 다시 처음부터 세는 학생 — "
            "'곱셈으로 풀어보자'라는 습관을 들이세요."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fact_family_triangle",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "균등 분배 점검 — 모든 모둠이 같은가?",
        "content": (
            "나눗셈은 항상 똑같이 나누는 것. 답을 구한 뒤 검증: "
            "단계 1) 답 × 모둠 수 = 전체? (예: 24 ÷ 6 = 4 → 4 × 6 = 24 ✓). "
            "단계 2) 모든 모둠 크기가 같은가? (그림으로 그려서 확인). "
            "흔한 실수 (M04): 24를 5+4+5+4+3+3=24처럼 불균등하게 나누고 한 모둠을 답으로 — "
            "'똑같이' 조건 위반. "
            "🔍 검증: 단계 1을 통과해도 단계 2를 빠뜨리면 잘못 — 두 가지 모두 확인."
        ),
        "cpa_stage": "abstract",
        "visual_type": "equal_share_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 248 + 575.",
        "choices": ["A. 713", "B. 723", "C. 813", "D. 823"],
        "answer": "D",
        "explanation": "248+575: 8+5=13 (carry 1), 4+7+1=12 (carry 1), 2+5+1=8. Result: 823.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 13. Tens: 12. Hundreds: 8."],
        "feedback": {"correct": "Right — 823.", "incorrect": "248+575=823."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 803 − 467.",
        "choices": ["A. 336", "B. 346", "C. 436", "D. 446"],
        "answer": "A",
        "explanation": "803−467: 3−7 borrow → 13−7=6; tens 9−6=3 (after lending across zero); hundreds 7−4=3. Result: 336.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "803−467=336."],
        "feedback": {"correct": "Right — 336.", "incorrect": "803−467=336."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A store had 624 apples. They sold 287 and received 158 more. How many apples now?",
        "choices": ["A. 337", "B. 445", "C. 495", "D. 555"],
        "answer": "C",
        "explanation": "Step 1: 624−287=337. Step 2: 337+158=495.",
        "difficulty": 3,
        "hints": ["Subtract sold, then add received.", "624−287=337, 337+158=495."],
        "feedback": {"correct": "Right — 495 apples.", "incorrect": "624−287=337, then +158=495."},
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
        "prerequisite": "G3 U5 L5 — 한 자리 × 10의 배수 결정판 (3.NBT.A.3)",
        "current":      "G3 — 나눗셈의 의미: 분배·측정 모델 (3.OA.A.2 / 3.OA.A.3)",
        "successor":    "G3 U6 L2 — 모둠의 크기 구하기 (3.OA.A.2)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
