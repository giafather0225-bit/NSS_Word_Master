"""
G3 U10 L5 — Same Perimeter, Different Areas 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.MD.D.8 (같은 둘레, 다른 넓이 — 정사각형이 최대)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U10_perimeter/L5_same_perimeter_different_areas.json"

ID_PREFIX_MAP = {
    "c10_l5_pre_":   "PT_",
    "c10_l5_learn_": "LEARN_",
    "c10_l5_try_":   "TRY_",
    "c10_l5_pr1_":   "R1_",
    "c10_l5_pr2_":   "R2_",
    "c10_l5_pr3_":   "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.MD.D.8.M01"] for i in range(1, 6)},
    **{f"LEARN_0{i}": [] for i in range(1, 9)},
    **{f"TRY_0{i}": ["3.MD.D.8.M01"] for i in range(1, 6)},
    **{f"R1_{i:02d}": ["3.MD.D.8.M01"] for i in range(1, 11)},
    **{f"R2_0{i}": ["3.MD.D.8.M01"] for i in range(1, 8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.MD.D.8.M01"] for i in range(1, 6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "same_P_diff_A" for i in range(1, 6)},
    "LEARN_01": "concept_intro",
    "LEARN_02": "compare_areas",
    "LEARN_03": "list_all_pairs",
    "LEARN_04": "square_max_area",
    "LEARN_05": "thin_min_area",
    "LEARN_06": "lw_sum_routine",
    "LEARN_07": "real_world_garden",
    "LEARN_08": "intuition_visualization",
    **{f"TRY_0{i}": "same_P_diff_A" for i in range(1, 6)},
    **{f"R1_{i:02d}": "same_P_diff_A" for i in range(1, 11)},
    **{f"R2_0{i}": "same_P_word" for i in range(1, 8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "same_P_optimization" for i in range(1, 6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1, 6)},
    "LEARN_01": "pictorial", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract", "LEARN_06": "abstract",
    "LEARN_07": "abstract", "LEARN_08": "pictorial",
    **{f"TRY_0{i}": "abstract" for i in range(1, 6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R3_0{i}": "abstract" for i in range(1, 6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Lesson 10.5 'Same Perimeter, Different Areas' pp.429-432",
        "procedure_source": "EngageNY Grade 3 Module 7 Lesson 19 — Same Perimeter, Different Areas",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


LEARN_TITLE_MAP = {
    "LEARN_01": "같은 둘레라도 넓이가 다를 수 있다",
    "LEARN_02": "넓이 비교 — 정사각형에 가까울수록 큼",
    "LEARN_03": "모든 정수 쌍 나열 — l+w = P÷2",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "같은 둘레, 다른 넓이"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "same_P_diff_A"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "same_P_diff_A",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "same_P_diff_A")
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
        "title": "정사각형이 최대 넓이 — 핵심 원리",
        "content": (
            "주어진 둘레에서 가장 큰 넓이를 가지는 직사각형은 정사각형. "
            "예: P=20 → 5×5(=25)가 최대. 9×1(=9), 7×3(=21), 6×4(=24)보다 큼. "
            "🔍 왜? 길이와 너비가 균형 잡힐수록 넓이 ↑. 한쪽이 길어지면 다른 쪽이 줄어 곱 ↓."
        ),
        "cpa_stage": "abstract",
        "visual_type": "square_max_area",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "가늘고 긴 모양 = 최소 넓이",
        "content": (
            "같은 둘레에서 가장 작은 넓이는 1×(P/2−1) 모양 (가장 가늘고 긴 직사각형). "
            "예: P=20 → 9×1=9 (최소). "
            "🔍 정사각형 25와 비교하면 거의 1/3. 모양이 균형 잃을수록 넓이 손실 큼."
        ),
        "cpa_stage": "abstract",
        "visual_type": "thin_min_area",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "체계적 나열 — l+w 합 사용",
        "content": (
            "둘레 P → l+w = P÷2. 정수 쌍 (l, w)을 l ≥ w로 나열. "
            "예: P=18 → l+w=9 → 쌍: (8,1), (7,2), (6,3), (5,4). "
            "넓이: 8, 14, 18, 20. 최대 20 (5,4가 정사각형에 가장 가까움)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "lw_sum_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "실생활 최적화 — 정원/축사",
        "content": (
            "농부가 펜스 24 m로 정원을 만든다. 가장 넓은 모양은? "
            "  l+w=12 → 쌍: (11,1)=11, (9,3)=27, (7,5)=35, (6,6)=36. "
            "정답: 6×6 정사각형, 넓이 36 m². "
            "🔍 같은 펜스(둘레)로 면적을 최대화 → 정사각형."
        ),
        "cpa_stage": "abstract",
        "visual_type": "real_world_garden",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "직관 — 모눈종이로 시각화",
        "content": (
            "P=12로 만들 수 있는 직사각형 종류: "
            "  · 5×1 (얇고 긴 띠 모양) — 면적 5 "
            "  · 4×2 (직사각형) — 면적 8 "
            "  · 3×3 (정사각형) — 면적 9 "
            "🖍️ 모눈에 그려보면: 길쭉할수록 안쪽 칸 적음, 정사각에 가까울수록 안쪽 풍성."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "intuition_visualization",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Three rectangles all have perimeter 18 cm: 8×1, 6×3, 5×4. Which has the SMALLEST area?",
        "choices": ["A. 8×1 (8)", "B. 6×3 (18)", "C. 5×4 (20)", "D. 모두 같음"],
        "answer": "A",
        "explanation": "8×1 = 8이 가장 작음. 가장 가는 모양이 최소.",
        "difficulty": 2,
        "hints": ["가장 가늘 = 최소 넓이."],
        "feedback": {"correct": "정답! 8×1.", "incorrect": "8×1=8 — 가장 작음."},
    },
    {
        "id": "TRY_05",
        "type": "fill_in",
        "question": "List all whole-number rectangle pairs with perimeter 12 cm. Then state the GREATEST area.",
        "answer": "쌍: (5,1)=5, (4,2)=8, (3,3)=9. 최대 9 sq cm (3×3 정사각형)",
        "accept": [
            "5,1 / 4,2 / 3,3 — 최대 9",
            "(5,1)(4,2)(3,3) max 9",
            "9 sq cm 3×3",
            "최대 넓이 9"
        ],
        "explanation": "l+w=6 → (5,1), (4,2), (3,3). 넓이 5, 8, 9. 정사각형 3×3 최대.",
        "difficulty": 3,
        "hints": ["l+w = P÷2.", "3쌍."],
        "feedback": {"correct": "정확!", "incorrect": "(5,1),(4,2),(3,3) — 최대 9."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Perimeter = 14 cm. Which has the greatest area?",
        "choices": ["A. 6×1 (6)", "B. 5×2 (10)", "C. 4×3 (12)", "D. 3×4 (12)"],
        "answer": "C",
        "explanation": "4×3 = 3×4 = 12 (정사각에 가장 가까움 → 최대).",
        "difficulty": 2,
        "hints": ["정사각에 가까울수록 큼."],
        "feedback": {"correct": "정답! 12.", "incorrect": "4×3=12 — 최대."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "Perimeter = 16 cm. List a rectangle with area 12 sq cm.",
        "answer": "6×2",
        "accept": ["6×2", "6 by 2", "6,2", "2×6"],
        "explanation": "P=16 → l+w=8 → (6,2): A=12.",
        "difficulty": 2,
        "hints": ["l+w=8, l×w=12."],
        "feedback": {"correct": "정답! 6×2.", "incorrect": "6+2=8(P=16), 6×2=12."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Perimeter = 24 cm. Of these, which has the LEAST area?",
        "choices": ["A. 11×1 (11)", "B. 9×3 (27)", "C. 7×5 (35)", "D. 6×6 (36)"],
        "answer": "A",
        "explanation": "11×1 = 11이 최소 (가장 길쭉).",
        "difficulty": 2,
        "hints": ["가장 길쭉 = 최소."],
        "feedback": {"correct": "정답! 11×1.", "incorrect": "11×1=11 최소."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Farmer Joe has 20 m of fence. He wants the LARGEST area for his vegetable garden. What dimensions?",
        "choices": ["A. 9×1", "B. 7×3", "C. 6×4", "D. 5×5"],
        "answer": "D",
        "explanation": "5×5 정사각형 → A=25 m². 다른 옵션 모두 25보다 작음.",
        "difficulty": 2,
        "hints": ["정사각형이 최대."],
        "feedback": {"correct": "정답! 5×5.", "incorrect": "5×5=25 m² 최대."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Lily makes two pizza boxes. Both have perimeter 28 in. Box A: 12×2, Box B: 8×6. Which holds more pizza?",
        "choices": ["A. Box A (24)", "B. Box B (48)", "C. 같음", "D. 알 수 없음"],
        "answer": "B",
        "explanation": "B: 8×6=48 > A: 12×2=24. B가 정사각에 더 가까움.",
        "difficulty": 2,
        "hints": ["둘 다 넓이 계산.", "정사각에 가까운 게 큼."],
        "feedback": {"correct": "정답! Box B.", "incorrect": "B(48)>A(24)."},
    },
    {
        "id": "R2_07",
        "type": "fill_in",
        "question": "Sara has 18 ft of trim. She wants a rectangular flower bed with the SMALLEST area. What dimensions?",
        "answer": "8×1",
        "accept": ["8×1", "8 by 1 ft", "8,1", "1×8"],
        "explanation": "P=18 → l+w=9 → (8,1)→8, (7,2)→14, (6,3)→18, (5,4)→20. 최소 8 (8×1).",
        "difficulty": 3,
        "hints": ["가장 가는 모양.", "1과 가장 큰 수."],
        "feedback": {"correct": "정답! 8×1.", "incorrect": "(8,1)=8 최소."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Lin says: 'For perimeter 20, all rectangles have the same area.' Is she correct?",
        "choices": [
            "A. 예 — 둘레 같으면 넓이도 같음",
            "B. 아니오 — 정사각형(5×5)이 25, 9×1이 9 → 다름",
            "C. 일부만 맞음",
            "D. 비교 불가"
        ],
        "answer": "B",
        "explanation": "P=20 → 옵션: 9×1=9, 8×2=16, 7×3=21, 6×4=24, 5×5=25. 모두 다름. 같은 둘레 ≠ 같은 넓이.",
        "difficulty": 3,
        "hints": ["반례로 두 직사각형 계산."],
        "feedback": {"correct": "정답!", "incorrect": "5×5=25 vs 9×1=9 — 다름."},
    },
    {
        "id": "R3_05",
        "type": "open_response",
        "question": "A dog pen needs perimeter 22 ft. List ALL whole-number rectangle dimensions and their areas. Which gives the most space for the dog?",
        "answer": "쌍: (10,1)=10, (9,2)=18, (8,3)=24, (7,4)=28, (6,5)=30. 최대 30 sq ft → 6×5.",
        "accept": [
            "6×5 → 30 sq ft 최대",
            "(10,1),(9,2),(8,3),(7,4),(6,5) — 6×5 max",
            "30 sq ft (6×5)",
            "6×5 가 최대 30"
        ],
        "explanation": "P=22 → l+w=11. 5쌍: (10,1),(9,2),(8,3),(7,4),(6,5). 넓이 10,18,24,28,30. 6×5가 정사각에 가장 가까움 → 30 sq ft 최대.",
        "difficulty": 3,
        "hints": ["l+w=11.", "5쌍 모두."],
        "feedback": {"correct": "정확!", "incorrect": "(6,5)=30 sq ft 최대."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 658 + 274.",
        "choices": ["A. 822", "B. 832", "C. 922", "D. 932"],
        "answer": "D",
        "explanation": "658+274: 8+4=12 (carry 1), 5+7+1=13 (carry 1), 6+2+1=9. Result: 932.",
        "difficulty": 2,
        "hints": ["Two carries.", "658+274=932."],
        "feedback": {"correct": "Right — 932.", "incorrect": "658+274=932."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 803 − 519.",
        "choices": ["A. 284", "B. 294", "C. 384", "D. 394"],
        "answer": "A",
        "explanation": "803−519: borrow across zero. 803−519=284.",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "803−519=284."],
        "feedback": {"correct": "Right — 284.", "incorrect": "803−519=284."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 459 books. They received 187, then donated 246. How many books now?",
        "choices": ["A. 26", "B. 400", "C. 426", "D. 646"],
        "answer": "B",
        "explanation": "Step 1: 459+187=646. Step 2: 646−246=400.",
        "difficulty": 3,
        "hints": ["Add then subtract.", "459+187=646, −246=400."],
        "feedback": {"correct": "Right — 400.", "incorrect": "459+187=646, −246=400."},
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
        "prerequisite": "G3 U10 L4 — 둘레와 넓이의 관계 (3.MD.D.8)",
        "current":      "G3 U10 L5 — 같은 둘레, 다른 넓이 (3.MD.D.8)",
        "successor":    "G3 U10 L6 — 같은 넓이, 다른 둘레 (3.MD.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u10_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
