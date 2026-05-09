"""
G3 U4 L5 — Multiply with 7 7단계 업그레이드 스크립트
====================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (×7 — 분배 5+2 또는 4+3, 가장 어려운 사실 가족)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L5_multiply_with_7.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.C.7.M05"],
    "PT_02": ["3.OA.C.7.M05"],
    "PT_03": ["3.OA.C.7.M05"],
    "PT_04": ["3.OA.C.7.M05", "3.OA.C.7.M07"],
    "PT_05": ["3.OA.C.7.M05"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.C.7.M05"],
    "TRY_02": ["3.OA.C.7.M05"],
    "TRY_03": ["3.OA.B.5.M03"],
    "TRY_04": ["3.OA.C.7.M05"],
    "TRY_05": ["3.OA.C.7.M05", "3.OA.C.7.M07"],
    "R1_01": ["3.OA.C.7.M05"],
    "R1_02": ["3.OA.C.7.M05"],
    "R1_03": ["3.OA.C.7.M05"],
    "R1_04": ["3.OA.B.5.M05"],
    "R1_05": ["3.OA.C.7.M05"],
    "R1_06": ["3.OA.C.7.M05"],
    "R1_07": ["3.OA.B.5.M01"],
    "R1_08": ["3.OA.C.7.M05"],
    "R1_09": ["3.OA.B.5.M06"],
    "R1_10": ["3.OA.C.7.M05"],
    "R2_01": ["3.OA.B.5.M03"],
    "R2_02": ["3.OA.C.7.M05"],
    "R2_03": ["3.OA.C.7.M05"],
    "R2_04": ["3.OA.A.1.M01"],
    "R2_05": ["3.OA.B.5.M03"],
    "R2_06": ["3.OA.C.7.M05"],
    "R2_07": ["3.OA.C.7.M05"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.C.7.M05"],
    "R3_02": ["3.OA.B.5.M03"],
    "R3_03": ["3.OA.C.7.M05"],
    "R3_04": ["3.OA.C.7.M05"],
    "R3_05": ["3.OA.C.7.M05"],
}

SKILL_TAGS = {
    "PT_01": "x7_with_x2",
    "PT_02": "x7_with_x5",
    "PT_03": "x7_decompose",
    "PT_04": "x7_decompose",
    "PT_05": "x7_word_problem",
    "LEARN_01": "x7_skip_count",
    "LEARN_02": "x7_decompose_5_2",
    "LEARN_03": "x7_array",
    "LEARN_04": "x7_commutative",
    "LEARN_05": "x7_real_world",
    "LEARN_06": "x7_decompose_5_2",
    "LEARN_07": "x7_one_more_group",
    "LEARN_08": "x7_strategies",
    "TRY_01": "x7_with_x3",
    "TRY_02": "x7_decompose",
    "TRY_03": "x7_decompose_5_2",
    "TRY_04": "x7_word_problem",
    "TRY_05": "x7_one_more_group",
    "R1_01": "x7_decompose",
    "R1_02": "x7_squared",
    "R1_03": "x7_with_x10",
    "R1_04": "x7_with_x1",
    "R1_05": "x7_with_x5",
    "R1_06": "x7_with_x3",
    "R1_07": "x7_commutative",
    "R1_08": "x7_decompose",
    "R1_09": "x7_with_x0",
    "R1_10": "x7_identify_product",
    "R2_01": "x7_decompose_5_2",
    "R2_02": "missing_factor_x7",
    "R2_03": "x7_decompose",
    "R2_04": "verify_x7_addition",
    "R2_05": "best_split_x7",
    "R2_06": "x7_squared",
    "R2_07": "missing_factor_x7",
    "R2_08": "identify_x7_decomposition",
    "R2_09": "x7_word_problem",
    "R2_10": "x7_decompose",
    "R2_08": "addition_3digit",      # U1 (override)
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "two_step_x7",
    "R3_02": "x7_one_more_group",
    "R3_03": "x7_word_problem",
    "R3_04": "two_step_x7",
    "R3_05": "two_step_x7",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
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
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.5 'Multiply with 7' pp.155-158",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic E — Multiplying with the Unit of 7",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "x7_decompose")
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
        "title": "×7 = ×5 + ×2 (가장 신뢰할 만한 분해)",
        "content": (
            "×7은 깔끔한 패턴이 없어 가장 어려운 사실 가족. "
            "해결법: 7 = 5 + 2로 분해. "
            "예: 7 × 8 = (5 × 8) + (2 × 8) = 40 + 16 = 56. "
            "이유: ×5 사실은 잘 외우고(끝자리 0/5), ×2는 더블이라 둘 다 쉬움. "
            "두 결과를 더하면 ×7 답. "
            "흔한 실수: 한 부분만 곱하고 멈춤 (40만 답으로 쓰는 경우)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "decomposition_diagram",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "이미 아는 사실에서 +1그룹 또는 −1그룹",
        "content": (
            "7 × 7 = 49는 한 번 외우면 좋습니다. 인접 사실은 ±7로 풀 수 있어요. "
            "예 — 7 × 8 = (7 × 7) + 7 = 49 + 7 = 56 (한 그룹 추가). "
            "예 — 7 × 6 = (7 × 7) − 7 = 49 − 7 = 42 (한 그룹 빼기). "
            "예 — 7 × 9 = (7 × 10) − 7 = 70 − 7 = 63 (×10에서 1 그룹 빼기). "
            "팁: ×10은 매우 쉬우므로 7 × 9는 항상 'x10−7'로 풀 수 있음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "adjacent_fact_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×7 즉답 전략 4가지 (어려운 사실 가족 정복)",
        "content": (
            "전략 1 분해 5+2: 7×n = 5n + 2n. 예 7×8 = 40+16 = 56. "
            "전략 2 분해 4+3: 7×n = 4n + 3n. 예 7×8 = 32+24 = 56. "
            "전략 3 ×10 빼기: 7×n = 10n − 3n. 예 7×8 = 80−24 = 56. "
            "전략 4 교환법칙 활용: 7×n을 모르면 n×7로 바꿔보기 (잘 외운 인자가 앞으로). "
            "검증: 7 × n의 곱은 7의 배수. 곱셈표에서 '7의 배수 줄'에 있어야 함."
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
        "question": "Find the sum: 379 + 256.",
        "choices": ["A. 525", "B. 535", "C. 625", "D. 635"],
        "answer": "D",
        "explanation": "379+256: 9+6=15 (carry 1), 7+5+1=13 (carry 1), 3+2+1=6. Result: 635.",
        "hints": [
            "Two carries.",
            "Ones: 15. Tens: 13. Hundreds: 6.",
        ],
        "feedback": {
            "correct": "Right — 635.",
            "incorrect": "379+256=635.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 700 − 247.",
        "choices": ["A. 443", "B. 453", "C. 543", "D. 553"],
        "answer": "B",
        "explanation": "700−247: 0−7 borrow → 10−7=3; tens 9−4=5 (after lending); hundreds 6−2=4. Result: 453.",
        "hints": [
            "Borrow across both zeros.",
            "700−247=453.",
        ],
        "feedback": {
            "correct": "Right — 453.",
            "incorrect": "700−247=453.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A school had 845 books. Students borrowed 268, then librarians added 174 new ones. How many books now?",
        "choices": ["A. 403", "B. 577", "C. 751", "D. 1287"],
        "answer": "C",
        "explanation": "Step 1: 845−268=577. Step 2: 577+174=751.",
        "hints": [
            "Subtract borrowed, then add new.",
            "845−268=577, 577+174=751.",
        ],
        "feedback": {
            "correct": "Right — 751 books.",
            "incorrect": "845−268=577, then +174=751.",
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
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U4 L1-L4 — ×2/×4/×5/×10/×3/×6 사실·분배법칙 (3.OA.C.7, 3.OA.B.5)",
        "current":      "G3 — ×7 사실 (분배 5+2/4+3, ×10−3 빼기 전략) (3.OA.C.7)",
        "successor":    "G3 U4 L6 — 결합법칙 (3.OA.B.5)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
