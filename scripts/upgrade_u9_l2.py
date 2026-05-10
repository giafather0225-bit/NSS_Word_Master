"""
G3 U9 L2 — Compare Same Denominator 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3d (같은 분모 분수 비교 — 분자가 큰 쪽이 큼)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/L2_compare_same_denominator.json"

ID_PREFIX_MAP = {
    "c9_l2_pre_": "PT_",
    "c9_l2_learn_": "LEARN_",
    "c9_l2_try_": "TRY_",
    "c9_l2_pr1_": "R1_",
    "c9_l2_pr2_": "R2_",
    "c9_l2_pr3_": "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.3.M01"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    **{f"TRY_0{i}": ["3.NF.A.3.M01"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.3.M01"] for i in range(1,11)},
    **{f"R2_0{i}": ["3.NF.A.3.M01"] for i in range(1,8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.3.M01"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "compare_same_denominator" for i in range(1,6)},
    "LEARN_01": "same_denom_rule",
    "LEARN_02": "fraction_strip_compare",
    "LEARN_03": "equal_fractions",
    "LEARN_04": "numerator_count_compare",
    "LEARN_05": "zero_and_one_endpoints",
    "LEARN_06": "same_denom_routine",
    "LEARN_07": "ordering_same_denom",
    "LEARN_08": "verify_with_pictures",
    **{f"TRY_0{i}": "compare_same_denominator" for i in range(1,6)},
    **{f"R1_{i:02d}": "compare_same_denominator" for i in range(1,11)},
    **{f"R2_0{i}": "compare_same_denominator" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "compare_same_denominator" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "pictorial",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Lesson 9.2 'Compare Fractions with the Same Denominator' pp.357-360",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic F — Comparison, Order, and Size of Fractions",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


LEARN_TITLE_MAP = {
    "LEARN_01": "같은 분모 규칙 — 분자만 비교",
    "LEARN_02": "분수 스트립 — 시각적 비교",
    "LEARN_03": "같은 분수 — 분자도 같으면 =",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "분수 비교"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "compare_same_denominator"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "compare_strategy",
    }


TYPE_MAP = {
    "multiple_choice": "MC",
    "compare": "MC",
    "word_problem": "MC",
    "fill_in": "fill_in",
    "open_response": "open_response",
}


def normalize_item(item: dict) -> dict:
    old_id = item["id"]
    item_id = remap_id(old_id)
    item["id"] = item_id

    if item_id.startswith("LEARN_") and item.get("type") == "instruction_check":
        return normalize_existing_learn(item, item_id)
    if item_id.startswith("LEARN_") and item.get("type") == "card":
        item["type"] = "concept_card"

    if item.get("type") in TYPE_MAP:
        item["type"] = TYPE_MAP[item["type"]]
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "compare_same_denominator")
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
        "title": "분자 = 조각 개수 — 많을수록 큼",
        "content": (
            "같은 분모 분수에서 분자는 '조각 개수'를 의미. "
            "조각 크기가 같으니 개수가 많을수록 합도 큼. "
            "  3/8 = 1/8짜리 조각 3개. "
            "  5/8 = 1/8짜리 조각 5개. "
            "5개 > 3개 → 5/8 > 3/8. 🔍 분자 비교 = 자연수 비교."
        ),
        "cpa_stage": "abstract",
        "visual_type": "numerator_count",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "끝점 분수 — 0/b와 b/b",
        "content": (
            "같은 분모 분수의 양 끝: "
            "  0/b = 0 (조각 없음, 가장 작음). "
            "  b/b = 1 (전체, 가장 큼). "
            "예: 분모 4 → 0/4 = 0, 4/4 = 1. 그 사이 1/4, 2/4, 3/4. "
            "🔍 비교 시: 0/b가 가장 작고 b/b가 가장 큼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "endpoints",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "같은 분모 비교 3단계 루틴",
        "content": (
            "두 분수 비교 3단계: "
            "  단계 1) 분모가 같은지 확인. "
            "  단계 2) 같다면 → 분자만 비교. "
            "  단계 3) 분자 큰 쪽이 큰 분수, 같으면 =. "
            "예: 3/8 vs 7/8 → 1) 분모 같음 ✓, 2) 3 vs 7, 3) 3 < 7 → 3/8 < 7/8."
        ),
        "cpa_stage": "abstract",
        "visual_type": "same_denom_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "여러 분수 정렬 — 분자 순서대로",
        "content": (
            "같은 분모 분수를 작은 것부터 정렬할 때 분자만 보면 됨. "
            "예: 1/6, 5/6, 2/6, 4/6 → 분자: 1, 5, 2, 4. "
            "정렬: 1 < 2 < 4 < 5 → 1/6 < 2/6 < 4/6 < 5/6. "
            "🔍 단축 방법: 분자만 보고 자연수 정렬처럼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "ordering_same_denom",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "그림으로 검산 — 막대/원 비교",
        "content": (
            "두 분수가 진짜 다른지 그림으로 확인 가능: "
            "  같은 길이의 막대 두 개를 모두 b등분. "
            "  각 분수의 색칠 부분 길이를 옆으로 맞춰 비교. "
            "예: 2/6 vs 4/6 → 4/6 막대가 더 길게 색칠 → 4/6이 큼. "
            "🔍 그림 비교 = 정확하지만 느림 → 빠른 분자 비교가 우선."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "verify_with_pictures",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "Compare: 6/8 ○ 3/8",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "같은 분모 8. 6 > 3.",
        "difficulty": 1,
        "hints": ["분자 비교."],
        "feedback": {"correct": "정답!", "incorrect": "6/8 > 3/8."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Which is greater: 7/8 or 5/8?",
        "choices": ["A. 7/8", "B. 5/8", "C. 같음", "D. 비교 불가"],
        "answer": "A",
        "explanation": "같은 분모. 7 > 5.",
        "difficulty": 1,
        "hints": ["분자만 비교."],
        "feedback": {"correct": "정답! 7/8.", "incorrect": "7 > 5 → 7/8."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "Order from smallest: 5/6, 1/6, 4/6.",
        "choices": [
            "A. 1/6 < 4/6 < 5/6",
            "B. 1/6 < 5/6 < 4/6",
            "C. 5/6 < 4/6 < 1/6",
            "D. 4/6 < 1/6 < 5/6"
        ],
        "answer": "A",
        "explanation": "분자: 5, 1, 4 → 1, 4, 5.",
        "difficulty": 2,
        "hints": ["분자만 정렬."],
        "feedback": {"correct": "정답!", "incorrect": "1/6 < 4/6 < 5/6."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Compare: 5/8 ○ 5/8",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": "=",
        "explanation": "분자 분모 모두 같음.",
        "difficulty": 1,
        "hints": ["같은 분수 = 같음."],
        "feedback": {"correct": "정답!", "incorrect": "= (같은 분수)."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "Compare: 2/4 ○ 0/4",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "0/4 = 0. 2/4 > 0.",
        "difficulty": 1,
        "hints": ["0/b = 0."],
        "feedback": {"correct": "정답!", "incorrect": "2/4 > 0/4."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Order from largest: 1/4, 4/4, 2/4, 3/4.",
        "choices": [
            "A. 4/4 > 3/4 > 2/4 > 1/4",
            "B. 1/4 > 2/4 > 3/4 > 4/4",
            "C. 4/4 > 1/4 > 2/4 > 3/4",
            "D. 2/4 > 4/4 > 1/4 > 3/4"
        ],
        "answer": "A",
        "explanation": "분자: 4, 3, 2, 1.",
        "difficulty": 2,
        "hints": ["분자만 큰 순."],
        "feedback": {"correct": "정답!", "incorrect": "4/4 > 3/4 > 2/4 > 1/4."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Mike says 7/8 < 4/8 because 7 is closer to 8 than 4. Why is this wrong?",
        "choices": [
            "A. 분자 큰 쪽이 큰 분수 → 7/8 > 4/8",
            "B. 8에 가까운 분자가 작음",
            "C. 분모도 비교해야 함",
            "D. 정답"
        ],
        "answer": "A",
        "explanation": "같은 분모에서는 단순히 분자 비교. 7 > 4 → 7/8 > 4/8.",
        "difficulty": 3,
        "hints": ["같은 분모 → 분자 비교."],
        "feedback": {"correct": "정답!", "incorrect": "분자 큰 쪽이 큼."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Two same-size cakes. Liam ate 3/8, Mia ate 6/8. How many more eighths did Mia eat?",
        "choices": ["A. 1", "B. 2", "C. 3", "D. 6"],
        "answer": "C",
        "explanation": "6 − 3 = 3 (8분의 단위).",
        "difficulty": 2,
        "hints": ["분자 차이."],
        "feedback": {"correct": "정답! 3.", "incorrect": "6−3=3."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Order from smallest to largest: 5/6, 0/6, 3/6, 6/6.",
        "choices": [
            "A. 0/6 < 3/6 < 5/6 < 6/6",
            "B. 0/6 < 5/6 < 3/6 < 6/6",
            "C. 6/6 < 5/6 < 3/6 < 0/6",
            "D. 3/6 < 0/6 < 5/6 < 6/6"
        ],
        "answer": "A",
        "explanation": "분자: 5, 0, 3, 6 → 0, 3, 5, 6.",
        "difficulty": 2,
        "hints": ["분자 자연수 정렬."],
        "feedback": {"correct": "정답!", "incorrect": "0/6 < 3/6 < 5/6 < 6/6."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Maya, Sara, Eli each have an identical chocolate bar. Maya eats 7/10, Sara eats 4/10, Eli eats 9/10. Order from least to most.",
        "choices": [
            "A. Sara < Maya < Eli",
            "B. Maya < Sara < Eli",
            "C. Eli < Maya < Sara",
            "D. Sara < Eli < Maya"
        ],
        "answer": "A",
        "explanation": "분자: 7, 4, 9 → 4, 7, 9.",
        "difficulty": 3,
        "hints": ["같은 분모, 분자 정렬."],
        "feedback": {"correct": "정답!", "incorrect": "Sara(4) < Maya(7) < Eli(9)."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Write a fraction with denominator 6 that is GREATER than 4/6 but LESS than 6/6.",
        "choices": ["A. 3/6", "B. 5/6", "C. 6/6", "D. 7/6"],
        "answer": "B",
        "explanation": "4/6 < ? < 6/6 → 5/6.",
        "difficulty": 3,
        "hints": ["4와 6 사이 분자."],
        "feedback": {"correct": "정답! 5/6.", "incorrect": "분자가 4보다 크고 6보다 작음 → 5."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 376 + 248.",
        "choices": ["A. 514", "B. 524", "C. 614", "D. 624"],
        "answer": "D",
        "explanation": "376+248: 6+8=14 (carry 1), 7+4+1=12 (carry 1), 3+2+1=6. Result: 624.",
        "difficulty": 2,
        "hints": ["Two carries.", "376+248=624."],
        "feedback": {"correct": "Right — 624.", "incorrect": "376+248=624."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 805 − 467.",
        "choices": ["A. 338", "B. 348", "C. 438", "D. 448"],
        "answer": "A",
        "explanation": "805−467=338 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "805−467=338."],
        "feedback": {"correct": "Right — 338.", "incorrect": "805−467=338."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bookstore had 712 books. They sold 187, then received 245. How many books now?",
        "choices": ["A. 525", "B. 770", "C. 850", "D. 1144"],
        "answer": "B",
        "explanation": "Step 1: 712−187=525. Step 2: 525+245=770.",
        "difficulty": 3,
        "hints": ["Subtract sold, add received.", "712−187=525, 525+245=770."],
        "feedback": {"correct": "Right — 770 books.", "incorrect": "712−187=525, then +245=770."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 업그레이드됨.")
        return

    sm = {
        "pretest": list(d.get("pretest", [])),
        "learn": list(d.get("learn", [])),
        "try": list(d.get("try", [])),
        "practice_r1": list(d.get("practice_r1", [])),
        "practice_r2": list(d.get("practice_r2", [])),
        "practice_r3": list(d.get("practice_r3", [])),
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

    d["vertical_alignment"] = {
        "prerequisite": "G3 U9 L1 — 분수 비교 문장제: 같은 전체 가정 (3.NF.A.3d)",
        "current":      "G3 — 같은 분모 분수 비교: 분자가 큰 쪽이 큼 (3.NF.A.3d)",
        "successor":    "G3 U9 L3 — 같은 분자 분수 비교 (3.NF.A.3d)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
