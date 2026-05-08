"""
G3 U2 L6 — Solve Problems Using Data 7단계 업그레이드 스크립트
=============================================================
목적: L6_solve_problems_using_data.json을 7단계 검증 프로토콜에 맞게 업그레이드
- 23개 → 43개 문항 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
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
SRC  = ROOT / "backend/data/math/G3/U2_represent_interpret_data/L6_solve_problems_using_data.json"

# ── 오류 유형 맵 ───────────────────────────────────────────────────────────
ERRORS_MAP = {
    # Pretest
    "PT_01": ["3.MD.B.3.M03", "3.MD.B.3.M04"],
    "PT_02": ["3.MD.B.3.M04"],
    "PT_03": ["3.MD.B.3.M03"],
    "PT_04": ["3.MD.B.3.M04"],
    "PT_05": ["3.MD.B.3.M04", "3.MD.B.3.M05"],
    # Learn
    "LEARN_01": [],
    "LEARN_02": [],
    "LEARN_03": [],
    "LEARN_04": ["3.MD.B.3.M03"],
    "LEARN_05": ["3.MD.B.3.M05"],
    "LEARN_06": ["3.MD.B.3.M04"],
    "LEARN_07": ["3.MD.B.3.M03", "3.MD.B.3.M04"],
    "LEARN_08": [],
    # Try
    "TRY_01": ["3.MD.B.3.M05"],
    "TRY_02": ["3.MD.B.3.M03"],
    "TRY_03": ["3.MD.B.3.M05"],
    "TRY_04": ["3.MD.B.3.M04"],
    "TRY_05": ["3.MD.B.3.M05", "3.OA.D.8.M01"],
    # R1
    "R1_01": ["3.MD.B.3.M03"],
    "R1_02": ["3.MD.B.3.M04"],
    "R1_03": ["3.MD.B.3.M03"],
    "R1_04": ["3.MD.B.3.M05", "3.OA.D.8.M01"],
    "R1_05": ["3.MD.B.3.M03"],
    "R1_06": ["3.MD.B.3.M03"],
    "R1_07": ["3.MD.B.3.M04"],
    "R1_08": ["3.MD.B.3.M05", "3.OA.D.8.M01"],
    "R1_09": ["3.MD.B.3.M04", "3.OA.D.8.M07"],
    "R1_10": ["3.MD.B.3.M04"],
    # R2
    "R2_01": ["3.OA.D.8.M01", "3.OA.D.8.M04"],
    "R2_02": ["3.OA.D.8.M05"],
    "R2_03": ["3.OA.D.8.M01"],
    "R2_04": ["3.MD.B.3.M05", "3.OA.D.8.M07"],
    "R2_05": ["3.MD.B.3.M03"],
    "R2_06": ["3.MD.B.3.M05"],
    "R2_07": ["3.MD.B.3.M04", "3.OA.D.8.M07"],
    "R2_08": ["3.MD.B.3.M01"],           # U1 복습: 탤리
    "R2_09": ["3.MD.B.3.M04"],            # U1 복습: 합계
    "R2_10": ["3.MD.B.3.M03"],            # U1 복습: 비교
    # R3
    "R3_01": ["3.OA.D.8.M04", "3.OA.D.8.M07"],
    "R3_02": ["3.OA.D.8.M03"],
    "R3_03": ["3.MD.B.3.M05", "3.OA.D.8.M01"],
    "R3_04": ["3.MD.B.3.M06", "3.MD.B.3.M04"],
    "R3_05": ["3.OA.D.8.M05", "3.OA.D.8.M08"],
}

# ── 스킬 태그 맵 ───────────────────────────────────────────────────────────
SKILL_TAGS = {
    "PT_01": "compare_bars",
    "PT_02": "isolate_categories",
    "PT_03": "compare_bars",
    "PT_04": "isolate_categories",
    "PT_05": "total_bar_values",
    "LEARN_01": "compare_bars",
    "LEARN_02": "total_bar_values",
    "LEARN_03": "not_choose",
    "LEARN_04": "compare_bars",
    "LEARN_05": "not_choose",
    "LEARN_06": "isolate_categories",
    "LEARN_07": "compare_bars",
    "LEARN_08": "two_step_data",
    "TRY_01": "not_choose",
    "TRY_02": "compare_bars",
    "TRY_03": "not_choose",
    "TRY_04": "isolate_categories",
    "TRY_05": "not_choose",
    "R1_01": "compare_bars",
    "R1_02": "isolate_categories",
    "R1_03": "compare_bars",
    "R1_04": "not_choose",
    "R1_05": "compare_bars",
    "R1_06": "compare_bars",
    "R1_07": "total_bar_values",
    "R1_08": "not_choose",
    "R1_09": "two_step_data",
    "R1_10": "isolate_categories",
    "R2_01": "two_step_data",
    "R2_02": "total_bar_values",
    "R2_03": "total_bar_values",
    "R2_04": "two_step_data",
    "R2_05": "compare_bars",
    "R2_06": "not_choose",
    "R2_07": "two_step_data",
    "R2_08": "read_bar_value",          # U1 복습
    "R2_09": "total_bar_values",        # U1 복습
    "R2_10": "compare_bars",            # U1 복습
    "R3_01": "two_step_data",
    "R3_02": "total_bar_values",
    "R3_03": "two_step_data",
    "R3_04": "two_step_data",
    "R3_05": "two_step_data",
}

# ── CPA 단계 맵 ────────────────────────────────────────────────────────────
CPA_MAP = {
    "PT_01": "pictorial",
    "PT_02": "pictorial",
    "PT_03": "pictorial",
    "PT_04": "pictorial",
    "PT_05": "abstract",
    "LEARN_01": "concrete",
    "LEARN_02": "concrete",
    "LEARN_03": "pictorial",
    "LEARN_04": "pictorial",
    "LEARN_05": "pictorial",
    "LEARN_06": "abstract",
    "LEARN_07": "abstract",
    "LEARN_08": "abstract",
    "TRY_01": "pictorial",
    "TRY_02": "pictorial",
    "TRY_03": "abstract",
    "TRY_04": "abstract",
    "TRY_05": "abstract",
    "R1_01": "pictorial",
    "R1_02": "pictorial",
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
    """검증 블록 생성 — L6 Solve Problems Using Data"""
    return {
        "concept_source": "Go Math Grade 3 Ch.2 Lesson 2.6 'Solve Problems Using Data' pp.85-88",
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
        item["skill_tag"] = SKILL_TAGS.get(item_id, "two_step_data")

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
        "title": "단계별 가이드: '몇 명 더 많은가' 풀기",
        "content": (
            "데이터: 고양이 9, 강아지 15, 물고기 6. "
            "'강아지가 고양이보다 몇 명 더 많이 선택?' "
            "1단계: 두 값 찾기 — 강아지=15, 고양이=9. "
            "2단계: 큰 값 − 작은 값 = 15 − 9 = 6. "
            "답: 6명 더 많음."
        ),
        "data_table": {
            "title": "반려동물 조사",
            "type": "bar_graph",
            "categories": ["고양이", "강아지", "물고기"],
            "values": [9, 15, 6],
            "scale": 3,
            "unit": "명",
        },
        "cpa_stage": "pictorial",
        "visual_type": "comparison_bar_model",
    },
    {
        "id": "LEARN_05",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "단계별 가이드: '선택하지 않은' 인원 풀기",
        "content": (
            "데이터: 미술 8, 음악 12, 체육 10. "
            "'음악을 선택하지 않은 학생 수는?' "
            "1단계: 전체 합계 = 8+12+10 = 30. "
            "2단계: 전체 − 음악 = 30 − 12 = 18. "
            "답: 18명. "
            "실수 주의: 전체(30)를 정답으로 쓰지 말 것."
        ),
        "data_table": {
            "title": "좋아하는 과목",
            "type": "bar_graph",
            "categories": ["미술", "음악", "체육"],
            "values": [8, 12, 10],
            "scale": 2,
            "unit": "명",
        },
        "cpa_stage": "pictorial",
        "visual_type": "bar_model_two_step",
    },
    {
        "id": "LEARN_06",
        "section": "learn",
        "difficulty": 1,
        "type": "concept_card",
        "title": "특정 범주만 더하기",
        "content": (
            "데이터: 빨강 10, 파랑 8, 노랑 4, 초록 6. "
            "'빨강 또는 노랑을 선택한 학생 수?' "
            "→ 빨강(10) + 노랑(4) = 14. "
            "전체 합계(10+8+4+6=28)를 사용하지 않는다. "
            "핵심: 질문에 나온 범주만 더한다."
        ),
        "data_table": {
            "title": "좋아하는 색깔",
            "type": "bar_graph",
            "categories": ["빨강", "파랑", "노랑", "초록"],
            "values": [10, 8, 4, 6],
            "scale": 2,
            "unit": "명",
        },
        "cpa_stage": "abstract",
        "visual_type": "none",
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 1,
        "type": "explain",
        "title": "수학 토크: '몇 명 더' vs '합쳐서 몇 명'",
        "content": (
            "데이터: 축구 14, 농구 8, 테니스 6. "
            "Q1: '축구가 테니스보다 몇 명 더?' → 빼기: 14−6=8. "
            "Q2: '축구와 농구 합쳐서 몇 명?' → 더하기: 14+8=22. "
            "키워드: '더 많은/적은' → 뺄셈. '합쳐서/총' → 덧셈."
        ),
        "data_table": {
            "title": "스포츠 선호도",
            "type": "bar_graph",
            "categories": ["축구", "농구", "테니스"],
            "values": [14, 8, 6],
            "scale": 2,
            "unit": "명",
        },
        "question": "농구와 테니스를 합쳐서 몇 명인가요?",
        "choices": ["A. 8", "B. 2", "C. 14", "D. 22"],
        "answer": "C",
        "explanation": "농구(8) + 테니스(6) = 14.",
        "cpa_stage": "abstract",
        "visual_type": "none",
        "hints": [
            "'합쳐서'는 더하기입니다.",
            "8 + 6 = ?",
        ],
        "feedback_correct": "맞아요! 합쳐서 = 두 값 더하기.",
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "summary",
        "title": "L6 핵심 정리",
        "content": (
            "막대그래프 문제 풀기 4가지 전략: "
            "1. '몇 명 더 많은/적은' → 큰 값 − 작은 값 (뺄셈). "
            "2. '합쳐서/또는' → 해당 범주만 더하기. "
            "3. '전체/모두' → 모든 범주 더하기. "
            "4. '선택하지 않은' → 전체 − 해당 범주."
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
            "막대그래프: 월요일 6, 화요일 10, 수요일 4, 목요일 8. "
            "월요일과 목요일에 대출된 책은 합쳐서 몇 권인가요?"
        ),
        "data_table": {
            "title": "도서관 대출 현황",
            "type": "bar_graph",
            "categories": ["월요일", "화요일", "수요일", "목요일"],
            "values": [6, 10, 4, 8],
            "scale": 2,
            "unit": "권",
        },
        "choices": ["A. 8", "B. 14", "C. 16", "D. 28"],
        "answer": "B",
        "explanation": "월요일(6) + 목요일(8) = 14.",
        "hints": [
            "'합쳐서'는 더하기입니다.",
            "6 + 8 = ?",
        ],
        "feedback_correct": "잘했어요! 6+8=14권.",
        "solution_steps": ["월요일=6, 목요일=8", "6+8=14"],
    },
    {
        "id": "TRY_05",
        "section": "try",
        "difficulty": 2,
        "question": (
            "막대그래프: 축구 14, 농구 8, 테니스 6, 수영 12. 합계=40. "
            "테니스를 선택하지 않은 학생은 몇 명인가요?"
        ),
        "data_table": {
            "title": "스포츠 투표",
            "type": "bar_graph",
            "categories": ["축구", "농구", "테니스", "수영"],
            "values": [14, 8, 6, 12],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 6", "B. 26", "C. 34", "D. 40"],
        "answer": "C",
        "explanation": "전체 40. 테니스 미선택 = 40 − 6 = 34.",
        "hints": [
            "먼저 전체 합계를 구하세요: 14+8+6+12=?",
            "전체 − 테니스 = 선택하지 않은 수",
        ],
        "feedback_correct": "정답! 40−6=34명.",
        "solution_steps": ["전체=14+8+6+12=40", "테니스 미선택=40−6=34"],
    },
]

# ── 신규 R1 카드 (R1_06 ~ R1_10) ─────────────────────────────────────────
NEW_R1_CARDS = [
    {
        "id": "R1_06",
        "section": "practice_r1",
        "difficulty": 2,
        "question": (
            "막대그래프: 축구 14, 농구 8, 테니스 6, 수영 12. "
            "테니스가 수영보다 몇 명 더 적은가요?"
        ),
        "data_table": {
            "title": "스포츠 투표",
            "type": "bar_graph",
            "categories": ["축구", "농구", "테니스", "수영"],
            "values": [14, 8, 6, 12],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 6", "B. 8", "C. 12", "D. 18"],
        "answer": "A",
        "explanation": "12 − 6 = 6.",
        "hints": [
            "'몇 명 더 적은가' → 큰 값 − 작은 값",
            "12 − 6 = ?",
        ],
        "feedback_correct": "맞아요! 12−6=6명.",
    },
    {
        "id": "R1_07",
        "section": "practice_r1",
        "difficulty": 1,
        "question": (
            "막대그래프: 빨강 10, 파랑 8, 노랑 4, 초록 6. "
            "총 투표 수는 몇인가요?"
        ),
        "data_table": {
            "title": "좋아하는 색깔",
            "type": "bar_graph",
            "categories": ["빨강", "파랑", "노랑", "초록"],
            "values": [10, 8, 4, 6],
            "scale": 2,
            "unit": "표",
        },
        "choices": ["A. 14", "B. 18", "C. 24", "D. 28"],
        "answer": "D",
        "explanation": "10+8+4+6 = 28.",
        "hints": [
            "'총'은 모든 값을 더합니다.",
            "10+8=18, 18+4=22, 22+6=?",
        ],
        "feedback_correct": "잘했어요! 10+8+4+6=28.",
    },
    {
        "id": "R1_08",
        "section": "practice_r1",
        "difficulty": 2,
        "question": (
            "막대그래프: 벤치수리 4, 식품나눔 14, 책축제 10, 놀이터 6. 합계=34. "
            "책축제를 선택하지 않은 학생은 몇 명인가요?"
        ),
        "data_table": {
            "title": "학교 프로젝트 투표",
            "type": "bar_graph",
            "categories": ["벤치수리", "식품나눔", "책축제", "놀이터"],
            "values": [4, 14, 10, 6],
            "scale": 2,
            "unit": "표",
        },
        "choices": ["A. 10", "B. 20", "C. 24", "D. 34"],
        "answer": "C",
        "explanation": "전체 34. 책축제 미선택 = 34 − 10 = 24.",
        "hints": [
            "먼저 전체 합계를 확인하세요.",
            "전체 − 책축제 = ?",
        ],
        "feedback_correct": "정답! 34−10=24.",
    },
    {
        "id": "R1_09",
        "section": "practice_r1",
        "difficulty": 3,
        "question": (
            "막대그래프: 빨강 10, 파랑 8, 노랑 4, 초록 6. "
            "파랑과 초록 합계가 노랑보다 몇 명 더 많은가요?"
        ),
        "data_table": {
            "title": "좋아하는 색깔",
            "type": "bar_graph",
            "categories": ["빨강", "파랑", "노랑", "초록"],
            "values": [10, 8, 4, 6],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 4", "B. 6", "C. 10", "D. 14"],
        "answer": "C",
        "explanation": "파랑+초록=8+6=14. 14−4=10.",
        "hints": [
            "1단계: 파랑과 초록을 더하세요 (8+6).",
            "2단계: 그 합계에서 노랑을 빼세요.",
        ],
        "feedback_correct": "훌륭해요! 8+6=14, 14−4=10.",
    },
    {
        "id": "R1_10",
        "section": "practice_r1",
        "difficulty": 2,
        "question": (
            "막대그래프: 고양이 9, 강아지 15, 물고기 6. "
            "고양이 또는 물고기를 선택한 학생은 몇 명인가요?"
        ),
        "data_table": {
            "title": "반려동물 조사",
            "type": "bar_graph",
            "categories": ["고양이", "강아지", "물고기"],
            "values": [9, 15, 6],
            "scale": 3,
            "unit": "명",
        },
        "choices": ["A. 6", "B. 9", "C. 15", "D. 30"],
        "answer": "C",
        "explanation": "고양이(9) + 물고기(6) = 15.",
        "hints": [
            "'또는'은 두 범주를 더합니다.",
            "9 + 6 = ?",
        ],
        "feedback_correct": "맞아요! 9+6=15.",
    },
]

# ── 신규 R2 카드 (R2_05 ~ R2_10) ─────────────────────────────────────────
NEW_R2_CARDS = [
    {
        "id": "R2_05",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "막대그래프: 피자 11, 치킨 4, 핫도그 7, 치즈샌드위치 2. "
            "피자가 치즈샌드위치보다 몇 명 더 많이 선택됐나요?"
        ),
        "data_table": {
            "title": "좋아하는 점심",
            "type": "bar_graph",
            "categories": ["피자", "치킨", "핫도그", "치즈샌드위치"],
            "values": [11, 4, 7, 2],
            "scale": 1,
            "unit": "명",
        },
        "choices": ["A. 2", "B. 9", "C. 11", "D. 13"],
        "answer": "B",
        "explanation": "11 − 2 = 9.",
        "hints": [
            "'몇 명 더 많은가' → 뺄셈",
            "11 − 2 = ?",
        ],
        "feedback_correct": "잘했어요! 11−2=9.",
    },
    {
        "id": "R2_06",
        "section": "practice_r2",
        "difficulty": 2,
        "question": (
            "막대그래프: 미술 8, 음악 12, 체육 10. 합계=30. "
            "미술을 선택하지 않은 학생은 몇 명인가요?"
        ),
        "data_table": {
            "title": "좋아하는 과목",
            "type": "bar_graph",
            "categories": ["미술", "음악", "체육"],
            "values": [8, 12, 10],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 8", "B. 12", "C. 22", "D. 30"],
        "answer": "C",
        "explanation": "전체 30. 미술 미선택 = 30 − 8 = 22.",
        "hints": [
            "전체를 먼저 구한 다음 미술을 빼세요.",
            "30 − 8 = ?",
        ],
        "feedback_correct": "정답! 30−8=22.",
    },
    {
        "id": "R2_07",
        "section": "practice_r2",
        "difficulty": 3,
        "question": (
            "막대그래프: 걷기 10, 버스 12, 자동차 6, 자전거 4. "
            "버스와 걷기 합계가 자동차와 자전거 합계보다 몇 명 더 많나요?"
        ),
        "data_table": {
            "title": "등교 방법",
            "type": "bar_graph",
            "categories": ["걷기", "버스", "자동차", "자전거"],
            "values": [10, 12, 6, 4],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 4", "B. 6", "C. 12", "D. 22"],
        "answer": "C",
        "explanation": "버스+걷기=12+10=22. 자동차+자전거=6+4=10. 22−10=12.",
        "hints": [
            "1단계: 버스+걷기=?",
            "2단계: 자동차+자전거=?",
            "3단계: 두 합계의 차이=?",
        ],
        "feedback_correct": "훌륭해요! 22−10=12명.",
    },
    {
        "id": "R2_08",
        "section": "practice_r2",
        "review_from": "U1",
        "difficulty": 2,
        "question": (
            "탤리 차트: 독서 𝍸𝍸𝍸𝍸 (탤리 4묶음). 독서를 선택한 학생은 몇 명인가요?"
        ),
        "choices": ["A. 4", "B. 20", "C. 25", "D. 16"],
        "answer": "B",
        "explanation": "𝍸 1묶음 = 5. 4묶음 = 5×4 = 20.",
        "hints": [
            "탤리 한 묶음(𝍸)은 5를 나타냅니다.",
            "4묶음 × 5 = ?",
        ],
        "feedback_correct": "맞아요! 탤리 4묶음 = 20.",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "review_from": "U1",
        "difficulty": 2,
        "question": (
            "막대그래프: 고양이 9, 강아지 15, 물고기 6. "
            "전체 설문에 참여한 학생은 몇 명인가요?"
        ),
        "data_table": {
            "title": "반려동물 조사",
            "type": "bar_graph",
            "categories": ["고양이", "강아지", "물고기"],
            "values": [9, 15, 6],
            "scale": 3,
            "unit": "명",
        },
        "choices": ["A. 9", "B. 21", "C. 30", "D. 15"],
        "answer": "C",
        "explanation": "9 + 15 + 6 = 30.",
        "hints": [
            "전체 = 모든 범주 더하기",
            "9 + 15 = 24, 24 + 6 = ?",
        ],
        "feedback_correct": "정답! 9+15+6=30.",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "review_from": "U1",
        "difficulty": 2,
        "question": (
            "막대그래프: 빨강 10, 파랑 8, 노랑 4, 초록 6. "
            "빨강이 노랑보다 몇 명 더 많이 선택했나요?"
        ),
        "data_table": {
            "title": "좋아하는 색깔",
            "type": "bar_graph",
            "categories": ["빨강", "파랑", "노랑", "초록"],
            "values": [10, 8, 4, 6],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 4", "B. 6", "C. 10", "D. 14"],
        "answer": "B",
        "explanation": "10 − 4 = 6.",
        "hints": [
            "'몇 명 더 많은가' → 큰 값 − 작은 값",
            "10 − 4 = ?",
        ],
        "feedback_correct": "맞아요! 10−4=6.",
    },
]

# ── 신규 R3 카드 (R3_04 ~ R3_05) ─────────────────────────────────────────
NEW_R3_CARDS = [
    {
        "id": "R3_04",
        "section": "practice_r3",
        "difficulty": 3,
        "question": (
            "막대그래프: 축구 14, 농구 8, 테니스 6, 수영 12. "
            "코치가 가장 적게 선택된 두 종목을 합쳐 팀을 만들려 한다. "
            "그 팀엔 몇 명이 있나요?"
        ),
        "data_table": {
            "title": "스포츠 투표",
            "type": "bar_graph",
            "categories": ["축구", "농구", "테니스", "수영"],
            "values": [14, 8, 6, 12],
            "scale": 2,
            "unit": "명",
        },
        "choices": ["A. 6", "B. 8", "C. 14", "D. 22"],
        "answer": "C",
        "explanation": "가장 적게 선택: 테니스(6)와 농구(8). 6+8=14.",
        "hints": [
            "먼저 가장 작은 두 값을 찾으세요.",
            "테니스=6, 농구=8. 6+8=?",
        ],
        "feedback_correct": "훌륭해요! 테니스(6)+농구(8)=14.",
    },
    {
        "id": "R3_05",
        "section": "practice_r3",
        "difficulty": 3,
        "question": (
            "막대그래프: A반 18, B반 24, C반 12. "
            "각 반이 25권에 도달하려면 더 읽어야 하는 책이 있다. "
            "세 반이 추가로 읽어야 할 책은 총 몇 권인가요?"
        ),
        "data_table": {
            "title": "독서 마라톤",
            "type": "bar_graph",
            "categories": ["A반", "B반", "C반"],
            "values": [18, 24, 12],
            "scale": 2,
            "unit": "권",
        },
        "choices": ["A. 7", "B. 13", "C. 21", "D. 54"],
        "answer": "C",
        "explanation": "A반: 25−18=7. B반: 25−24=1. C반: 25−12=13. 합계: 7+1+13=21.",
        "hints": [
            "각 반이 25권에서 부족한 양을 구하세요.",
            "A반=7, B반=1, C반=13. 모두 더하면?",
        ],
        "feedback_correct": "완벽해요! 7+1+13=21권.",
    },
]


def upgrade():
    """L6_solve_problems_using_data.json 업그레이드 실행"""
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)

    # ── 이미 업그레이드된 파일이면 건너뜀 ────────────────────────────────
    if "pretest" in d:
        print("⚠️  이미 업그레이드된 파일입니다. 건너뜁니다.")
        return

    raw_items = d.pop("items", [])

    # ── LN_ → LEARN_ 정규화 ──────────────────────────────────────────────
    for item in raw_items:
        if item["id"].startswith("LN_"):
            item["id"] = f"LEARN_{item['id'][3:]}"

    # ── 섹션별 분류 ───────────────────────────────────────────────────────
    pt_items    = [i for i in raw_items if i.get("section") == "pretest"]
    learn_items = [i for i in raw_items if i.get("section") == "learn"]
    try_items   = [i for i in raw_items if i.get("section") == "try"]
    r1_items    = [i for i in raw_items if i.get("section") == "practice_r1"]
    r2_items    = [i for i in raw_items if i.get("section") == "practice_r2"]
    r3_items    = [i for i in raw_items if i.get("section") == "practice_r3"]

    # ── 신규 카드 추가 ────────────────────────────────────────────────────
    learn_items.extend(copy.deepcopy(NEW_LEARN_CARDS))
    try_items.extend(copy.deepcopy(NEW_TRY_CARDS))
    r1_items.extend(copy.deepcopy(NEW_R1_CARDS))
    r2_items.extend(copy.deepcopy(NEW_R2_CARDS))
    r3_items.extend(copy.deepcopy(NEW_R3_CARDS))

    # ── 공통 필드 적용 ────────────────────────────────────────────────────
    pt_items    = [add_item_fields(i) for i in pt_items]
    learn_items = [add_item_fields(i) for i in learn_items]
    try_items   = [add_item_fields(i) for i in try_items]
    r1_items    = [add_item_fields(i) for i in r1_items]
    r2_items    = [add_item_fields(i) for i in r2_items]
    r3_items    = [add_item_fields(i) for i in r3_items]

    # ── R2 인터리브: 마지막 25%에 review_from="U1" ───────────────────────
    r2_tail_start = len(r2_items) * 3 // 4  # 10개 → 인덱스 7~9
    for item in r2_items[r2_tail_start:]:
        if "review_from" not in item:
            item["review_from"] = "U1"

    # ── vertical_alignment ───────────────────────────────────────────────
    d["vertical_alignment"] = {
        "prerequisite": "G2 — 막대그래프·그림그래프에서 데이터 읽기; 단순 비교",
        "current":      "G3 — 축척 막대그래프에서 '몇 명 더/적은', '합쳐서', '선택 안 함' 문제 풀기",
        "successor":    "G4 — 다양한 표현(막대·꺾은선·표)에서 다단계 문제 풀기",
    }

    # ── 최상위 섹션 키로 저장 ─────────────────────────────────────────────
    d["pretest"]     = pt_items
    d["learn"]       = learn_items
    d["try"]         = try_items
    d["practice_r1"] = r1_items
    d["practice_r2"] = r2_items
    d["practice_r3"] = r3_items

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
    print(f"✅ 업그레이드 완료: L6_solve_problems_using_data.json")
    print(f"   PT={counts['pretest']}  LEARN={counts['learn']}  TRY={counts['try']}")
    print(f"   R1={counts['practice_r1']}  R2={counts['practice_r2']}  R3={counts['practice_r3']}")
    print(f"   총 문항 수: {total}")


if __name__ == "__main__":
    upgrade()
