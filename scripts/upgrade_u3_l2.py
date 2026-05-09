"""
G3 U3 L2 — Relate Addition and Multiplication 7단계 업그레이드 스크립트
======================================================================
목적: L2_relate_addition_and_multiplication.json을 7단계 검증 프로토콜에 맞게 업그레이드
- 40개 → 43개 문항 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
- LN_ → LEARN_ 아이디 정규화, cpa_phase → cpa_stage 정규화
- 최상위 섹션 키 구조로 변환
- vertical_alignment, cpa_stage, feedback_correct, verification 블록 추가
- R2_08/09/10 U1 복습으로 교체
- 표준: 3.OA.A.1 (반복 덧셈 ↔ 곱셈 식 전환)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U3_understand_multiplication/L2_relate_addition_and_multiplication.json"

# ── 오류 유형 맵 ───────────────────────────────────────────────────────────
ERRORS_MAP = {
    # PRETEST
    "PT_01": ["3.OA.A.1.M02"],                        # 3×5 vs 5×3 모델 혼동
    "PT_02": ["3.OA.A.1.M02", "3.OA.A.1.M04"],        # 4×4 오선택, 덧항 개수 오인
    "PT_03": ["3.OA.A.1.M04"],                        # 6개 3을 5×3으로 셈
    "PT_04": ["3.OA.A.1.M02"],                        # 6×6 (size×size) 오선택
    "PT_05": ["3.OA.A.1.M02", "3.OA.A.1.M01"],        # 5×5 또는 4+5 오선택
    # LEARN (concept cards)
    "LEARN_01": [],
    "LEARN_02": [],
    "LEARN_03": [],
    "LEARN_04": [],
    "LEARN_05": [],
    "LEARN_06": [],
    "LEARN_07": [],
    "LEARN_08": [],
    # TRY
    "TRY_01": ["3.OA.A.1.M04"],                       # 6의 개수 오인 → 6×6
    "TRY_02": ["3.OA.A.1.M01", "3.OA.A.1.M03"],       # 7(add) 또는 단일값 보고
    "TRY_03": ["3.OA.A.1.M02", "3.OA.A.1.M04"],       # 7×7 오선택
    "TRY_04": ["3.OA.A.1.M04"],                       # 5개 2의 개수 오인
    "TRY_05": ["3.OA.A.1.M04"],                       # 덧항 개수 → 인자 매칭 오류
    # R1
    "R1_01": ["3.OA.A.1.M04"],                        # 8+8 → 2×8 매칭
    "R1_02": ["3.OA.A.1.M02"],                        # 5×2 ↔ 2×5 양방향
    "R1_03": ["3.OA.A.1.M04"],                        # 9의 개수 4개
    "R1_04": ["3.OA.A.1.M04", "3.OA.A.1.M07"],        # 5씩 6번
    "R1_05": ["3.OA.A.1.M04"],                        # 3개 3 → 3×3
    "R1_06": ["3.OA.A.1.M02", "3.OA.A.1.M01"],        # 'each' 의미
    "R1_07": ["3.OA.A.1.M04"],                        # 6 세 개
    "R1_08": ["3.OA.A.1.M02"],                        # 7×2 = 일곱 2
    "R1_09": ["3.OA.A.1.M02"],                        # 5 groups of 6
    "R1_10": ["3.OA.A.1.M02"],                        # 'each' 5 packs × 4
    # R2 (R2_08/09/10은 U1 복습으로 교체)
    "R2_01": ["3.OA.A.1.M01"],                        # 4×6 vs 4+6 식별
    "R2_02": ["3.OA.A.1.M02"],                        # 양방향 변환
    "R2_03": ["3.OA.A.1.M04"],                        # 7개 2
    "R2_04": ["3.OA.A.1.M02"],                        # 6×4 - 3 두 단계
    "R2_05": ["3.OA.A.1.M02"],                        # 4 rows × 5
    "R2_06": ["3.OA.A.1.M04"],                        # 미지수 4×n=32
    "R2_07": ["3.OA.A.1.M02"],                        # 교환법칙 미리보기
    "R2_08": ["3.NBT.2.M01"],                         # U1 복습: 3자리 덧셈
    "R2_09": ["3.NBT.2.M01"],                         # U1 복습: 3자리 뺄셈
    "R2_10": ["3.NBT.2.M01"],                         # U1 복습: 두단계
    # R3
    "R3_01": ["3.OA.A.1.M02"],                        # 두 학생 비교
    "R3_02": ["3.OA.A.1.M04"],                        # 7×n=56
    "R3_03": ["3.OA.A.1.M02"],                        # 두 그룹 합산
    "R3_04": ["3.OA.A.1.M02"],                        # 3×9+5 두 단계
    "R3_05": ["3.OA.A.1.M02"],                        # 8×3 양방향
}

# ── 스킬 태그 맵 ───────────────────────────────────────────────────────────
SKILL_TAGS = {
    "PT_01": "addition_to_multiplication",
    "PT_02": "addition_to_multiplication",
    "PT_03": "addition_to_multiplication",
    "PT_04": "word_problem_to_multiplication",
    "PT_05": "word_problem_to_multiplication",
    "LEARN_01": "addition_to_multiplication",
    "LEARN_02": "factor_product_naming",
    "LEARN_03": "addition_to_multiplication",
    "LEARN_04": "addition_to_multiplication",
    "LEARN_05": "two_way_translation",
    "LEARN_06": "factor_product_naming",
    "LEARN_07": "two_way_translation",
    "LEARN_08": "addition_to_multiplication",
    "TRY_01": "addition_to_multiplication",
    "TRY_02": "groups_of_meaning",
    "TRY_03": "addition_to_multiplication",
    "TRY_04": "addition_to_multiplication",
    "TRY_05": "two_way_translation",
    "R1_01": "addition_to_multiplication",
    "R1_02": "two_way_translation",
    "R1_03": "addition_to_multiplication",
    "R1_04": "skip_count_inverse",
    "R1_05": "addition_to_multiplication",
    "R1_06": "word_problem_to_multiplication",
    "R1_07": "addition_to_multiplication",
    "R1_08": "multiplication_to_addition",
    "R1_09": "groups_of_meaning",
    "R1_10": "word_problem_to_multiplication",
    "R2_01": "identify_non_multiplication",
    "R2_02": "multiplication_to_addition",
    "R2_03": "addition_to_multiplication",
    "R2_04": "two_step_multiplication",
    "R2_05": "array_to_multiplication",
    "R2_06": "missing_factor",
    "R2_07": "commutative_preview",
    "R2_08": "addition_3digit",            # U1 복습
    "R2_09": "subtraction_3digit",         # U1 복습
    "R2_10": "two_step_add_sub",           # U1 복습
    "R3_01": "two_way_translation",
    "R3_02": "missing_factor",
    "R3_03": "two_step_multiplication",
    "R3_04": "two_step_multiplication",
    "R3_05": "multiplication_to_addition",
}

# ── CPA 단계 맵 ────────────────────────────────────────────────────────────
CPA_MAP = {
    "PT_01": "abstract",
    "PT_02": "abstract",
    "PT_03": "abstract",
    "PT_04": "pictorial",
    "PT_05": "pictorial",
    "LEARN_01": "concrete",
    "LEARN_02": "concrete",
    "LEARN_03": "pictorial",
    "LEARN_04": "abstract",
    "LEARN_05": "abstract",
    "LEARN_06": "pictorial",
    "LEARN_07": "abstract",
    "LEARN_08": "abstract",
    "TRY_01": "abstract",
    "TRY_02": "pictorial",
    "TRY_03": "abstract",
    "TRY_04": "abstract",
    "TRY_05": "abstract",
    "R1_01": "abstract",
    "R1_02": "abstract",
    "R1_03": "abstract",
    "R1_04": "abstract",
    "R1_05": "abstract",
    "R1_06": "abstract",
    "R1_07": "abstract",
    "R1_08": "abstract",
    "R1_09": "abstract",
    "R1_10": "abstract",
    "R2_01": "abstract",
    "R2_02": "abstract",
    "R2_03": "abstract",
    "R2_04": "abstract",
    "R2_05": "pictorial",
    "R2_06": "abstract",
    "R2_07": "abstract",
    "R2_08": "abstract",
    "R2_09": "abstract",
    "R2_10": "abstract",
    "R3_01": "abstract",
    "R3_02": "abstract",
    "R3_03": "abstract",
    "R3_04": "abstract",
    "R3_05": "abstract",
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.3 Lesson 3.2 'Relate Addition and Multiplication' pp.105-108",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic A — Relating Repeated Addition to Multiplication",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "addition_to_multiplication")
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )
    item["expected_errors"] = ERRORS_MAP.get(item_id, [])
    item.setdefault("math_note", "")
    item["verification"] = make_verification(item_id)
    return item


# ── 신규 LEARN 카드 (LEARN_06 ~ LEARN_08) ─────────────────────────────────
NEW_LEARN_CARDS = [
    {
        "id": "LEARN_06",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "덧항 개수가 첫 번째 인자",
        "content": (
            "반복 덧셈을 곱셈으로 바꿀 때, '몇 개의 같은 수가 더해지는가'를 "
            "먼저 셉니다. 그 개수가 첫 번째 인자입니다. "
            "예: 5 + 5 + 5 + 5 → 5가 4개 → 4 × 5 = 20. "
            "흔한 실수: 4 × 5를 5 × 5로 잘못 쓰는 경우 — 같은 수의 개수와 "
            "더해지는 수를 혼동한 것입니다."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "manipulative",
        "visual_data": {"tool": "array_grid", "config": {"rows": 4, "cols": 5}},
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "두 방향 변환 — 덧셈 ↔ 곱셈",
        "content": (
            "곱셈식 → 덧셈식: 3 × 6 → 6 + 6 + 6 (또는 3 + 3 + 3 + 3 + 3 + 3, "
            "교환법칙). 덧셈식 → 곱셈식: 7 + 7 + 7 + 7 → 4 × 7. "
            "방향에 관계없이 같은 수만 반복되어야 곱셈으로 변환 가능합니다. "
            "주의: 4 + 6은 같은 수가 아니므로 곱셈으로 바꿀 수 없습니다."
        ),
        "cpa_stage": "abstract",
        "visual_type": "none",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "곱셈식 읽기 요약",
        "content": (
            "3 × 7 = 21에서 — "
            "3과 7은 인자(factor), 21은 곱(product). "
            "× 기호는 'times' 또는 'groups of'로 읽습니다. "
            "'3 × 7'은 '3 groups of 7' 또는 '3 times 7'. "
            "교환법칙: 3 × 7 = 7 × 3 = 21 (곱은 같지만 모델은 다름)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]

# ── R2_08/09/10 U1 복습 항목 ────────────────────────────────────────────
U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the sum: 386 + 247.",
        "choices": ["A. 523", "B. 533", "C. 633", "D. 723"],
        "answer": "C",
        "explanation": "386+247: 6+7=13 (carry 1), 8+4+1=13 (carry 1), 3+2+1=6. Result: 633.",
        "hints": [
            "Line up the digits — ones, tens, hundreds.",
            "Carry when a column total is 10 or more.",
        ],
        "feedback": {
            "correct": "Right — 633.",
            "incorrect": "386+247=633. Watch the two carries.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 712 − 358.",
        "choices": ["A. 354", "B. 364", "C. 446", "D. 454"],
        "answer": "A",
        "explanation": "712−358: 2−8 borrow → 12−8=4, tens 0−5 borrow → 10−5=5, hundreds 6−3=3. Result: 354.",
        "hints": [
            "Borrow when the top digit is smaller.",
            "Two borrows are needed here.",
        ],
        "feedback": {
            "correct": "Right — 354.",
            "incorrect": "712−358=354. Borrow twice.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "Library has 524 books. They donate 86 books, then receive 142 new ones. How many books now?",
        "choices": ["A. 296", "B. 438", "C. 580", "D. 752"],
        "answer": "C",
        "explanation": "Step 1: 524−86=438. Step 2: 438+142=580.",
        "hints": [
            "Two steps: subtract donated, then add new.",
            "524−86=438, then 438+142=580.",
        ],
        "feedback": {
            "correct": "Right — 580 books.",
            "incorrect": "524−86=438, then +142=580.",
        },
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "pretest" in d:
        print("⚠️  이미 업그레이드됨. 건너뜁니다.")
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

    r2_keep_ids = {"R2_01","R2_02","R2_03","R2_04","R2_05","R2_06","R2_07"}
    sections_map["practice_r2"] = [
        i for i in sections_map["practice_r2"] if i["id"] in r2_keep_ids
    ]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key, items in sections_map.items():
        sections_map[sec_key] = [add_item_fields(item) for item in items]

    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별 문항 수:", counts)
    total = sum(counts.values())
    print(f"총 문항 수: {total} (목표: 43)")
    assert counts["pretest"] == 5
    assert counts["learn"] == 8
    assert counts["try"] == 5
    assert counts["practice_r1"] == 10
    assert counts["practice_r2"] == 10
    assert counts["practice_r3"] == 5
    assert total == 43

    r2_items = sections_map["practice_r2"]
    u1_review = [i for i in r2_items if i.get("review_from") == "U1"]
    print(f"R2 U1 복습 문항: {len(u1_review)}개 (목표: 3)")

    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G2 — 같은 수 반복 더하기 (2.OA.C.4)",
        "current":      "G3 — 반복 덧셈을 곱셈으로 변환; 인자/곱 명명 (3.OA.A.1)",
        "successor":    "G3 U3 L3 — 수직선에서 건너뛰며 세기 (3.OA.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = total
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u3_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   총 {total}개 문항 (PT={counts['pretest']} "
          f"LEARN={counts['learn']} TRY={counts['try']} "
          f"R1={counts['practice_r1']} R2={counts['practice_r2']} "
          f"R3={counts['practice_r3']})")


if __name__ == "__main__":
    upgrade()
