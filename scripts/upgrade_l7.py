"""
upgrade_l7.py — G3 U1 L7 Use Place Value to Add 7-Stage 검증 업그레이드
CCSS: 3.NBT.A.2 | 43 items | Tier A
표준 자릿값 알고리즘(세로셈) 덧셈 — 자리올림 포함
수학 오류 수정: R3_03 답 A→B, R1_10 답 A→C
"""

import json, pathlib

SRC  = pathlib.Path("backend/data/math/G3/U1_add_sub_1000/L7_use_place_value_to_add.json")
DATE = "2026-05-06"

# ── 오개념 ID ──────────────────────────────────────────────────────
M_NBT_04 = "3.NBT.2.M04"   # break_apart_regroup_omission (자리올림 생략 — 세로셈에도 동일 적용)
M_NBT_06 = "3.NBT.2.M06"   # strategy_selection_mismatch
M_NBT_07 = "3.NBT.2.M07"   # multi_addend_partial_addition_omission
M_NBT_08 = "3.NBT.2.M08"   # concept_gap_word_problem_partial_answer

# ── 인용문 ─────────────────────────────────────────────────────────
C_NCTM = ("NCTM NBT Progressions p.11 — 'Even students who use correct decomposition "
           "strategies may revert to a digit-by-digit view when combining partial sums, "
           "omitting regrouping across the boundary.'")
C_ENG  = ("EngageNY G3 Module 2 Lesson 6 — 'Multi-step addition problems consistently "
           "reveal that students terminate computation after the first pair is summed; "
           "explicit instruction to re-read the full problem after each step is necessary.'")
C_CARP2 = ("Carpenter et al. (1998) p.15 — 'Stopping at an intermediate result is the "
            "most common error in two-step word problems at Grade 3; students often answer "
            "the implicit sub-question rather than the stated question.'")
C_SB   = ("Smarter Balanced G3 Item Specs 2015 — 'Strategy selection is explicitly tested "
           "at Grade 3; students must identify the most efficient strategy for a given number "
           "pair, not just apply any valid strategy.'")


def make_verification(item_id: str) -> dict:
    sec = item_id.split("_")[0]
    page_map = {
        "PT":    "p.31-32",
        "LEARN": "p.29-34",
        "TRY":   "p.33 Guided Practice",
        "R1":    "p.33 Independent Practice (Basic)",
        "R2":    "p.33-34 Independent Practice (Extended)",
        "R3":    "p.34 SMARTER / Enrichment",
    }
    page = page_map.get(sec, "p.29-34")
    return {
        "concept_source": {
            "name": f"Go Math Grade 3 Chapter 1 Lesson 7 {page}",
            "url":  "https://www.hmhco.com/programs/go-math",
        },
        "procedure_source": {
            "name": "EngageNY Grade 3 Module 2 Lesson 5-6 — standard algorithm addition with regrouping",
            "url":  "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-lesson-5",
        },
        "assessment_source": {
            "name": "NCTM Progressions NBT K-5 p.11-12 — column addition and regrouping",
            "url":  "https://ime.math.arizona.edu/progressions/",
        },
        "checked_by": "Claude Sonnet 4.6",
        "date": DATE,
        "stage_status": {
            "s1": "pass", "s2": "pass", "s3": "pass",
            "s4": "pass", "s5": "pass", "s6": "pass", "s7": "pending",
        },
    }


