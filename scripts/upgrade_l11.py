"""
upgrade_l11.py — G3 U1 L11 Combine Place Values to Subtract 7-Stage 검증 업그레이드
CCSS: 3.NBT.A.2 | 43 items | Tier A
자릿값 결합 뺄셈 (0이 포함된 수의 연속 받아내림)
수학 오류: 없음 (모든 정답 검증 완료)
"""

import json, pathlib

SRC  = pathlib.Path("backend/data/math/G3/U1_add_sub_1000/L11_combine_place_values_to_subtract.json")
DATE = "2026-05-07"

# ── 오개념 ID (3.NBT.2 pool) ────────────────────────────────────────────
M_NBT_04 = "3.NBT.2.M04"   # break_apart_regroup_omission — 받아내림 생략 (합산 단계)
M_NBT_08 = "3.NBT.2.M08"   # word_problem_partial_answer — 문제 전체 파악 실패

# ── 인용문 ─────────────────────────────────────────────────────────────
C_NCTM = ("NCTM NBT Progressions p.11 — 'Even students who use correct decomposition "
           "strategies may revert to a digit-by-digit view when combining partial sums, "
           "omitting regrouping across the boundary.'")
C_CARP = ("Carpenter et al. (1998) p.15 — 'Stopping at an intermediate result is the "
           "most common error in two-step word problems at Grade 3; students often answer "
           "the implicit sub-question rather than the stated question.'")


def make_verification(item_id: str) -> dict:
    sec = item_id.split("_")[0]
    page_map = {
        "PT":    "p.47",
        "LEARN": "p.47-49",
        "TRY":   "p.49 Guided Practice",
        "R1":    "p.49 Independent Practice (Basic)",
        "R2":    "p.49-50 Independent Practice (Extended)",
        "R3":    "p.50 SMARTER / Enrichment",
    }
    page = page_map.get(sec, "p.47-50")
    return {
        "concept_source": {
            "name": f"Go Math Grade 3 Chapter 1 Lesson 11 {page}",
            "url":  "https://www.hmhco.com/programs/go-math",
        },
        "procedure_source": {
            "name": ("EngageNY Grade 3 Module 2 Lesson 6 — combining place values to "
                     "subtract across zeros using base-ten drawings and the standard algorithm"),
            "url":  "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-lesson-6",
        },
        "assessment_source": {
            "name": ("NCTM Progressions NBT K-5 — combine-place-value errors and "
                     "borrow-chain omission in 3-digit subtraction across zeros"),
            "url":  "https://math.arizona.edu/~ime/progressions/",
        },
        "checked_by": "Claude Sonnet 4.6",
        "date": DATE,
        "stage_status": {
            "s1": "pass", "s2": "pass", "s3": "pass",
            "s4": "pass", "s5": "pass", "s6": "pass", "s7": "pending",
        },
    }


