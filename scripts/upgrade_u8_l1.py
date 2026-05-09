"""
G3 U8 L1 — Equal Parts of a Whole 7단계 마이그레이션
==============================================================================
27개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.1 (전체의 균등 분할 — 분수의 개념)

기존 27개 (PT=5, LEARN=3, TRY=5, R1=7, R2=4, R3=3)에 추가:
+ LEARN_04~LEARN_08 (5개 신규)
+ R1_08~R1_10 (3개 신규)
+ R2_05~R2_07 (3개 분수 추가) + R2_08~R2_10 (3개 U1 복습)
+ R3_04~R3_05 (2개 신규)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L1_equal_parts_of_a_whole.json"

ERRORS_MAP = {
    "PT_01": ["3.NF.A.1.M03"],
    "PT_02": ["3.NF.A.1.M03"],
    "PT_03": ["3.NF.A.1.M03"],
    "PT_04": ["3.NF.A.1.M03"],
    "PT_05": ["3.NF.A.1.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.NF.A.1.M03"],
    "TRY_02": ["3.NF.A.1.M01"],
    "TRY_03": ["3.NF.A.1.M03"],
    "TRY_04": ["3.NF.A.1.M01"],
    "TRY_05": ["3.NF.A.1.M04"],
    "R1_01": ["3.NF.A.1.M03"],
    "R1_02": ["3.NF.A.1.M03"],
    "R1_03": ["3.NF.A.1.M03"],
    "R1_04": ["3.NF.A.1.M02"],
    "R1_05": ["3.NF.A.1.M01"],
    "R1_06": ["3.NF.A.1.M03"],
    "R1_07": ["3.NF.A.1.M01"],
    "R1_08": ["3.NF.A.1.M03"],
    "R1_09": ["3.NF.A.1.M03"],
    "R1_10": ["3.NF.A.1.M01"],
    "R2_01": ["3.NF.A.1.M02"],
    "R2_02": ["3.NF.A.1.M03"],
    "R2_03": ["3.NF.A.1.M04"],
    "R2_04": ["3.NF.A.1.M01"],
    "R2_05": ["3.NF.A.1.M05"],
    "R2_06": ["3.NF.A.1.M03"],
    "R2_07": ["3.NF.A.1.M07"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.NF.A.1.M06"],
    "R3_02": ["3.NF.A.1.M03"],
    "R3_03": ["3.NF.A.1.M04"],
    "R3_04": ["3.NF.A.1.M05"],
    "R3_05": ["3.NF.A.1.M01"],
}

SKILL_TAGS = {
    **{f"PT_0{i}": "name_equal_parts" for i in range(1,6)},
    "LEARN_01": "equal_parts_intro",
    "LEARN_02": "name_equal_parts",
    "LEARN_03": "equal_parts_cover_whole",
    "LEARN_04": "fraction_name_routine",
    "LEARN_05": "equal_area_check",
    "LEARN_06": "different_shapes_same_fraction",
    "LEARN_07": "no_gaps_no_overlap",
    "LEARN_08": "whole_first",
    **{f"TRY_0{i}": "name_equal_parts" for i in range(1,6)},
    **{f"R1_{i:02d}": "name_equal_parts" for i in range(1,11)},
    "R2_01": "name_equal_parts",
    "R2_02": "name_equal_parts",
    "R2_03": "fraction_one_part",
    "R2_04": "identify_halves",
    "R2_05": "different_shapes_same_fraction",
    "R2_06": "name_equal_parts",
    "R2_07": "no_gaps_no_overlap",
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    "R3_01": "equal_area_diagonals",
    "R3_02": "name_equal_parts",
    "R3_03": "compare_shaded_parts",
    "R3_04": "different_shapes_same_fraction",
    "R3_05": "no_gaps_no_overlap",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "abstract", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "pictorial",
    "LEARN_06": "pictorial", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.1 'Equal Parts of a Whole' pp.317-320",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic A — Partitioning a Whole into Equal Parts",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "name_equal_parts")
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
        "title": "분수 이름 짓기 — 갯수와 이름의 짝꿍",
        "content": (
            "분수 이름은 똑같이 나눈 부분의 갯수에 따라 정해짐: "
            "  2조각 = halves (절반/이분의), 3조각 = thirds (삼분의), "
            "  4조각 = fourths (사분의), 5조각 = fifths, "
            "  6조각 = sixths, 8조각 = eighths. "
            "예: 케이크를 6조각으로 똑같이 자르면 한 조각 = 1/6 (one-sixth). "
            "흔한 실수 (M03): 4조각인데 'thirds' (삼분의)라고 부름 — "
            "갯수와 이름을 정확히 매칭하세요."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fraction_naming",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "넓이 검증 — 진짜 똑같은 크기인가?",
        "content": (
            "분수가 되려면 '같은 갯수'만으로는 부족 — '같은 넓이'여야 함. "
            "예: 사각형을 가로 세로로 4조각 만들었는데 한쪽이 더 큰 경우 → 분수 X. "
            "예: 4조각이지만 모든 조각이 정확히 같은 넓이 → 1/4. "
            "검증 방법: "
            "  ① 한 조각을 오려서 다른 조각 위에 겹침 — 똑같이 맞나? "
            "  ② 격자 종이 위에 그려서 사각 칸 수를 셈. "
            "흔한 실수 (M06): 갯수만 보고 분수라 함."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "equal_area_check",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "모양은 달라도 같은 분수 — 1/4의 다양한 형태",
        "content": (
            "같은 분수도 여러 모양으로 표현 가능. 핵심은 '같은 넓이'. "
            "예: 정사각형 1/4 = 작은 사각 한 개 (가로 세로 4분할) "
            "    = 길쭉한 직사각형 (세로 4분할) "
            "    = 삼각형 (대각선으로 4분할) — 모두 1/4. "
            "전체 넓이의 1/4이면 모양이 달라도 같은 분수. "
            "흔한 실수 (M05): 모양이 다르니 다른 분수라 생각."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "different_shape_same_fraction",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "전체 덮기 — 빈 곳도 겹침도 없어야",
        "content": (
            "조각들이 전체를 빈틈 없이, 겹침 없이 정확히 덮어야 분수가 됨. "
            "예: 사각형을 4조각으로 자르되 한 구석에 빈 공간이 남으면 분수 X. "
            "예: 두 조각이 서로 겹치면 (넘치면) 분수 X. "
            "검증 절차: "
            "  ① 모든 조각을 합치면 전체와 정확히 일치? "
            "  ② 빈 부분 없음 + 겹친 부분 없음? "
            "흔한 실수 (M07): 비어있거나 겹친 partition을 분수로 받아들임."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "no_gap_no_overlap",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "전체 먼저 — 분수의 닻",
        "content": (
            "분수를 말하기 전 항상 묻기: '전체(whole)는 무엇인가?' "
            "예: 피자 한 판이 전체 → 한 조각은 1/8. "
            "예: 피자 두 판이 전체 → 한 조각은 1/16. "
            "🔍 검증 절차: "
            "  ① 전체 모양/물체를 동그라미 치기. "
            "  ② 똑같이 나눈 갯수 세기 (= 분모). "
            "  ③ 색칠된 또는 가리킨 갯수 세기 (= 분자). "
            "흔한 실수 (M04): 전체를 잊고 조각만 세서 분수 만들기."
        ),
        "cpa_stage": "abstract",
        "visual_type": "whole_first",
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "A pizza is cut into 5 equal slices. What is each slice called?",
        "choices": ["A. fourths", "B. fifths", "C. sixths", "D. halves"],
        "answer": "B",
        "explanation": "5 equal parts → fifths.",
        "difficulty": 1,
        "hints": ["Count = 5.", "5 = fifths."],
        "feedback": {"correct": "Right — fifths.", "incorrect": "5 equal parts = fifths."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "A rectangle is divided into 7 equal parts. What is each part called?",
        "choices": ["A. sevenths", "B. eighths", "C. fifths", "D. sixths"],
        "answer": "A",
        "explanation": "7 equal parts → sevenths.",
        "difficulty": 1,
        "hints": ["Count = 7.", "7 = sevenths."],
        "feedback": {"correct": "Right — sevenths.", "incorrect": "7 equal parts = sevenths."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "A bar is split into 3 pieces. The pieces are NOT all the same size. Are they thirds?",
        "choices": ["A. Yes, because there are 3 pieces", "B. No, because thirds must be equal", "C. Yes, halves", "D. Yes, but only one is a third"],
        "answer": "B",
        "explanation": "Thirds means 3 EQUAL parts. Unequal pieces are not thirds.",
        "difficulty": 2,
        "hints": ["Count = 3 but unequal.", "Fraction names need EQUAL parts."],
        "feedback": {"correct": "Right — not thirds (unequal).", "incorrect": "Equal parts only — these unequal pieces are not thirds."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Two squares are each shaded 1/4. Square A has 4 small squares (1 shaded). Square B is split by diagonals into 4 triangles (1 shaded). Are both 1/4?",
        "choices": ["A. Yes — same fraction, different shapes", "B. No — different shapes mean different fractions", "C. Only A is 1/4", "D. Only B is 1/4"],
        "answer": "A",
        "explanation": "Both have 4 equal-area parts with 1 shaded. Same fraction = 1/4. Shape of part doesn't change fraction.",
        "difficulty": 2,
        "hints": ["Both have 4 equal parts.", "Same fraction means same area share."],
        "feedback": {"correct": "Right — both 1/4.", "incorrect": "Same equal-area share = same fraction. Both are 1/4."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "A circle is cut into 9 equal slices. What is each slice called?",
        "choices": ["A. eighths", "B. ninths", "C. tenths", "D. sevenths"],
        "answer": "B",
        "explanation": "9 equal parts → ninths.",
        "difficulty": 1,
        "hints": ["Count = 9.", "9 = ninths."],
        "feedback": {"correct": "Right — ninths.", "incorrect": "9 equal parts = ninths."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "A rectangle has 4 pieces drawn on it: 3 are equal and 1 is missing (empty space). Can we name this in fourths?",
        "choices": ["A. Yes — there are 4 spots", "B. No — pieces don't cover the whole", "C. Yes — call it thirds", "D. No — call it eighths"],
        "answer": "B",
        "explanation": "Empty space means the pieces don't cover the whole. Cannot name as fourths until all 4 equal parts are present.",
        "difficulty": 2,
        "hints": ["Empty space = gap.", "Pieces must cover the whole."],
        "feedback": {"correct": "Right — not valid fourths.", "incorrect": "Pieces must fully cover the whole. Empty space = not a valid fraction partition."},
    },
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 458 + 376.",
        "choices": ["A. 724", "B. 734", "C. 824", "D. 834"],
        "answer": "D",
        "explanation": "458+376: 8+6=14 (carry 1), 5+7+1=13 (carry 1), 4+3+1=8. Result: 834.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 14. Tens: 13. Hundreds: 8."],
        "feedback": {"correct": "Right — 834.", "incorrect": "458+376=834."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 705 − 268.",
        "choices": ["A. 437", "B. 447", "C. 537", "D. 547"],
        "answer": "A",
        "explanation": "705−268: 5−8 borrow → 15−8=7; tens 9−6=3 (after lending across zero); hundreds 6−2=4. Result: 437.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "705−268=437."],
        "feedback": {"correct": "Right — 437.", "incorrect": "705−268=437."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 643 books. They donated 178, then bought 256 more. How many books now?",
        "choices": ["A. 465", "B. 543", "C. 721", "D. 899"],
        "answer": "C",
        "explanation": "Step 1: 643−178=465. Step 2: 465+256=721.",
        "difficulty": 3,
        "hints": ["Subtract donated, then add bought.", "643−178=465, 465+256=721."],
        "feedback": {"correct": "Right — 721 books.", "incorrect": "643−178=465, then +256=721."},
        "review_from": "U1",
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Maya draws a square cut into a tall thin rectangle and a short wide rectangle. She says 'these are halves because there are 2 pieces.' Is she correct?",
        "choices": ["A. Yes — 2 pieces means halves", "B. Only if the two pieces have equal area", "C. No — halves must be the same shape", "D. No — halves only work on circles"],
        "answer": "B",
        "explanation": "Halves = 2 equal-AREA parts. Different shapes can be halves IF the areas are equal.",
        "difficulty": 3,
        "hints": ["Count = 2 but check area.", "Halves need equal area, not equal shape."],
        "feedback": {"correct": "Right — equal area required.", "incorrect": "Halves require equal AREA, not equal shape. Different shapes can be halves if areas match."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "A circle is divided by 3 lines from the center, but the slices have different sizes. How many EQUAL parts can be named?",
        "choices": ["A. 3 (because there are 3 slices)", "B. 0 (slices unequal — not a valid fraction partition)", "C. 6 (three lines make 6 slices)", "D. 1 (only the smallest slice)"],
        "answer": "B",
        "explanation": "Unequal slices cannot be named as a fraction. The partition is invalid for naming.",
        "difficulty": 3,
        "hints": ["Equal-area required.", "Unequal partition = no fraction name."],
        "feedback": {"correct": "Right — invalid fraction partition.", "incorrect": "Without equal areas, no fraction name applies."},
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 새 7단계 표준으로 업그레이드됨.")
        return

    sections = d.get("sections", {})
    pretest = sections.get("pretest", [])
    learn = sections.get("learn", [])
    try_ = sections.get("try", [])
    r1 = sections.get("practice_r1", [])
    r2 = sections.get("practice_r2", [])
    r3 = sections.get("practice_r3", [])

    # Add new LEARN cards (LEARN_04~08)
    learn.extend(NEW_LEARN_CARDS)

    # Add R1_08~R1_10
    r1.extend(NEW_R1_ITEMS)

    # Trim r2 to first 4 (existing items), append 6 new (3 fraction + 3 U1 review)
    r2.extend(NEW_R2_ITEMS)

    # Add R3_04~R3_05
    r3.extend(NEW_R3_ITEMS)

    sections_map = {
        "pretest": pretest,
        "learn": learn,
        "try": try_,
        "practice_r1": r1,
        "practice_r2": r2,
        "practice_r3": r3,
    }

    for sec_key in sections_map:
        sections_map[sec_key] = [normalize_item(it) for it in sections_map[sec_key]]

    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    # Promote sections to top-level (matching U2-U7 format)
    d.pop("sections", None)
    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U7 L11 — 연산 순서 (3.OA.D.8)",
        "current":      "G3 — 전체의 균등 분할: 분수 이름 짓기 (3.NF.A.1)",
        "successor":    "G3 U8 L2 — 균등 공유: 분수 표현 (3.NF.A.1)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
