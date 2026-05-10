"""
G3 U9 L4 — Compare Fractions (일반 비교) 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3d (서로 다른 분모/분자 — 벤치마크 1/2, 1 활용)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/L4_compare_fractions.json"

ID_PREFIX_MAP = {
    "c9_l4_pre_": "PT_",
    "c9_l4_learn_": "LEARN_",
    "c9_l4_try_": "TRY_",
    "c9_l4_pr1_": "R1_",
    "c9_l4_pr2_": "R2_",
    "c9_l4_pr3_": "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.3.M02"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    **{f"TRY_0{i}": ["3.NF.A.3.M02"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.3.M02"] for i in range(1,11)},
    **{f"R2_0{i}": ["3.NF.A.3.M02"] for i in range(1,8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.3.M02"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "compare_fractions_general" for i in range(1,6)},
    "LEARN_01": "benchmark_half",
    "LEARN_02": "benchmark_half_check",
    "LEARN_03": "strategy_selection",
    "LEARN_04": "benchmark_one",
    "LEARN_05": "missing_pieces_strategy",
    "LEARN_06": "compare_routine_general",
    "LEARN_07": "decision_tree",
    "LEARN_08": "real_world_compare",
    **{f"TRY_0{i}": "compare_fractions_general" for i in range(1,6)},
    **{f"R1_{i:02d}": "compare_fractions_general" for i in range(1,11)},
    **{f"R2_0{i}": "compare_fractions_general" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "compare_fractions_general" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "pictorial",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "pictorial",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Lesson 9.4 'Compare Fractions' pp.365-368",
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
    "LEARN_01": "벤치마크 1/2 — 빠른 비교",
    "LEARN_02": "1/2와의 거리 판정",
    "LEARN_03": "전략 선택 — 어떤 방법?",
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
        "skill_tag": SKILL_TAGS.get(new_id, "compare_fractions_general"),
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "compare_fractions_general")
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
        "title": "벤치마크 1 — 1에 가까운 쪽이 큼",
        "content": (
            "1과의 거리로 비교: 1에 가까운 쪽이 큰 분수. "
            "  거리: 1 − 분수 = (b − a)/b. "
            "  예: 5/6 vs 7/8 → 1−5/6=1/6, 1−7/8=1/8 → 1/8이 작음 → 7/8이 1에 더 가까움 → 7/8 > 5/6. "
            "🔍 같은 분자에 가까운 분자 분수 비교에 효과적."
        ),
        "cpa_stage": "abstract",
        "visual_type": "benchmark_one",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "남은 조각 전략 — 1까지 얼마?",
        "content": (
            "분수가 1에 얼마나 가까운지: '남은 조각'으로 판단. "
            "  3/4 → 1/4 남음. "
            "  5/8 → 3/8 남음. "
            "남은 조각이 작은 쪽이 1에 가까움. "
            "예: 3/4 (남은 1/4) vs 5/8 (남은 3/8) → 1/4 < 3/8 → 3/4 더 가까움 → 3/4 > 5/8."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "missing_pieces",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "일반 비교 3단계 루틴",
        "content": (
            "어떤 분수든 비교 3단계: "
            "  단계 1) 같은 전체인지 확인. "
            "  단계 2) 같은 분모/분자가 있나? → 직접 규칙. "
            "  단계 3) 둘 다 다르면 → 벤치마크 (1/2 또는 1) 사용. "
            "예: 1/8 vs 5/6 → 1) 같은 전체 ✓, 2) 모두 다름, 3) 1/8 < 1/2 < 5/6 → 1/8 < 5/6."
        ),
        "cpa_stage": "abstract",
        "visual_type": "compare_routine_general",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "결정 트리 — 빠른 길 선택",
        "content": (
            "분수 비교 결정 트리: "
            "  Q1) 분모 같음? → 분자 큰 쪽 (L2 규칙). "
            "  Q2) 분자 같음? → 분모 작은 쪽 (L3 규칙). "
            "  Q3) 둘 다 다름? → 벤치마크 1/2 (한쪽 < 1/2 < 다른쪽). "
            "  Q4) 둘 다 1/2의 같은 쪽? → 1까지 거리 비교. "
            "예: 2/3 vs 5/6 → 모두 > 1/2 → 1까지: 1/3 vs 1/6 → 1/6 작음 → 5/6 더 큼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "decision_tree",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "실생활 — 같은 크기 가정",
        "content": (
            "분수 비교는 항상 '같은 전체' 가정 위에서. "
            "  같은 크기 피자, 같은 길이 막대, 같은 양 물. "
            "  다른 크기 → 분수만으로 비교 불가. "
            "예: 큰 피자 1/4 vs 작은 피자 1/2 → 분수만 비교하면 1/2 > 1/4지만, "
            "실제 양은 큰 피자 1/4가 더 많을 수 있음. "
            "🔍 문제 풀 때 항상 '같은 ___' 표현 확인."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "real_world",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Compare: 3/8 ○ 4/6",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": "<",
        "explanation": "3/8 < 1/2 (3×2=6 < 8). 4/6 > 1/2 (4×2=8 > 6). 따라서 3/8 < 4/6.",
        "difficulty": 2,
        "hints": ["벤치마크 1/2 사용."],
        "feedback": {"correct": "정답!", "incorrect": "3/8 < 1/2 < 4/6."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "Which fraction is closer to 1: 5/6 or 3/4?",
        "choices": ["A. 5/6", "B. 3/4", "C. 같음", "D. 비교 불가"],
        "answer": "A",
        "explanation": "1−5/6=1/6, 1−3/4=1/4. 1/6 < 1/4 → 5/6이 1에 더 가까움.",
        "difficulty": 3,
        "hints": ["1까지 남은 조각 비교."],
        "feedback": {"correct": "정답! 5/6.", "incorrect": "남은 1/6 < 1/4 → 5/6."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Compare: 2/8 ○ 4/6",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": "<",
        "explanation": "2/8 < 1/2 < 4/6.",
        "difficulty": 2,
        "hints": ["벤치마크 1/2."],
        "feedback": {"correct": "정답!", "incorrect": "2/8 < 4/6."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "Compare: 5/6 ○ 1/4",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "5/6 > 1/2 > 1/4.",
        "difficulty": 1,
        "hints": ["벤치마크 1/2."],
        "feedback": {"correct": "정답!", "incorrect": "5/6 > 1/4."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Which fraction is greater than 1/2?",
        "choices": ["A. 2/6", "B. 3/8", "C. 5/8", "D. 1/4"],
        "answer": "C",
        "explanation": "5×2=10 > 8 → 5/8 > 1/2. 다른 것들은 모두 < 1/2.",
        "difficulty": 2,
        "hints": ["분자×2 > 분모?"],
        "feedback": {"correct": "정답! 5/8.", "incorrect": "5/8 > 1/2."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Compare 2/3 and 5/6. Both are > 1/2. Which is greater?",
        "choices": ["A. 2/3", "B. 5/6", "C. 같음", "D. 비교 불가"],
        "answer": "B",
        "explanation": "1까지 거리: 2/3 → 1/3, 5/6 → 1/6. 1/6 작음 → 5/6 더 큼.",
        "difficulty": 3,
        "hints": ["1까지 남은 거리."],
        "feedback": {"correct": "정답! 5/6.", "incorrect": "1−5/6=1/6 < 1−2/3=1/3 → 5/6 큼."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Order from smallest to largest: 1/4, 7/8, 3/6.",
        "choices": [
            "A. 1/4 < 3/6 < 7/8",
            "B. 7/8 < 3/6 < 1/4",
            "C. 3/6 < 1/4 < 7/8",
            "D. 1/4 < 7/8 < 3/6"
        ],
        "answer": "A",
        "explanation": "1/4 < 1/2 = 3/6 < 7/8.",
        "difficulty": 2,
        "hints": ["벤치마크 1/2."],
        "feedback": {"correct": "정답!", "incorrect": "1/4 < 3/6 (=1/2) < 7/8."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Write a fraction that is greater than 1/2 but less than 3/4.",
        "choices": ["A. 1/4", "B. 5/8", "C. 3/8", "D. 7/8"],
        "answer": "B",
        "explanation": "5/8 > 1/2 (5×2=10>8) and 5/8 < 3/4 (= 6/8).",
        "difficulty": 3,
        "hints": ["1/2 < ? < 3/4."],
        "feedback": {"correct": "정답! 5/8.", "incorrect": "5/8: > 1/2, < 6/8=3/4."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Three runners. Ava ran 3/4, Ben ran 5/8, Cora ran 2/3. Order finish from least to greatest distance (same track).",
        "choices": [
            "A. Ben < Cora < Ava",
            "B. Cora < Ben < Ava",
            "C. Ava < Ben < Cora",
            "D. Ben < Ava < Cora"
        ],
        "answer": "A",
        "explanation": "5/8=0.625, 2/3≈0.667, 3/4=0.75. → Ben < Cora < Ava.",
        "difficulty": 3,
        "hints": ["1까지 거리: 1/8, 1/3, 1/4."],
        "feedback": {"correct": "정답!", "incorrect": "Ben(5/8) < Cora(2/3) < Ava(3/4)."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Without drawing, why is 2/3 > 3/8? (Choose the best reasoning.)",
        "choices": [
            "A. 2/3 > 1/2 (4>3) and 3/8 < 1/2 (6<8) → 2/3 > 1/2 > 3/8",
            "B. 2 < 3과 3 < 8이라서 비교 불가",
            "C. 분자 분모 모두 작으므로 2/3가 작음",
            "D. 항상 2/3 < 3/8"
        ],
        "answer": "A",
        "explanation": "벤치마크 1/2 양쪽으로 갈리면 명확.",
        "difficulty": 3,
        "hints": ["벤치마크 1/2."],
        "feedback": {"correct": "정답!", "incorrect": "벤치마크 1/2이 둘을 가름."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 567 + 285.",
        "choices": ["A. 742", "B. 752", "C. 842", "D. 852"],
        "answer": "D",
        "explanation": "567+285: 7+5=12 (carry 1), 6+8+1=15 (carry 1), 5+2+1=8. Result: 852.",
        "difficulty": 2,
        "hints": ["Two carries.", "567+285=852."],
        "feedback": {"correct": "Right — 852.", "incorrect": "567+285=852."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 902 − 547.",
        "choices": ["A. 345", "B. 355", "C. 445", "D. 455"],
        "answer": "B",
        "explanation": "902−547=355 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "902−547=355."],
        "feedback": {"correct": "Right — 355.", "incorrect": "902−547=355."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 489 students. 158 enrolled, then 73 left. How many students now?",
        "choices": ["A. 258", "B. 416", "C. 574", "D. 720"],
        "answer": "C",
        "explanation": "Step 1: 489+158=647. Step 2: 647−73=574.",
        "difficulty": 3,
        "hints": ["Add enrolled, subtract left.", "489+158=647, 647−73=574."],
        "feedback": {"correct": "Right — 574 students.", "incorrect": "489+158=647, then −73=574."},
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
        "prerequisite": "G3 U9 L3 — 같은 분자 분수 비교 (3.NF.A.3d)",
        "current":      "G3 — 일반 분수 비교: 벤치마크 1/2, 1 활용 (3.NF.A.3d)",
        "successor":    "G3 U9 L5 — 분수 비교 및 정렬 (3.NF.A.3d)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
