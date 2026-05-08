"""
G3 U2 L7 — Use and Make Line Plots 7단계 업그레이드 스크립트
=============================================================
목적: L7_use_and_make_line_plots.json을 7단계 검증 프로토콜에 맞게 업그레이드
- 27개 → 43개 문항 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
- LN_ → LEARN_ 아이디 정규화
- cpa_phase → cpa_stage 필드 정규화
- 최상위 섹션 키 구조로 변환
- vertical_alignment, cpa_stage, feedback_correct, verification 블록 추가
- R2 마지막 25%에 U1 복습 연계 (R2_08/09/10)
- 표준: 3.MD.B.4 (라인 플롯 제작·독해)
"""

import json
import pathlib

# ── 경로 설정 ──────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U2_represent_interpret_data/L7_use_and_make_line_plots.json"

# ── 오류 유형 맵 (3.MD.B.4 미스컨셉션 ID) ─────────────────────────────────
ERRORS_MAP = {
    # ── PRETEST ──
    "PT_01": ["3.MD.B.4.M01"],                          # 축 레이블 값을 개수로 읽음
    "PT_02": ["3.MD.B.4.M01"],                          # X = 1개 임을 모름
    "PT_03": ["3.MD.B.4.M02"],                          # 미만 경계 포함 오류
    "PT_04": ["3.MD.B.4.M03"],                          # 전체 합산 미실행
    "PT_05": ["3.MD.B.4.M06"],                          # 최빈값 잘못 선택
    # ── LEARN (개념 카드 — 오류 없음) ──
    "LEARN_01": [],
    "LEARN_02": [],
    "LEARN_03": [],
    "LEARN_04": [],
    "LEARN_05": [],
    "LEARN_06": [],
    "LEARN_07": [],
    "LEARN_08": [],
    # ── TRY ──
    "TRY_01": ["3.MD.B.4.M01"],                         # 레이블 값 혼동
    "TRY_02": ["3.MD.B.4.M02", "3.MD.B.4.M07"],         # ≥ 경계 + ½눈금 오배치
    "TRY_03": ["3.MD.B.4.M02"],                         # 이상 경계 포함 혼동
    "TRY_04": ["3.MD.B.4.M02", "3.MD.B.4.M07"],         # < 경계 + ½눈금 오류
    "TRY_05": ["3.MD.B.4.M06", "3.MD.B.4.M03"],         # 최빈값·최솟값 혼동
    # ── R1 ──
    "R1_01": ["3.MD.B.4.M06"],                          # 최빈값 오선택
    "R1_02": ["3.MD.B.4.M03"],                          # 특정값 vs 전체 혼동
    "R1_03": ["3.MD.B.4.M04"],                          # 0 X 값 수직선 생략
    "R1_04": ["3.MD.B.4.M02"],                          # ≥ 경계 포함 오류
    "R1_05": ["3.MD.B.4.M04"],                          # 0 X 값 존재 의미 오해
    "R1_06": ["3.MD.B.4.M02", "3.MD.B.4.M07"],         # < 경계 + ½눈금
    "R1_07": ["3.MD.B.4.M07", "3.MD.B.4.M06"],         # ¼눈금 오배치·최빈값
    "R1_08": ["3.MD.B.4.M01", "3.MD.B.4.M03"],         # 특정 열 고립 실패
    "R1_09": ["3.MD.B.4.M03"],                          # 전체 합산
    "R1_10": ["3.MD.B.4.M02", "3.MD.B.4.M07"],         # > 경계 + ½눈금
    # ── R2 ──
    "R2_01": ["3.MD.B.4.M02"],                          # 경계값 이중 포함
    "R2_02": ["3.MD.B.4.M05"],                          # X 개수 ≠ 데이터 수
    "R2_03": ["3.MD.B.4.M06"],                          # 추가 후 최빈값 재계산 누락
    "R2_04": ["3.NBT.A.2"],                             # U1 복습: 3자리 덧셈
    "R2_05": ["3.MD.B.4.M02"],                          # 포함 범위 경계 오류
    "R2_06": ["3.MD.B.4.M03"],                          # 전체−특정 두 단계 누락
    "R2_07": ["3.MD.B.4.M06"],                          # 추가 후 최빈값 재계산
    "R2_08": ["3.MD.B.3.M01"],                          # U1 복습: 탤리 읽기
    "R2_09": ["3.MD.B.3.M04"],                          # U1 복습: 막대그래프 합계
    "R2_10": ["3.MD.B.3.M03"],                          # U1 복습: 막대그래프 비교
    # ── R3 ──
    "R3_01": ["3.MD.B.4.M03"],                          # 평균 계산 오류
    "R3_02": ["3.NBT.A.2"],                             # U1 복습: 3자리 뺄셈
    "R3_03": ["3.NBT.A.1"],                             # U1 복습: 백의 자리 반올림
    "R3_04": ["3.MD.B.4.M02", "3.MD.B.4.M07"],         # 포함 범위 + ½눈금
    "R3_05": ["3.NBT.A.1"],                             # U1 복습: 십의 자리 반올림
}

