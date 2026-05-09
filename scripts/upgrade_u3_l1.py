"""
G3 U3 L1 — Count Equal Groups 7단계 업그레이드 스크립트
=========================================================
목적: L1_count_equal_groups.json을 7단계 검증 프로토콜에 맞게 업그레이드
- 40개 → 43개 문항 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
- LN_ → LEARN_ 아이디 정규화
- cpa_phase → cpa_stage 필드 정규화
- 최상위 섹션 키 구조로 변환
- vertical_alignment, cpa_stage, feedback_correct, verification 블록 추가
- R2 마지막 25%(R2_08/09/10)를 U1 복습으로 교체
- 표준: 3.OA.A.1 (등량 그룹의 곱 해석)
"""

import json
import pathlib

# ── 경로 설정 ──────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U3_understand_multiplication/L1_count_equal_groups.json"

# ── 오류 유형 맵 ───────────────────────────────────────────────────────────
ERRORS_MAP = {
    # PRETEST
    "PT_01": ["3.OA.A.1.M01", "3.OA.A.1.M03"],
    "PT_02": ["3.OA.A.1.M01"],
    "PT_03": ["3.OA.A.1.M01", "3.OA.A.1.M04"],
    "PT_04": ["3.OA.A.1.M02", "3.OA.A.1.M06"],
    "PT_05": ["3.OA.A.1.M02", "3.OA.A.1.M06"],
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
    "TRY_01": ["3.OA.A.1.M01", "3.OA.A.1.M04"],
    "TRY_02": ["3.OA.A.1.M01", "3.OA.A.1.M03"],
    "TRY_03": ["3.OA.A.1.M02", "3.OA.A.1.M06"],
    "TRY_04": ["3.OA.A.1.M05"],
    "TRY_05": ["3.OA.A.1.M02", "3.OA.A.1.M06"],
    # R1
    "R1_01": ["3.OA.A.1.M01"],
    "R1_02": ["3.OA.A.1.M01", "3.OA.A.1.M04"],
    "R1_03": ["3.OA.A.1.M04", "3.OA.A.1.M07"],
    "R1_04": ["3.OA.A.1.M04"],
    "R1_05": ["3.OA.A.1.M02"],
    "R1_06": ["3.OA.A.1.M01"],
    "R1_07": ["3.OA.A.1.M01", "3.OA.A.1.M04"],
    "R1_08": ["3.OA.A.1.M03"],
    "R1_09": ["3.OA.A.1.M01"],
    "R1_10": ["3.OA.A.1.M04"],
    # R2 (R2_08/09/10은 U1 복습으로 교체)
    "R2_01": ["3.OA.A.1.M02"],
    "R2_02": ["3.OA.A.1.M01", "3.OA.A.1.M04"],
    "R2_03": ["3.OA.A.1.M05"],
    "R2_04": ["3.OA.A.1.M04"],
    "R2_05": ["3.OA.A.1.M01", "3.OA.A.1.M04"],
    "R2_06": ["3.OA.A.1.M02"],
    "R2_07": ["3.OA.A.1.M04"],
    "R2_08": ["3.NBT.2.M01"],   # U1 복습: 3자리 덧셈 받아올림
    "R2_09": ["3.NBT.2.M01"],   # U1 복습: 3자리 뺄셈 받아내림
    "R2_10": ["3.NBT.2.M01"],   # U1 복습: 두 단계 add/sub
    # R3
    "R3_01": ["3.OA.A.1.M02", "3.OA.A.1.M04"],
    "R3_02": ["3.OA.A.1.M04"],
    "R3_03": ["3.OA.A.1.M04"],
    "R3_04": ["3.OA.A.1.M01", "3.OA.A.1.M04"],
    "R3_05": ["3.OA.A.1.M02"],
}

# ── 스킬 태그 맵 ───────────────────────────────────────────────────────────
SKILL_TAGS = {
    "PT_01": "count_equal_groups",
    "PT_02": "count_equal_groups",
    "PT_03": "count_equal_groups",
    "PT_04": "groups_of_meaning",
    "PT_05": "groups_of_meaning",
    "LEARN_01": "equal_vs_unequal",
    "LEARN_02": "skip_count_total",
    "LEARN_03": "groups_of_meaning",
    "LEARN_04": "repeated_addition",
    "LEARN_05": "groups_of_meaning",
    "LEARN_06": "skip_count_total",
    "LEARN_07": "groups_of_meaning",
    "LEARN_08": "count_equal_groups",
    "TRY_01": "skip_count_total",
    "TRY_02": "count_equal_groups",
    "TRY_03": "groups_of_meaning",
    "TRY_04": "equal_vs_unequal",
    "TRY_05": "groups_of_meaning",
    "R1_01": "repeated_addition",
    "R1_02": "skip_count_total",
    "R1_03": "skip_count_total",
    "R1_04": "skip_count_total",
    "R1_05": "groups_of_meaning",
    "R1_06": "skip_count_total",
    "R1_07": "skip_count_total",
    "R1_08": "count_equal_groups",
    "R1_09": "repeated_addition",
    "R1_10": "skip_count_total",
    "R2_01": "groups_of_meaning",
    "R2_02": "skip_count_total",
    "R2_03": "equal_vs_unequal",
    "R2_04": "skip_count_total",
    "R2_05": "groups_of_meaning",
    "R2_06": "groups_of_meaning",
    "R2_07": "skip_count_total",
    "R2_08": "addition_3digit",          # U1 복습
    "R2_09": "subtraction_3digit",       # U1 복습
    "R2_10": "two_step_add_sub",         # U1 복습
    "R3_01": "two_step_multiplication",
    "R3_02": "find_groups",
    "R3_03": "find_group_size",
    "R3_04": "two_step_multiplication",
    "R3_05": "two_step_multiplication",
}

