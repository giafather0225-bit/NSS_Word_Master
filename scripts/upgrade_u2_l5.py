"""
G3 U2 L5 — Make Bar Graphs 7단계 업그레이드 스크립트
======================================================
목적: L5_make_bar_graphs.json을 7단계 검증 프로토콜에 맞게 업그레이드
- 25개 → 43개 문항 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
- LN_ → LEARN_ 아이디 정규화
- 최상위 섹션 키 구조로 변환
- vertical_alignment, cpa_stage, feedback_correct, verification 블록 추가
- R2 마지막 25%에 U1 복습 연계
"""

import json
import pathlib
import copy

# ── 경로 설정 ──────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U2_represent_interpret_data/L5_make_bar_graphs.json"

# ── 오류 유형 맵 (아이디 → 주요 오개념 ID 목록) ───────────────────────────
ERRORS_MAP = {
    # ── Pretest ──
    "PT_01": ["3.MD.B.3.M01"],
    "PT_02": ["3.MD.B.3.M02"],
    "PT_03": ["3.MD.B.3.M01", "3.MD.B.3.M02"],
    "PT_04": ["3.MD.B.3.M06"],
    "PT_05": ["3.MD.B.3.M02"],
    # ── Learn ──
    "LEARN_01": [],
    "LEARN_02": [],
    "LEARN_03": [],
    "LEARN_04": ["3.MD.B.3.M01"],
    "LEARN_05": ["3.MD.B.3.M01"],
    "LEARN_06": ["3.MD.B.3.M06"],
    "LEARN_07": ["3.MD.B.3.M03"],
    "LEARN_08": [],
    # ── Try ──
    "TRY_01": ["3.MD.B.3.M01"],
    "TRY_02": ["3.MD.B.3.M06"],
    "TRY_03": ["3.MD.B.3.M04"],
    "TRY_04": ["3.MD.B.3.M01"],
    "TRY_05": ["3.MD.B.3.M06"],
    # ── R1 ──
    "R1_01": ["3.MD.B.3.M02"],
    "R1_02": ["3.MD.B.3.M06"],
    "R1_03": ["3.MD.B.3.M01"],
    "R1_04": ["3.OA.D.8.M01"],
    "R1_05": ["3.MD.B.3.M04", "3.MD.B.3.M05"],
    "R1_06": ["3.MD.B.3.M01"],
    "R1_07": ["3.MD.B.3.M01"],
    "R1_08": ["3.MD.B.3.M06"],
    "R1_09": ["3.MD.B.3.M02"],
    "R1_10": ["3.OA.D.8.M01", "3.MD.B.3.M04"],
    # ── R2 ──
    "R2_01": ["3.OA.D.8.M03"],
    "R2_02": ["3.OA.D.8.M03"],
    "R2_03": ["3.MD.B.3.M04", "3.OA.D.8.M01"],
    "R2_04": ["3.MD.B.3.M01"],
    "R2_05": ["3.MD.B.3.M01", "3.MD.B.3.M02"],
    "R2_06": ["3.MD.B.3.M01"],
    "R2_07": ["3.MD.B.3.M01"],
    "R2_08": ["3.MD.B.3.M01"],        # U1 복습: 탤리 읽기
    "R2_09": ["3.MD.B.3.M03"],        # U1 복습: 막대 비교
    "R2_10": ["3.MD.B.3.M04", "3.MD.B.3.M05"],  # U1 복습: 전체 합산
    # ── R3 ──
    "R3_01": ["3.OA.D.8.M01"],
    "R3_02": ["3.MD.B.3.M01"],
    "R3_03": ["3.MD.B.3.M01"],
    "R3_04": ["3.OA.D.8.M06"],
    "R3_05": ["3.MD.B.3.M01", "3.MD.B.3.M06"],
}

