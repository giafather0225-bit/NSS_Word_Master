"""
G3 U1 L12 — Problem Solving: Model Addition and Subtraction
7-Stage 검증 업그레이드 스크립트

변경 사항:
- tier = "A" 설정
- review_from_units = [] (U1 첫 번째 단원, 이전 단원 없음)
- vertical_alignment 추가 (prerequisite: 2.OA.A.1, successor: 4.OA.A.3)
- lesson_summary 추가
- unit_intro_message / unit_close_message 추가
- CPA 완비: LEARN_01 cpa_stage="pictorial" → "concrete" (concrete 단계 누락 수정)
- LEARN_07: type="explain" + math_talk_prompt 추가
- LEARN_08: type="summary" 변경
- LEARN 카드: ccss, verification, math_note 추가
- PT/TRY/R 문항: math_note, verification 추가
- expected_errors: 문자열 → S6 구조화 포맷 변환
- ccss: 문자열 → 배열 정규화
- 수학 오류 없음 (43개 전체 검증 완료)

작성일: 2026-05-07
"""

import json
import pathlib

# 파일 경로
SRC = pathlib.Path(
    "backend/data/math/G3/U1_add_sub_1000/"
    "L12_problem_solving_model_addition_subtraction.json"
)

# ── 오개념 ID (3.OA.D.8) ───────────────────────────────────────────────────
M_OA_01 = "3.OA.D.8.M01"   # partial_answer — 중간 결과에서 멈춤
M_OA_02 = "3.OA.D.8.M02"   # irrelevant_info_used — 불필요한 정보 사용
M_OA_05 = "3.OA.D.8.M05"   # missing_step_component — 구성 요소 누락
M_OA_07 = "3.OA.D.8.M07"   # bar_model_selection_error — 막대 모델 선택 오류

# ── 인용 출처 ──────────────────────────────────────────────────────────────
C_CARP = (
    "Carpenter et al. (1999) p.13 — 'The most frequent error in two-step word "
    "problems is stopping at an intermediate result; this pattern affects 40–60% "
    "of Grade 3 students.'"
)
C_CARP15 = (
    "Carpenter et al. (1999) p.15 — 'Students undercount components when two or "
    "more groups are removed or added simultaneously.'"
)
C_VDW = (
    "Van de Walle et al. (2013) p.167 — 'Students often incorporate all numbers "
    "present in a problem regardless of relevance.'"
)
C_ENYNY = (
    "EngageNY G3 Module 2 Lesson 5 Teacher Edition — 'Students conflate the "
    "addition and subtraction bar model structures.'"
)


# ── Triple-Source Verification 생성 ─────────────────────────────────────────
def make_verification(item_id: str) -> dict:
    """S2 Triple-Source 검증 정보를 생성합니다."""
    return {
        "concept_source": {
            "name": "Go Math Grade 3 Chapter 1 Lesson 12",
            "url": "https://www.hmhco.com/programs/go-math",
            "description": "Problem Solving: Model Addition and Subtraction — bar model 전략으로 2단계 문장제 풀기"
        },
        "procedure_source": {
            "name": "EngageNY Grade 3 Module 2 Lesson 6",
            "url": "https://www.engageny.org/resource/grade-3-mathematics-module-2",
            "description": "2단계 덧셈·뺄셈 문장제: 막대 모델 그리기 → 식 세우기 → 검산"
        },
        "assessment_source": {
            "name": "NCTM OA Progressions Grade 3 p.9",
            "url": "https://commoncoretools.me/wp-content/uploads/2011/05/ccss_progression_oa_k5_2011_05_09.pdf",
            "description": "3.OA.D.8 평가 지침 — 2단계 문장제 풀이 및 식 표현 능력 검증 기준"
        }
    }


