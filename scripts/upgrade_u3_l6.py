"""
G3 U3 L6 — Commutative Property of Multiplication 7단계 업그레이드 스크립트
=========================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.5 (곱셈 교환법칙 적용)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U3_understand_multiplication/L6_commutative_property.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.B.5.M01"],
    "PT_02": ["3.OA.B.5.M01"],
    "PT_03": ["3.OA.B.5.M01"],
    "PT_04": ["3.OA.B.5.M01"],
    "PT_05": ["3.OA.B.5.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.B.5.M01"],
    "TRY_02": ["3.OA.B.5.M01"],
    "TRY_03": ["3.OA.B.5.M01"],
    "TRY_04": ["3.OA.B.5.M01"],
    "TRY_05": ["3.OA.B.5.M01"],
    "R1_01": ["3.OA.B.5.M01"],
    "R1_02": ["3.OA.B.5.M01"],
    "R1_03": ["3.OA.B.5.M01"],
    "R1_04": ["3.OA.B.5.M01"],
    "R1_05": ["3.OA.B.5.M01"],
    "R1_06": ["3.OA.B.5.M01"],
    "R1_07": ["3.OA.B.5.M01"],
    "R1_08": ["3.OA.B.5.M01"],
    "R1_09": ["3.OA.B.5.M01"],
    "R1_10": ["3.OA.B.5.M01"],
    "R2_01": ["3.OA.B.5.M01"],
    "R2_02": ["3.OA.B.5.M01", "3.OA.B.5.M07"],
    "R2_03": ["3.OA.B.5.M02"],
    "R2_04": ["3.OA.B.5.M01"],
    "R2_05": ["3.OA.B.5.M01"],
    "R2_06": ["3.OA.B.5.M01"],
    "R2_07": ["3.OA.B.5.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.B.5.M01"],
    "R3_02": ["3.OA.B.5.M01"],
    "R3_03": ["3.OA.B.5.M01"],
    "R3_04": ["3.OA.B.5.M07"],
    "R3_05": ["3.OA.B.5.M01"],
}

SKILL_TAGS = {
    "PT_01": "apply_commutative",
    "PT_02": "identify_property",
    "PT_03": "apply_commutative",
    "PT_04": "rotate_array_commutative",
    "PT_05": "missing_factor_commutative",
    "LEARN_01": "commutative_definition",
    "LEARN_02": "rotate_array_commutative",
    "LEARN_03": "turn_around_facts",
    "LEARN_04": "missing_factor_commutative",
    "LEARN_05": "commutative_scope",
    "LEARN_06": "turn_around_facts",
    "LEARN_07": "commutative_scope",
    "LEARN_08": "commutative_strategies",
    "TRY_01": "apply_commutative",
    "TRY_02": "missing_factor_commutative",
    "TRY_03": "verify_commutative",
    "TRY_04": "apply_commutative",
    "TRY_05": "missing_factor_commutative",
    "R1_01": "apply_commutative",
    "R1_02": "identify_turn_around_pair",
    "R1_03": "apply_commutative",
    "R1_04": "missing_factor_commutative",
    "R1_05": "verify_commutative",
    "R1_06": "apply_commutative",
    "R1_07": "missing_factor_commutative",
    "R1_08": "apply_commutative",
    "R1_09": "identify_turn_around_pair",
    "R1_10": "apply_commutative",
    "R2_01": "rotate_array_commutative",
    "R2_02": "fact_inventory_commutative",
    "R2_03": "commutative_scope",
    "R2_04": "apply_commutative",
    "R2_05": "rotate_array_commutative",
    "R2_06": "apply_commutative",
    "R2_07": "commutative_scope",
    "R2_08": "addition_3digit",        # U1
    "R2_09": "subtraction_3digit",     # U1
    "R2_10": "two_step_add_sub",       # U1
    "R3_01": "fact_inventory_commutative",
    "R3_02": "missing_factor_commutative",
    "R3_03": "missing_factor_commutative",
    "R3_04": "apply_commutative_context",
    "R3_05": "identify_property",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,4)},
    "PT_04": "pictorial", "PT_05": "abstract",
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "pictorial", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,10)},
    "R1_10": "abstract",
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.3 Lesson 3.6 'Commutative Property of Multiplication' pp.123-126",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic F — Distributive Property and Properties of Multiplication",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "apply_commutative")
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
        "title": "턴어라운드 짝(Turn-Around Pair) 만들기",
        "content": (
            "곱셈 한 사실을 알면, 짝이 되는 사실 하나를 공짜로 얻습니다. "
            "예: 6 × 7 = 42 알면 → 7 × 6 = 42도 자동으로 앎. "
            "100개 곱셈표(1×1~10×10)에서 — 같은 수끼리 곱한 'square' 사실(예: 5×5) 10개와, "
            "나머지 90개가 45쌍의 턴어라운드를 만들어 — 외워야 할 고유 사실은 단 55개."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "turn_around_pair_chart",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "교환법칙은 어디까지 적용되는가?",
        "content": (
            "교환법칙(Commutative Property)이 작동하는 연산: 덧셈(+), 곱셈(×). "
            "작동하지 않는 연산: 뺄셈(−), 나눗셈(÷). "
            "예 — 8 − 3 = 5이지만 3 − 8 ≠ 5. "
            "예 — 12 ÷ 3 = 4이지만 3 ÷ 12 ≠ 4. "
            "흔한 실수: 곱셈에서 배운 교환법칙을 뺄셈/나눗셈에도 그대로 쓰는 일반화 오류."
        ),
        "cpa_stage": "abstract",
        "visual_type": "comparison_table",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "교환법칙 활용 — 모르는 사실 풀기",
        "content": (
            "전략 1: 알고 있는 친한 인자가 앞에 오도록 swap. "
            "  예: 8 × 3을 모르면, 3 × 8 = 24를 떠올려 → 8 × 3 = 24. "
            "전략 2: 미지수 문제에서 양변 매칭. "
            "  예: 7 × ? = ? × 7 = 56 → 7 × 8 = 56이므로 ? = 8. "
            "전략 3: 워드 프로블럼에서도 swap 가능 — 답은 동일. "
            "  예: '8 vans × 7 students each' = '7 × 8' = 56."
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
        "question": "Find the sum: 467 + 285.",
        "choices": ["A. 642", "B. 652", "C. 742", "D. 752"],
        "answer": "D",
        "explanation": "467+285: 7+5=12 (carry 1), 6+8+1=15 (carry 1), 4+2+1=7. Result: 752.",
        "hints": [
            "Carry twice.",
            "Ones: 12. Tens: 15. Hundreds: 7.",
        ],
        "feedback": {
            "correct": "Right — 752.",
            "incorrect": "467+285=752.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 614 − 358.",
        "choices": ["A. 244", "B. 256", "C. 266", "D. 356"],
        "answer": "B",
        "explanation": "614−358: 4−8 borrow → 14−8=6; tens 0−5 borrow → 10−5=5 (after lending); hundreds 5−3=2. Result: 256.",
        "hints": [
            "Two borrows.",
            "614−358=256.",
        ],
        "feedback": {
            "correct": "Right — 256.",
            "incorrect": "614−358=256.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A school had 528 markers. They donated 137 to another school, then ordered 245 more. How many markers now?",
        "choices": ["A. 391", "B. 482", "C. 636", "D. 910"],
        "answer": "C",
        "explanation": "Step 1: 528−137=391. Step 2: 391+245=636.",
        "hints": [
            "Two steps: subtract donated, then add ordered.",
            "528−137=391, 391+245=636.",
        ],
        "feedback": {
            "correct": "Right — 636.",
            "incorrect": "528−137=391, then +245=636.",
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
        "prerequisite": "G3 U3 L1-L5 — 등량 그룹·반복 덧셈·배열 (3.OA.A.1, 3.OA.A.3)",
        "current":      "G3 — 곱셈 교환법칙 형식화; 턴어라운드 사실 활용 (3.OA.B.5)",
        "successor":    "G3 U3 L7 — 1과 0 곱셈; 항등원·영원 (3.OA.B.5)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u3_l6.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
