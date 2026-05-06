#!/usr/bin/env python3
"""
G3 U1 L1 7-Stage 업그레이드 스크립트 (일회성)
실행: python3 scripts/upgrade_l1.py
결과: L1_number_patterns.json 인플레이스 업그레이드
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
L1_PATH = REPO_ROOT / "backend/data/math/G3/U1_add_sub_1000/L1_number_patterns.json"

# ─── Triple-Source URL 상수 ───────────────────────────────────────────────────
CONCEPT_SRC = {
    "name": "Illustrative Mathematics G3 Unit 1 Lesson 1 — Teacher Summary",
    "url": "https://curriculum.illustrativemathematics.org/k5/teachers/grade-3/unit-1/lesson-1/teacher-lesson-summary"
}
PROCEDURE_SRC = {
    "name": "EngageNY Grade 3 Module 1 Topic A Lesson 1",
    "url": "https://www.engageny.org/resource/grade-3-mathematics-module-1-topic-a-lesson-1"
}
ASSESSMENT_SRC = {
    "name": "Smarter Balanced Grade 3 Sample Items — 3.OA.D.9",
    "url": "https://sampleitems.smarterbalanced.org/"
}

# ─── Misconception ID 상수 ────────────────────────────────────────────────────
M01 = "3.OA.D.9.M01"  # commutative_confusion
M02 = "3.OA.D.9.M02"  # odd_even_sum_rule
M03 = "3.OA.D.9.M03"  # addition_table_row_pattern
M04 = "3.OA.D.9.M04"  # diagonal_pattern_direction
M05 = "3.OA.D.9.M05"  # doubles_pattern_generalization
M06 = "3.OA.D.9.M06"  # skip_counting_rule_application
M07 = "3.OA.D.9.M07"  # commutativity_symmetry_misread
M08 = "3.OA.D.9.M08"  # pattern_rule_vs_specific_case

# ─── Citation 문자열 (misconceptions/3.OA.D.9.json 그대로) ────────────────────
CITE = {
    M01: "NCTM OA Progressions p.6 — 'Students may conflate the two addition properties when they only see symbolic examples without concrete/pictorial models.'",
    M02: "Ashlock (2010) p.22 — 'Children often over-generalize even/odd rules from multiplication to addition without testing.'",
    M03: "EngageNY G3 Module 1 Lesson 1 Teacher Edition — 'A common error is that students report the row header number as the increment.'",
    M04: "Illustrative Mathematics Grade 3 Unit 1 — 'Students benefit from explicitly labeling diagonals before making claims about patterns.'",
    M05: "Burger & Shaughnessy (2012) p.41 — 'Overgeneralizing doubles as the only source of even sums is a persistent misconception through G4.'",
    M06: "NCTM OA Progressions p.8 — 'Students must distinguish between the generator (rule) and the starting value of a sequence.'",
    M07: "Smarter Balanced G3 Item Specs 2015 — 'Symmetry of addition table is a high-Bloom item; expect precision errors in how symmetry is described.'",
    M08: "NCTM OA Progressions p.9 — 'Moving from noticing a pattern to articulating a generalized rule requires explicit instructional scaffolding.'",
}


def make_mid(mid):
    return {"misconception_id": mid, "citation": CITE[mid]}


def careless(note):
    return {"error_type": "careless", "note": note}


# ─── 아이템별 expected_errors 새 포맷 매핑 ────────────────────────────────────
# 형식: item_id → list of error dicts (misconception_id + citation 또는 careless)
ERRORS_MAP = {
    # ── PRETEST ──────────────────────────────────────────────────────────────
    "PT_01": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Confused Commutative Property with Identity Property (a+0=a)"},
        {**{"error_type": "careless"}, "wrong_choice": "C",
         "note": "True fact but does not demonstrate Commutative Property"},
        {**{"error_type": "careless"}, "wrong_choice": "D",
         "note": "True fact but does not demonstrate Commutative Property"},
    ],
    "PT_02": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Believes adding 0 yields 0 — confuses Identity Property behavior"},
        {**{"error_type": "careless"}, "wrong_choice": "B",
         "note": "Concatenated digits (80) instead of computing"},
        {**{"error_type": "careless"}, "wrong_choice": "D",
         "note": "Added 1 instead of 0"},
    ],
    "PT_03": [
        {**make_mid(M02), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "3+4=7 (odd); applies incorrect odd/even rule"},
        {**make_mid(M02), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "7+2=9 (odd); applies incorrect odd/even rule"},
        {**make_mid(M02), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "9+6=15 (odd); applies incorrect odd/even rule"},
    ],
    "PT_04": [
        {**make_mid(M06), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Applied skip-count of 1 instead of 2 — confuses increment with starting value"},
        {**make_mid(M06), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Applied skip-count of 3 instead of 2"},
        {**{"error_type": "careless"}, "wrong_choice": "D",
         "note": "Added 4 instead of 2"},
    ],
    "PT_05": [
        {**{"error_type": "careless"}, "wrong_choice": "A",
         "note": "Confused addition-table row pattern with skip-count by 2"},
        {**make_mid(M03), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Chose the row label (3) as the increment — classic row-pattern error"},
        {**make_mid(M03), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Does not recognize increasing pattern in the addition table row"},
    ],

    # ── TRY ──────────────────────────────────────────────────────────────────
    "TRY_01": [
        {**{"error_type": "careless"}, "wrong_choice": "B",
         "note": "Added the sum to one addend (9+3=12)"},
        {**make_mid(M01), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Confused Commutative Property with subtraction / opposite operation"},
        {**{"error_type": "careless"}, "wrong_choice": "D",
         "note": "Doubled one addend (3+3=6)"},
    ],
    "TRY_02": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Confused Identity Property (adding 0) with Commutative Property (switching order)"},
        {**make_mid(M08), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Cannot recognize 5+0=5 as an instance of a named property rule"},
    ],
    "TRY_03": [
        {**make_mid(M02), "wrong_choice": "B", "error_type": "concept_gap",
         "note": "Both addends are odd so assumed sum is odd — incorrect odd/even rule application"},
    ],
    "TRY_04": [
        {**make_mid(M06), "wrong_answer": "13", "error_type": "concept_gap",
         "note": "Added 1 instead of 3 — applied wrong increment to skip-count rule"},
        {**make_mid(M06), "wrong_answer": "14", "error_type": "concept_gap",
         "note": "Added 2 instead of 3 — applied wrong increment"},
        {**{"error_type": "careless"}, "wrong_answer": "16",
         "note": "Added 4 instead of 3"},
    ],
    "TRY_05": [
        {**make_mid(M03), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Confused main diagonal pattern with row +1 pattern"},
        {**{"error_type": "careless"}, "wrong_choice": "C",
         "note": "Computed incorrect difference"},
        {**make_mid(M05), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Confuses additive pattern (doubles +2) with multiplicative pattern"},
    ],

    # ── R1 ────────────────────────────────────────────────────────────────────
    "R1_01": [
        {**make_mid(M08), "wrong_choice": "B", "error_type": "concept_gap",
         "note": "Identifies a true sum but cannot distinguish that from the Commutative Property"},
        {**make_mid(M01), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Selects subtraction — confused about what addition properties look like"},
        {**make_mid(M01), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Selected Identity Property example instead of Commutative"},
    ],
    "R1_02": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Believes adding 0 yields 0 — confuses Identity Property"},
        {**{"error_type": "careless"}, "wrong_choice": "C",
         "note": "Concatenated digits"},
        {**{"error_type": "careless"}, "wrong_choice": "D",
         "note": "Confused addition with multiplication"},
    ],
    "R1_03": [
        {**{"error_type": "careless"}, "wrong_choice": "A", "note": "Subtracted 1"},
        {**{"error_type": "careless"}, "wrong_choice": "C", "note": "Added 1 extra"},
        {**{"error_type": "careless"}, "wrong_choice": "D", "note": "Concatenated digits"},
    ],
    "R1_04": [
        {**make_mid(M02), "wrong_choice": "B", "error_type": "concept_gap",
         "note": "Incorrect even/odd rule: 4+6=10 is even (even+even=even)"},
    ],
    "R1_05": [
        {**make_mid(M02), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Confused parity rule for odd+even; 5+8=13 is odd"},
    ],
    "R1_06": [
        {**make_mid(M06), "wrong_answer": "17", "error_type": "concept_gap",
         "note": "Added 1 instead of 4 — wrong skip-count increment"},
        {**make_mid(M06), "wrong_answer": "18", "error_type": "concept_gap",
         "note": "Added 2 instead of 4"},
        {**{"error_type": "careless"}, "wrong_answer": "24", "note": "Doubled the rule"},
    ],
    "R1_07": [
        {**make_mid(M06), "wrong_answer": "21", "error_type": "concept_gap",
         "note": "Added 1 instead of 5"},
        {**{"error_type": "careless"}, "wrong_answer": "30", "note": "Added 10 instead of 5"},
    ],
    "R1_08": [
        {**make_mid(M03), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Chose row label (5) as the increment — classic row-pattern misconception"},
        {**{"error_type": "careless"}, "wrong_choice": "C", "note": "Incorrect difference"},
        {**{"error_type": "careless"}, "wrong_choice": "D", "note": "Numbers are increasing, not decreasing"},
    ],
    "R1_09": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Confused Identity Property with Commutative Property"},
        {**make_mid(M01), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Key feature is +0; it's Identity, not both properties"},
    ],
    "R1_10": [
        {**make_mid(M02), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "E+E=Odd is incorrect (e.g. 2+4=6, even)"},
        {**make_mid(M02), "wrong_choice": "B", "error_type": "concept_gap",
         "note": "O+O=Odd is incorrect (e.g. 3+5=8, even)"},
        {**make_mid(M02), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "E+O=Even is incorrect (e.g. 2+3=5, odd)"},
    ],

    # ── R2 ────────────────────────────────────────────────────────────────────
    "R2_01": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Identity Property involves adding 0; this question has no 0"},
        {**make_mid(M08), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Cannot identify property by name from example"},
        {**make_mid(M08), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Cannot identify property by name from example"},
    ],
    "R2_02": [
        {**make_mid(M02), "wrong_answer": "True", "error_type": "concept_gap",
         "note": "Incorrect rule: odd+odd=even not odd (counter: 3+5=8)"},
    ],
    "R2_03": [
        {**make_mid(M06), "wrong_answer": "35", "error_type": "concept_gap",
         "note": "Added 5 instead of 10 — wrong skip-count increment"},
        {**make_mid(M06), "wrong_answer": "31", "error_type": "concept_gap",
         "note": "Added 1 instead of 10"},
    ],
    "R2_04": [
        {**{"error_type": "careless"}, "wrong_choice": "A", "note": "Guessed"},
        {**{"error_type": "careless"}, "wrong_choice": "B", "note": "Guessed"},
        {**make_mid(M08), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Does not recognize constant difference as a generalizable pattern"},
    ],
    "R2_05": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "3+4=4+3 shows Commutative, not Identity"},
        {**make_mid(M08), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "5+5=10 is a true fact but does not demonstrate Identity Property"},
        {**make_mid(M01), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Subtraction is not the Identity Property of addition"},
    ],
    "R2_06": [
        {**{"error_type": "careless"}, "wrong_answer": "10", "note": "Subtracted instead of using Commutative"},
        {**{"error_type": "careless"}, "wrong_answer": "12", "note": "Added 1 extra"},
    ],
    "R2_07": [
        {**make_mid(M06), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Computed incorrect difference (should be 3-1=2, not 1)"},
        {**make_mid(M06), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Computed incorrect difference (should be 2, not 3)"},
        {**make_mid(M05), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Confuses additive pattern with multiplicative pattern"},
    ],
    "R2_08": [
        {**{"error_type": "careless"}, "wrong_choice": "A", "note": "7+8=15, not 14"},
        {**{"error_type": "careless"}, "wrong_choice": "C", "note": "9+4=13, not 14"},
        {**{"error_type": "careless"}, "wrong_choice": "D", "note": "5+8=13, not 14"},
    ],
    "R2_09": [
        {**make_mid(M07), "wrong_answer": "False", "error_type": "concept_gap",
         "note": "Does not apply Commutative Property symmetry to larger numbers"},
    ],
    "R2_10": [
        {**make_mid(M06), "wrong_answer": "28", "error_type": "concept_gap",
         "note": "Added 4 instead of 8 — wrong skip-count increment"},
        {**{"error_type": "careless"}, "wrong_answer": "30", "note": "Guessed midpoint"},
    ],

    # ── R3 ────────────────────────────────────────────────────────────────────
    "R3_01": [
        {**make_mid(M05), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Over-generalizes: thinks the whole table has only even numbers"},
        {**make_mid(M08), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Can see the pattern (numbers in order) but cannot explain WHY they are even"},
        {**make_mid(M08), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Irrelevant observation — cannot connect even/odd to the doubles structure"},
    ],
    "R3_02": [
        {**make_mid(M06), "wrong_answer": "42", "error_type": "concept_gap",
         "note": "Found 6th term (35+7=42) — miscounted position by 2"},
        {**make_mid(M06), "wrong_answer": "49", "error_type": "concept_gap",
         "note": "Found 7th term (42+7=49) — miscounted position by 1"},
        {**make_mid(M06), "wrong_answer": "63", "error_type": "concept_gap",
         "note": "Found 9th term — miscounted position by -1"},
    ],
    "R3_03": [
        {**make_mid(M02), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Applies odd+odd=even twice but forgets to add the third odd"},
        {**make_mid(M08), "wrong_choice": "C", "error_type": "concept_gap",
         "note": "Cannot generalize rule for three odds — tests individual cases only"},
        {**make_mid(M08), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Cannot see that parity rules determine the answer without calculating"},
    ],
    "R3_04": [
        {**{"error_type": "careless"}, "wrong_answer": "5",
         "note": "Subtracted 6 four times instead of three (went back one too many)"},
        {**make_mid(M06), "wrong_answer": "17", "error_type": "concept_gap",
         "note": "Went back only 2 steps — confused position index with number of steps"},
        {**make_mid(M06), "wrong_answer": "23", "error_type": "concept_gap",
         "note": "Went back only 1 step — confused position index with number of steps"},
    ],
    "R3_05": [
        {**make_mid(M01), "wrong_choice": "A", "error_type": "concept_gap",
         "note": "Sees (1) 6+0=6 as Identity but misses (4) 0+15=15 also shows Identity"},
        {**make_mid(M01), "wrong_choice": "B", "error_type": "concept_gap",
         "note": "Sees (4) 0+15=15 as Identity but misses (1) 6+0=6 also shows Identity"},
        {**make_mid(M01), "wrong_choice": "D", "error_type": "concept_gap",
         "note": "Includes (2) 3+8=8+3 which is Commutative, not Identity"},
    ],
}


def make_verification(math_note: str) -> dict:
    """verification 문자열을 7-Stage 객체로 변환."""
    return {
        "concept_source": CONCEPT_SRC,
        "procedure_source": PROCEDURE_SRC,
        "assessment_source": ASSESSMENT_SRC,
        "standard_alignment": "3.OA.D.9",
        "math_note": math_note,
        "stage_status": {
            "s1": True,
            "s2": True,
            "s3": None,
            "s4": None,
            "s5": None,
            "s6": None,
            "s7": None
        }
    }


def upgrade_item(item: dict) -> dict:
    """개별 문항(또는 LEARN 카드) 업그레이드."""
    item_id = item.get("id", "")

    # 1. verification: string → object
    v = item.get("verification", "")
    if isinstance(v, str):
        item["verification"] = make_verification(v)

    # 2. expected_errors: dict → list (misconception_id + citation)
    if "expected_errors" in item and isinstance(item["expected_errors"], dict):
        if item_id in ERRORS_MAP:
            item["expected_errors"] = ERRORS_MAP[item_id]
        else:
            # 매핑 없는 항목: 기존 dict 값을 리스트로 변환 (careless 처리)
            item["expected_errors"] = [
                {"error_type": v.get("error_type", "careless"), "note": v.get("note", "")}
                for v in item["expected_errors"].values()
                if isinstance(v, dict)
            ]

    return item


def main():
    with open(L1_PATH, encoding="utf-8") as f:
        lesson = json.load(f)

    # ── 레슨 레벨 필드 추가 ─────────────────────────────────────────────────
    lesson["tier"] = "A"
    lesson["vertical_alignment"] = {
        "prerequisite": "2.OA.B.2",
        "predecessor_description": "G2 fluently add and subtract within 20 using mental strategies",
        "successor": "4.OA.C.5",
        "successor_description": "G4 generate a number or shape pattern that follows a given rule"
    }
    lesson["unit_intro_message"] = (
        "Welcome to Unit 1! In this unit you will explore patterns in addition "
        "and subtraction with numbers up to 1,000. You will start by looking "
        "at the addition table and discovering the rules hiding inside it. "
        "Are you ready to become a pattern detective?"
    )
    lesson["unit_close_message"] = (
        "Great work finishing Unit 1! You can now spot patterns in the addition "
        "table, explain the Commutative and Identity Properties, and predict "
        "what comes next in a number sequence. Keep these skills sharp — "
        "you'll need them all the way through Grade 4 and beyond!"
    )
    lesson["review_from_units"] = []
    lesson["interleave_ratio"] = 0.0
    lesson["passing_threshold"] = 0.80
    lesson["fluency_required"] = False
    lesson["supplementary_video"] = {
        "title": "Patterns in the Addition Table (Khan Academy)",
        "url": "https://www.khanacademy.org/math/cc-third-grade-math/imp-arithmetic-patterns/imp-patterns-in-the-addition-table/v/patterns-in-the-addition-table"
    }

    # ── LEARN 카드: ccss 추가 + LEARN_07 type → explain ─────────────────────
    for card in lesson.get("learn", []):
        if "ccss" not in card:
            card["ccss"] = "3.OA.D.9"
        if card.get("id") == "LEARN_07":
            card["type"] = "explain"
            card["interaction"] = "math_talk"
            card["math_talk_prompt"] = (
                "Turn to a partner. Pick any pattern from the addition table. "
                "Describe it using these three steps: (1) What numbers are in the pattern? "
                "(2) What is the rule? (3) What comes next? Listen to your partner's explanation."
            )

    # ── 전체 문항 업그레이드 ─────────────────────────────────────────────────
    for section in ("pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"):
        lesson[section] = [upgrade_item(item) for item in lesson.get(section, [])]

    # ── 저장 ─────────────────────────────────────────────────────────────────
    with open(L1_PATH, "w", encoding="utf-8") as f:
        json.dump(lesson, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"✅ 업그레이드 완료: {L1_PATH}")
    item_count = sum(
        len(lesson.get(s, []))
        for s in ("pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3")
    )
    print(f"   처리된 문항/카드 수: {item_count}")
    print(f"   tier: {lesson['tier']}")
    print(f"   vertical_alignment: {lesson['vertical_alignment']['prerequisite']} → {lesson['vertical_alignment']['successor']}")


if __name__ == "__main__":
    main()
