#!/usr/bin/env python3
"""
G3 U2 L4 — Use Bar Graphs
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
SRC  = REPO / "backend/data/math/G3/U2_represent_interpret_data/L4_use_bar_graphs.json"
DST  = SRC   # 원본 파일을 직접 업그레이드

# ─────────────────────────────────────────
# 오개념 ID 상수 (3.MD.B.3)
# ─────────────────────────────────────────
M01 = "3.MD.B.3.M01"   # tally_miscount (탈리 오독)
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
            "name": "Go Math Grade 3 Chapter 2 Lesson 2.4 — Use Bar Graphs",
            "url": "https://www.hmhco.com/programs/go-math",
            "description": "막대 그래프 읽기: 스케일 읽기, 바 끝점 값 읽기, 비교(더 많은/적은), 최대/최소 식별"
        },
        "procedure_source": {
            "name": "EngageNY Grade 3 Module 6 Lesson 3 — Use Bar Graphs",
            "url": "https://www.engageny.org/resource/grade-3-mathematics-module-6",
            "description": "막대 그래프 읽기 절차: 스케일 확인 → 바 끝점 읽기 → 비교 연산"
        },
        "assessment_source": {
            "name": "Smarter Balanced Grade 3 Sample Items — 3.MD.B.3",
            "url": "https://sampleitems.smarterbalanced.org/",
            "description": "3.MD.B.3 평가 지침 — 막대 그래프 해석 및 비교 문제"
        }
    }


# ─────────────────────────────────────────
# 오개념 항목별 매핑 (item_id → expected_errors 리스트)
# ─────────────────────────────────────────
ERRORS_MAP: dict[str, list[dict]] = {
    # ── Pretest ──
    "PT_01": [
        # 스케일 0,2,4,6,8. 바가 6에서 끝남 → 6. 오답 A(3): 6÷2=3으로 나눔
        {"error_type": "misconception", "misconception_id": M02,
         "description": "스케일 값(6)을 그대로 읽지 않고 6÷2=3으로 계산",
         "citation": "Friel et al. (2001) p.130 — 스케일 오독"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "6 대신 다음 눈금인 8을 읽음"},
    ],
    "PT_02": [
        # 가장 높은 바 = Homework(7). 오답 C(Games=5): 목록 두 번째 선택
        {"error_type": "misconception", "misconception_id": M06,
         "description": "Homework(7) 대신 Games(5) 선택 — 체계적으로 모든 바를 비교하지 않음",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Reading(4) 선택 — 인접한 행 오독 (M02)"},
    ],
    "PT_03": [
        # Games(5) + Reading(4) = 9. 오답 D(12): Homework(7)+Games(5)=12 (잘못된 카테고리)
        {"error_type": "misconception", "misconception_id": M04,
         "description": "모든 카테고리 합산 시도: 7+5+4+3=19보다 Homework+Games=12 제출",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Homework(7)만 읽거나 Games만 읽고 7 제출 — 두 카테고리 합산 누락"},
    ],
    "PT_04": [
        # Tuna = 18. 오답 A(12): Turkey 행 오독
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Tuna 대신 Turkey(12) 행 읽음 — 행 추적 오류",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Ham(16) 행 읽음 — Tuna와 인접한 행 오독 (M02)"},
    ],
    "PT_05": [
        # Homework(7) - Reading(4) = 3. 오답 C(4): Reading 값 그대로 제출
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 적은'을 빼기가 아닌 Reading 값(4) 그대로 답으로 제출",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Games(5)-Reading(4)=1이 아닌 2 제출 — 잘못된 카테고리 비교"},
    ],
    # ── TRY ──
    "TRY_01": [
        # 바가 15에서 끝남 → 15. 오답 A(3): 15÷5=3으로 나눔 (스케일 간격으로 나눔)
        {"error_type": "misconception", "misconception_id": M02,
         "description": "바 끝점 값(15)을 읽지 않고 스케일 간격(5)으로 나눠 15÷5=3 제출",
         "citation": "Friel et al. (2001) p.130 — 스케일 오독"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "다음 눈금인 20 읽음"},
    ],
    "TRY_02": [
        # 가장 짧은 바 = Green(6). 오답 A(Red=8): 두 번째로 작음
        {"error_type": "misconception", "misconception_id": M06,
         "description": "Green(6) 대신 Red(8) 선택 — 체계적 스캔 없이 첫 번째 카테고리 선택",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Blue(12) 선택 — 가장 큰 값(긴 바)을 가장 짧은 바로 혼동"},
    ],
    "TRY_03": [
        # 7+5+4+3=19. 오답 C(17): 한 카테고리 누락
        {"error_type": "misconception", "misconception_id": M04,
         "description": "TV(3) 누락: 7+5+4=16이 아닌 7+5+5=17 계산 오류",
         "citation": "Friel et al. (2001) p.131 — 카테고리 합산 누락"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "7+5+3=15 계산 — Reading(4) 누락"},
    ],
    "TRY_04": [
        # 스케일 by 2. Grapes 바가 8과 10 중간 → 9. 오답 A(8): 아래 눈금 읽음
        {"error_type": "misconception", "misconception_id": M02,
         "description": "중간값(9) 읽지 않고 아래 눈금(8) 제출 — 중간 스케일 오독",
         "citation": "Friel et al. (2001) p.130 — 막대 끝점 오독"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "위 눈금(10) 읽음 — 중간값을 위쪽으로 올림"},
    ],
    "TRY_05": [
        # Walk(5)+Bus(8)+Car(3)+Bike(4)=20. NOT Bus=20-8=12. 오답 D(20): 중간 결과에서 멈춤
        {"error_type": "misconception", "misconception_id": M05,
         "description": "총합(20)만 구하고 Bus(8) 빼기 단계 누락 — 중간 결과 제출",
         "citation": "EngageNY G3 M6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Bus 값(8) 그대로 제출 — 'NOT Bus' 의미 미파악"},
    ],
    # ── R1 ──
    "R1_01": [
        # Oranges = 6. 오답 C(8): Bananas 행 오독
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Oranges 대신 Bananas(8) 행 읽음 — 인접 행 추적 오류",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Apples(10) 행 읽음 — 가장 큰 값 선택"},
    ],
    "R1_02": [
        # 가장 인기 = Dogs(14). 오답 C(Cats=10): 두 번째 높은 값
        {"error_type": "misconception", "misconception_id": M06,
         "description": "Dogs(14) 대신 Cats(10) 선택 — 목록 두 번째 항목 선택 (체계적 스캔 부재)",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Birds(4) 선택 — 가장 작은 값과 가장 큰 값 혼동"},
    ],
    "R1_03": [
        # 스케일 by 5. 10과 15 중간 = 12½. 오답 B(12): 반올림 내림
        {"error_type": "misconception", "misconception_id": M02,
         "description": "중간값 12½을 정수 12로 내림 — 막대 끝점의 반값 인식 부재",
         "citation": "Friel et al. (2001) p.130 — 스케일 중간값 오독"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "13 제출 — 중간값을 반올림"},
    ],
    "R1_04": [
        # Pizza(11) - Chicken(4) = 7. 오답 C(9): Grilled Cheese(2) 대신 빼기
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Chicken(4) 대신 Grilled Cheese(2) 사용: 11-2=9 제출 — 잘못된 카테고리 비교",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Pizza 값(11) 그대로 제출 — 차이를 구하지 않음 (M05)"},
    ],
    "R1_05": [
        # Total=24, NOT Pizza = 24-11=13. 오답 D(24): 총합에서 멈춤
        {"error_type": "misconception", "misconception_id": M05,
         "description": "총합(24) 구한 후 Pizza(11) 빼기 단계 누락 — 중간 결과(24) 제출",
         "citation": "EngageNY G3 Module 6 Lesson 2 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Pizza 값(11) 그대로 제출 — 'NOT Pizza' 의미 미파악"},
    ],
    "R1_06": [
        # Reading=4, +3 → 7. 오답 A(4): 원래 Reading 값 그대로 제출
        {"error_type": "misconception", "misconception_id": M05,
         "description": "Reading 원래 값(4) 그대로 제출 — 3명 추가 반영 누락",
         "citation": "EngageNY G3 Module 6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Homework(7)+3=10 제출 — Reading 대신 Homework 행에 적용 (M02)"},
    ],
    "R1_07": [
        # Reading(4) - TV(3) = 1. 오답 C(3): TV 값 그대로 제출
        {"error_type": "misconception", "misconception_id": M05,
         "description": "TV 값(3) 그대로 제출 — '더 많은' 비교에서 빼기 미수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "2 제출 — 잘못된 빼기 (4-2=2 또는 3-1=2)"},
    ],
    "R1_08": [
        # 스케일 by 2. Soccer 바가 4와 6 중간 → 5. 오답 A(4): 아래 눈금 읽음
        {"error_type": "misconception", "misconception_id": M02,
         "description": "중간값(5) 읽지 않고 아래 눈금(4) 제출",
         "citation": "Friel et al. (2001) p.130 — 스케일 중간값 오독"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "위 눈금(6) 읽음 — 중간값을 올림"},
    ],
    "R1_09": [
        # Chocolate(12) - Vanilla(5) = 7. 오답 D(17): 더하기 수행
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 적은' 질문에 12+5=17 덧셈 수행 — 비교 언어 오해",
         "citation": "NCTM MD Progressions K-5 (2011) p.9 — 비교 언어 오오해"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Chocolate 값(12) 그대로 제출 — 차이 계산 누락 (M05)"},
    ],
    "R1_10": [
        # NOT most popular(Drawing=12) = Reading(8)+Dancing(6)+Cooking(10)=24. 오답 A(12): 최다에서 멈춤
        {"error_type": "misconception", "misconception_id": M05,
         "description": "가장 인기 있는 Drawing(12)만 구하고 나머지 합산 단계 누락 — 12 제출",
         "citation": "EngageNY G3 Module 6 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "모든 카테고리 합산 8+12+6+10=36 (Drawing 포함) — M04"},
    ],
    # ── R2 ──
    "R2_01": [
        # Cheese(10) + Veggie(8) = 18. 오답 B(14): 잘못된 카테고리 조합
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Cheese+Veggie 대신 Pepperoni+Veggie=6+8=14 제출 — 잘못된 행 읽기",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Cheese+Mushroom=10+4=14가 아닌 다른 쌍 계산 오류"},
    ],
    "R2_02": [
        # Bus(12) - Walk(10) = 2. 오답 B(4): 잘못된 카테고리 비교
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Walk(10) 대신 Car(6) 사용: 12-6=6? 아니면 Walk-Bike=10-4=6 제출",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "'더 많은' 질문에 12+10=22가 아닌 8을 제출 — 계산 오류"},
    ],
    "R2_03": [
        # Car+Bus=18 > Walk+Bike=14 by 4. 오답 B(Less by 4): 방향 반전
        {"error_type": "misconception", "misconception_id": M07,
         "description": "Car+Bus=18, Walk+Bike=14임에도 방향 반전 — '더 큰' 그룹을 잘못 식별",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Equal 선택 — 합산 계산 오류 (18≠14)"},
    ],
    "R2_04": [
        # Food Drive(14) - Bench Repair(4) = 10. 오답 B(8): 잘못된 카테고리
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Bench Repair(4) 대신 Playground(6) 사용: 14-6=8 제출 — 잘못된 행",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Food Drive 값(14) 그대로 제출 — 차이 계산 누락 (M05)"},
    ],
    "R2_05": [
        # Cats(9)+Dogs(15)+Fish(6)+Rabbits(12)=42. 오답 D(27): 일부 카테고리 누락
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Cats+Dogs+Fish만 합산: 9+15+6=30 또는 일부 누락 — Rabbits 포함 안 함",
         "citation": "Friel et al. (2001) p.131 — 카테고리 누락"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Rabbits 값(12)만 제출 — 최댓값 선택"},
    ],
    "R2_06": [
        # Red(16) - Yellow(4) = 12. 오답 C(20): 덧셈 수행
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 많은' 질문에 16+4=20 덧셈 수행 — 비교 언어 오해",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "잘못된 카테고리 비교: Blue-Green=10-8=2 또는 다른 쌍 계산"},
    ],
    "R2_07": [
        # Morning(20) + Afternoon(14) = 34. 오답 C(48): 모든 카테고리 합산
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Morning+Afternoon만 구하는 것이 아닌 4개 전체 합산: 20+14+8+6=48",
         "citation": "Friel et al. (2001) p.131 — 불필요한 카테고리 포함"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Morning(20)만 제출 — Afternoon 합산 누락 (M04)"},
    ],
    "R2_08": [
        # 탈리 Cloudy=𝍸𝍸=10. 막대 그래프 값=10. 오답 C(15): Sunny 행 오독
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Cloudy 대신 Sunny(𝍸𝍸𝍸=15) 행 읽음 — 탈리 표에서 잘못된 행 추적",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "탈리 그룹 수(2)만 세어 2 제출 — 각 그룹=5 무시 (M01)"},
    ],
    "R2_09": [
        # Pizza(16) - Burger(10) = 6. 오답 C(26): 덧셈 수행
        {"error_type": "misconception", "misconception_id": M03,
         "description": "비교 질문에 Pizza+Burger=16+10=26 덧셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Pizza 값(16) 그대로 제출 — 차이 계산 누락 (M05)"},
    ],
    "R2_10": [
        # Cats(11)+Dogs(15)+Fish(5)=31. 오답 B(26): Fish 누락
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Fish(𝍸=5) 누락: Cats(11)+Dogs(15)=26만 합산 — 세 번째 카테고리 포함 안 함",
         "citation": "Friel et al. (2001) p.131 — 카테고리 누락"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Dogs 값(15) 그대로 제출 — 최대 탈리 수 카테고리 선택"},
    ],
    # ── R3 ──
    "R3_01": [
        # Wed=6, 두 배=12=Tuesday. 오답 C(Thursday=10): 잘못된 계산
        {"error_type": "misconception", "misconception_id": M07,
         "description": "6×2=12를 찾지 않고 6+6=12 계산 후 목록에서 12 아닌 Thursday(10) 선택",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Monday(8) 선택 — 6+2=8으로 '두 배' 대신 '2 더하기' 해석"},
    ],
    "R3_02": [
        # Mushroom=4, +3 → 7. 오답 D(8): 하나 더 추가
        {"error_type": "misconception", "misconception_id": M07,
         "description": "4+3=7이 아닌 4+4=8 계산 — 추가 수를 잘못 읽음",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "4+2=6 계산 — 3 대신 2를 더함"},
    ],
    "R3_03": [
        # Total=90, 100-90=10. 오답 A(5): 부분 합산 오류
        {"error_type": "misconception", "misconception_id": M07,
         "description": "총합 계산: 25+15+30+20=90이 아닌 잘못된 합산 후 100-95=5 제출",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "일부 카테고리만 합산: 25+15+30=70, 100-70=30? 아니면 세 카테고리 포함 오류"},
    ],
    "R3_04": [
        # Music(14)-6 → Art=8+6=14. 오답 A(8): 원래 Art 값 그대로 제출
        {"error_type": "misconception", "misconception_id": M07,
         "description": "Art 원래 값(8) 그대로 제출 — 6명 전환 반영 누락",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Music(14)+Art(8)=22 제출 — 두 카테고리를 더함"},
    ],
    "R3_05": [
        # Spring(15)+Winter(20)=35, Summer(25)+Fall(10)=35. Equal. 오답 B(Spring+Winter 더 큼): 계산 오류
        {"error_type": "misconception", "misconception_id": M07,
         "description": "Spring+Winter=35, Summer+Fall=35 같음을 계산하지 않고 Spring값(25) 보고 Summer그룹 더 크다고 오판",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Summer+Fall=25+10=35 오계산 — Summer 값이 크다고 그룹 합도 더 크다고 가정"},
    ],
}


# ─────────────────────────────────────────
# 기본 skill_tag 매핑 (item_id → tag)
# ─────────────────────────────────────────
SKILL_TAGS: dict[str, str] = {
    "PT_01": "scale_reading",
    "PT_02": "identify_most_least",
    "PT_03": "total_bar_values",
    "PT_04": "read_bar_value",
    "PT_05": "compare_bars",
    "TRY_01": "scale_reading",
    "TRY_02": "identify_most_least",
    "TRY_03": "total_bar_values",
    "TRY_04": "scale_reading",
    "TRY_05": "two_step_bar",
    "R1_01": "read_bar_value",
    "R1_02": "identify_most_least",
    "R1_03": "scale_reading",
    "R1_04": "compare_bars",
    "R1_05": "two_step_bar",
    "R1_06": "two_step_bar",
    "R1_07": "compare_bars",
    "R1_08": "scale_reading",
    "R1_09": "compare_bars",
    "R1_10": "two_step_bar",
    "R2_01": "total_bar_values",
    "R2_02": "compare_bars",
    "R2_03": "two_step_bar",
    "R2_04": "compare_bars",
    "R2_05": "total_bar_values",
    "R2_06": "compare_bars",
    "R2_07": "total_bar_values",
    "R2_08": "read_bar_value",
    "R2_09": "compare_bars",
    "R2_10": "total_bar_values",
    "R3_01": "two_step_bar",
    "R3_02": "two_step_bar",
    "R3_03": "two_step_bar",
    "R3_04": "two_step_bar",
    "R3_05": "two_step_bar",
}

# CPA 단계 (문항별)
CPA_MAP: dict[str, str] = {
    "PT_01": "concrete",
    "PT_02": "pictorial",
    "PT_03": "pictorial",
    "PT_04": "pictorial",
    "PT_05": "abstract",
    "TRY_01": "concrete",
    "TRY_02": "pictorial",
    "TRY_03": "abstract",
    "TRY_04": "pictorial",
    "TRY_05": "abstract",
    "R1_01": "pictorial",
    "R1_02": "pictorial",
    "R1_03": "concrete",
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
        item["skill_tag"] = SKILL_TAGS.get(iid, "read_bar_value")

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
        "title": "Guided Example — Reading a Bar Graph",
        "content": (
            "Bar graph: Cats 8, Dogs 12, Fish 4, Birds 6. "
            "Step 1: Find the category the question asks about. → Fish "
            "Step 2: Look at where the Fish bar ends. → It ends at 4. "
            "Step 3: Read the scale. → Each gridline = 2. The bar ends on the gridline marked 4. "
            "Answer: 4 students chose Fish. "
            "Tip: Place your finger on the bar and slide it straight to the scale axis."
        ),
        "visual_type": "bar_graph",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "Fish 바가 4에서 끝남 → 4명. 스케일 by 2: 0,2,4,6,8,10,12.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "Reading Values Between Gridlines",
        "content": (
            "When a bar ends exactly halfway between two gridlines, the value is the average of those two gridlines. "
            "Example: Scale counts by 2s (0, 2, 4, 6, 8, 10). A bar ends halfway between 8 and 10. "
            "Halfway = (8 + 10) ÷ 2 = 9. "
            "So the bar shows 9. "
            "Rule: Halfway between two scale marks = smaller + (scale interval ÷ 2)."
        ),
        "visual_type": "bar_graph",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "중간값: (8+10)÷2=9. 스케일 간격=2, 중간=1. 8+1=9.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "Comparing Bars — How Many More or Fewer?",
        "content": (
            "To find 'how many more' or 'how many fewer': SUBTRACT the two bar values. "
            "Example: Soccer 14, Basketball 8. "
            "'How many more chose Soccer than Basketball?' → 14 − 8 = 6. "
            "Key: 'More than' or 'fewer than' → SUBTRACT (never add). "
            "Step 1: Read the value of each bar. "
            "Step 2: Subtract smaller from larger. "
            "Step 3: Check: does your answer make sense?"
        ),
        "visual_type": "bar_graph",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "비교: Soccer(14) - Basketball(8) = 6. '더 많은/적은' → 빼기.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_07",
        "type": "explain",
        "title": "Math Talk: Two-Step Bar Graph Problems",
        "content": (
            "Bar graph: Mon 8, Tue 6, Wed 10, Thu 4. Total = 8+6+10+4 = 28. "
            "Problem: 'How many students did NOT choose Monday?' "
            "Wrong approach: Answer = 28 (stopping at the total). "
            "Correct approach: Step 1 → find total = 28. Step 2 → subtract Monday: 28 − 8 = 20. "
            "Always re-read the question after Step 1 to confirm whether one more step is needed."
        ),
        "visual_type": "bar_graph",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_talk_prompt": (
            "Mon(8), Tue(6), Wed(10), Thu(4) 막대 그래프에서 "
            "'Monday를 선택하지 않은 학생 수'를 구할 때 "
            "왜 총합(28)만 구하면 안 될까요? "
            "두 번째 단계(빼기)가 왜 필요한지 설명해보세요. "
            "어떤 문제는 총합이 답이고 어떤 문제는 총합에서 한 카테고리를 빼야 할까요?"
        ),
        "math_note": "2단계: ①총합=28, ②NOT Monday=28-8=20. 문제 재읽기 필수.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_08",
        "type": "summary",
        "title": "Lesson Summary: Use Bar Graphs",
        "content": (
            "In this lesson you learned how to: "
            "① Read bar values: find where the bar ends on the scale axis. "
            "② Read between gridlines: halfway between two marks = smaller + (interval ÷ 2). "
            "③ Find most/least: the tallest bar = most; shortest bar = least. "
            "④ Compare bars: 'how many more/fewer' → SUBTRACT the two values. "
            "⑤ Solve two-step problems: Step 1 find the needed value(s), Step 2 apply the final operation."
        ),
        "lesson_summary": (
            "막대 그래프 마스터: "
            "①바 끝점 = 값 ②중간값 = 작은 눈금 + 간격÷2 "
            "③최다=가장 높은 바, 최소=가장 낮은 바 "
            "④비교='더 많은/적은'→빼기 "
            "⑤2단계 문제: 1단계 값 구하기 → 문제 재읽기 → 2단계 연산"
        ),
        "visual_type": "none",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "핵심: 바 끝점 읽기 + 중간값 + 비교(빼기) + 2단계 문제.",
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
            "A bar graph has a scale counting by 2s: 0, 2, 4, 6, 8, 10. "
            "The bar for 'Grapes' ends exactly halfway between 8 and 10. "
            "How many students chose Grapes?"
        ),
        "data_table": {
            "title": "Favorite Fruit",
            "type": "bar_graph",
            "categories": ["Grapes"],
            "values": [9],
            "scale": 2,
            "unit": "students",
            "axis_label": {"x": "Fruit", "y": "Number of Students"}
        },
        "choices": [
            "A. 8",
            "B. 8½",
            "C. 9",
            "D. 10"
        ],
        "answer": "C",
        "explanation": "The bar is halfway between 8 and 10. Halfway = (8+10)÷2 = 9.",
        "solution_steps": [
            "Identify the two gridlines the bar is between: 8 and 10.",
            "Find halfway: (8+10)÷2 = 9."
        ],
        "hints": [
            "Look at the two gridlines the bar is between.",
            "Halfway between two numbers = add them and divide by 2."
        ],
        "feedback": {
            "correct": "Correct! Halfway between 8 and 10 is 9.",
            "incorrect": "The bar is halfway between 8 and 10. (8+10)÷2=9."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "scale_reading",
        "cpa_stage": "pictorial",
        "expected_errors": ERRORS_MAP["TRY_04"],
        "math_note": "(8+10)÷2=9 ✓. 오답 A(8): 아래 눈금, D(10): 위 눈금.",
        "verification": make_verification()
    },
    {
        "id": "TRY_05",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Bar graph: Walk 5, Bus 8, Car 3, Bike 4. "
            "How many students did NOT come to school by Bus?"
        ),
        "data_table": {
            "title": "How Students Get to School",
            "type": "bar_graph",
            "categories": ["Walk", "Bus", "Car", "Bike"],
            "values": [5, 8, 3, 4],
            "scale": 1,
            "unit": "students",
            "axis_label": {"x": "Way", "y": "Number of Students"}
        },
        "choices": [
            "A. 8",
            "B. 11",
            "C. 12",
            "D. 20"
        ],
        "answer": "C",
        "explanation": "Total = 5+8+3+4 = 20. NOT Bus = 20−8 = 12.",
        "solution_steps": [
            "Step 1: Find total = 5+8+3+4 = 20.",
            "Step 2: NOT Bus = Total − Bus = 20−8 = 12."
        ],
        "hints": [
            "First add all bar values to find the total.",
            "Then subtract the Bus value from the total."
        ],
        "feedback": {
            "correct": "Excellent! Total=20, NOT Bus=20−8=12.",
            "incorrect": "Step 1: add all values (5+8+3+4=20). Step 2: subtract Bus (20−8=12)."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "two_step_bar",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["TRY_05"],
        "math_note": "총합=20, NOT Bus=20-8=12 ✓. 오답 D(20): 총합에서 멈춤.",
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
            "A bar graph has a scale counting by 2s: 0, 2, 4, 6, 8. "
            "The bar for 'Soccer' ends halfway between 4 and 6. "
            "How many students chose Soccer?"
        ),
        "choices": [
            "A. 4",
            "B. 5",
            "C. 6",
            "D. 7"
        ],
        "answer": "B",
        "explanation": "Halfway between 4 and 6 = (4+6)÷2 = 5.",
        "solution_steps": [
            "The bar is between 4 and 6.",
            "(4+6)÷2 = 5."
        ],
        "hints": [
            "Identify the two gridlines the bar is between: 4 and 6.",
            "Halfway = (4+6)÷2."
        ],
        "feedback": {
            "correct": "Correct! (4+6)÷2=5.",
            "incorrect": "The bar is halfway between 4 and 6. Add them and divide by 2: (4+6)÷2=5."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "scale_reading",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_08"],
        "math_note": "(4+6)÷2=5 ✓ 중간값. 오답 A(4): 아래 눈금, C(6): 위 눈금.",
        "verification": make_verification()
    },
    {
        "id": "R1_09",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Bar graph: Strawberry 9, Vanilla 5, Chocolate 12, Mint 6. "
            "How many fewer students chose Vanilla than Chocolate?"
        ),
        "data_table": {
            "title": "Favorite Ice Cream Flavor",
            "type": "bar_graph",
            "categories": ["Strawberry", "Vanilla", "Chocolate", "Mint"],
            "values": [9, 5, 12, 6],
            "scale": 1,
            "unit": "students",
            "axis_label": {"x": "Flavor", "y": "Students"}
        },
        "choices": [
            "A. 5",
            "B. 7",
            "C. 12",
            "D. 17"
        ],
        "answer": "B",
        "explanation": "Chocolate=12, Vanilla=5. 12−5=7 fewer.",
        "solution_steps": [
            "Chocolate=12, Vanilla=5.",
            "12−5=7."
        ],
        "hints": [
            "Find the value for Vanilla and Chocolate.",
            "Subtract: larger − smaller."
        ],
        "feedback": {
            "correct": "Correct! 12−5=7.",
            "incorrect": "'Fewer than' means subtract. Chocolate(12)−Vanilla(5)=7."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_bars",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_09"],
        "math_note": "Chocolate(12) - Vanilla(5) = 7 ✓. 오답 D(17): 12+5=17 덧셈 오류.",
        "verification": make_verification()
    },
    {
        "id": "R1_10",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Bar graph: Reading 8, Drawing 12, Dancing 6, Cooking 10. "
            "How many students did NOT choose the most popular activity?"
        ),
        "data_table": {
            "title": "Favorite After-School Activity",
            "type": "bar_graph",
            "categories": ["Reading", "Drawing", "Dancing", "Cooking"],
            "values": [8, 12, 6, 10],
            "scale": 2,
            "unit": "students",
            "axis_label": {"x": "Activity", "y": "Students"}
        },
        "choices": [
            "A. 12",
            "B. 24",
            "C. 36",
            "D. 8"
        ],
        "answer": "B",
        "explanation": (
            "Most popular = Drawing (12). "
            "NOT Drawing = Reading+Dancing+Cooking = 8+6+10 = 24."
        ),
        "solution_steps": [
            "Step 1: Most popular = Drawing (12, tallest bar).",
            "Step 2: NOT Drawing = 8+6+10 = 24."
        ],
        "hints": [
            "First find the most popular activity (tallest bar).",
            "Then add all other activities' values."
        ],
        "feedback": {
            "correct": "Excellent! Drawing is most popular (12). NOT Drawing = 8+6+10 = 24.",
            "incorrect": "Step 1: most popular = Drawing (12). Step 2: add the rest: 8+6+10=24."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "two_step_bar",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R1_10"],
        "math_note": "Drawing=12 (최다). NOT Drawing=8+6+10=24 ✓. 오답 A(12): 중간 단계 멈춤.",
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
            "Bar graph: Cats 9, Dogs 15, Fish 6, Rabbits 12. "
            "How many animals in total does the graph show?"
        ),
        "data_table": {
            "title": "Pets at the Shelter",
            "type": "bar_graph",
            "categories": ["Cats", "Dogs", "Fish", "Rabbits"],
            "values": [9, 15, 6, 12],
            "scale": 3,
            "unit": "animals",
            "axis_label": {"x": "Animal", "y": "Number"}
        },
        "choices": [
            "A. 12",
            "B. 33",
            "C. 42",
            "D. 27"
        ],
        "answer": "C",
        "explanation": "9+15+6+12 = 42.",
        "solution_steps": [
            "Read each bar: Cats=9, Dogs=15, Fish=6, Rabbits=12.",
            "9+15+6+12 = 42."
        ],
        "hints": [
            "Read all four bar values carefully.",
            "Add all four values together."
        ],
        "feedback": {
            "correct": "Correct! 9+15+6+12=42.",
            "incorrect": "Read all four bars and add: 9+15+6+12=42."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "total_bar_values",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_05"],
        "math_note": "9+15+6+12=42 ✓. 오답 B(33): Rabbits 누락.",
        "verification": make_verification()
    },
    {
        "id": "R2_06",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Bar graph: Red 16, Blue 10, Green 8, Yellow 4. "
            "How many more students chose Red than Yellow?"
        ),
        "data_table": {
            "title": "Favorite Color",
            "type": "bar_graph",
            "categories": ["Red", "Blue", "Green", "Yellow"],
            "values": [16, 10, 8, 4],
            "scale": 2,
            "unit": "students",
            "axis_label": {"x": "Color", "y": "Students"}
        },
        "choices": [
            "A. 6",
            "B. 12",
            "C. 20",
            "D. 4"
        ],
        "answer": "B",
        "explanation": "Red=16, Yellow=4. 16−4=12.",
        "solution_steps": [
            "Red=16, Yellow=4.",
            "16−4=12."
        ],
        "hints": [
            "Read Red and Yellow bar values.",
            "Subtract: larger − smaller."
        ],
        "feedback": {
            "correct": "Correct! 16−4=12.",
            "incorrect": "'More than' means subtract. Red(16)−Yellow(4)=12."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_bars",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_06"],
        "math_note": "Red(16) - Yellow(4) = 12 ✓. 오답 C(20): 16+4=20 덧셈 오류.",
        "verification": make_verification()
    },
    {
        "id": "R2_07",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Bar graph: Morning 20, Afternoon 14, Evening 8, Night 6. "
            "How many students exercised in the Morning or Afternoon?"
        ),
        "data_table": {
            "title": "Exercise Times",
            "type": "bar_graph",
            "categories": ["Morning", "Afternoon", "Evening", "Night"],
            "values": [20, 14, 8, 6],
            "scale": 2,
            "unit": "students",
            "axis_label": {"x": "Time", "y": "Students"}
        },
        "choices": [
            "A. 34",
            "B. 22",
            "C. 48",
            "D. 20"
        ],
        "answer": "A",
        "explanation": "Morning=20, Afternoon=14. 20+14=34.",
        "solution_steps": [
            "Read Morning=20 and Afternoon=14.",
            "20+14=34."
        ],
        "hints": [
            "Only read Morning and Afternoon bars.",
            "Add those two values."
        ],
        "feedback": {
            "correct": "Correct! 20+14=34.",
            "incorrect": "Only add Morning(20) and Afternoon(14): 20+14=34. Don't include Evening or Night."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "total_bar_values",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_07"],
        "math_note": "Morning(20)+Afternoon(14)=34 ✓. 오답 C(48): 전체 합산(M04).",
        "verification": make_verification()
    },
    {
        "id": "R2_08",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "A tally table shows: Sunny = 𝍸𝍸𝍸 (15), Cloudy = 𝍸𝍸 (10), Rainy = 𝍸| (6). "
            "You make a bar graph from this data. Where does the bar for Cloudy end?"
        ),
        "data_table": {
            "title": "Weather This Month (Tally)",
            "type": "tally_table",
            "categories": ["Sunny", "Cloudy", "Rainy"],
            "tally_counts": [15, 10, 6],
            "unit": "days"
        },
        "choices": [
            "A. 2",
            "B. 10",
            "C. 15",
            "D. 6"
        ],
        "answer": "B",
        "explanation": "Cloudy tally: 𝍸𝍸 = 5+5 = 10 days. The bar ends at 10.",
        "solution_steps": [
            "Read Cloudy tally: 𝍸𝍸 = 5+5 = 10.",
            "Bar for Cloudy ends at 10."
        ],
        "hints": [
            "Each 𝍸 = 5. Count only the Cloudy row.",
            "𝍸𝍸 = 5+5 = ?"
        ],
        "feedback": {
            "correct": "Correct! 𝍸𝍸=10, so the bar ends at 10.",
            "incorrect": "Read the Cloudy tally: 𝍸𝍸 = 5+5 = 10."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "read_bar_value",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_08"],
        "math_note": "Cloudy: 𝍸𝍸=10 ✓. 오답 C(15): Sunny 행 오독. (U1 연계)",
        "verification": make_verification()
    },
    {
        "id": "R2_09",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Tally table: Pizza = 𝍸𝍸𝍸| (16), Burger = 𝍸𝍸 (10), Taco = 𝍸𝍸𝍸 (15). "
            "You make a bar graph with this data. "
            "How many more students chose Pizza than Burger?"
        ),
        "data_table": {
            "title": "Lunch Preference (Tally)",
            "type": "tally_table",
            "categories": ["Pizza", "Burger", "Taco"],
            "tally_counts": [16, 10, 15],
            "unit": "students"
        },
        "choices": [
            "A. 6",
            "B. 1",
            "C. 26",
            "D. 16"
        ],
        "answer": "A",
        "explanation": "Pizza = 𝍸𝍸𝍸| = 5+5+5+1 = 16. Burger = 𝍸𝍸 = 10. 16−10 = 6.",
        "solution_steps": [
            "Pizza: 𝍸𝍸𝍸| = 5+5+5+1 = 16.",
            "Burger: 𝍸𝍸 = 10.",
            "16−10 = 6."
        ],
        "hints": [
            "Count each tally: 𝍸=5, |=1.",
            "Subtract: Pizza − Burger."
        ],
        "feedback": {
            "correct": "Correct! Pizza=16, Burger=10, 16−10=6.",
            "incorrect": "Read tallies: Pizza=16, Burger=10. Then subtract: 16−10=6."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_bars",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_09"],
        "math_note": "Pizza(16) - Burger(10) = 6 ✓. 오답 C(26): 16+10=26 덧셈. (U1 연계)",
        "review_from": "U1",
        "verification": make_verification()
    },
    {
        "id": "R2_10",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Tally table: Cats = 𝍸𝍸| (11), Dogs = 𝍸𝍸𝍸 (15), Fish = 𝍸 (5). "
            "You make a bar graph from this data. "
            "What is the total number of animals recorded?"
        ),
        "data_table": {
            "title": "Classroom Pets (Tally)",
            "type": "tally_table",
            "categories": ["Cats", "Dogs", "Fish"],
            "tally_counts": [11, 15, 5],
            "unit": "animals"
        },
        "choices": [
            "A. 5",
            "B. 26",
            "C. 31",
            "D. 15"
        ],
        "answer": "C",
        "explanation": "Cats=𝍸𝍸|=11. Dogs=𝍸𝍸𝍸=15. Fish=𝍸=5. Total=11+15+5=31.",
        "solution_steps": [
            "Cats: 𝍸𝍸| = 5+5+1 = 11.",
            "Dogs: 𝍸𝍸𝍸 = 15.",
            "Fish: 𝍸 = 5.",
            "11+15+5 = 31."
        ],
        "hints": [
            "Count each tally carefully: 𝍸=5, |=1.",
            "Add all three totals."
        ],
        "feedback": {
            "correct": "Excellent! Cats=11, Dogs=15, Fish=5, Total=31.",
            "incorrect": "Count all tallies: Cats=11, Dogs=15, Fish=5. Then add: 11+15+5=31."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "total_bar_values",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_10"],
        "math_note": "11+15+5=31 ✓. 오답 B(26): Fish(5) 누락. (U1 연계)",
        "review_from": "U1",
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
            "Bar graph: Art 8, Music 14, Drama 10, Dance 12. "
            "Suppose 6 students who originally chose Music decide to switch to Art instead. "
            "What will the new value for Art be?"
        ),
        "data_table": {
            "title": "Favorite School Subject",
            "type": "bar_graph",
            "categories": ["Art", "Music", "Drama", "Dance"],
            "values": [8, 14, 10, 12],
            "scale": 2,
            "unit": "students",
            "axis_label": {"x": "Subject", "y": "Students"}
        },
        "choices": [
            "A. 8",
            "B. 14",
            "C. 22",
            "D. 6"
        ],
        "answer": "B",
        "explanation": "Original Art = 8. Add 6 switchers: 8+6 = 14.",
        "solution_steps": [
            "Original Art = 8.",
            "6 students switch to Art: 8+6 = 14."
        ],
        "hints": [
            "Start with Art's original value.",
            "Add the 6 students who switch."
        ],
        "feedback": {
            "correct": "Correct! Art=8, add 6 switchers: 8+6=14.",
            "incorrect": "Art starts at 8. Add 6 more: 8+6=14."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "two_step_bar",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R3_04"],
        "math_note": "Art(8)+6=14 ✓. 오답 A(8): 원래 값 그대로.",
        "verification": make_verification()
    },
    {
        "id": "R3_05",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Bar graph: Spring 15, Summer 25, Fall 10, Winter 20. "
            "Is the total for Spring and Winter equal to, greater than, or less than the total for Summer and Fall?"
        ),
        "data_table": {
            "title": "Favorite Season",
            "type": "bar_graph",
            "categories": ["Spring", "Summer", "Fall", "Winter"],
            "values": [15, 25, 10, 20],
            "scale": 5,
            "unit": "students",
            "axis_label": {"x": "Season", "y": "Students"}
        },
        "choices": [
            "A. Equal — both groups total 35",
            "B. Spring+Winter is greater, by 5",
            "C. Summer+Fall is greater, by 5",
            "D. Cannot determine without more information"
        ],
        "answer": "A",
        "explanation": (
            "Spring+Winter = 15+20 = 35. "
            "Summer+Fall = 25+10 = 35. "
            "Both equal 35."
        ),
        "solution_steps": [
            "Spring+Winter = 15+20 = 35.",
            "Summer+Fall = 25+10 = 35.",
            "35 = 35 → Equal."
        ],
        "hints": [
            "Calculate Spring+Winter first.",
            "Calculate Summer+Fall and compare."
        ],
        "feedback": {
            "correct": "Correct! Both groups equal 35.",
            "incorrect": "Spring+Winter=15+20=35. Summer+Fall=25+10=35. They are equal."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "two_step_bar",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R3_05"],
        "math_note": "Spring+Winter=35=Summer+Fall ✓. 합산 전 단일 값으로 비교하면 오류.",
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
    # R2_08, R2_09, R2_10은 이미 review_from="U1" 설정됨
    # 추가로 아직 없는 항목에도 적용 (마지막 3개 = 인덱스 7,8,9)
    r2_tail_start = len(r2_items) * 3 // 4
    for item in r2_items[r2_tail_start:]:
        if "review_from" not in item:
            item["review_from"] = "U1"

    # 레슨 레벨 필드 추가
    d["tier"] = "A"
    d["review_from_units"] = ["U1"]
    d["vertical_alignment"] = {
        "prerequisite": "G2 — Organize data in up to 4 categories; use tally marks",
        "current": "G3 — Read scaled bar graphs; solve 'how many more/fewer' and two-step problems",
        "successor": "G4 — Multi-step problems using data in various representations"
    }
    d["unit_intro_message"] = (
        "이번 단원에서는 막대 그래프를 읽고 해석하는 방법을 배웁니다. "
        "스케일 읽기, 바 끝점에서 값 읽기, '더 많은/적은' 비교, 2단계 문제 풀기를 익힙니다."
    )
    d["unit_close_message"] = (
        "잘 했어요! 이제 막대 그래프를 읽고 비교 문제를 풀 수 있습니다. "
        "다음 레슨에서는 막대 그래프를 직접 만드는 방법을 학습합니다."
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
    print(f"✅ 업그레이드 완료: L4_use_bar_graphs.json")
    print(f"   PT={counts['pretest']}  LEARN={counts['learn']}  TRY={counts['try']}")
    print(f"   R1={counts['practice_r1']}  R2={counts['practice_r2']}  R3={counts['practice_r3']}")
    print(f"   총 문항 수: {total}")


if __name__ == "__main__":
    upgrade()
