"""
G3 U9 L5 — Compare and Order Fractions 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3d (분수 정렬 — 같은 분모/분자/벤치마크 통합)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/L5_compare_and_order_fractions.json"

ID_PREFIX_MAP = {
    "c9_l5_pre_": "PT_",
    "c9_l5_learn_": "LEARN_",
    "c9_l5_try_": "TRY_",
    "c9_l5_pr1_": "R1_",
    "c9_l5_pr2_": "R2_",
    "c9_l5_pr3_": "R3_",
}

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
    **{f"PT_0{i}": "order_fractions" for i in range(1,6)},
    "LEARN_01": "order_same_denom",
    "LEARN_02": "order_same_num",
    "LEARN_03": "sort_by_benchmark",
    "LEARN_04": "order_three_step",
    "LEARN_05": "ordering_strategies",
    "LEARN_06": "between_fractions",
    "LEARN_07": "verify_order",
    "LEARN_08": "real_world_ordering",
    **{f"TRY_0{i}": "order_fractions" for i in range(1,6)},
    **{f"R1_{i:02d}": "order_fractions" for i in range(1,11)},
    **{f"R2_0{i}": "order_fractions" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "order_fractions" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "pictorial", "LEARN_07": "abstract", "LEARN_08": "pictorial",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Lesson 9.5 'Compare and Order Fractions' pp.369-372",
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
    "LEARN_01": "같은 분모 정렬 — 분자만 보기",
    "LEARN_02": "같은 분자 정렬 — 분모 큰 순",
    "LEARN_03": "벤치마크로 분류 후 정렬",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "분수 정렬"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "order_fractions"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "ordering_strategy",
    }


TYPE_MAP = {
    "multiple_choice": "MC",
    "compare": "MC",
    "word_problem": "MC",
    "fill_in": "fill_in",
    "open_response": "open_response",
    "ordering": "ordering",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "order_fractions")
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
        "title": "정렬 3단계 루틴",
        "content": (
            "여러 분수 정렬 3단계: "
            "  단계 1) 모든 분수를 한 줄에 적기. "
            "  단계 2) 공통 패턴 찾기 (같은 분모 / 같은 분자 / 다 다름). "
            "  단계 3) 패턴별 규칙 적용 → 작은 → 큰 순으로 다시 적기. "
            "예: 5/8, 1/8, 7/8 → 같은 분모 → 분자 1, 5, 7 → 1/8 < 5/8 < 7/8."
        ),
        "cpa_stage": "abstract",
        "visual_type": "order_routine",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "혼합 분수 정렬 — 벤치마크 분류",
        "content": (
            "분모/분자 모두 다른 분수들을 정렬할 때: "
            "  단계 1) 1/2와 비교해 < 1/2 / = 1/2 / > 1/2 그룹으로 분류. "
            "  단계 2) 그룹 안에서 추가 비교 (벤치마크 1, 같은 분모로 변환 등). "
            "예: 1/8, 5/6, 1/2, 3/8 → "
            "    < 1/2: 1/8, 3/8 (분자 비교 → 1/8 < 3/8) "
            "    = 1/2: 1/2 "
            "    > 1/2: 5/6 "
            "결과: 1/8 < 3/8 < 1/2 < 5/6."
        ),
        "cpa_stage": "abstract",
        "visual_type": "benchmark_classify",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "두 분수 사이 — 'between'",
        "content": (
            "두 분수 사이의 분수 찾기: "
            "  단계 1) 양 끝 값 확인 (예: 2/8과 6/8). "
            "  단계 2) 같은 분모로 표현 가능한지 확인. "
            "  단계 3) 사이 값 선택. "
            "예: 2/8과 6/8 사이 → 3/8, 4/8, 5/8 모두 가능. "
            "🔍 수직선 위에서 순서가 시각적으로 잘 보임."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "between_fractions",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "정렬 검산 — 인접 쌍 비교",
        "content": (
            "정렬한 결과를 검산: 인접한 두 분수씩 짝지어 부등호 확인. "
            "  예: 1/8 < 3/8 < 1/2 < 5/6 → "
            "    1/8 < 3/8 ✓, 3/8 < 1/2 ✓, 1/2 < 5/6 ✓. "
            "🔍 모든 인접 쌍이 통과하면 전체 순서 정확. "
            "한 곳이라도 틀리면 그 부분을 다시 정렬."
        ),
        "cpa_stage": "abstract",
        "visual_type": "verify_order",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "실생활 정렬 — 결승선/물 채우기",
        "content": (
            "실생활 문제에서 정렬: "
            "  '같은 거리 4명 달리기 → 7/8, 5/6, 1/2, 3/8 완주' → "
            "    완주 적은 순 = 분수 작은 순 → 3/8 < 1/2 < 5/6 < 7/8. "
            "  '같은 크기 항아리 4개 채움' 등도 동일 원리. "
            "🔍 핵심 가정: '같은 전체' (같은 거리, 같은 항아리)."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "real_world_ordering",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Order from least to greatest: 1/8, 3/4, 1/2.",
        "choices": [
            "A. 1/8 < 1/2 < 3/4",
            "B. 1/2 < 1/8 < 3/4",
            "C. 3/4 < 1/2 < 1/8",
            "D. 1/8 < 3/4 < 1/2"
        ],
        "answer": "A",
        "explanation": "벤치마크 1/2: 1/8 < 1/2, 3/4 > 1/2.",
        "difficulty": 2,
        "hints": ["벤치마크 1/2."],
        "feedback": {"correct": "정답!", "incorrect": "1/8 < 1/2 < 3/4."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "Which list is in order from greatest to least?",
        "choices": [
            "A. 6/6, 4/6, 1/6",
            "B. 1/6, 4/6, 6/6",
            "C. 4/6, 1/6, 6/6",
            "D. 6/6, 1/6, 4/6"
        ],
        "answer": "A",
        "explanation": "같은 분모. 분자: 6, 4, 1.",
        "difficulty": 1,
        "hints": ["같은 분모, 분자 큰 순."],
        "feedback": {"correct": "정답!", "incorrect": "6/6 > 4/6 > 1/6."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Order from least to greatest: 3/3, 1/3, 2/3.",
        "choices": [
            "A. 1/3 < 2/3 < 3/3",
            "B. 3/3 < 2/3 < 1/3",
            "C. 2/3 < 1/3 < 3/3",
            "D. 1/3 < 3/3 < 2/3"
        ],
        "answer": "A",
        "explanation": "같은 분모. 분자: 1, 2, 3.",
        "difficulty": 1,
        "hints": ["분자 정렬."],
        "feedback": {"correct": "정답!", "incorrect": "1/3 < 2/3 < 3/3."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "Order from greatest to least: 1/2, 1/4, 1/6.",
        "choices": [
            "A. 1/2 > 1/4 > 1/6",
            "B. 1/6 > 1/4 > 1/2",
            "C. 1/4 > 1/2 > 1/6",
            "D. 1/2 > 1/6 > 1/4"
        ],
        "answer": "A",
        "explanation": "같은 분자. 분모 작을수록 큼.",
        "difficulty": 1,
        "hints": ["분모 작은 순."],
        "feedback": {"correct": "정답!", "incorrect": "1/2 > 1/4 > 1/6."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Order from least to greatest: 1/8, 5/6, 1/2.",
        "choices": [
            "A. 1/8 < 1/2 < 5/6",
            "B. 5/6 < 1/2 < 1/8",
            "C. 1/2 < 1/8 < 5/6",
            "D. 1/8 < 5/6 < 1/2"
        ],
        "answer": "A",
        "explanation": "벤치마크 1/2.",
        "difficulty": 2,
        "hints": ["1/2와 비교."],
        "feedback": {"correct": "정답!", "incorrect": "1/8 < 1/2 < 5/6."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Three jars are the same size. A=3/4 full, B=1/2 full, C=5/8 full. Order from least full.",
        "choices": [
            "A. B < C < A",
            "B. A < C < B",
            "C. C < A < B",
            "D. A < B < C"
        ],
        "answer": "A",
        "explanation": "1/2=4/8, 5/8, 3/4=6/8 → 4/8 < 5/8 < 6/8.",
        "difficulty": 3,
        "hints": ["8분의로 통일."],
        "feedback": {"correct": "정답!", "incorrect": "B(4/8) < C(5/8) < A(6/8)."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Which fraction belongs BETWEEN 2/6 and 5/6?",
        "choices": ["A. 1/6", "B. 4/6", "C. 6/6", "D. 7/6"],
        "answer": "B",
        "explanation": "2/6 < 4/6 < 5/6.",
        "difficulty": 2,
        "hints": ["분자 2~5 사이."],
        "feedback": {"correct": "정답! 4/6.", "incorrect": "분자 3 또는 4."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Order from greatest to least: 7/8, 1/3, 4/6.",
        "choices": [
            "A. 7/8 > 4/6 > 1/3",
            "B. 1/3 > 4/6 > 7/8",
            "C. 4/6 > 7/8 > 1/3",
            "D. 7/8 > 1/3 > 4/6"
        ],
        "answer": "A",
        "explanation": "벤치마크: 7/8 > 1/2, 4/6 > 1/2, 1/3 < 1/2. 7/8 ≈ 0.875, 4/6 ≈ 0.667.",
        "difficulty": 3,
        "hints": ["벤치마크 1/2 + 추가."],
        "feedback": {"correct": "정답!", "incorrect": "7/8 > 4/6 > 1/3."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Four runners (same distance). A: 7/8, B: 1/2, C: 5/6, D: 1/4. Order from least to greatest distance run.",
        "choices": [
            "A. D < B < C < A",
            "B. A < C < B < D",
            "C. D < B < A < C",
            "D. B < D < C < A"
        ],
        "answer": "A",
        "explanation": "1/4 < 1/2 < 5/6 < 7/8.",
        "difficulty": 3,
        "hints": ["벤치마크 1/2."],
        "feedback": {"correct": "정답!", "incorrect": "D(1/4) < B(1/2) < C(5/6) < A(7/8)."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Kai says: 'To order 1/3, 1/6, 1/8 from least to greatest, just look at denominators in order.' Why is that wrong?",
        "choices": [
            "A. 같은 분자에서는 분모 큰 순 = 작은 분수 순 → 1/8 < 1/6 < 1/3",
            "B. Kai의 방법이 맞음",
            "C. 분자도 비교해야 함",
            "D. 분수 정렬 불가능"
        ],
        "answer": "A",
        "explanation": "같은 분자라면 분모 큰 분수가 작음.",
        "difficulty": 3,
        "hints": ["분모 큰 = 분수 작은."],
        "feedback": {"correct": "정답!", "incorrect": "1/8 < 1/6 < 1/3."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 348 + 467.",
        "choices": ["A. 705", "B. 715", "C. 805", "D. 815"],
        "answer": "D",
        "explanation": "348+467: 8+7=15 (carry 1), 4+6+1=11 (carry 1), 3+4+1=8. Result: 815.",
        "difficulty": 2,
        "hints": ["Two carries.", "348+467=815."],
        "feedback": {"correct": "Right — 815.", "incorrect": "348+467=815."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 600 − 247.",
        "choices": ["A. 343", "B. 353", "C. 443", "D. 453"],
        "answer": "B",
        "explanation": "600−247=353 (borrow across both zeros).",
        "difficulty": 2,
        "hints": ["Borrow across zeros.", "600−247=353."],
        "feedback": {"correct": "Right — 353.", "incorrect": "600−247=353."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A box had 543 apples. They added 168, then sold 245. How many apples now?",
        "choices": ["A. 298", "B. 466", "C. 620", "D. 711"],
        "answer": "B",
        "explanation": "Step 1: 543+168=711. Step 2: 711−245=466.",
        "difficulty": 3,
        "hints": ["Add then subtract.", "543+168=711, 711−245=466."],
        "feedback": {"correct": "Right — 466 apples.", "incorrect": "543+168=711, then −245=466."},
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
        "prerequisite": "G3 U9 L4 — 일반 분수 비교 (3.NF.A.3d)",
        "current":      "G3 — 분수 정렬: 같은 분모/분자/벤치마크 통합 (3.NF.A.3d)",
        "successor":    "G3 U9 L6 — 모델로 동치 분수 (3.NF.A.3b)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
