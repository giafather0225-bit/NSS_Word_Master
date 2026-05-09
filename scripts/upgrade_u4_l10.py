"""
G3 U4 L10 — Problem Solving: Multiplication 7단계 업그레이드 스크립트
======================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.D.8 (두 단계 워드프로블럼 — 곱셈 + 덧셈/뺄셈)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U4_multiplication_facts_strategies/L10_problem_solving_multiplication.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.D.8.M06"],
    "PT_02": ["3.OA.D.8.M06"],
    "PT_03": ["3.OA.D.8.M06"],
    "PT_04": ["3.OA.D.8.M01"],
    "PT_05": ["3.OA.D.8.M04", "3.OA.D.8.M01"],
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.D.8.M06"],
    "TRY_02": ["3.OA.D.8.M06"],
    "TRY_03": ["3.OA.D.8.M06"],
    "TRY_04": ["3.OA.D.8.M02", "3.OA.D.8.M03"],
    "TRY_05": ["3.OA.D.8.M06"],
    "R1_01": ["3.OA.D.8.M06"],
    "R1_02": ["3.OA.D.8.M06"],
    "R1_03": ["3.OA.D.8.M06"],
    "R1_04": ["3.OA.D.8.M06"],
    "R1_05": ["3.OA.D.8.M06"],
    "R1_06": ["3.OA.D.8.M06"],
    "R1_07": ["3.OA.D.8.M06"],
    "R1_08": ["3.OA.D.8.M06"],
    "R1_09": ["3.OA.B.5.M06"],
    "R1_10": ["3.OA.D.8.M06"],
    "R2_01": ["3.OA.D.8.M06"],
    "R2_02": ["3.OA.D.8.M06"],
    "R2_03": ["3.OA.D.8.M06"],
    "R2_04": ["3.OA.D.8.M01", "3.OA.D.8.M05"],
    "R2_05": ["3.OA.D.8.M06"],
    "R2_06": ["3.OA.D.8.M06"],
    "R2_07": ["3.OA.D.8.M06"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    "R3_01": ["3.OA.D.8.M08"],
    "R3_02": ["3.OA.B.5.M07"],
    "R3_03": ["3.OA.D.8.M08", "3.OA.D.8.M01"],
    "R3_04": ["3.OA.D.8.M01", "3.OA.D.8.M05"],
    "R3_05": ["3.OA.D.8.M05"],
}

SKILL_TAGS = {
    "PT_01": "function_table",
    "PT_02": "rule_apply",
    "PT_03": "find_rule",
    "PT_04": "extend_pattern",
    "PT_05": "two_step_multiply_subtract",
    "LEARN_01": "function_table_concept",
    "LEARN_02": "rule_apply",
    "LEARN_03": "two_step_problem",
    "LEARN_04": "find_rule",
    "LEARN_05": "verify_rule",
    "LEARN_06": "function_table_concept",
    "LEARN_07": "two_step_problem",
    "LEARN_08": "problem_solving_strategies",
    "TRY_01": "rule_apply",
    "TRY_02": "find_rule",
    "TRY_03": "rate_word_problem",
    "TRY_04": "two_step_multiply_subtract",
    "TRY_05": "missing_input",
    "R1_01": "rule_apply",
    "R1_02": "extend_pattern",
    "R1_03": "rate_word_problem",
    "R1_04": "rule_apply",
    "R1_05": "rate_word_problem",
    "R1_06": "find_rule",
    "R1_07": "rate_word_problem",
    "R1_08": "rate_word_problem",
    "R1_09": "rule_with_zero",
    "R1_10": "rate_extension",
    "R2_01": "array_word_problem",
    "R2_02": "rate_word_problem",
    "R2_03": "rate_word_problem",
    "R2_04": "two_step_multiply_add",
    "R2_05": "complete_table",
    "R2_06": "rule_apply",
    "R2_07": "rate_extension",
    "R2_08": "two_step_multiply_subtract",
    "R2_09": "find_rule",
    "R2_10": "rate_word_problem",
    "R2_08": "addition_3digit",       # U1 (override)
    "R2_09": "subtraction_3digit",    # U1
    "R2_10": "two_step_add_sub",      # U1
    "R3_01": "three_step_problem",
    "R3_02": "missing_input",
    "R3_03": "three_step_problem",
    "R3_04": "two_step_multiply_subtract",
    "R3_05": "two_group_combined",
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1,6)},
    "LEARN_01": "concrete", "LEARN_02": "pictorial", "LEARN_03": "abstract",
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
        "concept_source": "Go Math Grade 3 Ch.4 Lesson 4.10 'Problem Solving: Multiplication' pp.175-178",
        "procedure_source": "EngageNY Grade 3 Module 3 Topic G — Two-Step Word Problems with Multiplication",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def add_item_fields(item: dict) -> dict:
    item_id = item["id"]
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "rule_apply")
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
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "함수표 — 입력에서 출력으로 (규칙 찾기)",
        "content": (
            "함수표(function table)는 입력 → 규칙 → 출력 패턴. "
            "예: 입력 1→6, 2→12, 3→18. 규칙은 ×6 (각 출력 = 입력 × 6). "
            "단계 1: 같은 쌍에서 출력 ÷ 입력으로 규칙 후보 찾기. "
            "단계 2: 다른 쌍에 그 규칙을 적용해 검증. "
            "단계 3: 일치하면 규칙 확정, 미지수 입력에도 적용. "
            "흔한 실수: 한 쌍만 보고 규칙 결정 (예: 2→12에서 +10이라 잘못 추론)."
        ),
        "cpa_stage": "concrete",
        "visual_type": "function_table_diagram",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "두 단계 풀기 — 곱셈 먼저, 그 다음에 ±",
        "content": (
            "두 단계 워드프로블럼 패턴: 'N묶음 × M크기, 그 후 +K 또는 −K'. "
            "예: '7개의 박스, 박스당 6개. 5개 잃음. 남은 개수?' "
            "단계 1: 곱셈으로 총량 — 7 × 6 = 42. "
            "단계 2: ±K 적용 — 42 − 5 = 37. "
            "흔한 실수 1: M01 — 곱셈만 하고 멈춤 (42를 답으로). "
            "흔한 실수 2: M04 — 순서를 바꿔 (7−5)×6 = 12 (잘못)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_step_diagram",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "워드프로블럼 풀이 4단계 + 검증",
        "content": (
            "단계 1 읽기: 무엇을 묻는지 마지막 문장에 표시. "
            "단계 2 정보 추출: 숫자와 단위 모두 옆에 적기. "
            "단계 3 연산 선택: 'each', 'per' → 곱셈; 'left', 'remaining' → 뺄셈; 'in all' → 덧셈. "
            "단계 4 계산: 두 단계 이상이면 곱셈 먼저. "
            "🔍 검증: 답이 합리적인 범위인지 (예: 6 boxes × 8 = 48, 답이 100이면 의심). "
            "추가 정보 함정 주의 (M02): 모든 숫자를 쓸 필요 없음."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]

U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the sum: 392 + 487.",
        "choices": ["A. 779", "B. 869", "C. 879", "D. 979"],
        "answer": "C",
        "explanation": "392+487: 2+7=9, 9+8=17 (carry 1), 3+4+1=8. Result: 879.",
        "hints": [
            "One carry in the tens.",
            "Ones: 9. Tens: 17. Hundreds: 8.",
        ],
        "feedback": {
            "correct": "Right — 879.",
            "incorrect": "392+487=879.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 504 − 286.",
        "choices": ["A. 218", "B. 228", "C. 318", "D. 328"],
        "answer": "A",
        "explanation": "504−286: 4−6 borrow → 14−6=8; tens 9−8=1 (after lending); hundreds 4−2=2. Result: 218.",
        "hints": [
            "Borrow across the zero in tens.",
            "504−286=218.",
        ],
        "feedback": {
            "correct": "Right — 218.",
            "incorrect": "504−286=218.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "A factory had 815 cars. They shipped 387, then produced 254 more. How many cars now?",
        "choices": ["A. 174", "B. 428", "C. 682", "D. 1456"],
        "answer": "C",
        "explanation": "Step 1: 815−387=428. Step 2: 428+254=682.",
        "hints": [
            "Subtract shipped, then add produced.",
            "815−387=428, 428+254=682.",
        ],
        "feedback": {
            "correct": "Right — 682 cars.",
            "incorrect": "815−387=428, then +254=682.",
        },
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "pretest" in d:
        print("⚠️  이미 업그레이드됨.")
        return

    raw_items = d.pop("items", [])
    for item in raw_items:
        if item["id"].startswith("LN_"):
            item["id"] = f"LEARN_{item['id'][3:]}"

    sections_map: dict = {
        "pretest": [], "learn": [], "try": [],
        "practice_r1": [], "practice_r2": [], "practice_r3": [],
    }
    for item in raw_items:
        sec = item.get("section", "")
        if sec in sections_map:
            sections_map[sec].append(item)

    sections_map["learn"].extend(NEW_LEARN_CARDS)
    r2_keep = {f"R2_0{i}" for i in range(1,8)}
    sections_map["practice_r2"] = [i for i in sections_map["practice_r2"] if i["id"] in r2_keep]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key, items in sections_map.items():
        sections_map[sec_key] = [add_item_fields(item) for item in items]

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
        "prerequisite": "G3 U4 L1-L9 — 모든 ×n 사실, 분배·결합법칙, 곱셈표 패턴 (3.OA.C.7, 3.OA.B.5, 3.OA.D.9)",
        "current":      "G3 — 함수표·두 단계 워드프로블럼 (곱셈 + 덧셈/뺄셈) (3.OA.D.8)",
        "successor":    "G3 U5 — 곱셈 사실 활용 (3.OA.A.4 미지수, 3.MD.C.7 면적)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u4_l10.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
