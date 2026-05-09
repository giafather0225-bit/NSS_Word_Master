"""
G3 U3 L7 — Multiply with 1 and 0 7단계 업그레이드 스크립트
==========================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.B.5 (항등원·영원 곱셈 적용)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U3_understand_multiplication/L7_multiply_with_1_and_0.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.B.5.M05"],
    "PT_02": ["3.OA.B.5.M06"],
    "PT_03": ["3.OA.B.5.M05"],
    "PT_04": ["3.OA.B.5.M06"],
    "PT_05": ["3.OA.B.5.M05"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.B.5.M06"],
    "TRY_02": ["3.OA.B.5.M05"],
    "TRY_03": ["3.OA.B.5.M06"],
    "TRY_04": ["3.OA.B.5.M05"],
    "TRY_05": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R1_01": ["3.OA.B.5.M05"],
    "R1_02": ["3.OA.B.5.M06"],
    "R1_03": ["3.OA.B.5.M05"],
    "R1_04": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R1_05": ["3.OA.B.5.M05"],
    "R1_06": ["3.OA.B.5.M06"],
    "R1_07": ["3.OA.B.5.M06"],
    "R1_08": ["3.OA.B.5.M05"],
    "R1_09": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R1_10": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R2_01": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R2_02": ["3.OA.B.5.M05"],
    "R2_03": ["3.OA.B.5.M06"],
    "R2_04": ["3.OA.B.5.M05"],
    "R2_05": ["3.OA.B.5.M06"],
    "R2_06": ["3.OA.B.5.M06"],
    "R2_07": ["3.OA.B.5.M05"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R3_02": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R3_03": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R3_04": ["3.OA.B.5.M05", "3.OA.B.5.M06"],
    "R3_05": ["3.OA.B.5.M06"],
}

SKILL_TAGS = {
    "PT_01": "apply_identity",
    "PT_02": "apply_zero",
    "PT_03": "identify_property",
    "PT_04": "apply_zero",
    "PT_05": "apply_identity",
    "LEARN_01": "identity_definition",
    "LEARN_02": "zero_definition",
    "LEARN_03": "fast_facts_with_0_and_1",
    "LEARN_04": "scan_for_0_and_1",
    "LEARN_05": "zero_in_chain",
    "LEARN_06": "compare_identity_zero",
    "LEARN_07": "missing_factor_with_1",
    "LEARN_08": "properties_summary",
    "TRY_01": "apply_zero",
    "TRY_02": "apply_identity",
    "TRY_03": "apply_zero_word_problem",
    "TRY_04": "apply_identity",
    "TRY_05": "compare_identity_zero",
    "R1_01": "apply_identity",
    "R1_02": "apply_zero",
    "R1_03": "apply_identity",
    "R1_04": "compare_identity_zero",
    "R1_05": "missing_factor_with_1",
    "R1_06": "apply_zero",
    "R1_07": "apply_zero",
    "R1_08": "missing_factor_with_1",
    "R1_09": "apply_zero",
    "R1_10": "compare_identity_zero",
    "R2_01": "compare_identity_zero",
    "R2_02": "identity_chain",
    "R2_03": "apply_zero",
    "R2_04": "apply_identity",
    "R2_05": "identify_property",
    "R2_06": "apply_zero",
    "R2_07": "identify_property",
    "R2_08": "addition_3digit",      # U1
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "chain_with_zero",
    "R3_02": "boundary_reasoning",
    "R3_03": "compare_identity_zero",
    "R3_04": "compare_identity_zero",
    "R3_05": "zero_in_chain",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "concrete", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,3)},
    "TRY_03": "pictorial", "TRY_04": "abstract", "TRY_05": "abstract",
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.3 Lesson 3.7 'Multiply with 1 and 0' pp.127-130",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "apply_identity")
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
        "title": "1과 0 — 헷갈리지 않는 비교",
        "content": (
            "이 두 규칙은 비슷해 보여서 자주 헷갈립니다. 명확히 구분: "
            "n × 1 = n (Identity, 항등원) — 1을 곱하면 그대로. "
            "n × 0 = 0 (Zero, 영원) — 0을 곱하면 0. "
            "흔한 실수 1: 5 × 1 = 1로 답함 (1이 다른 수를 '먹어버린다'고 오해). "
            "흔한 실수 2: 5 × 0 = 5로 답함 (덧셈 규칙 '5+0=5'을 곱셈에 잘못 적용). "
            "기억법: '1배 = 그대로, 0배 = 아예 없음'."
        ),
        "cpa_stage": "concrete",
        "visual_type": "comparison_chart",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "미지수 풀기 — ?×1 = N 패턴",
        "content": (
            "Identity Property를 거꾸로 활용하면 미지수를 즉시 찾을 수 있습니다. "
            "? × 1 = 99 → ? = 99 (계산 없이 곱과 같음). "
            "? × 1 = 8 → ? = 8. "
            "유사 패턴: 0 × ? = 0 → ?에는 어떤 수든 가능 (모든 수 정답). "
            "주의: ? × 0 = 5 같은 식은 풀 수 없음 — 0을 곱한 결과는 항상 0이므로 5가 될 수 없음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "none",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "1·0 곱셈 — 즉답 전략 요약",
        "content": (
            "곱셈식을 보고 계산하기 전에 스캔! "
            "1) 0이 하나라도 있으면 → 답 = 0 (다른 인자는 무시). "
            "2) 1이 인자면 → 답 = 다른 인자 (0이 없는 경우). "
            "3) 둘 다 없으면 → 일반 곱셈 진행. "
            "이 전략으로 곱셈표 100개 사실 중 19개(0×n=0의 11개 + 1×n=n의 9개 중복 제외)를 즉답!"
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
        "question": "Find the sum: 348 + 276.",
        "choices": ["A. 524", "B. 614", "C. 624", "D. 724"],
        "answer": "C",
        "explanation": "348+276: 8+6=14 (carry 1), 4+7+1=12 (carry 1), 3+2+1=6. Result: 624.",
        "hints": [
            "Two carries.",
            "Ones: 14. Tens: 12. Hundreds: 6.",
        ],
        "feedback": {
            "correct": "Right — 624.",
            "incorrect": "348+276=624.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 706 − 289.",
        "choices": ["A. 417", "B. 423", "C. 467", "D. 517"],
        "answer": "A",
        "explanation": "706−289: 6−9 borrow → 16−9=7; tens 0−8 borrow → 10−9=1 (after lending); hundreds 6−2=4. Result: 417.",
        "hints": [
            "Borrow across the zero in tens.",
            "706−289=417.",
        ],
        "feedback": {
            "correct": "Right — 417.",
            "incorrect": "706−289=417.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A factory produced 645 toys on Monday. They shipped 287, then produced 174 more. How many toys are at the factory now?",
        "choices": ["A. 358", "B. 532", "C. 558", "D. 1106"],
        "answer": "B",
        "explanation": "Step 1: 645−287=358. Step 2: 358+174=532.",
        "hints": [
            "Two steps: subtract shipped, then add produced.",
            "645−287=358, 358+174=532.",
        ],
        "feedback": {
            "correct": "Right — 532 toys.",
            "incorrect": "645−287=358, then +174=532.",
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
        "prerequisite": "G3 U3 L1-L6 — 등량 그룹·반복 덧셈·배열·교환법칙 (3.OA.A.1, 3.OA.A.3, 3.OA.B.5)",
        "current":      "G3 — 항등원(×1)과 영원(×0) 곱셈; 즉답 전략 (3.OA.B.5)",
        "successor":    "G3 U4 — 곱셈 사실 전략 (2/4/8, 5/10, 3/6/9 묶음 — 3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u3_l7.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
