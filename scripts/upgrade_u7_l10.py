"""
G3 U7 L10 — Two-Step Problems 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.D.8 (두 단계 문장제 — 4가지 연산 혼합)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U7_division_facts_strategies/L10_two_step_problems.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.OA.D.8.M01"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.OA.D.8.M01"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.OA.D.8.M01"] for i in range(1,11)},
    "R2_01": ["3.OA.D.8.M01"],
    "R2_02": ["3.OA.D.8.M01"],
    "R2_03": ["3.OA.D.8.M01"],
    "R2_04": ["3.OA.D.8.M01"],
    "R2_05": ["3.OA.D.8.M01"],
    "R2_06": ["3.OA.D.8.M01"],
    "R2_07": ["3.OA.D.8.M01"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.OA.D.8.M01"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "two_step_word_problem" for i in range(1,6)},
    "LEARN_01": "two_step_intro",
    "LEARN_02": "bar_model_two_step",
    "LEARN_03": "single_equation_two_step",
    "LEARN_04": "identify_operations",
    "LEARN_05": "check_two_step_answer",
    "LEARN_06": "two_step_routine",
    "LEARN_07": "operation_clue_words",
    "LEARN_08": "two_step_estimate_check",
    **{f"TRY_0{i}": "two_step_word_problem" for i in range(1,6)},
    **{f"R1_{i:02d}": "two_step_word_problem" for i in range(1,11)},
    **{f"R2_0{i}": "two_step_word_problem" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "two_step_word_problem" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "abstract", "LEARN_02": "pictorial", "LEARN_03": "abstract",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.7 Lesson 7.10 'Two-Step Problems' pp.301-304",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic G — Two-Step Word Problems with Four Operations",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_item(item: dict) -> dict:
    item_id = item["id"]
    if item_id.startswith("LN_"):
        item_id = f"LEARN_{item_id[3:]}"
        item["id"] = item_id
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "two_step_word_problem")
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
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "두 단계 루틴 — 단계 분리하기",
        "content": (
            "두 단계 문제는 한 번에 풀지 말고 두 단계로 나눔. "
            "예: '24 스티커 → 6 빼기 → 3명에게 나누기' "
            "  단계 1) 24 − 6 = 18. "
            "  단계 2) 18 ÷ 3 = 6. 답: 한 명당 6장. "
            "단계 1) 문제를 읽고 첫 번째 동작 찾기. "
            "단계 2) 첫 번째 결과를 적기 (중간 답). "
            "단계 3) 두 번째 동작 적용 → 최종 답. "
            "흔한 실수 (M01): 한 단계만 풀고 끝냄 — 문제를 끝까지 읽고 두 단계 모두 처리."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_step_routine",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "단어로 연산 알아내기 — 4가지 신호",
        "content": (
            "문제 단어로 어떤 연산을 쓸지 결정: "
            "  + 더하기: '모두', '총', '합쳐', '받았다', '더 추가' "
            "  − 빼기: '남은', '나갔다', '주었다', '잃었다', '먹었다' "
            "  × 곱하기: '__개씩 N묶음', '__의 N배', '한 개당 ___이 N개' "
            "  ÷ 나누기: '똑같이 나누어', '__개씩 묶음', '__명에게 같은 수' "
            "팁: 두 단계 문제는 단어 신호 두 개를 모두 찾아야 함."
        ),
        "cpa_stage": "abstract",
        "visual_type": "operation_clues",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "어림셈 검산 — 답이 합리적인가?",
        "content": (
            "답을 적은 뒤 어림셈으로 검증: 답이 너무 크거나 작지 않은가? "
            "예: '24 − 6 ÷ 3' → 24 − 2 = 22 (어림 25). 답 22 ✓. "
            "예: 28 ÷ 7 = 4, +2 → 6. 어림: 30 ÷ 7 ≈ 4, +2 = 6 ✓. "
            "🔍 검증 절차: 단계마다 어림 → 최종 답이 어림 ± 작은 차이인지 확인. "
            "흔한 실수 (M01): 두 단계를 거꾸로 적용 (예: 먼저 ÷ 후 −를 해야 하는데 먼저 −) — "
            "단어 순서대로 단계 분리."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_step_estimate_check",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 478 + 386.",
        "choices": ["A. 754", "B. 764", "C. 854", "D. 864"],
        "answer": "D",
        "explanation": "478+386: 8+6=14 (carry 1), 7+8+1=16 (carry 1), 4+3+1=8. Result: 864.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 14. Tens: 16. Hundreds: 8."],
        "feedback": {"correct": "Right — 864.", "incorrect": "478+386=864."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 803 − 467.",
        "choices": ["A. 336", "B. 346", "C. 436", "D. 446"],
        "answer": "A",
        "explanation": "803−467: 3−7 borrow → 13−7=6; tens 9−6=3 (after lending across zero); hundreds 7−4=3. Result: 336.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "803−467=336."],
        "feedback": {"correct": "Right — 336.", "incorrect": "803−467=336."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A class had 658 cookies. They sold 247, then baked 175 more. How many cookies now?",
        "choices": ["A. 411", "B. 488", "C. 586", "D. 658"],
        "answer": "C",
        "explanation": "Step 1: 658−247=411. Step 2: 411+175=586.",
        "difficulty": 3,
        "hints": ["Subtract sold, then add baked.", "658−247=411, 411+175=586."],
        "feedback": {"correct": "Right — 586 cookies.", "incorrect": "658−247=411, then +175=586."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 새 7단계 표준으로 업그레이드됨.")
        return

    sections_map = {
        "pretest": d.get("pretest", []),
        "learn": d.get("learn", []),
        "try": d.get("try", []),
        "practice_r1": d.get("practice_r1", []),
        "practice_r2": d.get("practice_r2", []),
        "practice_r3": d.get("practice_r3", []),
    }

    learn_ids = {i["id"].replace("LN_","LEARN_") for i in sections_map["learn"]}
    for new_card in NEW_LEARN_CARDS:
        if new_card["id"] not in learn_ids:
            sections_map["learn"].append(new_card)

    sections_map["practice_r2"] = sections_map["practice_r2"][:7]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key in sections_map:
        sections_map[sec_key] = [normalize_item(it) for it in sections_map[sec_key]]

    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U7 L9 — 9 나눗셈: 자릿수 합 9 트릭 (3.OA.C.7)",
        "current":      "G3 — 두 단계 문장제: 4가지 연산 혼합 (3.OA.D.8)",
        "successor":    "G3 U7 L11 — 연산 순서 (3.OA.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u7_l10.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
