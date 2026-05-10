"""
G3 U8 L7 — Fractions of a Group 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.1 (그룹의 분수 — 전체 N개 중 a개 = a/N)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L7_fractions_of_a_group.json"

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
    **{f"PT_0{i}": "fraction_of_group" for i in range(1,6)},
    "LEARN_01": "group_fraction_intro",
    "LEARN_02": "find_numerator_count",
    "LEARN_03": "part_not_described",
    "LEARN_04": "denominator_total_count",
    "LEARN_05": "fractions_sum_to_one",
    "LEARN_06": "group_routine",
    "LEARN_07": "complement_rule",
    "LEARN_08": "verify_group_fraction",
    **{f"TRY_0{i}": "fraction_of_group" for i in range(1,6)},
    **{f"R1_{i:02d}": "fraction_of_group" for i in range(1,11)},
    **{f"R2_0{i}": "fraction_of_group" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "fraction_of_group" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,6)},
    **{f"R1_{i:02d}": "pictorial" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.7 'Fractions of a Group' pp.337-340",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "fraction_of_group")
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
        "title": "분모 = 그룹 전체 개수",
        "content": (
            "그룹의 분수 a/b에서 분모 b는 전체 물건 개수. "
            "예: 8개 사탕 중 3개가 빨강 → 빨강 분수 = 3/8 (분모는 항상 8). "
            "흔한 실수 (M04): 빨강이 3개니까 '3/3'이라고 적음 — "
            "전체 개수(8)를 잊음. 항상 '전체가 몇 개?' 먼저 묻기."
        ),
        "cpa_stage": "abstract",
        "visual_type": "denominator_total",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "부분의 합 = 1 (전체)",
        "content": (
            "그룹의 모든 부분 분수를 더하면 1이 됨. "
            "예: 6개 구슬 = 빨강 2/6 + 파랑 1/6 + 노랑 3/6 = 6/6 = 1. "
            "🔍 검산: 모든 색의 분수를 더해 b/b가 나오면 정답. "
            "다르면 어딘가 빠뜨림."
        ),
        "cpa_stage": "abstract",
        "visual_type": "fractions_sum_to_one",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "그룹 분수 3단계 루틴",
        "content": (
            "그룹의 분수를 적을 때 3단계: "
            "  단계 1) 전체 개수를 센다 → 분모. "
            "  단계 2) 조건에 맞는 개수를 센다 → 분자. "
            "  단계 3) 분자/분모 형태로 적는다. "
            "예: 8 꽃 중 5 빨강 → 1) 분모 8, 2) 분자 5, 3) 5/8."
        ),
        "cpa_stage": "abstract",
        "visual_type": "group_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "여집합 — 빨강이 3/8이면 빨강 아닌 것은?",
        "content": (
            "한 부분의 분수를 알면 나머지(여집합)는 1에서 뺀 값. "
            "예: 빨강 = 3/8 → 빨강 아닌 것 = 8/8 − 3/8 = 5/8. "
            "예: 좋아함 = 2/6 → 안 좋아함 = 4/6. "
            "🔍 빠른 검산: 두 분수 합이 1 (b/b)인가?"
        ),
        "cpa_stage": "abstract",
        "visual_type": "complement_rule",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "검증 — 분자 ≤ 분모 항상 성립",
        "content": (
            "그룹 분수에서 분자는 분모를 넘을 수 없음 (전체보다 부분이 많을 수 없음). "
            "  분자 < 분모 → 일부 (예: 3/8) "
            "  분자 = 분모 → 전체 (예: 8/8 = 1) "
            "  분자 > 분모 → 그룹 분수에서는 불가능. "
            "예: 5개 사탕 중 7개가 빨강? 불가능. "
            "🔍 검산: 분자가 분모 이하인지 확인."
        ),
        "cpa_stage": "abstract",
        "visual_type": "verify_group_fraction",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "There are 8 fish in a tank. 5 are gold and 3 are silver. What fraction are gold?",
        "choices": ["A. 3/8", "B. 5/8", "C. 5/3", "D. 8/5"],
        "answer": "B",
        "explanation": "전체 8, 금 5 → 5/8.",
        "difficulty": 1,
        "hints": ["분모=전체, 분자=조건."],
        "feedback": {"correct": "정답! 5/8.", "incorrect": "5/8 (전체 8 중 5개 금)."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "A group of 6 puppies has 4 brown ones. What fraction is NOT brown?",
        "choices": ["A. 2/6", "B. 4/6", "C. 6/2", "D. 6/4"],
        "answer": "A",
        "explanation": "갈색 아닌 것 = 6 − 4 = 2. → 2/6.",
        "difficulty": 2,
        "hints": ["여집합 = 1 − 4/6 = 2/6."],
        "feedback": {"correct": "정답! 2/6.", "incorrect": "6−4=2 → 2/6."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "There are 5 books: 2 are fiction, 3 are non-fiction. What fraction are fiction?",
        "choices": ["A. 2/3", "B. 2/5", "C. 3/5", "D. 5/2"],
        "answer": "B",
        "explanation": "전체 5, 소설 2 → 2/5.",
        "difficulty": 1,
        "hints": ["분모=5, 분자=2."],
        "feedback": {"correct": "정답! 2/5.", "incorrect": "2/5."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "There are 10 stickers: 7 are stars, 3 are hearts. What fraction are hearts?",
        "choices": ["A. 3/7", "B. 3/10", "C. 7/10", "D. 10/3"],
        "answer": "B",
        "explanation": "전체 10, 하트 3 → 3/10.",
        "difficulty": 1,
        "hints": ["3/10."],
        "feedback": {"correct": "정답!", "incorrect": "3/10."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "A group of 5 birds has 5 sparrows. What fraction are sparrows?",
        "choices": ["A. 0/5", "B. 1/5", "C. 5/5", "D. 5/0"],
        "answer": "C",
        "explanation": "모두가 참새 → 5/5 = 1.",
        "difficulty": 1,
        "hints": ["전체 = 분자."],
        "feedback": {"correct": "정답! 5/5.", "incorrect": "전체 = 5/5 = 1."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "There are 9 toys: 4 cars, 5 dolls. What fraction are cars?",
        "choices": ["A. 4/5", "B. 4/9", "C. 5/9", "D. 9/4"],
        "answer": "B",
        "explanation": "전체 9, 자동차 4 → 4/9.",
        "difficulty": 1,
        "hints": ["분모 9."],
        "feedback": {"correct": "정답! 4/9.", "incorrect": "4/9."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "A bag has 10 marbles: 4 red, 3 blue, 3 green. What fraction are NOT red?",
        "choices": ["A. 4/10", "B. 6/10", "C. 7/10", "D. 10/4"],
        "answer": "B",
        "explanation": "빨강 아닌 것 = 3+3 = 6 → 6/10.",
        "difficulty": 2,
        "hints": ["10 − 4 = 6.", "여집합 = 6/10."],
        "feedback": {"correct": "정답! 6/10.", "incorrect": "여집합 = 6/10."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Sam says 4/3 of his 3 toys are robots. Why is that impossible?",
        "choices": [
            "A. 분자가 분모보다 클 수 없음 (그룹 분수)",
            "B. 분수는 자연수여야 함",
            "C. 3 toys는 너무 적음",
            "D. 가능함"
        ],
        "answer": "A",
        "explanation": "전체 3개 중 4개일 수 없음.",
        "difficulty": 3,
        "hints": ["분자 ≤ 분모.", "전체보다 부분이 많을 수 없음."],
        "feedback": {"correct": "정답!", "incorrect": "분자 > 분모 → 불가능 (그룹 분수)."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "A class of 6 students: 1/6 brought lunch, 2/6 brought snacks, 3/6 brought neither. Verify the parts sum to 1.",
        "choices": [
            "A. 합 = 5/6 (오류)",
            "B. 합 = 6/6 = 1 (정확)",
            "C. 합 = 7/6 (오류)",
            "D. 합 = 3/6"
        ],
        "answer": "B",
        "explanation": "1/6 + 2/6 + 3/6 = 6/6 = 1.",
        "difficulty": 2,
        "hints": ["분자 모두 더하기."],
        "feedback": {"correct": "정답! 6/6 = 1.", "incorrect": "1+2+3=6 → 6/6=1."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "If 3/10 of the 10 students like pizza and 2/10 like pasta, what fraction likes neither?",
        "choices": ["A. 3/10", "B. 5/10", "C. 7/10", "D. 10/10"],
        "answer": "B",
        "explanation": "1 − 3/10 − 2/10 = 5/10.",
        "difficulty": 3,
        "hints": ["여집합 = 10/10 − 3/10 − 2/10."],
        "feedback": {"correct": "정답! 5/10.", "incorrect": "10−3−2=5 → 5/10."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "A box has 8 chocolates. Mia eats 3/8, then her brother eats 2/8. What fraction is left?",
        "choices": ["A. 2/8", "B. 3/8", "C. 5/8", "D. 6/8"],
        "answer": "B",
        "explanation": "8/8 − 3/8 − 2/8 = 3/8.",
        "difficulty": 3,
        "hints": ["남은 = 1 − 먹은 합."],
        "feedback": {"correct": "정답! 3/8.", "incorrect": "8−3−2=3 → 3/8."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 286 + 374.",
        "choices": ["A. 550", "B. 560", "C. 650", "D. 660"],
        "answer": "D",
        "explanation": "286+374: 6+4=10 (carry 1), 8+7+1=16 (carry 1), 2+3+1=6. Result: 660.",
        "difficulty": 2,
        "hints": ["Two carries.", "286+374=660."],
        "feedback": {"correct": "Right — 660.", "incorrect": "286+374=660."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 800 − 365.",
        "choices": ["A. 425", "B. 435", "C. 445", "D. 535"],
        "answer": "B",
        "explanation": "800−365=435 (borrow across both zeros).",
        "difficulty": 2,
        "hints": ["Borrow across zeros.", "800−365=435."],
        "feedback": {"correct": "Right — 435.", "incorrect": "800−365=435."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A farm had 478 chickens. They sold 156, then bought 234 more. How many chickens now?",
        "choices": ["A. 322", "B. 466", "C. 556", "D. 712"],
        "answer": "C",
        "explanation": "Step 1: 478−156=322. Step 2: 322+234=556.",
        "difficulty": 3,
        "hints": ["Subtract sold, add bought.", "478−156=322, 322+234=556."],
        "feedback": {"correct": "Right — 556 chickens.", "incorrect": "478−156=322, then +234=556."},
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
        "prerequisite": "G3 U8 L6 — 분수와 자연수 (3.NF.A.3c)",
        "current":      "G3 — 그룹의 분수: 전체 N개 중 a개 = a/N (3.NF.A.1)",
        "successor":    "G3 U8 L8 — 단위분수로 그룹의 일부 찾기 (3.NF.A.1)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l7.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