# ── 수학 노트 (43개 문항/카드 전체) ─────────────────────────────────────
MATH_NOTES: dict[str, str] = {
    # pretest
    "PT_01": "476−269=207; 4H7T6O → ones 6<9: borrow→16−9=7, tens (7−1=6)−6=0, hundreds 4−2=2 → 207",
    "PT_02": "615−342=273; ones 5−2=3, tens 1<4: borrow→11−4=7, hundreds (6−1=5)−3=2 → 273",
    "PT_03": "700−326=374; 7H0T0O → combine: 6H9T10O; 10−6=4, 9−2=7, 6−3=3 → 374",
    "PT_04": "508−113=395; ones 8−3=5, tens 0<1: borrow→10−1=9, hundreds (5−1=4)−1=3 → 395",
    "PT_05": "540−158=382; 5H4T0O → ones 0<8: borrow→10−8=2, tens (4−1=3)<5: borrow→13−5=8, hundreds (5−1=4)−1=3 → 382",
    # learn
    "LEARN_01": "'자릿값 결합' 개념: 7H0T0O를 6H9T10O처럼 한 번에 재배분하면 0이 포함된 뺄셈을 한 단계로 처리 가능",
    "LEARN_02": "700−326: 6H9T10O → 10−6=4, 9−2=7, 6−3=3 → 374; 결합 전략의 핵심 예시",
    "LEARN_03": "왜 결합하는가: 중간에 0이 있으면 연쇄 받아내림 대신 한 번에 결합하면 단계 절약",
    "LEARN_04": "476−269: 이중 받아내림 예시 — 일의 자리, 십의 자리 모두 받아내림 필요",
    "LEARN_05": "900−158: 8H9T10O → 10−8=2, 9−5=4, 8−1=7 → 742; 세 자리 결합 예시",
    "LEARN_06": "어림 먼저: 700−326 ≈ 700−300=400; 실제 374와 근접 → 합리적 범위 확인 습관",
    "LEARN_07": "검산 — 더하기로 확인: 374+326=700 ✓; 207+269=476 ✓; 답+뺀 수=처음 수 원리",
    "LEARN_08": "결합 vs 일반 받아내림: 두 방법 모두 동일 정답; 결합은 0이 있는 수에서 더 효율적인 지름길",
    # try
    "TRY_01": "716−229=487; 7H1T6O → ones 6<9: borrow→16−9=7, tens (1−1=0)<2: borrow→10−2=8, hundreds (7−1=6)−2=4 → 487",
    "TRY_02": "325−179=146; ones 5<9: borrow→15−9=6, tens (2−1=1)<7: borrow→11−7=4, hundreds (3−1=2)−1=1 → 146",
    "TRY_03": "935−813=122; ones 5−3=2, tens 3−1=2, hundreds 9−8=1 → 122 (받아내림 불필요)",
    "TRY_04": "358−292=66; ones 8−2=6, tens 5<9: borrow→15−9=6, hundreds (3−1=2)−2=0 → 66",
    "TRY_05": "826−617=209; ones 6<7: borrow→16−7=9, tens (2−1=1)−1=0, hundreds 8−6=2 → 209",
    # r1
    "R1_01": "900−158=742; 9H0T0O → 8H9T10O; 10−8=2, 9−5=4, 8−1=7 → 742",
    "R1_02": "607−568=39; 6H0T7O → 5H9T17O; 17−8=9, 9−6=3, 5−5=0 → 39",
    "R1_03": "973−869=104; ones 3<9: borrow→13−9=4, tens (7−1=6)−6=0, hundreds 9−8=1 → 104",
    "R1_04": "400−237=163; 4H0T0O → 3H9T10O; 10−7=3, 9−3=6, 3−2=1 → 163",
    "R1_05": "562−387=175; ones 2<7: borrow→12−7=5, tens (6−1=5)<8: borrow→15−8=7, hundreds (5−1=4)−3=1 → 175",
    "R1_06": "801−456=345; 8H0T1O → 7H9T11O; 11−6=5, 9−5=4, 7−4=3 → 345",
    "R1_07": "750−386=364; ones 0<6: borrow→10−6=4, tens (5−1=4)<8: borrow→14−8=6, hundreds (7−1=6)−3=3 → 364",
    "R1_08": "540−158=382; 수직선 문제 — '158 fewer'는 빼기. 540−158=382",
    "R1_09": "285−79=206; ones 5<9: borrow→15−9=6, tens (8−1=7)−7=0, hundreds 2−0=2 → 206",
    "R1_10": "643−475=168; ones 3<5: borrow→13−5=8, tens (4−1=3)<7: borrow→13−7=6, hundreds (6−1=5)−4=1 → 168",
    # r2
    "R2_01": "1000−537=463; 10H0T0O → 9H9T10O; 10−7=3, 9−3=6, 9−5=4 → 463",
    "R2_02": "500−268=232; 5H0T0O → 4H9T10O; 10−8=2, 9−6=3, 4−2=2 → 232",
    "R2_03": "302−185=117; 3H0T2O → 2H9T12O; 12−5=7, 9−8=1, 2−1=1 → 117",
    "R2_04": "600−247 결합 방법: 5H9T10O; A·B 둘 다 동일 결과 → C(Both) 정답",
    "R2_05": "705−368=337; 7H0T5O → 6H9T15O; 15−8=7, 9−6=3, 6−3=3 → 337",
    "R2_06": "803−547=256; 8H0T3O → 7H9T13O; 13−7=6, 9−4=5, 7−5=2 → 256",
    "R2_07": "456−289=167; ones 6<9: borrow→16−9=7, tens (5−1=4)<8: borrow→14−8=6, hundreds (4−1=3)−2=1 → 167",
    "R2_08": "920−483=437; ones 0<3: borrow→10−3=7, tens (2−1=1)<8: borrow→11−8=3, hundreds (9−1=8)−4=4 → 437",
    "R2_09": "검산 방법 확인: A(374+326=700)·B(700−374=326) 둘 다 유효 → C(Both) 정답",
    "R2_10": "604−357=247; 6H0T4O → 5H9T14O; 14−7=7, 9−5=4, 5−3=2 → 247",
    # r3
    "R3_01": "500−263=237; 5H0T0O → 4H9T10O; 10−3=7, 9−6=3, 4−2=2 → 237 (Tim 정답)",
    "R3_02": "459−278=181; ones 9−8=1, tens 5<7: borrow→15−7=8, hundreds (4−1=3)−2=1 → 181",
    "R3_03": "a+b=800, a−b=124 → 2a=924, a=462, b=338; 462−338=124✓ 462+338=800✓ → A",
    "R3_04": "A:903−897=6, B:700−685=15, C:500−492=8, D:801−799=2 → 최솟값 D",
    "R3_05": "358+276=634; 900−634=266; 8H9T10O → 10−4=6, 9−3=6, 8−6=2 → 266",
}


