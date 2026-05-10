"""
G3 U9 L6 — Model Equivalent Fractions 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3a/b (모델로 동치 분수 — 같은 양 다른 분수)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/L6_model_equivalent_fractions.json"

ID_PREFIX_MAP = {
    "c9_l6_pre_": "PT_",
    "c9_l6_learn_": "LEARN_",
    "c9_l6_try_": "TRY_",
    "c9_l6_pr1_": "R1_",
    "c9_l6_pr2_": "R2_",
    "c9_l6_pr3_": "R3_",
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
    **{f"PT_0{i}": "model_equivalent_fractions" for i in range(1,6)},
    "LEARN_01": "fraction_strip_equivalence",
    "LEARN_02": "area_model_equivalence",
    "LEARN_03": "number_line_equivalence",
    "LEARN_04": "equivalent_definition",
    "LEARN_05": "doubling_pattern",
    "LEARN_06": "find_equivalent_routine",
    "LEARN_07": "verify_equivalence",
    "LEARN_08": "common_pitfall_size_change",
    **{f"TRY_0{i}": "model_equivalent_fractions" for i in range(1,6)},
    **{f"R1_{i:02d}": "model_equivalent_fractions" for i in range(1,11)},
    **{f"R2_0{i}": "model_equivalent_fractions" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "model_equivalent_fractions" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "pictorial", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,6)},
    **{f"R1_{i:02d}": "pictorial" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Lesson 9.6 'Model Equivalent Fractions' pp.373-376",
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
    "LEARN_01": "분수 스트립 — 같은 길이 다른 이름",
    "LEARN_02": "면적 모델 — 같은 색칠 면적",
    "LEARN_03": "수직선 — 같은 점, 다른 분수",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "동치 분수 모델"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "pictorial"),
        "skill_tag": SKILL_TAGS.get(new_id, "model_equivalent_fractions"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "equivalence_model",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "model_equivalent_fractions")
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
        "title": "동치 분수 정의 — 같은 양",
        "content": (
            "동치 분수란: 다르게 적었지만 같은 양을 나타내는 분수. "
            "  1/2 = 2/4 = 4/8 (같은 양, 다른 표기). "
            "  2/3 = 4/6 = 6/9. "
            "🔍 핵심: 그림/수직선/막대에서 같은 자리를 차지함. "
            "다르게 보여도 가치는 같음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "equivalent_definition",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "두 배 패턴 — 분자/분모 같은 수만큼 곱",
        "content": (
            "분수의 분자와 분모에 같은 수를 곱하면 동치 분수. "
            "  1/2 → ×2 → 2/4 → ×2 → 4/8 (모두 동치) "
            "  2/3 → ×2 → 4/6 → ×2 → 8/12 "
            "🔍 직관: 같은 케이크를 더 잘게 나누면 조각 수와 분자도 같이 늘어남. "
            "(분자만 곱하거나 분모만 곱하면 다른 분수.)"
        ),
        "cpa_stage": "abstract",
        "visual_type": "doubling_pattern",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "동치 찾기 3단계 루틴",
        "content": (
            "주어진 분수의 동치 분수 찾기: "
            "  단계 1) 모델 그리기 (스트립/원/수직선). "
            "  단계 2) 같은 양을 다른 칸 수로 표현. "
            "  단계 3) 새 분자/분모 읽기. "
            "예: 1/2 → 2등분 한 쪽 색칠 → 4등분 다시 그려도 같은 면적 → 2/4."
        ),
        "cpa_stage": "abstract",
        "visual_type": "find_equivalent",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "검산 — 그림 겹쳐 보기",
        "content": (
            "두 분수가 동치인지 검산: 같은 크기 모델에 각각 색칠해 겹쳐 봄. "
            "  같은 면적/길이 → 동치. "
            "  다른 면적 → 동치 아님. "
            "예: 1/2와 2/4 같은 길이 막대에 색칠 → 둘 다 절반 색칠 → 동치 ✓. "
            "🔍 디지털: 수직선의 같은 점을 가리키면 동치."
        ),
        "cpa_stage": "abstract",
        "visual_type": "verify_overlap",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "흔한 실수 — 분자만/분모만 변경",
        "content": (
            "흔한 실수 (M03): 분자나 분모 한 쪽만 바꿔서 동치라고 함. "
            "  예: 1/2 = 2/2? ❌ (분자만 ×2 — 다른 분수가 됨). "
            "  예: 1/2 = 1/4? ❌ (분모만 ×2 — 더 작은 분수). "
            "올바름: 분자와 분모 모두 같은 수만큼 곱. 1/2 = 2/4. "
            "🔍 검산: 곱한 후에도 비율이 같은가?"
        ),
        "cpa_stage": "abstract",
        "visual_type": "common_pitfall",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Which fraction is equivalent to 2/3?",
        "choices": ["A. 4/6", "B. 2/6", "C. 4/3", "D. 1/3"],
        "answer": "A",
        "explanation": "2×2/3×2 = 4/6.",
        "difficulty": 1,
        "hints": ["분자/분모 모두 ×2."],
        "feedback": {"correct": "정답! 4/6.", "incorrect": "2/3 = 4/6."},
    },
    {
        "id": "TRY_05",
        "type": "fill_in",
        "question": "Complete: 3/4 = __/8",
        "answer": "6",
        "explanation": "3×2/4×2 = 6/8.",
        "difficulty": 1,
        "hints": ["분자/분모 ×2."],
        "feedback": {"correct": "정답! 6.", "incorrect": "3×2=6."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Which fraction is equivalent to 1/3?",
        "choices": ["A. 2/6", "B. 1/6", "C. 3/3", "D. 2/3"],
        "answer": "A",
        "explanation": "1×2/3×2 = 2/6.",
        "difficulty": 1,
        "hints": ["분자/분모 ×2."],
        "feedback": {"correct": "정답!", "incorrect": "1/3 = 2/6."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "Complete: 2/4 = __/8",
        "answer": "4",
        "explanation": "2×2/4×2 = 4/8.",
        "difficulty": 1,
        "hints": ["×2."],
        "feedback": {"correct": "정답! 4.", "incorrect": "2×2=4."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Two same-size rectangles. A: 1/2 shaded. B: 4/8 shaded. Are they equivalent?",
        "choices": ["A. 예 (1/2 = 4/8)", "B. 아니오 (분모 다름)", "C. 모르겠음", "D. A가 더 큼"],
        "answer": "A",
        "explanation": "1×4/2×4 = 4/8.",
        "difficulty": 2,
        "hints": ["같은 면적인지 확인."],
        "feedback": {"correct": "정답!", "incorrect": "1/2 = 4/8."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "fill_in",
        "question": "Complete: 1/2 = __/6",
        "answer": "3",
        "explanation": "1×3/2×3 = 3/6.",
        "difficulty": 2,
        "hints": ["×3."],
        "feedback": {"correct": "정답! 3.", "incorrect": "1×3=3."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Which pair shows EQUIVALENT fractions?",
        "choices": ["A. 1/2 = 1/4", "B. 2/3 = 4/6", "C. 3/4 = 3/8", "D. 2/4 = 4/4"],
        "answer": "B",
        "explanation": "2×2/3×2 = 4/6.",
        "difficulty": 2,
        "hints": ["분자/분모 같은 수 ×."],
        "feedback": {"correct": "정답!", "incorrect": "2/3 × 2/2 = 4/6."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Emma says 2/8 = 1/4. Is she right?",
        "choices": [
            "A. 예 (2÷2=1, 8÷2=4 → 약분)",
            "B. 아니오 — 분자가 다름",
            "C. 아니오 — 분모가 다름",
            "D. 모르겠음"
        ],
        "answer": "A",
        "explanation": "2/8 ÷ 2/2 = 1/4 (약분).",
        "difficulty": 3,
        "hints": ["같은 수로 나누기 = 동치."],
        "feedback": {"correct": "정답!", "incorrect": "2÷2=1, 8÷2=4 → 1/4 동치."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Name a fraction with denominator 8 that is equivalent to 1/2.",
        "choices": ["A. 1/8", "B. 2/8", "C. 4/8", "D. 8/8"],
        "answer": "C",
        "explanation": "1×4/2×4 = 4/8.",
        "difficulty": 2,
        "hints": ["분모 2 → 8 (×4)."],
        "feedback": {"correct": "정답! 4/8.", "incorrect": "1/2 = 4/8."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Nate says 2/4 = 2/8 because they have the same numerator. Why is he wrong?",
        "choices": [
            "A. 동치는 분자/분모 모두 같은 수로 곱/나눔. 2/4의 분모만 ×2 했으니 다른 분수.",
            "B. 분자만 같으면 충분",
            "C. 2/4 = 2/8이 맞음",
            "D. 분수는 비교 불가"
        ],
        "answer": "A",
        "explanation": "2/4 = 1/2, 2/8 = 1/4. 다름.",
        "difficulty": 3,
        "hints": ["분자만 비교 ≠ 동치."],
        "feedback": {"correct": "정답!", "incorrect": "분자/분모 둘 다 같은 수로 변환해야."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 287 + 354.",
        "choices": ["A. 531", "B. 541", "C. 631", "D. 641"],
        "answer": "D",
        "explanation": "287+354: 7+4=11 (carry 1), 8+5+1=14 (carry 1), 2+3+1=6. Result: 641.",
        "difficulty": 2,
        "hints": ["Two carries.", "287+354=641."],
        "feedback": {"correct": "Right — 641.", "incorrect": "287+354=641."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 705 − 268.",
        "choices": ["A. 437", "B. 447", "C. 537", "D. 547"],
        "answer": "A",
        "explanation": "705−268=437 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "705−268=437."],
        "feedback": {"correct": "Right — 437.", "incorrect": "705−268=437."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A theater had 538 tickets. They sold 167, then printed 245 more. How many tickets now?",
        "choices": ["A. 371", "B. 460", "C. 616", "D. 783"],
        "answer": "C",
        "explanation": "Step 1: 538−167=371. Step 2: 371+245=616.",
        "difficulty": 3,
        "hints": ["Subtract sold, add printed.", "538−167=371, 371+245=616."],
        "feedback": {"correct": "Right — 616 tickets.", "incorrect": "538−167=371, then +245=616."},
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
        "prerequisite": "G3 U9 L5 — 분수 정렬 (3.NF.A.3d)",
        "current":      "G3 — 모델로 동치 분수: 같은 양 다른 분수 (3.NF.A.3a/b)",
        "successor":    "G3 U9 L7 — 동치 분수 (수치 변환) (3.NF.A.3b)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_l6.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
