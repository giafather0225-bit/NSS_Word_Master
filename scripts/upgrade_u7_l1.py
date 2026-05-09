"""
G3 U7 L1 — Divide by 2 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (2 나눗셈 사실 — 절반/더블 전략)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L1_divide_by_2.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.A.2.M06"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.A.2.M06"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.A.2.M06"] for i in range(1,11)},
    "R2_01": ["3.OA.A.2.M06"],
    "R2_02": ["3.OA.A.4.M01"],
    "R2_03": ["3.OA.C.7.M01"],
    "R2_04": ["3.OA.A.2.M02"],
    "R2_05": ["3.OA.A.2.M02"],
    "R2_06": ["3.OA.A.2.M06"],
    "R2_07": ["3.OA.A.2.M06"],
    "R2_08": ["3.OA.C.7.M01"],
    "R2_09": ["3.OA.A.2.M02"],
    "R2_10": ["3.OA.D.8.M01", "3.OA.A.2.M06"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M06"],
    "R3_02": ["3.OA.D.8.M01", "3.OA.A.4.M01"],
    "R3_03": ["3.OA.A.2.M06"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M06"],
    "R3_05": ["3.OA.A.4.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "divide_by_2" for i in range(1,6)},
    "LEARN_01": "divide_by_2",
    "LEARN_02": "use_doubles",
    "LEARN_03": "model_two_groups",
    "LEARN_04": "halving_number_line",
    "LEARN_05": "halving_rule",
    "LEARN_06": "halving_routine",
    "LEARN_07": "doubles_inverse",
    "LEARN_08": "halving_check",
    **{f"TRY_0{i}": "divide_by_2" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_2" for i in range(1,11)},
    "R2_01": "divide_by_2_inverse",
    "R2_02": "missing_dividend",
    "R2_03": "compare_quotients",
    "R2_04": "rate_division_word",
    "R2_05": "divide_by_2",
    "R2_06": "halving_measurement",
    "R2_07": "divide_by_2_inverse",
    "R2_08": "identify_not_half",
    "R2_09": "divide_by_2",
    "R2_10": "two_step_division_subtract",
    "R3_01": "two_step_division_combine",
    "R3_02": "two_step_unknown_factor",
    "R3_03": "compare_equal_quotients",
    "R3_04": "two_step_division_add",
    "R3_05": "missing_dividend",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "concrete",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.1 'Divide by 2' pp.265-268",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Halving and Doubling",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_2")
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
        "title": "절반 루틴 — ÷2는 반으로 자르기",
        "content": (
            "÷2 = 반으로. 즉 두 그룹으로 똑같이 나누기. "
            "예: 14 ÷ 2 → 14의 반 = 7. "
            "예: 18 ÷ 2 → 18의 반 = 9. "
            "단계 1) 짝수인지 확인 (이번 단원은 모두 짝수). "
            "단계 2) 두 그룹으로 나눠 한 쪽 세기 = 답. "
            "팁: 두 자리 짝수 → 십의 자리 ÷ 2 + 일의 자리 ÷ 2. "
            "예: 16 ÷ 2 = (10 ÷ 2) + (6 ÷ 2) = 5 + 3 = 8."
        ),
        "cpa_stage": "abstract",
        "visual_type": "halving_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "더블의 역연산 — ÷2는 ×2의 반대",
        "content": (
            "더블(×2)을 알면 ÷2도 즉답. "
            "예: 2 × 7 = 14 → 14 ÷ 2 = 7. "
            "예: 2 × 9 = 18 → 18 ÷ 2 = 9. "
            "곱셈 사실로 사고: 14 ÷ 2 = ? → '몇 × 2 = 14?' → 7. "
            "흔한 실수 (M06): 곱셈으로 풀 줄 알면서도 ÷2에서 다시 그림 — "
            "'더블 짝꿍'을 항상 활용."
        ),
        "cpa_stage": "abstract",
        "visual_type": "doubles_inverse",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "절반 검증 — 답 + 답 = 원래 수?",
        "content": (
            "÷2 답을 구한 뒤 검산: 답 + 답 = 원래 수? "
            "예: 18 ÷ 2 = 9 → 검산: 9 + 9 = 18 ✓. "
            "예: 14 ÷ 2 = 7 → 검산: 7 + 7 = 14 ✓. "
            "또는 답 × 2 = 원래 수? (곱셈 검산). "
            "🔍 두 가지 검산이 모두 통과해야 정답."
        ),
        "cpa_stage": "abstract",
        "visual_type": "halving_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 268 + 547.",
        "choices": ["A. 705", "B. 715", "C. 805", "D. 815"],
        "answer": "D",
        "explanation": "268+547: 8+7=15 (carry 1), 6+4+1=11 (carry 1), 2+5+1=8. Result: 815.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 15. Tens: 11. Hundreds: 8."],
        "feedback": {"correct": "Right — 815.", "incorrect": "268+547=815."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 503 − 167.",
        "choices": ["A. 336", "B. 346", "C. 436", "D. 446"],
        "answer": "A",
        "explanation": "503−167: 3−7 borrow → 13−7=6; tens 9−6=3 (after lending across zero); hundreds 4−1=3. Result: 336.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "503−167=336."],
        "feedback": {"correct": "Right — 336.", "incorrect": "503−167=336."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 392 magazines. They donated 148, then received 235 more. How many magazines now?",
        "choices": ["A. 244", "B. 379", "C. 479", "D. 775"],
        "answer": "C",
        "explanation": "Step 1: 392−148=244. Step 2: 244+235=479.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add received.", "392−148=244, 244+235=479."],
        "feedback": {"correct": "Right — 479 magazines.", "incorrect": "392−148=244, then +235=479."},
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
        "prerequisite": "G3 U6 L9 — 1과 0의 나눗셈 규칙 (3.OA.B.5)",
        "current":      "G3 — 2 나눗셈 사실: 절반/더블 전략 (3.OA.C.7)",
        "successor":    "G3 U7 L2 — 10 나눗셈 사실 (3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
