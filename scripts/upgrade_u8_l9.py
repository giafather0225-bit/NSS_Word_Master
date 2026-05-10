"""
G3 U8 L9 — Problem Solving: Find Whole Group 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.1 (부분으로 전체 찾기 — 1/b of N = P → N = P × b)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L9_problem_solving_find_whole_group.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.1.M04"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    **{f"TRY_0{i}": ["3.NF.A.1.M04"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.1.M04"] for i in range(1,11)},
    **{f"R2_0{i}": ["3.NF.A.1.M04"] for i in range(1,8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.1.M04"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "find_whole_from_part" for i in range(1,6)},
    "LEARN_01": "part_to_whole_intro",
    "LEARN_02": "why_multiply",
    "LEARN_03": "check_answer",
    "LEARN_04": "multiplication_formula",
    "LEARN_05": "inverse_division",
    "LEARN_06": "find_whole_routine",
    "LEARN_07": "bar_model_part_whole",
    "LEARN_08": "word_problem_keyword",
    **{f"TRY_0{i}": "find_whole_from_part" for i in range(1,6)},
    **{f"R1_{i:02d}": "find_whole_from_part" for i in range(1,11)},
    **{f"R2_0{i}": "find_whole_from_part" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "find_whole_from_part" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.9 'Problem Solving: Find the Whole Group' pp.345-348",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic F — Comparison, Order, and Size of Fractions",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_item(item: dict) -> dict:
    item_id = item["id"]
    if item_id.startswith("LRN_"):
        item_id = f"LEARN_{item_id[4:]}"
        item["id"] = item_id
    elif item_id.startswith("LN_"):
        item_id = f"LEARN_{item_id[3:]}"
        item["id"] = item_id
    if item_id.startswith("LEARN_") and item.get("type") == "card":
        item["type"] = "concept_card"
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "find_whole_from_part")
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
        "title": "전체 = 부분 × b — 핵심 공식",
        "content": (
            "1/b of N = P이면 N = P × b. "
            "  1/3 of N = 6 → N = 6 × 3 = 18 "
            "  1/4 of N = 5 → N = 5 × 4 = 20 "
            "🔍 직관: 부분이 b개 모이면 전체가 됨."
        ),
        "cpa_stage": "abstract",
        "visual_type": "multiplication_formula",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "역연산 — 나눗셈의 반대",
        "content": (
            "L8에서 1/b of N = N÷b를 배웠음. "
            "이번에는 거꾸로: 부분 P를 알고 N을 찾기 → 곱하기. "
            "  N÷b = P (앞 단계) "
            "  N = P×b (역연산) "
            "검산: P × b의 답을 다시 b로 나누면 P가 되어야 함."
        ),
        "cpa_stage": "abstract",
        "visual_type": "inverse_division",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "전체 찾기 3단계 루틴",
        "content": (
            "부분 → 전체 풀이 3단계: "
            "  단계 1) 단위분수 1/b의 분모 b 확인. "
            "  단계 2) 부분 값 P 확인. "
            "  단계 3) N = P × b 계산. "
            "예: 1/4가 7이면 → 1) b=4, 2) P=7, 3) N=7×4=28."
        ),
        "cpa_stage": "abstract",
        "visual_type": "find_whole_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "막대 모델 — b개 칸으로 시각화",
        "content": (
            "1/b가 P이면 막대를 b개 칸으로 그리고 한 칸을 P로 표시. "
            "  예: 1/4 of N = 5 → [5][5][5][5] → N = 20 "
            "🔍 막대 모델은 곱셈을 시각적으로 보여줌. "
            "한 칸 × 칸 수 = 전체."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "bar_model",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "문장제 신호 — '~의 1/b가 P'",
        "content": (
            "문장 패턴: 'A의 1/b는 P이다 → A는?' "
            "  예: '학생의 1/3이 8명이면 전체는?' → 8 × 3 = 24명. "
            "  예: '돈의 1/5가 4달러면 전체는?' → 4 × 5 = 20달러. "
            "흔한 실수 (M04): 부분과 전체 혼동 — 'A의 1/b'에서 A가 전체임을 명심."
        ),
        "cpa_stage": "abstract",
        "visual_type": "word_problem_keyword",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "1/4 of a group is 6. How many are in the whole group?",
        "choices": ["A. 10", "B. 18", "C. 24", "D. 30"],
        "answer": "C",
        "explanation": "6 × 4 = 24.",
        "difficulty": 1,
        "hints": ["P×b = N.", "6×4=24."],
        "feedback": {"correct": "정답! 24.", "incorrect": "6×4=24."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "1/5 of the candies is 3. How many candies in all?",
        "choices": ["A. 8", "B. 12", "C. 15", "D. 18"],
        "answer": "C",
        "explanation": "3 × 5 = 15.",
        "difficulty": 1,
        "hints": ["3×5."],
        "feedback": {"correct": "정답! 15.", "incorrect": "3×5=15."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "1/7 of a number is 2. What is the number?",
        "choices": ["A. 9", "B. 14", "C. 21", "D. 28"],
        "answer": "B",
        "explanation": "2 × 7 = 14.",
        "difficulty": 2,
        "hints": ["2×7."],
        "feedback": {"correct": "정답! 14.", "incorrect": "2×7=14."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "1/3 of the apples is 4. How many apples are there?",
        "choices": ["A. 7", "B. 10", "C. 12", "D. 15"],
        "answer": "C",
        "explanation": "4×3=12.",
        "difficulty": 1,
        "hints": ["4×3."],
        "feedback": {"correct": "정답!", "incorrect": "4×3=12."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "1/5 of the marbles is 6. How many marbles are there?",
        "choices": ["A. 11", "B. 25", "C. 30", "D. 36"],
        "answer": "C",
        "explanation": "6×5=30.",
        "difficulty": 1,
        "hints": ["6×5."],
        "feedback": {"correct": "정답! 30.", "incorrect": "6×5=30."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "1/6 of a number is 7. What is the number?",
        "choices": ["A. 13", "B. 36", "C. 42", "D. 48"],
        "answer": "C",
        "explanation": "7×6=42.",
        "difficulty": 2,
        "hints": ["7×6."],
        "feedback": {"correct": "정답! 42.", "incorrect": "7×6=42."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Joe says 1/3 of his pencils is 6, so he has 6÷3=2 pencils. What is wrong?",
        "choices": [
            "A. 부분→전체일 때는 곱해야 함 → 6×3=18",
            "B. 답은 6/3=2가 맞음",
            "C. 분모를 빼야 함",
            "D. 정답"
        ],
        "answer": "A",
        "explanation": "부분 P를 알면 N = P×b. 6×3=18.",
        "difficulty": 3,
        "hints": ["부분→전체 = ×."],
        "feedback": {"correct": "정답!", "incorrect": "P×b=18 (부분→전체는 곱셈)."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Compare: A) 1/2 of N = 8. B) 1/4 of M = 8. Which is larger, N or M?",
        "choices": ["A. N (=16)", "B. M (=32)", "C. 같음", "D. 알 수 없음"],
        "answer": "B",
        "explanation": "N = 8×2 = 16, M = 8×4 = 32. M이 큼.",
        "difficulty": 3,
        "hints": ["각각 P×b 계산."],
        "feedback": {"correct": "정답! M=32.", "incorrect": "N=16, M=32."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "1/8 of the books is 3. Verify: total × 1/8 should equal 3. What is the total, and check with division.",
        "choices": [
            "A. 24, 24÷8=3 ✓",
            "B. 11, 11÷8 ≠ 3",
            "C. 16, 16÷8=2",
            "D. 32, 32÷8=4"
        ],
        "answer": "A",
        "explanation": "3×8=24. 검산 24÷8=3.",
        "difficulty": 2,
        "hints": ["3×8=24, 검산 24÷8=3."],
        "feedback": {"correct": "정답!", "incorrect": "24, 검산 24÷8=3."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "1/5 of a class is 4 students. The teacher splits the whole class into 2 equal teams. How many in each team?",
        "choices": ["A. 5", "B. 8", "C. 10", "D. 20"],
        "answer": "C",
        "explanation": "전체 = 4×5 = 20. 팀당 = 20÷2 = 10.",
        "difficulty": 3,
        "hints": ["전체 먼저, 그 다음 팀당.", "4×5=20, 20÷2=10."],
        "feedback": {"correct": "정답! 10.", "incorrect": "전체=20, 팀당=10."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "1/4 of Mia's beads is 7. She uses 1/2 of all her beads. How many does she use?",
        "choices": ["A. 7", "B. 14", "C. 21", "D. 28"],
        "answer": "B",
        "explanation": "전체 = 7×4 = 28. 사용 = 28×1/2 = 14.",
        "difficulty": 3,
        "hints": ["전체 먼저: 7×4=28."],
        "feedback": {"correct": "정답! 14.", "incorrect": "전체=28, 1/2=14."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 367 + 489.",
        "choices": ["A. 746", "B. 756", "C. 846", "D. 856"],
        "answer": "D",
        "explanation": "367+489: 7+9=16 (carry 1), 6+8+1=15 (carry 1), 3+4+1=8. Result: 856.",
        "difficulty": 2,
        "hints": ["Two carries.", "367+489=856."],
        "feedback": {"correct": "Right — 856.", "incorrect": "367+489=856."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 905 − 467.",
        "choices": ["A. 438", "B. 448", "C. 538", "D. 548"],
        "answer": "A",
        "explanation": "905−467=438 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "905−467=438."],
        "feedback": {"correct": "Right — 438.", "incorrect": "905−467=438."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A theater had 624 seats. They added 137 more, then removed 89. How many seats now?",
        "choices": ["A. 398", "B. 672", "C. 752", "D. 850"],
        "answer": "B",
        "explanation": "Step 1: 624+137=761. Step 2: 761−89=672.",
        "difficulty": 3,
        "hints": ["Add then subtract.", "624+137=761, 761−89=672."],
        "feedback": {"correct": "Right — 672 seats.", "incorrect": "624+137=761, then −89=672."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 업그레이드됨.")
        return

    nested = d.get("sections", {})
    sm = {
        "pretest": list(nested.get("pretest", [])),
        "learn": list(nested.get("learn", [])),
        "try": list(nested.get("try", [])),
        "practice_r1": list(nested.get("practice_r1", [])),
        "practice_r2": list(nested.get("practice_r2", [])),
        "practice_r3": list(nested.get("practice_r3", [])),
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
    if "sections" in d:
        del d["sections"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U8 L8 — 1/b of N = N÷b (3.NF.A.1)",
        "current":      "G3 — 부분으로 전체 찾기: 1/b of N = P → N = P×b (3.NF.A.1)",
        "successor":    "G3 U9 L1 — 분수 비교 시작 (3.NF.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l9.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
