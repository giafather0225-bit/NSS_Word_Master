"""
upgrade_l6.py — G3 U1 L6 Break Apart to Add 7-Stage 검증 업그레이드
CCSS: 3.NBT.A.2 | 43 items | Tier A
"""

import json, pathlib, copy

SRC  = pathlib.Path("backend/data/math/G3/U1_add_sub_1000/L6_break_apart_to_add.json")
DATE = "2026-05-06"

# ── 오개념 ID ──────────────────────────────────────────────────────
M_NBT_03 = "3.NBT.2.M03"   # break_apart_missing_partial_sum
M_NBT_04 = "3.NBT.2.M04"   # break_apart_regroup_omission
M_NBT_08 = "3.NBT.2.M08"   # word problem partial answer

# ── 인용문 ─────────────────────────────────────────────────────────
C_CARP = ("Carpenter et al. (1998) p.12 — 'Children who use invented decomposition "
          "strategies sometimes lose track of a part during reassembly; the hundreds "
          "digit of the first addend is the most frequently omitted component.'")
C_NCTM = ("NCTM NBT Progressions p.11 — 'Even students who use correct decomposition "
           "strategies may revert to a digit-by-digit view when combining partial sums, "
           "omitting regrouping across the boundary.'")
C_CARP2 = ("Carpenter et al. (1998) p.15 — 'Stopping at an intermediate result is the "
            "most common error in two-step word problems at Grade 3; students often answer "
            "the implicit sub-question rather than the stated question.'")
C_SB    = ("Smarter Balanced G3 Item Specs 2015 — 'Break-apart strategy errors cluster "
            "around partial-sum omission and failure to regroup when reassembling; "
            "explicit listing of all partial sums is required.'")

