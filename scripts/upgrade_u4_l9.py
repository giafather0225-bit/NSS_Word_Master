"""
G3 U4 L9 — Multiply with 9 7단계 업그레이드 스크립트
====================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (×9 — 자릿수 합=9, 십의 자리=인자−1, ×10 빼기)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L9_multiply_with_9.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.C.7.M04"],
    "PT_02": ["3.OA.C.7.M04"],
    "PT_03": ["3.OA.C.7.M04"],
    "PT_04": ["3.OA.C.7.M04"],
    "PT_05": ["3.OA.C.7.M04"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.C.7.M04"],
    "TRY_02": ["3.OA.C.7.M04"],
    "TRY_03": ["3.OA.C.7.M04"],
    "TRY_04": ["3.OA.C.7.M04"],
    "TRY_05": ["3.OA.C.7.M04"],
    "R1_01": ["3.OA.C.7.M01"],
    "R1_02": ["3.OA.C.7.M04"],
    "R1_03": ["3.OA.C.7.M03"],
    "R1_04": ["3.OA.B.5.M05"],
    "R1_05": ["3.OA.C.7.M04"],
    "R1_06": ["3.OA.C.7.M04"],
    "R1_07": ["3.OA.B.5.M06"],
    "R1_08": ["3.OA.C.7.M04"],
    "R1_09": ["3.OA.B.5.M01"],
    "R1_10": ["3.OA.C.7.M04"],
    "R2_01": ["3.OA.C.7.M04"],
    "R2_02": ["3.OA.C.7.M04"],
    "R2_03": ["3.OA.C.7.M04"],
    "R2_04": ["3.OA.C.7.M04"],
    "R2_05": ["3.OA.D.9.M02"],
    "R2_06": ["3.OA.C.7.M04"],
    "R2_07": ["3.OA.C.7.M04"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.C.7.M04"],
    "R3_02": ["3.OA.B.5.M03"],
    "R3_03": ["3.OA.B.5.M03"],
    "R3_04": ["3.OA.C.7.M04"],
    "R3_05": ["3.OA.C.7.M04"],
}

SKILL_TAGS = {
    "PT_01": "x9_skip_count",
    "PT_02": "x9_with_x5",
    "PT_03": "x9_subtract_from_x10",
    "PT_04": "x9_two_digit_rule",
    "PT_05": "x9_squared",
    "LEARN_01": "x9_skip_count",
    "LEARN_02": "x9_subtract_from_x10",
    "LEARN_03": "x9_two_digit_rule",
    "LEARN_04": "x9_digit_sum_check",
    "LEARN_05": "x9_finger_trick",
    "LEARN_06": "x9_two_digit_rule",
    "LEARN_07": "x9_subtract_from_x10",
    "LEARN_08": "x9_strategies",
    "TRY_01": "x9_subtract_from_x10",
    "TRY_02": "x9_subtract_from_x10",
    "TRY_03": "x9_two_digit_rule",
    "TRY_04": "x9_digit_sum_check",
    "TRY_05": "x9_word_problem",
    "R1_01": "x9_with_x2",
    "R1_02": "x9_two_digit_rule",
    "R1_03": "x9_with_x10",
    "R1_04": "x9_with_x1",
    "R1_05": "x9_with_x5",
    "R1_06": "x9_two_digit_rule",
    "R1_07": "x9_with_x0",
    "R1_08": "x9_squared",
    "R1_09": "x9_commutative",
    "R1_10": "x9_identify_product",
    "R2_01": "x9_digit_sum_check",
    "R2_02": "missing_factor_x9",
    "R2_03": "x9_two_digit_rule",
    "R2_04": "x9_two_digit_rule_apply",
    "R2_05": "x9_even_product",
    "R2_06": "x9_two_digit_rule",
    "R2_07": "missing_factor_x9",
    "R2_08": "identify_x9_decomposition",
    "R2_09": "x9_two_digit_rule",
    "R2_10": "x9_digit_sum_check",
    "R2_08": "addition_3digit",       # U1 (override)
    "R2_09": "subtraction_3digit",    # U1
    "R2_10": "two_step_add_sub",      # U1
    "R3_01": "two_step_x9",
    "R3_02": "verify_x9_distributive",
    "R3_03": "x9_two_digit_extension",
    "R3_04": "two_step_x9_word",
    "R3_05": "two_step_x9",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "concrete",
    "LEARN_06": "concrete", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.9 'Multiply with 9' pp.171-174",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic E — Multiplying with the Unit of 9",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "x9_two_digit_rule")
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
        "title": "×9 두 자리 규칙 (가장 강력한 패턴)",
        "content": (
            "9 × n의 두 자리는 항상 두 가지 규칙으로 결정됨: "
            "1) 십의 자리 = (n − 1). "
            "2) 일의 자리 = (10 − n). "
            "두 자리 합은 항상 9. "
            "예: 9 × 4 → 십=3, 일=6 → 36 (3+6=9 ✓). "
            "예: 9 × 7 → 십=6, 일=3 → 63 (6+3=9 ✓). "
            "예: 9 × 8 → 십=7, 일=2 → 72 (7+2=9 ✓). "
            "흔한 실수: 십의 자리에 (n−1) 대신 n을 그대로 쓰는 경우."
        ),
        "cpa_stage": "concrete",
        "visual_type": "two_digit_rule_chart",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×9 = ×10 − 자기 자신 (한 줄 풀이)",
        "content": (
            "9는 10보다 1 작으므로 — 9 × n = 10 × n − n. "
            "예: 9 × 7 = 70 − 7 = 63. "
            "예: 9 × 6 = 60 − 6 = 54. "
            "예: 9 × 8 = 80 − 8 = 72. "
            "장점: ×10은 즉답 (n에 0 붙이기), 그 다음 n 한 번만 빼면 끝. "
            "검증: 두 자리 합이 9가 되는지 확인 (예: 63 → 6+3=9 ✓)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "subtraction_strategy",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "×9 즉답 전략 4가지 + 검증법",
        "content": (
            "전략 1 두 자리 규칙: 십=n−1, 일=10−n. "
            "전략 2 ×10 빼기: 9n = 10n − n. "
            "전략 3 손가락 트릭: 손가락 10개 펴고 n번째 손가락 접기. 왼쪽=십, 오른쪽=일. "
            "전략 4 분배 5+4: 9 × n = (5n) + (4n). 예 9×8 = 40+32 = 72. "
            "🔍 검증법 (자릿수 합 검사): 정답이라면 두 자리 합 = 9. "
            "  예: 9 × 4 = 36 → 3+6=9 ✓. 잘못된 답 9 × 5 = 48 → 4+8=12 ≠ 9 ❌."
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
        "question": "Find the sum: 549 + 268.",
        "choices": ["A. 707", "B. 717", "C. 807", "D. 817"],
        "answer": "D",
        "explanation": "549+268: 9+8=17 (carry 1), 4+6+1=11 (carry 1), 5+2+1=8. Result: 817.",
        "hints": [
            "Two carries.",
            "Ones: 17. Tens: 11. Hundreds: 8.",
        ],
        "feedback": {
            "correct": "Right — 817.",
            "incorrect": "549+268=817.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 813 − 467.",
        "choices": ["A. 346", "B. 356", "C. 446", "D. 456"],
        "answer": "A",
        "explanation": "813−467: 3−7 borrow → 13−7=6; tens 0−6 borrow → 10−6=4 (after lending); hundreds 7−4=3. Result: 346.",
        "hints": [
            "Borrow across the zero in tens.",
            "813−467=346.",
        ],
        "feedback": {
            "correct": "Right — 346.",
            "incorrect": "813−467=346.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A warehouse had 645 boxes. They shipped 287, then received 156 more. How many boxes now?",
        "choices": ["A. 358", "B. 514", "C. 671", "D. 802"],
        "answer": "B",
        "explanation": "Step 1: 645−287=358. Step 2: 358+156=514.",
        "hints": [
            "Subtract shipped, then add received.",
            "645−287=358, 358+156=514.",
        ],
        "feedback": {
            "correct": "Right — 514 boxes.",
            "incorrect": "645−287=358, then +156=514.",
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
        "prerequisite": "G3 U4 L1-L8 — 모든 ×n 사실 (×8 포함), 분배·결합법칙 (3.OA.C.7, 3.OA.B.5)",
        "current":      "G3 — ×9 사실 (자릿수 합=9, 십=n−1, ×10−n) (3.OA.C.7)",
        "successor":    "G3 U4 L10 — 두 단계 워드프로블럼 (3.OA.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l9.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