# ── 스킬 태그 맵 ───────────────────────────────────────────────────────────
SKILL_TAGS = {
    "PT_01": "read_x_count",
    "PT_02": "read_x_count",
    "PT_03": "boundary_comparison",
    "PT_04": "total_x_count",
    "PT_05": "find_mode",
    "LEARN_01": "read_x_count",
    "LEARN_02": "read_x_count",
    "LEARN_03": "plot_construction",
    "LEARN_04": "plot_construction",
    "LEARN_05": "boundary_comparison",
    "LEARN_06": "find_mode",
    "LEARN_07": "boundary_comparison",
    "LEARN_08": "read_x_count",
    "TRY_01": "read_x_count",
    "TRY_02": "boundary_comparison",
    "TRY_03": "boundary_comparison",
    "TRY_04": "boundary_comparison",
    "TRY_05": "find_mode",
    "R1_01": "find_mode",
    "R1_02": "total_x_count",
    "R1_03": "read_x_count",
    "R1_04": "boundary_comparison",
    "R1_05": "read_x_count",
    "R1_06": "boundary_comparison",
    "R1_07": "half_mark_reading",
    "R1_08": "read_x_count",
    "R1_09": "total_x_count",
    "R1_10": "boundary_comparison",
    "R2_01": "boundary_comparison",
    "R2_02": "plot_construction",
    "R2_03": "find_mode",
    "R2_04": "addition_3digit",          # U1 복습
    "R2_05": "boundary_comparison",
    "R2_06": "total_x_count",
    "R2_07": "find_mode",
    "R2_08": "tally_read",               # U1 복습
    "R2_09": "bar_graph_total",          # U1 복습
    "R2_10": "bar_graph_compare",        # U1 복습
    "R3_01": "total_x_count",
    "R3_02": "subtraction_3digit",       # U1 복습
    "R3_03": "round_to_hundred",         # U1 복습
    "R3_04": "boundary_comparison",
    "R3_05": "round_to_ten",             # U1 복습
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
    "LEARN_05": "pictorial",
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
    "R1_05": "pictorial",
    "R1_06": "pictorial",
    "R1_07": "pictorial",
    "R1_08": "pictorial",
    "R1_09": "pictorial",
    "R1_10": "pictorial",
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
    """검증 블록 생성 — L7 Use and Make Line Plots"""
    return {
        "concept_source": "Go Math Grade 3 Ch.2 Lesson 2.7 'Use and Make Line Plots' pp.89-92",
        "procedure_source": "EngageNY Grade 3 Module 6 Lessons 3-4 — Collecting and Displaying Data (Line Plots)",
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

    # CPA_MAP으로 덮어쓰기 (신규 카드 포함)
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]

    # skill_tag 추가
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "read_x_count")

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


