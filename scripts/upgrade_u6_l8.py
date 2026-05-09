"""
G3 U6 L8 — Write Related Facts 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.6 (사실 패밀리 — 4식/2식 작성)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L8_write_related_facts.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.A.2.M06"],
    "PT_02": ["3.OA.A.2.M06"],
    "PT_03": ["3.OA.A.2.M06"],
    "PT_04": ["3.OA.A.2.M06"],
    "PT_05": ["3.OA.A.2.M06"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.A.2.M06"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.A.2.M06"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.4.M01"],
    "R2_03": ["3.OA.A.2.M06"],
    "R2_04": ["3.OA.A.2.M06"],
    "R2_05": ["3.OA.A.2.M06"],
    "R2_06": ["3.OA.A.2.M06"],
    "R2_07": ["3.OA.A.2.M06"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.A.2.M06"],
    "R3_02": ["3.OA.A.4.M01"],
    "R3_03": ["3.OA.A.2.M06"],
    "R3_04": ["3.OA.A.2.M06"],
    "R3_05": ["3.OA.A.2.M06"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "fact_family" for i in range(1,6)},
    "LEARN_01": "fact_family_intro",
    "LEARN_02": "square_fact_family",
    "LEARN_03": "write_related_facts_steps",
    "LEARN_04": "fact_family_triangle",
    "LEARN_05": "fact_family_rule",
    "LEARN_06": "four_facts_routine",
    "LEARN_07": "two_facts_square",
    "LEARN_08": "fact_family_validation",
    **{f"TRY_0{i}": "fact_family" for i in range(1,6)},
    **{f"R1_{i:02d}": "fact_family" for i in range(1,11)},
    "R2_01": "square_fact_family",
    "R2_02": "missing_factor_family",
    "R2_03": "complete_fact_family",
    "R2_04": "count_fact_families",
    "R2_05": "fact_family",
    "R2_06": "find_product_from_factors",
    "R2_07": "fact_family",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "count_related_facts",
    "R3_02": "missing_factor_family",
    "R3_03": "square_fact_family",
    "R3_04": "complete_fact_family",
    "R3_05": "fact_family",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.8 'Write Related Facts' pp.249-252",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic E — Fact Families and Inverse Relationships",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "fact_family")
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
        "title": "패밀리 4식 — 한 사실로 4가지 쓰기",
        "content": (
            "세 수 (a, b, ab)로 만들 수 있는 4식: "
            "  a × b = ab "
            "  b × a = ab (교환법칙) "
            "  ab ÷ a = b (역연산) "
            "  ab ÷ b = a (역연산) "
            "예: 3, 8, 24 → 3×8=24, 8×3=24, 24÷3=8, 24÷8=3. "
            "단계 1) 가장 큰 수가 곱(ab) — 위쪽. "
            "단계 2) 작은 두 수가 인수(a, b) — 곱셈 두 식. "
            "단계 3) 나눗셈 두 식 (큰 수에서 작은 수 둘 각각으로). "
            "흔한 실수 (M06): 곱셈만 적고 나눗셈 빠뜨림."
        ),
        "cpa_stage": "abstract",
        "visual_type": "four_facts_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "정사각형 패밀리 — 4식이 아니라 2식만",
        "content": (
            "같은 두 인수가 곱해질 때(예: 6 × 6 = 36)는 패밀리에 식이 2개뿐. "
            "  6 × 6 = 36 (곱셈 1개 — 교환해도 같음) "
            "  36 ÷ 6 = 6 (나눗셈 1개 — 두 식이 같음) "
            "예: 9 × 9 = 81 → 81 ÷ 9 = 9 → 식 2개. "
            "예: 5 × 5 = 25 → 25 ÷ 5 = 5 → 식 2개. "
            "왜? 두 인수가 같으니 곱셈 교환·나눗셈 두 형태가 모두 같은 식이 됨."
        ),
        "cpa_stage": "abstract",
        "visual_type": "square_fact_family",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "패밀리 검증 — 세 수가 맞는지 확인",
        "content": (
            "주어진 세 수 (a, b, c)가 진짜 패밀리인지 확인: a × b = c 인가? "
            "예: 4, 5, 20 → 4 × 5 = 20 ✓ → 패밀리. "
            "예: 3, 4, 15 → 3 × 4 = 12 ≠ 15 ❌ → 패밀리 X. "
            "🔍 검증: 가장 큰 수를 다른 두 수의 곱과 비교. "
            "맞으면 4식(또는 정사각형이면 2식)을 모두 쓸 수 있음. "
            "흔한 실수: 우연히 비슷한 수를 보고 패밀리라고 착각."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fact_family_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 596 + 348.",
        "choices": ["A. 834", "B. 844", "C. 934", "D. 944"],
        "answer": "D",
        "explanation": "596+348: 6+8=14 (carry 1), 9+4+1=14 (carry 1), 5+3+1=9. Result: 944.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 14. Tens: 14. Hundreds: 9."],
        "feedback": {"correct": "Right — 944.", "incorrect": "596+348=944."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 902 − 547.",
        "choices": ["A. 355", "B. 365", "C. 455", "D. 465"],
        "answer": "A",
        "explanation": "902−547: 2−7 borrow → 12−7=5; tens 9−4=5 (after lending across zero); hundreds 8−5=3. Result: 355.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "902−547=355."],
        "feedback": {"correct": "Right — 355.", "incorrect": "902−547=355."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A store had 481 hats. They sold 167, then bought 248 more. How many hats now?",
        "choices": ["A. 314", "B. 462", "C. 562", "D. 896"],
        "answer": "C",
        "explanation": "Step 1: 481−167=314. Step 2: 314+248=562.",
        "difficulty": 3,
        "hints": ["Subtract sold, then add bought.", "481−167=314, 314+248=562."],
        "feedback": {"correct": "Right — 562 hats.", "incorrect": "481−167=314, then +248=562."},
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
        "prerequisite": "G3 U6 L7 — 곱셈과 나눗셈의 관계 (3.OA.B.6)",
        "current":      "G3 — 사실 패밀리 4식/2식 작성 (3.OA.B.6)",
        "successor":    "G3 U6 L9 — 1과 0의 나눗셈 규칙 (3.OA.B.5)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l8.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
