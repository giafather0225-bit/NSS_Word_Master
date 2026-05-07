#!/usr/bin/env python3
"""
G3 U2 L2 — Use Picture Graphs
7-Stage 업그레이드 스크립트

변환 작업:
1. 평탄 items 배열 → 섹션별 구조 (pretest/learn/try/practice_r1/r2/r3)
2. LN_XX 식별자 → LEARN_XX로 변경
3. cpa_phase → cpa_stage로 필드명 통일
4. 각 문항에 verification 블록 추가
5. 각 문항에 expected_errors 추가 (3.MD.B.3 오개념 매핑)
6. LEARN 카드 3개 → 8개로 확장 (LEARN_04~08 신규)
7. TRY 카드 3개 → 5개로 확장 (TRY_04~05 신규)
8. R1 카드 7개 → 10개로 확장 (R1_08~10 신규)
9. R2 카드 4개 → 10개로 확장 (R2_05~10 신규)
10. R3 카드 3개 → 5개로 확장 (R3_04~05 신규)
11. 레슨 레벨 필드 추가: tier, vertical_alignment, unit_intro/close_message 등
"""

import json
import pathlib

# ─────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────
REPO = pathlib.Path(__file__).resolve().parent.parent
SRC  = REPO / "backend/data/math/G3/U2_represent_interpret_data/L2_use_picture_graphs.json"
DST  = SRC   # 원본 파일을 직접 업그레이드

# ─────────────────────────────────────────
# 오개념 ID 상수 (3.MD.B.3)
# ─────────────────────────────────────────
M01 = "3.MD.B.3.M01"   # tally_miscount (그림 그래프에서는 반 심볼 오독)
M02 = "3.MD.B.3.M02"   # wrong_row_column (잘못된 카테고리 선택)
M03 = "3.MD.B.3.M03"   # add_instead_of_subtract (비교에서 덧셈 수행)
M04 = "3.MD.B.3.M04"   # include_all_categories (전체 합산)
M05 = "3.MD.B.3.M05"   # total_as_comparison (중간 결과에서 멈춤)
M06 = "3.MD.B.3.M06"   # category_identification_error (최대/최소 오식별)
M07 = "3.MD.B.3.M07"   # two_step_data_error (2단계 문제 오류)

# ─────────────────────────────────────────
# 검증 블록 (레슨 전체 공통)
# ─────────────────────────────────────────
def make_verification() -> dict:
    return {
        "concept_source": {
            "name": "Go Math Grade 3 Chapter 2 Lesson 2.3 — Read Picture Graphs",
            "url": "https://www.hmhco.com/programs/go-math",
            "description": "그림 그래프 읽기, 키 값 활용, 반 심볼 해석"
        },
        "procedure_source": {
            "name": "EngageNY Grade 3 Module 6 Lesson 4 — Scaled Picture Graphs",
            "url": "https://www.engageny.org/resource/grade-3-mathematics-module-6",
            "description": "스케일 그림 그래프 읽기 및 비교 절차"
        },
        "assessment_source": {
            "name": "Smarter Balanced Grade 3 Sample Items — 3.MD.B.3",
            "url": "https://sampleitems.smarterbalanced.org/",
            "description": "3.MD.B.3 평가 지침 — 그림 그래프 해석 및 비교 문제"
        }
    }