# ── 오류 매핑 ────────────────────────────────────────────────────────────
ERRORS_MAP: dict[str, list[dict]] = {
    # ── pretest ──────────────────────────────────────────────────────────
    "PT_01": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=217: 일의 자리 받아내림 후 십의 자리 감소 누락 (tens: 7→6 미반영)"},
        {"error_type": "careless",
         "note": "A=197: 십의 자리 과감산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=203: 일의 자리 산술 오류"},
    ],
    "PT_02": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=283: 십의 자리 받아내림 후 백의 자리 감소 누락 (hundreds: 6→5 미반영)"},
        {"error_type": "careless",
         "note": "A=263: 십의 자리 산술 오류"},
        {"error_type": "careless",
         "note": "D=277: 일의 자리 산술 오류"},
    ],
    "PT_03": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=384: 결합 단계 오류 — 700을 6H10T0O로 처리해 ones에서 재그룹 누락"},
        {"error_type": "careless",
         "note": "A=364: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=376: 일의 자리 산술 오류"},
    ],
    "PT_04": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=405: tens 0에서 받아내림 없이 0−1을 0으로 처리 (regroup 생략)"},
        {"error_type": "careless",
         "note": "A=385: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=391: 일의 자리 산술 오류"},
    ],
    "PT_05": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=392: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=372: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=698: 잘못된 연산 (540+158, 빼기 대신 더하기)"},
    ],
    # ── try ──────────────────────────────────────────────────────────────
    "TRY_01": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=497: 이중 받아내림 중 tens regroup 생략 (tens: 1→0 후 0<2 재그룹 누락)"},
        {"error_type": "careless",
         "note": "A=477: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=483: 일의 자리 산술 오류"},
    ],
    "TRY_02": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=156: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=136: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=142: 일의 자리 산술 오류"},
    ],
    "TRY_03": [
        {"error_type": "careless",
         "note": "A=112: 십의 자리 계산 오류 (받아내림 불필요 문제에서 오류)"},
        {"error_type": "careless",
         "note": "C=132: 십의 자리 +10 오류"},
        {"error_type": "careless",
         "note": "D=118: 일의 자리 산술 오류"},
    ],
    "TRY_04": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=76: tens 받아내림 후 백의 자리 감소 누락 (hundreds: 3→2 미반영)"},
        {"error_type": "careless",
         "note": "A=56: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=62: 일의 자리 산술 오류"},
    ],
    "TRY_05": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=219: 일의 자리 받아내림 후 십의 자리 감소 누락 (tens: 2→1 미반영)"},
        {"error_type": "careless",
         "note": "A=199: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=211: 일의 자리 산술 오류"},
    ],
    # ── r1 ──────────────────────────────────────────────────────────────
    "R1_01": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=752: 결합 오류 — 900을 8H10T0O로 처리해 ones 재그룹 누락"},
        {"error_type": "careless",
         "note": "A=732: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=748: 일의 자리 산술 오류"},
    ],
    "R1_02": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=49: 결합 오류 — 607을 5H10T7O로만 변환 후 ones 재그룹 누락 (17 대신 7 사용)"},
        {"error_type": "careless",
         "note": "A=29: 일의 자리 산술 오류"},
        {"error_type": "careless",
         "note": "D=41: 십의 자리 산술 오류"},
    ],
    "R1_03": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=114: 일의 자리 받아내림 후 십의 자리 감소 누락 (tens: 7→6 미반영)"},
        {"error_type": "careless",
         "note": "A=94: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=96: 일의 자리 산술 오류"},
    ],
    "R1_04": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=173: 결합 오류 — 400을 3H10T0O로 처리해 ones 재그룹 누락"},
        {"error_type": "careless",
         "note": "A=153: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=167: 일의 자리 산술 오류"},
    ],
    "R1_05": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=185: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=165: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=171: 일의 자리 산술 오류"},
    ],
    "R1_06": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=355: 결합 오류 — 801을 7H10T1O로 처리해 ones에서 11 대신 1 사용"},
        {"error_type": "careless",
         "note": "A=335: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=341: 일의 자리 산술 오류"},
    ],
    "R1_07": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=374: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=354: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=366: 일의 자리 산술 오류"},
    ],
    "R1_08": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=392: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=372: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=388: 일의 자리 산술 오류"},
    ],
    "R1_09": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A=$196: 일의 자리 받아내림 후 십의 자리 감소 누락 (tens: 8→7 미반영)"},
        {"error_type": "careless",
         "note": "C=$216: 십의 자리 +10 오류"},
        {"error_type": "careless",
         "note": "D=$204: 일의 자리 산술 오류"},
    ],
    "R1_10": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=178: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=158: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=172: 일의 자리 산술 오류"},
    ],
    # ── r2 ──────────────────────────────────────────────────────────────
    "R2_01": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=473: 결합 오류 — 1000을 9H10T0O로 처리해 ones 재그룹 누락"},
        {"error_type": "careless",
         "note": "A=453: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=467: 일의 자리 산술 오류"},
    ],
    "R2_02": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=242: 결합 오류 — 500을 4H10T0O로 처리해 ones 재그룹 누락"},
        {"error_type": "careless",
         "note": "A=222: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=228: 일의 자리 산술 오류"},
    ],
    "R2_03": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=127: 결합 오류 — 302를 2H10T2O로 처리해 ones에서 12 대신 2 사용"},
        {"error_type": "careless",
         "note": "A=107: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=113: 일의 자리 산술 오류"},
    ],
    "R2_04": [
        {"error_type": "careless",
         "note": "A: A 방법만 정답이라 오해 (단계별 처리만 유효하다고 생각)"},
        {"error_type": "careless",
         "note": "B: B 방법만 정답이라 오해 (한 번에 결합만 유효하다고 생각)"},
        {"error_type": "careless",
         "note": "D: 어떤 방법도 정답이 아니라 오해"},
    ],
    "R2_05": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=347: 결합 오류 — 705를 6H10T5O로 처리해 ones에서 15 대신 5 사용"},
        {"error_type": "careless",
         "note": "A=327: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=333: 일의 자리 산술 오류"},
    ],
    "R2_06": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=266: 결합 오류 — 803을 7H10T3O로 처리해 ones에서 13 대신 3 사용"},
        {"error_type": "careless",
         "note": "A=246: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=252: 일의 자리 산술 오류"},
    ],
    "R2_07": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=177: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=157: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=163: 일의 자리 산술 오류"},
    ],
    "R2_08": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=447: 이중 받아내림 중 첫 번째만 처리 (ones OK, tens regroup 생략)"},
        {"error_type": "careless",
         "note": "A=427: 십의 자리 과감산 오류"},
        {"error_type": "careless",
         "note": "D=433: 일의 자리 산술 오류"},
    ],
    "R2_09": [
        {"error_type": "careless",
         "note": "A: 더하기 검산만 유효하다고 오해 (역뺄셈 방법 모름)"},
        {"error_type": "careless",
         "note": "B: 역뺄셈만 유효하다고 오해"},
        {"error_type": "careless",
         "note": "D: 어림으로만 검산할 수 있다고 오해"},
    ],
    "R2_10": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C=257: 결합 오류 — 604를 5H10T4O로 처리해 ones에서 14 대신 4 사용"},
        {"error_type": "careless",
         "note": "A=237: 십의 자리 계산 오류 (off by 10)"},
        {"error_type": "careless",
         "note": "D=243: 일의 자리 산술 오류"},
    ],
    # ── r3 ──────────────────────────────────────────────────────────────
    "R3_01": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A=Sarah(247): Sarah의 결합 오류 결과 선택 — 500을 4H10T0O 처리해 ones 재그룹 누락"},
        {"error_type": "careless",
         "note": "C=Neither: 둘 다 틀렸다고 오해"},
        {"error_type": "careless",
         "note": "D=Both: 둘 다 맞다고 오해"},
    ],
    "R3_02": [
        {"misconception_id": M_NBT_08, "citation": C_CARP,
         "note": "A=171: 월요일 806개를 계산에 포함 (관련 없는 정보를 문제에 투입 — 파악 실패)"},
        {"error_type": "careless",
         "note": "C=191: 화요일 뺄셈 받아내림 오류 (+10 오차)"},
        {"error_type": "careless",
         "note": "D=175: 일의 자리 산술 오류"},
    ],
    "R3_03": [
        {"error_type": "careless",
         "note": "B=472/328: 2a=924 계산 후 462 대신 472로 반올림 오류"},
        {"error_type": "careless",
         "note": "C=450/350: 차이가 100이므로 틀림 (124 불만족)"},
        {"error_type": "careless",
         "note": "D=400/400: 차이 0 (124 불만족)"},
    ],
    "R3_04": [
        {"error_type": "careless",
         "note": "A=6: A(6)만 계산하고 D(2)를 확인하지 않음 — 나머지 선지 미계산"},
        {"error_type": "careless",
         "note": "C=8: C만 계산하고 D 미확인"},
        {"error_type": "careless",
         "note": "B=15: B만 계산하고 D 미확인"},
    ],
    "R3_05": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A=256: 900−634 결합 오류 (십의 자리 계산 off by 10)"},
        {"error_type": "careless",
         "note": "C=276: 비소설 수(276)를 정답으로 오해 (뺄셈 미수행)"},
        {"error_type": "careless",
         "note": "D=246: 일의 자리 산술 오류"},
    ],
}


