"""
G3 U5 L2 — Find Unknown Factors 7단계 업그레이드 스크립트 (재이주)
====================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.4 (미지수 인자 — 곱셈/나눗셈 역연산)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U5_use_multiplication_facts/L2_find_unknown_factors.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.A.4.M01"],
    "PT_02": ["3.OA.A.4.M01", "3.OA.A.4.M05"],
    "PT_03": ["3.OA.A.4.M01"],
    "PT_04": ["3.OA.A.4.M02"],
    "PT_05": ["3.OA.A.4.M02"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.A.4.M04"],
    "TRY_02": ["3.OA.A.4.M01"],
    "TRY_03": ["3.OA.A.4.M01"],
    "TRY_04": ["3.OA.A.4.M01"],
    "TRY_05": ["3.OA.A.4.M01"],
    "R1_01": ["3.OA.A.4.M04"],
    "R1_02": ["3.OA.A.4.M01"],
    "R1_03": ["3.OA.B.5.M05"],
    "R1_04": ["3.OA.A.4.M04"],
    "R1_05": ["3.OA.A.4.M01"],
    "R1_06": ["3.OA.A.4.M06"],
    "R1_07": ["3.OA.A.4.M01"],
    "R1_08": ["3.OA.A.4.M01"],
    "R1_09": ["3.OA.A.4.M06"],
    "R1_10": ["3.OA.A.4.M04"],
    "R2_01": ["3.OA.A.4.M01"],
    "R2_02": ["3.OA.A.4.M02"],
    "R2_03": ["3.OA.A.4.M02"],
    "R2_04": ["3.OA.A.4.M04"],
    "R2_05": ["3.OA.A.4.M01"],
    "R2_06": ["3.OA.A.4.M02"],
    "R2_07": ["3.OA.A.4.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.A.4.M02"],
    "R3_02": ["3.OA.A.4.M02"],
    "R3_03": ["3.OA.A.4.M03"],
    "R3_04": ["3.OA.A.4.M02"],
    "R3_05": ["3.OA.A.4.M02"],
}

SKILL_TAGS = {
    "PT_01": "missing_factor",
    "PT_02": "missing_factor",
    "PT_03": "missing_factor",
    "PT_04": "missing_factor_word",
    "PT_05": "missing_factor_word",
    "LEARN_01": "missing_factor_concept",
    "LEARN_02": "fact_family",
    "LEARN_03": "verify_solution",
    "LEARN_04": "missing_factor_word",
    "LEARN_05": "left_right_equation",
    "LEARN_06": "fact_family",
    "LEARN_07": "verify_solution",
    "LEARN_08": "missing_factor_strategies",
    "TRY_01": "missing_factor_left",
    "TRY_02": "missing_factor",
    "TRY_03": "missing_factor",
    "TRY_04": "missing_factor",
    "TRY_05": "missing_factor",
    "R1_01": "missing_factor_left",
    "R1_02": "missing_factor",
    "R1_03": "missing_factor_identity",
    "R1_04": "missing_factor_left",
    "R1_05": "missing_factor",
    "R1_06": "missing_factor",
    "R1_07": "missing_factor",
    "R1_08": "missing_factor",
    "R1_09": "missing_factor",
    "R1_10": "missing_factor_left",
    "R2_01": "missing_factor",
    "R2_02": "array_missing_factor",
    "R2_03": "missing_factor_word",
    "R2_04": "missing_factor_left",
    "R2_05": "missing_factor",
    "R2_06": "missing_factor_word",
    "R2_07": "missing_factor",
    "R2_08": "addition_3digit",       # U1
    "R2_09": "subtraction_3digit",    # U1
    "R2_10": "two_step_add_sub",      # U1
    "R3_01": "missing_factor_constraint",
    "R3_02": "set_up_equation",
    "R3_03": "verify_solution",
    "R3_04": "missing_factor_word",
    "R3_05": "missing_factor_word",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "abstract",
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
        "concept_source": "Go Math Grade 3 Ch.5 Lesson 5.2 'Find Unknown Factors' pp.193-196",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic E — Division as an Unknown-Factor Problem",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "missing_factor")
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
        "title": "사실 가족(Fact Family) — 곱셈과 나눗셈은 한 가족",
        "content": (
            "세 수 (6, 7, 42)는 4개의 식을 만듭니다 — '사실 가족'. "
            "곱셈: 6 × 7 = 42, 7 × 6 = 42. "
            "나눗셈: 42 ÷ 6 = 7, 42 ÷ 7 = 6. "
            "미지수를 찾을 때 활용: 6 × ? = 42에서 가족 멤버 7이 답. "
            "팁: 사실 가족 삼각형 — 위에 곱(42), 아래에 두 인자(6, 7). "
            "어느 모서리가 가려지면 그게 미지수. 곱이 가려지면 ×, 인자가 가려지면 ÷."
        ),
        "cpa_stage": "concrete",
        "visual_type": "fact_family_triangle",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "검증 — 답을 식에 다시 넣기",
        "content": (
            "미지수 답을 찾았으면 반드시 원식에 다시 넣어 확인. "
            "예: 7 × ? = 42에서 ? = 6이라 답했으면 — 7 × 6 = 42 ✓ 검증. "
            "잘못된 답: ? = 5라 답하면 7 × 5 = 35 ≠ 42 ❌. "
            "이 단계 없으면 '느낌 답'으로 자주 틀림 (M03 random_guess). "
            "검증은 1초밖에 안 걸리지만 정답률을 크게 올림. "
            "흔한 실수: 검증 없이 첫 답을 그대로 제출."
        ),
        "cpa_stage": "abstract",
        "visual_type": "verify_loop",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "미지수 인자 풀이 4단계 + 검증",
        "content": (
            "단계 1 식 분석: a × ? = b 또는 b = a × ?. "
            "단계 2 무엇이 가려졌는지 — 인자(둘 중 하나)? "
            "단계 3 나눗셈 적용: ? = b ÷ a. "
            "  예: 7 × ? = 42 → ? = 42 ÷ 7 = 6. "
            "단계 4 검증: 7 × 6 = 42 ✓. "
            "🔍 양변 어디든 미지수 가능: 56 = 8 × ? ↔ 8 × ? = 56 (같은 의미). "
            "교환법칙 활용: 9 × ? = 63 모르면 ? × 9 = 63으로 바꿔 ×9표 떠올리기."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 419 + 376.",
        "choices": ["A. 685", "B. 695", "C. 785", "D. 795"],
        "answer": "D",
        "explanation": "419+376: 9+6=15 (carry 1), 1+7+1=9, 4+3=7. Result: 795.",
        "difficulty": 2,
        "hints": [
            "Watch the carry from ones to tens.",
            "Ones: 15. Tens: 9. Hundreds: 7.",
        ],
        "feedback": {
            "correct": "Right — 795.",
            "incorrect": "419+376=795.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 506 − 248.",
        "choices": ["A. 248", "B. 258", "C. 348", "D. 358"],
        "answer": "B",
        "explanation": "506−248: 6−8 borrow → 16−8=8; tens 9−4=5 (after lending); hundreds 4−2=2. Result: 258.",
        "difficulty": 2,
        "hints": [
            "Borrow across the zero in tens.",
            "506−248=258.",
        ],
        "feedback": {
            "correct": "Right — 258.",
            "incorrect": "506−248=258.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bookstore had 542 books. They sold 187 books, then received 226 new ones. How many books now?",
        "choices": ["A. 355", "B. 503", "C. 581", "D. 955"],
        "answer": "C",
        "explanation": "Step 1: 542−187=355. Step 2: 355+226=581.",
        "difficulty": 3,
        "hints": [
            "Subtract sold, then add received.",
            "542−187=355, 355+226=581.",
        ],
        "feedback": {
            "correct": "Right — 581 books.",
            "incorrect": "542−187=355, then +226=581.",
        },
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
        "prerequisite": "G3 U3-U4 — 곱셈 사실 + 분배·결합법칙 (3.OA.B.5, 3.OA.C.7)",
        "current":      "G3 — 미지수 인자 찾기; 곱셈/나눗셈 역연산 (3.OA.A.4)",
        "successor":    "G3 U5 L3 — 분배법칙으로 큰 수 곱셈 (3.OA.B.5, 3.NBT.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u5_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
