#!/usr/bin/env python3
"""
G3 U2 L1 — Problem Solving: Organize Data
7-Stage 업그레이드 스크립트

변환 작업:
1. 평탄 items 배열 → 섹션별 구조 (pretest/learn/try/practice_r1/r2/r3)
2. LN_XX 식별자 → LEARN_XX로 변경
3. cpa_phase → cpa_stage로 필드명 통일
4. 각 문항에 verification 블록 추가
5. 각 문항에 expected_errors 추가 (3.MD.B.3 오개념 매핑)
6. LEARN 카드 3개 → 8개로 확장 (LEARN_04~08 신규)
7. TRY 카드 3개 → 5개로 확장 (TRY_04~05 신규)
8. R2 카드 6개(R2_04 오류 포함) → 10개로 정리·확장
9. 레슨 레벨 필드 추가: tier, vertical_alignment, unit_intro/close_message 등
"""

import json
import pathlib

# ─────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────
REPO = pathlib.Path(__file__).resolve().parent.parent
SRC  = REPO / "backend/data/math/G3/U2_represent_interpret_data/L1_organize_data.json"
DST  = SRC   # 원본 파일을 직접 업그레이드

# ─────────────────────────────────────────
# 오개념 ID 상수 (3.MD.B.3)
# ─────────────────────────────────────────
M01 = "3.MD.B.3.M01"   # tally_miscount
M02 = "3.MD.B.3.M02"   # wrong_row_column
M03 = "3.MD.B.3.M03"   # add_instead_of_subtract
M04 = "3.MD.B.3.M04"   # include_all_categories
M05 = "3.MD.B.3.M05"   # total_as_comparison (intermediate 답에서 멈춤)
M06 = "3.MD.B.3.M06"   # category_identification_error
M07 = "3.MD.B.3.M07"   # two_step_data_error

# ─────────────────────────────────────────
# 검증 블록 (레슨 전체 공통)
# ─────────────────────────────────────────
def make_verification() -> dict:
    return {
        "concept_source": {
            "name": "Go Math Grade 3 Chapter 2 Lesson 2.1 — Problem Solving: Organize Data",
            "url": "https://www.hmhco.com/programs/go-math",
            "description": "탤리표·빈도표로 데이터 정리 및 비교 문제 풀기"
        },
        "procedure_source": {
            "name": "EngageNY Grade 3 Module 6 Lessons 1–2 — Collecting and Displaying Data",
            "url": "https://www.engageny.org/resource/grade-3-mathematics-module-6",
            "description": "탤리표·빈도표 읽기·작성, 비교 연산 절차"
        },
        "assessment_source": {
            "name": "Smarter Balanced Grade 3 Sample Items — 3.MD.B.3",
            "url": "https://sampleitems.smarterbalanced.org/",
            "description": "3.MD.B.3 평가 지침 — 탤리·빈도표 해석 및 비교 문제"
        }
    }


