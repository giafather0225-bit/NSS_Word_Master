"""
G3 U8 L5 — Fractions on a Number Line 7단계 재마이그레이션
==============================================================================
24개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.2 (수직선 위의 분수 — 0~1을 b등분, a/b 위치)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L5_fractions_on_a_number_line.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.2.M01"] for i in range(1,6)},
    **{f"LEARN_0{i}": [] for i in range(1,9)},
    **{f"TRY_0{i}": ["3.NF.A.2.M01"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.2.M01"] for i in range(1,11)},
    **{f"R2_0{i}": ["3.NF.A.2.M01"] for i in range(1,8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.2.M02"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "fraction_number_line" for i in range(1,6)},
    "LEARN_01": "number_line_intro",
    "LEARN_02": "locate_fraction",
    "LEARN_03": "endpoints_0_1",
    "LEARN_04": "count_jumps_method",
    "LEARN_05": "label_tickmarks",
    "LEARN_06": "denominator_partition",
    "LEARN_07": "fraction_distance_origin",
    "LEARN_08": "number_line_routine",
    **{f"TRY_0{i}": "fraction_number_line" for i in range(1,6)},
    **{f"R1_{i:02d}": "fraction_number_line" for i in range(1,11)},
    **{f"R2_0{i}": "fraction_number_line" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "fraction_number_line" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "pictorial",
    "LEARN_06": "abstract", "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "pictorial" for i in range(1,6)},
    **{f"R1_{i:02d}": "pictorial" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.5 'Fractions on a Number Line' pp.329-332",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic C — Comparing Unit Fractions and Specifying the Whole",
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
        item["cpa_stage"] = CPA_MAP.get(item_id, "pictorial")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "fraction_number_line")
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
        "title": "점프 세기 방법 — 0에서 출발",
        "content": (
            "수직선에서 a/b를 찾으려면: 0에서 출발해 1/b씩 a번 점프한다. "
            "예: 3/4 → 0에서 1/4씩 3번 점프 → 3번째 눈금. "
            "예: 5/6 → 0에서 1/6씩 5번 점프 → 5번째 눈금. "
            "🔍 핵심: 분자 a = 점프 횟수, 분모 b = 점프 한 번의 크기."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "count_jumps",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "눈금에 라벨 붙이기 — 0/b부터 b/b까지",
        "content": (
            "0~1을 b등분하면 b+1개의 눈금이 생김. "
            "왼쪽부터 0/b, 1/b, 2/b, …, b/b (=1). "
            "예: 4등분 → 0/4, 1/4, 2/4, 3/4, 4/4. "
            "끝점 0 = 0/b, 끝점 1 = b/b. "
            "흔한 실수 (M01): 칸 수와 눈금 수 혼동 — 칸이 b개면 눈금은 b+1개."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "label_tickmarks",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "분모는 칸 수 — 0~1을 몇 등분?",
        "content": (
            "분모 b는 0과 1 사이를 몇 칸으로 나눴는지 알려줌. "
            "분모 4 → 4칸 / 분모 6 → 6칸 / 분모 8 → 8칸. "
            "분모가 클수록 한 칸의 길이는 짧고, 같은 거리를 가는 데 더 많은 점프가 필요. "
            "🔍 빠른 검산: 1까지 b번 점프했는가?"
        ),
        "cpa_stage": "abstract",
        "visual_type": "denominator_partition",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "분수 = 0에서의 거리",
        "content": (
            "수직선 위의 a/b는 단순한 점이 아니라 '0에서 그 점까지의 거리'를 의미. "
            "예: 3/4는 0에서 출발해 전체 길이의 3/4만큼 떨어진 위치. "
            "이 관점은 분수 비교에도 도움 — 0에서 더 멀면 더 큰 분수. "
            "예: 3/4 > 2/4 (3/4가 0에서 더 멀리 있음)."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "fraction_distance",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "수직선 분수 3단계 루틴",
        "content": (
            "낯선 분수 a/b를 수직선에 표시할 때 3단계: "
            "  단계 1) 0과 1 사이를 분모 b만큼 같은 칸으로 나눈다. "
            "  단계 2) 0부터 시작해 분자 a번 점프한다. "
            "  단계 3) a번째 눈금이 a/b의 위치. "
            "예: 5/8 → 8칸으로 나누고 5번째 눈금. "
            "흔한 실수 (M02): 분모 만큼 칸으로 나누지 않고 자기 마음대로 — "
            "반드시 같은 길이로 b등분 했는지 검증."
        ),
        "cpa_stage": "abstract",
        "visual_type": "number_line_routine",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_03",
        "type": "MC",
        "question": "A number line from 0 to 1 is divided into 6 equal parts. Where is 4/6 located?",
        "choices": ["A. The 2nd tick from 0", "B. The 3rd tick from 0", "C. The 4th tick from 0", "D. The 5th tick from 0"],
        "answer": "C",
        "explanation": "분모 6 → 6등분. 분자 4 → 0에서 1/6씩 4번 점프. 4번째 눈금.",
        "difficulty": 2,
        "hints": ["1/6씩 점프.", "분자가 점프 횟수."],
        "feedback": {"correct": "정답! 4번째 눈금.", "incorrect": "분자만큼 점프하면 4번째."},
    },
    {
        "id": "TRY_04",
        "type": "MC",
        "question": "On a number line from 0 to 1 divided into 4 equal parts, what fraction is at the 4th tick from 0?",
        "choices": ["A. 1/4", "B. 3/4", "C. 4/4", "D. 4/3"],
        "answer": "C",
        "explanation": "오른쪽 끝점 = 1 = 4/4.",
        "difficulty": 1,
        "hints": ["4번째 눈금은 끝점 1.", "분자/분모가 같으면 1."],
        "feedback": {"correct": "정답! 4/4 = 1.", "incorrect": "끝점 1 = 4/4."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "A number line from 0 to 1 has 3 equal parts. Where is 2/3?",
        "choices": ["A. The 1st tick", "B. The 2nd tick", "C. The 3rd tick", "D. Beyond 1"],
        "answer": "B",
        "explanation": "0에서 1/3씩 2번 → 2번째 눈금.",
        "difficulty": 1,
        "hints": ["1/3씩 2번 점프."],
        "feedback": {"correct": "정답! 2번째 눈금.", "incorrect": "분자=2, 즉 2번 점프."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "MC",
        "question": "A number line from 0 to 1 is divided into 8 equal parts. Where is 5/8?",
        "choices": ["A. 4번째 눈금", "B. 5번째 눈금", "C. 6번째 눈금", "D. 8번째 눈금"],
        "answer": "B",
        "explanation": "분자 5 → 0에서 1/8씩 5번 점프 → 5번째 눈금.",
        "difficulty": 2,
        "hints": ["1/8씩 5번."],
        "feedback": {"correct": "정답! 5번째.", "incorrect": "분자=5번 점프."},
    },
    {
        "id": "R1_09",
        "type": "MC",
        "question": "What fraction names 1 on a number line divided into 6 equal parts (using sixths)?",
        "choices": ["A. 0/6", "B. 1/6", "C. 5/6", "D. 6/6"],
        "answer": "D",
        "explanation": "끝점 1 = b/b = 6/6.",
        "difficulty": 1,
        "hints": ["전체 길이 = b/b = 1."],
        "feedback": {"correct": "정답! 6/6 = 1.", "incorrect": "끝점 1 = 6/6."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "A number line from 0 to 1 is divided into 3 equal parts. Where is 1/3?",
        "choices": ["A. 1번째 눈금", "B. 2번째 눈금", "C. 3번째 눈금", "D. 0번째 눈금"],
        "answer": "A",
        "explanation": "분자 1 → 1번 점프 → 1번째 눈금.",
        "difficulty": 1,
        "hints": ["1/3씩 1번."],
        "feedback": {"correct": "정답! 1번째.", "incorrect": "1번 점프."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "On a number line from 0 to 1 divided into 8 equal parts, which fraction is closer to 1: 7/8 or 5/8?",
        "choices": ["A. 5/8", "B. 7/8", "C. 둘 다 같음", "D. 알 수 없음"],
        "answer": "B",
        "explanation": "0에서 더 멀수록 1에 가까움. 7/8가 더 멀리.",
        "difficulty": 2,
        "hints": ["분자가 클수록 1에 가까움."],
        "feedback": {"correct": "정답! 7/8.", "incorrect": "7/8이 1에 더 가까움."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "A point sits exactly halfway between 0 and 1. What fraction is it (in fourths)?",
        "choices": ["A. 1/4", "B. 2/4", "C. 3/4", "D. 4/4"],
        "answer": "B",
        "explanation": "정중앙 = 1/2 = 2/4.",
        "difficulty": 2,
        "hints": ["1/2 = ?/4"],
        "feedback": {"correct": "정답! 2/4.", "incorrect": "1/2 = 2/4."},
    },
    {
        "id": "R2_07",
        "type": "MC",
        "question": "A number line from 0 to 1 has 6 equal parts. How many of those parts make 4/6?",
        "choices": ["A. 2 parts", "B. 3 parts", "C. 4 parts", "D. 6 parts"],
        "answer": "C",
        "explanation": "4/6 = 1/6짜리 4개.",
        "difficulty": 1,
        "hints": ["분자가 부분 개수."],
        "feedback": {"correct": "정답! 4 parts.", "incorrect": "분자 = 4."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "Tom marks 2/4 and Lisa marks 1/2 on identical number lines from 0 to 1. Compare positions.",
        "choices": ["A. 2/4가 더 오른쪽", "B. 1/2가 더 오른쪽", "C. 같은 위치", "D. 비교 불가"],
        "answer": "C",
        "explanation": "2/4 = 1/2 (같은 분수, 같은 점).",
        "difficulty": 3,
        "hints": ["2/4를 약분하면?"],
        "feedback": {"correct": "정답! 같은 위치.", "incorrect": "2/4 = 1/2 → 같은 점."},
    },
    {
        "id": "R3_05",
        "type": "MC",
        "question": "A number line from 0 to 1 is divided into n equal parts. As n grows larger, what happens to the distance between consecutive ticks?",
        "choices": ["A. 더 길어짐", "B. 더 짧아짐", "C. 변화 없음", "D. 사라짐"],
        "answer": "B",
        "explanation": "1을 더 많은 칸으로 나눌수록 한 칸 길이는 짧아짐.",
        "difficulty": 3,
        "hints": ["분모가 클수록 한 칸은?"],
        "feedback": {"correct": "정답! 짧아짐.", "incorrect": "분모↑ → 한 칸↓."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 437 + 285.",
        "choices": ["A. 612", "B. 622", "C. 712", "D. 722"],
        "answer": "D",
        "explanation": "437+285: 7+5=12 (carry 1), 3+8+1=12 (carry 1), 4+2+1=7. Result: 722.",
        "difficulty": 2,
        "hints": ["Two carries.", "437+285=722."],
        "feedback": {"correct": "Right — 722.", "incorrect": "437+285=722."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 600 − 247.",
        "choices": ["A. 343", "B. 353", "C. 363", "D. 453"],
        "answer": "B",
        "explanation": "600−247=353 (borrow across both zeros).",
        "difficulty": 2,
        "hints": ["Borrow across zeros.", "600−247=353."],
        "feedback": {"correct": "Right — 353.", "incorrect": "600−247=353."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 645 pencils. They handed out 278, then bought 159 more. How many pencils now?",
        "choices": ["A. 367", "B. 437", "C. 526", "D. 645"],
        "answer": "C",
        "explanation": "Step 1: 645−278=367. Step 2: 367+159=526.",
        "difficulty": 3,
        "hints": ["Subtract handed, add bought.", "645−278=367, 367+159=526."],
        "feedback": {"correct": "Right — 526 pencils.", "incorrect": "645−278=367, then +159=526."},
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
    # R2: keep existing 4 + add 3 fraction (R2_05~07) + 3 U1 (R2_08~10) = 10
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
        "prerequisite": "G3 U8 L4 — 분수 a/b: 단위분수 a개 모음 (3.NF.A.1)",
        "current":      "G3 — 수직선 위의 분수: 0~1을 b등분 → a/b 위치 (3.NF.A.2)",
        "successor":    "G3 U8 L6 — 분수와 자연수 관계 (3.NF.A.3c)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l5.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
