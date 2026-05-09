"""
G3 U8 L2 — Equal Shares 7단계 마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.1 (균등 공유 — 분수의 의미 적용)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L2_equal_shares.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.1.M03"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    "TRY_01": ["3.NF.A.1.M03"],
    "TRY_02": ["3.NF.A.1.M03"],
    "TRY_03": ["3.NF.A.1.M03"],
    "TRY_04": ["3.NF.A.1.M02"],
    "TRY_05": ["3.NF.A.1.M01"],
    **{f"R1_{i:02d}": ["3.NF.A.1.M03"] for i in range(1,11)},
    "R2_01": ["3.NF.A.1.M01"],
    "R2_02": ["3.NF.A.1.M04"],
    "R2_03": ["3.NF.A.1.M04"],
    "R2_04": ["3.NF.A.1.M05"],
    "R2_05": ["3.NF.A.1.M03"],
    "R2_06": ["3.NF.A.1.M04"],
    "R2_07": ["3.NF.A.1.M04"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.NF.A.1.M04"],
    "R3_02": ["3.NF.A.1.M01"],
    "R3_03": ["3.NF.A.1.M03"],
    "R3_04": ["3.NF.A.1.M02"],
    "R3_05": ["3.NF.A.1.M04"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "equal_shares" for i in range(1,6)},
    "LEARN_01": "equal_shares_intro",
    "LEARN_02": "different_shapes_same_fraction",
    "LEARN_03": "equal_vs_unequal",
    "LEARN_04": "sixths_eighths",
    "LEARN_05": "name_equal_shares",
    "LEARN_06": "denominator_meaning",
    "LEARN_07": "share_routine",
    "LEARN_08": "fraction_left_check",
    **{f"TRY_0{i}": "equal_shares" for i in range(1,6)},
    **{f"R1_{i:02d}": "equal_shares" for i in range(1,11)},
    "R2_01": "equal_vs_unequal",
    "R2_02": "fraction_one_part",
    "R2_03": "fraction_remaining",
    "R2_04": "different_shapes_halves",
    "R2_05": "halve_again",
    "R2_06": "fraction_eaten",
    "R2_07": "fraction_one_part",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "share_two_objects",
    "R3_02": "validate_equal_shares",
    "R3_03": "halve_again_naming",
    "R3_04": "combine_unit_fractions",
    "R3_05": "validate_shaded",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.2 'Equal Shares' pp.321-324",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic A — Equal Sharing and Fraction Notation",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_item(item: dict) -> dict:
    item_id = item["id"]
    if item_id.startswith("LRN_"):
        item_id = f"LEARN_{item_id[4:]}"
        item["id"] = item_id
    elif item_id.startswith("LN_"):
        item_id = f"LEARN_{item_id[3:]}"
        item["id"] = item_id
    if item_id.startswith("LEARN_") and item.get("type") == "card":
        item["type"] = "concept_card"
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "equal_shares")
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
        "title": "분모의 의미 — 전체를 몇 등분?",
        "content": (
            "분수 a/b에서 분모(b)는 '전체를 몇 등분으로 나누었나?'를 알려줌. "
            "  분모 2 = 두 등분 (halves) "
            "  분모 4 = 네 등분 (fourths) "
            "  분모 6 = 여섯 등분 (sixths) "
            "  분모 8 = 여덟 등분 (eighths) "
            "분모가 클수록 한 조각은 작음 (1/8 < 1/4 < 1/2). "
            "팁: 분모는 'pieces in the whole', 분자는 'pieces I have'."
        ),
        "cpa_stage": "abstract",
        "visual_type": "denominator_meaning",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "균등 공유 루틴 — 3단계 절차",
        "content": (
            "물체를 여러 사람에게 똑같이 나누기: "
            "단계 1) 사람 수 확인 → 분모. "
            "단계 2) 한 사람이 받는 갯수 → 분자 (보통 1). "
            "단계 3) 분자/분모로 적기. "
            "예: 4명이 1개 피자 공유 → 한 명당 1/4. "
            "예: 6명이 1개 케이크 공유 → 한 명당 1/6. "
            "흔한 실수 (M03): 받는 사람 수와 분수 이름을 헷갈림."
        ),
        "cpa_stage": "abstract",
        "visual_type": "equal_share_routine",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "남은 분수 검산 — 먹은 + 남은 = 1 (전체)",
        "content": (
            "전체에서 일부를 빼면 남은 분수도 알 수 있음. "
            "예: 4조각 중 1조각 먹음 → 먹은 1/4, 남은 3/4 (1/4 + 3/4 = 4/4 = 1). "
            "예: 8조각 중 3조각 먹음 → 먹은 3/8, 남은 5/8 (3/8 + 5/8 = 8/8 = 1). "
            "🔍 검증: 먹은 분수 + 남은 분수 = 1 (분모/분모). "
            "흔한 실수 (M04): 전체를 잊고 먹은 부분만 분수로 답."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fraction_complement",
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
        "question": "Find the difference: 803 − 458.",
        "choices": ["A. 345", "B. 355", "C. 445", "D. 455"],
        "answer": "A",
        "explanation": "803−458: 3−8 borrow → 13−8=5; tens 9−5=4 (after lending across zero); hundreds 7−4=3. Result: 345.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "803−458=345."],
        "feedback": {"correct": "Right — 345.", "incorrect": "803−458=345."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A class had 587 stickers. They gave out 246, then bought 158 more. How many stickers now?",
        "choices": ["A. 341", "B. 433", "C. 499", "D. 587"],
        "answer": "C",
        "explanation": "Step 1: 587−246=341. Step 2: 341+158=499.",
        "difficulty": 3,
        "hints": ["Subtract given out, then add bought.", "587−246=341, 341+158=499."],
        "feedback": {"correct": "Right — 499 stickers.", "incorrect": "587−246=341, then +158=499."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 새 7단계 표준으로 업그레이드됨.")
        return

    sections = d.get("sections", {})
    sections_map = {
        "pretest": sections.get("pretest", []),
        "learn": sections.get("learn", []),
        "try": sections.get("try", []),
        "practice_r1": sections.get("practice_r1", []),
        "practice_r2": sections.get("practice_r2", []),
        "practice_r3": sections.get("practice_r3", []),
    }

    # Rename LRN_ → LEARN_ in learn list before extending
    for it in sections_map["learn"]:
        if it["id"].startswith("LRN_"):
            it["id"] = f"LEARN_{it['id'][4:]}"

    sections_map["learn"].extend(NEW_LEARN_CARDS)

    # Replace last 3 R2 with U1 review
    sections_map["practice_r2"] = sections_map["practice_r2"][:7]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key in sections_map:
        sections_map[sec_key] = [normalize_item(it) for it in sections_map[sec_key]]

    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    d.pop("sections", None)
    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U8 L1 — 전체의 균등 분할: 분수 이름 (3.NF.A.1)",
        "current":      "G3 — 균등 공유: 분수의 의미 적용 (3.NF.A.1)",
        "successor":    "G3 U8 L3 — 단위분수 1/b (3.NF.A.1)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