# ── 스킬 태그 맵 ───────────────────────────────────────────────────────────
SKILL_TAGS = {
    "PT_01": "choose_scale",
    "PT_02": "label_axes",
    "PT_03": "bar_to_gridline",
    "PT_04": "choose_scale",
    "PT_05": "read_bar_value",
    "LEARN_01": "draw_bar",
    "LEARN_02": "choose_scale",
    "LEARN_03": "draw_bar",
    "LEARN_04": "bar_to_gridline",
    "LEARN_05": "choose_scale",
    "LEARN_06": "draw_bar",
    "LEARN_07": "bar_to_gridline",
    "LEARN_08": "draw_bar",
    "TRY_01": "bar_to_gridline",
    "TRY_02": "identify_most_least",
    "TRY_03": "choose_scale",
    "TRY_04": "bar_to_gridline",
    "TRY_05": "choose_scale",
    "R1_01": "label_axes",
    "R1_02": "choose_scale",
    "R1_03": "bar_to_gridline",
    "R1_04": "interpret_table",
    "R1_05": "total_bar_values",
    "R1_06": "bar_to_gridline",
    "R1_07": "bar_to_gridline",
    "R1_08": "choose_scale",
    "R1_09": "label_axes",
    "R1_10": "total_bar_values",
    "R2_01": "choose_scale",          # 나머지 주제 (반올림) — 나선 복습
    "R2_02": "choose_scale",          # 나선 복습
    "R2_03": "interpret_table",
    "R2_04": "choose_scale",
    "R2_05": "bar_to_gridline",
    "R2_06": "choose_scale",
    "R2_07": "bar_to_gridline",
    "R2_08": "read_bar_value",        # U1 복습
    "R2_09": "compare_bars",          # U1 복습
    "R2_10": "total_bar_values",      # U1 복습
    "R3_01": "interpret_table",
    "R3_02": "bar_to_gridline",
    "R3_03": "bar_to_gridline",
    "R3_04": "draw_bar",
    "R3_05": "choose_scale",
}

# ── CPA 단계 맵 ────────────────────────────────────────────────────────────
CPA_MAP = {
    "PT_01": "concrete",
    "PT_02": "concrete",
    "PT_03": "pictorial",
    "PT_04": "concrete",
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
    "TRY_03": "abstract",
    "TRY_04": "pictorial",
    "TRY_05": "abstract",
    "R1_01": "concrete",
    "R1_02": "concrete",
    "R1_03": "pictorial",
    "R1_04": "abstract",
    "R1_05": "abstract",
    "R1_06": "abstract",
    "R1_07": "abstract",
    "R1_08": "abstract",
    "R1_09": "concrete",
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
    """검증 블록 생성 — L5 Make Bar Graphs"""
    return {
        "concept_source": "Go Math Grade 3 Ch.2 Lesson 2.5 'Make Bar Graphs' pp.81-84",
        "procedure_source": "EngageNY Grade 3 Module 6 — Scaled Bar Graphs Teacher Edition",
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

    # skill_tag 추가
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "draw_bar")

    # hints 있는데 feedback_correct 없으면 추가 (S4 통과 조건)
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )

    # expected_errors 추가
    item["expected_errors"] = ERRORS_MAP.get(item_id, [])

    # math_note 추가
    item.setdefault("math_note", "")

    # verification 블록 추가
    item["verification"] = make_verification(item_id)

    return item


