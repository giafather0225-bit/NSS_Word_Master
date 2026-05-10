"""
G3 U10 L6 — Same Area, Different Perimeters 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.MD.D.8 (같은 넓이, 다른 둘레 — 정사각형이 최소 둘레)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U10_perimeter/L6_same_area_different_perimeters.json"

ID_PREFIX_MAP = {
    "c10_l6_pre_":   "PT_",
    "c10_l6_learn_": "LEARN_",
    "c10_l6_try_":   "TRY_",
    "c10_l6_pr1_":   "R1_",
    "c10_l6_pr2_":   "R2_",
    "c10_l6_pr3_":   "R3_",
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
    **{f"PT_0{i}": "same_A_diff_P" for i in range(1, 6)},
    "LEARN_01": "concept_intro",
    "LEARN_02": "factor_pairs",
    "LEARN_03": "fence_optimization",
    "LEARN_04": "square_min_perimeter",
    "LEARN_05": "thin_max_perimeter",
    "LEARN_06": "factor_pair_routine",
    "LEARN_07": "real_world_decision",
    "LEARN_08": "summary_two_principles",
    **{f"TRY_0{i}": "same_A_diff_P" for i in range(1, 6)},
    **{f"R1_{i:02d}": "same_A_diff_P" for i in range(1, 11)},
    **{f"R2_0{i}": "same_A_word" for i in range(1, 8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "same_A_optimization" for i in range(1, 6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1, 6)},
    "LEARN_01": "pictorial", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract", "LEARN_06": "abstract",
    "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1, 6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R3_0{i}": "abstract" for i in range(1, 6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Lesson 10.6 'Same Area, Different Perimeters' pp.433-436",
        "procedure_source": "EngageNY Grade 3 Module 7 Lesson 20 — Same Area, Different Perimeters",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


LEARN_TITLE_MAP = {
    "LEARN_01": "같은 넓이라도 둘레가 다를 수 있다",
    "LEARN_02": "약수 쌍으로 직사각형 나열",
    "LEARN_03": "펜스 최소 — 정사각형이 답",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "같은 넓이, 다른 둘레"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "same_A_diff_P"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "same_A_diff_P",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "same_A_diff_P")
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
        "title": "정사각형이 최소 둘레 — 핵심 원리",
        "content": (
            "주어진 넓이에서 가장 작은 둘레를 가지는 직사각형은 정사각형. "
            "예: A=36 → 6×6 (P=24)가 최소. 36×1(P=74), 18×2(P=40), 12×3(P=30), 9×4(P=26)보다 작음. "
            "🔍 직관: 균형 잡힌 모양일수록 가장자리 짧음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "square_min_perimeter",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "가늘고 긴 모양 = 최대 둘레",
        "content": (
            "같은 넓이에서 가장 큰 둘레는 1×넓이 (가장 가늘고 긴) 모양. "
            "예: A=24 → 24×1(P=50)이 최대. 6×4(P=20)와 비교하면 2.5배. "
            "🔍 같은 면적이라도 길게 늘이면 펜스 더 많이 필요."
        ),
        "cpa_stage": "abstract",
        "visual_type": "thin_max_perimeter",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "약수 쌍 루틴 — 모든 직사각형 찾기",
        "content": (
            "넓이 A → l × w = A 인 정수 쌍 모두 나열 (l ≥ w). "
            "예: A=20 → 약수쌍: (20,1), (10,2), (5,4). 둘레 42, 24, 18. "
            "  단계: ① A의 약수 찾기. ② l≥w 쌍으로 묶기. ③ 각 P 계산. "
            "🔍 정사각형 가능 (A가 제곱수일 때)? → 그게 최소 P."
        ),
        "cpa_stage": "abstract",
        "visual_type": "factor_pair_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "실생활 결정 — 펜스 절약",
        "content": (
            "넓이 36 m² 정원, 펜스를 최소로 쓰려면? "
            "  옵션: 36×1(P=74m), 12×3(P=30m), 9×4(P=26m), 6×6(P=24m). "
            "정답: 6×6 정사각형, 펜스 24 m. "
            "🔍 같은 넓이 보장 + 펜스 최소화 = 정사각형. (반대로 가늘게 만들면 펜스 낭비.)"
        ),
        "cpa_stage": "abstract",
        "visual_type": "real_world_decision",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "두 원리 요약 — L5 vs L6",
        "content": (
            "L5: 같은 둘레 → 정사각형 = 최대 넓이 / 길쭉 = 최소 넓이. "
            "L6: 같은 넓이 → 정사각형 = 최소 둘레 / 길쭉 = 최대 둘레. "
            "🔍 두 원리 공통점: '정사각형이 가장 효율적'. "
            "응용: 펜스 절약(같은 면적), 면적 최대(같은 펜스) — 둘 다 정사각형 답."
        ),
        "cpa_stage": "abstract",
        "visual_type": "summary",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "Three rectangles all have area 24 sq cm: 24×1, 8×3, 6×4. Which has the GREATEST perimeter?",
        "choices": ["A. 24×1 (50)", "B. 8×3 (22)", "C. 6×4 (20)", "D. 모두 같음"],
        "answer": "A",
        "explanation": "24×1 = P=50이 최대 (가장 길쭉).",
        "difficulty": 2,
        "hints": ["가장 길쭉 = 최대 둘레."],
        "feedback": {"correct": "정답! 24×1.", "incorrect": "24×1 P=50 최대."},
    },
    {
        "id": "TRY_05",
        "type": "fill_in",
        "question": "List all whole-number rectangle pairs with area 18 sq cm. Then state the SMALLEST perimeter.",
        "answer": "쌍: (18,1)P=38, (9,2)P=22, (6,3)P=18. 최소 18 cm (6×3)",
        "accept": [
            "(18,1)(9,2)(6,3) — 최소 18",
            "6×3 P=18 최소",
            "P=18 cm 6×3",
            "최소 둘레 18"
        ],
        "explanation": "약수 쌍: 1×18, 2×9, 3×6. 둘레 38, 22, 18. 6×3이 정사각에 가장 가까움 → 최소 P=18.",
        "difficulty": 3,
        "hints": ["18의 약수.", "각 P 계산."],
        "feedback": {"correct": "정확!", "incorrect": "(6,3) P=18 최소."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "Area = 12 sq cm. Which has the smallest perimeter?",
        "choices": ["A. 12×1 (26)", "B. 6×2 (16)", "C. 4×3 (14)", "D. 3×4 (14)"],
        "answer": "C",
        "explanation": "4×3 = 3×4 = P=14 최소 (정사각에 가장 가까움).",
        "difficulty": 2,
        "hints": ["정사각에 가까울수록 P 작음."],
        "feedback": {"correct": "정답! P=14.", "incorrect": "4×3 P=14 최소."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "Area = 16 sq cm. Find a square rectangle. Side = __ cm.",
        "answer": "4 cm",
        "accept": ["4", "4 cm"],
        "explanation": "4×4 = 16. 정사각 변 4 cm. P=16 cm (최소).",
        "difficulty": 1,
        "hints": ["같은 두 수 곱해서 16."],
        "feedback": {"correct": "정답! 4 cm.", "incorrect": "4×4=16."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Area = 30 sq cm. Of these, which has the GREATEST perimeter?",
        "choices": ["A. 30×1 (62)", "B. 15×2 (34)", "C. 10×3 (26)", "D. 6×5 (22)"],
        "answer": "A",
        "explanation": "30×1 P=62 최대 (가장 길쭉).",
        "difficulty": 2,
        "hints": ["가장 길쭉 = 최대 P."],
        "feedback": {"correct": "정답! 30×1.", "incorrect": "30×1 P=62 최대."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Farmer Sue needs a 36 sq m garden. She wants the LEAST amount of fence. What dimensions?",
        "choices": ["A. 36×1 (P=74)", "B. 12×3 (P=30)", "C. 9×4 (P=26)", "D. 6×6 (P=24)"],
        "answer": "D",
        "explanation": "6×6 정사각형 → P=24 m (최소). 다른 옵션 모두 24보다 큼.",
        "difficulty": 2,
        "hints": ["같은 넓이라도 P 다름.", "정사각형이 최소 P."],
        "feedback": {"correct": "정답! 6×6.", "incorrect": "정사각 6×6 P=24 m 최소."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Two flags both cover 20 sq ft. Flag A: 10×2, Flag B: 5×4. Which has SHORTER trim around the edge?",
        "choices": ["A. Flag A (P=24)", "B. Flag B (P=18)", "C. 같음", "D. 알 수 없음"],
        "answer": "B",
        "explanation": "A: P=2×(10+2)=24. B: P=2×(5+4)=18. B가 정사각에 더 가까움 → P 짧음.",
        "difficulty": 2,
        "hints": ["둘 다 P 계산.", "정사각에 가까운 쪽."],
        "feedback": {"correct": "정답! Flag B.", "incorrect": "B(18)<A(24)."},
    },
    {
        "id": "R2_07",
        "type": "fill_in",
        "question": "A rug has area 48 sq ft. Find the rectangle with the shortest perimeter (whole numbers).",
        "answer": "6×8 또는 8×6 (P=28)",
        "accept": [
            "6×8",
            "8×6",
            "6 by 8",
            "P=28",
            "6×8 P=28",
            "6,8"
        ],
        "explanation": "약수쌍: (48,1) P=98, (24,2) P=52, (16,3) P=38, (12,4) P=32, (8,6) P=28. 8×6이 정사각에 가장 가까움 → P=28.",
        "difficulty": 3,
        "hints": ["48의 약수쌍.", "정사각에 가장 가까운."],
        "feedback": {"correct": "정답! 8×6.", "incorrect": "(8,6) P=28 최소."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Tom says: 'Same area means same perimeter.' Lin disagrees. Who is correct?",
        "choices": [
            "A. Tom 맞음 — 둘 다 항상 같음",
            "B. Lin 맞음 — 1×16(P=34) ≠ 4×4(P=16) 같은 A=16",
            "C. 둘 다 맞음",
            "D. 둘 다 틀림"
        ],
        "answer": "B",
        "explanation": "같은 넓이라도 둘레는 다양함. A=16 → 16×1 P=34, 8×2 P=20, 4×4 P=16. P 다름.",
        "difficulty": 3,
        "hints": ["반례 찾기.", "같은 A에 다른 직사각형."],
        "feedback": {"correct": "정답! Lin.", "incorrect": "16×1≠4×4의 P."},
    },
    {
        "id": "R3_05",
        "type": "open_response",
        "question": "A 28 sq ft garden needs fencing. List ALL whole-number rectangle dimensions and their perimeters. Which uses the LEAST fence?",
        "answer": "쌍: (28,1)P=58, (14,2)P=32, (7,4)P=22. 최소 22 ft → 7×4.",
        "accept": [
            "7×4 → P=22 최소",
            "(28,1),(14,2),(7,4) — 7×4 min",
            "22 ft (7×4)",
            "7×4 가 최소 P=22"
        ],
        "explanation": "28의 약수쌍: 1×28, 2×14, 4×7 (3개). 둘레 58, 32, 22. 7×4가 정사각에 가장 가까움 → 22 ft 최소. (28은 제곱수 아님 → 정사각 불가.)",
        "difficulty": 3,
        "hints": ["28의 약수.", "3쌍 모두."],
        "feedback": {"correct": "정확!", "incorrect": "(7,4) P=22 최소."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 549 + 386.",
        "choices": ["A. 825", "B. 835", "C. 925", "D. 935"],
        "answer": "D",
        "explanation": "549+386: 9+6=15 (carry 1), 4+8+1=13 (carry 1), 5+3+1=9. Result: 935.",
        "difficulty": 2,
        "hints": ["Two carries.", "549+386=935."],
        "feedback": {"correct": "Right — 935.", "incorrect": "549+386=935."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 700 − 463.",
        "choices": ["A. 237", "B. 247", "C. 337", "D. 343"],
        "answer": "A",
        "explanation": "700−463: borrow across two zeros. 700−463=237.",
        "difficulty": 2,
        "hints": ["Borrow across two zeros.", "700−463=237."],
        "feedback": {"correct": "Right — 237.", "incorrect": "700−463=237."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A toy store had 387 toys. They received 256 more, then sold 198. How many toys remain?",
        "choices": ["A. 445", "B. 533", "C. 643", "D. 841"],
        "answer": "A",
        "explanation": "Step 1: 387+256=643. Step 2: 643−198=445.",
        "difficulty": 3,
        "hints": ["Add then subtract.", "387+256=643, −198=445."],
        "feedback": {"correct": "Right — 445.", "incorrect": "387+256=643, −198=445."},
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
        "prerequisite": "G3 U10 L5 — 같은 둘레, 다른 넓이 (3.MD.D.8)",
        "current":      "G3 U10 L6 — 같은 넓이, 다른 둘레 (3.MD.D.8)",
        "successor":    "G3 U10 unit_test — 둘레 단원 평가 (3.MD.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u10_l6.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