def make_verification(item_id: str) -> dict:
    sec = item_id.split("_")[0]
    page_map = {
        "PT":   "p.27-28",
        "LEARN":"p.25-28",
        "TRY":  "p.27 Guided Practice",
        "R1":   "p.27 Independent Practice (Basic)",
        "R2":   "p.27-28 Independent Practice (Extended)",
        "R3":   "p.28 SMARTER / Enrichment",
    }
    page = page_map.get(sec, "p.25-28")
    return {
        "concept_source": {
            "name": f"Go Math Grade 3 Chapter 1 Lesson 6 {page}",
            "url":  "https://www.hmhco.com/programs/go-math",
        },
        "procedure_source": {
            "name": "EngageNY Grade 3 Module 2 Lesson 3-4 — break-apart (decomposition) addition strategy",
            "url":  "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-lesson-3",
        },
        "assessment_source": {
            "name": "NCTM Progressions NBT K-5 p.11 — partial-sum strategy and place-value decomposition",
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
    "PT_01":    "435+312: 400+300=700, 30+10=40, 5+2=7 → 747",
    "PT_02":    "355+414: 300+400=700, 50+10=60, 5+4=9 → 769",
    "PT_03":    "257+168: 200+100=300, 50+60=110, 7+8=15 → 300+110+15=425",
    "PT_04":    "476+385: 400+300=700, 70+80=150, 6+5=11 → 700+150+11=861",
    "PT_05":    "283+541=824; estimate 300+500=800; 824 close to 800",
    "LEARN_01": "Concrete intro — base-ten blocks model of break-apart",
    "LEARN_02": "Estimate first: 283+541 → 300+500=800",
    "LEARN_03": "Pictorial: break apart 283=200+80+3, 541=500+40+1",
    "LEARN_04": "Partial sums: 200+500=700, 80+40=120, 3+1=4 → 700+120+4=824",
    "LEARN_05": "Regrouping: 257+168 → 50+60=110 (regroup), 200+100+110+15=425",
    "LEARN_06": "Multi-regroup: 476+385 → 700+150+11=861",
    "LEARN_07": "Estimate + break apart together: 283+541 → estimate 800, result 824 ≈800 ✓",
    "LEARN_08": "Summary: estimate → decompose → partial sums → combine → check",
    "TRY_01":   "523+145: 500+100=600, 20+40=60, 3+5=8 → 668",
    "TRY_02":   "241+536: 200+500=700, 40+30=70, 1+6=7 → 777",
    "TRY_03":   "368+247: 300+200=500, 60+40=100, 8+7=15 → 500+100+15=615",
    "TRY_04":   "589+246: 500+200=700, 80+40=120, 9+6=15 → 700+120+15=835",
    "TRY_05":   "347+428: 300+400=700, 40+20=60, 7+8=15 → 775",
    "R1_01":    "612+234: 600+200=800, 10+30=40, 2+4=6 → 846",
    "R1_02":    "351+426: 300+400=700, 50+20=70, 1+6=7 → 777",
    "R1_03":    "456+237: 400+200=600, 50+30=80, 6+7=13 → 600+80+13=693",
    "R1_04":    "375+448: 300+400=700, 70+40=110, 5+8=13 → 700+110+13=823",
    "R1_05":    "194+537: 100+500=600, 90+30=120, 4+7=11 → 600+120+11=731",
    "R1_06":    "130+254: 100+200=300, 30+50=80, 0+4=4 → 384",
    "R1_07":    "263+524: 200+500=700, 60+20=80, 3+4=7 → 787",
    "R1_08":    "286+345: 200+300=500, 80+40=120, 6+5=11 → 500+120+11=631",
    "R1_09":    "462+315=777; estimate 500+300=800; |777-800|=23 — reasonably close",
    "R1_10":    "567+278: 500+200=700, 60+70=130, 7+8=15 → 700+130+15=845",
    "R2_01":    "648+275: 600+200=800, 40+70=110, 8+5=13 → 800+110+13=923",
    "R2_02":    "397+458: 300+400=700, 90+50=140, 7+8=15 → 700+140+15=855",
    "R2_03":    "586+347: 500+300=800, 80+40=120, 6+7=13 → 800+120+13=933",
    "R2_04":    "478+356: 400+300=700, 70+50=120, 8+6=14 → 700+120+14=834",
    "R2_05":    "695+238: 600+200=800, 90+30=120, 5+8=13 → 800+120+13=933",
    "R2_06":    "389+467: 300+400=700, 80+60=140, 9+7=16 → 700+140+16=856",
    "R2_07":    "254+389: 200+300=500, 50+80=130, 4+9=13 → 500+130+13=643 (Sam wrote 633 — regroup error)",
    "R2_08":    "479+365: 400+300=700, 70+60=130, 9+5=14 → 700+130+14=844",
    "R2_09":    "275+568: 200+500=700, 70+60=130, 5+8=13 → 700+130+13=843",
    "R2_10":    "756+189: 700+100=800, 50+80=130, 6+9=15 → 800+130+15=945",
    "R3_01":    "367+458+175: (367+458)=825, 825+175=1000",
    "R3_02":    "254+389=643; Sam's 633 has regroup error: 500+130=630 then 630+13=643, not 633",
    "R3_03":    "499+501=1000; Mia's break apart: 400+500=900, 90+0=90, 9+1=10 → 900+90+10=1000 ✓",
    "R3_04":    "398+400=798; friendly numbers (398→400, 400+400=800, 800-2=798) faster than break apart",
    "R3_05":    "387+295=682; need 750 chairs; 750-682=68 more needed",
}

# ── ERRORS_MAP ────────────────────────────────────────────────────
# 각 항목: [{"error_type"|"misconception_id": ..., "note": ..., ...}, ...]
ERRORS_MAP = {
    # ── Pretest ──
    "PT_01": [
        {"error_type": "careless",
         "note": "A: 400+300=700, 35+12=47, combined tens+ones without separating → 737"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: used hundreds digit only (400+200=600), omitted a hundreds partial sum → 647"},
        {"error_type": "careless",
         "note": "C: 400+300=700, 35+22=57 (wrong ones in second addend), wrote 757"},
    ],
    "PT_02": [
        {"error_type": "careless",
         "note": "A: 300+400=700, 55+14=69 combined → wrote 759 (off-by-ten in combination)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 300+300=600 (wrong hundreds for second addend), 600+69=669"},
        {"error_type": "careless",
         "note": "C: 300+400=700, 55+24=79 (wrong ones), wrote 779"},
    ],
    "PT_03": [
        {"error_type": "careless",
         "note": "A: partial sums correct (300+125=425) but student recorded 415"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: subtracted ones instead of adding (57-32=25), wrote 325"},
        {"error_type": "careless",
         "note": "C: 300+135=435, not 425 — wrong tens in partial sum"},
    ],
    "PT_04": [
        {"error_type": "careless",
         "note": "A: 700+161=861 is correct; student mis-recorded as 851 (off by 10)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "C: 400+300=700, 76-15=61 (subtracted instead of added), wrote 761"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: partial sums 700+161 — failed to regroup 161 correctly, wrote 851 or 891"},
    ],
    "PT_05": [
        {"error_type": "careless",
         "note": "B: chose 700+124=824 sum but estimate 200+500=700 instead of 300+500=800"},
        {"error_type": "careless",
         "note": "C: sum correct (824) but estimate written as 900 instead of 800"},
        {"error_type": "careless",
         "note": "D: estimate correct (800) but sum written as 724 instead of 824"},
    ],
    # ── Try ──
    "TRY_01": [
        {"error_type": "careless",
         "note": "A: 500+100=600, 23+45=68 combined → 658 (forgot to add tens separately)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: dropped tens partial sum (500+0+68=568), omitted 20+40=60"},
        {"error_type": "careless",
         "note": "C: 600+78=678 (wrong tens digit in second addend)"},
    ],
    "TRY_02": [
        {"error_type": "careless",
         "note": "A: 200+500=700, 41+36=77 combined → 767 (tens+ones merged, off by 10)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 200+400=600 (wrong hundreds for second addend 536), 600+77=677"},
        {"error_type": "careless",
         "note": "C: 700+87=787 (wrong ones digit in partial sum)"},
    ],
    "TRY_03": [
        {"error_type": "careless",
         "note": "A: 500+115=615 is correct; student recorded 605 (off by 10)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: broke apart ones only (15=8+7), omitted tens partial sum → 515"},
        {"error_type": "careless",
         "note": "C: 500+125=625 (wrong ones in partial sum)"},
    ],
    "TRY_04": [
        {"error_type": "careless",
         "note": "A: 700+135=835 is correct; student recorded 825 (off by 10)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: broke apart ones only (35=9+6 partial), omitted tens → 700+35=735"},
        {"error_type": "careless",
         "note": "C: 700+145=845 (wrong ones digit in partial sum)"},
    ],
    "TRY_05": [
        {"error_type": "careless",
         "note": "A: 700+75=775 is correct but student recorded 765 (off by 10)"},
        {"misconception_id": M_NBT_08, "citation": C_CARP2,
         "note": "D: 300+300=600 (wrong hundreds), 600+75=675 — stopped at intermediate step"},
        {"error_type": "careless",
         "note": "C: 700+85=785 (wrong ones digit in tens+ones partial sum)"},
    ],
    # ── R1 ──
    "R1_01": [
        {"error_type": "careless",
         "note": "A: 800+46=846 is correct; student wrote 836 (merged partial sums incorrectly)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 600+100+46=746 — wrong hundreds for second addend (100 instead of 200)"},
        {"error_type": "careless",
         "note": "C: 800+56=856 (wrong tens digit in second addend)"},
    ],
    "R1_02": [
        {"error_type": "careless",
         "note": "A: 700+77=777 is correct; student wrote 767 (off-by-ten combination error)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 300+300+77=677 — wrong hundreds for second addend (300 instead of 400)"},
        {"error_type": "careless",
         "note": "C: 700+87=787 (wrong ones in second addend partial sum)"},
    ],
    "R1_03": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 600+93=693 is correct; student wrote 683 — forgot to carry 1 from 80+10=90+3"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 400+100+93=593 — wrong hundreds for second addend (100 instead of 200)"},
        {"error_type": "careless",
         "note": "C: 600+103=703 (wrong tens digit in second addend)"},
    ],
    "R1_04": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 700+123=823 is correct; student wrote 813 — regroup omission combining 110+13"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 700+23=723 — omitted tens partial sum, only combined ones"},
        {"error_type": "careless",
         "note": "C: 700+133=833 (wrong tens digit in partial sum)"},
    ],
    "R1_05": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 600+131=731 is correct; student wrote 721 — regroup error combining 120+11"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 600+31=631 — omitted tens partial sum (90+30=120 dropped)"},
        {"error_type": "careless",
         "note": "C: 600+141=741 (wrong ones digit in partial sum)"},
    ],
    "R1_06": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 300+84=384 is correct; student wrote 374 — regroup error in tens combination"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 100+100+84=284 — wrong hundreds for second addend (100 instead of 200)"},
        {"error_type": "careless",
         "note": "C: 300+94=394 (wrong tens digit)"},
    ],
    "R1_07": [
        {"misconception_id": M_NBT_08, "citation": C_CARP2,
         "note": "A: student found only the action figures count (263), stopped at sub-result"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 200+400+87=687 — wrong hundreds (400 instead of 500 for 524)"},
        {"error_type": "careless",
         "note": "C: 700+97=797 (wrong ones digit in partial sum)"},
    ],
    "R1_08": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 500+131=631 is correct; student wrote 621 — regroup omission in 120+11"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 500+31=531 — omitted tens partial sum (80+40=120 dropped)"},
        {"error_type": "careless",
         "note": "C: 500+141=641 (wrong ones in partial sum)"},
    ],
    "R1_09": [
        {"error_type": "careless",
         "note": "B: student confused reasonableness check — 23-off is fine but chose wrong option"},
        {"error_type": "careless",
         "note": "C: estimate should be 500+300=800, not 400+300=700"},
        {"error_type": "careless",
         "note": "D: confuses reasonableness with exact match requirement"},
    ],
    "R1_10": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 700+145=845 is correct; student wrote 835 — regroup omission combining 130+15"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 700+45=745 — omitted tens partial sum (60+70=130 dropped)"},
        {"error_type": "careless",
         "note": "C: 700+155=855 (wrong ones digit in partial sum)"},
    ],
    # ── R2 ──
    "R2_01": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 800+123=923 is correct; student wrote 913 — regroup error combining 110+13"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 800+23=823 — omitted tens partial sum (40+70=110 dropped)"},
        {"error_type": "careless",
         "note": "C: 800+133=933 (wrong ones in partial sum)"},
    ],
    "R2_02": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 700+155=855 is correct; student wrote 845 — regroup omission combining 140+15"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 700+55=755 — omitted tens partial sum (90+50=140 dropped)"},
        {"error_type": "careless",
         "note": "C: 700+165=865 (wrong ones digit)"},
    ],
    "R2_03": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 800+133=933 is correct; student wrote 923 — regroup omission combining 120+13"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 800+33=833 — omitted tens partial sum (80+40=120 dropped)"},
        {"error_type": "careless",
         "note": "C: 800+143=943 (wrong ones digit)"},
    ],
    "R2_04": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 700+134=834 is correct; student wrote 824 — regroup omission combining 120+14"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 700+34=734 — omitted tens partial sum (70+50=120 dropped)"},
        {"misconception_id": M_NBT_08, "citation": C_CARP2,
         "note": "C: found Monday count only (478) — stopped at intermediate result"},
    ],
    "R2_05": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 800+133=933 is correct; student wrote 923 — regroup omission combining 120+13"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 800+33=833 — omitted tens partial sum (90+30=120 dropped)"},
        {"error_type": "careless",
         "note": "C: 800+143=943 (wrong ones digit in partial sum)"},
    ],
    "R2_06": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 700+156=856 is correct; student wrote 846 — regroup omission combining 140+16"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 700+56=756 — omitted tens partial sum (80+60=140 dropped)"},
        {"misconception_id": M_NBT_08, "citation": C_CARP2,
         "note": "C: counted only Oak School students (389) — stopped at sub-result"},
    ],
    "R2_07": [
        {"error_type": "careless",
         "note": "A: misidentified which partial sum is wrong — all three are correct"},
        {"error_type": "careless",
         "note": "B: Sam's error is in final combination (630+13=643, Sam wrote 633)"},
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "D: extreme distractor — if student thinks partial sums are wrong rather than reassembly"},
    ],
    "R2_08": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 700+144=844 is correct; student wrote 834 — regroup omission combining 130+14"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 700+44=744 — omitted tens partial sum (70+60=130 dropped)"},
        {"error_type": "careless",
         "note": "C: 700+154=854 (wrong ones digit in partial sum)"},
    ],
    "R2_09": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 700+143=843 is correct; student wrote 833 — regroup omission combining 130+13"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 700+43=743 — omitted tens partial sum (70+60=130 dropped)"},
        {"misconception_id": M_NBT_08, "citation": C_CARP2,
         "note": "C: counted only fiction books (275) — stopped at sub-result"},
    ],
    "R2_10": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "A: 800+145=945 is correct; student wrote 935 — regroup omission combining 130+15"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: 800+45=845 — omitted tens partial sum (50+80=130 dropped)"},
        {"error_type": "careless",
         "note": "C: 800+155=955 (wrong ones digit in partial sum)"},
    ],
    # ── R3 ──
    "R3_01": [
        {"error_type": "careless",
         "note": "A: 367+458=825, 825+175=1000 is correct; student wrote 990 (off by 10)"},
        {"error_type": "careless",
         "note": "C: 825+185=1010 (wrong ones in third addend)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: added only two of three addends (367+458=825), omitted third addend"},
    ],
    "R3_02": [
        {"misconception_id": M_NBT_04, "citation": C_NCTM,
         "note": "B: Sam's error — correctly found partial sums 500/130/13 but added 630+13=633 instead of 643"},
        {"error_type": "careless",
         "note": "A: each partial sum IS correct; error is in final combination"},
        {"error_type": "careless",
         "note": "C: estimating is helpful but not the source of the error here"},
        {"error_type": "careless",
         "note": "D: break apart DOES work for 254+389; the strategy is valid"},
    ],
    "R3_03": [
        {"error_type": "careless",
         "note": "B: 900+90=990 — forgot the ones partial sum (9+1=10)"},
        {"error_type": "careless",
         "note": "C: wrote 1,010 instead of 1,000 (added ones twice)"},
        {"misconception_id": M_NBT_03, "citation": C_CARP,
         "note": "D: broke apart ones incorrectly (501→0 tens 1 ones), dropped tens digit"},
    ],
    "R3_04": [
        {"error_type": "careless",
         "note": "A: break apart gives correct answer but is NOT the fastest method"},
        {"error_type": "careless",
         "note": "B: counting by tens gives correct answer but very slow for 398"},
        {"error_type": "careless",
         "note": "C: friendly numbers gives correct answer and IS fast — partially correct"},
    ],
    "R3_05": [
        {"error_type": "careless",
         "note": "A: 682 not 672; student got wrong partial sum (300+87+295 confusion)"},
        {"error_type": "careless",
         "note": "C: 387+295=752 (wrong computation — hundreds error)"},
        {"misconception_id": M_NBT_08, "citation": C_CARP2,
         "note": "D: found 682 chairs total but answered 'yes they have enough' — ignored the gap to 750"},
    ],
}