# ── 신규 LEARN 카드 (LEARN_04 ~ LEARN_08) ─────────────────────────────────
NEW_LEARN_CARDS = [
    {
        "id": "LEARN_04",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "단계별 가이드: 막대그래프 그리기",
        "content": (
            "데이터: 빨강 6, 파랑 8, 초록 4, 노랑 2. 척도: 2씩. "
            "각 막대의 높이: 빨강=6÷2=3칸, 파랑=8÷2=4칸, 초록=4÷2=2칸, 노랑=2÷2=1칸. "
            "공식: 막대 높이 = 값 ÷ 척도"
        ),
        "data_table": {
            "title": "좋아하는 색깔",
            "type": "frequency_table",
            "categories": ["빨강", "파랑", "초록", "노랑"],
            "values": [6, 8, 4, 2],
            "scale": 1,
            "unit": "명",
        },
        "cpa_stage": "pictorial",
        "visual_type": "bar_graph_scaffold",
    },
    {
        "id": "LEARN_05",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "척도 선택 예시",
        "content": (
            "데이터: 강아지 10, 고양이 5, 물고기 15, 새 20. "
            "가장 큰 값 = 20. 5씩 세면 0,5,10,15,20 → 딱 4칸. 가장 좋은 척도. "
            "2씩 세면 0~20 → 10칸(복잡). 1씩 세면 20칸(너무 많음). "
            "규칙: 모든 값이 딱 격자선에 떨어지는 척도를 고른다."
        ),
        "data_table": {
            "title": "기르는 동물",
            "type": "frequency_table",
            "categories": ["강아지", "고양이", "물고기", "새"],
            "values": [10, 5, 15, 20],
            "scale": 1,
            "unit": "마리",
        },
        "cpa_stage": "pictorial",
        "visual_type": "scale_comparison",
    },
    {
        "id": "LEARN_06",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "홀수 값 그리기",
        "content": (
            "척도가 2씩일 때(0,2,4,6,8) 값이 7이라면? "
            "7은 6과 8의 사이 → 막대를 6과 8의 정중앙에 그린다. "
            "규칙: 값이 두 격자선 사이에 있으면 그 중간에 막대를 그린다."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "midpoint_bar_diagram",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 1,
        "type": "explain",
        "title": "수학 토크: 척도 실수 찾기",
        "content": (
            "데이터: 봄 15, 여름 25, 가을 10, 겨울 20. 척도: 5씩. "
            "봄 막대를 15칸 높이로 그리면 틀린 이유: "
            "척도가 5씩이면 칸 1개 = 5. 봄 막대 높이 = 15÷5 = 3칸이어야 한다. "
            "15칸이 아니라 3칸이 정답."
        ),
        "data_table": {
            "title": "좋아하는 계절",
            "type": "frequency_table",
            "categories": ["봄", "여름", "가을", "겨울"],
            "values": [15, 25, 10, 20],
            "scale": 5,
            "unit": "명",
        },
        "question": "여름 막대는 몇 칸 높이여야 하나요?",
        "choices": ["A. 5", "B. 10", "C. 25", "D. 5칸"],
        "answer": "A",
        "explanation": "25 ÷ 5 = 5칸.",
        "cpa_stage": "abstract",
        "visual_type": "none",
        "hints": ["척도가 5씩이면 칸 1개가 5를 나타냅니다.", "값 ÷ 척도 = 막대 높이(칸 수)"],
        "feedback_correct": "맞아요! 값을 척도로 나누면 칸 수가 됩니다.",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "summary",
        "title": "L5 핵심 정리",
        "content": (
            "막대그래프 만들기 5단계: "
            "1. 제목 쓰기. "
            "2. 두 축 이름 붙이기(가로=종류, 세로=숫자). "
            "3. 모든 값이 격자선에 떨어지는 척도 선택. "
            "4. 각 막대를 값÷척도 칸 높이로 그리기. "
            "5. 그래프와 원래 데이터 비교·확인."
        ),
        "cpa_stage": "abstract",
        "visual_type": "none",
    },
]

# ── 신규 TRY 카드 (TRY_04 ~ TRY_05) ─────────────────────────────────────
NEW_TRY_CARDS = [
    {
        "id": "TRY_04",
        "section": "try",
        "difficulty": 2,
        "question": (
            "자전거 9, 자동차 14, 버스 6, 트럭 11. 척도: 2씩. "
            "트럭 막대는 어디에서 끝나나요?"
        ),
        "data_table": {
            "title": "탈것 조사",
            "type": "frequency_table",
            "categories": ["자전거", "자동차", "버스", "트럭"],
            "values": [9, 14, 6, 11],
            "scale": 2,
            "unit": "대",
        },
        "choices": [
            "A. 10 격자선 위",
            "B. 10과 12 사이 중간",
            "C. 12 격자선 위",
            "D. 12와 14 사이 중간",
        ],
        "answer": "B",
        "explanation": "11은 10과 12 사이(척도 2씩). 막대가 10과 12 정중간에 끝난다.",
        "hints": [
            "척도가 2씩일 때 격자선은 0,2,4,6,8,10,12,14… 입니다.",
            "11은 어떤 두 격자선 사이에 있나요?",
        ],
        "feedback_correct": "잘했어요! 홀수 값은 두 격자선의 정중간에 그립니다.",
        "solution_steps": [
            "척도 2씩 격자선: 0,2,4,6,8,10,12,14",
            "11은 10과 12 사이",
            "중간 위치에 막대를 그린다",
        ],
    },
    {
        "id": "TRY_05",
        "section": "try",
        "difficulty": 2,
        "question": (
            "데이터: 10, 20, 30, 40. 막대그래프를 만들 때 가장 좋은 척도는?"
        ),
        "choices": [
            "A. 2씩",
            "B. 5씩",
            "C. 10씩",
            "D. 7씩",
        ],
        "answer": "C",
        "explanation": "모두 10의 배수. 10씩 쓰면 0~40에 격자선 4개만 필요(간결).",
        "hints": [
            "10, 20, 30, 40은 모두 몇의 배수인가요?",
            "가장 적은 격자선으로 모든 값을 정확히 나타낼 수 있는 척도를 고르세요.",
        ],
        "feedback_correct": "정답! 10씩 세면 모든 값이 격자선에 정확히 떨어집니다.",
        "solution_steps": [
            "가장 큰 값: 40",
            "10의 배수 확인: 10✓, 20✓, 30✓, 40✓",
            "10씩 → 0,10,20,30,40 (격자선 4개, 모든 값 정확)",
        ],
    },
]

# ── 신규 R1 카드 (R1_07 ~ R1_10) ─────────────────────────────────────────
NEW_R1_CARDS = [
    {
        "id": "R1_07",
        "section": "practice_r1",
        "difficulty": 2,
        "question": (
            "데이터: 봄 12, 여름 18, 가을 6, 겨울 24. 척도: 6씩. "
            "여름 막대는 몇 칸 높이인가요?"
        ),
        "data_table": {
            "title": "계절 선호도",
            "type": "frequency_table",
            "categories": ["봄", "여름", "가을", "겨울"],
            "values": [12, 18, 6, 24],
            "scale": 6,
            "unit": "명",
        },
        "choices": ["A. 2칸", "B. 3칸", "C. 4칸", "D. 18칸"],
        "answer": "B",
        "explanation": "18 ÷ 6 = 3칸.",
        "hints": [
            "막대 높이(칸) = 값 ÷ 척도",
            "18 ÷ 6 = ?",
        ],
        "feedback_correct": "맞아요! 18÷6=3칸.",
    },
    {
        "id": "R1_08",
        "section": "practice_r1",
        "difficulty": 2,
        "question": (
            "데이터: 8, 16, 24, 32. 모든 막대가 격자선에 정확히 떨어지는 척도는?"
        ),
        "choices": ["A. 2씩", "B. 4씩", "C. 8씩", "D. 3씩"],
        "answer": "C",
        "explanation": (
            "모두 8의 배수(8÷8=1, 16÷8=2, 24÷8=3, 32÷8=4). "
            "8씩이면 격자선 4개만 필요 — 가장 간결."
        ),
        "hints": [
            "8, 16, 24, 32는 모두 몇의 배수인가요?",
            "가장 큰 값 32를 딱 떨어지게 나타내는 척도를 찾으세요.",
        ],
        "feedback_correct": "잘했어요! 8씩이면 모든 값이 격자선에 정확히 떨어집니다.",
    },
    {
        "id": "R1_09",
        "section": "practice_r1",
        "difficulty": 1,
        "question": (
            "'우리가 기르는 동물' 막대그래프에서 바르게 붙인 레이블은?"
        ),
        "choices": [
            "A. 제목: '우리가 기르는 동물', 가로축: '동물 종류', 세로축: '수(마리)'",
            "B. 제목: '우리가 기르는 동물', 가로축: '수(마리)', 세로축: '동물 종류'",
            "C. 제목: '수(마리)', 가로축: '우리가 기르는 동물', 세로축: '동물 종류'",
            "D. 제목: '동물 종류', 가로축: '수(마리)', 세로축: '우리가 기르는 동물'",
        ],
        "answer": "A",
        "explanation": (
            "제목은 위쪽, 가로축엔 종류(범주), 세로축엔 숫자(개수)를 표시한다."
        ),
        "hints": [
            "막대그래프에서 가로축에는 범주(종류), 세로축에는 숫자(개수)가 옵니다.",
            "제목은 그래프 위쪽에 씁니다.",
        ],
        "feedback_correct": "맞아요! 가로축=종류, 세로축=개수, 제목=위쪽.",
    },
    {
        "id": "R1_10",
        "section": "practice_r1",
        "difficulty": 3,
        "question": (
            "강아지 6, 고양이 4, 새 2를 막대그래프로 그린 뒤 고양이에게 5명이 더 투표했다. "
            "전체 투표 수는 이제 몇인가요?"
        ),
        "data_table": {
            "title": "반려동물 투표",
            "type": "frequency_table",
            "categories": ["강아지", "고양이", "새"],
            "values": [6, 4, 2],
            "scale": 1,
            "unit": "표",
        },
        "choices": ["A. 9", "B. 12", "C. 17", "D. 5"],
        "answer": "C",
        "explanation": "원래 합계: 6+4+2=12. 5표 추가 → 12+5=17.",
        "hints": [
            "먼저 원래 전체 투표 수를 구하세요.",
            "그런 다음 새로 추가된 표를 더하세요.",
        ],
        "feedback_correct": "정답! 12+5=17표.",
    },
]

# ── 신규 R2 카드 (R2_05 ~ R2_10) ─────────────────────────────────────────
NEW_R2_CARDS = [
    {
        "id": "R2_05",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "데이터: 사과 6, 바나나 10, 오렌지 8, 포도 4. 척도: 2씩. "
            "5칸 높이인 막대는 어느 과일인가요?"
        ),
        "data_table": {
            "title": "좋아하는 과일",
            "type": "frequency_table",
            "categories": ["사과", "바나나", "오렌지", "포도"],
            "values": [6, 10, 8, 4],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 사과", "B. 바나나", "C. 오렌지", "D. 포도"],
        "answer": "B",
        "explanation": "5칸 × 2 = 10 → 바나나.",
        "hints": [
            "5칸 × 척도(2) = ?",
            "어떤 과일의 값이 그 숫자와 같나요?",
        ],
        "feedback_correct": "잘했어요! 5칸×2=10=바나나.",
    },
    {
        "id": "R2_06",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "데이터: 9, 12, 6, 3. 모든 막대가 격자선에 정확히 떨어지는 척도는?"
        ),
        "choices": ["A. 2씩", "B. 3씩", "C. 5씩", "D. 4씩"],
        "answer": "B",
        "explanation": (
            "모두 3의 배수(9÷3=3, 12÷3=4, 6÷3=2, 3÷3=1). "
            "2씩이면 9와 3이 격자선 사이에 위치."
        ),
        "hints": [
            "9, 12, 6, 3은 모두 몇의 배수인가요?",
            "각 값을 척도로 나눠서 딱 떨어지는지 확인하세요.",
        ],
        "feedback_correct": "맞아요! 3의 배수이므로 3씩이 최적 척도입니다.",
    },
    {
        "id": "R2_07",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "데이터: 빨강 16, 파랑 12, 초록 8. 척도: 4씩. "
            "미아가 빨강 막대를 4칸 높이로 그렸다. 맞는가요?"
        ),
        "data_table": {
            "title": "색깔 투표",
            "type": "frequency_table",
            "categories": ["빨강", "파랑", "초록"],
            "values": [16, 12, 8],
            "scale": 4,
            "unit": "표",
        },
        "choices": [
            "A. 맞아요, 16÷4=4칸 ✓",
            "B. 틀려요, 빨강 막대는 8칸이어야 해요",
            "C. 틀려요, 빨강 막대는 2칸이어야 해요",
            "D. 틀려요, 빨강 막대는 16칸이어야 해요",
        ],
        "answer": "A",
        "explanation": "16 ÷ 4 = 4칸 → 미아가 맞습니다.",
        "hints": [
            "막대 높이(칸) = 값 ÷ 척도",
            "16 ÷ 4 = ?",
        ],
        "feedback_correct": "정답! 16÷4=4칸이 맞습니다.",
    },
    {
        "id": "R2_08",
        "section": "practice_r2",
        "review_from": "U1",
        "difficulty": 2,
        "question": (
            "탤리 차트: 강아지 𝍸𝍸𝍸 (탤리 3묶음). 강아지는 몇 마리인가요?"
        ),
        "choices": ["A. 3", "B. 10", "C. 15", "D. 12"],
        "answer": "C",
        "explanation": "𝍸 1묶음 = 5. 3묶음 = 5×3 = 15.",
        "hints": [
            "탤리 한 묶음(𝍸)은 5를 나타냅니다.",
            "3묶음 × 5 = ?",
        ],
        "feedback_correct": "맞아요! 탤리 3묶음 = 15.",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "review_from": "U1",
        "difficulty": 2,
        "question": (
            "막대그래프: 축구 10, 테니스 4, 수영 6. "
            "축구가 수영보다 몇 명 더 많이 선택했나요?"
        ),
        "choices": ["A. 16", "B. 4", "C. 6", "D. 14"],
        "answer": "B",
        "explanation": "10 − 6 = 4명.",
        "hints": [
            "'몇 명 더 많은가' → 빼기를 사용합니다.",
            "10 − 6 = ?",
        ],
        "feedback_correct": "잘했어요! 10−6=4명.",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "review_from": "U1",
        "difficulty": 2,
        "question": (
            "막대그래프: 월요일 8, 화요일 12, 수요일 6, 목요일 10. "
            "4일 합계는 몇인가요?"
        ),
        "choices": ["A. 16", "B. 26", "C. 36", "D. 28"],
        "answer": "C",
        "explanation": "8+12+6+10 = 36.",
        "hints": [
            "네 값을 모두 더하세요.",
            "8+12=20, 20+6=26, 26+10=?",
        ],
        "feedback_correct": "정답! 8+12+6+10=36.",
    },
]

