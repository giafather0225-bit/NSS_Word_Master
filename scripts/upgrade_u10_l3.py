"""
G3 U10 L3 — Unknown Side Lengths 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.MD.D.8 (둘레로부터 미지의 변 구하기 — 역방향 추론)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U10_perimeter/L3_unknown_side_lengths.json"

ID_PREFIX_MAP = {
    "c10_l3_pre_":   "PT_",
    "c10_l3_learn_": "LEARN_",
    "c10_l3_try_":   "TRY_",
    "c10_l3_pr1_":   "R1_",
    "c10_l3_pr2_":   "R2_",
    "c10_l3_pr3_":   "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.MD.D.8.M06"] for i in range(1, 6)},
    **{f"LEARN_0{i}": [] for i in range(1, 9)},
    **{f"TRY_0{i}": ["3.MD.D.8.M06"] for i in range(1, 6)},
    **{f"R1_{i:02d}": ["3.MD.D.8.M06"] for i in range(1, 11)},
    **{f"R2_0{i}": ["3.MD.D.8.M06"] for i in range(1, 8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.MD.D.8.M06"] for i in range(1, 6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "unknown_side" for i in range(1, 6)},
    "LEARN_01": "subtract_known_sides",
    "LEARN_02": "rectangle_unknown",
    "LEARN_03": "square_unknown",
    "LEARN_04": "two_step_routine",
    "LEARN_05": "verify_by_addition",
    "LEARN_06": "irregular_unknown",
    "LEARN_07": "common_pitfall_M06",
    "LEARN_08": "real_world_unknown",
    **{f"TRY_0{i}": "unknown_side" for i in range(1, 6)},
    **{f"R1_{i:02d}": "unknown_side" for i in range(1, 11)},
    **{f"R2_0{i}": "unknown_side_word" for i in range(1, 8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "unknown_side_complex" for i in range(1, 6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1, 6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract", "LEARN_06": "pictorial",
    "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1, 6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R3_0{i}": "abstract" for i in range(1, 6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Lesson 10.3 'Find Unknown Side Lengths' pp.421-424",
        "procedure_source": "EngageNY Grade 3 Module 7 Lesson 18 — Unknown Side Lengths",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


LEARN_TITLE_MAP = {
    "LEARN_01": "미지의 변 — 알려진 변을 빼기",
    "LEARN_02": "직사각형 — 가로 알면 세로 구하기",
    "LEARN_03": "정사각형 — 둘레 ÷ 4",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "미지의 변"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "unknown_side"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "unknown_side",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "unknown_side")
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
        "title": "2단계 루틴 — 직사각형 미지 변",
        "content": (
            "직사각형 둘레와 가로(또는 세로) 알 때 나머지 구하기: "
            "  단계 1) 둘레 − (아는 변 × 2) = 모르는 두 변의 합. "
            "  단계 2) 그 합 ÷ 2 = 모르는 변 1개. "
            "예: P=20, l=6 → 20−12=8 → 8÷2=4. w=4. "
            "🔍 핵심: 직사각형은 마주 보는 변이 같으므로 같은 변 2개가 남음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_step_routine",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "검산 — 다시 더해서 둘레 확인",
        "content": (
            "미지의 변을 구한 후 모든 변을 다시 더해 둘레와 같은지 확인. "
            "예: P=20, l=6, w=4 (구한 값) → 6+4+6+4 = 20 ✓. "
            "🔍 다르면 어딘가 계산 오류. 검산 습관은 답의 신뢰도를 높임."
        ),
        "cpa_stage": "abstract",
        "visual_type": "verify_addition",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "삼각형/오각형 — 알려진 모든 변 빼기",
        "content": (
            "삼각형: P − (아는 두 변) = 세 번째 변. "
            "예: P=24, sides 9, 7, ? → 24−9−7 = 8. "
            "오각형도 같은 원리: P − (아는 4변) = 다섯 번째 변. "
            "예: P=30, sides 4, 6, 5, 7, ? → 30−(4+6+5+7) = 30−22 = 8."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "irregular_unknown",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "흔한 함정 — 더하면 안 됨 (M06)",
        "content": (
            "❌ 잘못된 풀이: 둘레 + 아는 변 → 더 커짐. "
            "예: P=20, l=6, w=? → 20+6=26 (잘못!). "
            "✅ 올바름: P − 아는 변 = 모르는 변 합. "
            "🔍 직관: 둘레는 모든 변의 합 → 아는 부분을 빼면 모르는 부분이 남음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "common_pitfall",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "실생활 — 펜스/액자 미지 변",
        "content": (
            "실생활 예: 직사각형 마당, 펜스 36 m. 가로가 12 m라면 세로는? "
            "  36 − 24 = 12 → 12÷2 = 6 m 세로. "
            "🔍 검산: 12+6+12+6 = 36 m ✓. "
            "단위 통일 잊지 말기 (M03 방지)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "real_world_unknown",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "fill_in",
        "question": "A rectangle has P = 30 m and l = 9 m. What is w?",
        "answer": "6 m",
        "accept": ["6", "6 m"],
        "explanation": "30 − 18 = 12 → 12 ÷ 2 = 6 m.",
        "difficulty": 2,
        "hints": ["P − 2l 먼저, 그 후 ÷2."],
        "feedback": {"correct": "정답! 6 m.", "incorrect": "30−18=12, 12÷2=6 m."},
    },
    {
        "id": "TRY_05",
        "type": "fill_in",
        "question": "A pentagon has perimeter 35 cm. Four sides are 6, 8, 5, and 7 cm. What is the fifth side?",
        "answer": "9 cm",
        "accept": ["9", "9 cm"],
        "explanation": "35 − (6+8+5+7) = 35 − 26 = 9 cm.",
        "difficulty": 2,
        "hints": ["아는 4변 더한 후 빼기."],
        "feedback": {"correct": "정답! 9 cm.", "incorrect": "35−26 = 9 cm."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "fill_in",
        "question": "A square has perimeter 36 m. What is one side?",
        "answer": "9 m",
        "accept": ["9", "9 m"],
        "explanation": "36 ÷ 4 = 9 m.",
        "difficulty": 1,
        "hints": ["P ÷ 4."],
        "feedback": {"correct": "정답! 9 m.", "incorrect": "36÷4 = 9."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "A rectangle has P = 26 cm and w = 5 cm. What is l?",
        "answer": "8 cm",
        "accept": ["8", "8 cm"],
        "explanation": "26 − 10 = 16 → 16 ÷ 2 = 8 cm.",
        "difficulty": 2,
        "hints": ["P − 2w 먼저."],
        "feedback": {"correct": "정답! 8 cm.", "incorrect": "26−10=16, 16÷2=8."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "A triangle has perimeter 22 in. Two sides are 8 in and 6 in. What is the third side?",
        "choices": ["A. 6 in", "B. 7 in", "C. 8 in", "D. 14 in"],
        "answer": "C",
        "explanation": "22 − 8 − 6 = 8 in.",
        "difficulty": 2,
        "hints": ["P − 두 변."],
        "feedback": {"correct": "정답! 8 in.", "incorrect": "22−8−6=8 in."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Mark's rectangular garden has perimeter 40 ft. The length is 12 ft. What is the width?",
        "choices": ["A. 4 ft", "B. 8 ft", "C. 14 ft", "D. 28 ft"],
        "answer": "B",
        "explanation": "40 − (12×2) = 40 − 24 = 16 → 16 ÷ 2 = 8 ft.",
        "difficulty": 2,
        "hints": ["P − 2l → ÷ 2."],
        "feedback": {"correct": "정답! 8 ft.", "incorrect": "40−24=16, 16÷2=8 ft."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "A square pool has perimeter 32 m. What is one side?",
        "choices": ["A. 4 m", "B. 6 m", "C. 8 m", "D. 16 m"],
        "answer": "C",
        "explanation": "32 ÷ 4 = 8 m.",
        "difficulty": 1,
        "hints": ["P ÷ 4."],
        "feedback": {"correct": "정답! 8 m.", "incorrect": "32÷4=8."},
    },
    {
        "id": "R2_07",
        "type": "fill_in",
        "question": "A quadrilateral (4 sides) has perimeter 25 cm. Three sides are 5, 7, and 6 cm. What is the fourth side?",
        "answer": "7 cm",
        "accept": ["7", "7 cm"],
        "explanation": "25 − (5+7+6) = 25 − 18 = 7 cm.",
        "difficulty": 2,
        "hints": ["3변 더한 후 빼기."],
        "feedback": {"correct": "정답! 7 cm.", "incorrect": "25−18=7 cm."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "A rectangular yard has perimeter 50 ft. The length is 15 ft. Lily computes the width as 50 − 15 = 35 ft. What's wrong?",
        "choices": [
            "A. 그녀는 P + l 연산을 해야 함",
            "B. 그녀는 길이를 두 번 빼고 ÷2 해야 함 (M06)",
            "C. 50과 15를 더해야 함",
            "D. 정답이 맞음"
        ],
        "answer": "B",
        "explanation": "직사각형은 가로 2개 + 세로 2개. 정답: 50 − (15×2) = 20 → 20÷2 = 10 ft. M06 함정.",
        "difficulty": 3,
        "hints": ["변이 4개임을 잊었음.", "마주 보는 변 같음."],
        "feedback": {"correct": "정확! 10 ft.", "incorrect": "50−30=20, 20÷2=10 ft."},
    },
    {
        "id": "R3_05",
        "type": "open_response",
        "question": "A hexagon has perimeter 42 cm. Five of its sides are 6, 8, 5, 9, and 7 cm. Find the sixth side and verify your answer.",
        "answer": "여섯 번째 변 = 7 cm. 검산: 6+8+5+9+7+7 = 42 cm ✓",
        "accept": [
            "7 cm. 검산 6+8+5+9+7+7=42",
            "42 − 35 = 7 cm",
            "여섯 번째 = 7 cm",
            "7 cm — 모든 변 합 42"
        ],
        "explanation": "5변 합 = 6+8+5+9+7 = 35. 여섯 번째 = 42−35 = 7 cm. 검산: 35+7 = 42 ✓.",
        "difficulty": 3,
        "hints": ["5변 합 먼저.", "P − 5변 합."],
        "feedback": {"correct": "정확! 7 cm + 검산.", "incorrect": "42−35 = 7 cm."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 489 + 256.",
        "choices": ["A. 635", "B. 645", "C. 735", "D. 745"],
        "answer": "D",
        "explanation": "489+256: 9+6=15 (carry 1), 8+5+1=14 (carry 1), 4+2+1=7. Result: 745.",
        "difficulty": 2,
        "hints": ["Two carries.", "489+256=745."],
        "feedback": {"correct": "Right — 745.", "incorrect": "489+256=745."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 503 − 287.",
        "choices": ["A. 216", "B. 224", "C. 316", "D. 326"],
        "answer": "A",
        "explanation": "503−287: borrow across zero. 503−287=216.",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "503−287=216."],
        "feedback": {"correct": "Right — 216.", "incorrect": "503−287=216."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school store had 612 pencils. They sold 248, then received 175. How many pencils now?",
        "choices": ["A. 189", "B. 364", "C. 539", "D. 685"],
        "answer": "C",
        "explanation": "Step 1: 612−248=364. Step 2: 364+175=539.",
        "difficulty": 3,
        "hints": ["Subtract then add.", "612−248=364, 364+175=539."],
        "feedback": {"correct": "Right — 539.", "incorrect": "612−248=364, +175=539."},
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
        "prerequisite": "G3 U10 L2 — 둘레 구하기 (3.MD.D.8)",
        "current":      "G3 U10 L3 — 미지의 변 길이 구하기 (3.MD.D.8)",
        "successor":    "G3 U10 L4 — 둘레와 넓이의 관계 (3.MD.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u10_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
