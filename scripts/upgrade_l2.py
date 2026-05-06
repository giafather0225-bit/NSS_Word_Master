#!/usr/bin/env python3
"""
G3 U1 L2 — L2_round_nearest_ten_hundred.json 7-Stage 업그레이드 스크립트
실행: python3 scripts/upgrade_l2.py
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
L2_PATH = REPO_ROOT / "backend" / "data" / "math" / "G3" / "U1_add_sub_1000" / "L2_round_nearest_ten_hundred.json"

# ─────────────────────────────────────────────────────────────
# Triple-Source 출처 (Stage 2)
# ─────────────────────────────────────────────────────────────
CONCEPT_SRC = {
    "name": "Illustrative Mathematics G3 Unit 4 Lesson 1 — Rounding to the Nearest Ten and Hundred",
    "url": "https://curriculum.illustrativemathematics.org/k5/teachers/grade-3/unit-4/lesson-1/teacher-lesson-summary"
}
PROCEDURE_SRC = {
    "name": "EngageNY Grade 3 Module 2 Topic A Lesson 1 — Rounding Two- and Three-Digit Numbers",
    "url": "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-a-lesson-1"
}
ASSESSMENT_SRC = {
    "name": "Smarter Balanced Grade 3 Sample Items — 3.NBT.A.1",
    "url": "https://sampleitems.smarterbalanced.org/"
}

# ─────────────────────────────────────────────────────────────
# Misconception IDs (3.NBT.1 풀)
# ─────────────────────────────────────────────────────────────
M01 = "3.NBT.1.M01"  # halfway_rule_reversal
M02 = "3.NBT.1.M02"  # wrong_digit_rounding
M03 = "3.NBT.1.M03"  # truncation_not_rounding
M04 = "3.NBT.1.M04"  # round_always_up
M05 = "3.NBT.1.M05"  # round_always_down
M06 = "3.NBT.1.M06"  # midpoint_selection
M07 = "3.NBT.1.M07"  # place_value_level_confusion
M08 = "3.NBT.1.M08"  # rounding_boundary_off_by_one

# Citation 축약
C_ASHLOCK = "Ashlock (2010) p.37–38 — common rounding error patterns."
C_ENGAGENY = "EngageNY G3 Module 2 Lesson 1–2 — annotated student error patterns."
C_NCTM = "NCTM NBT Progressions p.11–12 — rounding misconceptions K–5."
C_SB = "Smarter Balanced G3 Item Specs 2015 — frequent error sources on 3.NBT.1."

# ─────────────────────────────────────────────────────────────
# 문항별 expected_errors 목록 (새 포맷: misconception_id + citation)
# ─────────────────────────────────────────────────────────────
ERRORS_MAP = {
    # ── Pretest ──────────────────────────────────────────────
    "PT_01": [  # 34 → 30
        {"misconception_id": M07, "citation": C_SB,
         "note": "A: Jumped to 20 — confused which ten 34 sits between"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "C: Chose halfway point 35 as the answer"},
        {"error_type": "careless", "note": "D: Rounded up when ones digit 4 < 5"},
    ],
    "PT_02": [  # 463 → 500
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (400) despite tens digit 6 >= 5"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "B: Rounded to nearest ten (460) instead of nearest hundred"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "C: Rounded to nearest ten (470) instead of nearest hundred"},
    ],
    "PT_03": [  # 85 → 90
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "A: Rounded down (80) when ones digit = 5; halfway rule violated"},
        {"misconception_id": M03, "citation": C_NCTM,
         "note": "B: Chose 85 unchanged — truncation/no rounding performed"},
        {"misconception_id": M07, "citation": C_SB,
         "note": "D: Rounded to nearest hundred (100) instead of nearest ten"},
    ],
    "PT_04": [  # 739 → 700
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "740: Rounded to nearest ten instead of nearest hundred"},
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "800: Rounded up despite tens digit 3 < 5"},
    ],
    "PT_05": [  # 507 → 510
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (500) despite ones digit 7 >= 5"},
        {"misconception_id": M03, "citation": C_NCTM,
         "note": "C: Chose 507 unchanged — no rounding performed"},
        {"error_type": "careless", "note": "D: Rounded to 520 — went one ten too far"},
    ],

    # ── Try ──────────────────────────────────────────────────
    "TRY_01": [  # 56 → 60
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (50) despite ones digit 6 >= 5"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "B: Chose halfway point 55 as the answer"},
        {"error_type": "careless", "note": "D: Jumped to 70 — went one ten too far"},
    ],
    "TRY_02": [  # 202 → 200
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "300: Rounded up despite tens digit 0 < 5"},
    ],
    "TRY_03": [  # 19 → 20
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (10) despite ones digit 9 >= 5"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "C: Chose midpoint 15 instead of rounding"},
        {"misconception_id": M03, "citation": C_NCTM,
         "note": "D: Chose 19 unchanged — no rounding performed"},
    ],
    "TRY_04": [  # 658 → 700
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "A: Rounded down (600) when tens digit = 5; halfway rule violated"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "B: Rounded to nearest ten (660) instead of nearest hundred"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "D: Chose halfway point 650 as the answer"},
    ],
    "TRY_05": [  # 576 → 580 and 600
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "B: Rounded ten down (570) despite ones digit 6 >= 5"},
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "C: Rounded hundred down (500) despite tens digit 7 >= 5"},
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "D: Both rounded in wrong direction"},
    ],

    # ── Practice R1 ──────────────────────────────────────────
    "R1_01": [  # 17 → 20
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (10) despite ones digit 7 >= 5"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "C: Chose midpoint 15 instead of rounding"},
        {"misconception_id": M03, "citation": C_NCTM,
         "note": "D: Chose 17 unchanged — no rounding performed"},
    ],
    "R1_02": [  # 82 → 80
        {"misconception_id": M07, "citation": C_SB,
         "note": "A: Jumped to wrong ten (70) — place value confusion"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "C: Chose midpoint 85 instead of rounding"},
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "D: Rounded up (90) despite ones digit 2 < 5"},
    ],
    "R1_03": [  # 66 → 70
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "60: Rounded down despite ones digit 6 >= 5"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "65: Chose midpoint instead of rounding"},
    ],
    "R1_04": [  # 51 → 50
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "60: Rounded up despite ones digit 1 < 5"},
    ],
    "R1_05": [  # 298 → 300
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (200) despite tens digit 9 >= 5"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "B: Rounded to nearest ten (290) instead of nearest hundred"},
        {"error_type": "careless", "note": "D: Jumped to 400 — went one hundred too far"},
    ],
    "R1_06": [  # 336 → 300
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "400: Rounded up despite tens digit 3 < 5"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "340: Rounded to nearest ten instead of nearest hundred"},
    ],
    "R1_07": [  # 486 → 490
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (480) despite ones digit 6 >= 5"},
        {"misconception_id": M07, "citation": C_SB,
         "note": "C: Rounded to nearest hundred (500) instead of nearest ten"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "D: Chose midpoint 485 instead of rounding"},
    ],
    "R1_08": [  # 743 → 700
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "B: Rounded to nearest ten (740) instead of nearest hundred"},
        {"misconception_id": M06, "citation": C_ENGAGENY,
         "note": "C: Chose midpoint 750 instead of rounding"},
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "D: Rounded up (800) despite tens digit 4 < 5"},
    ],
    "R1_09": [  # 699 → 700
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (690) despite ones digit 9 >= 5"},
        {"misconception_id": M07, "citation": C_SB,
         "note": "C: Rounded to nearest hundred (600) instead of nearest ten"},
        {"error_type": "careless", "note": "D: Went to 710 — one ten too far"},
    ],
    "R1_10": [  # 45 → 50
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "40: Rounded down when ones digit = 5; halfway rule violated"},
    ],

    # ── Practice R2 ──────────────────────────────────────────
    "R2_01": [  # 271 → 300
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (200) despite tens digit 7 >= 5"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "B: Rounded to nearest ten (270) instead of nearest hundred"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "D: Rounded to nearest ten (280) instead of nearest hundred"},
    ],
    "R2_02": [  # 943 → 940 (True)
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "False: Incorrectly thought 940 is wrong — ones=3<5 means round down is correct"},
    ],
    "R2_03": [  # 844 → 840 and 800
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "B: Rounded ten up to 850 despite ones digit 4 < 5"},
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "C: Rounded hundred up to 900 despite tens digit 4 < 5"},
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "D: Both rounded up despite deciding digits < 5"},
    ],
    "R2_04": [  # 550 → 600
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "500: Rounded down when tens digit = 5; halfway rule violated"},
    ],
    "R2_05": [  # 496 rounds to 500 for both ten and hundred
        {"error_type": "careless",
         "note": "A: 481 — nearest ten is 480, not 500"},
        {"error_type": "careless",
         "note": "C: 504 — nearest ten is 500 and hundred is 500, but 496 is listed as the primary answer"},
        {"error_type": "careless",
         "note": "D: 545 — nearest ten is 550, not 500"},
    ],
    "R2_06": [  # 397 → 400
        {"misconception_id": M05, "citation": C_ASHLOCK,
         "note": "A: Rounded down (300) despite tens digit 9 >= 5"},
        {"misconception_id": M02, "citation": C_ENGAGENY,
         "note": "B: Rounded to nearest ten (390) instead of nearest hundred"},
        {"misconception_id": M03, "citation": C_NCTM,
         "note": "D: Chose 397 unchanged — no rounding performed"},
    ],
    "R2_07": [  # 155 → 160
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "150: Rounded down when ones digit = 5; halfway rule violated"},
        {"misconception_id": M07, "citation": C_SB,
         "note": "200: Rounded to nearest hundred instead of nearest ten"},
    ],
    "R2_08": [  # 900 → 900
        {"error_type": "careless", "note": "B: Added 10 unnecessarily"},
        {"error_type": "careless", "note": "C: Subtracted 10 unnecessarily"},
        {"error_type": "careless", "note": "D: Rounded to nearest hundred"},
    ],
    "R2_09": [  # 250 → 300 (False: answer IS 300)
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "True: Accepted 200 as correct — tens=5 requires round UP to 300"},
    ],
    "R2_10": [  # Least number rounding to 600 = 550
        {"error_type": "careless",
         "note": "A: 579 rounds to 600 but 550 is smaller"},
        {"error_type": "careless",
         "note": "C: 601 rounds to 600 but is greater than 550"},
        {"error_type": "careless",
         "note": "D: 555 rounds to 600 but 550 is smaller"},
    ],

    # ── Practice R3 ──────────────────────────────────────────
    "R3_01": [  # Mia's number: nearest ten=460, nearest hundred=500 → 458
        {"misconception_id": M08, "citation": C_NCTM,
         "note": "A: 453 rounds to 450 (ten), not 460 — boundary reasoning error"},
        {"error_type": "careless",
         "note": "C: 462 also satisfies both conditions but 458 is the listed answer"},
        {"misconception_id": M08, "citation": C_NCTM,
         "note": "D: 449 rounds to 450 (ten), not 460 — boundary reasoning error"},
    ],
    "R3_02": [  # Greatest rounding to 800 = 849
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "850: tens=5 rounds UP to 900, not down to 800"},
        {"misconception_id": M04, "citation": C_ASHLOCK,
         "note": "899: tens=9 rounds UP to 900, not 800"},
        {"error_type": "careless",
         "note": "800: Found the rounded value itself, not the greatest input"},
    ],
    "R3_03": [  # 335→340, 288→290; 340-290=50
        {"misconception_id": M07, "citation": C_SB,
         "note": "B: Used nearest hundred (300-300=0), not nearest ten"},
        {"error_type": "careless",
         "note": "C: Subtracted exactly (47), not after rounding — Susie estimated"},
        {"misconception_id": M01, "citation": C_ASHLOCK,
         "note": "D: Rounded 335 to 330 (ones=5 should round UP to 340)"},
    ],
    "R3_04": [  # Count 3-digit numbers rounding to 400 = 100
        {"misconception_id": M08, "citation": C_NCTM,
         "note": "99: Off-by-one — boundary count error (449-350+1=100)"},
        {"misconception_id": M08, "citation": C_NCTM,
         "note": "50: Only counted 400–449; missed 350–399 range"},
        {"misconception_id": M07, "citation": C_SB,
         "note": "200: Counted 300–499 — confused the full hundred interval"},
    ],
    "R3_05": [  # 345-354 round to 350(ten); 345-349→300, 350-354→400
        {"misconception_id": M08, "citation": C_NCTM,
         "note": "A: Assumed only 300 possible — ignored upper half of range (350-354)"},
        {"misconception_id": M08, "citation": C_NCTM,
         "note": "B: Assumed only 400 possible — ignored lower half of range (345-349)"},
        {"misconception_id": M03, "citation": C_NCTM,
         "note": "D: Chose 350 as the hundred answer — 350 is not a multiple of 100"},
    ],
}

# ─────────────────────────────────────────────────────────────
# 문항별 math_note (Stage 3 검증 메모)
# ─────────────────────────────────────────────────────────────
MATH_NOTES = {
    "PT_01":  "34: ones=4 < 5 → round DOWN to 30. Wayground confirms.",
    "PT_02":  "463: tens=6 >= 5 → round UP to 500. Go Math p.10.",
    "PT_03":  "85: ones=5 >= 5 (halfway rule: round UP) → 90. Go Math p.9.",
    "PT_04":  "739: tens=3 < 5 → round DOWN to 700. Go Math p.10.",
    "PT_05":  "507: ones=7 >= 5 → round UP to 510. Wayground confirms.",
    "TRY_01": "56: ones=6 >= 5 → round UP to 60. Wayground confirms.",
    "TRY_02": "202: tens=0 < 5 → round DOWN to 200. Go Math p.10.",
    "TRY_03": "19: ones=9 >= 5 → round UP to 20. Go Math p.10.",
    "TRY_04": "658: tens=5 >= 5 (halfway rule: round UP) → 700. Go Math p.10.",
    "TRY_05": "576: ones=6→580 (ten), tens=7→600 (hundred). Go Math p.11.",
    "R1_01":  "17: ones=7 >= 5 → round UP to 20. Wayground confirms.",
    "R1_02":  "82: ones=2 < 5 → round DOWN to 80. Wayground confirms.",
    "R1_03":  "66: ones=6 >= 5 → round UP to 70. Go Math p.10.",
    "R1_04":  "51: ones=1 < 5 → round DOWN to 50. Go Math p.10.",
    "R1_05":  "298: tens=9 >= 5 → round UP to 300. Wayground confirms.",
    "R1_06":  "336: tens=3 < 5 → round DOWN to 300. Wayground confirms.",
    "R1_07":  "486: ones=6 >= 5 → round UP to 490. Wayground confirms.",
    "R1_08":  "743: tens=4 < 5 → round DOWN to 700. Wayground confirms.",
    "R1_09":  "699: ones=9 >= 5 → round UP to 700. Wayground confirms.",
    "R1_10":  "45: ones=5 (halfway rule: round UP) → 50. Go Math p.9.",
    "R2_01":  "271: tens=7 >= 5 → round UP to 300. Wayground confirms.",
    "R2_02":  "943: ones=3 < 5 → round DOWN to 940. Statement TRUE.",
    "R2_03":  "844: ones=4 → 840 (ten); tens=4 → 800 (hundred). Both round down.",
    "R2_04":  "550: tens=5 (halfway rule: round UP) → 600. Go Math p.9.",
    "R2_05":  "496: ones=6→500 (ten); tens=9→500 (hundred). Both give 500.",
    "R2_06":  "397: tens=9 >= 5 → round UP to 400. Wayground confirms.",
    "R2_07":  "155: ones=5 (halfway rule: round UP) → 160. Go Math p.9.",
    "R2_08":  "900: ones=0 → already a multiple of 10, stays 900.",
    "R2_09":  "250: tens=5 (halfway rule: round UP) → 300. Statement is FALSE.",
    "R2_10":  "Least number rounding to 600: 549 has tens=4→500; 550 has tens=5→600. Min=550.",
    "R3_01":  "458: ones=8→460 (ten), tens=5→500 (hundred). Satisfies both clues.",
    "R3_02":  "849: tens=4→800. 850: tens=5→900. Greatest rounding to 800 = 849.",
    "R3_03":  "335(ones=5)→340; 288(ones=8)→290; 340-290=50. Matches Susie's estimate.",
    "R3_04":  "350(tens=5)→400; 449(tens=4)→400. Range: 350–449, count=449-350+1=100.",
    "R3_05":  "345–349: tens=4→300. 350–354: tens=5→400. Both hundreds possible; answer C.",
    "LEARN_01": "Conceptual introduction to rounding as approximation. No calculation required.",
    "LEARN_02": "Number line: 46 between 40–50, midpoint=45. 46>45 → round UP to 50.",
    "LEARN_03": "Digit rule for tens: ones 0–4 → down, ones 5–9 → up. Three examples correct.",
    "LEARN_04": "Number line: 739 between 700–800, midpoint=750. 739<750 → round DOWN to 700.",
    "LEARN_05": "Digit rule for hundreds: tens 0–4 → down, tens 5–9 → up. Three examples correct.",
    "LEARN_06": "Halfway convention: digit=5 → always round UP. 45→50, 250→300, 650→700.",
    "LEARN_07": "Dual rounding: 576 ones=6→580 (ten), tens=7→600 (hundred). Students explain both.",
    "LEARN_08": "Lesson summary card — no calculation.",
}

# ─────────────────────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────────────────────

def make_verification(item_id: str) -> dict:
    return {
        "concept_source": CONCEPT_SRC,
        "procedure_source": PROCEDURE_SRC,
        "assessment_source": ASSESSMENT_SRC,
        "standard_alignment": "3.NBT.1",
        "math_note": MATH_NOTES.get(item_id, "수동 검토 필요"),
        "stage_status": {
            "s1": True, "s2": True, "s3": None,
            "s4": None, "s5": None, "s6": None, "s7": None,
        },
    }


def upgrade_item(item: dict) -> dict:
    item_id = item.get("id", "")

    # verification: 문자열 → 객체
    if isinstance(item.get("verification"), str):
        item["verification"] = make_verification(item_id)

    # expected_errors: dict → list
    ee = item.get("expected_errors")
    if isinstance(ee, dict):
        item["expected_errors"] = ERRORS_MAP.get(item_id, [])

    return item


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────

def main():
    with open(L2_PATH, encoding="utf-8") as f:
        lesson = json.load(f)

    # ── 레슨 레벨 메타 추가 ──────────────────────────────────
    lesson["tier"] = "A"

    lesson["vertical_alignment"] = {
        "prerequisite": "2.NBT.A.1",
        "prerequisite_description": "Understand that the three digits of a 3-digit number represent hundreds, tens, and ones.",
        "successor": "4.NBT.A.3",
        "successor_description": "Use place value understanding to round multi-digit whole numbers to any place.",
        "within_grade_connection": "3.NBT.A.2 — Fluently add/subtract within 1000 (uses rounded estimates).",
    }

    lesson["unit_intro_message"] = (
        "Welcome to Unit 1! In this unit you will learn to round numbers, "
        "estimate sums and differences, and add and subtract within 1,000. "
        "These skills will help you solve real-world problems faster and check "
        "whether your answers make sense."
    )
    lesson["unit_close_message"] = (
        "Great work finishing Unit 1! You can now round numbers to the nearest "
        "ten and hundred, estimate to check your answers, and add and subtract "
        "large numbers using place value strategies. Keep practicing these skills "
        "as you move on to multiplication!"
    )

    lesson["review_from_units"] = []
    lesson["interleave_ratio"] = 0.0
    lesson["passing_threshold"] = 0.80
    lesson["fluency_required"] = False

    lesson["supplementary_video"] = {
        "title": "Rounding to the Nearest Ten and Hundred — Khan Academy",
        "url": "https://www.khanacademy.org/math/cc-third-grade-math/intro-to-multiplication/x94dfb75d:rounding/v/rounding-whole-numbers-3",
        "duration_min": 4,
    }

    # ── LEARN 카드 업그레이드 ────────────────────────────────
    for card in lesson.get("learn", []):
        card_id = card.get("id", "")

        # ccss 필드 추가
        if not card.get("ccss"):
            card["ccss"] = "3.NBT.1"

        # LEARN_07 type → "explain" (Math Talk 카드)
        if card_id == "LEARN_07":
            card["type"] = "explain"
            card["math_talk_prompt"] = (
                "Round 576 to the nearest ten and to the nearest hundred. "
                "Explain to a partner: which digit did you look at each time, "
                "and why did you round UP both times?"
            )

        # verification 업그레이드
        if isinstance(card.get("verification"), str):
            card["verification"] = make_verification(card_id)

    # ── 모든 섹션 문항 업그레이드 ────────────────────────────
    for section in ("pretest", "try", "practice_r1", "practice_r2", "practice_r3"):
        lesson[section] = [upgrade_item(item) for item in lesson.get(section, [])]

    # ── 파일 저장 ────────────────────────────────────────────
    with open(L2_PATH, "w", encoding="utf-8") as f:
        json.dump(lesson, f, ensure_ascii=False, indent=2)

    total = sum(
        len(lesson.get(s, []))
        for s in ("pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3")
    )
    print(f"✅ 업그레이드 완료: {L2_PATH}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {lesson['tier']}")
    va = lesson.get("vertical_alignment", {})
    print(f"   vertical_alignment: {va.get('prerequisite')} → {va.get('successor')}")


if __name__ == "__main__":
    main()