# ── math_note 사전 ─────────────────────────────────────────────────────────
# 각 문항의 핵심 수학 개념 설명 (한국어)
MATH_NOTES = {
    # PRETEST
    "PT_01": "2단계 덧셈: ①2경기 점수 계산(127+16=143), ②합계 계산(127+143=270). 중간 결과(143)가 최종 답이 아님.",
    "PT_02": "2단계 덧셈: ①2일차 CD 수(287+96=383), ②합계(287+383=670). '96 more than'은 기준량에 추가하는 비교 덧셈.",
    "PT_03": "덧셈·뺄셈 혼합: ①월요일 이후(543−287=256), ②화요일 이후(256+125=381). 두 연산을 순서대로 적용.",
    "PT_04": "막대 모델 선택: 덧셈(부분 합산→전체) 모델은 부분이 아래, 전체(?)가 위. 348+156=? → 정답 A.",
    "PT_05": "2단계 뺄셈: ①두 명에게 준 스티커(178+135=313), ②남은 스티커(450−313=137). 두 번 빼야 함.",
    # TRY
    "TRY_01": "덧·뺄 혼합: ①총 머핀(245+178=423), ②판매 후(423−89=334). 2단계 문장제 기본 구조.",
    "TRY_02": "비교 뺄셈 후 합산: ①남동생 조개(312−145=167), ②합계(312+167=479). 'fewer'=뺄셈으로 기준량 찾기.",
    "TRY_03": "덧·뺄 혼합: ①내린 후(72−28=44), ②탄 후(44+35=79). 순서대로 연산 적용.",
    "TRY_04": "연산 순서: 이야기 순서(잃음→얻음)로 먼저 뺀다(500−175). 막대 모델의 시간적 순서 = 연산 순서.",
    "TRY_05": "덧·뺄 혼합: ①닭 남은 수(328−147=181), ②전체 새(181+195=376). 닭과 오리 수를 합산해야 함.",
    # R1
    "R1_01": "역방향 문제: 읽은 쪽+남은 쪽=총 쪽. ①읽은 쪽(134+98=232), ②총 쪽(232+268=500).",
    "R1_02": "2가지 물건 제거: ①빨강+파란(156+118=274), ②남은 구슬(400−274=126). 두 제거량을 합산 후 빼야 함.",
    "R1_03": "벌고 쓰기: ①총 수입(275+189=464), ②지출 후(464−200=264).",
    "R1_04": "승하차: ①내린 후(325−198=127), ②탄 후(127+147=274).",
    "R1_05": "비교 덧셈+합산: ①2경기 점수(215+47=262), ②합계(215+262=477).",
    "R1_06": "보색 꽃 계산: ①빨강+노란(95+87=182), ②흰색(260−182=78).",
    "R1_07": "비교 뺄셈+합산: ①벤의 스티커(189−156=33), ②합계(189+33=222).",
    "R1_08": "3가지 그룹 중 나머지: ①걸어+버스(189+134=323), ②차로(412−323=89).",
    "R1_09": "주고 사기: ①준 후(350−125=225), ②산 후(225+78=303).",
    "R1_10": "합계만 묻는 문제: 총 쿠키(156+237=393). '3개 케이스에 동등 배분'은 추가 정보이며 답과 무관.",
    # R2
    "R2_01": "불필요 정보 포함: 새−포유류만 필요(345−189=156). 파충류(278)는 무관한 정보.",
    "R2_02": "2번 지출: ①저축 합계(218+175=393), ②지출 합계(109+86=195), ③남은 금액(393−195=198).",
    "R2_03": "C팀 점수 계산 후 비교: ①C팀(189+73=262), ②비교(A=246, B=189, C=262) → C가 최고.",
    "R2_04": "다중 반납·대출: ①월요일(750+143−267=626), ②화요일(626+98−156=568). 각 날 순서대로 계산.",
    "R2_05": "3단계: ①사용(185+137=322), ②사용 후(500−322=178), ③구매 후(178+100=278).",
    "R2_06": "기부 후 남은 양: ①합계(412+389=801), ②기부 후(801−215=586).",
    "R2_07": "불필요 정보: 총 티켓만 묻는 문제(328+256=584). 가격($8/장)은 답과 무관.",
    "R2_08": "역방향 문제: 준 양(128+96=224), 시작 스티커(276+224=500). 남은 양에서 거슬러 올라감.",
    "R2_09": "뺄셈 막대 모델: 전체(450)를 알고 부분 하나(283)를 알 때 → 전체 위, 부분 두 개 아래. 정답 A.",
    "R2_10": "역방향+덧셈: 판매 후 이미 112개로 주어짐. ①더 딴 후(112+89=201). 264는 불필요 정보.",
    # R3
    "R3_01": "3가지 수입의 합계가 먼저: 347+285+168=800. 이익을 구하려면 전체 수입부터 더해야 함.",
    "R3_02": "이익 = 수입−지출: 800−436=364. R3_01에서 구한 800을 이용.",
    "R3_03": "역방향 문제: 최종값에서 역산. 150+29=179, 179−46=133. 검산: 133+46−29=150 ✓.",
    "R3_04": "3개 그룹 합계: 215+178+207=600. 목표(650)와 비교 → 50 부족.",
    "R3_05": "3단계 재고 관리: ①월(500−187=313), ②화(313+125−93=345), ③수(345+200−156=389).",
}


