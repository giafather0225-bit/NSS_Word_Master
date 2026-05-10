"""
G3 U8 L8 — Find Part of Group Using Unit Fractions 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.1 (1/b of N = N÷b — 단위분수로 그룹 일부 찾기)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L8_find_part_of_group_using_unit_fractions.json"

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
    **{f"PT_0{i}": "unit_fraction_of_group" for i in range(1,6)},
    "LEARN_01": "unit_fraction_of_group_intro",
    "LEARN_02": "equal_groups_method",
    "LEARN_03": "division_connection",
    "LEARN_04": "division_formula",
    "LEARN_05": "verify_with_multiplication",
    "LEARN_06": "find_part_routine",
    "LEARN_07": "smaller_b_larger_part",
    "LEARN_08": "word_problem_strategy",
    **{f"TRY_0{i}": "unit_fraction_of_group" for i in range(1,6)},
    **{f"R1_{i:02d}": "unit_fraction_of_group" for i in range(1,11)},
    **{f"R2_0{i}": "unit_fraction_of_group" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "unit_fraction_of_group" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.8 'Find Part of a Group Using Unit Fractions' pp.341-344",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic E — Equivalent Fractions",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "unit_fraction_of_group")
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
        "title": "1/b of N = N ÷ b — 핵심 공식",
        "content": (
            "그룹의 단위분수 1/b만큼은 전체 N을 b로 나눈 값. "
            "  1/2 of 12 = 12 ÷ 2 = 6 "
            "  1/3 of 15 = 15 ÷ 3 = 5 "
            "  1/4 of 20 = 20 ÷ 4 = 5 "
            "🔍 핵심: 분수 of 그룹 = 나눗셈."
        ),
        "cpa_stage": "abstract",
        "visual_type": "division_formula",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "곱셈으로 검산 — 답 × b = N",
        "content": (
            "1/b of N의 답을 b번 모으면 다시 전체 N이 되어야 함. "
            "  1/3 of 15 = 5 → 5 × 3 = 15 ✓ "
            "  1/4 of 20 = 5 → 5 × 4 = 20 ✓ "
            "🔍 검산 단계: 답을 분모로 곱했을 때 원래 N과 같은가?"
        ),
        "cpa_stage": "abstract",
        "visual_type": "verify_multiplication",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "일부 찾기 3단계 루틴",
        "content": (
            "1/b of N 풀이 3단계: "
            "  단계 1) 전체 N과 분모 b 확인. "
            "  단계 2) N ÷ b 계산. "
            "  단계 3) 답을 단위와 함께 적기 (예: 5 학생). "
            "예: 24 사탕의 1/4 → 1) N=24, b=4 → 2) 24÷4=6 → 3) 6 사탕."
        ),
        "cpa_stage": "abstract",
        "visual_type": "find_part_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "분모 작을수록 더 큰 부분",
        "content": (
            "같은 N에서 분모가 작을수록 한 부분이 더 큼. "
            "  1/2 of 12 = 6 (큼) "
            "  1/3 of 12 = 4 (중간) "
            "  1/4 of 12 = 3 (작음) "
            "🔍 직관: 적게 나누면 한 조각이 큼, 많이 나누면 작아짐. "
            "흔한 실수: 분모가 크면 답도 크다고 생각 — 실제는 반대."
        ),
        "cpa_stage": "abstract",
        "visual_type": "smaller_b_larger_part",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "문장제 전략 — 'of'를 ÷로 변환",
        "content": (
            "단어 신호 'of'는 단위분수 문장제에서 나눗셈 신호. "
            "  '24의 1/3' → 24 ÷ 3 = 8 "
            "  '20의 1/5' → 20 ÷ 5 = 4 "
            "🔍 검산: 답 × b = 원래 N? "
            "흔한 실수 (M04): 분모를 곱함 (24×3=72) — 'of'는 곱이 아니라 나눗셈."
        ),
        "cpa_stage": "abstract",
        "visual_type": "word_problem_strategy",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "What is 1/3 of 12?",
        "choices": ["A. 3", "B. 4", "C. 6", "D. 9"],
        "answer": "B",
        "explanation": "12 ÷ 3 = 4.",
        "difficulty": 1,
        "hints": ["12÷3."],
        "feedback": {"correct": "정답! 4.", "incorrect": "12÷3=4."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "What is 1/5 of 20?",
        "choices": ["A. 4", "B. 5", "C. 15", "D. 20"],
        "answer": "A",
        "explanation": "20 ÷ 5 = 4.",
        "difficulty": 1,
        "hints": ["20÷5."],
        "feedback": {"correct": "정답! 4.", "incorrect": "20÷5=4."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "There are 18 cookies. 1/6 are oatmeal. How many are oatmeal?",
        "choices": ["A. 2", "B. 3", "C. 6", "D. 12"],
        "answer": "B",
        "explanation": "18 ÷ 6 = 3.",
        "difficulty": 2,
        "hints": ["18÷6."],
        "feedback": {"correct": "정답! 3.", "incorrect": "18÷6=3."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "What is 1/5 of 25?",
        "choices": ["A. 4", "B. 5", "C. 20", "D. 25"],
        "answer": "B",
        "explanation": "25÷5=5.",
        "difficulty": 1,
        "hints": ["25÷5."],
        "feedback": {"correct": "정답!", "incorrect": "25÷5=5."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "What is 1/7 of 14?",
        "choices": ["A. 2", "B. 7", "C. 12", "D. 14"],
        "answer": "A",
        "explanation": "14÷7=2.",
        "difficulty": 1,
        "hints": ["14÷7."],
        "feedback": {"correct": "정답! 2.", "incorrect": "14÷7=2."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "What is 1/9 of 27?",
        "choices": ["A. 3", "B. 9", "C. 18", "D. 27"],
        "answer": "A",
        "explanation": "27÷9=3.",
        "difficulty": 2,
        "hints": ["27÷9."],
        "feedback": {"correct": "정답! 3.", "incorrect": "27÷9=3."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Compare: 1/3 of 18 vs 1/6 of 18. Which is larger?",
        "choices": ["A. 1/3 of 18", "B. 1/6 of 18", "C. 같음", "D. 알 수 없음"],
        "answer": "A",
        "explanation": "1/3 of 18 = 6, 1/6 of 18 = 3. 6 > 3.",
        "difficulty": 2,
        "hints": ["분모가 작을수록 더 큼."],
        "feedback": {"correct": "정답! 1/3 of 18 = 6.", "incorrect": "6 > 3 → 1/3 더 큼."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Mei has 28 stamps. 1/4 are foreign. Verify: how many foreign, and does 4 × answer = 28?",
        "choices": ["A. 7 foreign, 4×7=28 ✓", "B. 4 foreign, 4×4=16 ✗", "C. 8 foreign, 4×8=32 ✗", "D. 24 foreign"],
        "answer": "A",
        "explanation": "28÷4=7. 검산 4×7=28.",
        "difficulty": 2,
        "hints": ["28÷4=7. 7×4=28?"],
        "feedback": {"correct": "정답!", "incorrect": "28÷4=7, 검산 4×7=28."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "Tom says 1/4 of 16 = 64 because 16 × 4 = 64. What is wrong?",
        "choices": [
            "A. 'of'는 ÷ 신호, 곱셈 아님 → 16÷4=4",
            "B. 답이 너무 작다",
            "C. 16과 4는 약수 관계가 아님",
            "D. 정답"
        ],
        "answer": "A",
        "explanation": "1/b of N = N÷b. 16÷4=4.",
        "difficulty": 3,
        "hints": ["of = ÷ (단위분수에서)."],
        "feedback": {"correct": "정답!", "incorrect": "of = 나눗셈 → 16÷4=4."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "A library has 36 books. 1/4 are children's books and 1/6 are reference. How many are NEITHER?",
        "choices": ["A. 12", "B. 15", "C. 21", "D. 24"],
        "answer": "C",
        "explanation": "어린이 = 36÷4=9. 참고 = 36÷6=6. 둘 다 아님 = 36−9−6=21.",
        "difficulty": 3,
        "hints": ["각 부분 계산 후 빼기."],
        "feedback": {"correct": "정답! 21.", "incorrect": "36−9−6=21."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "Lia bakes 24 cookies. She gives 1/3 to her brother and 1/4 to her sister. How many does she keep?",
        "choices": ["A. 6", "B. 8", "C. 10", "D. 14"],
        "answer": "C",
        "explanation": "동생 = 24÷3=8. 자매 = 24÷4=6. 남은 = 24−8−6=10.",
        "difficulty": 3,
        "hints": ["각각 계산 후 빼기."],
        "feedback": {"correct": "정답! 10.", "incorrect": "24−8−6=10."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 459 + 286.",
        "choices": ["A. 635", "B. 645", "C. 735", "D. 745"],
        "answer": "D",
        "explanation": "459+286: 9+6=15 (carry 1), 5+8+1=14 (carry 1), 4+2+1=7. Result: 745.",
        "difficulty": 2,
        "hints": ["Two carries.", "459+286=745."],
        "feedback": {"correct": "Right — 745.", "incorrect": "459+286=745."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 706 − 358.",
        "choices": ["A. 348", "B. 358", "C. 448", "D. 458"],
        "answer": "A",
        "explanation": "706−358=348 (borrow across zero).",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "706−358=348."],
        "feedback": {"correct": "Right — 348.", "incorrect": "706−358=348."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A store had 583 toys. They sold 246, then received 178 more. How many toys now?",
        "choices": ["A. 337", "B. 415", "C. 515", "D. 651"],
        "answer": "C",
        "explanation": "Step 1: 583−246=337. Step 2: 337+178=515.",
        "difficulty": 3,
        "hints": ["Subtract sold, add received.", "583−246=337, 337+178=515."],
        "feedback": {"correct": "Right — 515 toys.", "incorrect": "583−246=337, then +178=515."},
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
        "prerequisite": "G3 U8 L7 — 그룹의 분수 (3.NF.A.1)",
        "current":      "G3 — 단위분수로 그룹의 일부 찾기: 1/b of N = N÷b (3.NF.A.1)",
        "successor":    "G3 U8 L9 — 부분으로 전체 그룹 찾기 (3.NF.A.1)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l8.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