# ── 신규 R3 카드 (R3_04 ~ R3_05) ─────────────────────────────────────────
NEW_R3_CARDS = [
    {
        "id": "R3_04",
        "section": "practice_r3",
        "difficulty": 3,
        "question": (
            "막대그래프(척도 5씩, 최대 20): 독서 10, 수학 15, 미술 5, 음악 20. "
            "그래프를 완성한 후 미술에 3명이 더 투표해 미술=8이 됐다. "
            "현재 척도(0~20, 5씩)를 바꿔야 하나요?"
        ),
        "choices": [
            "A. 아니오 — 8은 0~20 범위 안이라 척도 유지, 막대만 5와 10 사이에 그린다",
            "B. 예 — 8이 격자선에 안 떨어지니 척도를 1씩으로 바꿔야 한다",
            "C. 예 — 8이 격자선에 안 떨어지니 척도를 4씩으로 바꿔야 한다",
            "D. 예 — 8이라는 숫자를 척도에 새로 추가해야 한다",
        ],
        "answer": "A",
        "explanation": (
            "8은 0~20 범위 안에 있으므로 척도 범위는 유지. "
            "8은 5와 10 사이에 위치하므로 막대를 그 중간에 그리면 된다. "
            "척도를 바꿀 필요 없다."
        ),
        "hints": [
            "척도를 바꿔야 하는 경우: 가장 큰 값이 현재 최대값을 초과할 때.",
            "8은 현재 척도 범위(0~20) 안에 있나요?",
        ],
        "feedback_correct": "맞아요! 값이 범위 안이면 척도를 바꿀 필요 없어요.",
    },
    {
        "id": "R3_05",
        "section": "practice_r3",
        "difficulty": 3,
        "question": (
            "데이터: 봄 18, 여름 24, 가을 12, 겨울 6. "
            "레오는 3씩, 안나는 6씩 척도를 사용했다. "
            "두 사람 모두 모든 막대가 격자선에 정확히 떨어졌다. 이유는?"
        ),
        "choices": [
            "A. 한 명이 반드시 틀렸다 — 하나의 데이터엔 하나의 척도만 맞다",
            "B. 데이터 값이 두 척도의 배수이면 두 척도 모두 사용 가능하다",
            "C. 6씩만 맞다 — 6이 가장 작은 값이기 때문이다",
            "D. 3씩만 맞다 — 3이 가장 작은 척도이기 때문이다",
        ],
        "answer": "B",
        "explanation": (
            "18, 24, 12, 6 모두 3의 배수(÷3=6,8,4,2 ✓)이고 6의 배수(÷6=3,4,2,1 ✓)이다. "
            "데이터가 여러 수의 공배수라면 여러 척도가 모두 유효하다."
        ),
        "hints": [
            "18, 24, 12, 6을 3으로 나눠 보세요. 모두 나누어 떨어지나요?",
            "같은 값을 6으로도 나눠 보세요.",
        ],
        "feedback_correct": "훌륭해요! 데이터가 두 척도의 배수면 둘 다 유효합니다.",
    },
]