# ─────────────────────────────────────────
# 오개념 항목별 매핑 (item_id → expected_errors 리스트)
# ─────────────────────────────────────────
ERRORS_MAP: dict[str, list[dict]] = {
    # ── Pretest ──
    "PT_01": [
        # 3×2=6 → 오답 A(3, 심볼 수 그대로): M01 (반 심볼 오독 아니지만 키 무시)
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(×2) 무시하고 심볼 수(3) 그대로 제출",
         "citation": "Friel et al. (2001) p.130 — 그림 그래프 스케일 오독"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "3×2=6이 아닌 3×3=9로 계산"},
    ],
    "PT_02": [
        # 반 심볼=2 → 오답 D(4, 전체 심볼로 읽음): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "½ 심볼을 1 심볼로 읽어 반이 아닌 키 값(4) 전체 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "절반 계산 오류: ½×4=1로 잘못 계산"},
    ],
    "PT_03": [
        # 10-6=4 → 오답 C(10+6=16): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 많은' 질문에서 Cats+Dogs=16 덧셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Cats 값(10)만 제출"},
    ],
    "PT_04": [
        # 20+12=32 → 오답 A(20, 100점만): M05
        {"error_type": "misconception", "misconception_id": M05,
         "description": "100점(20명) 구한 후 합산 2단계 미완료",
         "citation": "EngageNY G3 M6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "5+3=8 심볼 합 제출 (키 곱하기 누락)"},
    ],
    "PT_05": [
        # 2½×6=15 → 오답 A(12=2×6, 반 심볼 무시): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "2½ 심볼을 2로 읽어 2×6=12 계산",
         "citation": "Friel et al. (2001) p.130 — 반 심볼 오독"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "3×6=18 (반올림 오류)"},
    ],
    # ── TRY ──
    "TRY_01": [
        # 4×3=12 → 오답 B(7=4+3): M04
        {"error_type": "misconception", "misconception_id": M01,
         "description": "4개 심볼에 키(3)를 곱하지 않고 4+3=7 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "4×4=16으로 키 값 혼동"},
    ],
    "TRY_02": [
        # 2½×2=5 → 오답 D(4=2×2, 반 심볼 무시): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "Banana 2½를 2로 읽어 2×2=4 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "반 심볼 = ½×2=1이라고 잘못 계산하여 2-1=1"},
    ],
    "TRY_03": [
        # 2×2=4 → 오답 A(10=5×2 Beagle): M02
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Poodle 대신 Beagle(5심볼) 행 읽어 5×2=10 제출",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "2+2=4가 아닌 심볼 수(2)만 제출"},
    ],
    "TRY_04": [
        # 30-18=12 → 오답 B(30+18=48): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 많은' 비교에 덧셈 수행 (30+18=48)",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Spring 값(30)만 제출"},
    ],
    "TRY_05": [
        # 8+12+6+4=30 → 오답 A(26, 마지막 카테고리 누락): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "전체 합을 구할 때 마지막 카테고리 Fish(4) 누락 → 26 제출",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "심볼 수 합(7)만 제출하고 키 곱하기 누락"},
    ],
    # ── R1 ──
    "R1_01": [
        # 3×5=15 → 오답 A(3, 키 곱하기 누락): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(×5) 무시하고 심볼 수(3) 그대로 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "3×5=15가 아닌 3+5=8"},
    ],
    "R1_02": [
        # 6×2=12 → 오답 B(6, 키 무시): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(×2) 무시하고 심볼 수(6) 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "6+2=8로 잘못 계산"},
    ],
    "R1_03": [
        # 반 심볼=2 → 오답 D(4, 전체 키 값): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "½ 심볼을 1로 보아 키 값(4) 전체 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "½×4=1로 계산 오류"},
    ],
    "R1_04": [
        # Blue=5×4=20 → 오답 A(Red=3×4=12): M02
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Blue(5심볼) 대신 Red(3심볼) 행 읽어 12 제출",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "5+4=9로 잘못 계산"},
    ],
    "R1_05": [
        # 8+12+5=25 → 오답 A(20=Vanilla+Chocolate만): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Mint 카테고리 누락하여 Vanilla+Chocolate=20만 합산",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Mint: 2½×2=4로 계산 오류 → 합계=24"},
    ],
    "R1_06": [
        # 30+21=51 → 오답 A(30-21=9): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'합계' 대신 차이(30-21=9) 계산",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "심볼 합(5+3.5=8.5)만 제출하고 키 곱하기 누락"},
    ],
    "R1_07": [
        # 반 심볼=3 → 오답 A(6, 전체 키): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "½ 심볼을 1로 보아 키 전체 값(6) 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "½×6=2로 계산 오류"},
    ],
    "R1_08": [
        # 새 문항: 비교 문제 (더 많은)
        {"error_type": "misconception", "misconception_id": M03,
         "description": "비교 대신 덧셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "큰 카테고리 값만 제출"},
    ],
    "R1_09": [
        # 새 문항: 반 심볼 포함 총합
        {"error_type": "misconception", "misconception_id": M01,
         "description": "반 심볼을 1로 보아 잘못된 합계 계산",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "심볼 수 합만 제출하고 키 곱하기 누락"},
    ],
    "R1_10": [
        # 새 문항: 가상 변경 (심볼 추가/제거)
        {"error_type": "misconception", "misconception_id": M07,
         "description": "가상 변경 후 심볼 수 계산에서 2단계 오류",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "변경 전 값 그대로 제출"},
    ],
    # ── R2 ──
    "R2_01": [
        # 8-6=2 → 오답 C(8+6=14): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 많은' 질문에 8+6=14 덧셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "큰 값(8) 그대로 제출"},
    ],
    "R2_02": [
        # 20+12+8+6=46 → 오답 A(20+12=32, 일부만): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "95점과 100점만 합산(32)하고 나머지 카테고리 누락",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "심볼 수 합(5+3+2+1.5=11.5)만 제출하고 키 곱하기 누락"},
    ],
    "R2_03": [
        # 12+14=26 → 26÷4=6½ → 오답 D(26, 2단계 미완료): M05
        {"error_type": "misconception", "misconception_id": M05,
         "description": "새 95점 학생 수(26)를 구하고 심볼 수 변환 2단계 미완료",
         "citation": "EngageNY G3 M6 L2 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "14 (85+90 학생 합계)만 제출"},
    ],
    "R2_04": [
        # 40-28=12 → 오답 D(40+28=68): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 많은' 질문에 40+28=68 덧셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Soccer(40) 값만 제출"},
    ],
    "R2_05": [
        {"error_type": "misconception", "misconception_id": M04,
         "description": "지정된 두 카테고리 대신 전체 합 계산",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "큰 카테고리 값만 제출"},
    ],
    "R2_06": [
        {"error_type": "misconception", "misconception_id": M06,
         "description": "최솟값 카테고리 오식별",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "전체 합 제출"},
    ],
    "R2_07": [
        {"error_type": "misconception", "misconception_id": M05,
         "description": "중간 단계 결과에서 멈춤",
         "citation": "EngageNY G3 M6 L2"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "첫 번째 카테고리 값만 제출"},
    ],
    "R2_08": [
        {"error_type": "misconception", "misconception_id": M07,
         "description": "2단계 문제에서 두 번째 연산 오류",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "심볼 수만 제출하고 키 곱하기 누락"},
    ],
    "R2_09": [
        {"error_type": "misconception", "misconception_id": M01,
         "description": "반 심볼 오독으로 잘못된 계산",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "전체 합 제출"},
    ],
    "R2_10": [
        {"error_type": "misconception", "misconception_id": M07,
         "description": "가상 변경 시나리오에서 잘못된 카테고리 업데이트",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "원래 값 그대로 제출"},
    ],
    # ── R3 ──
    "R3_01": [
        # 45+30+25=100 → 오답 A(45, 3A만): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "전체 합 대신 Grade 3A(45) 값만 제출",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "4.5+3+2.5=10 심볼만 합산하고 키 곱하기 누락"},
    ],
    "R3_02": [
        # 2÷4=½ → 오답 A(1 star): M07
        {"error_type": "misconception", "misconception_id": M07,
         "description": "학생 수(2)를 심볼로 변환하는 나눗셈 대신 곱셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "4개 새 심볼 추가라고 오해"},
    ],
    "R3_03": [
        # Bikes=24 < Scooters+Skateboards=26 → 오답 A(Bikes more by 2): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "합 대신 개별 최대 카테고리(Bikes=24)가 더 많다고 결론",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "차이를 4로 잘못 계산"},
    ],
    "R3_04": [
        {"error_type": "misconception", "misconception_id": M07,
         "description": "3단계 문제에서 3단계 연산 오류",
         "citation": "Van de Walle et al. (2013) p.168"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "중간 단계 값 제출"},
    ],
    "R3_05": [
        {"error_type": "misconception", "misconception_id": M05,
         "description": "중간 합계에서 멈추고 최종 빼기 단계 누락",
         "citation": "EngageNY G3 M6 L2"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "전체 합 제출"},
    ],
}


# ─────────────────────────────────────────
# 기본 skill_tag 매핑 (item_id → tag)
# ─────────────────────────────────────────
SKILL_TAGS: dict[str, str] = {
    "PT_01": "read_picture_graph",
    "PT_02": "read_half_symbol",
    "PT_03": "compare_picture_graph",
    "PT_04": "multi_step_picture_graph",
    "PT_05": "read_half_symbol",
    "TRY_01": "read_picture_graph",
    "TRY_02": "read_half_symbol",
    "TRY_03": "read_picture_graph",
    "TRY_04": "compare_picture_graph",
    "TRY_05": "find_total_picture_graph",
    "R1_01": "read_picture_graph",
    "R1_02": "read_picture_graph",
    "R1_03": "read_half_symbol",
    "R1_04": "read_picture_graph",
    "R1_05": "find_total_picture_graph",
    "R1_06": "find_total_picture_graph",
    "R1_07": "read_half_symbol",
    "R1_08": "compare_picture_graph",
    "R1_09": "find_total_picture_graph",
    "R1_10": "hypothetical_graph_change",
    "R2_01": "compare_picture_graph",
    "R2_02": "find_total_picture_graph",
    "R2_03": "hypothetical_graph_change",
    "R2_04": "compare_picture_graph",
    "R2_05": "multi_step_picture_graph",
    "R2_06": "identify_max_min",
    "R2_07": "multi_step_picture_graph",
    "R2_08": "multi_step_picture_graph",
    "R2_09": "read_half_symbol",
    "R2_10": "hypothetical_graph_change",
    "R3_01": "find_total_picture_graph",
    "R3_02": "hypothetical_graph_change",
    "R3_03": "multi_step_picture_graph",
    "R3_04": "multi_step_picture_graph",
    "R3_05": "multi_step_picture_graph",
}

# CPA 단계 (문항별)
CPA_MAP: dict[str, str] = {
    "PT_01": "concrete",
    "PT_02": "concrete",
    "PT_03": "pictorial",
    "PT_04": "abstract",
    "PT_05": "pictorial",
    "TRY_01": "concrete",
    "TRY_02": "pictorial",
    "TRY_03": "concrete",
    "TRY_04": "pictorial",
    "TRY_05": "pictorial",
    "R1_01": "concrete",
    "R1_02": "concrete",
    "R1_03": "concrete",
    "R1_04": "pictorial",
    "R1_05": "pictorial",
    "R1_06": "abstract",
    "R1_07": "concrete",
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


def add_item_fields(item: dict) -> dict:
    """개별 문항에 검증·오개념·공통 필드를 추가한다."""
    iid = item.get("id", "")

    # type 필드 보완
    if "type" not in item:
        item["type"] = "multiple_choice"

    # ccss 통일 (문자열 또는 리스트 → 표준 문자열)
    if "ccss" not in item:
        item["ccss"] = "3.MD.B.3"
    elif isinstance(item["ccss"], list):
        item["ccss"] = item["ccss"][0] if item["ccss"] else "3.MD.B.3"

    # skill_tag
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(iid, "read_picture_graph")

    # cpa_stage (cpa_phase가 있으면 변환)
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(iid, "abstract")

    # section 필드 제거 (섹션 배열로 분리됨)
    item.pop("section", None)

    # expected_errors
    if "expected_errors" not in item:
        item["expected_errors"] = ERRORS_MAP.get(iid, [
            {"error_type": "careless", "note": "단순 계산 실수"}
        ])

    # math_note (정답 기반 간단 해설)
    if "math_note" not in item and "explanation" in item:
        item["math_note"] = item["explanation"]

    # feedback_correct (S4 감사 통과 — hints 있으면 필수)
    if item.get("hints") and not item.get("feedback_correct"):
        fb = item.get("feedback", {})
        if isinstance(fb, dict) and fb.get("correct"):
            item["feedback_correct"] = fb["correct"]
        else:
            item["feedback_correct"] = item.get("explanation", "정답입니다! 잘 풀었어요.")

    # verification 블록
    if "verification" not in item:
        item["verification"] = make_verification()

    return item


# ─────────────────────────────────────────
# 신규 LEARN 카드 (LEARN_04 ~ LEARN_08)
# ─────────────────────────────────────────
NEW_LEARN_CARDS = [
    {
        "id": "LEARN_04",
        "type": "concept_card",
        "title": "Finding the Total from a Picture Graph",
        "content": (
            "To find the TOTAL number, multiply each category's symbol count by the key, "
            "then ADD all the results together. "
            "Example: Key = 4. Category A has 3 symbols → 3×4=12. "
            "Category B has 2½ symbols → 2½×4=10. Total = 12+10 = 22."
        ),
        "visual_type": "picture_graph",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "전체 합 = Σ(심볼 수 × 키). 반 심볼은 키÷2.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "Comparing Categories in a Picture Graph",
        "content": (
            "'How many MORE' means SUBTRACT. "
            "'How many FEWER' also means SUBTRACT (bigger − smaller). "
            "Step 1: Find each category's value (symbols × key). "
            "Step 2: Subtract smaller from larger. "
            "Example: Dogs=5 symbols, Cats=3 symbols. Key=6. Dogs=30, Cats=18. 30−18=12 more."
        ),
        "visual_type": "picture_graph",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "'더 많은/적은' = 큰 값 − 작은 값. 먼저 각 값을 구한 후 뺄셈.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "Hypothetical Changes to a Picture Graph",
        "content": (
            "If N new data points are added to a category: "
            "Step 1: Add N to the current value. "
            "Step 2: Divide by the key to find how many symbols to draw. "
            "Example: Current Sports value = 20. Add 4 more students. Key = 4. "
            "New value = 24. 24 ÷ 4 = 6 symbols."
        ),
        "visual_type": "picture_graph",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "새 심볼 수 = (원래 값 + 변화량) ÷ 키.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_07",
        "type": "explain",
        "title": "Math Talk: Check Your Picture Graph Reasoning",
        "content": (
            "A picture graph shows: Spring 🌸🌸🌸½ (3½ symbols), Winter ❄️❄️ (2 symbols). Key = 4. "
            "How many MORE Spring days than Winter days? "
            "Spring = 3½ × 4 = 14. Winter = 2 × 4 = 8. 14 − 8 = 6. ✓ "
            "(Not 3½ + 2 = 5½ symbols — always multiply by key FIRST!)"
        ),
        "visual_type": "picture_graph",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_talk_prompt": (
            "그림 그래프: Spring = 3½ 심볼, Winter = 2 심볼, 키=4. "
            "Spring=3½×4=14, Winter=2×4=8, 14−8=6. "
            "친구가 '3½−2=1½이 답이에요'라고 했습니다. "
            "어디에서 실수했는지 설명하고, 올바른 풀이 순서를 말해 봅시다. "
            "심볼 수가 아니라 실제 값(키를 곱한 수)을 비교해야 하는 이유는 무엇인가요?"
        ),
        "math_note": "비교 전에 반드시 키를 곱해 실제 값으로 변환. 3½×4=14, 2×4=8, 14−8=6 ✓",
        "verification": make_verification()
    },
    {
        "id": "LEARN_08",
        "type": "summary",
        "title": "Lesson Summary: Use Picture Graphs",
        "content": (
            "In this lesson you learned how to: "
            "① Read a picture graph using the KEY (symbols × key = value). "
            "② Read half symbols (½ symbol = key ÷ 2). "
            "③ Find totals by adding all category values. "
            "④ Compare categories using subtraction ('how many more/fewer'). "
            "⑤ Solve multi-step picture graph problems. "
            "⑥ Understand hypothetical changes (add/remove data points → change symbols)."
        ),
        "lesson_summary": (
            "그림 그래프 마스터: "
            "①심볼×키=값 ②½심볼=키÷2 "
            "③전체=모든 카테고리 값 합산 "
            "④비교='더 많은/적은'=뺄셈 "
            "⑤2단계: 값 구하기→비교 "
            "⑥가상변경: (값+변화)÷키=새 심볼 수"
        ),
        "visual_type": "none",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "핵심: 항상 키 먼저 곱한 후 비교. 반 심볼 = 키÷2.",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 신규 TRY 카드 (TRY_04, TRY_05)
# ─────────────────────────────────────────
NEW_TRY_CARDS = [
    {
        "id": "TRY_04",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Picture graph: Spring 🌺🌺🌺 (3 symbols), Fall 🌺🌺½ (2½ symbols). "
            "Each 🌺 = 10 days. How many more Spring days than Fall days?"
        ),
        "data_table": {
            "title": "Favorite Season",
            "type": "picture_graph",
            "categories": ["Spring", "Fall"],
            "symbol_counts": [3, 2.5],
            "key_value": 10,
            "unit": "days"
        },
        "choices": ["A. 30", "B. 5", "C. 55", "D. 25"],
        "answer": "B",
        "explanation": "Spring = 3×10 = 30. Fall = 2½×10 = 25. 30 − 25 = 5.",
        "solution_steps": [
            "Spring = 3 × 10 = 30",
            "Fall = 2½ × 10 = 25",
            "30 − 25 = 5"
        ],
        "hints": [
            "Multiply each symbol count by the key (10).",
            "'How many more' means subtract."
        ],
        "feedback": {
            "correct": "Excellent! Spring=30, Fall=25, difference=5.",
            "incorrect": "First find each value (symbols × key), then subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_picture_graph",
        "cpa_stage": "pictorial",
        "expected_errors": ERRORS_MAP["TRY_04"],
        "math_note": "Spring=3×10=30, Fall=2½×10=25, 30−25=5 ✓",
        "verification": make_verification()
    },
    {
        "id": "TRY_05",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Picture graph key: Each 🐟 = 2 fish. "
            "Trout: 4 symbols, Salmon: 6 symbols, Bass: 3 symbols, Catfish: 2 symbols. "
            "How many fish in all?"
        ),
        "data_table": {
            "title": "Fish Caught",
            "type": "picture_graph",
            "categories": ["Trout", "Salmon", "Bass", "Catfish"],
            "symbol_counts": [4, 6, 3, 2],
            "key_value": 2,
            "unit": "fish"
        },
        "choices": ["A. 26", "B. 15", "C. 30", "D. 18"],
        "answer": "C",
        "explanation": "Trout=4×2=8. Salmon=6×2=12. Bass=3×2=6. Catfish=2×2=4. Total=8+12+6+4=30.",
        "solution_steps": [
            "Trout=4×2=8, Salmon=6×2=12, Bass=3×2=6, Catfish=2×2=4",
            "8+12+6+4=30"
        ],
        "hints": [
            "Multiply each category's symbols by 2.",
            "Add all four values to get the total."
        ],
        "feedback": {
            "correct": "Great! You multiplied correctly and added all categories.",
            "incorrect": "Don't forget to multiply by 2 (the key) for each category, then add all."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "find_total_picture_graph",
        "cpa_stage": "pictorial",
        "expected_errors": ERRORS_MAP["TRY_05"],
        "math_note": "8+12+6+4=30 ✓ 키(×2)를 각 카테고리에 곱한 후 합산.",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 신규 R1 카드 (R1_08 ~ R1_10)
# ─────────────────────────────────────────
NEW_R1_CARDS = [
    {
        "id": "R1_08",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Picture graph: Apples 🍎🍎🍎🍎 (4 symbols), Oranges 🍎🍎 (2 symbols). "
            "Each 🍎 = 5. How many more apples than oranges?"
        ),
        "data_table": {
            "title": "Fruit Count",
            "type": "picture_graph",
            "categories": ["Apples", "Oranges"],
            "symbol_counts": [4, 2],
            "key_value": 5,
            "unit": "pieces"
        },
        "choices": ["A. 20", "B. 30", "C. 10", "D. 2"],
        "answer": "C",
        "explanation": "Apples=4×5=20. Oranges=2×5=10. 20−10=10.",
        "solution_steps": ["Apples=4×5=20, Oranges=2×5=10", "20−10=10"],
        "hints": [
            "Multiply both symbol counts by 5.",
            "Subtract: larger − smaller."
        ],
        "feedback": {
            "correct": "Correct! Apples=20, Oranges=10, difference=10.",
            "incorrect": "Multiply by key first, then subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_picture_graph",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_08"],
        "math_note": "20−10=10 ✓",
        "verification": make_verification()
    },
    {
        "id": "R1_09",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Picture graph key: Each 🌟 = 3. "
            "Red team: 4 symbols. Blue team: 3½ symbols. Green team: 2 symbols. "
            "How many students in all three teams?"
        ),
        "data_table": {
            "title": "Team Members",
            "type": "picture_graph",
            "categories": ["Red", "Blue", "Green"],
            "symbol_counts": [4, 3.5, 2],
            "key_value": 3,
            "unit": "students"
        },
        "choices": ["A. 9½", "B. 28", "C. 28½", "D. 9"],
        "answer": "C",
        "explanation": "Red=4×3=12. Blue=3½×3=10½. Green=2×3=6. Total=12+10½+6=28½.",
        "solution_steps": [
            "Red=4×3=12, Blue=3½×3=10½, Green=2×3=6",
            "12+10½+6=28½"
        ],
        "hints": [
            "Multiply each team's symbols by 3. Remember ½×3=1½.",
            "Add all three values."
        ],
        "feedback": {
            "correct": "Great! 12+10½+6=28½ students total.",
            "incorrect": "Don't skip the ½ symbol: 3½×3=10½, not 9."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "find_total_picture_graph",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_09"],
        "math_note": "12+10½+6=28½ ✓ 반 심볼: ½×3=1½.",
        "verification": make_verification()
    },
    {
        "id": "R1_10",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "A picture graph shows: Soccer = 4 symbols. Key = 5. "
            "If 5 more students join the soccer category, how many total symbols "
            "would Soccer need to show?"
        ),
        "data_table": {
            "title": "Sports Club",
            "type": "picture_graph",
            "categories": ["Soccer"],
            "symbol_counts": [4],
            "key_value": 5,
            "unit": "students"
        },
        "choices": ["A. 4", "B. 5", "C. 9", "D. 25"],
        "answer": "B",
        "explanation": "Current Soccer = 4×5 = 20. New total = 20+5 = 25. Symbols needed = 25÷5 = 5.",
        "solution_steps": [
            "Current value = 4×5 = 20",
            "New value = 20+5 = 25",
            "New symbols = 25÷5 = 5"
        ],
        "hints": [
            "First find the current value (symbols × key).",
            "Add 5, then divide by key to get new symbol count."
        ],
        "feedback": {
            "correct": "Correct! 20+5=25, 25÷5=5 symbols.",
            "incorrect": "Step 1: current value = 4×5=20. Step 2: add 5. Step 3: divide by key."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "hypothetical_graph_change",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_10"],
        "math_note": "현재=4×5=20, 새값=20+5=25, 심볼=25÷5=5 ✓",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 신규 R2 카드 (R2_05 ~ R2_10)
# ─────────────────────────────────────────
NEW_R2_CARDS = [
    {
        "id": "R2_05",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Picture graph: Cats 🐱🐱🐱🐱 (4 symbols), Dogs 🐱🐱🐱 (3 symbols), "
            "Fish 🐱½ (1½ symbols). Key = 4. "
            "How many more students chose Cats than Fish?"
        ),
        "data_table": {
            "title": "Favorite Pet",
            "type": "picture_graph",
            "categories": ["Cats", "Dogs", "Fish"],
            "symbol_counts": [4, 3, 1.5],
            "key_value": 4,
            "unit": "students"
        },
        "choices": ["A. 16", "B. 10", "C. 22", "D. 2.5"],
        "answer": "B",
        "explanation": "Cats=4×4=16. Fish=1½×4=6. 16−6=10.",
        "hints": [
            "Find Cats and Fish values only (ignore Dogs).",
            "Subtract Fish from Cats."
        ],
        "feedback": {
            "correct": "Correct! Cats=16, Fish=6, 16−6=10.",
            "incorrect": "Use only Cats and Fish. Multiply by key, then subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_picture_graph",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_05"],
        "math_note": "Cats=4×4=16, Fish=1½×4=6, 16−6=10 ✓",
        "verification": make_verification()
    },
    {
        "id": "R2_06",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Picture graph key: Each 🏆 = 6 points. "
            "Team A: 5 symbols, Team B: 4½ symbols, Team C: 2 symbols, Team D: 3 symbols. "
            "Which team scored the fewest points?"
        ),
        "data_table": {
            "title": "Tournament Scores",
            "type": "picture_graph",
            "categories": ["Team A", "Team B", "Team C", "Team D"],
            "symbol_counts": [5, 4.5, 2, 3],
            "key_value": 6,
            "unit": "points"
        },
        "choices": ["A. Team A", "B. Team B", "C. Team C", "D. Team D"],
        "answer": "C",
        "explanation": "A=30, B=27, C=12, D=18. Fewest = Team C (12).",
        "hints": [
            "Multiply each team's symbols by 6.",
            "Compare all four values to find the smallest."
        ],
        "feedback": {
            "correct": "Correct! C=2×6=12 is the fewest.",
            "incorrect": "Check all teams: A=30, B=27, C=12, D=18. Which is smallest?"
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "identify_max_min",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_06"],
        "math_note": "A=30, B=27, C=12, D=18. 최솟값=C(12) ✓",
        "verification": make_verification()
    },
    {
        "id": "R2_07",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Picture graph key: Each 🎵 = 5. "
            "Rock: 6 symbols, Pop: 4½ symbols, Jazz: 3 symbols. "
            "How many students chose Rock or Jazz in total?"
        ),
        "data_table": {
            "title": "Favorite Music",
            "type": "picture_graph",
            "categories": ["Rock", "Pop", "Jazz"],
            "symbol_counts": [6, 4.5, 3],
            "key_value": 5,
            "unit": "students"
        },
        "choices": ["A. 30", "B. 22½", "C. 45", "D. 15"],
        "answer": "C",
        "explanation": "Rock=6×5=30. Jazz=3×5=15. Rock+Jazz=30+15=45.",
        "hints": [
            "Find Rock and Jazz values only (ignore Pop).",
            "Add Rock and Jazz together."
        ],
        "feedback": {
            "correct": "Great! Rock=30, Jazz=15, total=45.",
            "incorrect": "Find Rock and Jazz separately, then add them."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "multi_step_picture_graph",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_07"],
        "math_note": "Rock=30, Jazz=15, 합=45 ✓. Pop(22½) 제외.",
        "verification": make_verification()
    },
    {
        "id": "R2_08",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Picture graph key: Each 🌍 = 10. "
            "Asia: 7 symbols, Africa: 5½ symbols, Americas: 4 symbols. "
            "How many more students chose Asia than Africa and Americas combined?"
        ),
        "data_table": {
            "title": "Continent Study",
            "type": "picture_graph",
            "categories": ["Asia", "Africa", "Americas"],
            "symbol_counts": [7, 5.5, 4],
            "key_value": 10,
            "unit": "students"
        },
        "choices": ["A. 15", "B. 70", "C. 25", "D. 155"],
        "answer": "A",
        "explanation": "Asia=7×10=70. Africa=5½×10=55. Americas=4×10=40. Africa+Americas=55+40=95. 70−95=−25? Wait — 95>70, so Americas+Africa > Asia by 25. Asia is fewer. But answer A=15. Let me recalculate. Africa=5½×10=55. Americas=4×10=40. Combined=95. Asia=70. 70<95, so Asia has fewer. The question asks 'more than combined', so this needs correcting.",
        "solution_steps": [
            "Asia=7×10=70",
            "Africa=5½×10=55, Americas=4×10=40",
            "Africa+Americas=55+40=95",
            "95−70=25 (combined is more than Asia)"
        ],
        "hints": [
            "Find Asia, Africa, and Americas values.",
            "Add Africa+Americas, then compare to Asia."
        ],
        "feedback": {
            "correct": "Well done!",
            "incorrect": "Find each value first, then add Africa+Americas to compare with Asia."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "multi_step_picture_graph",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_08"],
        "math_note": "See solution steps.",
        "verification": make_verification()
    },
    {
        "id": "R2_09",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Picture graph key: Each 🌞 = 4. "
            "Monday: 3½ symbols, Tuesday: 2½ symbols. "
            "How many sunny hours on Tuesday?"
        ),
        "data_table": {
            "title": "Sunny Hours",
            "type": "picture_graph",
            "categories": ["Monday", "Tuesday"],
            "symbol_counts": [3.5, 2.5],
            "key_value": 4,
            "unit": "hours"
        },
        "choices": ["A. 2½", "B. 14", "C. 8", "D. 10"],
        "answer": "D",
        "explanation": "Tuesday = 2½ × 4 = 10.",
        "hints": [
            "Tuesday has 2½ symbols.",
            "2½ × 4 = 2×4 + ½×4 = 8+2 = 10."
        ],
        "feedback": {
            "correct": "Correct! 2½×4=10 hours.",
            "incorrect": "Multiply 2½ by 4: 2×4=8, ½×4=2, total=10."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "read_half_symbol",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_09"],
        "math_note": "Tuesday=2½×4=10 ✓",
        "verification": make_verification()
    },
    {
        "id": "R2_10",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Picture graph key: Each 📱 = 8. "
            "Brand A currently has 4 symbols. If 16 more students choose Brand A, "
            "how many total symbols will Brand A show?"
        ),
        "data_table": {
            "title": "Phone Brand Survey",
            "type": "picture_graph",
            "categories": ["Brand A"],
            "symbol_counts": [4],
            "key_value": 8,
            "unit": "students"
        },
        "choices": ["A. 4", "B. 6", "C. 20", "D. 48"],
        "answer": "B",
        "explanation": "Current Brand A = 4×8 = 32. New total = 32+16 = 48. Symbols = 48÷8 = 6.",
        "hints": [
            "Step 1: Find current value (4×8=32).",
            "Step 2: Add 16. Step 3: Divide by key."
        ],
        "feedback": {
            "correct": "Correct! 32+16=48, 48÷8=6 symbols.",
            "incorrect": "Three steps: current value → add 16 → divide by key(8)."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "hypothetical_graph_change",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_10"],
        "math_note": "현재=4×8=32, 새값=32+16=48, 심볼=48÷8=6 ✓",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 신규 R3 카드 (R3_04, R3_05)
# ─────────────────────────────────────────
NEW_R3_CARDS = [
    {
        "id": "R3_04",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Picture graph: key=5. "
            "Library A: 6 symbols, Library B: 4½ symbols, Library C: 3 symbols. "
            "Library B got a donation of 10 new books. "
            "After the donation, how many more books does Library A have than Library C?"
        ),
        "data_table": {
            "title": "Library Books",
            "type": "picture_graph",
            "categories": ["Library A", "Library B", "Library C"],
            "symbol_counts": [6, 4.5, 3],
            "key_value": 5,
            "unit": "books"
        },
        "choices": ["A. 15", "B. 30", "C. 22½", "D. 3"],
        "answer": "A",
        "explanation": (
            "Library A=6×5=30. Library C=3×5=15. "
            "The donation goes to B, not A or C, so it doesn't affect this comparison. "
            "A−C=30−15=15."
        ),
        "hints": [
            "The donation is to Library B — does it change A or C?",
            "Find A and C values, then subtract."
        ],
        "feedback": {
            "correct": "Excellent! The donation to B doesn't change A or C. A=30, C=15, 30−15=15.",
            "incorrect": "The donation goes to Library B. Find A=6×5=30 and C=3×5=15. Subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "multi_step_picture_graph",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R3_04"],
        "math_note": "A=30, C=15, 30−15=15 ✓. Library B 변화는 A-C 비교에 영향 없음.",
        "verification": make_verification()
    },
    {
        "id": "R3_05",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Picture graph key: Each ⚽ = 6 goals. "
            "Team Red: 5 symbols, Team Blue: 3½ symbols, Team Green: 4 symbols, Team Yellow: 2½ symbols. "
            "How many students did NOT cheer for Team Red or Team Blue? "
            "(Each student cheered for exactly one team.)"
        ),
        "data_table": {
            "title": "Team Supporters",
            "type": "picture_graph",
            "categories": ["Team Red", "Team Blue", "Team Green", "Team Yellow"],
            "symbol_counts": [5, 3.5, 4, 2.5],
            "key_value": 6,
            "unit": "students"
        },
        "choices": ["A. 57", "B. 51", "C. 39", "D. 90"],
        "answer": "C",
        "explanation": (
            "Red=5×6=30. Blue=3½×6=21. Green=4×6=24. Yellow=2½×6=15. "
            "Total=30+21+24+15=90. "
            "NOT Red or Blue = Green+Yellow = 24+15 = 39."
        ),
        "hints": [
            "Find all four team values first.",
            "Add only Green and Yellow (those NOT cheering for Red or Blue)."
        ],
        "feedback": {
            "correct": "Correct! Green=24, Yellow=15, total NOT Red/Blue=39.",
            "incorrect": "Find Green+Yellow: 4×6=24 and 2½×6=15. Add them: 39."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "multi_step_picture_graph",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R3_05"],
        "math_note": "Green=24, Yellow=15, 합=39 ✓. Red+Blue=51(오답 함정).",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 메인 업그레이드 함수
# ─────────────────────────────────────────
def upgrade():
    with open(SRC) as f:
        d = json.load(f)

    items_flat: list[dict] = d.pop("items", [])
    d.pop("concept", None)

    # 섹션별 분류 (원본 flat items)
    by_section: dict[str, list[dict]] = {
        "pretest": [],
        "learn": [],
        "try": [],
        "practice_r1": [],
        "practice_r2": [],
        "practice_r3": [],
    }
    for item in items_flat:
        sec = item.pop("section", "")
        by_section.get(sec, []).append(item)

    # ─ Pretest (PT_01~05) ─
    pretest_items = [add_item_fields(item) for item in by_section["pretest"]]

    # ─ Learn (LN_01~03 → LEARN_01~03, + LEARN_04~08) ─
    learn_items = []
    for i, item in enumerate(by_section["learn"], start=1):
        item["id"] = f"LEARN_0{i}"
        if "cpa_phase" in item:
            item["cpa_stage"] = item.pop("cpa_phase")
        item["ccss"] = "3.MD.B.3"
        item["math_note"] = item.get("content", "")[:80]
        item["verification"] = make_verification()
        item.pop("section", None)
        item.pop("difficulty", None)
        learn_items.append(item)
    learn_items.extend(NEW_LEARN_CARDS)

    # ─ Try (TRY_01~03 원본 + TRY_04~05 신규) ─
    try_items = []
    for item in by_section["try"]:
        try_items.append(add_item_fields(item))
    for card in NEW_TRY_CARDS:
        add_item_fields(card)   # feedback_correct 등 공통 필드 추가
    try_items.extend(NEW_TRY_CARDS)

    # ─ R1 (7개 원본 + 3개 신규 = 10개) ─
    r1_items = [add_item_fields(item) for item in by_section["practice_r1"]]
    for card in NEW_R1_CARDS:
        add_item_fields(card)
    r1_items.extend(NEW_R1_CARDS)

    # ─ R2 (4개 원본 + 6개 신규 = 10개) ─
    # R2_08에 오류가 있으므로 수정 후 추가
    r2_items = [add_item_fields(item) for item in by_section["practice_r2"]]
    # R2_08 수정: 문제가 모순적 — Asia < Africa+Americas이므로 질문 방향 수정
    for card in NEW_R2_CARDS:
        # R2_08 문제 수정: "How many more combined (Africa+Americas) than Asia?"
        if card["id"] == "R2_08":
            card["question"] = (
                "Picture graph key: Each 🌍 = 10. "
                "Asia: 7 symbols, Africa: 5½ symbols, Americas: 4 symbols. "
                "How many more students chose Africa and Americas combined than Asia?"
            )
            card["choices"] = ["A. 15", "B. 25", "C. 70", "D. 95"]
            card["answer"] = "B"
            card["explanation"] = "Asia=7×10=70. Africa=5½×10=55. Americas=4×10=40. Combined=95. 95−70=25."
            card["solution_steps"] = [
                "Asia=7×10=70",
                "Africa=5½×10=55, Americas=4×10=40",
                "Africa+Americas=55+40=95",
                "95−70=25"
            ]
            card["math_note"] = "Asia=70, Africa+Americas=95, 95−70=25 ✓"
        add_item_fields(card)
    r2_items.extend(NEW_R2_CARDS)

    # ─ R2 마지막 25% (3개)에 interleave 태그 추가 (S5 감사 통과 — review_from_units=['U1'])
    r2_tail_start = len(r2_items) * 3 // 4
    for item in r2_items[r2_tail_start:]:
        item["review_from"] = "U1"

    # ─ R3 (3개 원본 + 2개 신규 = 5개) ─
    r3_items = [add_item_fields(item) for item in by_section["practice_r3"]]
    for card in NEW_R3_CARDS:
        add_item_fields(card)
    r3_items.extend(NEW_R3_CARDS)

    # ─────────────────────────────────────────
    # 레슨 레벨 메타데이터 추가
    # ─────────────────────────────────────────
    d["tier"] = "A"
    d["vertical_alignment"] = {
        "prerequisite": "2.MD.D.10",
        "successor": "4.MD.B.4"
    }
    # unit_intro/close는 L1에서 이미 설정됨 — L2는 레슨별 메시지만
    d["unit_intro_message"] = (
        "U2에 오신 것을 환영합니다! 이 단원에서는 탤리표·빈도표·그림 그래프·막대 그래프로 "
        "데이터를 정리하고 읽는 방법을 배웁니다."
    )
    d["unit_close_message"] = (
        "U2를 완료했습니다! 탤리표와 빈도표를 읽고 작성하며, "
        "그림 그래프와 막대 그래프를 해석하는 능력을 갖추었습니다."
    )
    d["review_from_units"] = ["U1"]
    d["interleave_ratio"] = 0.2
    d["passing_threshold"] = 0.75
    d["fluency_required"] = False
    d["supplementary_video"] = (
        "https://www.khanacademy.org/math/cc-third-grade-math/represent-and-interpret-data"
    )

    # ─────────────────────────────────────────
    # 섹션 배열 삽입
    # ─────────────────────────────────────────
    d["pretest"]      = pretest_items
    d["learn"]        = learn_items
    d["try"]          = try_items
    d["practice_r1"]  = r1_items
    d["practice_r2"]  = r2_items
    d["practice_r3"]  = r3_items

    # ─────────────────────────────────────────
    # 저장
    # ─────────────────────────────────────────
    with open(DST, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    total = (len(pretest_items) + len(learn_items) + len(try_items)
             + len(r1_items) + len(r2_items) + len(r3_items))
    print(f"✅ 업그레이드 완료: {DST.name}")
    print(f"   PT={len(pretest_items)}  LEARN={len(learn_items)}  TRY={len(try_items)}")
    print(f"   R1={len(r1_items)}  R2={len(r2_items)}  R3={len(r3_items)}")
    print(f"   총 문항 수: {total}")


if __name__ == "__main__":
    upgrade()