# ── CPA 단계 맵 ────────────────────────────────────────────────────────────
CPA_MAP = {
    "PT_01": "pictorial",
    "PT_02": "concrete",
    "PT_03": "pictorial",
    "PT_04": "pictorial",
    "PT_05": "pictorial",
    "LEARN_01": "concrete",
    "LEARN_02": "concrete",
    "LEARN_03": "pictorial",
    "LEARN_04": "pictorial",
    "LEARN_05": "abstract",
    "LEARN_06": "pictorial",
    "LEARN_07": "abstract",
    "LEARN_08": "abstract",
    "TRY_01": "pictorial",
    "TRY_02": "pictorial",
    "TRY_03": "pictorial",
    "TRY_04": "pictorial",
    "TRY_05": "pictorial",
    "R1_01": "pictorial",
    "R1_02": "pictorial",
    "R1_03": "pictorial",
    "R1_04": "pictorial",
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
    "R2_05": "abstract",
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
    """검증 블록 생성 — L1 Count Equal Groups"""
    return {
        "concept_source": "Go Math Grade 3 Ch.3 Lesson 3.1 'Count Equal Groups' pp.101-104",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic A — Multiplication and the Meaning of the Factors",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def add_item_fields(item: dict) -> dict:
    """각 문항에 공통 필드 추가/정규화"""
    item_id = item["id"]

    # cpa_phase → cpa_stage 정규화
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")

    # CPA_MAP으로 덮어쓰기
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]

    # skill_tag 추가
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "count_equal_groups")

    # hints 있는데 feedback_correct 없으면 추가
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )

    # expected_errors, math_note, verification 추가
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
        "title": "건너뛰며 세기 — 올바른 방향",
        "content": (
            "곱셈에서 건너뛰며 세기는 '한 그룹의 크기'만큼 점프하고, "
            "'그룹의 개수'만큼 점프 횟수를 만듭니다. "
            "예: 4 groups of 5 → 5씩 4번 점프 → 5, 10, 15, 20. "
            "주의: 4씩 5번(4, 8, 12, 16, 20)으로 세면 답은 같아도 "
            "'몇 그룹?'을 물었을 때 틀린 모델이 됩니다. "
            "팁: 손가락 하나가 한 그룹 — 손가락마다 점프 한 번."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "number_line_skip",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "GROUPS와 SIZE 구별하기",
        "content": (
            "문제를 읽을 때 '몇 개의 그룹(GROUPS)'과 "
            "'한 그룹에 몇 개(SIZE)'를 분리합니다. "
            "예: '5개의 상자에 연필이 4개씩' → GROUPS=5, SIZE=4. "
            "'4개의 상자에 연필이 5개씩'과는 모델이 완전히 다름! "
            "팁: GROUPS 단어에 밑줄, SIZE 단어에 동그라미. "
            "'each / every / per' 뒤의 숫자 = SIZE."
        ),
        "cpa_stage": "abstract",
        "visual_type": "none",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "등량 그룹 풀이 4가지 전략 요약",
        "content": (
            "전략 1 그리기: 각 그룹을 동그라미로 그리고 안에 점 찍기. "
            "전략 2 건너뛰며 세기: SIZE만큼 점프, GROUPS만큼 횟수. "
            "전략 3 반복 덧셈: SIZE를 GROUPS번 더하기. "
            "전략 4 곱셈: GROUPS × SIZE = 합계. "
            "검증: '같은 수 × 같은 수'가 되는지(등량 조건) 먼저 확인!"
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]

# ── R2_08/09/10 — U1 복습 항목으로 교체 (3.NBT 덧셈/뺄셈) ────────────────
U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the sum: 247 + 156.",
        "choices": ["A. 393", "B. 403", "C. 413", "D. 503"],
        "answer": "B",
        "explanation": "247+156: 7+6=13 (carry 1), 4+5+1=10 (carry 1), 2+1+1=4. Result: 403.",
        "hints": [
            "Line up the digits — ones, tens, hundreds.",
            "Don't forget to carry when a column sum is 10 or more.",
        ],
        "feedback": {
            "correct": "Right — 403.",
            "incorrect": "247+156=403. Watch the carries.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 538 − 274.",
        "choices": ["A. 254", "B. 264", "C. 274", "D. 364"],
        "answer": "B",
        "explanation": "538−274: 8−4=4. 3−7 needs borrow → 13−7=6, hundreds becomes 4. 4−2=2. Result: 264.",
        "hints": [
            "Subtract right to left: ones, tens, hundreds.",
            "Borrow from the next column if the top digit is smaller.",
        ],
        "feedback": {
            "correct": "Right — 264.",
            "incorrect": "538−274=264. Remember to borrow.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "Maya had 425 stickers. She gave 138 to her friend, then earned 56 more. How many stickers does she have now?",
        "choices": ["A. 287", "B. 343", "C. 363", "D. 619"],
        "answer": "B",
        "explanation": "Step 1: 425−138=287. Step 2: 287+56=343.",
        "hints": [
            "Two steps: subtract first (gave away), then add (earned).",
            "Be careful with borrow in 425−138 and carry in 287+56.",
        ],
        "feedback": {
            "correct": "Right — 343 stickers.",
            "incorrect": "425−138=287, then 287+56=343.",
        },
        "review_from": "U1",
    },
]


def upgrade():
    """L1 파일을 7단계 검증 프로토콜에 맞게 업그레이드"""
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)

    # ── 멱등성 가드 ──
    if "pretest" in d:
        print("⚠️  이미 업그레이드된 파일입니다. 건너뜁니다.")
        return

    # ── 원본 items 추출 및 LN_ → LEARN_ 아이디 정규화 ──
    raw_items = d.pop("items", [])
    for item in raw_items:
        if item["id"].startswith("LN_"):
            item["id"] = f"LEARN_{item['id'][3:]}"

    # ── 섹션별 분류 ──
    sections_map: dict = {
        "pretest": [],
        "learn": [],
        "try": [],
        "practice_r1": [],
        "practice_r2": [],
        "practice_r3": [],
    }
    for item in raw_items:
        sec = item.get("section", "")
        if sec in sections_map:
            sections_map[sec].append(item)

    # ── 신규 LEARN 카드 추가 ──
    sections_map["learn"].extend(NEW_LEARN_CARDS)

    # ── R2_08/09/10 U1 복습으로 교체 ──
    r2_keep_ids = {"R2_01","R2_02","R2_03","R2_04","R2_05","R2_06","R2_07"}
    sections_map["practice_r2"] = [
        i for i in sections_map["practice_r2"] if i["id"] in r2_keep_ids
    ]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    # ── 모든 문항에 공통 필드 적용 ──
    for sec_key, items in sections_map.items():
        sections_map[sec_key] = [add_item_fields(item) for item in items]

    # ── 섹션별 문항 수 검증 ──
    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별 문항 수:", counts)
    total = sum(counts.values())
    print(f"총 문항 수: {total} (목표: 43)")
    assert counts["pretest"] == 5,       f"PT 오류: {counts['pretest']}"
    assert counts["learn"] == 8,         f"LEARN 오류: {counts['learn']}"
    assert counts["try"] == 5,           f"TRY 오류: {counts['try']}"
    assert counts["practice_r1"] == 10,  f"R1 오류: {counts['practice_r1']}"
    assert counts["practice_r2"] == 10,  f"R2 오류: {counts['practice_r2']}"
    assert counts["practice_r3"] == 5,   f"R3 오류: {counts['practice_r3']}"
    assert total == 43,                  f"총 문항 오류: {total}"

    # ── R2 마지막 25% U1 복습 검증 ──
    r2_items = sections_map["practice_r2"]
    u1_review = [i for i in r2_items if i.get("review_from") == "U1"]
    print(f"R2 U1 복습 문항: {len(u1_review)}개 (목표: 3)")

    # ── 최상위 섹션 키 저장 ──
    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    # ── vertical_alignment 추가 ──
    d["vertical_alignment"] = {
        "prerequisite": "G2 — 같은 수 반복 더하기, 2·5·10 건너뛰며 세기 (2.OA.C.4)",
        "current":      "G3 — 등량 그룹의 곱 해석; 그룹 수 × 그룹 크기 (3.OA.A.1)",
        "successor":    "G4 — 곱셈 비교; 'n배' 관계 이해 (4.OA.A.1)",
    }

    # ── 메타데이터 갱신 ──
    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = total
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u3_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    # ── 파일 저장 ──
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   총 {total}개 문항 (PT={counts['pretest']} "
          f"LEARN={counts['learn']} TRY={counts['try']} "
          f"R1={counts['practice_r1']} R2={counts['practice_r2']} "
          f"R3={counts['practice_r3']})")


if __name__ == "__main__":
    upgrade()
