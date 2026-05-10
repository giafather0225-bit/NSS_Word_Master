"""
G3 U8 L6 — Relate Fractions and Whole Numbers 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3c (분수와 자연수 — b/b=1, nb/b=n, n=n/1)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L6_relate_fractions_and_whole_numbers.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.3.M01"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    **{f"TRY_0{i}": ["3.NF.A.3.M01"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.3.M01"] for i in range(1,11)},
    **{f"R2_0{i}": ["3.NF.A.3.M02"] for i in range(1,8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.3.M02"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "fraction_whole_number" for i in range(1,6)},
    "LEARN_01": "fraction_equal_one",
    "LEARN_02": "fraction_greater_than_one",
    "LEARN_03": "whole_as_fraction",
    "LEARN_04": "fractions_for_n_wholes",
    "LEARN_05": "n_over_1_form",
    "LEARN_06": "denominator_independence",
    "LEARN_07": "convert_routine",
    "LEARN_08": "number_line_whole_marks",
    **{f"TRY_0{i}": "fraction_whole_number" for i in range(1,6)},
    **{f"R1_{i:02d}": "fraction_whole_number" for i in range(1,11)},
    **{f"R2_0{i}": "fraction_whole_number" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "fraction_whole_number" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "pictorial",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.6 'Relate Fractions and Whole Numbers' pp.333-336",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic D — Fractions on the Number Line",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "fraction_whole_number")
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
        "title": "n 전체 = nb/b — 패턴 공식",
        "content": (
            "n개의 전체를 b분의 단위로 표현하면: n = nb/b. "
            "예: 2 전체 = 2×4/4 = 8/4 (사분의 단위로). "
            "예: 3 전체 = 3×6/6 = 18/6. "
            "🔍 빠른 검산: 분자가 분모의 정확히 n배인가? 그렇다면 답은 n."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "n_wholes_pattern",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "n = n/1 — 자연수의 분수 표현",
        "content": (
            "모든 자연수는 분모 1의 분수로 쓸 수 있음. "
            "  3 = 3/1, 5 = 5/1, 100 = 100/1. "
            "이유: '전체 1을 1등분 → 한 부분 = 전체' → n번 모으면 n. "
            "응용: 분수 연산에서 자연수를 분수로 바꿔 통일된 형태로 처리."
        ),
        "cpa_stage": "abstract",
        "visual_type": "n_over_1",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "분모 무관 — 어떤 분모로도 1 표현",
        "content": (
            "1 = 2/2 = 3/3 = 4/4 = 100/100 — 모두 같은 1. "
            "분모는 다르지만 분자=분모이면 항상 1. "
            "예: 케이크를 어떻게 자르든 모든 조각을 합치면 1 (전체). "
            "흔한 실수 (M01): 분모가 크면 더 크다고 착각 — 분자/분모가 같으면 모두 1."
        ),
        "cpa_stage": "abstract",
        "visual_type": "denominator_independence",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "변환 루틴 — 분수↔자연수",
        "content": (
            "분수 a/b를 자연수로 바꿀 때: a를 b로 나눔 → a÷b. "
            "  나누어 떨어지면: 자연수. (예: 12/4 → 12÷4 = 3) "
            "  나누어 떨어지지 않으면: 자연수가 아님 (대분수). "
            "자연수 n을 분수로 바꿀 때: n × b/b. "
            "  예: 5를 사분의 단위로 → 5 × 4/4 = 20/4."
        ),
        "cpa_stage": "abstract",
        "visual_type": "convert_routine",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "수직선 위 자연수 위치",
        "content": (
            "0~3 수직선을 사분의 단위로 표시하면: "
            "  0/4 = 0, 4/4 = 1, 8/4 = 2, 12/4 = 3. "
            "자연수는 분자가 분모의 정수배인 위치에 있음. "
            "🔍 검산: 수직선에서 1, 2, 3 자리 → 분자가 b의 정수배."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "whole_marks_on_line",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "Write 2 as a fraction with denominator 5.",
        "choices": ["A. 2/5", "B. 5/2", "C. 7/5", "D. 10/5"],
        "answer": "D",
        "explanation": "2 = 2 × 5/5 = 10/5.",
        "difficulty": 2,
        "hints": ["n × b/b = nb/b.", "2×5=10."],
        "feedback": {"correct": "정답! 10/5.", "incorrect": "2 = 10/5."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Which whole number equals 9/3?",
        "choices": ["A. 2", "B. 3", "C. 6", "D. 9"],
        "answer": "B",
        "explanation": "9÷3 = 3.",
        "difficulty": 1,
        "hints": ["9를 3으로 나누면?"],
        "feedback": {"correct": "정답! 3.", "incorrect": "9/3 = 3."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "How many fifths are in 4 wholes?",
        "choices": ["A. 9", "B. 15", "C. 20", "D. 25"],
        "answer": "C",
        "explanation": "4 × 5 = 20 → 20/5.",
        "difficulty": 2,
        "hints": ["전체 수 × 분모.", "4×5=20."],
        "feedback": {"correct": "정답! 20.", "incorrect": "4 wholes = 20 fifths."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "How many thirds are in 5 wholes?",
        "choices": ["A. 8", "B. 10", "C. 12", "D. 15"],
        "answer": "D",
        "explanation": "5 × 3 = 15 → 15/3.",
        "difficulty": 2,
        "hints": ["5 × 3."],
        "feedback": {"correct": "정답! 15.", "incorrect": "5×3=15."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "Which whole number equals 16/4?",
        "choices": ["A. 2", "B. 3", "C. 4", "D. 8"],
        "answer": "C",
        "explanation": "16÷4 = 4.",
        "difficulty": 1,
        "hints": ["16/4 = ?"],
        "feedback": {"correct": "정답! 4.", "incorrect": "16/4 = 4."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Write 7 as a fraction with denominator 1.",
        "choices": ["A. 1/7", "B. 7/1", "C. 7/7", "D. 14/2"],
        "answer": "B",
        "explanation": "n = n/1 → 7 = 7/1.",
        "difficulty": 1,
        "hints": ["분모 1 = 자연수 그대로."],
        "feedback": {"correct": "정답! 7/1.", "incorrect": "7 = 7/1."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Which fraction does NOT equal 1?",
        "choices": ["A. 5/5", "B. 8/8", "C. 6/9", "D. 10/10"],
        "answer": "C",
        "explanation": "분자=분모이면 1. 6/9는 분자≠분모.",
        "difficulty": 2,
        "hints": ["1 = b/b 형태인가?"],
        "feedback": {"correct": "정답! 6/9.", "incorrect": "분자=분모인 것만 1."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Lin says 6/2 equals 4 because 6 + 2 = ... wait, 6 − 2 = 4. Is she right?",
        "choices": ["A. 맞음", "B. 틀림 — 분수는 나눗셈, 6/2 = 3", "C. 맞음, 다른 방법", "D. 분수는 자연수가 될 수 없음"],
        "answer": "B",
        "explanation": "분수 a/b = a÷b. 6/2 = 6÷2 = 3.",
        "difficulty": 3,
        "hints": ["분수는 뺄셈 아님.", "a/b = a÷b."],
        "feedback": {"correct": "정답! 3이 맞음.", "incorrect": "6/2 = 3 (나눗셈)."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Order from smallest: 4/4, 6/6, 9/3.",
        "choices": ["A. 4/4 < 6/6 < 9/3", "B. 4/4 = 6/6 < 9/3", "C. 9/3 < 4/4 < 6/6", "D. 4/4 < 9/3 < 6/6"],
        "answer": "B",
        "explanation": "4/4 = 1, 6/6 = 1, 9/3 = 3.",
        "difficulty": 3,
        "hints": ["분자=분모이면 1.", "9/3 = 3."],
        "feedback": {"correct": "정답!", "incorrect": "4/4=6/6=1, 9/3=3."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "On a number line from 0 to 4 divided into halves, what fraction marks the position of 2?",
        "choices": ["A. 2/2", "B. 4/2", "C. 6/2", "D. 4/4"],
        "answer": "B",
        "explanation": "2 = 2 × 2/2 = 4/2.",
        "difficulty": 3,
        "hints": ["2를 분모 2의 분수로."],
        "feedback": {"correct": "정답! 4/2.", "incorrect": "2 = 4/2."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Which statement about 12/4 is true?",
        "choices": [
            "A. 12/4 = 3 (정수)",
            "B. 12/4 < 1",
            "C. 12/4는 자연수가 아님",
            "D. 12/4 = 12 + 4"
        ],
        "answer": "A",
        "explanation": "12÷4 = 3.",
        "difficulty": 2,
        "hints": ["12/4 = ?"],
        "feedback": {"correct": "정답! 3.", "incorrect": "12/4 = 3."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 348 + 257.",
        "choices": ["A. 495", "B. 505", "C. 595", "D. 605"],
        "answer": "D",
        "explanation": "348+257: 8+7=15 (carry 1), 4+5+1=10 (carry 1), 3+2+1=6. Result: 605.",
        "difficulty": 2,
        "hints": ["Two carries.", "348+257=605."],
        "feedback": {"correct": "Right — 605.", "incorrect": "348+257=605."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 504 − 268.",
        "choices": ["A. 236", "B. 246", "C. 336", "D. 346"],
        "answer": "A",
        "explanation": "504−268=236 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "504−268=236."],
        "feedback": {"correct": "Right — 236.", "incorrect": "504−268=236."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bakery had 532 muffins. They sold 187, then baked 245 more. How many muffins now?",
        "choices": ["A. 345", "B. 432", "C. 590", "D. 777"],
        "answer": "C",
        "explanation": "Step 1: 532−187=345. Step 2: 345+245=590.",
        "difficulty": 3,
        "hints": ["Subtract sold, add baked.", "532−187=345, 345+245=590."],
        "feedback": {"correct": "Right — 590 muffins.", "incorrect": "532−187=345, then +245=590."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 업그레이드됨.")
        return

    nested = d.get("sections", {})
    sm = {
        "pretest": list(nested.get("pretest", [])),
        "learn": list(nested.get("learn", [])),
        "try": list(nested.get("try", [])),
        "practice_r1": list(nested.get("practice_r1", [])),
        "practice_r2": list(nested.get("practice_r2", [])),
        "practice_r3": list(nested.get("practice_r3", [])),
    }

    sm["learn"].extend(NEW_LEARN_CARDS)
    sm["try"].extend(NEW_TRY_ITEMS)
    sm["practice_r1"].extend(NEW_R1_ITEMS)
    sm["practice_r2"].extend(NEW_R2_ITEMS)
    sm["practice_r2"].extend(U1_REVIEW_R2)
    sm["practice_r3"].extend(NEW_R3_ITEMS)

    for sec_key in sm:
        sm[sec_key] = [normalize_item(it) for it in sm[sec_key]]

    counts = {k: len(v) for k, v in sm.items()}
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    for k in sm:
        d[k] = sm[k]
    if "sections" in d:
        del d["sections"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U8 L5 — 수직선 위의 분수 (3.NF.A.2)",
        "current":      "G3 — 분수와 자연수: b/b=1, n=n/1, nb/b=n (3.NF.A.3c)",
        "successor":    "G3 U8 L7 — 그룹의 분수 (3.NF.A.1)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l6.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