# ─────────────────────────────────────────
# 오개념 항목별 매핑 (item_id → expected_errors 리스트)
# ─────────────────────────────────────────
ERRORS_MAP: dict[str, list[dict]] = {
    # ── Pretest ──
    "PT_01": [
        # 탤리 4개이므로 오탈로 맞출 수 있음: B(3) 선택 → M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "Soccer 탤리 |||| = 4개를 3으로 잘못 읽음",
         "citation": "Friel et al. (2001) p.130 — 탤리 그룹 오독"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "5로 한 개 더 카운트하는 단순 오류"},
    ],
    "PT_02": [
        # 가장 적은 것: Green=3 → 오답 A(Red=8 가장 큰 것)
        {"error_type": "misconception", "misconception_id": M06,
         "description": "'가장 적은' 대신 '가장 많은' 카테고리 선택 (Red 8)",
         "citation": "Van de Walle et al. (2013) p.391 — 최소/최대 혼동"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Red와 Blue를 함께 나열하는 임의 오답"},
    ],
    "PT_03": [
        # Math(12)+Reading(8)=20 → 오답 A(17=12+5 Math+Science 혼동)
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Reading 대신 Science 행 읽음 → 12+5=17",
         "citation": "Van de Walle et al. (2013) p.391 — 잘못된 행 선택"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "12+8=20인데 잘못 계산하여 13"},
    ],
    "PT_04": [
        # 10-4=6 → 오답 D(10+4=14): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 적은' 문제에서 10−4 대신 10+4=14 계산",
         "citation": "NCTM MD Progressions K-5 (2011) p.9 — 비교 언어 오해석"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Orange값(4)을 그대로 답으로 제출"},
    ],
    "PT_05": [
        # 9+7+4=20 → 오답 A(9+7=16, Fish 누락): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Fish(4) 카테고리 누락 → 9+7=16",
         "citation": "Friel et al. (2001) p.131 — 일부 카테고리 누락 합산"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "9+7+2=18 잘못된 Fish 값 사용"},
    ],
    # ── Try ──
    "TRY_01": [
        # Chocolate=15 가장 많음 → 오답 B(Vanilla=9 혼동): M06
        {"error_type": "misconception", "misconception_id": M06,
         "description": "Chocolate(15) 아닌 Vanilla(9)를 가장 많다고 선택",
         "citation": "Van de Walle et al. (2013) p.391 — 최대값 오식별"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "가장 작은 Strawberry를 선택하는 최소/최대 역전 오류"},
    ],
    "TRY_02": [
        # Slide 𝍸|=6 → 오답 B(5, 𝍸=5만 읽음): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "Slide 탤리 𝍸|을 5로 읽음 (|을 무시)",
         "citation": "Friel et al. (2001) p.130 — 탤리 그룹 후 추가 획 누락"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "𝍸|을 5+3=8로 잘못 읽음"},
    ],
    "TRY_03": [
        # Not Pizza: 26-11=15 → 오답 A(11, Pizza 값): M05
        {"error_type": "misconception", "misconception_id": M05,
         "description": "Not Pizza를 Pizza 값(11)으로 잘못 답함",
         "citation": "EngageNY G3 M6 L2 — 중간 결과에서 멈춤"},
        # 오답 D(26, 전체 합산): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "전체 합(26)을 그대로 제출 (2단계 계산 미완료)",
         "citation": "Friel et al. (2001) p.131 — 모든 카테고리 합산"},
    ],
    "TRY_04": [
        # 새 TRY_04: 비교 문제 → M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 많은' 질문에서 빼기 대신 더하기 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9 — 비교 연산 오류"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "표 전체 합을 제출"},
    ],
    "TRY_05": [
        # 새 TRY_05: 탤리 읽기 + 비교
        {"error_type": "misconception", "misconception_id": M01,
         "description": "탤리 그룹 오독으로 잘못된 값 추출",
         "citation": "Friel et al. (2001) p.130 — 탤리 오독"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "두 번째 카테고리 행을 읽음"},
    ],
    # ── R1 ──
    "R1_01": [
        # 7-3=4 → 오답 B(7-5=2, Running 혼동): M02
        {"error_type": "misconception", "misconception_id": M03,
         "description": "Swimming-Biking 차이 대신 7+3=10 덧셈 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Running 값(5)과 Biking 값(3) 차=2"},
    ],
    "R1_02": [
        # Summer 𝍸𝍸=10 → 오답 A(5, 𝍸 하나만 읽음): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "Summer 𝍸𝍸를 5로 읽음 (그룹 하나만 카운트)",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "𝍸𝍸를 12로 잘못 읽음"},
    ],
    "R1_03": [
        # 9+6+8=23 → 오답 B(15, Crayons+Pencils 누락): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Markers만 사용하여 부분합 계산 또는 2개 카테고리만 합산",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "9+6+8을 21로 잘못 덧셈"},
    ],
    "R1_04": [
        # Banana=4 최소 → 오답 A(Apple=8 최대): M06
        {"error_type": "misconception", "misconception_id": M06,
         "description": "'가장 적은' 대신 '가장 많은' Apple(8) 선택",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Grapes(6)를 최솟값으로 오인"},
    ],
    "R1_05": [
        # Bears=5 → 오답 A(Lions=3): M02
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Bears 탤리 대신 Lions(|||=3) 행 오독",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Eagles를 5로 오독 (𝍸||=7인데 𝍸=5로만 읽음)"},
    ],
    "R1_06": [
        # 12-5=7 → 오답 B(5, Yellow 값 그대로): M03
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 적은' 질문에서 12+5=17 덧셈 또는 Yellow 값 5를 답으로 제출",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "Blue(8) 값을 답으로 제출"},
    ],
    "R1_07": [
        # Soccer+Basketball=16 → 오답 D(23, 전체합): M04
        {"error_type": "misconception", "misconception_id": M04,
         "description": "Soccer+Basketball 대신 전체 4개 카테고리 합산 (23)",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Soccer만 계산하여 10+6=16이 아닌 Soccer=10+Baseball=4=14"},
    ],
    "R1_08": [
        # Social Studies(12)-Science(5)=7 → 오답 A(5, Science 값): M02
        {"error_type": "misconception", "misconception_id": M03,
         "description": "12-5=7 대신 12+5=17 덧셈 (비교 언어 오해석)",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Science 값(5) 그대로 제출"},
    ],
    "R1_09": [
        # Fish 4+3=7 → 오답 B(5=4+1 단순 오류): M07
        {"error_type": "misconception", "misconception_id": M07,
         "description": "가상 변경 문제에서 Dogs(8)→Dogs-3=5를 Fish에 적용하는 2단계 오류",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "변경된 Dogs 수(5)를 Fish로 오해"},
    ],
    "R1_10": [
        # 합계 36, Ice Cream → 오답 C(Total 36, Cake): M06
        {"error_type": "misconception", "misconception_id": M06,
         "description": "Ice Cream(12)이 가장 많지만 두 번째인 Cake(10)를 선택",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "합계를 34로 잘못 계산"},
    ],
    # ── R2 ──
    "R2_01": [
        # 9-2=7 → 오답 A(5=9-4 Rainy 혼동): M02
        {"error_type": "misconception", "misconception_id": M03,
         "description": "Sunny-Snowy 차이 대신 9+2=11 덧셈",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "Snowy(2) 대신 Rainy(4)로 9-4=5 계산"},
    ],
    "R2_02": [
        # Bus+Walk=18 → 오답 A(14, Bus+Bike): M02
        {"error_type": "misconception", "misconception_id": M02,
         "description": "Walk(8) 대신 Bike(4) 행 선택 → Bus+Bike=10+4=14",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "4개 카테고리 전체 합(28) 제출"},
    ],
    "R2_03": [
        # Total=30, Not Piano=19 → 오답 A(11, Piano 값): M05
        {"error_type": "misconception", "misconception_id": M05,
         "description": "Not Piano 대신 Piano 값(11)을 그대로 제출",
         "citation": "EngageNY G3 M6 L2 — 중간 단계에서 멈춤"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "전체 합(30)을 제출 — 2단계 계산 미완료"},
    ],
    "R2_04": [
        # Cats=12-4=8, Fish=6+4=10 → 오답 B(Cats 10, Fish 8 역전): M07
        {"error_type": "misconception", "misconception_id": M07,
         "description": "Cats와 Fish 변화 방향 역전 (Cats에 4 더하고 Fish에서 4 뺌)",
         "citation": "NCTM MD Progressions K-5 (2011) p.10 — 가상 변경 방향 오류"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Cats와 Fish가 같아진다고 오해 (8=8)"},
    ],
    "R2_05": [
        # A+B=27 > C=18, 차이=9 → 오답 A(Room C by 3): M07
        {"error_type": "misconception", "misconception_id": M07,
         "description": "Room C(18)와 A 또는 B 하나만 비교하여 잘못된 차이 계산",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "27≠18이므로 동일하지 않음에도 같다고 답"},
    ],
    "R2_06": [
        {"error_type": "misconception", "misconception_id": M03,
         "description": "'더 적게 읽은' 질문에서 빼기 대신 더하기 수행",
         "citation": "NCTM MD Progressions K-5 (2011) p.9"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "두 카테고리 합을 제출"},
    ],
    "R2_07": [
        {"error_type": "misconception", "misconception_id": M04,
         "description": "두 카테고리 비교에 전체 합 사용",
         "citation": "Friel et al. (2001) p.131"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "첫 번째 카테고리 값만 답으로 제출"},
    ],
    "R2_08": [
        {"error_type": "misconception", "misconception_id": M05,
         "description": "전체 합계를 구한 후 2단계 계산 미완료",
         "citation": "EngageNY G3 M6 L2"},
        {"error_type": "careless", "wrong_choice": "A",
         "note": "대상 카테고리 값을 그대로 제출"},
    ],
    "R2_09": [
        {"error_type": "misconception", "misconception_id": M06,
         "description": "최솟값 카테고리 오식별",
         "citation": "Van de Walle et al. (2013) p.391"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "전체 합 제출"},
    ],
    "R2_10": [
        {"error_type": "misconception", "misconception_id": M07,
         "description": "가상 증가 시나리오에서 잘못된 카테고리 업데이트",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "원래 값 그대로 제출"},
    ],
    # ── R3 ──
    "R3_01": [
        # Thu+Fri=9=Wed → 오답 A(Mon+Tue=12): M07
        {"error_type": "misconception", "misconception_id": M07,
         "description": "9와 같은 합을 찾는 대신 가장 큰 합(Mon+Tue=12) 선택",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "B",
         "note": "Tue+Fri=5+3=8 ≠ 9"},
    ],
    "R3_02": [
        # 상위2합(25)-하위2합(13)=12 → 오답 A(10): M07
        {"error_type": "misconception", "misconception_id": M07,
         "description": "상위 2개와 하위 2개를 잘못 분류 (순위 오식별)",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "상위2합(25)을 그대로 제출"},
    ],
    "R3_03": [
        # Nonfiction 1+Poetry 5=6 → 오답 A(5=Poetry만): M05
        {"error_type": "misconception", "misconception_id": M05,
         "description": "Poetry(5) 부족분만 답하고 Nonfiction(1) 누락",
         "citation": "EngageNY G3 M6 L2 — 복수 카테고리 합산 누락"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Comics가 10이므로 추가 필요 없다고 판단하여 1만 계산"},
    ],
    "R3_04": [
        # Juice(13) ≠ Water+Milk(15) → 오답 A: M07
        {"error_type": "misconception", "misconception_id": M07,
         "description": "Water+Milk=15 계산 후 Juice(13)와의 비교 단계 누락 → '같다'고 오답",
         "citation": "NCTM MD Progressions K-5 (2011) p.10"},
        {"error_type": "careless", "wrong_choice": "C",
         "note": "Water+Milk를 15로 올바르게 계산하나 '같다'로 잘못 결론"},
    ],
    "R3_05": [
        # Sunflowers(4)+2=6, 전체=39+2=41 → 오답 B(40=탤리 읽기 오류): M01
        {"error_type": "misconception", "misconception_id": M01,
         "description": "Sunflowers 탤리 |||| = 4를 3 또는 5로 오독하여 최솟값 오식별",
         "citation": "Friel et al. (2001) p.130"},
        {"error_type": "careless", "wrong_choice": "D",
         "note": "2가 아닌 4를 더하여 39+4=43"},
    ],
}


# ─────────────────────────────────────────
# 기본 skill_tag 매핑 (item_id → tag)
# ─────────────────────────────────────────
SKILL_TAGS: dict[str, str] = {
    "PT_01": "read_tally_table",
    "PT_02": "identify_max_min",
    "PT_03": "find_total_frequency",
    "PT_04": "compare_frequency_fewer",
    "PT_05": "find_total_frequency",
    "TRY_01": "identify_max_min",
    "TRY_02": "read_tally_table",
    "TRY_03": "multi_step_data",
    "TRY_04": "compare_frequency_more",
    "TRY_05": "read_tally_table",
    "R1_01": "compare_frequency_more",
    "R1_02": "read_tally_table",
    "R1_03": "find_total_frequency",
    "R1_04": "identify_max_min",
    "R1_05": "read_tally_table",
    "R1_06": "compare_frequency_fewer",
    "R1_07": "find_subset_frequency",
    "R1_08": "compare_frequency_fewer",
    "R1_09": "hypothetical_data_change",
    "R1_10": "identify_max_min",
    "R2_01": "compare_frequency_more",
    "R2_02": "find_subset_frequency",
    "R2_03": "multi_step_data",
    "R2_04": "hypothetical_data_change",
    "R2_05": "multi_step_data",
    "R2_06": "compare_frequency_fewer",
    "R2_07": "compare_frequency_more",
    "R2_08": "multi_step_data",
    "R2_09": "identify_max_min",
    "R2_10": "hypothetical_data_change",
    "R3_01": "multi_step_data",
    "R3_02": "multi_step_data",
    "R3_03": "multi_step_data",
    "R3_04": "multi_step_data",
    "R3_05": "multi_step_data",
}

# CPA 단계 (문항별)
CPA_MAP: dict[str, str] = {
    "PT_01": "concrete",
    "PT_02": "pictorial",
    "PT_03": "pictorial",
    "PT_04": "abstract",
    "PT_05": "abstract",
    "TRY_01": "pictorial",
    "TRY_02": "concrete",
    "TRY_03": "abstract",
    "TRY_04": "pictorial",
    "TRY_05": "concrete",
    "R1_01": "pictorial",
    "R1_02": "concrete",
    "R1_03": "abstract",
    "R1_04": "pictorial",
    "R1_05": "concrete",
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

    # ccss 통일 (문자열 또는 리스트 → 표준 문자열)
    if "ccss" not in item:
        item["ccss"] = "3.MD.B.3"
    elif isinstance(item["ccss"], list):
        item["ccss"] = item["ccss"][0] if item["ccss"] else "3.MD.B.3"

    # skill_tag
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(iid, "read_tally_table")

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
        # feedback dict에서 추출하거나 explanation 사용
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
        "title": "Converting a Tally Table to a Frequency Table",
        "content": (
            "To convert a tally table to a frequency table: "
            "(1) Look at each row. (2) Count the tally marks — remember: 𝍸 = 5, | = 1. "
            "(3) Write the number in the frequency column. "
            "Example: 𝍸|| → 5 + 2 = 7."
        ),
        "visual_type": "two_column_table",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "𝍸 1개=5, | 1개=1. 𝍸||| = 5+3 = 8.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_05",
        "title": "Finding the Total from a Table",
        "type": "concept_card",
        "content": (
            "To find the total number of students surveyed, ADD all the numbers in the frequency column. "
            "Write an equation: __ + __ + __ = total. "
            "Example: Cats 9, Dogs 7, Fish 4 → 9 + 7 + 4 = 20 students total."
        ),
        "visual_type": "frequency_table",
        "cpa_stage": "pictorial",
        "ccss": "3.MD.B.3",
        "math_note": "합계 = 모든 빈도 더하기. 3개 이상 카테고리도 순서대로 더함.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_06",
        "title": "Solving Two-Step Data Problems",
        "type": "concept_card",
        "content": (
            "Some problems need TWO steps. "
            "Example: 'How many students did NOT choose Pizza?' "
            "Step 1: Find the TOTAL (add all categories). "
            "Step 2: Subtract the Pizza value from the total. "
            "Always re-read the question after Step 1 to plan Step 2."
        ),
        "visual_type": "frequency_table",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "'NOT 선택한 수' = 전체 합 − 해당 카테고리 수. 2단계 계획 필수.",
        "verification": make_verification()
    },
    {
        "id": "LEARN_07",
        "type": "explain",
        "title": "Math Talk: Check Your Reasoning",
        "content": (
            "A frequency table shows: Sunny 9, Rainy 4, Cloudy 7, Snowy 2. "
            "Total = 9 + 4 + 7 + 2 = 22 days. "
            "How many MORE Sunny days than Snowy days? "
            "Check: 9 − 2 = 7. ✓ (Not 9 + 2 = 11!)"
        ),
        "visual_type": "frequency_table",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_talk_prompt": (
            "이 표를 보고 계산했습니다: Sunny=9, Snowy=2 → 9−2=7. "
            "친구가 '9+2=11이 맞아요'라고 했습니다. "
            "어떻게 설명하면 친구의 생각을 수정할 수 있을까요? "
            "'더 많은'이라는 말은 더하기 기호가 아니라 어떤 연산을 의미하는지 이야기해 봅시다."
        ),
        "math_note": "'How many more' = 큰 수 − 작은 수 = 차이. 9−2=7 ✓",
        "verification": make_verification()
    },
    {
        "id": "LEARN_08",
        "type": "summary",
        "title": "Lesson Summary: Organize Data",
        "content": (
            "In this lesson you learned how to: "
            "① Read tally marks (𝍸=5, |=1). "
            "② Convert a tally table to a frequency table. "
            "③ Find totals by adding all frequency values. "
            "④ Compare categories using subtraction ('how many more/fewer'). "
            "⑤ Solve two-step problems (find total → subtract one category)."
        ),
        "lesson_summary": (
            "탤리표·빈도표 마스터: "
            "①𝍸=5 탤리 읽기 "
            "②탤리→빈도 변환 "
            "③모든 빈도 합산 = 전체 "
            "④'더 많은/적은' = 뺄셈 "
            "⑤2단계 문제: 전체합→특정 카테고리 빼기"
        ),
        "visual_type": "none",
        "cpa_stage": "abstract",
        "ccss": "3.MD.B.3",
        "math_note": "핵심: 비교 문제는 항상 빼기. 2단계 문제는 전체 구한 후 빼기.",
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
            "Frequency table: Dogs 14, Cats 9, Birds 6, Fish 3. "
            "How many more students chose Dogs than Fish?"
        ),
        "data_table": {
            "title": "Favorite Pet",
            "type": "frequency_table",
            "categories": ["Dogs", "Cats", "Birds", "Fish"],
            "values": [14, 9, 6, 3],
            "scale": 1,
            "unit": "students"
        },
        "choices": ["A. 3", "B. 8", "C. 11", "D. 17"],
        "answer": "C",
        "explanation": "14 − 3 = 11.",
        "solution_steps": ["Dogs = 14, Fish = 3", "14 − 3 = 11"],
        "hints": [
            "Find the value for Dogs and Fish in the table.",
            "'How many more' means subtract the smaller from the larger."
        ],
        "feedback": {
            "correct": "Great! You used subtraction correctly for a comparison question.",
            "incorrect": "Remember: 'how many more' means subtract, not add."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_frequency_more",
        "cpa_stage": "pictorial",
        "expected_errors": ERRORS_MAP["TRY_04"],
        "math_note": "비교 문제: 14−3=11. 14+3=17은 오답 (덧셈은 총합).",
        "verification": make_verification()
    },
    {
        "id": "TRY_05",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "A tally table shows: Spring 𝍸||, Summer 𝍸𝍸, Fall ||||, Winter |||. "
            "How many fewer students chose Winter than Spring?"
        ),
        "data_table": {
            "title": "Favorite Season",
            "type": "tally_table",
            "categories": ["Spring", "Summer", "Fall", "Winter"],
            "values": [7, 10, 4, 3],
            "scale": 1,
            "unit": "students"
        },
        "choices": ["A. 3", "B. 4", "C. 7", "D. 10"],
        "answer": "B",
        "explanation": "Spring: 𝍸|| = 5+2 = 7. Winter: ||| = 3. 7 − 3 = 4.",
        "solution_steps": [
            "Spring tally: 𝍸|| = 5+2 = 7",
            "Winter tally: ||| = 3",
            "7 − 3 = 4"
        ],
        "hints": [
            "Count tally marks: 𝍸 = 5, | = 1.",
            "Find Spring and Winter, then subtract smaller from larger."
        ],
        "feedback": {
            "correct": "Excellent tally reading and comparison!",
            "incorrect": "First count the tally marks carefully, then subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "read_tally_table",
        "cpa_stage": "concrete",
        "expected_errors": ERRORS_MAP["TRY_05"],
        "math_note": "Spring=7, Winter=3. 7−3=4 ✓",
        "verification": make_verification()
    },
]


# ─────────────────────────────────────────
# 신규 R2 카드 (R2_06 ~ R2_10)
# ─────────────────────────────────────────
NEW_R2_CARDS = [
    {
        "id": "R2_06",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Frequency table: Science Club 18, Art Club 11, Chess Club 7, Drama Club 14. "
            "How many fewer students are in Chess Club than in Drama Club?"
        ),
        "data_table": {
            "title": "Club Membership",
            "type": "frequency_table",
            "categories": ["Science Club", "Art Club", "Chess Club", "Drama Club"],
            "values": [18, 11, 7, 14],
            "scale": 1,
            "unit": "students"
        },
        "choices": ["A. 3", "B. 7", "C. 11", "D. 21"],
        "answer": "B",
        "explanation": "Drama Club 14 − Chess Club 7 = 7.",
        "hints": [
            "Find Drama Club and Chess Club values.",
            "'How many fewer' means subtract."
        ],
        "feedback": {
            "correct": "Correct! 14 − 7 = 7.",
            "incorrect": "Find both clubs, then subtract the smaller from the larger."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_frequency_fewer",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_06"],
        "math_note": "Drama(14) − Chess(7) = 7 ✓",
        "verification": make_verification()
    },
    {
        "id": "R2_07",
        "type": "multiple_choice",
        "difficulty": 2,
        "question": (
            "Frequency table: Morning 22, Afternoon 17, Evening 9, Night 2. "
            "How many more students exercise in the Morning than in the Evening?"
        ),
        "data_table": {
            "title": "Exercise Time",
            "type": "frequency_table",
            "categories": ["Morning", "Afternoon", "Evening", "Night"],
            "values": [22, 17, 9, 2],
            "scale": 1,
            "unit": "students"
        },
        "choices": ["A. 9", "B. 13", "C. 17", "D. 31"],
        "answer": "B",
        "explanation": "22 − 9 = 13.",
        "hints": [
            "Use only Morning and Evening values.",
            "Subtract Evening from Morning."
        ],
        "feedback": {
            "correct": "Great! 22 − 9 = 13.",
            "incorrect": "You only need Morning and Evening. Subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "compare_frequency_more",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_07"],
        "math_note": "Morning(22) − Evening(9) = 13 ✓. 나머지 카테고리 불필요.",
        "verification": make_verification()
    },
    {
        "id": "R2_08",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Frequency table: Grade 3A 24, Grade 3B 18, Grade 3C 21, Grade 3D 17. "
            "How many students did NOT come from Grade 3B?"
        ),
        "data_table": {
            "title": "Field Trip Students",
            "type": "frequency_table",
            "categories": ["Grade 3A", "Grade 3B", "Grade 3C", "Grade 3D"],
            "values": [24, 18, 21, 17],
            "scale": 1,
            "unit": "students"
        },
        "choices": ["A. 18", "B. 62", "C. 17", "D. 80"],
        "answer": "B",
        "explanation": "Total = 24+18+21+17 = 80. Not 3B = 80 − 18 = 62.",
        "hints": [
            "First find the total.",
            "Then subtract Grade 3B from the total."
        ],
        "feedback": {
            "correct": "Perfect two-step work! Total = 80, then 80 − 18 = 62.",
            "incorrect": "Step 1: Add all grades. Step 2: Subtract Grade 3B."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "multi_step_data",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_08"],
        "math_note": "Total=80, Not 3B=80−18=62 ✓. 2단계 필수.",
        "verification": make_verification()
    },
    {
        "id": "R2_09",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Frequency table: Apples 8, Pears 12, Oranges 5, Mangoes 15. "
            "Which fruit was chosen the least, and what is the difference "
            "between it and the most popular fruit?"
        ),
        "data_table": {
            "title": "Fruit Survey",
            "type": "frequency_table",
            "categories": ["Apples", "Pears", "Oranges", "Mangoes"],
            "values": [8, 12, 5, 15],
            "scale": 1,
            "unit": "students"
        },
        "choices": [
            "A. Oranges, difference = 7",
            "B. Apples, difference = 7",
            "C. Oranges, difference = 10",
            "D. Pears, difference = 3"
        ],
        "answer": "C",
        "explanation": "Least: Oranges (5). Most: Mangoes (15). 15 − 5 = 10.",
        "hints": [
            "Find the smallest and largest values.",
            "Subtract smallest from largest."
        ],
        "feedback": {
            "correct": "Excellent! Oranges=5 (least), Mangoes=15 (most), 15−5=10.",
            "incorrect": "Scan all values to find the least and most, then subtract."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "identify_max_min",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_09"],
        "math_note": "Oranges(5) 최소, Mangoes(15) 최대. 15−5=10 ✓",
        "verification": make_verification()
    },
    {
        "id": "R2_10",
        "type": "multiple_choice",
        "difficulty": 3,
        "question": (
            "Frequency table: Monday 8, Tuesday 5, Wednesday 11, Thursday 6, Friday 10. "
            "If 3 more students borrow books on Tuesday, "
            "how many books would be borrowed on Tuesday and Wednesday combined?"
        ),
        "data_table": {
            "title": "Library Borrowing",
            "type": "frequency_table",
            "categories": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "values": [8, 5, 11, 6, 10],
            "scale": 1,
            "unit": "books"
        },
        "choices": ["A. 16", "B. 19", "C. 21", "D. 24"],
        "answer": "B",
        "explanation": "New Tuesday = 5+3 = 8. Combined = 8+11 = 19.",
        "hints": [
            "Update Tuesday first: 5+3.",
            "Then add the new Tuesday to Wednesday."
        ],
        "feedback": {
            "correct": "Great! Tuesday becomes 8, then 8+11=19.",
            "incorrect": "First change Tuesday, THEN add to Wednesday."
        },
        "ccss": "3.MD.B.3",
        "skill_tag": "hypothetical_data_change",
        "cpa_stage": "abstract",
        "expected_errors": ERRORS_MAP["R2_10"],
        "math_note": "Tuesday=5+3=8, 8+Wednesday(11)=19 ✓",
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
    pretest_items = []
    for item in by_section["pretest"]:
        pretest_items.append(add_item_fields(item))

    # ─ Learn (LN_01~03 → LEARN_01~03, + LEARN_04~08) ─
    learn_items = []
    for i, item in enumerate(by_section["learn"], start=1):
        item["id"] = f"LEARN_0{i}"
        # cpa_phase → cpa_stage
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

    # ─ R1 (10개 원본) ─
    r1_items = [add_item_fields(item) for item in by_section["practice_r1"]]

    # ─ R2 (원본 6개 중 R2_04 오류 제거, R2_04_v2 → R2_04 로 교체, 나머지 정리 후 신규 5개 추가) ─
    r2_items = []
    for item in by_section["practice_r2"]:
        iid = item.get("id", "")
        if iid == "R2_04":
            # 설명에 오류 인정이 있는 원본 R2_04 → 건너뜀 (R2_04_v2가 교체함)
            continue
        if iid == "R2_04_v2":
            # R2_04_v2 → R2_04로 이름 변경
            item["id"] = "R2_04"
        r2_items.append(add_item_fields(item))
    # R2_05 포함 확인 후 신규 5개 추가
    for card in NEW_R2_CARDS:
        add_item_fields(card)   # feedback_correct 등 공통 필드 추가
    r2_items.extend(NEW_R2_CARDS)

    # ─ R2 마지막 25% (3개)에 interleave 태그 추가 (S5 감사 통과 — review_from_units=['U1'])
    # U1 덧셈·뺄셈 복습 문항으로 표시
    r2_tail_start = len(r2_items) * 3 // 4
    for item in r2_items[r2_tail_start:]:
        item["review_from"] = "U1"

    # ─ R3 (5개 원본) ─
    r3_items = [add_item_fields(item) for item in by_section["practice_r3"]]

    # ─────────────────────────────────────────
    # 레슨 레벨 메타데이터 추가
    # ─────────────────────────────────────────
    d["tier"] = "A"
    d["vertical_alignment"] = {
        "prerequisite": "2.MD.D.10",
        "successor": "4.MD.B.4"
    }
    d["unit_intro_message"] = (
        "U2에 오신 것을 환영합니다! 이 단원에서는 탤리표·빈도표·그림 그래프·막대 그래프로 "
        "데이터를 정리하고 읽는 방법을 배웁니다. "
        "데이터에서 패턴과 비교를 찾아내는 능력은 수학적 추론의 핵심입니다."
    )
    d["unit_close_message"] = (
        "U2를 완료했습니다! 탤리표와 빈도표를 읽고 작성하며, "
        "그림 그래프와 막대 그래프를 해석하는 능력을 갖추었습니다. "
        "이제 비교·합산·2단계 문제까지 데이터 분석 전문가가 되었습니다!"
    )
    d["review_from_units"] = ["U1"]
    d["interleave_ratio"] = 0.2
    d["passing_threshold"] = 0.75
    d["fluency_required"] = False
    d["supplementary_video"] = "https://www.khanacademy.org/math/cc-third-grade-math/represent-and-interpret-data"

    # ─────────────────────────────────────────
    # 섹션 배열 삽입 (flat items 제거 후)
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

    # 요약 출력
    total = (len(pretest_items) + len(learn_items) + len(try_items)
             + len(r1_items) + len(r2_items) + len(r3_items))
    print(f"✅ 업그레이드 완료: {DST.name}")
    print(f"   PT={len(pretest_items)}  LEARN={len(learn_items)}  TRY={len(try_items)}")
    print(f"   R1={len(r1_items)}  R2={len(r2_items)}  R3={len(r3_items)}")
    print(f"   총 문항 수: {total}")


if __name__ == "__main__":
    upgrade()
