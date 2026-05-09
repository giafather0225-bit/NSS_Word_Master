"""
G3 U7 L9 — Divide by 9 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.C.7 (9 나눗셈 사실 — 자릿수 합 9 패턴 / ×9 역연산)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L9_divide_by_9.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.C.7.M04"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.C.7.M04"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.C.7.M04"] for i in range(1,11)},
    "R2_01": ["3.OA.C.7.M04"],
    "R2_02": ["3.OA.A.2.M06"],
    "R2_03": ["3.OA.A.4.M01"],
    "R2_04": ["3.OA.C.7.M04"],
    "R2_05": ["3.OA.B.5.M05"],
    "R2_06": ["3.OA.A.4.M01"],
    "R2_07": ["3.OA.C.7.M04"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_02": ["3.OA.C.7.M04"],
    "R3_03": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.A.2.M02"],
    "R3_05": ["3.OA.A.4.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "divide_by_9" for i in range(1,6)},
    "LEARN_01": "divide_by_9",
    "LEARN_02": "array_nine_rows",
    "LEARN_03": "digit_sum_trick",
    "LEARN_04": "number_line_jumps_9",
    "LEARN_05": "reverse_times_9",
    "LEARN_06": "digit_sum_routine",
    "LEARN_07": "times_9_inverse",
    "LEARN_08": "div_9_check",
    **{f"TRY_0{i}": "divide_by_9" for i in range(1,6)},
    **{f"R1_{i:02d}": "divide_by_9" for i in range(1,11)},
    "R2_01": "digit_sum_check",
    "R2_02": "divide_by_9_inverse",
    "R2_03": "missing_dividend_9",
    "R2_04": "compare_quotients",
    "R2_05": "divide_by_self",
    "R2_06": "missing_dividend_9",
    "R2_07": "identify_correct_9_fact",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "two_step_division_multiply",
    "R3_02": "digit_sum_check",
    "R3_03": "two_step_division_combine",
    "R3_04": "two_step_division_subtract",
    "R3_05": "missing_dividend_9",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.9 'Divide by 9' pp.297-300",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Division Facts: Divide by 9",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "divide_by_9")
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
        "title": "자릿수 합 9 트릭 — ÷9 마법 같은 패턴",
        "content": (
            "9의 배수는 자릿수의 합이 항상 9 (또는 9의 배수). "
            "예: 18 → 1+8 = 9 ✓, 27 → 2+7 = 9 ✓, 36 → 3+6 = 9 ✓. "
            "예: 45→9, 54→9, 63→9, 72→9, 81→9, 90→9. "
            "활용: ÷9 풀기 전에 '이 수가 9의 배수인가?'를 자릿수 합으로 빠르게 점검. "
            "흔한 실수 (M04): 9단을 외우지 않고 추측 — 자릿수 합 트릭으로 검증부터."
        ),
        "cpa_stage": "abstract",
        "visual_type": "digit_sum_trick",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "×9의 역연산 — 손가락 트릭/×10−한번",
        "content": (
            "×9 = ×10 − 자기 (예: 9 × 7 = 70 − 7 = 63). "
            "사고 절차: 63 ÷ 9 = ? → '몇 × 9 = 63?' → 7 (왜냐: 7 × 10 = 70, 70 − 7 = 63 ✓). "
            "예: 72 ÷ 9 → '몇 × 9 = 72?' → 8 (8 × 10 = 80, 80 − 8 = 72 ✓). "
            "팁: ×10 다음 자기 빼기는 머릿속 1초 — 9단 즉답 가능. "
            "예: 9 × 6 = 60 − 6 = 54 → 54 ÷ 9 = 6."
        ),
        "cpa_stage": "abstract",
        "visual_type": "times_9_inverse",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "÷9 검증 — 답 × 9 = 원래 수?",
        "content": (
            "÷9 답을 구한 뒤 검산: 답 × 9 = 원래 수? "
            "예: 63 ÷ 9 = 7 → 검산: 7 × 9 = 70 − 7 = 63 ✓. "
            "예: 81 ÷ 9 = 9 → 검산: 9 × 9 = 81 ✓ (정사각형 사실). "
            "🔍 추가 검증: 원래 수의 자릿수 합이 9인가? "
            "  예: 81 → 8+1 = 9 ✓ (9의 배수 맞음). "
            "흔한 실수 (M04): 9단 추측만으로 답 적기 — 자릿수 합과 곱셈 검산 둘 다 사용."
        ),
        "cpa_stage": "abstract",
        "visual_type": "div_9_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 358 + 476.",
        "choices": ["A. 724", "B. 734", "C. 824", "D. 834"],
        "answer": "D",
        "explanation": "358+476: 8+6=14 (carry 1), 5+7+1=13 (carry 1), 3+4+1=8. Result: 834.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 14. Tens: 13. Hundreds: 8."],
        "feedback": {"correct": "Right — 834.", "incorrect": "358+476=834."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 504 − 268.",
        "choices": ["A. 236", "B. 246", "C. 336", "D. 346"],
        "answer": "A",
        "explanation": "504−268: 4−8 borrow → 14−8=6; tens 9−6=3 (after lending across zero); hundreds 4−2=2. Result: 236.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "504−268=236."],
        "feedback": {"correct": "Right — 236.", "incorrect": "504−268=236."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 619 books. They donated 247, then bought 158 more. How many books now?",
        "choices": ["A. 372", "B. 458", "C. 530", "D. 760"],
        "answer": "C",
        "explanation": "Step 1: 619−247=372. Step 2: 372+158=530.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add bought.", "619−247=372, 372+158=530."],
        "feedback": {"correct": "Right — 530 books.", "incorrect": "619−247=372, then +158=530."},
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
        "prerequisite": "G3 U7 L8 — 8 나눗셈: 절반 세 번/×8 역연산 (3.OA.C.7)",
        "current":      "G3 — 9 나눗셈 사실: 자릿수 합 9 트릭/×9 역연산 (3.OA.C.7)",
        "successor":    "G3 U7 L10 — 두 단계 문제 해결 (3.OA.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l9.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