# ── 신규 LEARN 카드 (LEARN_04 ~ LEARN_08) ─────────────────────────────────
NEW_LEARN_CARDS = [
    {
        "id": "LEARN_04",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "라인 플롯 만들기 실전 연습",
        "content": (
            "데이터: 연필 길이(인치) — 6, 6½, 6, 7, 6½, 6, 7½, 6½. "
            "단계 1: 최솟값(6) ~ 최댓값(7½) 수직선 그리기. "
            "단계 2: 제목 쓰기 — '연필 길이'. "
            "단계 3: 각 데이터 위에 X 표시: "
            "6인치=X X X / 6½인치=X X X / 7인치=X X / 7½인치=X. "
            "단계 4: X 개수(8) = 데이터 수(8) 확인 ✓. "
            "실수 주의: ½ 눈금을 통째로 건너뛰지 않는다."
        ),
        "data_table": {
            "title": "연필 길이",
            "type": "line_plot",
            "categories": ["6", "6½", "7", "7½"],
            "values": [3, 3, 2, 1],
            "scale": 1,
            "unit": "연필",
        },
        "cpa_stage": "pictorial",
        "visual_type": "line_plot_construction",
    },
    {
        "id": "LEARN_05",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "'미만'과 '이하' 구별하기",
        "content": (
            "미만(less than / <) → 경계값 포함 안 함. "
            "이하(less than or equal to / ≤) → 경계값 포함. "
            "예: '3인치 미만' → 1인치, 2인치만 세기 (3인치 제외). "
            "예: '3인치 이하' → 1인치, 2인치, 3인치 세기. "
            "팁: '미만'=열린 동그라미, '이하'=닫힌 동그라미로 표시."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "number_line_boundary",
    },
    {
        "id": "LEARN_06",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "최빈값(가장 많은 값) 찾기",
        "content": (
            "챔피언 스캔: 왼쪽 → 오른쪽으로 X 개수 비교. "
            "1단계: 첫 번째 열을 현재 챔피언으로 설정. "
            "2단계: 오른쪽으로 이동하며 더 높은 스택 찾기. "
            "3단계: 더 높으면 새 챔피언 교체. "
            "4단계: 끝까지 스캔 → 챔피언 = 최빈값. "
            "동점이면 두 값 모두 최빈값으로 보고."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "champion_scan_diagram",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "Math Talk: '이상'과 '초과' 구별하기",
        "content": (
            "이상(at least / ≥) → 경계값 포함. "
            "초과(more than / >) → 경계값 포함 안 함. "
            "예: '5인치 이상' → 5, 5½, 6 모두 세기. "
            "예: '5인치 초과' → 5½, 6만 세기 (5 제외). "
            "완전 정리: "
            "미만(<) 제외 | 이하(≤) 포함 | 초과(>) 제외 | 이상(≥) 포함."
        ),
        "cpa_stage": "abstract",
        "visual_type": "inequality_chart",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "라인 플롯 4가지 핵심 전략 요약",
        "content": (
            "전략 1 특정값 개수: 그 값 위 X만 세기 — 레이블을 답으로 쓰지 말 것. "
            "전략 2 전체 합계: 모든 X를 빠짐없이 세기 — 한 열만 세지 말 것. "
            "전략 3 범위 비교: 경계 포함/제외 확인 후 해당 열만 합산. "
            "전략 4 최빈값: 챔피언 스캔으로 가장 높은 스택 찾기. "
            "추가: ½·¼ 눈금은 반드시 수직선에 표시한다."
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]

# ── 신규 TRY 카드 (TRY_04 ~ TRY_05) ──────────────────────────────────────
NEW_TRY_CARDS = [
    {
        "id": "TRY_04",
        "section": "try",
        "difficulty": 2,
        "question": (
            "Line plot of ribbon lengths: 4 in=1X, 4½ in=3X, 5 in=5X, "
            "5½ in=2X, 6 in=1X. How many ribbons are shorter than 5½ inches?"
        ),
        "data_table": {
            "title": "Ribbon Lengths",
            "type": "line_plot",
            "categories": ["4", "4½", "5", "5½", "6"],
            "values": [1, 3, 5, 2, 1],
            "scale": 1,
            "unit": "ribbons",
        },
        "choices": [
            "A. 4",
            "B. 9",
            "C. 11",
            "D. 12",
        ],
        "answer": "B",
        "explanation": "Strictly < 5½: 4in(1)+4½in(3)+5in(5)=9.",
        "hints": [
            "'Shorter than 5½' means strictly less than — do NOT include 5½.",
            "Add only the values at 4, 4½, and 5.",
        ],
        "feedback": {
            "correct": "Excellent! You correctly excluded the boundary value.",
            "incorrect": "Not quite. The answer is B. Remember: 'shorter than 5½' excludes 5½ itself.",
        },
        "solution_steps": [
            "Identify: less than 5½ means < 5½ (do not include 5½).",
            "Count: 4in=1, 4½in=3, 5in=5.",
            "Add: 1+3+5=9.",
        ],
    },
    {
        "id": "TRY_05",
        "section": "try",
        "difficulty": 2,
        "question": (
            "Caterpillar length line plot: 1 in=2X, 1½ in=3X, 2 in=6X, "
            "2½ in=4X, 3 in=1X. What is the difference between the count "
            "of the most common length and the least common length?"
        ),
        "data_table": {
            "title": "Caterpillar Lengths",
            "type": "line_plot",
            "categories": ["1", "1½", "2", "2½", "3"],
            "values": [2, 3, 6, 4, 1],
            "scale": 1,
            "unit": "caterpillars",
        },
        "choices": [
            "A. 3",
            "B. 4",
            "C. 5",
            "D. 6",
        ],
        "answer": "C",
        "explanation": "Most common: 2 in (6 Xs). Least common: 3 in (1 X). 6−1=5.",
        "hints": [
            "Find the tallest stack (most) and the shortest stack (least).",
            "Subtract: most count − least count.",
        ],
        "feedback": {
            "correct": "Great! You found both the mode and minimum count correctly.",
            "incorrect": "Not quite. The answer is C. Find the tallest stack (6) and shortest (1), then subtract.",
        },
        "solution_steps": [
            "Champion scan: 2 in has 6 Xs — most common.",
            "Smallest stack: 3 in has 1 X — least common.",
            "Difference: 6−1=5.",
        ],
    },
]

# ── 신규 R1 카드 (R1_08 ~ R1_10) ─────────────────────────────────────────
NEW_R1_CARDS = [
    {
        "id": "R1_08",
        "section": "practice_r1",
        "difficulty": 1,
        "question": (
            "Caterpillar lengths: 1 in=2X, 1½ in=3X, 2 in=6X, 2½ in=4X, 3 in=1X. "
            "How many caterpillars are exactly 2 inches long?"
        ),
        "data_table": {
            "title": "Caterpillar Lengths",
            "type": "line_plot",
            "categories": ["1", "1½", "2", "2½", "3"],
            "values": [2, 3, 6, 4, 1],
            "scale": 1,
            "unit": "caterpillars",
        },
        "choices": [
            "A. 2",
            "B. 3",
            "C. 6",
            "D. 16",
        ],
        "answer": "C",
        "explanation": "6 Xs are stacked above the 2-inch mark.",
        "hints": [
            "Put your finger above the 2-inch mark. Count only those Xs.",
            "Do not count all the Xs — only the ones above 2.",
        ],
        "feedback": {
            "correct": "Great job! You found the right column.",
            "incorrect": "Not quite. The answer is C. Count only the Xs above 2 inches.",
        },
    },
    {
        "id": "R1_09",
        "section": "practice_r1",
        "difficulty": 1,
        "question": (
            "Same caterpillar line plot: 1 in=2X, 1½ in=3X, 2 in=6X, "
            "2½ in=4X, 3 in=1X. How many caterpillars were measured in all?"
        ),
        "data_table": {
            "title": "Caterpillar Lengths",
            "type": "line_plot",
            "categories": ["1", "1½", "2", "2½", "3"],
            "values": [2, 3, 6, 4, 1],
            "scale": 1,
            "unit": "caterpillars",
        },
        "choices": [
            "A. 6",
            "B. 12",
            "C. 16",
            "D. 21",
        ],
        "answer": "C",
        "explanation": "2+3+6+4+1=16 total caterpillars.",
        "hints": [
            "Count ALL Xs from every column.",
            "Add each column: 2+3+6+4+1.",
        ],
        "feedback": {
            "correct": "Excellent! You summed all the columns.",
            "incorrect": "Not quite. The answer is C. Add ALL the Xs: 2+3+6+4+1=16.",
        },
    },
    {
        "id": "R1_10",
        "section": "practice_r1",
        "difficulty": 2,
        "question": (
            "Worm lengths: 3 in=1X, 3¼ in=2X, 3½ in=4X, 3¾ in=3X, 4 in=2X. "
            "How many worms are longer than 3½ inches?"
        ),
        "data_table": {
            "title": "Worm Lengths",
            "type": "line_plot",
            "categories": ["3", "3¼", "3½", "3¾", "4"],
            "values": [1, 2, 4, 3, 2],
            "scale": 1,
            "unit": "worms",
        },
        "choices": [
            "A. 3",
            "B. 5",
            "C. 7",
            "D. 9",
        ],
        "answer": "B",
        "explanation": "Strictly > 3½: 3¾in(3)+4in(2)=5.",
        "hints": [
            "'Longer than 3½' means strictly greater than — do NOT include 3½.",
            "Add only 3¾ and 4.",
        ],
        "feedback": {
            "correct": "Well done! You excluded the boundary correctly.",
            "incorrect": "Not quite. The answer is B. 'Longer than 3½' excludes 3½: 3¾(3)+4(2)=5.",
        },
    },
]

# ── 신규 R2 카드 (R2_05 ~ R2_10) ─────────────────────────────────────────
NEW_R2_CARDS = [
    {
        "id": "R2_05",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "Test scores: 80=1X, 85=3X, 90=5X, 95=4X, 100=2X. "
            "How many students scored between 85 and 95 (inclusive)?"
        ),
        "data_table": {
            "title": "Test Scores",
            "type": "line_plot",
            "categories": ["80", "85", "90", "95", "100"],
            "values": [1, 3, 5, 4, 2],
            "scale": 1,
            "unit": "students",
        },
        "choices": [
            "A. 5",
            "B. 9",
            "C. 12",
            "D. 15",
        ],
        "answer": "C",
        "explanation": "85 to 95 inclusive: 85(3)+90(5)+95(4)=12.",
        "hints": [
            "Inclusive means include both 85 and 95.",
            "Add only the columns at 85, 90, and 95.",
        ],
        "feedback": {
            "correct": "Excellent! You included both boundary values.",
            "incorrect": "Not quite. The answer is C. 'Inclusive' includes 85 and 95: 3+5+4=12.",
        },
        "solution_steps": [
            "Range: 85, 90, 95 (both ends included).",
            "Add: 85(3)+90(5)+95(4)=12.",
        ],
    },
    {
        "id": "R2_06",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "Pencil lengths: 6 in=2X, 6½ in=4X, 7 in=3X, 7½ in=1X. "
            "How many pencils are NOT 7 inches?"
        ),
        "data_table": {
            "title": "Pencil Lengths",
            "type": "line_plot",
            "categories": ["6", "6½", "7", "7½"],
            "values": [2, 4, 3, 1],
            "scale": 1,
            "unit": "pencils",
        },
        "choices": [
            "A. 3",
            "B. 6",
            "C. 7",
            "D. 10",
        ],
        "answer": "C",
        "explanation": "Total: 2+4+3+1=10. Not 7 inches: 10−3=7.",
        "hints": [
            "Find the total number of pencils first.",
            "Then subtract the 7-inch pencils from the total.",
        ],
        "feedback": {
            "correct": "Nice two-step thinking!",
            "incorrect": "Not quite. The answer is C. Total=10; subtract 7in(3): 10−3=7.",
        },
        "solution_steps": [
            "Step 1: Count total Xs: 2+4+3+1=10.",
            "Step 2: Subtract 7-inch pencils: 10−3=7.",
        ],
    },
    {
        "id": "R2_07",
        "section": "practice_r2",
        "difficulty": 3,
        "question": (
            "Worm lengths: 3 in=1X, 3¼ in=2X, 3½ in=4X, 3¾ in=3X, 4 in=2X. "
            "If you add 2 more worms that are each 3¾ inches, "
            "what is the new most common length?"
        ),
        "data_table": {
            "title": "Worm Lengths",
            "type": "line_plot",
            "categories": ["3", "3¼", "3½", "3¾", "4"],
            "values": [1, 2, 4, 3, 2],
            "scale": 1,
            "unit": "worms",
        },
        "choices": [
            "A. 3½ inches (still 4 Xs)",
            "B. 3¾ inches (now 5 Xs)",
            "C. 4 inches (still 2 Xs)",
            "D. No change",
        ],
        "answer": "B",
        "explanation": "3¾ goes from 3→5 Xs. Now 5 > 4 (3½). New mode: 3¾ inches.",
        "hints": [
            "Update 3¾: it had 3 Xs, add 2 more → now 5 Xs.",
            "Compare updated stacks: 3½=4, 3¾=5. Which is taller?",
        ],
        "feedback": {
            "correct": "Great reasoning! You recalculated the mode after updating.",
            "incorrect": "Not quite. The answer is B. 3¾ becomes 5 Xs, which beats 3½ (4 Xs).",
        },
        "solution_steps": [
            "Update: 3¾ was 3 Xs + 2 new = 5 Xs.",
            "Compare: 3½=4 vs 3¾=5. 3¾ is now highest.",
            "New mode: 3¾ inches.",
        ],
    },
    {
        # U1 복습: 탤리 차트 읽기
        "id": "R2_08",
        "section": "practice_r2",
        "difficulty": 1,
        "question": (
            "A tally chart shows: Cats = |||| | (6 tallies), "
            "Dogs = |||| |||| (9 tallies), Fish = ||| (3 tallies). "
            "How many pets were counted in all?"
        ),
        "choices": [
            "A. 9",
            "B. 15",
            "C. 18",
            "D. 21",
        ],
        "answer": "C",
        "explanation": "Cats(6)+Dogs(9)+Fish(3)=18.",
        "hints": [
            "Count each group of tallies carefully (every 5 marks = one gate).",
            "Add all three totals together.",
        ],
        "feedback": {
            "correct": "Great tally reading!",
            "incorrect": "Not quite. The answer is C. 6+9+3=18.",
        },
        "review_from": "U1",
    },
    {
        # U1 복습: 막대그래프 전체 합계
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 1,
        "question": (
            "A bar graph shows favorite seasons: "
            "Spring=8, Summer=12, Fall=6, Winter=4. "
            "How many students answered in all?"
        ),
        "data_table": {
            "title": "Favorite Seasons",
            "type": "bar_graph",
            "categories": ["Spring", "Summer", "Fall", "Winter"],
            "values": [8, 12, 6, 4],
            "scale": 2,
            "unit": "students",
        },
        "choices": [
            "A. 12",
            "B. 20",
            "C. 26",
            "D. 30",
        ],
        "answer": "D",
        "explanation": "8+12+6+4=30.",
        "hints": [
            "Add ALL the bar values together.",
            "8+12=20, then 20+6=26, then 26+4=30.",
        ],
        "feedback": {
            "correct": "Excellent! You remembered to sum all bars.",
            "incorrect": "Not quite. The answer is D. 8+12+6+4=30.",
        },
        "review_from": "U1",
    },
    {
        # U1 복습: 막대그래프 비교
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "A bar graph shows fruit counts: Apples=15, Oranges=9, Bananas=12. "
            "How many more apples are there than oranges?"
        ),
        "data_table": {
            "title": "Fruit Count",
            "type": "bar_graph",
            "categories": ["Apples", "Oranges", "Bananas"],
            "values": [15, 9, 12],
            "scale": 3,
            "unit": "fruits",
        },
        "choices": [
            "A. 3",
            "B. 6",
            "C. 9",
            "D. 24",
        ],
        "answer": "B",
        "explanation": "15−9=6 more apples than oranges.",
        "hints": [
            "Find Apples (15) and Oranges (9).",
            "Subtract: bigger − smaller.",
        ],
        "feedback": {
            "correct": "Great subtraction thinking!",
            "incorrect": "Not quite. The answer is B. 15−9=6.",
        },
        "review_from": "U1",
    },
]


def upgrade():
    """L7 파일을 7단계 검증 프로토콜에 맞게 업그레이드"""
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)

    # ── 멱등성 가드: 이미 업그레이드된 파일이면 종료 ──
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

    # ── 신규 카드 추가 ──
    sections_map["learn"].extend(NEW_LEARN_CARDS)
    sections_map["try"].extend(NEW_TRY_CARDS)
    sections_map["practice_r1"].extend(NEW_R1_CARDS)
    sections_map["practice_r2"].extend(NEW_R2_CARDS)
    # R3는 이미 5개 — 추가 없음

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

    # ── R2 마지막 25% U1 복습 연계 확인 ──
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
        "prerequisite": "G2 — 정수 눈금 기초 라인 플롯 읽기 및 만들기 (2.MD.D.9)",
        "current":      "G3 — ½·¼인치 눈금 라인 플롯 제작; 데이터 범위·최빈값 파악 (3.MD.B.4)",
        "successor":    "G4 — 분수 단위 포함 라인 플롯에서 분수 덧셈·뺄셈 문제 풀기 (4.MD.B.4)",
    }

    # ── 메타데이터 갱신 ──
    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = total
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u2_l7.py"
    d["metadata"]["review_from_units"] = ["U1"]

    # ── 파일 저장 ──
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   총 {total}개 문항 저장 (PT={counts['pretest']} "
          f"LEARN={counts['learn']} TRY={counts['try']} "
          f"R1={counts['practice_r1']} R2={counts['practice_r2']} "
          f"R3={counts['practice_r3']})")


if __name__ == "__main__":
    upgrade()