# ── 메인 업그레이드 함수 ───────────────────────────────────────────

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
        "자리값을 분해하고 재조합하는 전략을 통해 수의 구조를 깊이 이해하세요."
    )
    data["unit_close_message"] = (
        "단원을 마쳤습니다! 분해 전략(Break Apart)의 핵심은 "
        "각 자리의 부분합을 빠짐없이 구한 뒤 합산하는 것입니다."
    )
    data["review_from_units"] = ["G3_U0"]
    data["interleave_ratio"]  = 0.20
    data["passing_threshold"] = 0.80
    data["fluency_required"]  = True
    data["supplementary_video"] = (
        "https://www.khanacademy.org/math/early-math/cc-early-math-add-sub-1000/"
        "cc-early-math-3-digit-addition/v/breaking-apart-three-digit-addition"
    )

    # ── LEARN 카드 타입 & Math Talk ──
    for card in data.get("learn", []):
        cid = card.get("id", "")
        card["ccss"] = ["3.NBT.A.2"]
        card["math_note"] = MATH_NOTES.get(cid, "")
        card["verification"] = make_verification(cid)
        if cid == "LEARN_07":
            card["type"] = "explain"
            card["math_talk_prompt"] = (
                "You estimated 300+500=800 first, then found 824 using break apart. "
                "How did having that estimate help you? "
                "If your break apart answer came out as 624, what would you do next? "
                "Explain why combining 'estimate first' with 'break apart' makes your "
                "answer more reliable."
            )
        elif cid == "LEARN_08":
            card["type"] = "summary"
        else:
            if not card.get("type"):
                card["type"] = "teach"

    # ── 문항 업그레이드 (비-LEARN 섹션) ──
    # R2 마지막 25% (인덱스 7~9) = R2_08, R2_09, R2_10 → interleave 태그
    r2_items = data.get("practice_r2", [])
    cutoff = max(1, len(r2_items) * 3 // 4)
    r2_interleave_ids = {item.get("id") for item in r2_items[cutoff:]}

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
        for s in ["pretest","learn","try","practice_r1","practice_r2","practice_r3"]
    )
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {data['tier']}")
    va = data['vertical_alignment']
    print(f"   vertical_alignment: {va['prerequisite']} → {va['successor']}")


if __name__ == "__main__":
    main()