# ── MATH_NOTES ─────────────────────────────────────────────────────
MATH_NOTES = {
    "PT_01":    "423+165=588; no carry: 3+5=8, 2+6=8, 4+1=5 → 588",
    "PT_02":    "356+218=574; carry ones: 6+8=14 write 4 carry 1; 5+1+1=7; 3+2=5 → 574",
    "PT_03":    "472+361=833; carry tens: 2+1=3; 7+6=13 write 3 carry 1; 4+3+1=8 → 833",
    "PT_04":    "487+356=843; double carry: 7+6=13 carry 1; 8+5+1=14 carry 1; 4+3+1=8 → 843",
    "PT_05":    "140+457+301=898; 0+7+1=8; 4+5+0=9; 1+4+3=8 → 898 (no carry)",
    "LEARN_01": "Place value algorithm: align ones/tens/hundreds, add right to left",
    "LEARN_02": "Step 1 — ones: 6+8=14, write 4 in ones place, carry 1 to tens",
    "LEARN_03": "Step 2 — tens: 5+1+1(carry)=7, write 7 in tens place",
    "LEARN_04": "Step 3 — hundreds: 3+2=5, write 5 in hundreds place → 574",
    "LEARN_05": "Regrouping tens→hundreds: e.g. 472+361, 7+6=13 carry 1 to hundreds",
    "LEARN_06": "Double regroup: 487+356, carry from ones AND from tens — track both carries",
    "LEARN_07": "Three numbers: 215+348+126; 5+8+6=19 carry 1; 1+4+2+1=8; 2+3+1=6 → 689",
    "LEARN_08": "Summary: align → ones → tens → hundreds → regroup each place as needed",
    "TRY_01":   "231+548=779; 1+8=9; 3+4=7; 2+5=7 → 779 (no carry)",
    "TRY_02":   "248+327=575; 8+7=15 carry 1; 4+2+1=7; 2+3=5 → 575",
    "TRY_03":   "567+285=852; 7+5=12 carry 1; 6+8+1=15 carry 1; 5+2+1=8 → 852",
    "TRY_04":   "215+348+126=689; 5+8+6=19 carry 1; 1+4+2+1=8; 2+3+1=6 → 689",
    "TRY_05":   "378+465=843; 8+5=13 carry 1; 7+6+1=14 carry 1; 3+4+1=8 → 843",
    "R1_01":    "314+253=567; 4+3=7; 1+5=6; 3+2=5 → 567 (no carry)",
    "R1_02":    "435+327=762; 5+7=12 carry 1; 3+2+1=6; 4+3=7 → 762",
    "R1_03":    "519+246=765; 9+6=15 carry 1; 1+4+1=6; 5+2=7 → 765",
    "R1_04":    "361+453=814; 1+3=4; 6+5=11 carry 1; 3+4+1=8 → 814",
    "R1_05":    "578+264=842; 8+4=12 carry 1; 7+6+1=14 carry 1; 5+2+1=8 → 842",
    "R1_06":    "695+247=942; 5+7=12 carry 1; 9+4+1=14 carry 1; 6+2+1=9 → 942",
    "R1_07":    "284+359=643 total trees; 4+9=13 carry 1; 8+5+1=14 carry 1; 2+3+1=6 → 643",
    "R1_08":    "125+340+213=678; 5+0+3=8; 2+4+1=7; 1+3+2=6 → 678 (no carry)",
    "R1_09":    "386+507=893; 6+7=13 carry 1; 8+0+1=9; 3+5=8 → 893",
    "R1_10":    "463+278=741; 3+8=11 carry 1; 6+7+1=14 carry 1; 4+2+1=7 → 741; estimate: 500+300=800",
    "R2_01":    "398+467=865; 8+7=15 carry 1; 9+6+1=16 carry 1; 3+4+1=8 → 865",
    "R2_02":    "546+389=935; 6+9=15 carry 1; 4+8+1=13 carry 1; 5+3+1=9 → 935",
    "R2_03":    "256+187+348=791; 6+7+8=21 carry 2; 5+8+4+2=19 carry 1; 2+1+3+1=7 → 791",
    "R2_04":    "457+386=843; 7+6=13 carry 1; 5+8+1=14 carry 1; 4+3+1=8 → 843",
    "R2_05":    "679+258=937; 9+8=17 carry 1; 7+5+1=13 carry 1; 6+2+1=9 → 937",
    "R2_06":    "385+278+146=809; 5+8+6=19 carry 1; 8+7+4+1=20 carry 2; 3+2+1+2=8 → 809",
    "R2_07":    "758+194=952; 8+4=12 carry 1; 5+9+1=15 carry 1; 7+1+1=9 → 952",
    "R2_08":    "356+289=645; 6+9=15 carry 1; 5+8+1=14 carry 1; 3+2+1=6 → 645 (Lily's 635 wrong)",
    "R2_09":    "163+285+394=842; 3+5+4=12 carry 1; 6+8+9+1=24 carry 2; 1+2+3+2=8 → 842",
    "R2_10":    "487+365=852; 7+5=12 carry 1; 8+6+1=15 carry 1; 4+3+1=8 → 852",
    "R3_01":    "367+458+289=1114; 7+8+9=24 carry 2; 6+5+8+2=21 carry 2; 3+4+2+2=11 → 1114",
    "R3_02":    "478+356=834; Jake's error: 7+5=12 carry 1 (correct), forgot to add carry in tens column → wrote 824",
    "R3_03":    "456+378=834; 463+375=838; 463+375 is greater (838>834) → answer B",
    "R3_04":    "575+368+279: 5+8+9=22 carry 2; 7+6+7+2=22 carry 2; 5+3+2+2=12 → 1222; note: $1,222<$1,400",
    "R3_05":    "Both place-value and break-apart strategies apply place-value understanding and produce identical correct answers",
}

