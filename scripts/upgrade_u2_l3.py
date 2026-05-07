#!/usr/bin/env python3
"""
G3 U2 L3 — Make Picture Graphs
7-Stage 업그레이드 스크립트

변환 작업:
1. 평탄 items 배열 → 섹션별 구조 (pretest/learn/try/practice_r1/r2/r3)
2. LN_XX 식별자 → LEARN_XX로 변경
3. cpa_phase → cpa_stage로 필드명 통일
4. 각 문항에 verification 블록 추가
5. 각 문항에 expected_errors 추가 (3.MD.B.3 오개념 매핑)
6. LEARN 카드 3개 → 8개로 확장 (LEARN_04~08 신규)
7. TRY 카드 3개 → 5개로 확장 (TRY_04~05 신규)
8. R1 카드 8개 → 10개로 확장 (R1_09~10 신규)
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
SRC  = REPO / "backend/data/math/G3/U2_represent_interpret_data/L3_make_picture_graphs.json"
DST  = SRC   # 원본 파일을 직접 업그레이드

# ─────────────────────────────────────────
# 오개념 ID 상수 (3.MD.B.3)
# ─────────────────────────────────────────
M01 = "3.MD.B.3.M01"   # tally_miscount / 키 무시 (심볼→값 변환 오류)
M02 = "3.MD.B.3.M02"   # wrong_row_column (잘못된 카테고리 선택)
M03 = "3.MD.B.3.M03"   # add_instead_of_subtract (비교에서 덧셈)
M04 = "3.MD.B.3.M04"   # include_all_categories (전체 합산 오류)
M05 = "3.MD.B.3.M05"   # total_as_comparison (중간 결과에서 멈춤)
M06 = "3.MD.B.3.M06"   # category_identification_error (최대/최소 오식별)
M07 = "3.MD.B.3.M07"   # two_step_data_error (2단계 문제 오류)

# ─────────────────────────────────────────
# 검증 블록 (레슨 전체 공통)
# ─────────────────────────────────────────
def make_verification() -> dict:
    return {
        "concept_source": {
            "name": "Go Math Grade 3 Chapter 2 Lesson 2.3 — Make Picture Graphs",
            "url": "https://www.hmhco.com/programs/go-math",
            "description": "그림 그래프 만들기: 키 선택, 값÷키=심볼 수, 반 심볼 사용"
        },
        "procedure_source": {
            "name": "EngageNY Grade 3 Module 6 Lesson 5 — Make Picture Graphs",
            "url": "https://www.engageny.org/resource/grade-3-mathematics-module-6",
            "description": "스케일 그림 그래프 만들기 절차: 키 결정 → 나눗셈 → 심볼 그리기"
        },
        "assessment_source": {
            "name": "Smarter Balanced Grade 3 Sample Items — 3.MD.B.3",
            "url": "https://sampleitems.smarterbalanced.org/",
            "description": "3.MD.B.3 평가 지침 — 그림 그래프 만들기 및 키 선택 문제"
        }
    }


# ─────────────────────────────────────────
# 오개념 항목별 매핑 (item_id → expected_errors 리스트)
# ─────────────────────────────────────────
ERRORS_MAP: dict[str, list[dict]] = {
    # ── Pretest ──
    "PT_01": [
        # Comedy 8 → 8÷2=4. 오답 D(8): 나눗셈 없이 원래 값 제출
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(÷2) 무시하고 원래 값(8) 그대로 제출",
         "citation": "Friel et al. (2001) p.130 — 그림 그래프 스케일 오독"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "8÷4=2로 키를 4로 혼동"},
    ],
    "PT_02": [
        # 15÷5=3. 오답 D(15): 나눗셈 없이 원래 투표 수 제출
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(÷5) 무시하고 투표 수(15) 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "15÷5=3이 아닌 5÷3≈1.7로 잘못 계산"},
    ],
    "PT_03": [
        # Toast 5÷5=1. 오답 B(2): Cereal(10÷5=2) 행 잘못 읽음
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Toast 대신 Cereal(10) 행 읽어 10÷5=2 제출",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Toast 값(5)을 심볼 수로 오독"},
    ],
    "PT_04": [
        # key=3 (12/9/6 모두 나눠짐). 오답 D(key=5): 14÷3≠정수 아닌지 검토 없이 round 숫자 선택
        # 실제로는 soccer=9는 9÷5=1.8로 key=5 안 됨
        {"error_type": "misconception", "misconception_id": M06,
         "description": "각 값을 나눠보지 않고 직관적으로 key=5(큰 수) 선택",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "key=2: 12÷2=6, 9÷2=4.5 (반 심볼 필요) — 완전 나눔 아님"},
    ],
    "PT_05": [
        # (6+9+3)÷3=6 총 심볼. 오답 D(18): 나눗셈 없이 원래 합 18 제출
        {"error_type": "misconception", "misconception_id": M05,
         "description": "합(18)을 구한 후 키(÷3) 단계를 누락하고 18 제출",
         "citation": "EngageNY G3 M6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "6÷3+9÷3=2+3=5만 계산 (Climbing 누락)"},
    ],
    # ── TRY ──
    "TRY_01": [
        # Dogs 12÷4=3. 오답 D(12): 나눗셈 없이 값 제출
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(÷4) 무시하고 Dogs 값(12) 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "12÷3=4로 키 값 혼동 (나누는 수로 4 대신 3 사용)"},
    ],
    "TRY_02": [
        # Bananas 7÷2=3½. 오답 C(4): 반 심볼 반올림
        {"error_type": "misconception", "misconception_id": M01,
         "description": "7÷2=3.5를 반올림하여 4로 제출 (반 심볼 무시)",
         "citation": "Friel et al. (2001) p.130 — 반 심볼 오독"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "7÷2=3으로 소수점 이하 버림"},
    ],
    "TRY_03": [
        # Soccer 4×2=8, Baseball 2½×2=5, 8-5=3. 오답 A(2): 심볼 수만 빼기
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키 곱하기 없이 심볼 수(4-2.5=1.5≈2) 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "8+5=13 (비교에 덧셈 수행)"},
    ],
    "TRY_04": [
        # key=5: 3,2,4,1 모두 정수. 오답 A(key=2): 기술적으로 가능하나 반 심볼 있음
        {"error_type": "misconception", "misconception_id": M06,
         "description": "key=2 선택 (Art=10÷2=5는 정수지만 Dance=20÷2=10 심볼 과다)",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "key=3: Drama=5÷3=1⅔ (정수 아님), 잘못된 선택"},
    ],
    "TRY_05": [
        # 총 심볼 2+3+1+4=10. 오답 A(50, 원래 합계): 나눗셈 없이 합산
        {"error_type": "misconception", "misconception_id": M05,
         "description": "10+15+5+20=50을 구한 후 키(÷5) 단계 누락",
         "citation": "EngageNY G3 M6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Spring(2)+Summer(3)=5만 계산 (나머지 카테고리 누락)"},
    ],
    # ── R1 ──
    "R1_01": [
        # 9÷3=3. 오답 D(9): 키 무시
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(÷3) 무시하고 원래 값(9) 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "9÷3=3이 아닌 9-3=6으로 잘못 계산"},
    ],
    "R1_02": [
        # 20÷5=4. 오답 D(10): 20÷2=10 (키를 2로 혼동)
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(5) 대신 2로 나눠 20÷2=10 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "20÷10=2로 계산 오류"},
    ],
    "R1_03": [
        # Red 6÷2=3. 오답 A(2): Blue(10÷5=2) 잘못 읽음
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Red 대신 Blue(10÷2=5→오답 C) 또는 Yellow(4÷2=2→오답 A) 행 읽음",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "6÷2=3이 아닌 6 그대로 제출"},
    ],
    "R1_04": [
        # 4÷2=2. 오답 B(4): 나눗셈 없이 값 제출
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(÷2) 무시하고 Country 투표 수(4) 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "4÷2=2가 아닌 4+2=6으로 잘못 계산"},
    ],
    "R1_05": [
        # key=3: 14÷3=4.67 (½ 아님). 오답 A(key=2): key=2도 14÷2=7, 8÷2=4 정수 → 문제는 '잘 안 맞는' 키
        {"error_type": "misconception", "misconception_id": M06,
         "description": "key=3이 Swim(14)에서 깔끔하지 않음을 파악 못하고 key=2(정답 아님) 선택",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "key=1 선택 (맞지만 비효율적, 문제는 '잘 맞지 않는' 키)"},
    ],
    "R1_06": [
        # 4+2+3=9 총 심볼. 오답 D(27): 나눗셈 없이 원래 합 제출
        {"error_type": "misconception", "misconception_id": M05,
         "description": "12+6+9=27 합계만 구하고 키(÷3) 변환 미완료",
         "citation": "EngageNY G3 M6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Fiction(12÷3=4)만 계산하고 다른 카테고리 누락"},
    ],
    "R1_07": [
        # 12÷4=3. 오답 A(2): 12÷6=2로 키 값 혼동
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키(4) 대신 6으로 나눠 12÷6=2 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "12÷4=3이 아닌 12 그대로 제출"},
    ],
    "R1_08": [
        # 10÷5 = 2, 즉 key=2. 오답 D(key=10): 각 심볼이 10을 나타냄
        {"error_type": "misconception", "misconception_id": M07,
         "description": "심볼 수(5)와 값(10)의 관계를 역산하지 않고 key=10 선택",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "10÷2=5이므로 key=5라고 오해 (10÷5=2인데 key를 5로 혼동)"},
    ],
    "R1_09": [
        # 9÷6=1½. 오답 C(2): 반 심볼 반올림
        {"error_type": "misconception", "misconception_id": M01,
         "description": "9÷6=1.5를 반올림하여 2 제출 (반 심볼 무시)",
         "citation": "Friel et al. (2001) p.130 — 반 심볼 오독"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "9÷6=1.5를 내림하여 1 제출"},
    ],
    "R1_10": [
        # Dance 18÷3=6 (가장 많음). 오답 B(Drama): Drama(12÷3=4) 잘못 선택
        {"error_type": "misconception", "misconception_id": M06,
         "description": "가장 큰 심볼 수(Dance=6) 대신 두 번째(Drama=4) 선택",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "나눗셈 없이 가장 큰 원래 값(18) 카테고리 선택(= 우연히 정답)"},
    ],
    # ── R2 ──
    "R2_01": [
        # Hiking 15÷5=3. 오답 D(5): 나눗셈 없이 키 값(5) 제출
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키 값(5)을 심볼 수로 오해하여 5 제출",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "15÷15=1로 잘못 계산"},
    ],
    "R2_02": [
        # Markers 7÷2=3½. 오답 C(4): 반 심볼 반올림
        {"error_type": "misconception", "misconception_id": M01,
         "description": "7÷2=3.5를 4로 반올림 (반 심볼 무시)",
         "citation": "Friel et al. (2001) p.130 — 반 심볼 오독"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "나눗셈 없이 Markers 값(7) 제출"},
    ],
    "R2_03": [
        # 가장 큰 값(24), max 6심볼 → 24÷4=6, key=4. 오답 A(key=3): 24÷3=8>6 초과
        {"error_type": "misconception", "misconception_id": M06,
         "description": "key=3 선택: 24÷3=8>6 심볼로 조건 위반",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "key=6: Peach=6÷6=1, Grapes=18÷6=3, 조건 충족하나 반 심볼 생김"},
    ],
    "R2_04": [
        # Pizza 8심볼, Soup 4심볼, 8-4=4. 오답 C(6): Pizza-Salad 혼동
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Soup 대신 Salad(6÷2=3) 행 읽어 8-3=5 또는 Pizza-Burger=8-5=3 제출",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "키(÷2) 없이 심볼 수 차이만 계산 (8-4=4이지만 심볼 수만으로 4-2=2)"},
    ],
    "R2_05": [
        # 4×4+3½×4+5×4=16+14+20=50. 오답 A(12½): 심볼 수만 합산
        {"error_type": "misconception", "misconception_id": M01,
         "description": "키 곱하기 없이 심볼 수(4+3½+5=12½)만 합산",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "일부 카테고리만 계산 (Math+Science=16+20=36)"},
    ],
    "R2_06": [
        # Red=7심볼, Purple=2심볼, 7-2=5. 오답 A(3): Blue-Purple=4-2=2가 아닌 다른 비교
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 많은' 질문에 7+2=9 덧셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "나눗셈 없이 원래 값 차이(14-4=10) 제출"},
    ],
    "R2_07": [
        # 5+3+2+4=14 총 심볼. 오답 D(42): 원래 합계 제출
        {"error_type": "misconception", "misconception_id": M05,
         "description": "15+9+6+12=42 합계만 구하고 키(÷3) 변환 미완료",
         "citation": "EngageNY G3 M6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Apples(5)+Pears(3)=8만 합산 (나머지 카테고리 누락)"},
    ],
    "R2_08": [
        # 탈리 Soccer=𝍸𝍸|=11, 11÷2=5½. 오답 B(5): 반 심볼 무시
        {"error_type": "misconception", "misconception_id": M01,
         "description": "11÷2=5.5를 5로 내림 (반 심볼 무시)",
         "citation": "Friel et al. (2001) p.130 — 탤리 오독 + 반 심볼 무시"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "나눗셈 없이 탈리 수(11) 그대로 제출"},
    ],
    "R2_09": [
        # Red=𝍸𝍸𝍸=15→3심볼, Blue=𝍸𝍸=10→2심볼, 3-2=1. 오답 B(2): Red 심볼 수 제출
        {"error_type": "misconception", "misconception_id": M03,
         "description": "비교 대신 Red 심볼 수(3) 또는 Blue 심볼 수(2)를 답으로 제출",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "원래 탈리 차이(15-10=5) 제출 (심볼 변환 전)"},
    ],
    "R2_10": [
        # Mon=𝍸𝍸=10→2, Tue=𝍸𝍸𝍸=15→3, Wed=𝍸=5→1, 2+3+1=6. 오답 D(30): 원래 합계
        {"error_type": "misconception", "misconception_id": M05,
         "description": "10+15+5=30 원래 합계 제출 (키÷5 변환 미완료)",
         "citation": "EngageNY G3 M6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Tuesday(3)+Wednesday(1)=4만 합산 (Monday 누락)"},
    ],
    # ── R3 ──
    "R3_01": [
        # 4+3+2+1=10심볼, 12+9+6+3=30. 오답 C(12): Soccer 심볼(4) 그대로 제출
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Soccer(4)만 계산하고 나머지 카테고리 심볼 합산 누락",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "8심볼 + 합계 계산 오류"},
    ],
    "R3_02": [
        # 3½×4=14, 14+6=20, 20÷4=5. 오답 A(4½): 반 심볼 유지 오류
        {"error_type": "misconception", "misconception_id": M07,
         "description": "14+6=20 후 20÷4=5가 아닌 3½+6÷4=3½+1½=5 오해",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "원래 심볼(3½)에 직접 덧셈: 3½+2=5½"},
    ],
    "R3_03": [
        # Jake(key=5)=14심볼, friend(key=10)=7심볼, 14-7=7. 오답 C(8): 계산 오류
        {"error_type": "misconception", "misconception_id": M07,
         "description": "friend의 심볼 계산: 2+1½+2½+1=7이 아닌 2+2+2+2=8로 계산",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Jake 심볼 수(14)만 제출"},
    ],
    "R3_04": [
        # Drama=4×6=24, +12→36, 36÷6=6. 오답 A(4): 원래 심볼 수 제출
        {"error_type": "misconception", "misconception_id": M07,
         "description": "24+12=36 후 36÷6=6이 아닌 4+2=6 계산 오류",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "12÷6=2만 계산하고 원래 4심볼에 더하지 않음"},
    ],
    "R3_05": [
        # key=3: 4,6,2,3 모두 정수. 오답 A(key=2): Winter=9÷2=4½ 반 심볼 생김
        {"error_type": "misconception", "misconception_id": M06,
         "description": "key=2 선택: Winter=9÷2=4½ (반 심볼 필요 → 정수 조건 위반)",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "key=6: Winter=9÷6=1½ (반 심볼 필요 → 정수 조건 위반)"},
    ],
}


# ─────────────────────────────────────────
# 기본 skill_tag 매핑 (item_id → tag)
# ─────────────────────────────────────────
SKILL_TAGS: dict[str, str] = {
    "PT_01": "divide_to_symbols",
    "PT_02": "divide_to_symbols",
    "PT_03": "divide_to_symbols",
    "PT_04": "choose_key",
    "PT_05": "total_symbols",
    "TRY_01": "divide_to_symbols",
    "TRY_02": "half_symbol_draw",
    "TRY_03": "compare_symbols",
    "TRY_04": "choose_key",
    "TRY_05": "total_symbols",
    "R1_01": "divide_to_symbols",
    "R1_02": "divide_to_symbols",
    "R1_03": "divide_to_symbols",
    "R1_04": "divide_to_symbols",
    "R1_05": "choose_key",
    "R1_06": "total_symbols",
    "R1_07": "divide_to_symbols",
    "R1_08": "choose_key",
    "R1_09": "half_symbol_draw",
    "R1_10": "compare_symbols",
    "R2_01": "divide_to_symbols",
    "R2_02": "half_symbol_draw",
    "R2_03": "choose_key",
    "R2_04": "compare_symbols",
    "R2_05": "symbol_to_value",
    "R2_06": "compare_symbols",
    "R2_07": "total_symbols",
    "R2_08": "half_symbol_draw",
    "R2_09": "compare_symbols",
    "R2_10": "total_symbols",
    "R3_01": "total_symbols",
    "R3_02": "graph_update",
    "R3_03": "compare_symbols",
    "R3_04": "graph_update",
    "R3_05": "choose_key",
}

# CPA 단계 (문항별)
CPA_MAP: dict[str, str] = {
    "PT_01": "concrete",
    "PT_02": "concrete",
    "PT_03": "concrete",
    "PT_04": "pictorial",
    "PT_05": "pictorial",
    "TRY_01": "concrete",
    "TRY_02": "concrete",
    "TRY_03": "pictorial",
    "TRY_04": "pictorial",
    "TRY_05": "abstract",
    "R1_01": "concrete",
    "R1_02": "concrete",
    "R1_03": "concrete",
    "R1_04": "concrete",
    "R1_05": "pictorial",
    "R1_06": "pictorial",
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


def add_item_fields(item: dict) -> dict:
    """개별 문항에 검증·오개념·공통 필드를 추가한다."""
    iid = item.get("id", "")

    # type 필드 보완
    if "type" not in item:
        item["type"] = "multiple_choice"

    # ccss 통일
    if "ccss" not in item:
        item["ccss"] = "3.MD.B.3"
    elif isinstance(item["ccss"], list):
        item["ccss"] = item["ccss"][0] if item["ccss"] else "3.MD.B.3"

    # skill_tag
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(iid, "divide_to_symbols")

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
        "title": "Guided Example — Making a Picture Graph",
        "content": (
            "Frequency table: Cats 6, Dogs 10, Birds 4. Key = 2. "
            "Step 1: Cats → 6 ÷ 2 = 3 symbols. "
            "Step 2: Dogs → 10 ÷ 2 = 5 symbols. "
            "Step 3: Birds → 4 ÷ 2 = 2 symbols. "
            "Draw the symbols in each row and write the key at the bottom."
        ),
        "visual_type": "picture_graph",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "Cats=6÷2=3, Dogs=10÷2=5, Birds=4÷2=2. 규칙: 심볼 수 = 값 ÷ 키.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "Half Symbols in Practice",
        "content": (
            "When a data value is NOT evenly divisible by the key, use a half symbol. "
            "Example: Key = 2. Red 9, Blue 6, Green 7. "
            "Red: 9 ÷ 2 = 4½ → draw 4 full + 1 half symbol. "
            "Blue: 6 ÷ 2 = 3 → draw 3 full symbols. "
            "Green: 7 ÷ 2 = 3½ → draw 3 full + 1 half symbol. "
            "Half symbol = half the key value (here, ½ symbol = 1 student)."
        ),
        "visual_type": "picture_graph",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "키=2: Red=4½심볼, Blue=3심볼, Green=3½심볼. 반 심볼=키÷2=1.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "Choosing the Right Key",
        "content": (
            "Test your key by dividing each data value. The best key gives whole numbers "
            "or clean halves (÷ 0.5) for ALL categories. "
            "Example: Basketball 12, Soccer 18, Tennis 6, Baseball 9. "
            "Test key=3: 12÷3=4 ✓, 18÷3=6 ✓, 6÷3=2 ✓, 9÷3=3 ✓ → key=3 works! "
            "Test key=4: 12÷4=3 ✓, 18÷4=4.5 ✓, 6÷4=1.5 ✓, 9÷4=2.25 ✗ → key=4 doesn't work cleanly."
        ),
        "visual_type": "none",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "key=3 선택 이유: 12,18,6,9 모두 3의 배수. key=4는 9÷4=2.25 (불가).",
        "verification": make_verification()
    },
    {
        "id": "LEARN_07",
        "type": "explain",
        "title": "Math Talk: Which Key Needs a Half Symbol?",
        "content": (
            "Frequency table: Band 20, Art 15, Drama 10. "
            "Lily uses key=5: Band=4, Art=3, Drama=2 — all WHOLE symbols. ✓ "
            "Her friend uses key=10: Band=2, Art=1½, Drama=1 — Art needs a HALF symbol. "
            "Both keys are valid, but key=5 gives a more precise graph with no half symbols. "
            "(Smaller key = more symbols = more precise. Larger key = fewer symbols = simpler graph.)"
        ),
        "visual_type": "none",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_talk_prompt": (
            "Band=20, Art=15, Drama=10 데이터에서 "
            "key=5: Band=4, Art=3, Drama=2 (반 심볼 없음) vs "
            "key=10: Band=2, Art=1½, Drama=1 (Art에 반 심볼 필요). "
            "왜 key=5가 key=10보다 정밀한가요? "
            "키를 작게 할수록/크게 할수록 그래프가 어떻게 달라지나요? "
            "어떤 상황에서 큰 키(key=10)를 쓰는 것이 나을까요?"
        ),
        "math_note": "key=5: 모두 정수 ✓. key=10: Art=1½ 반 심볼 필요. 작은 키=더 정밀, 큰 키=더 단순.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_08",
        "type": "summary",
        "title": "Lesson Summary: Make Picture Graphs",
        "content": (
            "In this lesson you learned how to: "
            "① Choose a key: pick a number that divides evenly into most data values. "
            "② Find symbols: data value ÷ key = number of symbols to draw. "
            "③ Use half symbols: if remainder = ½ of key, draw a half symbol. "
            "④ Count total symbols: divide each value by key, then ADD the symbol counts. "
            "⑤ Write the key at the bottom of every picture graph."
        ),
        "lesson_summary": (
            "그림 그래프 만들기 마스터: "
            "①키 선택: 모든 데이터 값이 깔끔하게 나눠지는 수 "
            "②심볼 수=값÷키 "
            "③반 심볼: 나머지=키÷2일 때 사용 "
            "④총 심볼=각 카테고리 심볼 수 합산 "
            "⑤그래프 하단에 키 표기 필수"
        ),
        "visual_type": "none",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "핵심: 값÷키=심볼 수. 나머지가 키÷2이면 반 심볼 사용.",
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
            "Frequency table: Music 15, Art 10, Dance 20, Drama 5. "
            "Which key lets ALL categories use whole number symbols only (no half symbols)?"
        ),
        "data_table": {
            "title": "After-School Club Survey",
            "type": "frequency_table",
            "categories": ["Music", "Art", "Dance", "Drama"],
            "values": [15, 10, 20, 5],
            "scale": 1,
            "unit": "students"
        },
        "choices": [
            "A. Each symbol = 2",
            "B. Each symbol = 3",
            "C. Each symbol = 5",
            "D. Each symbol = 4"
        ],
        "answer": "C",
        "explanation": (
            "key=5: Music=15÷5=3 ✓, Art=10÷5=2 ✓, Dance=20÷5=4 ✓, Drama=5÷5=1 ✓. "
            "key=2: Dance=20÷2=10 ✓ but others give large counts. "
            "key=3: Dance=20÷3≈6.67 ✗. key=4: Art=10÷4=2.5 ✗. Only key=5 gives all whole numbers."
        ),
        "solution_steps": [
            "Test key=5: 15÷5=3, 10÷5=2, 20÷5=4, 5÷5=1 → all whole ✓",
            "key=2: Drama=5÷2=2½ ✗. key=3: Dance=20÷3=6⅔ ✗. key=4: Art=10÷4=2½ ✗"
        ],
        "hints": [
            "Divide each data value by the key. All results must be whole numbers.",
            "Try key=5 with all four values."
        ],
        "feedback": {
            "correct": "Correct! key=5 divides evenly into 15, 10, 20, and 5.",
            "incorrect": "Test each key by dividing all four values. Only key=5 gives all whole numbers."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "choose_key",
        "cpa_stage": "pictorial",
        "expected_errors": ERRORS_MAP["TRY_04"],
        "math_note": "key=5: 3,2,4,1 모두 정수 ✓. 다른 키는 분수 발생.",
        "verification": make_verification()
    },
    {
        "id": "TRY_05",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Frequency table: Spring 10, Summer 15, Fall 5, Winter 20. Each symbol = 5 students. "
            "What is the TOTAL number of symbols in the picture graph?"
        ),
        "data_table": {
            "title": "Favorite Season",
            "type": "frequency_table",
            "categories": ["Spring", "Summer", "Fall", "Winter"],
            "values": [10, 15, 5, 20],
            "scale": 1,
            "unit": "students"
        },
        "choices": [
            "A. 50",
            "B. 8",
            "C. 10",
            "D. 5"
        ],
        "answer": "C",
        "explanation": (
            "Spring=10÷5=2. Summer=15÷5=3. Fall=5÷5=1. Winter=20÷5=4. "
            "Total symbols = 2+3+1+4 = 10."
        ),
        "solution_steps": [
            "Spring=10÷5=2, Summer=15÷5=3, Fall=5÷5=1, Winter=20÷5=4",
            "Total = 2+3+1+4 = 10"
        ],
        "hints": [
            "Divide each value by 5 to find symbols per category.",
            "Add all four symbol counts."
        ],
        "feedback": {
            "correct": "Perfect! 2+3+1+4=10 total symbols.",
            "incorrect": "First divide each value by 5, then add all symbol counts."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "total_symbols",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["TRY_05"],
        "math_note": "2+3+1+4=10 ✓ 총 심볼 수. 오답 A(50)은 키 변환 전 합계.",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 신규 R1 카드 (R1_09, R1_10)
# ─────────────────────────────────────────
NEW_R1_CARDS = [
    {
        "id": "R1_09",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": "Each symbol = 6. You need to show 9 students in a picture graph. How many symbols (including half symbols) do you draw?",
        "choices": [
            "A. 1",
            "B. 1½",
            "C. 2",
            "D. 3"
        ],
        "answer": "B",
        "explanation": "9 ÷ 6 = 1½. Draw 1 full symbol and 1 half symbol.",
        "solution_steps": ["9 ÷ 6 = 1.5 = 1½", "Draw 1 full symbol + 1 half symbol"],
        "hints": [
            "Divide 9 by the key (6).",
            "If the result is a decimal .5, use a half symbol."
        ],
        "feedback": {
            "correct": "Correct! 9÷6=1½ symbols.",
            "incorrect": "Divide 9 by 6. The answer is 1.5, which means 1 full and 1 half symbol."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "half_symbol_draw",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_09"],
        "math_note": "9÷6=1½ ✓ 반 심볼 사용.",
        "verification": make_verification()
    },
    {
        "id": "R1_10",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": "Frequency table: Dance 18, Drama 12, Art 6, Music 9. Key = 3. Which category will have the MOST symbols in the picture graph?",
        "data_table": {
            "title": "Favorite Club",
            "type": "frequency_table",
            "categories": ["Dance", "Drama", "Art", "Music"],
            "values": [18, 12, 6, 9],
            "scale": 1,
            "unit": "students"
        },
        "choices": [
            "A. Dance",
            "B. Drama",
            "C. Art",
            "D. Music"
        ],
        "answer": "A",
        "explanation": "Dance=18÷3=6, Drama=12÷3=4, Art=6÷3=2, Music=9÷3=3. Dance has 6 symbols — the most.",
        "solution_steps": [
            "Dance=18÷3=6, Drama=12÷3=4, Art=6÷3=2, Music=9÷3=3",
            "Compare: 6 > 4 > 3 > 2. Dance has the most."
        ],
        "hints": [
            "Divide each value by 3 to get the symbol count.",
            "Compare all four symbol counts to find the largest."
        ],
        "feedback": {
            "correct": "Right! Dance has 6 symbols, more than any other category.",
            "incorrect": "Divide each value by 3 first, then compare symbol counts."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_symbols",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_10"],
        "math_note": "Dance=6심볼 (최다). 6>4>3>2 ✓",
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
            "A picture graph shows: Math = 4 symbols, Reading = 3½ symbols, Science = 5 symbols. "
            "Each symbol = 4 students. How many students in total does the graph represent?"
        ),
        "data_table": {
            "title": "Favorite Subject",
            "type": "picture_graph",
            "categories": ["Math", "Reading", "Science"],
            "symbol_counts": [4, 3.5, 5],
            "key_value": 4,
            "unit": "students"
        },
        "choices": [
            "A. 12½",
            "B. 36",
            "C. 50",
            "D. 48"
        ],
        "answer": "C",
        "explanation": "Math=4×4=16. Reading=3½×4=14. Science=5×4=20. Total=16+14+20=50.",
        "solution_steps": [
            "Math=4×4=16, Reading=3½×4=14, Science=5×4=20",
            "16+14+20=50"
        ],
        "hints": [
            "Multiply each symbol count by 4 (the key).",
            "Add all three results to get the total."
        ],
        "feedback": {
            "correct": "Excellent! 16+14+20=50 students.",
            "incorrect": "Multiply each symbol count by the key (4), then add all totals."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "symbol_to_value",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_05"],
        "math_note": "16+14+20=50 ✓ 반 심볼: 3½×4=14.",
        "verification": make_verification()
    },
    {
        "id": "R2_06",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Frequency table: Red 14, Blue 8, Green 10, Purple 4. Key = 2. "
            "How many MORE symbols does Red have than Purple?"
        ),
        "data_table": {
            "title": "Favorite Color",
            "type": "frequency_table",
            "categories": ["Red", "Blue", "Green", "Purple"],
            "values": [14, 8, 10, 4],
            "scale": 1,
            "unit": "students"
        },
        "choices": [
            "A. 9",
            "B. 5",
            "C. 7",
            "D. 3"
        ],
        "answer": "B",
        "explanation": "Red=14÷2=7 symbols. Purple=4÷2=2 symbols. 7−2=5 more symbols for Red.",
        "solution_steps": [
            "Red=14÷2=7, Purple=4÷2=2",
            "7−2=5"
        ],
        "hints": [
            "Divide each value by 2 to find the symbol count.",
            "Subtract: Red symbols − Purple symbols."
        ],
        "feedback": {
            "correct": "Correct! Red=7 symbols, Purple=2 symbols, 7−2=5.",
            "incorrect": "First find each symbol count (÷2), then subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_symbols",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_06"],
        "math_note": "Red=7심볼, Purple=2심볼, 7-2=5 ✓",
        "verification": make_verification()
    },
    {
        "id": "R2_07",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Frequency table: Apples 15, Pears 9, Plums 6, Grapes 12. Each symbol = 3. "
            "How many TOTAL symbols will the picture graph have?"
        ),
        "data_table": {
            "title": "Fruit Basket",
            "type": "frequency_table",
            "categories": ["Apples", "Pears", "Plums", "Grapes"],
            "values": [15, 9, 6, 12],
            "scale": 1,
            "unit": "pieces"
        },
        "choices": [
            "A. 9",
            "B. 14",
            "C. 16",
            "D. 42"
        ],
        "answer": "B",
        "explanation": "Apples=15÷3=5. Pears=9÷3=3. Plums=6÷3=2. Grapes=12÷3=4. Total=5+3+2+4=14.",
        "solution_steps": [
            "Apples=15÷3=5, Pears=9÷3=3, Plums=6÷3=2, Grapes=12÷3=4",
            "5+3+2+4=14"
        ],
        "hints": [
            "Divide each value by 3 to find symbols per category.",
            "Add all four symbol counts."
        ],
        "feedback": {
            "correct": "Great! 5+3+2+4=14 total symbols.",
            "incorrect": "Divide each value by 3 first, then add all four symbol counts."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "total_symbols",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_07"],
        "math_note": "5+3+2+4=14 ✓ 오답 D(42)는 키 변환 전 합계.",
        "verification": make_verification()
    },
    {
        "id": "R2_08",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "A tally table shows Soccer: 𝍸𝍸| (2 groups of 5 plus 1 = 11 students). "
            "You are making a picture graph where each symbol = 2 students. "
            "How many symbols (including half symbols) do you draw for Soccer?"
        ),
        "data_table": {
            "title": "Favorite Sport (Tally)",
            "type": "tally_table",
            "categories": ["Soccer"],
            "tally_counts": [11],
            "unit": "students"
        },
        "choices": [
            "A. 4½",
            "B. 5",
            "C. 5½",
            "D. 11"
        ],
        "answer": "C",
        "explanation": "Soccer tally: 𝍸𝍸| = 5+5+1 = 11. Picture graph: 11÷2 = 5½ symbols.",
        "solution_steps": [
            "Read tally: 𝍸𝍸| = 5+5+1 = 11",
            "11 ÷ 2 = 5½ symbols"
        ],
        "hints": [
            "Count the tally marks first: each 𝍸 = 5, each | = 1.",
            "Then divide the total by the key (2)."
        ],
        "feedback": {
            "correct": "Correct! 11÷2=5½ symbols.",
            "incorrect": "First read the tally (11 students), then divide by 2 to find symbols."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "half_symbol_draw",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_08"],
        "math_note": "탈리 𝍸𝍸|=11, 11÷2=5½ ✓ (U1 탈리 읽기 연계)",
        "verification": make_verification()
    },
    {
        "id": "R2_09",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Tally table: Red = 𝍸𝍸𝍸 (15 students), Blue = 𝍸𝍸 (10 students). "
            "You make a picture graph with key = 5. "
            "How many MORE symbols does Red have than Blue?"
        ),
        "data_table": {
            "title": "Favorite Color (Tally)",
            "type": "tally_table",
            "categories": ["Red", "Blue"],
            "tally_counts": [15, 10],
            "unit": "students"
        },
        "choices": [
            "A. 1",
            "B. 2",
            "C. 3",
            "D. 5"
        ],
        "answer": "A",
        "explanation": "Red=𝍸𝍸𝍸=15. Blue=𝍸𝍸=10. Red symbols=15÷5=3. Blue symbols=10÷5=2. 3−2=1.",
        "solution_steps": [
            "Red=𝍸𝍸𝍸=15 → 15÷5=3 symbols",
            "Blue=𝍸𝍸=10 → 10÷5=2 symbols",
            "3−2=1"
        ],
        "hints": [
            "Count each tally: 𝍸 = 5. Then divide by key (5).",
            "Subtract: Red symbols − Blue symbols."
        ],
        "feedback": {
            "correct": "Correct! Red=3 symbols, Blue=2 symbols, 3−2=1.",
            "incorrect": "Convert tallies to counts (Red=15, Blue=10), then to symbols (÷5), then subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_symbols",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_09"],
        "math_note": "Red=3심볼, Blue=2심볼, 3-2=1 ✓ (U1 탈리 읽기 연계)",
        "verification": make_verification()
    },
    {
        "id": "R2_10",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Tally data: Monday = 𝍸𝍸 (10), Tuesday = 𝍸𝍸𝍸 (15), Wednesday = 𝍸 (5). "
            "Each symbol = 5 in the picture graph. "
            "What is the total number of symbols in the picture graph?"
        ),
        "data_table": {
            "title": "Library Visits (Tally)",
            "type": "tally_table",
            "categories": ["Monday", "Tuesday", "Wednesday"],
            "tally_counts": [10, 15, 5],
            "unit": "students"
        },
        "choices": [
            "A. 6",
            "B. 7",
            "C. 30",
            "D. 5"
        ],
        "answer": "A",
        "explanation": "Monday=10÷5=2. Tuesday=15÷5=3. Wednesday=5÷5=1. Total=2+3+1=6.",
        "solution_steps": [
            "Monday=𝍸𝍸=10 → 10÷5=2",
            "Tuesday=𝍸𝍸𝍸=15 → 15÷5=3",
            "Wednesday=𝍸=5 → 5÷5=1",
            "2+3+1=6"
        ],
        "hints": [
            "Read each tally and convert to a count.",
            "Divide each count by 5, then add."
        ],
        "feedback": {
            "correct": "Perfect! 2+3+1=6 total symbols.",
            "incorrect": "Read tallies, divide each by 5, then add all symbol counts."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "total_symbols",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_10"],
        "math_note": "2+3+1=6 ✓ 오답 C(30)는 키 변환 전 합계. (U1 탈리 읽기 연계)",
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
            "A picture graph shows Drama club = 4 symbols. Each symbol = 6 students. "
            "After 12 more students join Drama club, how many symbols will Drama have?"
        ),
        "choices": [
            "A. 4",
            "B. 5",
            "C. 6",
            "D. 7"
        ],
        "answer": "C",
        "explanation": "Drama original: 4×6=24 students. Add 12: 24+12=36. New symbols: 36÷6=6.",
        "solution_steps": [
            "Drama original: 4×6=24 students",
            "Add 12 more: 24+12=36 students",
            "New symbols: 36÷6=6"
        ],
        "hints": [
            "First find the original number of students (symbols × key).",
            "Add 12, then divide by the key again."
        ],
        "feedback": {
            "correct": "Excellent! 24+12=36, 36÷6=6 symbols.",
            "incorrect": "Step 1: 4×6=24 students. Step 2: 24+12=36. Step 3: 36÷6=6."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "graph_update",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R3_04"],
        "math_note": "4×6=24, +12=36, 36÷6=6 ✓ 3단계 문제.",
        "verification": make_verification()
    },
    {
        "id": "R3_05",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Frequency table: Spring 12, Summer 18, Fall 6, Winter 9. "
            "Which key results in ALL categories using only WHOLE number symbols (no half symbols)?"
        ),
        "data_table": {
            "title": "Favorite Season",
            "type": "frequency_table",
            "categories": ["Spring", "Summer", "Fall", "Winter"],
            "values": [12, 18, 6, 9],
            "scale": 1,
            "unit": "students"
        },
        "choices": [
            "A. Each symbol = 2",
            "B. Each symbol = 3",
            "C. Each symbol = 4",
            "D. Each symbol = 6"
        ],
        "answer": "B",
        "explanation": (
            "key=3: Spring=12÷3=4 ✓, Summer=18÷3=6 ✓, Fall=6÷3=2 ✓, Winter=9÷3=3 ✓ — all whole. "
            "key=2: Winter=9÷2=4½ ✗. key=4: Summer=18÷4=4.5 ✗. key=6: Winter=9÷6=1.5 ✗."
        ),
        "solution_steps": [
            "Test key=3: 4, 6, 2, 3 — all whole numbers ✓",
            "key=2: Winter=9÷2=4½ ✗. key=4: Summer=18÷4=4.5 ✗. key=6: Winter=9÷6=1.5 ✗"
        ],
        "hints": [
            "Divide every value (12, 18, 6, 9) by each key. All four results must be whole numbers.",
            "Try key=3 first."
        ],
        "feedback": {
            "correct": "Correct! key=3 divides evenly into 12, 18, 6, and 9.",
            "incorrect": "Test each key with all four values. key=3 gives 4, 6, 2, 3 — all whole numbers."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "choose_key",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R3_05"],
        "math_note": "key=3: 4,6,2,3 모두 정수 ✓. 다른 키는 Winter 또는 Summer에서 소수 발생.",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 메인 업그레이드 함수
# ─────────────────────────────────────────
def upgrade():
    # 원본 JSON 로드
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)

    # 이미 업그레이드된 파일인지 확인 (top-level 섹션 키 존재 여부로 판단)
    if "pretest" in d:
        print("⚠️  이미 업그레이드된 파일입니다. 원본 복원 후 다시 실행하세요.")
        return

    # 평탄 items 배열 추출
    raw_items: list[dict] = d.pop("items", [])

    # 섹션별로 분류
    pt_items, learn_items, try_items, r1_items, r2_items, r3_items = [], [], [], [], [], []
    for item in raw_items:
        sec = item.get("section", "")
        iid = item.get("id", "")

        # LN_XX → LEARN_XX 변경
        if iid.startswith("LN_"):
            new_id = "LEARN_" + iid[3:]
            item["id"] = new_id

        if sec == "pretest":
            pt_items.append(item)
        elif sec == "learn":
            learn_items.append(item)
        elif sec == "try":
            try_items.append(item)
        elif sec == "practice_r1":
            r1_items.append(item)
        elif sec == "practice_r2":
            r2_items.append(item)
        elif sec == "practice_r3":
            r3_items.append(item)

    # 기존 문항에 공통 필드 적용
    for lst in [pt_items, learn_items, try_items, r1_items, r2_items, r3_items]:
        for item in lst:
            add_item_fields(item)

    # 신규 카드 처리 (add_item_fields 적용 후 섹션에 추가)
    for card in NEW_LEARN_CARDS:
        add_item_fields(card)
    learn_items.extend(NEW_LEARN_CARDS)

    for card in NEW_TRY_CARDS:
        add_item_fields(card)
    try_items.extend(NEW_TRY_CARDS)

    for card in NEW_R1_CARDS:
        add_item_fields(card)
    r1_items.extend(NEW_R1_CARDS)

    for card in NEW_R2_CARDS:
        add_item_fields(card)
    r2_items.extend(NEW_R2_CARDS)

    for card in NEW_R3_CARDS:
        add_item_fields(card)
    r3_items.extend(NEW_R3_CARDS)

    # R2 마지막 25% → review_from = "U1" (인터리빙)
    r2_tail_start = len(r2_items) * 3 // 4
    for item in r2_items[r2_tail_start:]:
        item["review_from"] = "U1"

    # 레슨 레벨 필드 추가
    d["tier"] = "A"
    d["review_from_units"] = ["U1"]
    d["vertical_alignment"] = {
        "prerequisite": "G2 — Organize data in up to 4 categories; use tally marks",
        "current": "G3 — Make scaled picture graphs (value ÷ key = symbols; half symbols)",
        "successor": "G4 — Multi-step problems using data in various representations"
    }
    d["unit_intro_message"] = (
        "이번 단원에서는 빈도표 데이터를 이용해 그림 그래프를 직접 만드는 방법을 배웁니다. "
        "키를 선택하고, 각 값을 키로 나누어 심볼 수를 구하며, 반 심볼 사용법도 익힙니다."
    )
    d["unit_close_message"] = (
        "잘 했어요! 이제 빈도표에서 그림 그래프를 만들 수 있습니다. "
        "다음 레슨에서는 막대 그래프 읽기를 학습합니다."
    )

    # 섹션을 최상위 키로 저장 (감사 스크립트가 lesson.get("pretest") 형태로 읽음)
    d["pretest"]     = pt_items
    d["learn"]       = learn_items
    d["try"]         = try_items
    d["practice_r1"] = r1_items
    d["practice_r2"] = r2_items
    d["practice_r3"] = r3_items

    # 메타데이터 갱신
    sections_map = {
        "pretest": pt_items, "learn": learn_items, "try": try_items,
        "practice_r1": r1_items, "practice_r2": r2_items, "practice_r3": r3_items
    }
    total = sum(len(v) for v in sections_map.values())
    d["metadata"] = d.get("metadata", {})
    d["metadata"].update({
        "upgraded": True,
        "upgrade_version": "7-stage-v1",
        "total_items": total,
        "section_counts": {k: len(v) for k, v in sections_map.items()},
        "ccss": ["3.MD.B.3"],
        "misconception_pool": "3.MD.B.3",
        "stage7_pending": True
    })

    # 저장
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    counts = d["metadata"]["section_counts"]
    print(f"✅ 업그레이드 완료: L3_make_picture_graphs.json")
    print(f"   PT={counts['pretest']}  LEARN={counts['learn']}  TRY={counts['try']}")
    print(f"   R1={counts['practice_r1']}  R2={counts['practice_r2']}  R3={counts['practice_r3']}")
    print(f"   총 문항 수: {total}")


if __name__ == "__main__":
    upgrade()
