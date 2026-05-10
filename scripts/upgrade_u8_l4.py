"""
G3 U8 L4 — Fractions of a Whole 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.1 (분수 a/b — 단위분수 1/b의 a개 모음)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L4_fractions_of_a_whole.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.1.M02"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.NF.A.1.M02"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.1.M02"] for i in range(1,11)},
    "R2_01": ["3.NF.A.1.M02"],
    "R2_02": ["3.NF.A.1.M04"],
    "R2_03": ["3.NF.A.1.M03"],
    "R2_04": ["3.NF.A.1.M02"],
    "R2_05": ["3.NF.A.1.M04"],
    "R2_06": ["3.NF.A.1.M02"],
    "R2_07": ["3.NF.A.1.M03"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.1.M04"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "fraction_a_over_b" for i in range(1,6)},
    "LEARN_01": "name_fractions",
    "LEARN_02": "fraction_more_than_unit",
    "LEARN_03": "whole_as_fraction",
    "LEARN_04": "numerator_meaning",
    "LEARN_05": "fraction_routine",
    "LEARN_06": "fraction_complement",
    "LEARN_07": "fraction_count_units",
    "LEARN_08": "fraction_estimate_check",
    **{f"TRY_0{i}": "fraction_a_over_b" for i in range(1,6)},
    **{f"R1_{i:02d}": "fraction_a_over_b" for i in range(1,11)},
    **{f"R2_0{i}": "fraction_a_over_b" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "fraction_a_over_b" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "pictorial", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,6)},
    **{f"R1_{i:02d}": "pictorial" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.4 'Fractions of a Whole' pp.325-328",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic B — Fractions a/b as a Iterations of 1/b",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "fraction_a_over_b")
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
        "id": "LEARN_04",
        "type": "concept_card",
        "title": "분자의 의미 — '몇 조각 가졌나'",
        "content": (
            "분수 a/b에서 분자 a는 '단위분수 1/b를 몇 개 모았는지'를 알려줌. "
            "분모 b: 전체를 몇 등분 / 분자 a: 그 중 몇 조각. "
            "예: 3/4 → 4등분 중 3조각 (1/4 + 1/4 + 1/4). "
            "예: 5/8 → 8등분 중 5조각. "
            "🔍 빠른 확인: 분자=색칠한 조각 수, 분모=전체 조각 수."
        ),
        "cpa_stage": "abstract",
        "visual_type": "numerator_meaning",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "분수 a/b 만들기 4단계 루틴",
        "content": (
            "단계 1) 전체(whole) 정하기. "
            "단계 2) b개의 같은 부분으로 나누기. "
            "단계 3) a개를 색칠하기. "
            "단계 4) a/b로 적기. "
            "예: 8조각 피자에서 5조각 먹음 → 5/8 먹음, 3/8 남음. "
            "흔한 실수 (M02): 같은 크기 조건 무시 — 항상 균등 분할 검증."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fraction_routine",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "먹은 + 남은 = 1 (전체)",
        "content": (
            "분수에서 색칠한 부분과 남은 부분을 합하면 항상 전체(b/b = 1). "
            "예: 3/4 색칠 → 1/4 남음 (3/4 + 1/4 = 4/4 = 1). "
            "예: 5/8 색칠 → 3/8 남음 (5/8 + 3/8 = 8/8 = 1). "
            "🔍 검산: 색칠 분자 + 남은 분자 = 분모. 맞으면 OK. "
            "흔한 실수 (M04): 전체를 잊고 분자끼리만 비교 — 분모(전체)를 항상 확인."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fraction_complement",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "단위분수의 반복 — a/b = a × (1/b)",
        "content": (
            "분수 a/b는 단위분수 1/b를 a번 모은 것. "
            "  2/3 = 1/3 + 1/3 (1/3을 2번) "
            "  4/5 = 1/5 + 1/5 + 1/5 + 1/5 (1/5을 4번) "
            "수직선/막대모델에서 1/b 단위로 a칸 이동 → a/b 위치. "
            "🔍 활용: 분자가 분모와 같으면 a/b = b/b = 1 (전체)."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "fraction_count_units",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "어림 검산 — 1/2와 비교",
        "content": (
            "분수가 합리적인지 1/2 기준으로 어림: "
            "  분자 < 분모/2 → 1/2보다 작음 (예: 3/8, 분모/2=4) "
            "  분자 = 분모/2 → 정확히 1/2 (예: 4/8) "
            "  분자 > 분모/2 → 1/2보다 큼 (예: 5/8) "
            "예: 5/6은 분모/2=3보다 큰 5 → 1/2보다 큼 ✓. "
            "흔한 실수 (M03): '6분의 5'를 '5분의 6'으로 거꾸로 읽음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fraction_estimate_check",
    },
]


# 신규 보충 문항
NEW_TRY = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "A rectangle is divided into 6 equal parts. 4 parts are shaded. What fraction is shaded?",
        "choices": ["A. 4/4", "B. 4/6", "C. 6/4", "D. 2/6"],
        "answer": "B",
        "explanation": "Numerator = shaded parts (4); denominator = total equal parts (6) → 4/6.",
        "difficulty": 1,
        "hints": ["Top number = shaded.", "Bottom number = total parts."],
        "feedback": {"correct": "Right — 4/6.", "incorrect": "4 shaded out of 6 total = 4/6."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Which fraction equals 1 whole?",
        "choices": ["A. 3/8", "B. 5/6", "C. 7/7", "D. 1/4"],
        "answer": "C",
        "explanation": "When numerator = denominator, the fraction equals 1 whole. 7/7 = 1.",
        "difficulty": 1,
        "hints": ["a/a = 1.", "All parts shaded means whole."],
        "feedback": {"correct": "Right — 7/7 = 1.", "incorrect": "When top = bottom, fraction = 1. So 7/7=1."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "A pizza is cut into 8 equal slices. Lily ate 3 slices. What fraction did she eat, and what fraction is left?",
        "choices": ["A. 3/8 ate, 5/8 left", "B. 3/8 ate, 8/3 left", "C. 5/8 ate, 3/8 left", "D. 8/3 ate, 5/8 left"],
        "answer": "A",
        "explanation": "Ate 3/8. Left = 8/8 − 3/8 = 5/8. Sum: 3/8 + 5/8 = 8/8 = 1.",
        "difficulty": 2,
        "hints": ["Eaten = 3/8.", "Left = 8 − 3 = 5 parts → 5/8."],
        "feedback": {"correct": "Right — 3/8 ate, 5/8 left.", "incorrect": "3 of 8 = 3/8 eaten; 5 of 8 = 5/8 left."},
    },
]

NEW_R1 = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "A rectangle is divided into 5 equal parts. 2 parts are shaded. What fraction is shaded?",
        "choices": ["A. 2/3", "B. 2/5", "C. 3/5", "D. 5/2"],
        "answer": "B",
        "explanation": "2 shaded out of 5 equal parts = 2/5.",
        "difficulty": 1,
        "hints": ["Top: shaded count.", "Bottom: total parts."],
        "feedback": {"correct": "Right — 2/5.", "incorrect": "2 shaded / 5 total = 2/5."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "Which fraction means '3 copies of 1/4'?",
        "choices": ["A. 1/3", "B. 3/4", "C. 4/3", "D. 1/12"],
        "answer": "B",
        "explanation": "1/4 + 1/4 + 1/4 = 3/4. Three copies of 1/4 equal 3/4.",
        "difficulty": 2,
        "hints": ["a copies of 1/b = a/b.", "1/4 added 3 times."],
        "feedback": {"correct": "Right — 3/4.", "incorrect": "3 × 1/4 = 3/4."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "A circle is divided into 6 equal parts. All 6 parts are shaded. What fraction is shaded?",
        "choices": ["A. 0/6", "B. 1/6", "C. 6/6", "D. 6/0"],
        "answer": "C",
        "explanation": "All 6 of 6 parts shaded = 6/6 = 1 whole.",
        "difficulty": 1,
        "hints": ["a/a = 1.", "Shaded = all."],
        "feedback": {"correct": "Right — 6/6.", "incorrect": "All shaded means a/a = 6/6 = 1."},
    },
]

NEW_R2 = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Sam shaded 5 parts of a rectangle divided into 8 equal parts. What fraction is NOT shaded?",
        "choices": ["A. 5/8", "B. 3/8", "C. 8/3", "D. 8/5"],
        "answer": "B",
        "explanation": "Shaded 5/8, so unshaded = 8/8 − 5/8 = 3/8.",
        "difficulty": 2,
        "hints": ["Unshaded = total − shaded.", "8 − 5 = 3 unshaded parts."],
        "feedback": {"correct": "Right — 3/8.", "incorrect": "8 − 5 = 3 parts unshaded → 3/8."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Which fraction is equal to 4/4?",
        "choices": ["A. 0", "B. 1/2", "C. 1", "D. 4"],
        "answer": "C",
        "explanation": "When numerator = denominator, the fraction = 1 whole. 4/4 = 1.",
        "difficulty": 1,
        "hints": ["a/a = 1.", "All parts shaded means whole = 1."],
        "feedback": {"correct": "Right — 1.", "incorrect": "4/4 means all 4 of 4 parts → 1 whole."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Which is read as 'three-fifths'?",
        "choices": ["A. 5/3", "B. 3/5", "C. 1/3", "D. 1/5"],
        "answer": "B",
        "explanation": "Korean reads denominator first ('5분의'), numerator second ('3'). English: 3/5 = three-fifths (numerator first).",
        "difficulty": 2,
        "hints": ["Numerator on top.", "3 over 5 = three-fifths."],
        "feedback": {"correct": "Right — 3/5.", "incorrect": "Three-fifths = 3 on top, 5 on bottom = 3/5."},
    },
]

NEW_R3 = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Mark cut a pizza into 8 equal slices. He ate 3 slices and gave 2 slices to his friend. What fraction of the pizza is left?",
        "choices": ["A. 5/8", "B. 3/8", "C. 2/8", "D. 1/8"],
        "answer": "B",
        "explanation": "Eaten + given = 3 + 2 = 5 slices used. Left = 8 − 5 = 3 → 3/8.",
        "difficulty": 3,
        "hints": ["Add eaten and given first.", "Left = 8 − (3+2) = 3 parts → 3/8."],
        "feedback": {"correct": "Right — 3/8.", "incorrect": "5 slices used, 3 slices left → 3/8."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Two shapes are each divided into 6 equal parts. Shape A has 2 parts shaded; Shape B has 4 parts shaded. Which statement is true?",
        "choices": [
            "A. Shape A shows 2/6, Shape B shows 4/6 — both have the same denominator.",
            "B. Shape A shows 6/2 and Shape B shows 6/4.",
            "C. Both shapes show the same fraction.",
            "D. Shape B shows 4/2."
        ],
        "answer": "A",
        "explanation": "Both shapes are divided into 6 parts (same denominator). A: 2 shaded → 2/6. B: 4 shaded → 4/6.",
        "difficulty": 3,
        "hints": ["Same total parts → same denominator.", "Numerator changes with shaded count."],
        "feedback": {"correct": "Right — A: 2/6, B: 4/6.", "incorrect": "Same denominator (6); numerators differ (2 vs 4)."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 419 + 285.",
        "choices": ["A. 594", "B. 604", "C. 694", "D. 704"],
        "answer": "D",
        "explanation": "419+285: 9+5=14 (carry 1), 1+8+1=10 (carry 1), 4+2+1=7. Result: 704.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 14. Tens: 10. Hundreds: 7."],
        "feedback": {"correct": "Right — 704.", "incorrect": "419+285=704."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 600 − 247.",
        "choices": ["A. 343", "B. 353", "C. 363", "D. 453"],
        "answer": "B",
        "explanation": "600−247: 0−7 borrow → 10−7=3; tens 9−4=5 (after lending across zero); hundreds 5−2=3. Result: 353.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "600−247=353."],
        "feedback": {"correct": "Right — 353.", "incorrect": "600−247=353."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bakery had 438 muffins. They baked 175 more, then sold 296. How many muffins are left?",
        "choices": ["A. 297", "B. 317", "C. 327", "D. 613"],
        "answer": "B",
        "explanation": "Step 1: 438+175=613. Step 2: 613−296=317.",
        "difficulty": 3,
        "hints": ["Add baked, then subtract sold.", "438+175=613, 613−296=317."],
        "feedback": {"correct": "Right — 317 muffins.", "incorrect": "438+175=613, then −296=317."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 새 7단계 표준으로 업그레이드됨.")
        return

    nested = d.get("sections", {})
    sections_map = {
        "pretest": nested.get("pretest", d.get("pretest", [])),
        "learn": nested.get("learn", d.get("learn", [])),
        "try": nested.get("try", d.get("try", [])),
        "practice_r1": nested.get("practice_r1", d.get("practice_r1", [])),
        "practice_r2": nested.get("practice_r2", d.get("practice_r2", [])),
        "practice_r3": nested.get("practice_r3", d.get("practice_r3", [])),
    }

    # LEARN: 3 → 8 (add LEARN_04..08)
    sections_map["learn"].extend(NEW_LEARN_CARDS)
    # TRY: 2 → 5
    sections_map["try"].extend(NEW_TRY)
    # R1: 7 → 10
    sections_map["practice_r1"].extend(NEW_R1)
    # R2: 4 → 10 (4 keep + 3 fraction + 3 U1 review)
    sections_map["practice_r2"] = sections_map["practice_r2"][:4]
    sections_map["practice_r2"].extend(NEW_R2)
    sections_map["practice_r2"].extend(U1_REVIEW_R2)
    # R3: 3 → 5
    sections_map["practice_r3"].extend(NEW_R3)

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
    if "sections" in d:
        del d["sections"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U8 L3 — 단위분수 1/b: 전체를 b등분한 것 중 한 부분 (3.NF.A.1)",
        "current":      "G3 — 분수 a/b: 단위분수 1/b의 a개 모음 (3.NF.A.1)",
        "successor":    "G3 U8 L5 — 수직선 위의 분수 (3.NF.A.2)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