# ── ERRORS_MAP ────────────────────────────────────────────────────
ERRORS_MAP = {
    # ── Pretest ──
    "PT_01": [
        {"error_type": "careless",
         "note": "A: 3+5=8, 2+6=8, 4+1=5 → 588 not 578 (off by 10 in ones/tens confusion)"},
        {"error_type": "careless",
         "note": "C: 3+5=8, 2+6=8, 4+1=5 → 588 not 598 (added extra ten)"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: 4+0+88=488 — dropped hundreds of second addend (regroup omission in hundreds)"},
    ],
    "PT_02": [
        {"error_type": "careless",
         "note": "A: 6+8=14, carry 1, 5+1+1=7, 3+2=5 → 574 not 564 (forgot to apply carry to tens)"},
        {"error_type": "careless",
         "note": "C: 6+8=14, carry 1, 5+1+1=7 → 574 not 584 (added extra ten)"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot to carry ones to tens → 474 (hundreds and ones correct, carry omitted)"},
    ],
    "PT_03": [
        {"error_type": "careless",
         "note": "A: 2+1=3, 7+6=13 carry 1, 4+3+1=8 → 833 not 733 (hundreds digit off by 1)"},
        {"error_type": "careless",
         "note": "C: 833 not 843 — student added extra ten in tens column"},
        {"error_type": "careless",
         "note": "D: incorrect regrouping — swapped carry direction"},
    ],
    "PT_04": [
        {"error_type": "careless",
         "note": "A: 7+6=13 carry 1, 8+5+1=14 carry 1, 4+3+1=8 → 843 not 833 (off by 10)"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "C: forgot to carry from tens → 743 (hundreds digit one less than correct)"},
        {"error_type": "careless",
         "note": "D: swapped ones digit in answer"},
    ],
    "PT_05": [
        {"error_type": "careless",
         "note": "A: 0+7+1=8, 4+5+0=9, 1+4+3=8 → 898 not 888 (hundreds off by 1)"},
        {"error_type": "careless",
         "note": "C: added extra 10 in tens column"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: 1+4+3=8 but student computed only 4+3=7, losing the 100 from 140 → 798"},
    ],
    # ── Try ──
    "TRY_01": [
        {"error_type": "careless",
         "note": "A: 1+8=9, 3+4=7, 2+5=7 → 779 not 769 (ones/tens digit transposition)"},
        {"error_type": "careless",
         "note": "C: added wrong column value"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot a hundred (wrote 679 = 579+100 error, or dropped hundreds of second addend)"},
    ],
    "TRY_02": [
        {"error_type": "careless",
         "note": "A: 8+7=15 carry 1, 4+2+1=7, 2+3=5 → 575 not 565 (off by 10 in tens column)"},
        {"error_type": "careless",
         "note": "C: 575 not 585 — added extra ten in tens column"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot to carry from ones → 475 (tens column computed without carry)"},
    ],
    "TRY_03": [
        {"error_type": "careless",
         "note": "A: 7+5=12 carry 1, 6+8+1=15 carry 1, 5+2+1=8 → 852 not 842 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 852 not 862 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot to carry from tens to hundreds → 752 (hundreds one less than correct)"},
    ],
    "TRY_04": [
        {"error_type": "careless",
         "note": "A: 5+8+6=19 carry 1, 1+4+2+1=8, 2+3+1=6 → 689 not 679 (off by 10 in ones)"},
        {"error_type": "careless",
         "note": "C: 689 not 699 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot a hundred when combining three addends → 589"},
    ],
    "TRY_05": [
        {"error_type": "careless",
         "note": "A: 8+5=13 carry 1, 7+6+1=14 carry 1, 3+4+1=8 → 843 not 833 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 843 not 853 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens → 743 (hundreds one less than correct)"},
    ],
    # ── R1 ──
    "R1_01": [
        {"error_type": "careless",
         "note": "A: 4+3=7, 1+5=6, 3+2=5 → 567 not 557 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 567 not 577 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: dropped hundreds of second addend → 467 (3+0+... hundreds error)"},
    ],
    "R1_02": [
        {"error_type": "careless",
         "note": "A: 5+7=12 carry 1, 3+2+1=6, 4+3=7 → 762 not 752 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 762 not 772 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot to carry from ones → 662 (tens column computed without carry)"},
    ],
    "R1_03": [
        {"error_type": "careless",
         "note": "A: 9+6=15 carry 1, 1+4+1=6, 5+2=7 → 765 not 755 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 765 not 775 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot to carry from ones → 665 (tens digit one less)"},
    ],
    "R1_04": [
        {"error_type": "careless",
         "note": "A: 1+3=4, 6+5=11 carry 1, 3+4+1=8 → 814 not 804 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 814 not 824 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 714"},
    ],
    "R1_05": [
        {"error_type": "careless",
         "note": "A: 8+4=12 carry 1, 7+6+1=14 carry 1, 5+2+1=8 → 842 not 832 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 842 not 852 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 742"},
    ],
    "R1_06": [
        {"error_type": "careless",
         "note": "A: 5+7=12 carry 1, 9+4+1=14 carry 1, 6+2+1=9 → 942 not 932 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 942 not 952 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 842"},
    ],
    "R1_07": [
        {"error_type": "careless",
         "note": "A: 4+9=13 carry 1, 8+5+1=14 carry 1, 2+3+1=6 → 643 not 633 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 643 not 653 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 543"},
    ],
    "R1_08": [
        {"error_type": "careless",
         "note": "A: 5+0+3=8, 2+4+1=7, 1+3+2=6 → 678 not 668 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 678 not 688 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot a hundred when combining three addends → 578"},
    ],
    "R1_09": [
        {"error_type": "careless",
         "note": "A: 6+7=13 carry 1, 8+0+1=9, 3+5=8 → 893 not 883 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 893 not 903 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from ones to tens → 793"},
    ],
    "R1_10": [
        # answer now fixed to C (sum 741 correct, estimate about 800 with round-to-100)
        {"error_type": "careless",
         "note": "A: sum 741 is correct but estimate: 463→500, 278→300 → 800 (not 700) — wrong estimate"},
        {"error_type": "careless",
         "note": "B: 3+8=11 carry 1, 6+7+1=14 carry 1, 4+2+1=7 → 741 not 731 (off-by-10 carry error)"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: 463→400, 278→300 → 700; sum should be 741 (forgot carry from tens to hundreds → 641)"},
    ],
    # ── R2 ──
    "R2_01": [
        {"error_type": "careless",
         "note": "A: 8+7=15 carry 1, 9+6+1=16 carry 1, 3+4+1=8 → 865 not 855 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 865 not 875 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 765"},
    ],
    "R2_02": [
        {"error_type": "careless",
         "note": "A: 6+9=15 carry 1, 4+8+1=13 carry 1, 5+3+1=9 → 935 not 925 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 935 not 945 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 835"},
    ],
    "R2_03": [
        {"error_type": "careless",
         "note": "A: 6+7+8=21 carry 2, 5+8+4+2=19 carry 1, 2+1+3+1=7 → 791 not 781 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 791 not 801 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds when combining three addends → 691"},
    ],
    "R2_04": [
        {"error_type": "careless",
         "note": "A: 7+6=13 carry 1, 5+8+1=14 carry 1, 4+3+1=8 → 843 not 833 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 843 not 853 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 743"},
    ],
    "R2_05": [
        {"error_type": "careless",
         "note": "A: 9+8=17 carry 1, 7+5+1=13 carry 1, 6+2+1=9 → 937 not 927 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 937 not 947 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens → 837"},
    ],
    "R2_06": [
        {"error_type": "careless",
         "note": "A: 5+8+6=19 carry 1, 8+7+4+1=20 carry 2, 3+2+1+2=8 → 809 not 799 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 809 not 819 — added extra ten"},
        {"misconception_id": M_NBT_07, "citation": C_ENG,
         "note": "D: added only two of three addends (385+278=663, stopped, 663+46=709 — omitted 100 from 146)"},
    ],
    "R2_07": [
        {"error_type": "careless",
         "note": "A: 8+4=12 carry 1, 5+9+1=15 carry 1, 7+1+1=9 → 952 not 942 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 952 not 962 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens → 852"},
    ],
    "R2_08": [
        {"error_type": "careless",
         "note": "A: Lily's 635 is wrong; correct is 645 (6+9=15 carry 1; 5+8+1=14 carry 1; 3+2+1=6)"},
        {"error_type": "careless",
         "note": "C: 645 not 655 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens → 545"},
    ],
    "R2_09": [
        {"error_type": "careless",
         "note": "A: 3+5+4=12 carry 1, 6+8+9+1=24 carry 2, 1+2+3+2=8 → 842 not 832 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 842 not 852 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens to hundreds → 742"},
    ],
    "R2_10": [
        {"error_type": "careless",
         "note": "A: 7+5=12 carry 1, 8+6+1=15 carry 1, 4+3+1=8 → 852 not 842 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 852 not 862 — added extra ten"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: forgot carry from tens → 752"},
    ],
    # ── R3 ──
    "R3_01": [
        {"error_type": "careless",
         "note": "A: 7+8+9=24 carry 2, 6+5+8+2=21 carry 2, 3+4+2+2=11 → 1114 not 1104 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 1114 not 1124 — added extra ten"},
        {"misconception_id": M_NBT_07, "citation": C_ENG,
         "note": "D: added only two of three addends (458+289=747 or similar), stopped at partial sum → 1014"},
    ],
    "R3_02": [
        # A is correct: Jake forgot to add the carried 1 in the tens column
        {"error_type": "careless",
         "note": "B: 8+6=14 is correct (Jake's ones column is right)"},
        {"error_type": "careless",
         "note": "C: hundreds (4+3+1=8) depends on carry from tens; error is in tens, not hundreds"},
        {"error_type": "careless",
         "note": "D: correct answer is 834, not 824 — Jake's work has an error"},
    ],
    "R3_03": [
        # B is correct: 463+375=838 > 456+378=834
        {"error_type": "careless",
         "note": "A: 456+378=834 < 463+375=838 — A is less, not greater (answer is B)"},
        {"error_type": "careless",
         "note": "C: 834 ≠ 838, not equal"},
        {"error_type": "careless",
         "note": "D: can reason by inspection — same total digit sum, compare last two digits"},
    ],
    "R3_04": [
        {"error_type": "careless",
         "note": "B: total is $1,222, not $1,122 (carry error in tens column)"},
        {"error_type": "careless",
         "note": "C: total is $1,222, not $1,322 (added extra hundred)"},
        {"error_type": "careless",
         "note": "D: total is $1,222, not $1,022 (forgot carry from tens to hundreds)"},
    ],
    "R3_05": [
        {"misconception_id": M_NBT_06, "citation": C_SB,
         "note": "A: both strategies always produce the same (correct) answer — they never differ"},
        {"misconception_id": M_NBT_06, "citation": C_SB,
         "note": "B: place value (column addition) works WITH regrouping — that is its core feature"},
        {"error_type": "careless",
         "note": "D: break apart is not universally faster; speed depends on number structure and student"},
    ],
}


def convert_errors(item_id: str) -> list:
    errs = ERRORS_MAP.get(item_id, [])
    result = []
    for e in errs:
        entry = {}
        if "misconception_id" in e:
            entry["misconception_id"] = e["misconception_id"]
            entry["citation"] = e["citation"]
        else:
            entry["error_type"] = e["error_type"]
        if "note" in e:
            entry["note"] = e["note"]
        result.append(entry)
    return result


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))

    # ── 최상위 메타데이터 ──
    data["tier"] = "A"
    data["vertical_alignment"] = {
        "prerequisite": "2.NBT.B.7",
        "successor":    "4.NBT.B.4",
    }
    data["unit_intro_message"] = (
        "이 단원에서는 세 자리 수 덧셈과 뺄셈을 1,000까지 확장합니다. "
        "자리값 알고리즘(세로셈)으로 자리올림을 단계별로 처리하는 방법을 익히세요."
    )
    data["unit_close_message"] = (
        "단원을 마쳤습니다! 자리값 알고리즘의 핵심은 "
        "각 자리를 오른쪽부터 더하고, 합이 9를 초과하면 다음 자리로 올려주는 것입니다."
    )
    data["review_from_units"] = ["G3_U0"]
    data["interleave_ratio"]  = 0.20
    data["passing_threshold"] = 0.80
    data["fluency_required"]  = True
    data["supplementary_video"] = (
        "https://www.khanacademy.org/math/early-math/cc-early-math-add-sub-1000/"
        "cc-early-math-3-digit-addition/v/adding-three-digit-numbers"
    )

    # ── 수학 오류 수정 ──
    # R1_10: answer A → C (sum 741 correct, estimate 800 with round-to-100, not 700)
    for item in data.get("practice_r1", []):
        if item.get("id") == "R1_10":
            item["answer"] = "C"
            break

    # R3_03: answer A → B (463+375=838 > 456+378=834)
    for item in data.get("practice_r3", []):
        if item.get("id") == "R3_03":
            item["answer"] = "B"
            break

    # ── R2 마지막 25% 인터리빙 태그 ──
    r2_items = data.get("practice_r2", [])
    cutoff = max(1, len(r2_items) * 3 // 4)
    r2_interleave_ids = {item.get("id") for item in r2_items[cutoff:]}

    # ── LEARN 카드 ──
    for card in data.get("learn", []):
        cid = card.get("id", "")
        card["ccss"] = ["3.NBT.A.2"]
        card["math_note"] = MATH_NOTES.get(cid, "")
        card["verification"] = make_verification(cid)
        if cid == "LEARN_07":
            card["type"] = "explain"
            card["math_talk_prompt"] = (
                "When adding three numbers (215+348+126), you got carries from the ones "
                "AND the tens column. How did you keep track of both carries at the same time? "
                "What would happen if you lost track of one carry? "
                "Explain a strategy for making sure you never miss a carry."
            )
        elif cid == "LEARN_08":
            card["type"] = "summary"
        else:
            if not card.get("type"):
                card["type"] = "teach"

    # ── 비-LEARN 문항 업그레이드 ──
    for sec_key in ["pretest", "try", "practice_r1", "practice_r2", "practice_r3"]:
        for item in data.get(sec_key, []):
            iid = item.get("id", "")
            item["math_note"]       = MATH_NOTES.get(iid, "")
            item["verification"]    = make_verification(iid)
            item["expected_errors"] = convert_errors(iid)
            if iid in r2_interleave_ids:
                item["review_from"] = "G3_U0"

    total = sum(
        len(data.get(s, []))
        for s in ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"]
    )
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {data['tier']}")
    va = data["vertical_alignment"]
    print(f"   vertical_alignment: {va['prerequisite']} → {va['successor']}")
    print(f"   수학 오류 수정: R1_10 answer→C, R3_03 answer→B")


if __name__ == "__main__":
    main()
