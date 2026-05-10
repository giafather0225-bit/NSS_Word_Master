"""
G3 U9 L7 — Equivalent Fractions 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3b (동치 분수 — 곱하기/나누기 규칙)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/L7_equivalent_fractions.json"

ID_PREFIX_MAP = {
    "c9_l7_pre_": "PT_",
    "c9_l7_learn_": "LEARN_",
    "c9_l7_try_": "TRY_",
    "c9_l7_pr1_": "R1_",
    "c9_l7_pr2_": "R2_",
    "c9_l7_pr3_": "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.3.M03"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    **{f"TRY_0{i}": ["3.NF.A.3.M03"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.3.M03"] for i in range(1,11)},
    **{f"R2_0{i}": ["3.NF.A.3.M03"] for i in range(1,8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.3.M03"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "equivalent_fractions" for i in range(1,6)},
    "LEARN_01": "multiply_rule",
    "LEARN_02": "divide_rule",
    "LEARN_03": "verify_equivalent",
    "LEARN_04": "n_over_n_identity",
    "LEARN_05": "scaling_factor",
    "LEARN_06": "find_equivalent_routine",
    "LEARN_07": "simplify_routine",
    "LEARN_08": "common_pitfall_partial",
    **{f"TRY_0{i}": "equivalent_fractions" for i in range(1,6)},
    **{f"R1_{i:02d}": "equivalent_fractions" for i in range(1,11)},
    **{f"R2_0{i}": "equivalent_fractions" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "equivalent_fractions" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Lesson 9.7 'Equivalent Fractions' pp.377-380",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic G — Generating Equivalent Fractions",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


LEARN_TITLE_MAP = {
    "LEARN_01": "곱하기 규칙 — 같은 수로 ×",
    "LEARN_02": "나누기 규칙 — 같은 수로 ÷ (약분)",
    "LEARN_03": "동치 검증 — 비교 후 확인",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "동치 분수"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "equivalent_fractions"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "equivalent_rule",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "equivalent_fractions")
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
        "title": "n/n = 1 — 동치의 핵심",
        "content": (
            "곱셈/나눗셈 규칙의 원리: 어떤 수에 1을 곱해도 변하지 않음. "
            "  2/2 = 1, 3/3 = 1, 4/4 = 1, … "
            "  분수에 n/n 곱 = 1 곱 = 그대로 (다른 표기). "
            "예: 1/2 × 2/2 = 2/4 (값은 1/2 그대로). "
            "🔍 핵심: 같은 양인데 더 잘게 표현."
        ),
        "cpa_stage": "abstract",
        "visual_type": "n_over_n_identity",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "스케일 인자 찾기 — 분모 비율",
        "content": (
            "1/3 = ?/9를 풀려면: 분모가 3에서 9로 → ×3. "
            "분자도 같이 ×3 → 1×3 = 3. 답: 3/9. "
            "  단계: 분모 변화의 인자 찾기 → 분자에 같은 인자 곱하기. "
            "예: 2/4 = ?/8 → 분모 ×2 → 분자도 ×2 → 4/8."
        ),
        "cpa_stage": "abstract",
        "visual_type": "scaling_factor",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "동치 만들기 3단계 루틴",
        "content": (
            "주어진 분수의 동치 분수 만들기: "
            "  단계 1) 원하는 분모(또는 분자) 확인. "
            "  단계 2) 원본과 비교해 곱셈 인자 결정. "
            "  단계 3) 분자/분모에 같은 인자 곱하기. "
            "예: 1/2 = ?/8 → 분모 ×4 → 1×4/2×4 = 4/8."
        ),
        "cpa_stage": "abstract",
        "visual_type": "find_equivalent_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "약분 3단계 루틴",
        "content": (
            "분수를 더 간단히 (약분): "
            "  단계 1) 분자와 분모의 공약수 찾기. "
            "  단계 2) 공약수로 분자/분모 둘 다 나누기. "
            "  단계 3) 더 약분 안 되면 끝 (기약 분수). "
            "예: 6/8 → ÷2 → 3/4. 더 약분 안 됨 → 3/4가 가장 간단."
        ),
        "cpa_stage": "abstract",
        "visual_type": "simplify_routine",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "한쪽만 ×하면 다른 분수 — M03 함정",
        "content": (
            "흔한 실수 (M03): 분자만 또는 분모만 곱/나눔. "
            "  잘못: 1/2 = 2/2 (분자만 ×2 → 다른 분수, 값 1) "
            "  잘못: 1/2 = 1/4 (분모만 ×2 → 더 작은 분수) "
            "  맞음: 1/2 = 2/4 (둘 다 ×2). "
            "🔍 검산: 두 분수가 같은 모델/수직선 점에 매핑되는가?"
        ),
        "cpa_stage": "abstract",
        "visual_type": "common_pitfall",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "fill_in",
        "question": "Complete: 2/3 = __/9",
        "answer": "6",
        "explanation": "분모 3 → 9 (×3). 분자 2×3 = 6.",
        "difficulty": 2,
        "hints": ["분모 ×3."],
        "feedback": {"correct": "정답! 6.", "incorrect": "2×3=6."},
    },
    {
        "id": "TRY_05",
        "type": "fill_in",
        "question": "Simplify: 4/8 = __/__",
        "answer": "1/2",
        "accept": ["1/2"],
        "explanation": "÷4 → 1/2.",
        "difficulty": 2,
        "hints": ["분자/분모 ÷ 공약수."],
        "feedback": {"correct": "정답!", "incorrect": "4/8 ÷ 4/4 = 1/2."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "fill_in",
        "question": "Complete: 1/3 = __/9",
        "answer": "3",
        "explanation": "1×3/3×3 = 3/9.",
        "difficulty": 1,
        "hints": ["×3."],
        "feedback": {"correct": "정답! 3.", "incorrect": "1×3=3."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "Simplify: 6/8 = __/__",
        "answer": "3/4",
        "accept": ["3/4"],
        "explanation": "÷2 → 3/4.",
        "difficulty": 2,
        "hints": ["÷2."],
        "feedback": {"correct": "정답!", "incorrect": "6/8 ÷ 2/2 = 3/4."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Which fraction is equivalent to 1/2?",
        "choices": ["A. 2/3", "B. 3/6", "C. 4/6", "D. 1/4"],
        "answer": "B",
        "explanation": "1×3/2×3 = 3/6.",
        "difficulty": 1,
        "hints": ["1/2 × 3/3."],
        "feedback": {"correct": "정답! 3/6.", "incorrect": "1/2 = 3/6."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "fill_in",
        "question": "Complete: 4/4 = __/8",
        "answer": "8",
        "explanation": "4×2/4×2 = 8/8.",
        "difficulty": 2,
        "hints": ["×2."],
        "feedback": {"correct": "정답! 8.", "incorrect": "4×2=8 → 8/8."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Which pair is NOT equivalent?",
        "choices": ["A. 1/2 = 4/8", "B. 2/3 = 4/6", "C. 3/4 = 9/12", "D. 1/4 = 3/8"],
        "answer": "D",
        "explanation": "1/4 = 2/8, 아니라 3/8.",
        "difficulty": 3,
        "hints": ["분자/분모 같은 인자?"],
        "feedback": {"correct": "정답!", "incorrect": "1/4 = 2/8, not 3/8."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Sara ate 4/6 of her granola bar. Tim ate 2/3 of his (same size). Did they eat the same amount?",
        "choices": [
            "A. 예 (4/6 = 2/3 — 동치)",
            "B. 아니오 (Sara가 더)",
            "C. 아니오 (Tim이 더)",
            "D. 비교 불가"
        ],
        "answer": "A",
        "explanation": "4÷2/6÷2 = 2/3 → 동치.",
        "difficulty": 3,
        "hints": ["약분 가능?"],
        "feedback": {"correct": "정답! 같음.", "incorrect": "4/6 = 2/3."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Ben says 2/4 = 3/6 = 4/8. Is he correct?",
        "choices": [
            "A. 예 — 모두 1/2와 동치 (각각 ×2, ×3, ×4)",
            "B. 아니오 — 분자가 다름",
            "C. 아니오 — 분모가 다름",
            "D. 부분 정답"
        ],
        "answer": "A",
        "explanation": "1/2 → 2/4 (×2), 3/6 (×3), 4/8 (×4). 모두 1/2 동치.",
        "difficulty": 3,
        "hints": ["각각 1/2의 배수형."],
        "feedback": {"correct": "정답!", "incorrect": "모두 1/2와 동치."},
    },
    {
        "id": "R3_05",
        "type": "fill_in",
        "question": "Write TWO fractions equivalent to 2/3 (other than 2/3 itself).",
        "answer": "4/6, 6/9",
        "accept": ["4/6, 6/9", "4/6 and 6/9", "4/6, 8/12", "6/9, 8/12"],
        "explanation": "2/3 × 2/2 = 4/6, × 3/3 = 6/9, × 4/4 = 8/12.",
        "difficulty": 3,
        "hints": ["×2/2, ×3/3 …"],
        "feedback": {"correct": "정답!", "incorrect": "2/3 × n/n 형태."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 459 + 367.",
        "choices": ["A. 716", "B. 726", "C. 816", "D. 826"],
        "answer": "D",
        "explanation": "459+367: 9+7=16 (carry 1), 5+6+1=12 (carry 1), 4+3+1=8. Result: 826.",
        "difficulty": 2,
        "hints": ["Two carries.", "459+367=826."],
        "feedback": {"correct": "Right — 826.", "incorrect": "459+367=826."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 802 − 437.",
        "choices": ["A. 365", "B. 375", "C. 465", "D. 475"],
        "answer": "A",
        "explanation": "802−437=365 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "802−437=365."],
        "feedback": {"correct": "Right — 365.", "incorrect": "802−437=365."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 627 books. They received 184, then loaned 156. How many books now?",
        "choices": ["A. 287", "B. 471", "C. 655", "D. 811"],
        "answer": "C",
        "explanation": "Step 1: 627+184=811. Step 2: 811−156=655.",
        "difficulty": 3,
        "hints": ["Add then subtract.", "627+184=811, 811−156=655."],
        "feedback": {"correct": "Right — 655 books.", "incorrect": "627+184=811, then −156=655."},
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
        "prerequisite": "G3 U9 L6 — 모델로 동치 분수 (3.NF.A.3a/b)",
        "current":      "G3 — 동치 분수: 곱하기/나누기 규칙 (3.NF.A.3b)",
        "successor":    "G3 U10 L1 — 둘레 시작 (3.MD.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_l7.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