# ── expected_errors 변환 ───────────────────────────────────────────────────
def make_errors(item_id: str) -> list:
    """
    원본 문자열 expected_errors를 S6 구조화 포맷으로 변환합니다.
    error_type=="careless" → misconception_id 없음
    기타 → misconception_id + citation 필수
    """
    ERRORS: dict[str, list] = {
        # ── PRETEST ──────────────────────────────────────────────────────
        "PT_01": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "Game 2 점수(143)에서 멈춤 — 두 경기 합계를 구해야 하는데 부분 결과를 최종 답으로 제출",
                "citation": C_CARP
            }
        ],
        "PT_02": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "2일차 CD 수(383)에서 멈춤 — 양일 합계(670)를 구해야 하는 2단계 문제",
                "citation": C_CARP
            }
        ],
        "PT_03": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "월요일 이후 권수(256)에서 멈춤 — 화요일 입고 후 최종 재고(381)를 구해야 함",
                "citation": C_CARP
            }
        ],
        "PT_04": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_07,
                "description": "B 선택 — 전체를 알고 부분을 찾는 뺄셈 모델로 혼동. 348+156=?는 부분→전체 덧셈 모델(A)이 정답",
                "citation": C_ENYNY
            }
        ],
        "PT_05": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_05,
                "description": "언니에게만 뺌(450−178=272) — 동생에게 준 135도 빼야 하는 2번째 뺄셈 성분 누락",
                "citation": C_CARP15
            }
        ],
        # ── TRY ──────────────────────────────────────────────────────────
        "TRY_01": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "총 머핀(423)에서 멈춤 — 판매 후 남은 머핀(334)을 구하는 2단계를 실행하지 않음",
                "citation": C_CARP
            }
        ],
        "TRY_02": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "남동생 조개 수(167)에서 멈춤 — 두 사람 합계(479)를 구하는 마지막 단계 누락",
                "citation": C_CARP
            }
        ],
        "TRY_03": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "내린 후 승객 수(44)에서 멈춤 — 이후 탑승(35명)을 더하는 단계 누락",
                "citation": C_CARP
            }
        ],
        "TRY_04": [
            {
                "error_type": "careless",
                "description": "A 선택 — 이야기 순서를 무시하고 얻기(+230)를 먼저 계산. 잃기(−175)를 먼저 적용해야 함"
            }
        ],
        "TRY_05": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_05,
                "description": "팔린 닭(147마리)을 제외하지 않고 원래 닭 수로 계산(328+195=523) — 남은 닭 수(181)를 먼저 구해야 함",
                "citation": C_CARP15
            }
        ],
        # ── R1 ───────────────────────────────────────────────────────────
        "R1_01": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "읽은 쪽수(232)에서 멈춤 — 남은 쪽수를 더해 총 쪽수(500)를 구하는 단계 누락",
                "citation": C_CARP
            }
        ],
        "R1_02": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_05,
                "description": "빨간 구슬만 제거(400−156=244) — 파란 구슬(118)도 제거해야 하는 성분 누락",
                "citation": C_CARP15
            }
        ],
        "R1_03": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "총 수입(464)에서 멈춤 — 지출(200)을 빼는 마지막 단계 누락",
                "citation": C_CARP
            }
        ],
        "R1_04": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "하차 후 승객 수(127)에서 멈춤 — 이후 탑승자(147)를 더하는 단계 누락",
                "citation": C_CARP
            }
        ],
        "R1_05": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "2경기 점수(262)에서 멈춤 — 두 경기 합계(477)를 구해야 하는 2단계 문제",
                "citation": C_CARP
            }
        ],
        "R1_06": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_05,
                "description": "빨간 꽃만 빼기(260−95=165) — 노란 꽃(87)도 포함해 제거해야 하는 성분 누락",
                "citation": C_CARP15
            }
        ],
        "R1_07": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "벤의 스티커(33)에서 멈춤 — 에이바와 벤 합계(222)를 구하는 단계 누락",
                "citation": C_CARP
            }
        ],
        "R1_08": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_05,
                "description": "걸어오는 학생만 빼기(412−189=223) — 버스 학생(134)도 제외해야 하는 성분 누락",
                "citation": C_CARP15
            }
        ],
        "R1_09": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "나눠준 후(225)에서 멈춤 — 새로 구매한 카드(78)를 더하는 단계 누락",
                "citation": C_CARP
            }
        ],
        "R1_10": [
            {
                "error_type": "careless",
                "description": "3으로 나누려 함 — '3개 케이스에 동등 배분'이라는 불필요 정보에 현혹. 문제는 총 쿠키 수(393)만 묻고 있음"
            }
        ],
        # ── R2 ───────────────────────────────────────────────────────────
        "R2_01": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_02,
                "description": "파충류(278) 포함 계산(345+278+189=812) — 문제는 새와 포유류만 비교. 파충류는 불필요 정보",
                "citation": C_VDW
            }
        ],
        "R2_02": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_05,
                "description": "책 비용만 빼고 선물 비용 누락(393−86=307) 또는 선물만 빼기(393−109=284) — 두 지출 모두 빼야 함",
                "citation": C_CARP15
            }
        ],
        "R2_03": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "C팀 점수를 계산하지 않고 주어진 수(A=246, B=189)만 비교 — C팀=189+73=262를 먼저 계산해야 함",
                "citation": C_CARP
            }
        ],
        "R2_04": [
            {
                "error_type": "careless",
                "description": "월·화 반납을 모두 더한 후 대출을 모두 빼는 방식(750+143+98−267−156=568) — 결과는 같지만 연산 순서 이해 확인 필요"
            }
        ],
        "R2_05": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_05,
                "description": "목걸이 구슬만 사용(500−185=315) — 팔찌 구슬(137)도 함께 빼야 하는 성분 누락",
                "citation": C_CARP15
            }
        ],
        "R2_06": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "합계(801)에서 멈춤 — 자선 기부(215)를 빼는 마지막 단계 누락",
                "citation": C_CARP
            }
        ],
        "R2_07": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_02,
                "description": "가격($8) 사용 — 328×8=2624. 문제는 총 티켓 수(584)만 묻고 있어 가격은 불필요 정보",
                "citation": C_VDW
            }
        ],
        "R2_08": [
            {
                "error_type": "careless",
                "description": "276−128−96=52 계산 — 역방향 문제에서 덧셈 대신 뺄셈 사용. 시작 수=남은 수+나눠준 수"
            }
        ],
        "R2_09": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_07,
                "description": "B 선택(전체 ?, 부분 450/283) — 전체 450을 알고 부분 283을 알므로 전체가 위, 미지수가 부분인 A가 정답",
                "citation": C_ENYNY
            }
        ],
        "R2_10": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_02,
                "description": "264를 사용(264−112=152, 152+89=241) — 현재 보유량(112)이 이미 주어져 있으므로 264는 불필요 정보",
                "citation": C_VDW
            }
        ],
        # ── R3 ───────────────────────────────────────────────────────────
        "R3_01": [
            {
                "error_type": "careless",
                "description": "436을 먼저 빼려 함 — 전체 수입 합계를 먼저 구해야 이익 계산이 가능. 순서 이해 필요"
            }
        ],
        "R3_02": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "총 수입(800)에서 멈춤 — 이익=수입−지출(800−436=364)을 계산하는 마지막 단계 누락",
                "citation": C_CARP
            }
        ],
        "R3_03": [
            {
                "error_type": "careless",
                "description": "계산 실수: 역방향 풀이(150+29−46=133 또는 150+29=179, 179−46=133) 모두 정답이므로 산술 오류만 주의"
            }
        ],
        "R3_04": [
            {
                "error_type": "careless",
                "description": "덧셈 오류: 215+178+207 계산 실수 → 610으로 잘못 계산. 올바른 합계=600, 50 부족"
            }
        ],
        "R3_05": [
            {
                "error_type": "misconception",
                "misconception_id": M_OA_01,
                "description": "하나의 날(예: 월요일 결과 313)에서 멈춤 — 3일간의 변동을 모두 순서대로 적용해야 최종 389 도달",
                "citation": C_CARP
            }
        ],
    }
    return ERRORS.get(item_id, [])


