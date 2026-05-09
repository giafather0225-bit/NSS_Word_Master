"""
G3 U4 L7 — Patterns in the Multiplication Table 7단계 업그레이드 스크립트
============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.D.9 (곱셈표 패턴 — 짝/홀, 제곱수, 9의 자릿수 합 등)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L7_patterns_multiplication_table.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.D.9.M03"],
    "PT_02": ["3.OA.D.9.M02"],
    "PT_03": ["3.OA.D.9.M06"],
    "PT_04": ["3.OA.D.9.M05"],
    "PT_05": ["3.OA.D.9.M02"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.D.9.M03"],
    "TRY_02": ["3.OA.D.9.M02"],
    "TRY_03": ["3.OA.D.9.M05"],
    "TRY_04": ["3.OA.D.9.M06"],
    "TRY_05": ["3.OA.D.9.M02"],
    "R1_01": ["3.OA.D.9.M06"],
    "R1_02": ["3.OA.D.9.M02"],
    "R1_03": ["3.OA.D.9.M05"],
    "R1_04": ["3.OA.D.9.M06"],
    "R1_05": ["3.OA.D.9.M02"],
    "R1_06": ["3.OA.D.9.M01"],
    "R1_07": ["3.OA.D.9.M06"],
    "R1_08": ["3.OA.D.9.M08"],
    "R1_09": ["3.OA.D.9.M05"],
    "R1_10": ["3.OA.D.9.M04"],
    "R2_01": ["3.OA.D.9.M01"],
    "R2_02": ["3.OA.D.9.M04"],
    "R2_03": ["3.OA.D.9.M05"],
    "R2_04": ["3.OA.D.9.M02"],
    "R2_05": ["3.OA.D.9.M06"],
    "R2_06": ["3.OA.D.9.M05"],
    "R2_07": ["3.OA.D.9.M03"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.9.M02"],
    "R3_02": ["3.OA.D.9.M01"],
    "R3_03": ["3.OA.D.9.M05"],
    "R3_04": ["3.OA.D.9.M04"],
    "R3_05": ["3.OA.D.9.M02"],
}

SKILL_TAGS = {
    "PT_01": "row_column_intersection",
    "PT_02": "even_odd_product",
    "PT_03": "x5_pattern",
    "PT_04": "square_numbers",
    "PT_05": "even_odd_product",
    "LEARN_01": "table_layout",
    "LEARN_02": "row_patterns",
    "LEARN_03": "even_odd_pattern",
    "LEARN_04": "diagonal_squares",
    "LEARN_05": "x9_digit_sum",
    "LEARN_06": "even_odd_pattern",
    "LEARN_07": "diagonal_squares",
    "LEARN_08": "patterns_summary",
    "TRY_01": "row_column_intersection",
    "TRY_02": "even_odd_product",
    "TRY_03": "square_numbers",
    "TRY_04": "skip_count_continue",
    "TRY_05": "even_odd_product",
    "R1_01": "skip_count_continue",
    "R1_02": "even_odd_product",
    "R1_03": "square_numbers",
    "R1_04": "skip_count_continue",
    "R1_05": "even_odd_product",
    "R1_06": "commutative_table",
    "R1_07": "skip_count_continue",
    "R1_08": "x10_pattern",
    "R1_09": "square_numbers",
    "R1_10": "x9_digit_sum",
    "R2_01": "commutative_table",
    "R2_02": "x9_digit_sum",
    "R2_03": "square_numbers",
    "R2_04": "even_odd_product",
    "R2_05": "skip_count_continue",
    "R2_06": "square_numbers",
    "R2_07": "row_column_intersection",
    "R2_08": "addition_3digit",      # U1
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "count_odd_products",
    "R3_02": "table_symmetry",
    "R3_03": "nth_square",
    "R3_04": "x9_digit_sum_apply",
    "R3_05": "count_even_products",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.7 'Patterns on the Multiplication Table' pp.163-166",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic G — Multiplication Patterns and Tables",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "row_column_intersection")
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
        "title": "짝수·홀수 곱셈 규칙",
        "content": (
            "곱셈표에서 곱의 짝/홀 패턴은 단순합니다: "
            "짝수 × 어떤 수 = 짝수 (예: 2×7=14, 6×3=18). "
            "홀수 × 홀수 = 홀수 (예: 3×5=15, 7×9=63). "
            "이유: 짝수에는 2가 인자에 포함됨 → 짝의 배수. "
            "홀수×홀수만 홀수가 나옴 — 두 인자 모두 2가 없어야 곱도 2가 없음. "
            "흔한 실수: '홀수 + 짝수 = 홀수' 규칙(덧셈)을 곱셈에 잘못 적용."
        ),
        "cpa_stage": "abstract",
        "visual_type": "even_odd_chart",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "대각선 = 제곱수 (square numbers)",
        "content": (
            "곱셈표의 왼쪽 위에서 오른쪽 아래로 가는 대각선: "
            "1, 4, 9, 16, 25, 36, 49, 64, 81, 100. "
            "각 값은 같은 수를 두 번 곱한 것 — 1×1, 2×2, 3×3,... "
            "이 수들을 '제곱수(square number)'라 부름 — 정사각형 배열을 만드므로. "
            "예: 9 = 3 × 3 → 3행 × 3열의 정사각형 9개. "
            "흔한 실수: 더블(2배)과 제곱(자기 자신 ×) 혼동."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "diagonal_squares",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "곱셈표 패턴 6가지 요약",
        "content": (
            "1) 행/열 교환: 행 a 열 b = 행 b 열 a (교환법칙으로 표는 대각 대칭). "
            "2) ×5 행: 끝자리 0/5 반복 (5,10,15,...). "
            "3) ×10 행: 끝자리 항상 0 (10,20,30,...). "
            "4) ×9 행: 자릿수 합 항상 9 (18→1+8=9, 27→2+7=9). "
            "5) 대각선: 제곱수 (1, 4, 9, 16,...). "
            "6) 짝/홀: 둘 다 홀수일 때만 곱이 홀수. "
            "활용: 모르는 사실을 패턴으로 점검 가능 (예: 7 × 8 = 짝수가 맞는지)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "patterns_summary",
    },
]

U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the sum: 538 + 274.",
        "choices": ["A. 712", "B. 802", "C. 812", "D. 912"],
        "answer": "C",
        "explanation": "538+274: 8+4=12 (carry 1), 3+7+1=11 (carry 1), 5+2+1=8. Result: 812.",
        "hints": [
            "Two carries.",
            "Ones: 12. Tens: 11. Hundreds: 8.",
        ],
        "feedback": {
            "correct": "Right — 812.",
            "incorrect": "538+274=812.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 405 − 168.",
        "choices": ["A. 237", "B. 247", "C. 337", "D. 347"],
        "answer": "A",
        "explanation": "405−168: 5−8 borrow → 15−8=7; tens 9−6=3 (after lending); hundreds 3−1=2. Result: 237.",
        "hints": [
            "Borrow across the zero in tens.",
            "405−168=237.",
        ],
        "feedback": {
            "correct": "Right — 237.",
            "incorrect": "405−168=237.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A school had 762 pencils. Students used 245, then the school bought 187 more. How many pencils now?",
        "choices": ["A. 330", "B. 517", "C. 704", "D. 949"],
        "answer": "C",
        "explanation": "Step 1: 762−245=517. Step 2: 517+187=704.",
        "hints": [
            "Subtract used, then add bought.",
            "762−245=517, 517+187=704.",
        ],
        "feedback": {
            "correct": "Right — 704 pencils.",
            "incorrect": "762−245=517, then +187=704.",
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
        "prerequisite": "G3 U4 L1-L6 — ×2~×7 사실, 분배·결합법칙 (3.OA.C.7, 3.OA.B.5)",
        "current":      "G3 — 곱셈표 패턴 (짝/홀, 제곱수, ×9 자릿수 합) (3.OA.D.9)",
        "successor":    "G3 U4 L8 — ×8 사실 (×4 더블 또는 ×10−×2; 3.OA.C.7)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l7.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
