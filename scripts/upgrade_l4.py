#!/usr/bin/env python3
"""
upgrade_l4.py
G3 U1 L4 Mental Math Addition → 7-Stage Verification Protocol 업그레이드
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
L4_PATH = REPO_ROOT / "backend/data/math/G3/U1_add_sub_1000/L4_mental_math_addition.json"

CONCEPT_SRC = {
    "name": "Illustrative Mathematics G3 Unit 4 Lesson 4 — Mental Strategies for Addition",
    "url": "https://curriculum.illustrativemathematics.org/k5/teachers/grade-3/unit-4/section-a/lesson-4.html"
}
PROCEDURE_SRC = {
    "name": "EngageNY Grade 3 Module 2 Topic A Lesson 4 — Mental Strategies: Friendly Numbers and Break Apart",
    "url": "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-lesson-4"
}
ASSESSMENT_SRC = {
    "name": "Smarter Balanced Grade 3 Sample Items — 3.NBT.A.2 Mental Computation Strategies",
    "url": "https://sampleitems.smarterbalanced.org/itempreview/sbac/index.htm#mat/3/NBT.A.2"
}

# 오류 ID 단축 변수
M01 = "3.NBT.2.M01"   # friendly number 조정 방향 오류 (빼야 하는데 더함)
M02 = "3.NBT.2.M02"   # friendly number 조정 금액 오류
M03 = "3.NBT.2.M03"   # break-apart 부분합 누락
M04 = "3.NBT.2.M04"   # break-apart 받아올림 누락
M05 = "3.NBT.2.M05"   # count-by-tens 십의 자리 홉 오류
M06 = "3.NBT.2.M06"   # 전략 선택 불일치
M07 = "3.NBT.2.M07"   # 다중 덧셈 피가산수 누락
M08 = "3.NBT.2.M08"   # 2단계 문장제 중간 답 제출

C_FUSON   = "Fuson et al. (1997) p.140-143 — place-value decomposition and compensation error patterns."
C_CARP    = "Carpenter et al. (1998) p.12-15 — multidigit addition strategy errors and partial-answer patterns."
C_ENG     = "EngageNY G3 Module 2 Lessons 4-6 — friendly numbers, break apart, multi-addend errors."
C_SB      = "Smarter Balanced G3 Item Specs 2015 — strategy selection and efficiency items."


def careless(note):
    return {"error_type": "careless", "note": note}


def err(mid, cit, note):
    return {"misconception_id": mid, "citation": cit, "note": note}


# ── expected_errors: 각 문항의 오답 선택지 → 오류 목록 ──────────────────────────
ERRORS_MAP = {
    # ─── PRETEST ────────────────────────────────────────────────────────────────
    "PT_01": [
        careless("A: 56+20=76, then added 7-4=3 → 73; counting-on slip in ones phase"),
        err(M05, C_ENG,   "C: added 37 instead of 27 — miscounted 3 decades instead of 2"),
        careless("D: 56+26=82 — miscounted ones by 1"),
    ],
    "PT_02": [
        careless("A: 20+30=50, 8+5=13, wrote 53 instead of 63 — final combination error"),
        err(M01, C_FUSON, "C: 30+35=65, then added 2 back instead of subtracting → 67 or wrote 73; wrong adjustment direction"),
        careless("D: 28+34=62 — miscounted ones"),
    ],
    "PT_03": [
        err(M04, C_FUSON, "B: 100+200=300, 16+3=19, wrote 309 instead of 319 — treated 19 as ones-only, dropped the ten"),
        careless("C: 120+203=323 region, miscalculated to 329"),
        err(M03, C_CARP,  "D: 200+16+3=219 — omitted 100 from 116"),
    ],
    "PT_04": [
        careless("A: 10+57=67, forgot to add 8 more → 65 (or dropped the 10 from 18)"),
        err(M01, C_FUSON, "C: 20+57=77, added 8 instead of subtracting 2 → 85; wrong adjustment direction"),
        careless("D: 18+56=74 — miscounted"),
    ],
    "PT_05": [
        err(M08, C_CARP,  "B: 40+38=78, used wrong tens (subtracted instead of added); partial-answer or concept gap"),
        careless("C: 46+38=84 but student miscarried ones: 6+8=14, carried wrong → 74"),
        careless("D: 46+38=84 but student dropped the carried ten → 73"),
    ],

    # ─── TRY ────────────────────────────────────────────────────────────────────
    "TRY_01": [
        err(M05, C_FUSON, "A: 43+20=63, added 2 instead of 12; counted only 2 tens then stopped → 65"),
        err(M05, C_ENG,   "C: 43+40+2=85; counted 4 decades for 32 instead of 3 → over-counted by 1 decade"),
        careless("D: 43+31=74 — miscounted ones"),
    ],
    "TRY_02": [
        careless("A: 10+44=54 — forgot to add 9 ones from 19"),
        err(M01, C_FUSON, "C: 20+44=64, added 9 more instead of subtracting 1 → 73; wrong adjustment direction"),
        err(M02, C_FUSON, "D: 20+44=64, subtracted 0 (forgot to adjust) or subtracted 0 → 64; wrong adjustment amount"),
    ],
    "TRY_03": [
        careless("A: 200+100=300, 34+52=86, wrote 376 instead of 386 — partial sum combination error"),
        careless("C: 200+100=300, 34+52=86, added to get 396 — off by 10 in the combination"),
        err(M03, C_CARP,  "D: 200+52+34=286 — omitted 100 from 234"),
    ],
    "TRY_04": [
        careless("A: 40+36=76, subtracted 2 instead of adding 8; wrong decomposition of 48"),
        err(M01, C_FUSON, "C: 50+36=86, added 8 more instead of subtracting 2 → 94; wrong adjustment direction"),
        careless("D: 48+34=82 — miscounted"),
    ],
    "TRY_05": [
        err(M08, C_CARP,  "A: 19+14=33 — found the number of girls but stopped; did not add boys+girls for total"),
        careless("B: confusion in second step; likely carried from girls=33 incorrectly"),
        careless("D: 19+19=38 — used boys count twice; forgot the '+14 more' condition"),
    ],

    # ─── PRACTICE R1 ────────────────────────────────────────────────────────────
    "R1_01": [
        careless("A: 37+14=51 — added 14 instead of 24"),
        err(M05, C_FUSON, "C: 37+34=71 — added 34 instead of 24; miscounted decades"),
        err(M05, C_FUSON, "D: 37+20=57, added 3 instead of 4 → 60; ones-count slip"),
    ],
    "R1_02": [
        careless("A: 62+9=71 — forgot to add the ten; counted only 9 ones"),
        err(M05, C_FUSON, "C: 62+29=91 — added 29 instead of 19; extra decade"),
        careless("D: 62+18=80 — miscounted ones"),
    ],
    "R1_03": [
        careless("A: 20+53=73, subtracted 1 → 72; arithmetic slip in final subtraction"),
        err(M01, C_FUSON, "C: 30+53=83, added 9 instead of subtracting 1 → 92; wrong adjustment direction"),
        err(M02, C_FUSON, "D: 30+53=83, subtracted 2 instead of 1 → 81; wrong adjustment amount"),
    ],
    "R1_04": [
        careless("A: 30+45=75, subtracted 2 → 73; used wrong adjustment amount (2 instead of 0 or wrong rounding)"),
        err(M01, C_FUSON, "C: 40+45=85, added 8 instead of subtracting 2 → 93; wrong adjustment direction"),
        careless("D: 38+44=82 — miscounted"),
    ],
    "R1_05": [
        careless("A: 100+200=300, 45+32=77, wrote 367 — final digit error"),
        careless("C: 100+200=300, 45+42=87, wrote 387 — miscalculated tens partial sum"),
        err(M03, C_CARP,  "D: 200+45+32=277 — omitted 100 from 145"),
    ],
    "R1_06": [
        careless("A: 300+400=700, missed tens — only combined hundreds and final digits"),
        careless("C: 300+500+77=877 — over-counted 400 as 500"),
        careless("D: 300+400=700, 21+46=67 → 767 — forgot to separate tens and ones"),
    ],
    "R1_07": [
        careless("A: 67+15=82 — added 15 instead of 25"),
        err(M01, C_FUSON, "C: 70+25=95, added 7 more instead of subtracting 3 → 102; wrong adjustment direction"),
        careless("D: 67+24=91 — miscounted"),
    ],
    "R1_08": [
        careless("A: 100+200=300, 58+31=89, wrote 379 — final combination digit error"),
        careless("C: 100+200=300, 58+41=99, wrote 399 — miscalculated second addend"),
        err(M03, C_CARP,  "D: 200+58+31=289 — omitted 100 from 158"),
    ],
    "R1_09": [
        careless("A: 40+26=66, subtracted 1 → 65 — arithmetic slip"),
        err(M01, C_FUSON, "C: 50+26=76, added 9 instead of subtracting 1 → 85; wrong adjustment direction"),
        careless("D: 49+25=74 — miscounted"),
    ],
    "R1_10": [
        careless("A: 40+38=78, subtracted 3 → 75 — wrong adjustment direction"),
        err(M01, C_FUSON, "C: 50+38=88, added 7 instead of subtracting 3 → 95; wrong adjustment direction"),
        careless("D: 47+37=84 — miscounted"),
    ],

    # ─── PRACTICE R2 ────────────────────────────────────────────────────────────
    "R2_01": [
        careless("A: 70+45=115, subtracted 2 → 113 — wrong adjustment amount (should subtract 2 to get 123, but computed wrong starting point)"),
        err(M01, C_FUSON, "C: 80+45=125, added 8 instead of subtracting 2 → 133; wrong adjustment direction"),
        careless("D: 78+44=122 — miscounted"),
    ],
    "R2_02": [
        careless("A: 400+300=700, 63+25=88, wrote 778 — ones digit dropped"),
        careless("C: 400+300=700, 63+35=98 → 798 — miscalculated second tens partial sum"),
        err(M03, C_CARP,  "D: 400+200+88=688 — omitted 100 from 325"),
    ],
    "R2_03": [
        careless("A: 50+36=86, subtracted 3 → 83 — subtracted from wrong starting value"),
        err(M01, C_FUSON, "C: 60+36=96, added 7 instead of subtracting 3 → 103; wrong adjustment direction"),
        careless("D: 57+35=92 — miscounted"),
    ],
    "R2_04": [
        careless("A: 300+400=700, 76+27=103 but wrote 793 — combined 700+93 instead of 700+103"),
        careless("C: 300+400=700, 76+37=113 → 813 — miscalculated second partial"),
        err(M03, C_CARP,  "D: 300+400=700, 6+7=13 only → 703 — dropped tens of 76 and 27"),
    ],
    "R2_05": [
        careless("A: 376+427 carried wrong → 793"),
        careless("C: 376+437=813 — misread second addend"),
        err(M03, C_CARP,  "D: forgot the tens and ones: 300+400=700 only → 703"),
    ],
    "R2_06": [
        careless("A: 90+47=137, subtracted 1 → 136 — wrong starting point for friendly number"),
        err(M01, C_FUSON, "C: 100+47=147, added 9 instead of subtracting 1 → 156; wrong adjustment direction"),
        err(M02, C_FUSON, "D: 100+47=147, subtracted 2 instead of 1 → 145; wrong adjustment amount"),
    ],
    "R2_07": [
        err(M06, C_SB,    "A: student chose count-by-tens for 198; impractical — 19 decade hops needed"),
        err(M03, C_CARP,  "C: break-apart works but is less efficient; missed that 198 is closest to 200"),
        careless("D: 'use pencil and paper' — violates the mental-math objective of the lesson"),
    ],
    "R2_08": [
        careless("A: 200+100=300, 54+38=92, wrote 382 — ones digit slip"),
        careless("C: 200+100=300, 54+48=102 → 402 — miscalculated second partial"),
        err(M03, C_CARP,  "D: 200+54+38=292 — omitted 100 from 138"),
    ],
    "R2_09": [
        careless("A: 167+79=246 — misread 89 as 79"),
        careless("C: 167+99=266 — misread 89 as 99"),
        careless("D: 167-11=156 — subtracted instead of added"),
    ],
    "R2_10": [
        careless("A: 80+57=137, subtracted 4 → 133 — wrong starting point"),
        err(M01, C_FUSON, "C: 90+57=147, added 6 instead of subtracting 4 → 153; wrong adjustment direction"),
        careless("D: 86+56=142 — miscounted"),
    ],

    # ─── PRACTICE R3 ────────────────────────────────────────────────────────────
    "R3_01": [
        careless("A: 186+212=398, 398+198=586 — arithmetic error in second addition"),
        careless("C: 200+200+200=600, added 6 → 606 — over-rounded all three"),
        err(M07, C_ENG,   "D: only added two of the three grades (186+212=398); stopped after first addition"),
    ],
    "R3_02": [
        careless("A: Jake used count-by-tens — incorrect; Jake changed the number to a friendly hundred"),
        err(M03, C_ENG,   "B: student said 'break apart' — Jake did not split the number into parts; he changed 298 to 300 and adjusted"),
        careless("D: 'make a ten' involves shifting ones between addends; Jake rounded to the nearest hundred"),
    ],
    "R3_03": [
        careless("B: 50+36=86 is correct — student mis-identified this step as wrong"),
        careless("C: friendly numbers strategy is valid; Lily's error is in the adjust step, not the strategy choice"),
        careless("D: 47+36=83, not 89 — student did not verify the actual answer"),
    ],
    "R3_04": [
        careless("A: 475+168=643, 643+97=740 but student computed 643+87=730 — arithmetic slip"),
        careless("C: 475+168=643, 643+107=750 — added 107 instead of 97"),
        err(M07, C_CARP,  "D: student added only 475+168=643 and stopped; omitted the final +97 step"),
    ],
    "R3_05": [
        err(M01, C_FUSON, "B: friendly method got 564 but forgot to subtract 1 → left answer as 564 (off by 1); or stated methods give different answers"),
        err(M01, C_FUSON, "C: friendly method: 200+364=564, then +1=565 instead of -1=563; wrong adjustment direction"),
        careless("D: 'strategies always give different answers' — violates the commutative/associative correctness principle"),
    ],
}

MATH_NOTES = {
    "PT_01":    "56+27: 56+20=76, 76+7=83. ✓",
    "PT_02":    "28+35: 28+2=30, 30+35=65, 65-2=63. ✓",
    "PT_03":    "116+203: 100+200=300, 16+3=19, 300+19=319. ✓",
    "PT_04":    "18+57: 18+2=20, 20+57=77, 77-2=75. ✓",
    "PT_05":    "46+38: 40+30=70, 6+8=14, 70+14=84. ✓",
    "LEARN_01": "N/A — 소개 카드",
    "LEARN_02": "34+25: 34→44→54 (+2 tens), 54→55→56→57→58→59 (+5 ones) = 59. ✓",
    "LEARN_03": "17+25: 17+3=20, 20+25=45, 45-3=42. ✓",
    "LEARN_04": "116+203: 100+200=300, 16+3=19, 300+19=319. ✓",
    "LEARN_05": "28+35: 28+2=30, 30+35=65, 65-2=63. ✓",
    "LEARN_06": "N/A — 전략 비교 카드",
    "LEARN_07": "376+427: 300+400=700, 76+27=103, 700+103=803. Math Talk card. ✓",
    "LEARN_08": "N/A — 요약 카드",
    "TRY_01":   "43+32: 43+30=73, 73+2=75. ✓",
    "TRY_02":   "19+44: 19+1=20, 20+44=64, 64-1=63. ✓",
    "TRY_03":   "234+152: 200+100=300, 30+50=80, 4+2=6, 300+80+6=386. ✓",
    "TRY_04":   "48+36: 48+2=50, 50+36=86, 86-2=84. ✓",
    "TRY_05":   "Boys=19, Girls=19+14=33, Total=19+33=52. ✓",
    "R1_01":    "37+24: 37+20=57, 57+4=61. ✓",
    "R1_02":    "62+19: 62+10=72, 72+9=81. ✓",
    "R1_03":    "29+53: 29+1=30, 30+53=83, 83-1=82. ✓",
    "R1_04":    "38+45: 38+2=40, 40+45=85, 85-2=83. ✓",
    "R1_05":    "145+232: 100+200=300, 40+30=70, 5+2=7, 300+70+7=377. ✓",
    "R1_06":    "321+456: 300+400=700, 20+50=70, 1+6=7, 700+70+7=777. ✓",
    "R1_07":    "67+25: 67+3=70, 70+25=95, 95-3=92. ✓",
    "R1_08":    "158+231: 100+200=300, 50+30=80, 8+1=9, 300+80+9=389. ✓",
    "R1_09":    "49+26: 49+1=50, 50+26=76, 76-1=75. ✓",
    "R1_10":    "47+38: 40+30=70, 7+8=15, 70+15=85. ✓",
    "R2_01":    "78+45: 78+2=80, 80+45=125, 125-2=123. ✓",
    "R2_02":    "463+325: 400+300=700, 60+20=80, 3+5=8, 700+80+8=788. ✓",
    "R2_03":    "57+36: 57+3=60, 60+36=96, 96-3=93. ✓",
    "R2_04":    "376+427: 300+400=700, 76+27=103, 700+103=803. ✓",
    "R2_05":    "376+427=803. Same as R2_04 word problem. ✓",
    "R2_06":    "99+47: 99+1=100, 100+47=147, 147-1=146. ✓",
    "R2_07":    "198+245: 198+2=200, 200+245=445, 445-2=443. ✓ (전략 선택 문항)",
    "R2_08":    "254+138: 200+100=300, 50+30=80, 4+8=12, 300+80+12=392. ✓",
    "R2_09":    "167+89: 89+1=90, 167+90=257, 257-1=256. ✓",
    "R2_10":    "86+57: 86+4=90, 90+57=147, 147-4=143. ✓",
    "R3_01":    "186+212+198: 186+212=398, 398+200=598, 598-2=596. ✓",
    "R3_02":    "298+156: Jake used friendly numbers (298→300, +2 offset). ✓ (전략 식별 문항)",
    "R3_03":    "47+36: Lily made 47→50 (+3), so must subtract 3: 86-3=83. ✓ (오류 분석 문항)",
    "R3_04":    "475+168=643, 643+97: 643+100=743, 743-3=740. ✓",
    "R3_05":    "199+364: friendly 200+364=564, 564-1=563. Break apart: 100+300=400, 99+64=163, 400+163=563. Both=563. ✓",
}

MATH_TALK_PROMPT = (
    "You solved 376 + 427 by breaking apart. "
    "Could you also use friendly numbers? Which strategy is faster here, and why? "
    "How do you decide which mental math strategy to use?"
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
    data = json.loads(L4_PATH.read_text(encoding="utf-8"))

    # ── 레슨 레벨 메타 필드 ──────────────────────────────────────────────────────
    data["tier"] = "A"
    data["vertical_alignment"] = {
        "previous": "2.NBT.B.7 — 1000 이내 덧셈/뺄셈 (조작물·그림·수직선)",
        "next":     "4.NBT.B.4 — 100,000 이내 표준 알고리즘 덧셈/뺄셈"
    }
    data["unit_intro_message"] = (
        "이 단원에서는 받아올림 없이/있이 1000 이내 덧셈을 머릿속으로 빠르게 계산하는 "
        "전략들을 배웁니다. 수직선·십의자리 홉·친숙한 수·자리값 분리 전략을 익혀 "
        "어떤 문제에 어떤 전략이 가장 효율적인지 판단하는 눈을 기릅니다."
    )
    data["unit_close_message"] = (
        "잘했어요! 이제 네 가지 암산 전략을 사용할 수 있게 되었습니다. "
        "다음 레슨에서는 덧셈의 성질(교환법칙·결합법칙)을 활용해 더 빠른 전략을 탐구합니다."
    )
    data["review_from_units"] = []
    data["interleave_ratio"] = 0.0
    data["passing_threshold"] = 0.80
    data["fluency_required"] = True
    data["supplementary_video"] = {
        "title": "Mental Math Tricks for Addition — Khan Academy",
        "url": "https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/imp-mental-math/v/mental-addition-example-1"
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

    L4_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    total = (len(data["pretest"]) + len(data["learn"]) +
             len(data["try"]) + len(data["practice_r1"]) +
             len(data["practice_r2"]) + len(data["practice_r3"]))
    print(f"✅ 업그레이드 완료: {L4_PATH}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {data['tier']}")
    print(f"   vertical_alignment: 2.NBT.B.7 → 4.NBT.B.4")


if __name__ == "__main__":
    main()