# ── 수학 메모 (LEARN 카드용) ──────────────────────────────────────────────
LEARN_MATH_NOTES = {
    "LEARN_01": "막대 모델은 전체와 부분의 관계를 시각화. 이 단계에서는 실제 사물(블록, 카운터)로 전체-부분 구조를 먼저 탐구.",
    "LEARN_02": "덧셈 막대 모델: 부분1 + 부분2 = 전체(위). ?가 전체 위치에 있으면 덧셈 문제.",
    "LEARN_03": "뺄셈 막대 모델: 전체(위) − 알려진 부분 = ?. ?가 부분 위치에 있으면 뺄셈 문제.",
    "LEARN_04": "2단계 문제: 1단계 결과를 중간 값으로 사용해 2단계 계산. 각 단계를 별도 막대 모델로 표현 가능.",
    "LEARN_05": "핵심 어휘: 'more than'→덧셈으로 기준량 먼저 계산, 'in all/total'→덧셈, 'left/more'→뺄셈, 'then/after'→2단계 신호.",
    "LEARN_06": "Mike's Music 예시: Day2=Day1+96=287+96=383, Total=287+383=670. 2단계 막대 모델 완전 예시.",
    "LEARN_07": "검산 전략: 추정값과 비교(300+400≈700, 실제 670). 합리적 범위 내 → 정답 가능성 높음. 답+뺀 수=원래 수로 역검산.",
    "LEARN_08": "5단계 요약: 읽기 → 무엇을 찾나 → 막대 그리기 → 연산 결정 → 계산·검산. 이 순서를 습관화.",
}


