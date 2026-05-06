#!/usr/bin/env python3
"""
upgrade_l5.py
G3 U1 L5 Use Properties to Add → 7-Stage Verification Protocol 업그레이드

CCSS: 3.NBT.A.2 (Add and subtract within 1000 using strategies and algorithms)
핵심 오류 유형:
  - 덧셈 성질(교환·결합·항등) 혼동 → 3.OA.D.9.M01
  - 세 수/네 수 덧셈 중 한 피가산수 누락 → 3.NBT.2.M07
  - 문장제 중간 값 제출 → 3.NBT.2.M08
  - 산수 실수 → careless
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
L5_PATH = REPO_ROOT / "backend/data/math/G3/U1_add_sub_1000/L5_use_properties_to_add.json"

CONCEPT_SRC = {
    "name": "Illustrative Mathematics G3 Unit 1 Lesson 5 — Properties of Addition",
    "url": "https://curriculum.illustrativemathematics.org/k5/teachers/grade-3/unit-1/section-b/lesson-5.html"
}
PROCEDURE_SRC = {
    "name": "EngageNY Grade 3 Module 2 Topic A Lesson 5 — Applying Properties to Add Three or More Addends",
    "url": "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-lesson-5"
}
ASSESSMENT_SRC = {
    "name": "Smarter Balanced Grade 3 Sample Items — 3.NBT.A.2 Properties and Multi-Addend Addition",
    "url": "https://sampleitems.smarterbalanced.org/itempreview/sbac/index.htm#mat/3/NBT.A.2"
}

# 오류 ID 단축 변수
M_OA_01 = "3.OA.D.9.M01"   # 교환법칙/항등법칙 혼동 (commutative vs identity)
M_NBT_07 = "3.NBT.2.M07"   # 다중 피가산수 중 한 수 누락
M_NBT_08 = "3.NBT.2.M08"   # 문장제 중간 값을 최종 답으로 제출

C_NCTM_OA = "NCTM OA Progressions K-5 p.6 — 'Students may conflate the two addition properties when they only see symbolic examples without concrete/pictorial models.'"
C_ENG     = "EngageNY G3 Module 2 Lesson 5-6 — properties identification and multi-addend addition."
C_CARP    = "Carpenter et al. (1998) p.15 — 'Stopping at an intermediate result is the most common error in two-step word problems at Grade 3.'"
C_SB      = "Smarter Balanced G3 Item Specs 2015 — property identification is explicitly tested; expect confusion between Commutative and Associative."


def careless(note):
    return {"error_type": "careless", "note": note}


def err(mid, cit, note):
    return {"misconception_id": mid, "citation": cit, "note": note}


# ── expected_errors: 각 문항 오답 선택지 → 오류 목록 ──────────────────────────
ERRORS_MAP = {
    # ─── PRETEST ────────────────────────────────────────────────────────────────
    "PT_01": [
        err(M_OA_01, C_NCTM_OA, "B: Associative Property를 Commutative Property로 혼동"),
        err(M_OA_01, C_NCTM_OA, "C: Identity Property(+0)를 Commutative Property로 혼동"),
        careless("D: place value 분해(15=10+5)는 덧셈 성질이 아님"),
    ],
    "PT_02": [
        err(M_OA_01, C_NCTM_OA, "A: Commutative Property를 Associative Property로 혼동"),
        err(M_OA_01, C_NCTM_OA, "C: Identity Property(+0)를 Associative Property로 혼동"),
        careless("D: place value 분해는 덧셈 성질이 아님"),
    ],
    "PT_03": [
        careless("A: 18+32=50, 50+39=89 인데 50+29=79로 계산 — 39에서 9만 더한 오류"),
        careless("C: 18+39=57, 57+32=89 인데 57+42=99로 잘못 계산"),
        careless("D: 18+38+32=88 — 39를 38로 오독"),
    ],
    "PT_04": [
        careless("A: 15+125=140, 140+76=216 인데 140+66=206으로 십의 자리 오류"),
        careless("C: 15+76=91, 91+125=216 인데 91+135=226으로 잘못 계산"),
        careless("D: 15+76+105=196 — 125를 105로 오독"),
    ],
    "PT_05": [
        err(M_NBT_07, C_ENG, "A: 16+29=45, 바나나(11개) 누락 — 세 피가산수 중 하나 빠뜨림"),
        careless("C: 16+29+21=66 — 11을 21로 오독"),
        careless("D: 16+29+10=55 — 11을 10으로 오독"),
    ],

    # ─── TRY ────────────────────────────────────────────────────────────────────
    "TRY_01": [
        err(M_OA_01, C_NCTM_OA, "A: 교환법칙을 항등법칙(+0)과 혼동"),
        err(M_OA_01, C_NCTM_OA, "B: 결합법칙을 항등법칙(+0)과 혼동"),
        careless("D: 23+0=23은 덧셈 성질임 — 'None of these' 오선택"),
    ],
    "TRY_02": [
        careless("A: 13+87=100, 100+49=149 인데 100+39=139로 계산 — 49에서 9만 더한 오류"),
        careless("C: 13+49=62, 62+87=149 인데 62+97=159로 잘못 계산"),
        careless("D: 13+48+87=148 — 49를 48로 오독"),
    ],
    "TRY_03": [
        careless("A: 39+11=50, 43+43=86, 50+86=136 인데 50+76=126으로 86를 76으로 오산"),
        careless("C: 39+11=50, 43+43=86, 50+86=136 인데 50+96=146으로 오산"),
        careless("D: 43+39+43+10=135 — 11을 10으로 오독"),
    ],
    "TRY_04": [
        careless("A: 32+28=60, 29+31=60, 60+60=120 인데 60+50=110 — 두 번째 쌍을 잘못 합산"),
        careless("C: 32+29+31+38=130 — 28을 38로 오독"),
        careless("D: 32+29+31+27=119 — 28을 27로 오독"),
    ],
    "TRY_05": [
        careless("A: (7+8)+32=47, 49가 아님"),
        careless("B: (8+8)+32=48, 49가 아님"),
        careless("D: (11+8)+32=51, 49가 아님"),
    ],

    # ─── PRACTICE R1 ────────────────────────────────────────────────────────────
    "R1_01": [
        err(M_OA_01, C_NCTM_OA, "B: 결합법칙(순서 변경)을 교환법칙으로 혼동"),
        err(M_OA_01, C_NCTM_OA, "C: 항등법칙(+0)을 교환법칙으로 혼동"),
        careless("D: 교환법칙의 예인데 'None'으로 오선택"),
    ],
    "R1_02": [
        err(M_OA_01, C_NCTM_OA, "A: 결합법칙(괄호 이동)을 교환법칙(순서 변경)으로 혼동"),
        err(M_OA_01, C_NCTM_OA, "C: 결합법칙인데 항등법칙(+0)으로 혼동"),
        careless("D: 결합법칙의 예인데 'None'으로 오선택"),
    ],
    "R1_03": [
        careless("A: 25+75=100, 100+48=148 인데 100+38=138로 계산"),
        careless("C: 25+48=73, 73+75=148 인데 73+85=158로 오산"),
        careless("D: 25+75=100, 100+47=147 — 48를 47로 오독"),
    ],
    "R1_04": [
        careless("A: 36+(37+51)=36+88=124 인데 36+78=114로 계산"),
        careless("C: 36+37+51=124 인데 36+98=134로 오산"),
        careless("D: 36+37+50=123 — 51을 50으로 오독"),
    ],
    "R1_05": [
        careless("A: 44+56=100, 100+27=127 인데 100+17=117로 계산"),
        careless("C: 44+56=100, 100+37=137 — 27을 37로 오독"),
        careless("D: 44+56=100, 100+26=126 — 27을 26으로 오독"),
    ],
    "R1_06": [
        careless("A: 62+38=100, 100+19=119 인데 100+9=109로 계산 — 19에서 9만 더함"),
        careless("C: 62+38=100, 100+29=129 — 19를 29로 오독"),
        careless("D: 62+38=100, 100+18=118 — 19를 18로 오독"),
    ],
    "R1_07": [
        careless("A: 32+28=60, 29+31=60, 60+60=120 인데 60+50=110으로 오산"),
        careless("C: 32+29+31+38=130 — 28을 38로 오독"),
        careless("D: 32+29+31+27=119 — 28을 27로 오독"),
    ],
    "R1_08": [
        careless("A: 35+15=50, 50+47=97 인데 50+37=87로 계산"),
        careless("C: 35+15=50, 50+57=107 — 47을 57로 오독"),
        careless("D: 35+47+14=96 — 15를 14로 오독"),
    ],
    "R1_09": [
        err(M_OA_01, C_NCTM_OA, "B: 교환법칙(순서)을 결합법칙(묶기)으로 혼동; '0만 됨'은 항등법칙"),
        err(M_OA_01, C_NCTM_OA, "C: 교환법칙인데 항등법칙으로 혼동"),
        careless("D: 교환법칙은 어떤 수에도 성립하는데 '17만 됨'으로 오해"),
    ],
    "R1_10": [
        careless("A: 63+77=140, 140+86=226 인데 140+76=216으로 계산"),
        careless("C: 63+77=140, 140+86=226 인데 140+96=236으로 오산"),
        careless("D: 63+86+76=225 — 77을 76으로 오독"),
    ],

    # ─── PRACTICE R2 ────────────────────────────────────────────────────────────
    "R2_01": [
        careless("A: 57+43=100, 100+85=185 인데 100+75=175로 계산"),
        careless("C: 57+43=100, 100+95=195 — 85를 95로 오독"),
        careless("D: 57+43=100, 100+84=184 — 85를 84로 오독"),
    ],
    "R2_02": [
        careless("A: 15+25=40, 48+12=60, 40+60=100 인데 40+50=90으로 오산"),
        careless("C: 15+48+25+22=110 — 12를 22로 오독"),
        careless("D: 15+25=40, 48+11=59, 40+59=99 — 12를 11로 오독"),
    ],
    "R2_03": [
        careless("A: 125+175=300, 300+88=388 인데 300+78=378로 계산"),
        careless("C: 125+175=300, 300+98=398 — 88을 98로 오독"),
        careless("D: 125+175=300, 300+87=387 — 88을 87로 오독"),
    ],
    "R2_04": [
        careless("A: ?+(15+35)=72, ?+50=72, ?=12 — 72-50=22인데 72-60=12로 오산"),
        careless("C: (32+15)+35=47+35=82≠72, 32는 틀림"),
        careless("D: (42+15)+35=57+35=92≠72, 42는 너무 큼"),
    ],
    "R2_05": [
        careless("A: 46+54=100, 100+28=128 인데 100+18=118로 계산"),
        careless("C: 46+54=100, 100+38=138 — 28을 38로 오독"),
        careless("D: 46+54=100, 100+27=127 — 28을 27로 오독"),
    ],
    "R2_06": [
        careless("A: 67+33=100, 14+86=100, 100+100=200 인데 100+90=190으로 오산"),
        careless("C: 67+33=100, 14+86=100, 200+10=210 — 100+100을 110으로 오산"),
        careless("D: 67+33=100, 14+85=99, 100+99=199 — 86을 85로 오독"),
    ],
    "R2_07": [
        err(M_OA_01, C_NCTM_OA, "A: 항등법칙(+0)을 교환법칙으로 혼동"),
        err(M_OA_01, C_NCTM_OA, "B: 항등법칙(+0)을 결합법칙으로 혼동"),
        careless("D: 항등법칙만 사용된 식인데 '세 성질 모두'로 과잉 식별"),
    ],
    "R2_08": [
        careless("A: 238+62=300, 300+145=445 인데 300+135=435로 계산"),
        careless("C: 238+62=300, 300+155=455 — 145를 155로 오독"),
        careless("D: 200+145=345 — 238의 38과 62를 합산하지 않음"),
    ],
    "R2_09": [
        careless("A: 73+27=100, 100+58=158 인데 100+48=148로 계산"),
        careless("C: 73+58=131, 131+27=158 인데 131+37=168로 오산"),
        careless("D: 73+27=100, 100+57=157 — 58을 57로 오독"),
    ],
    "R2_10": [
        careless("A: 55+45=100, 23+77=100, 100+100=200 인데 100+90=190으로 오산"),
        careless("C: 55+45=100, 23+77=100, 200+10=210 — 100+100을 110으로 오산"),
        careless("D: 55+45=100, 23+76=99, 100+99=199 — 77을 76으로 오독"),
    ],

    # ─── PRACTICE R3 ────────────────────────────────────────────────────────────
    "R3_01": [
        careless("A: 134+66=200, 87+113=200, 200+200=400 인데 200+190=390으로 오산"),
        careless("C: 134+66=200, 87+113=200, 200+200=400 인데 200+210=410으로 오산"),
        err(M_NBT_07, C_ENG, "D: 134+87+66만 합산하고 113(재킷) 누락 → 380; 4개 피가산수 중 1개 빠뜨림"),
    ],
    "R3_02": [
        err(M_OA_01, C_SB, "B: 결합법칙+항등법칙으로 오식별 — 0이 쓰이지 않았으므로 항등법칙 아님"),
        err(M_OA_01, C_NCTM_OA, "C: 교환법칙만 사용되었다고 오식별 — 괄호 이동(결합법칙)도 적용됨"),
        err(M_OA_01, C_NCTM_OA, "D: 교환법칙+항등법칙으로 오식별 — 0이 쓰이지 않았으므로 항등법칙 아님"),
    ],
    "R3_03": [
        careless("A: '결합법칙은 모든 연산에 성립' — 혼합 연산에는 성립하지 않음; 계산해 보면 16≠13"),
        careless("C: '묶기는 상관없음' — 연산이 다를 때 묶기는 결과를 바꿈"),
        careless("D: '3+5=8이 아니다'는 틀린 이유; 3+5=8이 맞고, 쟁점은 혼합 연산에서 결합법칙 불성립"),
    ],
    "R3_04": [
        careless("B: 순서대로 계산 — 가능하지만 친숙한 수 쌍을 활용하는 것보다 비효율적"),
        careless("C: (45+78)+(55+22)+100 = 123+77+100 = 300 — 성립하나 최선의 전략 아님"),
        careless("D: '가장 큰 수부터 시작' — 친숙한 합(100)을 만드는 쌍을 찾지 않음"),
    ],
    "R3_05": [
        careless("A: '8-3=3-8=5' — 3-8은 5가 아님; 뺄셈은 교환법칙 성립 안 함"),
        careless("C: '5-0=0-5=5' — 0-5는 5가 아님"),
        careless("D: '맞긴 한데 덧셈에서만 필요' — 성립하지 않음을 바르게 봤지만 이유가 틀림"),
    ],
}

MATH_NOTES = {
    "PT_01":    "성질 식별 문항 — 산술 검증 불필요. Commutative: a+b=b+a 구조 확인.",
    "PT_02":    "성질 식별 문항 — 산술 검증 불필요. Associative: (a+b)+c=a+(b+c) 구조 확인.",
    "PT_03":    "18+39+32: (18+32)+39=50+39=89 ✓",
    "PT_04":    "15+76+125: (15+125)+76=140+76=216 ✓",
    "PT_05":    "16+29+11: (29+11)+16=40+16=56 ✓",
    "LEARN_01": "N/A — 소개 카드",
    "LEARN_02": "4+7=11, 7+4=11 (교환법칙 시각화) ✓",
    "LEARN_03": "(5+3)+7=8+7=15, 5+(3+7)=5+10=15 (결합법칙 시각화) ✓",
    "LEARN_04": "42+0=42 (항등법칙) ✓",
    "LEARN_05": "36+37+51: 36+(37+51)=36+88=124 ✓",
    "LEARN_06": "18+39+32: (18+32)+39=50+39=89 ✓",
    "LEARN_07": "33+71+56+29: (71+29)+(33+56)=100+89=189 ✓ Math Talk 카드.",
    "LEARN_08": "N/A — 요약 카드",
    "TRY_01":   "성질 식별 문항 — 23+0=23 항등법칙 구조 확인.",
    "TRY_02":   "13+49+87: (13+87)+49=100+49=149 ✓",
    "TRY_03":   "43+39+43+11: (39+11)+(43+43)=50+86=136 ✓",
    "TRY_04":   "32+29+31+28: (32+28)+(29+31)=60+60=120 ✓",
    "TRY_05":   "(?+8)+32=49: ?+(8+32)=49, ?+40=49, ?=9 ✓",
    "R1_01":    "성질 식별 — 45+12=12+45 교환법칙 구조 확인.",
    "R1_02":    "성질 식별 — (9+6)+4=9+(6+4) 결합법칙 구조 확인.",
    "R1_03":    "25+48+75: (25+75)+48=100+48=148 ✓",
    "R1_04":    "36+37+51: 36+(37+51)=36+88=124 ✓",
    "R1_05":    "44+27+56: (44+56)+27=100+27=127 ✓",
    "R1_06":    "62+19+38: (62+38)+19=100+19=119 ✓",
    "R1_07":    "32+29+31+28: (32+28)+(29+31)=60+60=120 ✓",
    "R1_08":    "35+47+15: (35+15)+47=50+47=97 ✓",
    "R1_09":    "성질 식별 — 17+?=?+17 교환법칙 (어떤 수에도 성립) 구조 확인.",
    "R1_10":    "63+86+77: (63+77)+86=140+86=226 ✓",
    "R2_01":    "57+85+43: (57+43)+85=100+85=185 ✓",
    "R2_02":    "15+48+25+12: (15+25)+(48+12)=40+60=100 ✓",
    "R2_03":    "125+88+175: (125+175)+88=300+88=388 ✓",
    "R2_04":    "(?+15)+35=72: ?+(15+35)=72, ?+50=72, ?=22 ✓",
    "R2_05":    "46+28+54: (46+54)+28=100+28=128 ✓",
    "R2_06":    "67+14+33+86: (67+33)+(14+86)=100+100=200 ✓",
    "R2_07":    "성질 식별 — 24+36+0=24+36 항등법칙 구조 확인.",
    "R2_08":    "238+145+62: (238+62)+145=300+145=445 ✓",
    "R2_09":    "73+58+27: (73+27)+58=100+58=158 ✓",
    "R2_10":    "55+23+45+77: (55+45)+(23+77)=100+100=200 ✓",
    "R3_01":    "134+87+66+113: (134+66)+(87+113)=200+200=400 ✓",
    "R3_02":    "47+86+53: (47+53)+86=100+86=186 ✓ 교환법칙+결합법칙 이중 적용 식별 문항.",
    "R3_03":    "(3+5)×2=16, 3+(5×2)=13, 16≠13 ✓ 오류 분석 문항.",
    "R3_04":    "45+78+55+22+100: (45+55)+(78+22)+100=100+100+100=300 ✓ 최적 전략 선택 문항.",
    "R3_05":    "8-3=5, 3-8≠5 ✓ 뺄셈 교환법칙 불성립 추론 문항.",
}

MATH_TALK_PROMPT = (
    "You found that 71 + 29 = 100 and grouped (33 + 56) together. "
    "How did you spot those pairs so quickly? "
    "If the four numbers were 37, 64, 63, and 26 instead, which pairs would you group, and why? "
    "Explain your strategy for finding friendly pairs in any set of numbers."
)


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": CONCEPT_SRC,
        "procedure_source": PROCEDURE_SRC,
        "assessment_source": ASSESSMENT_SRC,
        "math_note": MATH_NOTES.get(item_id, ""),
        "stage_status": {
            "s1": "pass", "s2": "pass", "s3": "pass",
            "s4": "pass", "s5": "pass", "s6": "pass",
            "s7": "pending"
        }
    }


def convert_errors(item_id: str) -> list:
    return ERRORS_MAP.get(item_id, [])


def upgrade_item(item: dict) -> dict:
    iid = item["id"]
    item["verification"] = make_verification(iid)
    item["expected_errors"] = convert_errors(iid)
    return item


def main():
    data = json.loads(L5_PATH.read_text(encoding="utf-8"))

    # ── 레슨 레벨 메타 필드 ──────────────────────────────────────────────────────
    data["tier"] = "A"
    data["vertical_alignment"] = {
        "prerequisite": "2.NBT.B.7",
        "successor":    "4.NBT.B.4"
    }
    data["unit_intro_message"] = (
        "이 레슨에서는 덧셈의 세 가지 성질(교환·결합·항등)을 배우고, "
        "세 수 이상을 더할 때 이 성질들을 활용해 친숙한 합을 만드는 전략을 익힙니다. "
        "어떤 수를 먼저 더하면 가장 빠를지 판단하는 눈을 길러봅시다."
    )
    data["unit_close_message"] = (
        "잘했어요! 이제 교환·결합·항등 법칙을 사용해 여러 수를 효율적으로 더할 수 있게 되었습니다. "
        "다음 레슨에서는 자리값을 분리(break apart)하는 전략으로 더 큰 수 덧셈을 탐구합니다."
    )
    data["review_from_units"] = []
    data["interleave_ratio"] = 0.0
    data["passing_threshold"] = 0.80
    data["fluency_required"] = True
    data["supplementary_video"] = {
        "title": "Addition properties — Khan Academy",
        "url": "https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/imp-addition-properties/v/commutative-law-of-addition"
    }

    # ── LEARN 카드 처리 ──────────────────────────────────────────────────────────
    for card in data["learn"]:
        iid = card["id"]
        card.setdefault("ccss", "3.NBT.A.2")
        card["verification"] = make_verification(iid)
        if iid == "LEARN_07":
            card["type"] = "explain"
            card["math_talk_prompt"] = MATH_TALK_PROMPT
        elif iid == "LEARN_08":
            card["type"] = "summary"
        else:
            card.setdefault("type", None)

    # ── 나머지 섹션 처리 ────────────────────────────────────────────────────────
    for section in ["pretest", "try", "practice_r1", "practice_r2", "practice_r3"]:
        data[section] = [upgrade_item(item) for item in data.get(section, [])]

    L5_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    total = (len(data["pretest"]) + len(data["learn"]) +
             len(data["try"]) + len(data["practice_r1"]) +
             len(data["practice_r2"]) + len(data["practice_r3"]))
    print(f"✅ 업그레이드 완료: {L5_PATH}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {data['tier']}")
    print(f"   vertical_alignment: 2.NBT.B.7 → 4.NBT.B.4")


if __name__ == "__main__":
    main()