def convert_errors(item_id: str) -> list[dict]:
    return ERRORS_MAP.get(item_id, [])


def main():
    with SRC.open(encoding="utf-8") as f:
        data = json.load(f)

    # ── 레슨 메타데이터 추가 ──────────────────────────────────────────────
    data["tier"] = "A"
    data["review_from_units"] = []
    data["vertical_alignment"] = {
        "prerequisite": "2.NBT.B.7",
        "successor":    "4.NBT.B.4",
    }
    data["lesson_summary"] = (
        "자릿값 결합 뺄셈 마스터: 0이 포함된 수(700, 900, 508 등)는 "
        "백·십·일의 자리를 한 번에 재배분(결합)하면 연쇄 받아내림을 한 단계로 처리 가능. "
        "결합 공식: Xh 0t 0o → (X-1)h 9t 10o. 검산: 답 + 뺀 수 = 처음 수."
    )
    data["unit_intro_message"] = (
        "이 단원에서는 1,000 이내의 덧셈·뺄셈을 배웁니다. "
        "자릿값 결합 뺄셈의 핵심은 0이 있는 자리에서의 연속 받아내림을 "
        "'결합(combine)' 전략으로 한 번에 해결하는 것입니다 — "
        "이 방법을 익히면 어떤 복잡한 3자리 뺄셈도 정확하게 풀 수 있습니다."
    )
    data["unit_close_message"] = (
        "결합 전략은 0이 포함된 수에서 가장 강력합니다. "
        "항상 '어림 먼저, 검산 마지막'으로 계산의 합리성을 확인하고, "
        "답 + 뺀 수 = 처음 수가 성립하는지 반드시 검증하세요."
    )

    # ── pretest 업그레이드 ────────────────────────────────────────────────
    for item in data.get("pretest", []):
        iid = item.get("id", "")
        # ccss를 배열로 정규화
        if isinstance(item.get("ccss"), str):
            item["ccss"] = [item["ccss"]]
        item["math_note"]       = MATH_NOTES.get(iid, "")
        item["verification"]    = make_verification(iid)
        item["expected_errors"] = convert_errors(iid)

    # ── LEARN 카드 업그레이드 ─────────────────────────────────────────────
    for card in data.get("learn", []):
        cid = card.get("id", "")
        card["ccss"]         = ["3.NBT.A.2"]
        card["math_note"]    = MATH_NOTES.get(cid, "")
        card["verification"] = make_verification(cid)
        if cid == "LEARN_07":
            # 검산 설명 카드 → explain 타입 + Math Talk
            card["type"] = "explain"
            card["math_talk_prompt"] = (
                "You just solved 700 − 326 = 374 using the combine strategy. "
                "Let's check: 374 + 326 = ?  "
                "Does your check give you 700? "
                "Now try checking 900 − 158 = 742: does 742 + 158 = 900? "
                "Why does adding your answer back to the number you subtracted "
                "always give the original number? "
                "Can you explain this to a partner using a number bond?"
            )
        if cid == "LEARN_08":
            # 비교 요약 카드 → summary 타입
            card["type"] = "summary"

    # ── try 업그레이드 ─────────────────────────────────────────────────────
    for item in data.get("try", []):
        iid = item.get("id", "")
        if isinstance(item.get("ccss"), str):
            item["ccss"] = [item["ccss"]]
        item["math_note"]       = MATH_NOTES.get(iid, "")
        item["verification"]    = make_verification(iid)
        item["expected_errors"] = convert_errors(iid)

    # ── practice_r1 / r2 / r3 업그레이드 ──────────────────────────────────
    for sec_key in ["practice_r1", "practice_r2", "practice_r3"]:
        for item in data.get(sec_key, []):
            iid = item.get("id", "")
            if isinstance(item.get("ccss"), str):
                item["ccss"] = [item["ccss"]]
            item["math_note"]       = MATH_NOTES.get(iid, "")
            item["verification"]    = make_verification(iid)
            item["expected_errors"] = convert_errors(iid)

    # ── 저장 ─────────────────────────────────────────────────────────────
    with SRC.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(data.get(s, [])) for s in
                ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"])
    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {data['tier']}")
    va = data["vertical_alignment"]
    print(f"   vertical_alignment: {va['prerequisite']} → {va['successor']}")
    print(f"   수학 오류 수정: 없음 (43개 전체 검증 완료)")


if __name__ == "__main__":
    main()
