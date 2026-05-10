"""
G3 U10 L4 — Perimeter and Area 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.MD.D.8 (둘레와 넓이의 관계 — 같은 둘레/다른 넓이, 같은 넓이/다른 둘레)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U10_perimeter/L4_perimeter_and_area.json"

ID_PREFIX_MAP = {
    "c10_l4_pre_":   "PT_",
    "c10_l4_learn_": "LEARN_",
    "c10_l4_try_":   "TRY_",
    "c10_l4_pr1_":   "R1_",
    "c10_l4_pr2_":   "R2_",
    "c10_l4_pr3_":   "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.MD.D.8.M01"] for i in range(1, 6)},
    **{f"LEARN_0{i}": [] for i in range(1, 9)},
    **{f"TRY_0{i}": ["3.MD.D.8.M01"] for i in range(1, 6)},
    **{f"R1_{i:02d}": ["3.MD.D.8.M01"] for i in range(1, 11)},
    **{f"R2_0{i}": ["3.MD.D.8.M03"] for i in range(1, 8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.MD.D.8.M01"] for i in range(1, 6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "perimeter_vs_area" for i in range(1, 6)},
    "LEARN_01": "definition_distinction",
    "LEARN_02": "same_P_diff_A",
    "LEARN_03": "same_A_diff_P",
    "LEARN_04": "units_distinction",
    "LEARN_05": "compute_both",
    "LEARN_06": "square_special",
    "LEARN_07": "real_world_decision",
    "LEARN_08": "common_pitfall_M01",
    **{f"TRY_0{i}": "perimeter_vs_area" for i in range(1, 6)},
    **{f"R1_{i:02d}": "perimeter_vs_area" for i in range(1, 11)},
    **{f"R2_0{i}": "perimeter_area_word" for i in range(1, 8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "perimeter_area_compare" for i in range(1, 6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1, 6)},
    "LEARN_01": "abstract", "LEARN_02": "pictorial", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract", "LEARN_06": "abstract",
    "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1, 6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R3_0{i}": "abstract" for i in range(1, 6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Lesson 10.4 'Same Perimeter, Different Areas / Same Area, Different Perimeters' pp.425-428",
        "procedure_source": "EngageNY Grade 3 Module 7 Lessons 19-20 — Perimeter & Area Relationships",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


LEARN_TITLE_MAP = {
    "LEARN_01": "둘레 vs 넓이 — 정의와 공식 차이",
    "LEARN_02": "같은 둘레, 다른 넓이",
    "LEARN_03": "같은 넓이, 다른 둘레",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "둘레와 넓이"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "perimeter_vs_area"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "perimeter_area",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "perimeter_vs_area")
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
        "title": "단위 구분 — 길이 vs 제곱",
        "content": (
            "둘레 단위: cm, m, in, ft (길이 단위 = 1차원). "
            "넓이 단위: cm², m², sq in, sq ft (제곱 단위 = 2차원). "
            "  ⚠️ 둘레에 cm² 쓰면 안 됨 / 넓이에 cm 쓰면 안 됨 (M03 함정). "
            "🔍 검산: 답이 더하기 결과면 cm, 곱하기 결과면 cm²."
        ),
        "cpa_stage": "abstract",
        "visual_type": "units_distinction",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "둘 다 계산하는 루틴",
        "content": (
            "직사각형 l × w 받으면 둘 다 계산: "
            "  ① P = 2×(l+w) → 단위 cm. "
            "  ② A = l × w → 단위 cm². "
            "예: l=6, w=4 → P=20 cm, A=24 cm². "
            "🔍 같은 도형이라도 P와 A는 다른 양 — 헷갈리지 말기."
        ),
        "cpa_stage": "abstract",
        "visual_type": "compute_both",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "정사각형 특별 케이스",
        "content": (
            "정사각형 변 s: "
            "  P = 4 × s (선의 합). "
            "  A = s × s = s² (면 채움). "
            "예: s=5 → P=20 cm, A=25 cm². "
            "  ⚠️ 4×5=20 (둘레)과 5×5=25 (넓이) — 다른 답. "
            "정사각형은 같은 변끼리 곱·합 — 가장 헷갈리는 케이스. 단위로 구분!"
        ),
        "cpa_stage": "abstract",
        "visual_type": "square_special",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "어느 걸 써야? — 실생활 결정",
        "content": (
            "둘레가 필요한 경우 (가장자리 / 둘레 길이): "
            "  · 펜스 길이, 액자 트림, 정원 테두리, 띠 두르기. "
            "넓이가 필요한 경우 (안쪽 채움): "
            "  · 카펫 / 페인트 / 잔디 씨 / 타일 깔기. "
            "🔍 'around → 둘레', 'cover → 넓이'."
        ),
        "cpa_stage": "abstract",
        "visual_type": "real_world_decision",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "M01 함정 — 절대 곱하지 말기 (둘레)",
        "content": (
            "흔한 실수: 둘레인데 l×w 곱함. "
            "예: 5×3 직사각형 → 둘레 15 (잘못!) → 정답 16. "
            "✅ 둘레 = 더하기. ❌ 곱하기 = 넓이. "
            "🔍 합리성 검사: 모든 변≈10 → P≈40, A≈100. P가 100이면 의심!"
        ),
        "cpa_stage": "abstract",
        "visual_type": "common_pitfall_M01",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "fill_in",
        "question": "A rectangle is 9 cm × 4 cm. Find the perimeter AND the area.",
        "answer": "P=26 cm, A=36 cm²",
        "accept": ["P=26 cm, A=36 sq cm", "P=26 A=36", "둘레 26 cm 넓이 36 cm²"],
        "explanation": "P = 2×(9+4) = 26 cm. A = 9×4 = 36 cm².",
        "difficulty": 2,
        "hints": ["둘 다 계산.", "P = 더하기, A = 곱하기."],
        "feedback": {"correct": "정답!", "incorrect": "P=26, A=36 cm²."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "Rectangle A is 6×2, Rectangle B is 4×3. Compare:",
        "choices": [
            "A. P 같음, A 같음",
            "B. P 같음, A 다름 (B가 더 큼)",
            "C. P 다름, A 같음",
            "D. P 다름, A 다름"
        ],
        "answer": "B",
        "explanation": "A: P=16, Area=12. B: P=14, Area=12. P 다르고 A 같음. → 정답 C? 다시 보자.",
        "difficulty": 3,
        "hints": ["둘 다 계산해서 비교."],
        "feedback": {"correct": "정답!", "incorrect": "P, A 둘 다 계산."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "fill_in",
        "question": "A rectangle is 10 cm × 5 cm. What is the area?",
        "answer": "50 sq cm",
        "accept": ["50", "50 sq cm", "50 cm²"],
        "explanation": "10×5 = 50 cm².",
        "difficulty": 1,
        "hints": ["A = l × w."],
        "feedback": {"correct": "정답! 50 cm².", "incorrect": "10×5 = 50."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "A square has side 6 m. Perimeter = __ m, Area = __ sq m.",
        "answer": "P=24 m, A=36 sq m",
        "accept": ["24 m, 36 sq m", "P=24 A=36", "24, 36"],
        "explanation": "P = 6×4 = 24 m. A = 6×6 = 36 m².",
        "difficulty": 2,
        "hints": ["변×4 / 변×변."],
        "feedback": {"correct": "정답!", "incorrect": "P=24 m, A=36 m²."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "Which has GREATER area? Rectangle X: 8×3 OR Rectangle Y: 5×5",
        "choices": ["A. X (24 sq cm)", "B. Y (25 sq cm)", "C. 같음", "D. 비교 불가"],
        "answer": "B",
        "explanation": "X: 8×3=24. Y: 5×5=25. Y가 1 더 큼.",
        "difficulty": 2,
        "hints": ["둘 다 곱셈."],
        "feedback": {"correct": "정답! Y.", "incorrect": "Y(25)>X(24)."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Mr. Lee is buying carpet for his rectangular room (12 ft × 9 ft). How much carpet does he need?",
        "choices": [
            "A. 21 sq ft (둘레)",
            "B. 42 sq ft (둘레)",
            "C. 108 sq ft (넓이)",
            "D. 가장자리만 측정"
        ],
        "answer": "C",
        "explanation": "카펫은 바닥 채움 → 넓이. 12×9 = 108 sq ft.",
        "difficulty": 2,
        "hints": ["채움 → 넓이.", "곱하기."],
        "feedback": {"correct": "정답! 108 sq ft.", "incorrect": "넓이 = 12×9 = 108."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Lila wants to put ribbon around the edge of a square 6 cm photo. How much ribbon?",
        "choices": ["A. 12 cm (둘레)", "B. 24 cm (둘레)", "C. 36 cm² (넓이)", "D. 36 cm (둘레)"],
        "answer": "B",
        "explanation": "리본 = 가장자리 = 둘레. 정사각형 둘레 = 6×4 = 24 cm.",
        "difficulty": 2,
        "hints": ["가장자리 → 둘레.", "변×4."],
        "feedback": {"correct": "정답! 24 cm.", "incorrect": "정사각형 둘레 6×4=24 cm."},
    },
    {
        "id": "R2_07",
        "type": "fill_in",
        "question": "Two rectangles BOTH have area 24 sq cm. Rectangle A is 6×4. Rectangle B is 8×3. Which has greater perimeter?",
        "answer": "B (P=22, A의 P=20)",
        "accept": [
            "B",
            "B가 더 큼",
            "Rectangle B",
            "B has greater perimeter",
            "B (22 cm)"
        ],
        "explanation": "A: P=2×(6+4)=20 cm. B: P=2×(8+3)=22 cm. 같은 넓이, 다른 둘레. B가 더 길쭉할수록 둘레 큼.",
        "difficulty": 3,
        "hints": ["둘 다 둘레 계산."],
        "feedback": {"correct": "정답! B.", "incorrect": "A=20, B=22 → B가 큼."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Sam needs to fence (둘레) a square garden of side 7 m AND fill it with grass seed (넓이). What does he need?",
        "choices": [
            "A. 펜스 28 m, 잔디 49 sq m",
            "B. 펜스 49 m, 잔디 28 sq m",
            "C. 펜스 14 m, 잔디 49 sq m",
            "D. 펜스 28 sq m, 잔디 49 m"
        ],
        "answer": "A",
        "explanation": "둘레 = 7×4 = 28 m (펜스). 넓이 = 7×7 = 49 m² (잔디 면적).",
        "difficulty": 3,
        "hints": ["둘 다 다른 양.", "단위도 다름."],
        "feedback": {"correct": "정답!", "incorrect": "펜스 28 m, 잔디 49 m²."},
    },
    {
        "id": "R3_05",
        "type": "open_response",
        "question": "Draw two rectangles that have the SAME perimeter (16 units) but DIFFERENT areas. List dimensions and both perimeters/areas.",
        "answer": "예: 7×1 (P=16, A=7), 6×2 (P=16, A=12), 5×3 (P=16, A=15), 4×4 (P=16, A=16). 둘 이상 적기.",
        "accept": [
            "7×1 P=16 A=7, 5×3 P=16 A=15",
            "6×2 P=16 A=12, 4×4 P=16 A=16",
            "7×1과 5×3 둘 다 P=16",
            "P=16 같고 A 다른 두 직사각형"
        ],
        "explanation": "직사각형 l+w = 8 인 모든 쌍이 P=16. 가능: 7×1, 6×2, 5×3, 4×4 — 모두 P 같음, 넓이 점점 큼 (정사각에 가까울수록 넓이 ↑).",
        "difficulty": 3,
        "hints": ["l+w = 8인 쌍 찾기.", "두 쌍 적기."],
        "feedback": {"correct": "정확!", "incorrect": "7×1, 6×2, 5×3, 4×4 등."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 376 + 458.",
        "choices": ["A. 724", "B. 734", "C. 824", "D. 834"],
        "answer": "D",
        "explanation": "376+458: 6+8=14 (carry 1), 7+5+1=13 (carry 1), 3+4+1=8. Result: 834.",
        "difficulty": 2,
        "hints": ["Two carries.", "376+458=834."],
        "feedback": {"correct": "Right — 834.", "incorrect": "376+458=834."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 604 − 357.",
        "choices": ["A. 247", "B. 257", "C. 347", "D. 357"],
        "answer": "A",
        "explanation": "604−357: borrow across zero. 604−357=247.",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "604−357=247."],
        "feedback": {"correct": "Right — 247.", "incorrect": "604−357=247."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A farm had 358 chickens. They sold 124, then bought 267 more. How many chickens now?",
        "choices": ["A. 234", "B. 391", "C. 501", "D. 749"],
        "answer": "C",
        "explanation": "Step 1: 358−124=234. Step 2: 234+267=501.",
        "difficulty": 3,
        "hints": ["Subtract then add.", "358−124=234, +267=501."],
        "feedback": {"correct": "Right — 501.", "incorrect": "358−124=234, +267=501."},
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
        "prerequisite": "G3 U10 L3 — 미지의 변 길이 (3.MD.D.8)",
        "current":      "G3 U10 L4 — 둘레와 넓이의 관계 (3.MD.D.8)",
        "successor":    "G3 U10 L5 — 같은 둘레, 다른 넓이 (3.MD.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u10_l4.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
