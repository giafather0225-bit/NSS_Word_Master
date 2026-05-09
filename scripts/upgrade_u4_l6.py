"""
G3 U4 L6 — Associative Property 7단계 업그레이드 스크립트
==========================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.5 (결합법칙: 그루핑 변경 가능; 친한 짝부터 곱하기)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L6_associative_property.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.B.5.M04"],
    "PT_02": ["3.OA.B.5.M04"],
    "PT_03": ["3.OA.B.5.M04"],
    "PT_04": ["3.OA.B.5.M04"],
    "PT_05": ["3.OA.B.5.M04"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.B.5.M04"],
    "TRY_02": ["3.OA.B.5.M04"],
    "TRY_03": ["3.OA.B.5.M04"],
    "TRY_04": ["3.OA.B.5.M04"],
    "TRY_05": ["3.OA.B.5.M04"],
    "R1_01": ["3.OA.B.5.M04"],
    "R1_02": ["3.OA.B.5.M05"],
    "R1_03": ["3.OA.B.5.M04"],
    "R1_04": ["3.OA.B.5.M04"],
    "R1_05": ["3.OA.B.5.M04"],
    "R1_06": ["3.OA.B.5.M04"],
    "R1_07": ["3.OA.B.5.M04"],
    "R1_08": ["3.OA.B.5.M04"],
    "R1_09": ["3.OA.B.5.M04"],
    "R1_10": ["3.OA.B.5.M04"],
    "R2_01": ["3.OA.B.5.M04"],
    "R2_02": ["3.OA.B.5.M04"],
    "R2_03": ["3.OA.B.5.M04"],
    "R2_04": ["3.OA.B.5.M04"],
    "R2_05": ["3.OA.B.5.M04"],
    "R2_06": ["3.OA.B.5.M04"],
    "R2_07": ["3.OA.B.5.M04"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.B.5.M04"],
    "R3_02": ["3.OA.B.5.M04"],
    "R3_03": ["3.OA.B.5.M04"],
    "R3_04": ["3.OA.B.5.M04"],
    "R3_05": ["3.OA.B.5.M04"],
}

SKILL_TAGS = {
    "PT_01": "associative_compute",
    "PT_02": "associative_compute",
    "PT_03": "verify_associative",
    "PT_04": "associative_compute",
    "PT_05": "identify_property",
    "LEARN_01": "associative_definition",
    "LEARN_02": "regrouping_three_factors",
    "LEARN_03": "friendly_pair_first",
    "LEARN_04": "associative_proof_arrays",
    "LEARN_05": "associative_word_problem",
    "LEARN_06": "regrouping_three_factors",
    "LEARN_07": "friendly_pair_first",
    "LEARN_08": "associative_strategies",
    "TRY_01": "associative_compute",
    "TRY_02": "best_grouping",
    "TRY_03": "make_10_pair",
    "TRY_04": "associative_compute",
    "TRY_05": "missing_grouping_factor",
    "R1_01": "associative_compute",
    "R1_02": "associative_with_identity",
    "R1_03": "associative_compute",
    "R1_04": "associative_compute",
    "R1_05": "associative_compute",
    "R1_06": "verify_associative",
    "R1_07": "associative_compute",
    "R1_08": "associative_compute",
    "R1_09": "associative_compute",
    "R1_10": "identify_property",
    "R2_01": "make_10_pair",
    "R2_02": "best_grouping",
    "R2_03": "associative_compute",
    "R2_04": "missing_grouping_factor",
    "R2_05": "verify_associative",
    "R2_06": "associative_compute",
    "R2_07": "best_grouping",
    "R2_08": "addition_3digit",       # U1
    "R2_09": "subtraction_3digit",    # U1
    "R2_10": "two_step_add_sub",      # U1
    "R3_01": "make_10_pair",
    "R3_02": "associative_word_problem",
    "R3_03": "make_10_pair",
    "R3_04": "associative_word_problem",
    "R3_05": "missing_grouping_factor",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "concrete", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.6 'Associative Property of Multiplication' pp.159-162",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Distributive and Associative Properties",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "associative_compute")
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
        "title": "결합법칙 — 괄호 위치를 바꿔도 곱은 같다",
        "content": (
            "세 수를 곱할 때, 어디부터 곱해도 결과는 같음 — 결합법칙. "
            "예: (2 × 3) × 5 = 6 × 5 = 30. "
            "예: 2 × (3 × 5) = 2 × 15 = 30. "
            "두 가지 모두 같은 답 30. 괄호의 위치는 결과를 바꾸지 않음. "
            "주의: 결합법칙은 인자의 '순서'가 아니라 '그루핑(괄호)'을 바꾸는 것 (순서 변경은 교환법칙)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "regrouping_diagram",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "친한 짝(Friendly Pair) 먼저 곱하기 — 빠른 풀이",
        "content": (
            "결합법칙의 진짜 힘: 쉬운 짝부터 골라 먼저 곱하기. "
            "친한 짝: ×2, ×5, ×10 (덧셈에서 '10 만들기'와 같은 원리). "
            "예: 7 × 2 × 5. 어렵게: (7 × 2) × 5 = 14 × 5 = 70. "
            "쉽게: 7 × (2 × 5) = 7 × 10 = 70 ⭐. "
            "팁: '×2와 ×5가 만나면 묶어라!' (= ×10이 되어 즉답)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "friendly_pair_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "결합법칙 활용 전략 요약",
        "content": (
            "전략 1 ×2와 ×5를 보면 묶어 ×10 만들기. "
            "  예: 6 × 5 × 2 → 6 × (5 × 2) = 6 × 10 = 60. "
            "전략 2 같은 수가 두 번 있으면 묶기 (제곱). "
            "  예: 3 × 3 × 4 → (3 × 3) × 4 = 9 × 4 = 36. "
            "전략 3 ×1이 있으면 무시 (곱셈 항등원). "
            "  예: 5 × 1 × 7 = 5 × 7 = 35. "
            "전략 4 작은 수끼리 먼저 (큰 곱은 마지막). "
            "검증: 어떻게 묶어도 결과는 같음 — 가장 쉬운 길 선택!"
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
        "question": "Find the sum: 487 + 296.",
        "choices": ["A. 673", "B. 683", "C. 773", "D. 783"],
        "answer": "D",
        "explanation": "487+296: 7+6=13 (carry 1), 8+9+1=18 (carry 1), 4+2+1=7. Result: 783.",
        "hints": [
            "Two carries.",
            "Ones: 13. Tens: 18. Hundreds: 7.",
        ],
        "feedback": {
            "correct": "Right — 783.",
            "incorrect": "487+296=783.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 605 − 248.",
        "choices": ["A. 347", "B. 357", "C. 447", "D. 457"],
        "answer": "B",
        "explanation": "605−248: 5−8 borrow → 15−8=7; tens 9−4=5 (after lending); hundreds 5−2=3. Result: 357.",
        "hints": [
            "Borrow across the zero in tens.",
            "605−248=357.",
        ],
        "feedback": {
            "correct": "Right — 357.",
            "incorrect": "605−248=357.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A store had 738 toys. They sold 269 toys, then received 145 new ones. How many toys now?",
        "choices": ["A. 324", "B. 469", "C. 614", "D. 883"],
        "answer": "C",
        "explanation": "Step 1: 738−269=469. Step 2: 469+145=614.",
        "hints": [
            "Subtract sold, then add received.",
            "738−269=469, 469+145=614.",
        ],
        "feedback": {
            "correct": "Right — 614 toys.",
            "incorrect": "738−269=469, then +145=614.",
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
        "prerequisite": "G3 U3 L6 — 교환법칙; G3 U4 L4 — 분배법칙 (3.OA.B.5)",
        "current":      "G3 — 결합법칙: 그루핑 변경; 친한 짝 먼저 곱하기 (3.OA.B.5)",
        "successor":    "G3 U4 L7 — 곱셈표 패턴 분석 (3.OA.D.9)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l6.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