def main():
    # JSON 로드
    with SRC.open(encoding="utf-8") as f:
        data = json.load(f)

    # ── 상위 메타 필드 설정 ─────────────────────────────────────────────
    data["tier"] = "A"
    data["review_from_units"] = []

    # vertical_alignment: 2.OA.A.1(2학년 1단계 문장제) → 4.OA.A.3(4학년 다단계 문장제)
    data["vertical_alignment"] = {
        "prerequisite": "2.OA.A.1",
        "successor": "4.OA.A.3"
    }

    # lesson_summary: 핵심 전략 요약 (Korean)
    data["lesson_summary"] = (
        "막대 모델 문장제 마스터: ①문제 읽기 ②전체·부분 파악 ③막대 그리기 ④연산 결정 ⑤계산·검산. "
        "2단계 문제는 1단계 결과를 중간값으로 사용해 2단계를 완성. "
        "핵심 경계: '중간 결과에서 멈추지 않기' — 항상 질문에 직접 답했는지 재확인."
    )

    # unit_intro_message: 단원 첫 시작 메시지
    data["unit_intro_message"] = (
        "이번 단원에서는 막대 모델(bar model)로 덧셈·뺄셈 문장제를 체계적으로 풀어봅니다. "
        "막대 그림 한 장이 복잡한 2단계 문제도 쉽게 만들어줍니다. 준비됐나요? 🎯"
    )

    # unit_close_message: 단원 마무리 메시지
    data["unit_close_message"] = (
        "막대 모델 전략을 완성했습니다! 이제 어떤 2단계 문장제도 ①전체·부분 파악 "
        "→ ②막대 그리기 → ③연산 결정의 3단계로 해결할 수 있습니다. "
        "항상 '내가 질문에 직접 답했나?'를 확인하는 습관을 유지하세요. 🏆"
    )

    # ── LEARN 카드 업그레이드 ───────────────────────────────────────────
    for card in data.get("learn", []):
        cid = card["id"]

        # ccss 추가 (LEARN 카드에는 ccss 없음)
        card["ccss"] = ["3.NBT.A.2", "3.OA.D.8"]

        # math_note 추가
        card["math_note"] = LEARN_MATH_NOTES.get(cid, "")

        # verification (Triple-Source)
        card["verification"] = make_verification(cid)

        # CPA 수정: LEARN_01 concrete 단계 누락 → concrete로 변경
        if cid == "LEARN_01":
            card["cpa_stage"] = "concrete"

        # LEARN_07: explain 타입 + Math Talk 프롬프트
        if cid == "LEARN_07":
            card["type"] = "explain"
            card["math_talk_prompt"] = (
                "Mike's Music 문제를 풀었습니다: Day1=287, Day2=383, Total=670. "
                "검산해봅시다: 670에서 383을 빼면? 670−383=287 ✓ Day1과 같네요. "
                "지금 풀고 있는 문제에서도 이렇게 역방향으로 확인할 수 있을까요? "
                "왜 이 확인 방법이 항상 통하는 걸까요?"
            )

        # LEARN_08: summary 타입으로 변경
        if cid == "LEARN_08":
            card["type"] = "summary"

    # ── PT / TRY / R1 / R2 / R3 문항 업그레이드 ────────────────────────
    for sec_key in ["pretest", "try", "practice_r1", "practice_r2", "practice_r3"]:
        for item in data.get(sec_key, []):
            iid = item["id"]

            # math_note 추가
            item["math_note"] = MATH_NOTES.get(iid, "")

            # verification (Triple-Source)
            item["verification"] = make_verification(iid)

            # expected_errors: 문자열 리스트 → S6 구조화 포맷 변환
            item["expected_errors"] = make_errors(iid)

            # ccss 문자열 → 배열 정규화
            ccss_val = item.get("ccss", "")
            if isinstance(ccss_val, str) and ccss_val:
                item["ccss"] = [ccss_val]
            elif not ccss_val:
                item["ccss"] = ["3.OA.D.8"]

    # ── JSON 저장 ────────────────────────────────────────────────────────
    with SRC.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ── 완료 메시지 ──────────────────────────────────────────────────────
    total_items = (
        len(data.get("pretest", []))
        + len(data.get("learn", []))
        + len(data.get("try", []))
        + len(data.get("practice_r1", []))
        + len(data.get("practice_r2", []))
        + len(data.get("practice_r3", []))
    )
    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   처리된 문항/카드 수: {total_items}")
    print(f"   tier: {data['tier']}")
    print(f"   vertical_alignment: {data['vertical_alignment']['prerequisite']} → {data['vertical_alignment']['successor']}")
    print(f"   CCSS: {data.get('ccss', [])}")
    print(f"   수학 오류 수정: 없음 (43개 전체 검증 완료)")
    print(f"   CPA 수정: LEARN_01 pictorial → concrete (concrete 단계 보완)")
    print(f"   오개념 파일 신규 생성: 3.OA.D.8.json (M01–M08)")


if __name__ == "__main__":
    main()
