"""
G3 U6 L9 — Division Rules for 1 and 0 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.5 (1과 0 나눗셈 — 4가지 규칙)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/L9_division_rules_for_1_and_0.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.B.5.M05"],
    "PT_02": ["3.OA.B.5.M05"],
    "PT_03": ["3.OA.B.5.M06"],
    "PT_04": ["3.OA.B.5.M06"],
    "PT_05": ["3.OA.B.5.M05"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.B.5.M05"],
    "TRY_02": ["3.OA.B.5.M06"],
    "TRY_03": ["3.OA.B.5.M05"],
    "TRY_04": ["3.OA.B.5.M06"],
    "TRY_05": ["3.OA.B.5.M05"],
    "R1_01": ["3.OA.B.5.M05"],
    "R1_02": ["3.OA.B.5.M05"],
    "R1_03": ["3.OA.B.5.M06"],
    "R1_04": ["3.OA.B.5.M05"],
    "R1_05": ["3.OA.B.5.M05"],
    "R1_06": ["3.OA.B.5.M06"],
    "R1_07": ["3.OA.B.5.M05"],
    "R1_08": ["3.OA.B.5.M05"],
    "R1_09": ["3.OA.B.5.M06"],
    "R1_10": ["3.OA.B.5.M06"],
    "R2_01": ["3.OA.B.5.M05"],
    "R2_02": ["3.OA.B.5.M06"],
    "R2_03": ["3.OA.B.5.M06"],
    "R2_04": ["3.OA.B.5.M06"],
    "R2_05": ["3.OA.B.5.M05"],
    "R2_06": ["3.OA.B.5.M06"],
    "R2_07": ["3.OA.B.5.M05"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.B.5.M05"],
    "R3_02": ["3.OA.B.5.M06"],
    "R3_03": ["3.OA.B.5.M05"],
    "R3_04": ["3.OA.B.5.M06"],
    "R3_05": ["3.OA.B.5.M05"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "division_rules_1_0" for i in range(1,6)},
    "LEARN_01": "divide_by_1",
    "LEARN_02": "divide_by_itself",
    "LEARN_03": "zero_dividend",
    "LEARN_04": "rules_on_number_line",
    "LEARN_05": "four_division_rules",
    "LEARN_06": "div_1_self_combined",
    "LEARN_07": "zero_dividend_routine",
    "LEARN_08": "divide_by_zero_undefined",
    **{f"TRY_0{i}": "division_rules_1_0" for i in range(1,6)},
    **{f"R1_{i:02d}": "division_rules_1_0" for i in range(1,11)},
    "R2_01": "division_rules_1_0",
    "R2_02": "zero_dividend",
    "R2_03": "combine_division_rules",
    "R2_04": "divide_by_zero_undefined",
    "R2_05": "divide_by_1",
    "R2_06": "zero_dividend",
    "R2_07": "divide_by_itself",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "combine_division_rules",
    "R3_02": "zero_dividend_pattern",
    "R3_03": "combine_division_rules",
    "R3_04": "combine_division_rules",
    "R3_05": "divide_by_1_inverse",
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
        "concept_source": "Go Math Grade 3 Ch.6 Lesson 6.9 'Division Rules for 1 and 0' pp.253-256",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic E — Properties of Division with 1 and 0",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "division_rules_1_0")
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
        "title": "÷1과 ÷자기 자신 — 두 규칙 묶음",
        "content": (
            "규칙 1) n ÷ 1 = n (1로 나누면 그대로). "
            "  예: 7 ÷ 1 = 7, 25 ÷ 1 = 25. "
            "  왜? '7개를 한 묶음으로' = 한 묶음에 7개. "
            "규칙 2) n ÷ n = 1 (자기 자신으로 나누면 1). "
            "  예: 7 ÷ 7 = 1, 25 ÷ 25 = 1. "
            "  왜? '7개를 7명에게 나누면' = 한 명당 1개. "
            "흔한 실수 (M05): 7 ÷ 1 = 1로 답하거나 7 ÷ 7 = 0/7로 답."
        ),
        "cpa_stage": "abstract",
        "visual_type": "div_1_self",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "0 ÷ n = 0 — 0 나누기는 항상 0",
        "content": (
            "규칙 3) 0 ÷ n = 0 (n ≠ 0이면 항상 0). "
            "  예: 0 ÷ 5 = 0, 0 ÷ 100 = 0, 0 ÷ 7 = 0. "
            "  왜? '0개를 5명에게 나누면' = 한 명당 0개 (아무도 못 받음). "
            "  또는 곱셈으로: 0 = ? × 5 → ? = 0. "
            "패턴: 0 ÷ 6 = 0, 0 ÷ 60 = 0, 0 ÷ 600 = 0 — 0 나누기는 항상 0. "
            "흔한 실수 (M06): 0 ÷ 5 = 5로 답 (방향 혼동)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "zero_dividend",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "n ÷ 0은 불가능 — 4번째 규칙",
        "content": (
            "규칙 4) n ÷ 0은 정의되지 않음(불가능). "
            "  예: 7 ÷ 0 = ? 답 없음. 5 ÷ 0 = ? 답 없음. "
            "  왜? '7개를 0명에게 나누면' = 의미 없음 (받을 사람이 없음). "
            "  또는 곱셈으로: 7 = ? × 0 → 어떤 수든 × 0 = 0이라 7이 될 수 없음. "
            "🔍 4가지 규칙 정리: "
            "  ① n ÷ 1 = n  ② n ÷ n = 1 (n≠0)  ③ 0 ÷ n = 0 (n≠0)  ④ n ÷ 0 = 불가능. "
            "흔한 실수 (M06): 7 ÷ 0 = 0 또는 = 7 — 둘 다 틀림 (답 없음)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "division_undefined",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 357 + 489.",
        "choices": ["A. 736", "B. 746", "C. 836", "D. 846"],
        "answer": "D",
        "explanation": "357+489: 7+9=16 (carry 1), 5+8+1=14 (carry 1), 3+4+1=8. Result: 846.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 16. Tens: 14. Hundreds: 8."],
        "feedback": {"correct": "Right — 846.", "incorrect": "357+489=846."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 700 − 458.",
        "choices": ["A. 242", "B. 252", "C. 342", "D. 352"],
        "answer": "A",
        "explanation": "700−458: 0−8 borrow → 10−8=2; tens 9−5=4 (after lending across zeros); hundreds 6−4=2. Result: 242.",
        "difficulty": 2,
        "hints": ["Borrow across two zeros.", "700−458=242."],
        "feedback": {"correct": "Right — 242.", "incorrect": "700−458=242."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A class had 567 stickers. They gave out 248, then bought 175 more. How many stickers now?",
        "choices": ["A. 319", "B. 423", "C. 494", "D. 644"],
        "answer": "C",
        "explanation": "Step 1: 567−248=319. Step 2: 319+175=494.",
        "difficulty": 3,
        "hints": ["Subtract given out, then add bought.", "567−248=319, 319+175=494."],
        "feedback": {"correct": "Right — 494 stickers.", "incorrect": "567−248=319, then +175=494."},
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
        "prerequisite": "G3 U6 L8 — 사실 패밀리 4식/2식 작성 (3.OA.B.6)",
        "current":      "G3 — 1과 0의 나눗셈 규칙 4가지 (3.OA.B.5)",
        "successor":    "G3 U7 L1 — 2/4/8 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_l9.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
