"""
G3 U9 L3 — Compare Same Numerator 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.3d (같은 분자 분수 비교 — 분모가 작을수록 큼)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/L3_compare_same_numerator.json"

ID_PREFIX_MAP = {
    "c9_l3_pre_": "PT_",
    "c9_l3_learn_": "LEARN_",
    "c9_l3_try_": "TRY_",
    "c9_l3_pr1_": "R1_",
    "c9_l3_pr2_": "R2_",
    "c9_l3_pr3_": "R3_",
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
    **{f"PT_0{i}": "compare_same_numerator" for i in range(1,6)},
    "LEARN_01": "same_num_rule",
    "LEARN_02": "fraction_strip_same_num",
    "LEARN_03": "size_of_pieces",
    "LEARN_04": "denominator_inverse_size",
    "LEARN_05": "same_num_routine",
    "LEARN_06": "ordering_same_num",
    "LEARN_07": "common_pitfall_denom_size",
    "LEARN_08": "real_world_example",
    **{f"TRY_0{i}": "compare_same_numerator" for i in range(1,6)},
    **{f"R1_{i:02d}": "compare_same_numerator" for i in range(1,11)},
    **{f"R2_0{i}": "compare_same_numerator" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "compare_same_numerator" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "pictorial", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "pictorial",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Lesson 9.3 'Compare Fractions with the Same Numerator' pp.361-364",
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
    "LEARN_01": "같은 분자 규칙 — 분모 작은 쪽이 큼",
    "LEARN_02": "분수 스트립 — 같은 조각 수, 다른 크기",
    "LEARN_03": "조각 크기 비교 — 사분의 vs 팔분의",
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
        "skill_tag": SKILL_TAGS.get(new_id, "compare_same_numerator"),
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "compare_same_numerator")
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
        "title": "분모 ↔ 조각 크기 — 반비례 관계",
        "content": (
            "분모 b는 '몇 등분?'을 의미. b가 클수록 한 조각이 작음. "
            "  분모 2 → 한 조각 = 1/2 (큼) "
            "  분모 4 → 한 조각 = 1/4 "
            "  분모 8 → 한 조각 = 1/8 (작음) "
            "🔍 핵심: 분모 ↑ → 조각 크기 ↓. 같은 분자라면 큰 조각이 모인 쪽이 큼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "denominator_inverse",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "같은 분자 비교 3단계 루틴",
        "content": (
            "같은 분자 분수 비교 3단계: "
            "  단계 1) 분자가 같은지 확인. "
            "  단계 2) 같다면 → 분모만 비교. "
            "  단계 3) 분모 작은 쪽이 큰 분수. "
            "예: 3/4 vs 3/6 → 1) 분자 3 같음 ✓, 2) 4 vs 6, 3) 4 < 6 → 3/4 > 3/6."
        ),
        "cpa_stage": "abstract",
        "visual_type": "same_num_routine",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "여러 분수 정렬 — 분모 큰 순 = 작은 분수 순",
        "content": (
            "같은 분자 분수 정렬: 분모만 보면 됨. "
            "예: 2/3, 2/8, 2/4 → 분모: 3, 8, 4. "
            "큰 분수 순 = 분모 작은 순 → 2/3 > 2/4 > 2/8. "
            "🔍 단축: 분모 정렬 후 분수 순서는 거꾸로."
        ),
        "cpa_stage": "abstract",
        "visual_type": "ordering_same_num",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "흔한 실수 — '분모 큰 = 분수 큰' 함정",
        "content": (
            "흔한 실수 (M02): 1/8 > 1/3 because 8 > 3? ❌ "
            "왜 틀렸나: 분모는 '나눈 칸 수'. 칸 수가 많으면 한 칸은 작음. "
            "올바른: 분자 같으면 분모 작은 쪽이 큰 분수. 1/3 > 1/8. "
            "🔍 직관 점검: 8조각 케이크의 1조각 vs 3조각 케이크의 1조각 — 어느 게 큼?"
        ),
        "cpa_stage": "abstract",
        "visual_type": "common_pitfall",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "실생활 예 — 피자 조각 비교",
        "content": (
            "분수 비교는 실생활 직관과 일치: "
            "  '피자 4조각 중 3조각' (3/4) vs '피자 8조각 중 3조각' (3/8). "
            "  같은 피자, 4조각으로 나누면 한 조각이 큼 → 3/4가 더 많음. "
            "🔍 같은 개수의 조각이라도 조각 크기가 다르면 양이 다름."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "real_world",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "Compare: 4/6 ○ 4/8",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "분자 같음. 분모 6 < 8 → 4/6이 큼.",
        "difficulty": 1,
        "hints": ["분모 작은 쪽이 큼."],
        "feedback": {"correct": "정답!", "incorrect": "4/6 > 4/8."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Which is greater: 1/2 or 1/4?",
        "choices": ["A. 1/2", "B. 1/4", "C. 같음", "D. 비교 불가"],
        "answer": "A",
        "explanation": "분자 같음. 분모 2 < 4 → 1/2.",
        "difficulty": 1,
        "hints": ["분모 작은 쪽."],
        "feedback": {"correct": "정답! 1/2.", "incorrect": "1/2 > 1/4."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "Order from largest: 3/4, 3/8, 3/6.",
        "choices": [
            "A. 3/4 > 3/6 > 3/8",
            "B. 3/8 > 3/6 > 3/4",
            "C. 3/4 > 3/8 > 3/6",
            "D. 3/6 > 3/4 > 3/8"
        ],
        "answer": "A",
        "explanation": "분모: 4, 8, 6 → 작은 순 4, 6, 8 → 분수 큰 순 3/4 > 3/6 > 3/8.",
        "difficulty": 2,
        "hints": ["분모 작은 = 분수 큰."],
        "feedback": {"correct": "정답!", "incorrect": "3/4 > 3/6 > 3/8."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Compare: 5/8 ○ 5/6",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": "<",
        "explanation": "분자 같음. 분모 8 > 6 → 5/8 < 5/6.",
        "difficulty": 1,
        "hints": ["분모 큰 = 분수 작은."],
        "feedback": {"correct": "정답!", "incorrect": "5/8 < 5/6."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "Compare: 2/2 ○ 2/4",
        "choices": [">", "<", "=", "비교 불가"],
        "answer": ">",
        "explanation": "2/2 = 1, 2/4 = 1/2. 1 > 1/2.",
        "difficulty": 2,
        "hints": ["분모 작은 쪽이 큼."],
        "feedback": {"correct": "정답!", "incorrect": "2/2 > 2/4."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Which is greater: 4/4 or 4/8?",
        "choices": ["A. 4/4", "B. 4/8", "C. 같음", "D. 비교 불가"],
        "answer": "A",
        "explanation": "분자 같음. 4 < 8 → 4/4 > 4/8.",
        "difficulty": 1,
        "hints": ["분모 작은."],
        "feedback": {"correct": "정답! 4/4.", "incorrect": "4/4 > 4/8."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Order from least to greatest: 5/6, 5/3, 5/8.",
        "choices": [
            "A. 5/8 < 5/6 < 5/3",
            "B. 5/3 < 5/6 < 5/8",
            "C. 5/6 < 5/8 < 5/3",
            "D. 5/3 < 5/8 < 5/6"
        ],
        "answer": "A",
        "explanation": "분모 큰 순 = 분수 작은 순. 8>6>3 → 5/8 < 5/6 < 5/3.",
        "difficulty": 2,
        "hints": ["분모 큰 = 분수 작은."],
        "feedback": {"correct": "정답!", "incorrect": "5/8 < 5/6 < 5/3."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Two same-size pizzas. Pizza A: 2/4 eaten. Pizza B: 2/8 eaten. Which had more eaten?",
        "choices": ["A. Pizza A", "B. Pizza B", "C. 같음", "D. 비교 불가"],
        "answer": "A",
        "explanation": "분자 같음. 분모 4 < 8 → 2/4 > 2/8.",
        "difficulty": 2,
        "hints": ["같은 피자, 분모 비교."],
        "feedback": {"correct": "정답! Pizza A.", "incorrect": "2/4 > 2/8."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Write a fraction with numerator 1 that is GREATER than 1/8 but LESS than 1/3.",
        "choices": ["A. 1/2", "B. 1/4", "C. 1/9", "D. 1/12"],
        "answer": "B",
        "explanation": "1/3 > 1/4 > 1/8 (분모 4가 3과 8 사이).",
        "difficulty": 3,
        "hints": ["분모가 3과 8 사이여야."],
        "feedback": {"correct": "정답! 1/4.", "incorrect": "분모 4 → 1/8 < 1/4 < 1/3."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Two ribbons of equal length. Kim cut 3/4 off her ribbon. Tom cut 3/8 off his. Who cut more?",
        "choices": ["A. Kim", "B. Tom", "C. 같음", "D. 비교 불가"],
        "answer": "A",
        "explanation": "분자 같음 3. 분모 4 < 8 → 3/4 > 3/8 → Kim.",
        "difficulty": 3,
        "hints": ["같은 길이, 분모 작은."],
        "feedback": {"correct": "정답! Kim.", "incorrect": "3/4 > 3/8 → Kim."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "If 2/3 = 4/6 (equivalent), what does that imply about comparing 2/3 and 2/6?",
        "choices": [
            "A. 2/3 > 2/6 (4 조각 vs 2 조각, 같은 단위)",
            "B. 2/3 < 2/6",
            "C. 2/3 = 2/6",
            "D. 비교 불가"
        ],
        "answer": "A",
        "explanation": "2/3 = 4/6 > 2/6 (같은 분모, 분자 4 > 2).",
        "difficulty": 3,
        "hints": ["2/3 = 4/6 활용."],
        "feedback": {"correct": "정답!", "incorrect": "2/3=4/6 > 2/6."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 419 + 286.",
        "choices": ["A. 595", "B. 605", "C. 695", "D. 705"],
        "answer": "D",
        "explanation": "419+286: 9+6=15 (carry 1), 1+8+1=10 (carry 1), 4+2+1=7. Result: 705.",
        "difficulty": 2,
        "hints": ["Two carries.", "419+286=705."],
        "feedback": {"correct": "Right — 705.", "incorrect": "419+286=705."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 703 − 458.",
        "choices": ["A. 235", "B. 245", "C. 335", "D. 345"],
        "answer": "B",
        "explanation": "703−458=245 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "703−458=245."],
        "feedback": {"correct": "Right — 245.", "incorrect": "703−458=245."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bakery had 564 cupcakes. They sold 248, then made 175 more. How many cupcakes now?",
        "choices": ["A. 316", "B. 491", "C. 587", "D. 739"],
        "answer": "B",
        "explanation": "Step 1: 564−248=316. Step 2: 316+175=491.",
        "difficulty": 3,
        "hints": ["Subtract sold, add baked.", "564−248=316, 316+175=491."],
        "feedback": {"correct": "Right — 491 cupcakes.", "incorrect": "564−248=316, then +175=491."},
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
        "prerequisite": "G3 U9 L2 — 같은 분모 분수 비교 (3.NF.A.3d)",
        "current":      "G3 — 같은 분자 분수 비교: 분모 작을수록 큼 (3.NF.A.3d)",
        "successor":    "G3 U9 L4 — 일반 분수 비교 (3.NF.A.3d)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
