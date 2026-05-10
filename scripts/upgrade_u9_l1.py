"""
G3 U9 L1 — Problem Solving: Compare Fractions 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3d (분수 비교 문장제 — 같은 전체 가정)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/L1_problem_solving_compare_fractions.json"

ID_PREFIX_MAP = {
    "c9_l1_pre_": "PT_",
    "c9_l1_learn_": "LEARN_",
    "c9_l1_try_": "TRY_",
    "c9_l1_pr1_": "R1_",
    "c9_l1_pr2_": "R2_",
    "c9_l1_pr3_": "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.3.M01"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    **{f"TRY_0{i}": ["3.NF.A.3.M02"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.3.M01"] for i in range(1,11)},
    **{f"R2_0{i}": ["3.NF.A.3.M02"] for i in range(1,8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.3.M02"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "compare_fractions" for i in range(1,6)},
    "LEARN_01": "same_denominator_compare",
    "LEARN_02": "same_numerator_compare",
    "LEARN_03": "same_whole_assumption",
    "LEARN_04": "compare_strategy_decision",
    "LEARN_05": "benchmark_half",
    "LEARN_06": "compare_routine",
    "LEARN_07": "common_misconception_check",
    "LEARN_08": "word_problem_compare",
    **{f"TRY_0{i}": "compare_fractions" for i in range(1,6)},
    **{f"R1_{i:02d}": "compare_fractions" for i in range(1,11)},
    **{f"R2_0{i}": "compare_fractions" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "compare_fractions" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "pictorial",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Lesson 9.1 'Problem Solving: Compare Fractions' pp.353-356",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic F — Comparison, Order, and Size of Fractions",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    """instruction_check → concept_card"""
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    title_map = {
        "LEARN_01": "같은 분모 비교 — 분자가 큰 쪽이 큼",
        "LEARN_02": "같은 분자 비교 — 분모가 작은 쪽이 큼",
        "LEARN_03": "같은 전체 가정 — 비교의 전제",
    }
    return {
        "id": new_id,
        "type": "concept_card",
        "title": title_map.get(new_id, "분수 비교"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "compare_fractions"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "compare_strategy",
    }


TYPE_MAP = {
    "multiple_choice": "MC",
    "compare": "MC",
    "word_problem": "MC",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "compare_fractions")
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
        "title": "전략 선택 — 분모/분자 무엇이 같나?",
        "content": (
            "두 분수를 비교할 때 먼저 확인: "
            "  · 분모가 같다 → 분자가 큰 쪽이 큰 분수 (3/8 < 5/8). "
            "  · 분자가 같다 → 분모가 작은 쪽이 큰 분수 (3/4 > 3/6). "
            "  · 둘 다 다르다 → 1/2 같은 기준 분수와 비교 (벤치마크). "
            "🔍 1단계: 같은 부분 찾기. 2단계: 규칙 적용."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_decision",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "벤치마크 1/2 — 빠른 비교 도구",
        "content": (
            "1/2와 비교해 어느 쪽이 더 큰지 빠르게 알 수 있음. "
            "  분자 × 2 < 분모 → 1/2보다 작음 (예: 3/8: 3×2=6 < 8 → < 1/2). "
            "  분자 × 2 > 분모 → 1/2보다 큼 (예: 5/8: 5×2=10 > 8 → > 1/2). "
            "  분자 × 2 = 분모 → 정확히 1/2 (예: 3/6). "
            "예: 3/8과 5/6 비교 → 3/8 < 1/2 < 5/6 → 5/6이 큼."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "benchmark_half",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "분수 비교 3단계 루틴",
        "content": (
            "두 분수 비교 3단계: "
            "  단계 1) 같은 전체인지 확인 (같은 피자, 같은 막대). "
            "  단계 2) 분모/분자 중 같은 부분 찾기 → 규칙 선택. "
            "  단계 3) 규칙 적용해 부등호 결정. "
            "예: 2/6 vs 4/6 → 1) 같은 피자 ✓, 2) 같은 분모, 3) 4>2이므로 2/6 < 4/6."
        ),
        "cpa_stage": "abstract",
        "visual_type": "compare_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "분모 클수록 크다? — 자주 하는 실수",
        "content": (
            "흔한 실수 (M02): 분모가 큰 쪽이 더 크다고 착각. "
            "예: 1/8 vs 1/3 → '8 > 3이니까 1/8이 더 큼'? ❌ "
            "사실: 분모가 클수록 한 조각은 더 작음. 1/8 < 1/3. "
            "🔍 직관: 케이크 8조각 < 케이크 3조각 (한 조각의 크기). "
            "교정: 분자가 같으면 분모 작은 쪽이 큼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "common_mistake",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "문장제에서 비교 단계",
        "content": (
            "문장제에서 분수 비교 단계: "
            "  단계 1) 같은 전체인지 확인 (같은 길이 막대, 같은 크기 피자). "
            "  단계 2) 두 분수 추출. "
            "  단계 3) 비교 → 누가/어느 쪽이 더 많이/적게? "
            "예: 'Tom 3/8 피자, Sara 5/8 피자. 누가 더?' → 3/8 < 5/8 → Sara. "
            "흔한 실수: 다른 크기 비교 — '같은 전체' 조건을 놓침."
        ),
        "cpa_stage": "abstract",
        "visual_type": "word_problem_compare",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Compare: 1/3 ○ 1/5",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "분자 같음 → 분모 작은 쪽이 큼. 1/3 > 1/5.",
        "difficulty": 2,
        "hints": ["같은 분자 → 분모 작은 쪽이 큼."],
        "feedback": {"correct": "정답!", "incorrect": "1/3 > 1/5."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "Anna ate 4/6 of an apple. Ben ate 5/6 of an identical apple. Who ate more?",
        "choices": ["A. Anna", "B. Ben", "C. 같음", "D. 비교 불가"],
        "answer": "B",
        "explanation": "같은 분모 6. 5 > 4 → Ben이 더 많이.",
        "difficulty": 1,
        "hints": ["같은 분모 → 분자 큰 쪽."],
        "feedback": {"correct": "정답! Ben.", "incorrect": "5/6 > 4/6 → Ben."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Compare: 2/3 ○ 2/8",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "분자 같음. 분모 3 < 8 → 2/3가 큼.",
        "difficulty": 1,
        "hints": ["같은 분자."],
        "feedback": {"correct": "정답!", "incorrect": "2/3 > 2/8."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "Which is greater: 3/8 or 5/8?",
        "choices": ["A. 3/8", "B. 5/8", "C. 같음", "D. 비교 불가"],
        "answer": "B",
        "explanation": "같은 분모. 5 > 3.",
        "difficulty": 1,
        "hints": ["같은 분모 → 분자."],
        "feedback": {"correct": "정답! 5/8.", "incorrect": "5/8 > 3/8."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Compare: 1/2 ○ 1/4",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "같은 분자 1. 분모 2 < 4 → 1/2 > 1/4.",
        "difficulty": 1,
        "hints": ["같은 분자, 분모 작은 쪽 큼."],
        "feedback": {"correct": "정답!", "incorrect": "1/2 > 1/4."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Compare 5/8 to 1/2 using benchmark.",
        "choices": ["A. 5/8 < 1/2", "B. 5/8 > 1/2", "C. 5/8 = 1/2", "D. 비교 불가"],
        "answer": "B",
        "explanation": "5×2=10 > 8 → 5/8 > 1/2.",
        "difficulty": 2,
        "hints": ["분자×2 vs 분모."],
        "feedback": {"correct": "정답!", "incorrect": "5×2=10 > 8 → > 1/2."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Two pizzas are different sizes. Tom ate 3/4 of a small pizza. Lily ate 2/4 of a large pizza. Can we say Tom ate more?",
        "choices": [
            "A. 예 (3/4 > 2/4)",
            "B. 아니오 — 같은 전체가 아니므로 비교 불가",
            "C. 예 (분수가 크면 양도 큼)",
            "D. 같음"
        ],
        "answer": "B",
        "explanation": "분수 비교는 같은 전체 가정. 다른 크기 피자는 비교 불가.",
        "difficulty": 3,
        "hints": ["같은 전체인가?"],
        "feedback": {"correct": "정답!", "incorrect": "다른 크기 → 분수만으론 비교 불가."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Order from smallest: 1/3, 1/8, 1/2.",
        "choices": [
            "A. 1/2 < 1/3 < 1/8",
            "B. 1/8 < 1/3 < 1/2",
            "C. 1/3 < 1/8 < 1/2",
            "D. 1/8 < 1/2 < 1/3"
        ],
        "answer": "B",
        "explanation": "같은 분자. 분모 큰 → 작은 분수. 1/8 < 1/3 < 1/2.",
        "difficulty": 2,
        "hints": ["분모 큰 순 = 분수 작은 순."],
        "feedback": {"correct": "정답!", "incorrect": "1/8 < 1/3 < 1/2."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Two friends share IDENTICAL bottles of juice. Mia drinks 2/3, Ana drinks 3/4. Who drinks more?",
        "choices": ["A. Mia", "B. Ana", "C. 같음", "D. 비교 불가"],
        "answer": "B",
        "explanation": "벤치마크 1/2: 2/3 > 1/2, 3/4 > 1/2. 더 정확히: 2/3 ≈ 0.67, 3/4 = 0.75. Ana가 더.",
        "difficulty": 3,
        "hints": ["벤치마크 1/2 또는 공통 분모."],
        "feedback": {"correct": "정답! Ana.", "incorrect": "3/4 > 2/3 → Ana."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Without drawing, explain: is 5/6 closer to 0 or to 1?",
        "choices": [
            "A. 0에 가깝다 (분자가 작음)",
            "B. 1에 가깝다 (5/6 = 6/6 − 1/6, 1에서 1/6만 떨어짐)",
            "C. 정확히 중간",
            "D. 알 수 없음"
        ],
        "answer": "B",
        "explanation": "5/6은 1에서 1/6만 떨어짐 → 1에 가까움.",
        "difficulty": 3,
        "hints": ["1 − 5/6 = ?"],
        "feedback": {"correct": "정답! 1에 가까움.", "incorrect": "5/6은 1에서 1/6만 떨어짐."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 528 + 374.",
        "choices": ["A. 792", "B. 802", "C. 892", "D. 902"],
        "answer": "D",
        "explanation": "528+374: 8+4=12 (carry 1), 2+7+1=10 (carry 1), 5+3+1=9. Result: 902.",
        "difficulty": 2,
        "hints": ["Two carries.", "528+374=902."],
        "feedback": {"correct": "Right — 902.", "incorrect": "528+374=902."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 600 − 358.",
        "choices": ["A. 242", "B. 252", "C. 342", "D. 358"],
        "answer": "A",
        "explanation": "600−358=242 (borrow across both zeros).",
        "difficulty": 2,
        "hints": ["Borrow across zeros.", "600−358=242."],
        "feedback": {"correct": "Right — 242.", "incorrect": "600−358=242."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A garden had 437 tulips. They planted 268 more, then sold 175. How many tulips now?",
        "choices": ["A. 392", "B. 530", "C. 612", "D. 705"],
        "answer": "B",
        "explanation": "Step 1: 437+268=705. Step 2: 705−175=530.",
        "difficulty": 3,
        "hints": ["Add then subtract.", "437+268=705, 705−175=530."],
        "feedback": {"correct": "Right — 530 tulips.", "incorrect": "437+268=705, then −175=530."},
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
        "prerequisite": "G3 U8 L9 — 부분으로 전체 그룹 찾기 (3.NF.A.1)",
        "current":      "G3 — 분수 비교 문장제: 같은 전체 가정 + 전략 선택 (3.NF.A.3d)",
        "successor":    "G3 U9 L2 — 같은 분모 분수 비교 (3.NF.A.3d)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