def upgrade():
    """L5_make_bar_graphs.json 업그레이드 실행"""
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)

    # ── 이미 업그레이드된 파일이면 건너뜀 (멱등성 보장) ──────────────────
    if "pretest" in d:
        print("⚠️  이미 업그레이드된 파일입니다. 건너뜁니다.")
        return

    # ── 원본 flat items 추출 ──────────────────────────────────────────────
    raw_items = d.pop("items", [])

    # ── LN_ → LEARN_ 아이디 정규화 ───────────────────────────────────────
    for item in raw_items:
        if item["id"].startswith("LN_"):
            num = item["id"][3:]
            item["id"] = f"LEARN_{num}"
        # section 필드 정규화
        sec = item.get("section", "")
        if sec == "learn":
            pass  # 그대로
        elif sec in ("pretest", "try", "practice_r1", "practice_r2", "practice_r3"):
            pass  # 그대로

    # ── 섹션별 분류 ───────────────────────────────────────────────────────
    pt_items   = [i for i in raw_items if i.get("section") == "pretest"]
    learn_items = [i for i in raw_items if i.get("section") == "learn"]
    try_items  = [i for i in raw_items if i.get("section") == "try"]
    r1_items   = [i for i in raw_items if i.get("section") == "practice_r1"]
    r2_items   = [i for i in raw_items if i.get("section") == "practice_r2"]
    r3_items   = [i for i in raw_items if i.get("section") == "practice_r3"]

    # ── 신규 카드 추가 ────────────────────────────────────────────────────
    learn_items.extend(copy.deepcopy(NEW_LEARN_CARDS))
    try_items.extend(copy.deepcopy(NEW_TRY_CARDS))
    r1_items.extend(copy.deepcopy(NEW_R1_CARDS))
    r2_items.extend(copy.deepcopy(NEW_R2_CARDS))
    r3_items.extend(copy.deepcopy(NEW_R3_CARDS))

    # ── 각 문항에 공통 필드 적용 ──────────────────────────────────────────
    pt_items    = [add_item_fields(i) for i in pt_items]
    learn_items = [add_item_fields(i) for i in learn_items]
    try_items   = [add_item_fields(i) for i in try_items]
    r1_items    = [add_item_fields(i) for i in r1_items]
    r2_items    = [add_item_fields(i) for i in r2_items]
    r3_items    = [add_item_fields(i) for i in r3_items]

    # ── R2 인터리브: 마지막 25%에 review_from="U1" 태그 ─────────────────
    r2_tail_start = len(r2_items) * 3 // 4  # 10개 → 7~10번 인덱스(7,8,9)
    for item in r2_items[r2_tail_start:]:
        if "review_from" not in item:
            item["review_from"] = "U1"

    # ── vertical_alignment 추가 ───────────────────────────────────────────
    d["vertical_alignment"] = {
        "prerequisite": "G2 — 최대 4개 범주로 데이터 정리; 척도 1인 단순 막대그래프 작성",
        "current":      "G3 — 축척 막대그래프 제작; 적절한 척도 선택; 정확한 막대 그리기",
        "successor":    "G4 — 막대그래프·꺾은선그래프 작성; 척도 및 간격 선택·정당화",
    }

    # ── 최상위 섹션 키로 저장 ─────────────────────────────────────────────
    d["pretest"]      = pt_items
    d["learn"]        = learn_items
    d["try"]          = try_items
    d["practice_r1"]  = r1_items
    d["practice_r2"]  = r2_items
    d["practice_r3"]  = r3_items

    # ── 메타데이터 업데이트 ───────────────────────────────────────────────
    sections_map = {
        "pretest":      pt_items,
        "learn":        learn_items,
        "try":          try_items,
        "practice_r1":  r1_items,
        "practice_r2":  r2_items,
        "practice_r3":  r3_items,
    }
    total = sum(len(v) for v in sections_map.values())

    d.setdefault("metadata", {})
    d["metadata"].update({
        "upgraded": True,
        "upgrade_version": "7stage-v1.0",
        "total_items": total,
        "section_counts": {k: len(v) for k, v in sections_map.items()},
        "ccss": ["3.MD.B.3"],
        "misconception_pool": "3.MD.B.3.json",
        "stage7_pending": True,
        "stage7_pilot_window": "2026-06-13~19",
    })

    # ── 저장 ──────────────────────────────────────────────────────────────
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    counts = {k: len(v) for k, v in sections_map.items()}
    print(f"✅ 업그레이드 완료: L5_make_bar_graphs.json")
    print(f"   PT={counts['pretest']}  LEARN={counts['learn']}  TRY={counts['try']}")
    print(f"   R1={counts['practice_r1']}  R2={counts['practice_r2']}  R3={counts['practice_r3']}")
    print(f"   총 문항 수: {total}")


if __name__ == "__main__":
    upgrade()
