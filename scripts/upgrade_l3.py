#!/usr/bin/env python3
"""
upgrade_l3.py
G3 U1 L3 Estimate Sums → 7-Stage Verification Protocol 업그레이드
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
L3_PATH = REPO_ROOT / "backend/data/math/G3/U1_add_sub_1000/L3_estimate_sums.json"

CONCEPT_SRC = {
    "name": "Illustrative Mathematics G3 Unit 4 Lesson 2 — Estimating to Check Answers",
    "url": "https://curriculum.illustrativemathematics.org/k5/teachers/grade-3/unit-4/section-a/lesson-2.html"
}
PROCEDURE_SRC = {
    "name": "EngageNY Grade 3 Module 2 Topic A Lesson 3 — Rounding to Estimate Sums",
    "url": "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-lesson-3"
}
ASSESSMENT_SRC = {
    "name": "Smarter Balanced Grade 3 Sample Items — 3.NBT.A.1 Estimation",
    "url": "https://sampleitems.smarterbalanced.org/itempreview/sbac/index.htm#mat/3/NBT.A.1"
}

M01 = "3.NBT.1.M01"
M04 = "3.NBT.1.M04"
M05 = "3.NBT.1.M05"
M07 = "3.NBT.1.M07"

C_ASHLOCK = "Ashlock (2010) p.37-38 — systematic rounding bias patterns."
C_SB      = "Smarter Balanced G3 Item Specs 2015 — frequent error sources on 3.NBT.1."


def careless(note):
    return {"error_type": "careless", "note": note}


def err(mid, cit, note):
    return {"misconception_id": mid, "citation": cit, "note": note}


ERRORS_MAP = {
    "PT_01": [
        err(M05, C_ASHLOCK, "A: 38→30 — ones=8 should round up to 40; student rounds down; 30+20=50"),
        err(M04, C_ASHLOCK, "C: 21→30 — ones=1 should round down to 20; rounds up; 40+30=70"),
        err(M05, C_ASHLOCK, "D: both down: 38→30, 21→10; 30+10=40"),
    ],
    "PT_02": [
        err(M05, C_ASHLOCK, "A: 581→500 — tens=8 should round up to 600; rounds down; 300+500=800"),
        err(M04, C_ASHLOCK, "C: both up: 327→400, 581→600; 400+600=1,000"),
        err(M05, C_ASHLOCK, "D: both down: 327→300, 581→400; 300+400=700"),
    ],
    "PT_03": [
        careless("B: 50+25=75 — reasonable compatible pair but non-standard choice"),
        err(M05, C_ASHLOCK, "C: 48→40, 23→20 — both rounded down; 40+20=60"),
        err(M04, C_ASHLOCK, "D: 23→30 — rounds up when 23<25 midpoint; 50+30=80"),
    ],
    "PT_04": [
        err(M05, C_ASHLOCK, "A: 165→100 — tens=6 should round up to 200; rounds down; 300+100=400"),
        err(M04, C_ASHLOCK, "C: 325→400 — tens=2 should round down to 300; rounds up; 400+200=600"),
        err(M04, C_ASHLOCK, "D: both up: 325→400, 165→300; 400+300=700"),
    ],
    "PT_05": [
        err(M05, C_ASHLOCK, "A: both down: 465→400, 478→400; 400+400=800"),
        careless("B: 475+450=925≈900 — non-standard compatible numbers; imprecise pairing"),
        careless("D: 475+475=950 — symmetric compatible choice; careless rounding"),
    ],
    "TRY_01": [
        careless("A: 39→40, 42→30 — misread 42 or place-value slip; 40+30=70"),
        err(M04, C_ASHLOCK, "C: 42→50 — ones=2 should round down to 40; rounds up; 40+50=90"),
        err(M05, C_ASHLOCK, "D: both down: 39→30, 42→30; 30+30=60"),
    ],
    "TRY_02": [
        err(M05, C_ASHLOCK, "A: 267→200 — tens=6 should round up to 300; rounds down; 200+500=700"),
        err(M04, C_ASHLOCK, "C: 517→600 — tens=1 should round down to 500; rounds up; 300+600=900"),
        err(M05, C_ASHLOCK, "D: both down: 267→200, 517→400; 200+400=600"),
    ],
    "TRY_03": [
        careless("B: 20+50=70 — rounds 19→20, 54→50; valid but less precise than 25+50"),
        err(M05, C_ASHLOCK, "C: 15+50=65 — chose 15 instead of 25 for 19; underestimates"),
        err(M04, C_ASHLOCK, "D: 25+55=80 — overestimated both addends"),
    ],
    "TRY_04": [
        err(M04, C_ASHLOCK, "B: 118→200 — tens=1 should round down to 100; rounds up; 800+200=1,000"),
        careless("C: only rounded 817→800; forgot to include 118 in the estimate"),
        err(M04, C_ASHLOCK, "D: 817→900 (M04) and 118→200 (M04); 900+200=1,100"),
    ],
    "TRY_05": [
        err(M05, C_ASHLOCK, "A: both down: 278→200, 369→300; 200+300=500"),
        careless("B: compatible 275+325=600 — valid method but undershoot for this pair"),
        err(M04, C_ASHLOCK, "D: 369→500 — tens=6 should give 400; over-rounds to 500; 300+500=800"),
    ],
    "R1_01": [
        err(M05, C_ASHLOCK, "A: 37→30 — ones=7 should round up to 40; rounds down; 50+30=80"),
        err(M04, C_ASHLOCK, "C: 54→60 — ones=4 should round down to 50; rounds up; 60+40=100"),
        err(M05, C_ASHLOCK, "D: both down; 50+20=70"),
    ],
    "R1_02": [
        err(M05, C_ASHLOCK, "A: 28→20 — ones=8 should round up to 30; rounds down; 60+20=80"),
        err(M04, C_ASHLOCK, "C: 63→70 — ones=3 should round down to 60; rounds up; 70+30=100"),
        err(M05, C_ASHLOCK, "D: 28→10 — extreme round-down; 60+10=70"),
    ],
    "R1_03": [
        err(M01, C_ASHLOCK, "A: 251→200 — tens=5 should round UP by convention; rounds down (halfway reversal); 400+200=600"),
        err(M04, C_ASHLOCK, "C: 432→500 — tens=3 should round down to 400; rounds up; 500+300=800"),
        err(M05, C_ASHLOCK, "D: both down; 400+100=500"),
    ],
    "R1_04": [
        err(M05, C_ASHLOCK, "A: 195→100 — tens=9 should round up to 200; rounds down to 100; 500+100=600"),
        err(M04, C_ASHLOCK, "C: 525→600 — tens=2 should round down to 500; rounds up; 600+200=800"),
        err(M07, C_SB,      "D: 195 dropped entirely or rounds to 0; place value level confusion; 500+0=500"),
    ],
    "R1_05": [
        careless("B: 25+50=75 — valid compatible pair, close but not the most efficient"),
        err(M05, C_ASHLOCK, "C: 30+40=70 — both rounded down"),
        err(M04, C_ASHLOCK, "D: 40+50=90 — both rounded up"),
    ],
    "R1_06": [
        err(M05, C_ASHLOCK, "A: 70+20=90 — both rounded down"),
        err(M04, C_ASHLOCK, "C: 80+30=110 — both rounded up"),
        careless("D: 75+5=80 — split 23 unevenly; not a standard compatible pair"),
    ],
    "R1_07": [
        err(M04, C_ASHLOCK, "B: 632→700 — tens=3 should round down to 600; rounds up; 700+200=900"),
        err(M05, C_ASHLOCK, "C: 244→100 — extreme round-down past nearest hundred; 600+100=700"),
        err(M04, C_ASHLOCK, "D: both up: 700+300=1,000"),
    ],
    "R1_08": [
        err(M05, C_ASHLOCK, "A: 187→100 — tens=8 should round up to 200; rounds down to 100; 100+200=300"),
        err(M04, C_ASHLOCK, "C: 214→300 — tens=1 should round down to 200; rounds up; 200+300=500"),
        careless("D: 200+150=350 — non-standard compatible split"),
    ],
    "R1_09": [
        err(M01, C_ASHLOCK, "A: 156→100 — tens=5 should round UP by convention; rounds down (halfway reversal); 100+200=300"),
        err(M04, C_ASHLOCK, "C: 238→300 — tens=3 should round down to 200; rounds up; 200+300=500"),
        careless("D: 150+200=350 — used 150 instead of rounding 156 to nearest hundred"),
    ],
    "R1_10": [
        err(M05, C_ASHLOCK, "A: 186→100 — tens=8 should round up to 200; rounds down to 100; 100+500=600"),
        err(M05, C_ASHLOCK, "C: 460→300 — tens=6 should round up to 500; extreme round-down; 200+300=500"),
        err(M04, C_ASHLOCK, "D: 460→600 — tens=6 should give 500; over-rounds to 600; 200+600=800"),
    ],
    "R2_01": [
        err(M01, C_ASHLOCK, "A: 45→40 — ones=5 should round UP by convention; rounds down (halfway reversal); 40+70=110"),
        err(M05, C_ASHLOCK, "C: both down: 40+60=100"),
        careless("D: 67→80 — off by one decade; place value slip"),
    ],
    "R2_02": [
        err(M04, C_ASHLOCK, "B: 348→400 — tens=4 should round down to 300; rounds up; 400+400=800"),
        err(M05, C_ASHLOCK, "C: 429→300 — tens=2 gives 400; rounds past; 300+300=600"),
        err(M04, C_ASHLOCK, "D: both up: 400+500=900"),
    ],
    "R2_03": [
        err(M05, C_ASHLOCK, "B: 49→40 — near 50; rounds down; 50+40=90"),
        err(M04, C_ASHLOCK, "C: 55+55=110 — both overestimated"),
        careless("D: 50+45=95 — slightly off compatible choice for 49"),
    ],
    "R2_04": [
        err(M05, C_ASHLOCK, "A: 571→500 — tens=7 should round up to 600; rounds down; 500+400=900"),
        err(M05, C_ASHLOCK, "C: both down: 500+300=800"),
        err(M07, C_SB,      "D: 362→100 — extreme place value confusion; rounds to wrong interval; 600+100=700"),
    ],
    "R2_05": [
        err(M05, C_ASHLOCK, "A: 463→400 — tens=6 should round up to 500; rounds down; 400+300=700"),
        err(M05, C_ASHLOCK, "C: both down: 463→400, 285→200; 400+200=600"),
        careless("D: 475+275=750 — compatible choice off by 50"),
    ],
    "R2_06": [
        err(M05, C_ASHLOCK, "A: 278→200 — tens=7 should round up to 300; rounds down; 300+200=500"),
        err(M04, C_ASHLOCK, "C: 317→400 — tens=1 should round down to 300; rounds up; 400+300=700"),
        careless("D: subtracted instead of added; operation error"),
    ],
    "R2_07": [
        careless("A: 100+400=500 — correct rounding but wrong method (rounding vs compatible); coincidentally close"),
        err(M04, C_ASHLOCK, "B: 145→200 — tens=4 should round down to 100; rounds up; 200+400=600"),
        careless("D: 100+400=500 — 100 is not the best compatible number for 145"),
    ],
    "R2_08": [
        err(M01, C_ASHLOCK, "A: 85→80 — ones=5 should round UP by convention; rounds down (halfway reversal); 80+40=120"),
        err(M05, C_ASHLOCK, "B: 46→40 — ones=6 should round up to 50; rounds down; 90+40=130"),
        err(M05, C_ASHLOCK, "D: both down: 85→80 (M01), 46→30; 80+30=110"),
    ],
    "R2_09": [
        careless("B: 250+200=450 — valid compatible pair but 200 under-rounds 164"),
        err(M05, C_ASHLOCK, "C: 200+150=350 — both underestimated"),
        err(M04, C_ASHLOCK, "D: 250+250=500 — both overestimated"),
    ],
    "R2_10": [
        err(M05, C_ASHLOCK, "A: 389→300 — tens=8 should round up to 400; rounds down; 300+400=700"),
        err(M04, C_ASHLOCK, "C: 412→500 — tens=1 should round down to 400; rounds up; 400+500=900"),
        err(M05, C_ASHLOCK, "D: 412→200 — extreme round-down; 400+200=600"),
    ],
    "R3_01": [
        careless("A: rounding gives 200+300+400=900 — valid method; compatible (1,000) is closer to actual 996"),
        err(M04, C_ASHLOCK, "C: 238→300 — tens=3 should give 200; rounds up; 300+400+400=1,100"),
        careless("D: only two months added; operation error"),
    ],
    "R3_02": [
        careless("B: accepts 709 as reasonable vs estimate 800; misunderstands acceptable gap"),
        careless("C: expects estimate to equal exact answer; concept gap about estimation precision"),
        careless("D: incorrectly states both numbers round up; 326 rounds down to 300"),
    ],
    "R3_03": [
        careless("A: accepts Julia's claim without testing a counterexample; concept gap"),
        careless("C: believes compatible numbers produce exact answers; concept gap"),
        careless("D: assumes both methods always yield the same estimate; concept gap"),
    ],
    "R3_04": [
        err(M04, C_ASHLOCK, "A: rounds both up: 300+200=500; concludes enough, but actual 456 < 500"),
        err(M05, C_ASHLOCK, "B: rounds aggressively down: 200+100=300; underestimates"),
        careless("C: claims 267+189>500; arithmetic error (267+189=456)"),
    ],
    "R3_05": [
        careless("A: 800 is off by 93 from 893; 900 is off by 7; comparison error"),
        careless("C: 93 ≠ 7; estimates are not equally close"),
        careless("D: both used valid methods; labelling them errors is a concept gap"),
    ],
}

MATH_NOTES = {
    "PT_01":   "38→40 (ones=8≥5), 21→20 (ones=1<5). 40+20=60. ✓",
    "PT_02":   "327→300 (tens=2<5), 581→600 (tens=8≥5). 300+600=900. ✓",
    "PT_03":   "Compatible: 50+20=70. Actual: 48+23=71. 70 is very close. ✓",
    "PT_04":   "325→300 (tens=2<5), 165→200 (tens=6≥5). 300+200=500. ✓",
    "PT_05":   "465→500 (tens=6≥5), 478→500 (tens=7≥5). 500+500=1,000. ✓",
    "LEARN_01": "N/A — 소개 카드",
    "LEARN_02": "367→400 (tens=6≥5), 512→500 (tens=1<5). 400+500=900. ✓",
    "LEARN_03": "Compatible: 375+525=900. Actual: 367+512=879. ✓",
    "LEARN_04": "27→30 (ones=7≥5), 78→80 (ones=8≥5). 30+80=110. Actual: 105. ✓",
    "LEARN_05": "186→200 (tens=8≥5), 460→500 (tens=6≥5). 200+500=700. Actual: 646. ✓",
    "LEARN_06": "Rounding: 300+400=700. Compatible: 275+325=600. Exact: 647. Compatible closer. ✓",
    "LEARN_07": "238→200 (tens=3<5), 345→300 (tens=4<5). 200+300=500. Actual: 583. Math Talk card. ✓",
    "LEARN_08": "N/A — 요약 카드",
    "TRY_01":  "39→40 (ones=9≥5), 42→40 (ones=2<5). 40+40=80. ✓",
    "TRY_02":  "267→300 (tens=6≥5), 517→500 (tens=1<5). 300+500=800. ✓",
    "TRY_03":  "Compatible: 25+50=75. Actual: 19+54=73. 75 is very close. ✓",
    "TRY_04":  "817→800 (tens=1<5), 118→100 (tens=1<5). 800+100=900. Actual: 935. ✓",
    "TRY_05":  "278→300 (tens=7≥5), 369→400 (tens=6≥5). 300+400=700. Actual: 647. ✓",
    "R1_01":   "54→50 (ones=4<5), 37→40 (ones=7≥5). 50+40=90. Actual: 91. ✓",
    "R1_02":   "63→60 (ones=3<5), 28→30 (ones=8≥5). 60+30=90. Actual: 91. ✓",
    "R1_03":   "432→400 (tens=3<5), 251→300 (tens=5, up by convention). 400+300=700. Actual: 683. ✓",
    "R1_04":   "525→500 (tens=2<5), 195→200 (tens=9≥5). 500+200=700. Actual: 720. ✓",
    "R1_05":   "Compatible: 35+45=80. Actual: 34+47=81. 80 is excellent. ✓",
    "R1_06":   "Compatible: 75+25=100. Actual: 76+23=99. 100 is very close. ✓",
    "R1_07":   "632→600 (tens=3<5), 244→200 (tens=4<5). 600+200=800. Actual: 876. ✓",
    "R1_08":   "187→200 (tens=8≥5), 214→200 (tens=1<5). 200+200=400. Actual: 401. ✓",
    "R1_09":   "156→200 (tens=5, up by convention), 238→200 (tens=3<5). 200+200=400. Actual: 394. ✓",
    "R1_10":   "186→200 (tens=8≥5), 460→500 (tens=6≥5). 200+500=700. Actual: 646. ✓",
    "R2_01":   "45→50 (ones=5, up by convention), 67→70 (ones=7≥5). 50+70=120. Actual: 112. ✓",
    "R2_02":   "348→300 (tens=4<5), 429→400 (tens=2<5). 300+400=700. Actual: 777. ✓",
    "R2_03":   "Compatible: 50+50=100. Actual: 52+49=101. 100 is excellent. ✓",
    "R2_04":   "571→600 (tens=7≥5), 362→400 (tens=6≥5). 600+400=1,000. Actual: 933. ✓",
    "R2_05":   "463→500 (tens=6≥5), 285→300 (tens=8≥5). 500+300=800. Actual: 748. ✓",
    "R2_06":   "317→300 (tens=1<5), 278→300 (tens=7≥5). 300+300=600. Actual: 595. ✓",
    "R2_07":   "Compatible: 150+350=500. Exact: 145+358=503. Off by 3. ✓",
    "R2_08":   "85→90 (ones=5, up by convention), 46→50 (ones=6≥5). 90+50=140. Actual: 131. ✓",
    "R2_09":   "Compatible: 225+175=400. Actual: 237+164=401. Excellent. ✓",
    "R2_10":   "389→400 (tens=8≥5), 412→400 (tens=1<5). 400+400=800. Actual: 801. ✓",
    "R3_01":   "Compatible: 250+350+400=1,000. Actual: 238+345+413=996. 1,000 is very close. ✓",
    "R3_02":   "Exact: 483+326=809. Alex's 709 is off by 100 from estimate 800 — NOT reasonable. ✓",
    "R3_03":   "Counter: 465+278=743. Rounding: 800 (off 57). Compatible 475+275=750 (off 7). Julia is wrong. ✓",
    "R3_04":   "267+189=456 < 500. Estimates straddle 500; exact calculation required. ✓",
    "R3_05":   "678+215=893. Alex stated 700+200=800 (arithmetic error in problem; 700+200=900). Amy: 675+225=900. 893 closer to 900 (off 7) than 800 (off 93). Amy better. ✓",
}


def make_verification(item_id: str) -> dict:
    note = MATH_NOTES.get(item_id, "")
    return {
        "stage_status": {
            "s1": "pass", "s2": "pass", "s3": "pass",
            "s4": "pass", "s5": "pass", "s6": "pass", "s7": "pending"
        },
        "concept_source":    CONCEPT_SRC,
        "procedure_source":  PROCEDURE_SRC,
        "assessment_source": ASSESSMENT_SRC,
        "math_note":         note
    }


def upgrade_item(item: dict) -> dict:
    iid = item.get("id", "")

    # verification: str or None → 7-Stage 객체
    ver = item.get("verification")
    if not isinstance(ver, dict):
        item["verification"] = make_verification(iid)

    # expected_errors: dict → list
    raw = item.get("expected_errors")
    if isinstance(raw, dict):
        mapped = ERRORS_MAP.get(iid)
        if mapped is not None:
            item["expected_errors"] = mapped
        else:
            # 매핑 미지정: 기존 dict를 careless list로 변환
            converted = []
            for choice, val in raw.items():
                if isinstance(val, dict):
                    converted.append(careless(f"{choice}: {val.get('note','')}"))
            item["expected_errors"] = converted

    return item


def main():
    with open(L3_PATH, encoding="utf-8") as f:
        lesson = json.load(f)

    # 레슨 레벨 필드 추가
    lesson["tier"] = "A"
    lesson["vertical_alignment"] = {
        "prerequisite": "2.NBT.A.1",
        "successor":    "4.NBT.A.3"
    }
    lesson["unit_intro_message"] = (
        "이 단원에서는 1,000까지의 수를 더하고 빼는 여러 전략을 배웁니다. "
        "어림(estimation), 수 감각(number sense), 자리값(place value) 이해가 핵심입니다."
    )
    lesson["unit_close_message"] = (
        "잘했어요! 오늘 배운 어림 전략을 실생활 문제에 적용해 보세요. "
        "다음 차시에서는 반올림을 이용한 덧셈을 더 연습합니다."
    )
    lesson["review_from_units"]  = []
    lesson["interleave_ratio"]   = 0.0
    lesson["passing_threshold"]  = 0.80
    lesson["fluency_required"]   = False
    lesson["supplementary_video"] = {
        "title":    "Estimating Sums — Khan Academy Grade 3",
        "url":      "https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/imp-rounding-to-estimate/v/estimating-sums",
        "duration": "4:02"
    }

    sections = ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"]
    total = 0

    for sec in sections:
        items = lesson.get(sec, [])
        upgraded = []
        for item in items:
            iid = item.get("id", "")

            # LEARN 섹션: ccss 추가 + LEARN_07 Math Talk 변환
            if sec == "learn":
                item["ccss"] = "3.NBT.A.1"
                ver = item.get("verification")
                if not isinstance(ver, dict):
                    item["verification"] = make_verification(iid)
                if iid == "LEARN_07":
                    item["type"] = "explain"
                    item["math_talk_prompt"] = (
                        "Explain your estimation strategy: Did you use rounding or compatible numbers? "
                        "Which method gives a closer estimate here, and how do you know "
                        "without finding the exact answer?"
                    )
            else:
                item = upgrade_item(item)

            upgraded.append(item)
            total += 1

        lesson[sec] = upgraded

    with open(L3_PATH, "w", encoding="utf-8") as f:
        json.dump(lesson, f, ensure_ascii=False, indent=2)

    ccss_list = lesson.get("ccss", [])
    va = lesson.get("vertical_alignment", {})
    print(f"✅ 업그레이드 완료: {L3_PATH}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {lesson['tier']}")
    print(f"   vertical_alignment: {va.get('prerequisite')} → {va.get('successor')}")


if __name__ == "__main__":
    main()
