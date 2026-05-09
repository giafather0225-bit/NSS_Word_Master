"""
G3 U5 L1 — Describe Patterns 7단계 업그레이드 스크립트 (재이주)
================================================================
구버전(섹션 분할만)에서 새 7단계 프로토콜로 마이그레이션
- stem → question 필드 정규화
- LN_ → LEARN_ 아이디 정규화
- cpa_phase → cpa_stage 정규화
- LEARN 5개 → 8개 (LEARN_06–08 추가)
- R2_08/09/10 U1 복습으로 교체
- expected_errors, verification, skill_tag, math_note, feedback_correct 추가
- vertical_alignment 추가
표준: 3.OA.D.9 (곱셈표 패턴 — 함수표·규칙 기술)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U5_use_multiplication_facts/L1_describe_patterns.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.D.9.M08"],
    "PT_02": ["3.OA.D.9.M03"],
    "PT_03": ["3.OA.D.9.M06"],
    "PT_04": ["3.OA.D.9.M03"],
    "PT_05": ["3.OA.A.1.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.D.9.M06"],
    "TRY_02": ["3.OA.A.1.M01"],
    "TRY_03": ["3.OA.C.7.M04"],
    "TRY_04": ["3.OA.D.9.M03"],
    "TRY_05": ["3.OA.D.9.M08"],
    "R1_01": ["3.OA.D.9.M03"],
    "R1_02": ["3.OA.D.9.M08"],
    "R1_03": ["3.OA.D.9.M03"],
    "R1_04": ["3.OA.D.9.M08"],
    "R1_05": ["3.OA.A.1.M01"],
    "R1_06": ["3.OA.A.1.M01"],
    "R1_07": ["3.OA.A.1.M01"],
    "R1_08": ["3.OA.A.1.M01"],
    "R1_09": ["3.OA.A.1.M01"],
    "R1_10": ["3.OA.D.9.M03"],
    "R2_01": ["3.OA.D.9.M03"],
    "R2_02": ["3.OA.A.1.M01"],
    "R2_03": ["3.OA.C.7.M07"],
    "R2_04": ["3.OA.A.4.M01"] if False else ["3.OA.D.9.M08"],
    "R2_05": ["3.OA.C.7.M06"],
    "R2_06": ["3.OA.D.9.M03"],
    "R2_07": ["3.OA.B.5.M06"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.9.M08"],
    "R3_02": ["3.OA.D.9.M08"],
    "R3_03": ["3.OA.D.9.M03"],
    "R3_04": ["3.OA.D.9.M03"],
    "R3_05": ["3.OA.A.4.M01"] if False else ["3.OA.D.9.M03"],
}

SKILL_TAGS = {
    "PT_01": "find_rule",
    "PT_02": "complete_table",
    "PT_03": "complete_table",
    "PT_04": "complete_table",
    "PT_05": "rate_word_problem",
    "LEARN_01": "table_concept",
    "LEARN_02": "find_rule",
    "LEARN_03": "complete_table",
    "LEARN_04": "rule_increment",
    "LEARN_05": "predict_with_rule",
    "LEARN_06": "find_rule",
    "LEARN_07": "complete_table",
    "LEARN_08": "patterns_strategies",
    "TRY_01": "complete_table",
    "TRY_02": "rate_word_problem",
    "TRY_03": "rule_apply",
    "TRY_04": "complete_table",
    "TRY_05": "find_rule",
    "R1_01": "complete_table",
    "R1_02": "find_rule",
    "R1_03": "complete_table",
    "R1_04": "complete_table",
    "R1_05": "rate_word_problem",
    "R1_06": "rate_word_problem",
    "R1_07": "rate_word_problem",
    "R1_08": "rate_word_problem",
    "R1_09": "rate_word_problem",
    "R1_10": "complete_table",
    "R2_01": "complete_table",
    "R2_02": "rate_word_problem",
    "R2_03": "rule_apply",
    "R2_04": "missing_input",
    "R2_05": "rule_apply",
    "R2_06": "complete_table",
    "R2_07": "rule_with_zero",
    "R2_08": "addition_3digit",      # U1
    "R2_09": "subtraction_3digit",   # U1
    "R2_10": "two_step_add_sub",     # U1
    "R3_01": "doubling_pattern",
    "R3_02": "find_rule_division",
    "R3_03": "find_table_error",
    "R3_04": "rule_apply",
    "R3_05": "missing_input",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "concrete", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "concrete", "LEARN_07": "abstract", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1,6)},
    **{f"R1_0{i}": "abstract" for i in range(1,11)},
    **{f"R2_0{i}": "abstract" for i in range(1,8)},
    "R2_08": "abstract", "R2_09": "abstract", "R2_10": "abstract",
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.5 Lesson 5.1 'Describe Patterns' pp.189-192",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic G — Patterns in the Multiplication Table",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_item(item: dict) -> dict:
    """공통 필드 정규화: stem→question, cpa_phase→cpa_stage, feedback→feedback_correct"""
    item_id = item["id"]

    # LN_ → LEARN_ 아이디 정규화
    if item_id.startswith("LN_"):
        item_id = f"LEARN_{item_id[3:]}"
        item["id"] = item_id

    # stem → question
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")

    # cpa_phase → cpa_stage
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]

    # skill_tag
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "find_rule")

    # feedback.correct → feedback_correct
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )

    # expected_errors, math_note, verification
    item["expected_errors"] = ERRORS_MAP.get(item_id, [])
    item.setdefault("math_note", "")
    item["verification"] = make_verification(item_id)

    return item


NEW_LEARN_CARDS = [
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "함수표 — 입력에서 규칙으로 (한 쌍은 부족!)",
        "content": (
            "함수표에서 규칙을 찾을 때 한 쌍만 보면 위험합니다. "
            "예: 입력 2 → 출력 12. 가능한 규칙: ×6 (2×6=12), +10 (2+10=12), ×2+8... "
            "단계 1: 첫 쌍에서 가능한 규칙 후보 나열. "
            "단계 2: 두 번째 쌍으로 검증. 예: 입력 3 → 출력 18. "
            "  ×6: 3×6=18 ✓. +10: 3+10=13 ✗. → ×6이 정답. "
            "단계 3: 세 번째 쌍에 적용해 다시 확인. "
            "흔한 실수: 첫 쌍만 보고 규칙 결정 (잘못된 패턴 발견)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "function_table",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "표 완성하기 — 규칙 적용 양방향",
        "content": (
            "규칙이 정해지면 양방향으로 사용 가능. "
            "정방향(input → output): 입력 × 규칙 = 출력. 예 ×7, 입력 6 → 6×7=42. "
            "역방향(output → input): 출력 ÷ 규칙 = 입력. 예 ×7, 출력 56 → 56÷7=8. "
            "표에 빈칸이 있으면 어느 쪽에 있는지 보고 적절한 방향 선택. "
            "흔한 실수: input→output만 외워 output 알 때 input을 못 찾음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "bidirectional_arrow",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "함수표 풀이 4단계 + 검증",
        "content": (
            "단계 1 한 쌍 찾기: 입력 × ? = 출력 형태로 규칙 후보. "
            "단계 2 두 번째 쌍으로 검증: 같은 규칙이 모든 쌍에 작동? "
            "단계 3 빈칸 채우기: 정/역방향 적절히 선택. "
            "단계 4 표 전체 점검: 모든 행이 같은 규칙 따르는지 확인. "
            "🔍 검증법: 표에 오류가 있을 수 있음 — 각 행 모두 규칙 검사. "
            "  예: ×8인데 5 → 42라면 오류 (5×8=40)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 374 + 286.",
        "choices": ["A. 550", "B. 560", "C. 650", "D. 660"],
        "answer": "D",
        "explanation": "374+286: 4+6=10 (carry 1), 7+8+1=16 (carry 1), 3+2+1=6. Result: 660.",
        "difficulty": 2,
        "hints": [
            "Two carries.",
            "Ones: 10. Tens: 16. Hundreds: 6.",
        ],
        "feedback": {
            "correct": "Right — 660.",
            "incorrect": "374+286=660.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 605 − 247.",
        "choices": ["A. 358", "B. 368", "C. 458", "D. 468"],
        "answer": "A",
        "explanation": "605−247: 5−7 borrow → 15−7=8; tens 9−4=5 (after lending); hundreds 5−2=3. Result: 358.",
        "difficulty": 2,
        "hints": [
            "Borrow across the zero in tens.",
            "605−247=358.",
        ],
        "feedback": {
            "correct": "Right — 358.",
            "incorrect": "605−247=358.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 482 chairs. They removed 156 broken chairs, then bought 235 new ones. How many chairs now?",
        "choices": ["A. 326", "B. 561", "C. 717", "D. 873"],
        "answer": "B",
        "explanation": "Step 1: 482−156=326. Step 2: 326+235=561.",
        "difficulty": 3,
        "hints": [
            "Subtract removed, then add bought.",
            "482−156=326, 326+235=561.",
        ],
        "feedback": {
            "correct": "Right — 561 chairs.",
            "incorrect": "482−156=326, then +235=561.",
        },
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)

    # 멱등성 가드: 이미 새 표준이면 종료
    if "vertical_alignment" in d:
        print("⚠️  이미 새 7단계 표준으로 업그레이드됨.")
        return

    # 기존 섹션을 가져와 정규화
    sections_map = {
        "pretest": d.get("pretest", []),
        "learn": d.get("learn", []),
        "try": d.get("try", []),
        "practice_r1": d.get("practice_r1", []),
        "practice_r2": d.get("practice_r2", []),
        "practice_r3": d.get("practice_r3", []),
    }

    # LEARN_06–08 추가 (없으면)
    learn_ids = {i["id"].replace("LN_","LEARN_") for i in sections_map["learn"]}
    for new_card in NEW_LEARN_CARDS:
        if new_card["id"] not in learn_ids:
            sections_map["learn"].append(new_card)

    # R2_08/09/10 교체 (앞 7개만 유지)
    sections_map["practice_r2"] = sections_map["practice_r2"][:7]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    # 모든 항목 정규화
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
        "prerequisite": "G3 U4 L7 — 곱셈표 패턴 (3.OA.D.9)",
        "current":      "G3 — 함수표·규칙 찾기·표 완성 (3.OA.D.9)",
        "successor":    "G3 U5 L2 — 미지수 인자 찾기 (3.OA.A.4)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u5_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
