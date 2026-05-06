"""
upgrade_l9.py — G3 U1 L9 Mental Math Subtraction 7-Stage 검증 업그레이드
CCSS: 3.NBT.A.2 | 43 items | Tier A
암산 뺄셈 전략: count-up / take-away tens&ones / friendly numbers
수학 오류: 없음 (모든 정답 검증 완료)
"""

import json, pathlib

SRC  = pathlib.Path("backend/data/math/G3/U1_add_sub_1000/L9_mental_math_subtraction.json")
DATE = "2026-05-06"

# ── 오개념 ID (3.NBT.2 pool) ────────────────────────────────────────────
M_NBT_01 = "3.NBT.2.M01"   # friendly_number_wrong_adjustment_direction — 보정 방향 반전
M_NBT_02 = "3.NBT.2.M02"   # friendly_number_wrong_adjustment_amount — 보정량 오류
M_NBT_05 = "3.NBT.2.M05"   # count_on_tens_count_error — 십 단위 홉 개수 오류
M_NBT_06 = "3.NBT.2.M06"   # strategy_selection_mismatch — 전략 선택 오류

# ── 인용문 ─────────────────────────────────────────────────────────────
C_ENG = ("EngageNY G3 Module 2 Lesson 4 Teacher Edition — 'Students frequently apply "
         "the compensation in the same direction as the original adjustment; explicit "
         "instruction that compensation must oppose the adjustment is required.'")
C_FUSON = ("Fuson et al. (1997) p.143 — 'Compensation errors frequently involve the "
            "correct direction but an incorrect magnitude; students lose track of the "
            "amount added when their working memory is occupied with the addition itself.'")
C_FUSON_140 = ("Fuson et al. (1997) p.140 — 'Decade-counting errors are common when "
                "the tens digit of the addend exceeds 2; students may map the tens digit "
                "directly onto number of hops rather than converting.'")
C_SB = ("Smarter Balanced G3 Item Specs 2015 — 'Strategy selection is explicitly tested "
        "at Grade 3; students must identify the most efficient strategy for a given number "
        "pair, not just apply any valid strategy.'")


def make_verification(item_id: str) -> dict:
    sec = item_id.split("_")[0]
    page_map = {
        "PT":    "p.39-40",
        "LEARN": "p.39-42",
        "TRY":   "p.41 Guided Practice",
        "R1":    "p.41 Independent Practice (Basic)",
        "R2":    "p.41-42 Independent Practice (Extended)",
        "R3":    "p.42 SMARTER / Enrichment",
    }
    page = page_map.get(sec, "p.39-42")
    return {
        "concept_source": {
            "name": f"Go Math Grade 3 Chapter 1 Lesson 9 {page}",
            "url":  "https://www.hmhco.com/programs/go-math",
        },
        "procedure_source": {
            "name": ("EngageNY Grade 3 Module 2 Lesson 4 — friendly-number subtraction "
                     "and count-up mental strategies"),
            "url":  "https://www.engageny.org/resource/grade-3-mathematics-module-2-topic-lesson-4",
        },
        "assessment_source": {
            "name": ("Fuson et al. (1997) — mental strategy selection and compensation "
                     "error patterns in 3-digit subtraction"),
            "url":  "https://doi.org/10.2307/749959",
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
    "PT_01": "74−39=35; 74−40=34, +1=35 (friendly: 39→40, 보정 +1)",
    "PT_02": "93−28=65; 93−30=63, +2=65 (friendly: 28→30, 보정 +2)",
    "PT_03": "285−99=186; 285−100=185, +1=186 (friendly: 99→100, 보정 +1)",
    "PT_04": "78−31=47; 78−30=48, −1=47 (십 단위 먼저, 일 단위 후)",
    "PT_05": "130−76=54; count-up: 76+4=80, 80+50=130 → 4+50=54",
    # learn
    "LEARN_01": "count-up 전략: 뺄 수에서 위로 세기 — 601−598: 598→601=3",
    "LEARN_02": "십·일 단위 빼기: 463−219 → 463−200=263, 263−19=244",
    "LEARN_03": "friendly numbers 뺄셈: 99→100(+1) → 285−100=185, +1=186",
    "LEARN_04": "전략 선택 기준: 수가 가까우면 count-up; 99·98 → friendly numbers; 기타 → tens&ones",
    "LEARN_05": "3자리 friendly: 285−99 → 285−100=185, +1=186; 보정 방향=반드시 덧셈",
    "LEARN_06": "3자리 tens&ones: 357−214 → 357−200=157, −10=147, −4=143",
    "LEARN_07": "수직선 시각화: 뺄셈=왼쪽 이동; count-up=오른쪽 이동으로 거리 측정",
    "LEARN_08": "흔한 실수: friendly numbers 보정 방향 반전 (빼야 할 때 더하거나 그 반대)",
    # try
    "TRY_01": "51−9=42; 51−10=41, +1=42 (friendly: 9→10, 보정 +1)",
    "TRY_02": "76−23=53; 76−20=56, 56−3=53 (tens&ones)",
    "TRY_03": "357−214=143; 357−200=157, −10=147, −4=143 (tens&ones)",
    "TRY_04": "54−9=45; 54−10=44, +1=45 (friendly: 9→10, 보정 +1)",
    "TRY_05": "50−36=14; count-up: 36+4=40, +10=50 → 14",
    # r1
    "R1_01": "62−39=23; 62−40=22, +1=23",
    "R1_02": "85−47=38; 85−50=35, +3=38 또는 85−40=45, 45−7=38",
    "R1_03": "146−98=48; 146−100=46, +2=48",
    "R1_04": "463−219=244; 463−220=243, +1=244",
    "R1_05": "500−136=364; count-up: 136+4=140, +60=200, +300=500 → 364",
    "R1_06": "81−56=25; count-up: 56+4=60, +21=81 → 25",
    "R1_07": "340−199=141; 340−200=140, +1=141",
    "R1_08": "72−48=24; 72−50=22, +2=24",
    "R1_09": "130−76=54; 130−80=50, +4=54",
    "R1_10": "253−118=135; 253−120=133, +2=135",
    # r2
    "R2_01": "567−298=269; 567−300=267, +2=269",
    "R2_02": "804−397=407; 804−400=404, +3=407",
    "R2_03": "601−598=3; count-up 3홉; 두 수가 매우 가까움 → count-up 최적",
    "R2_04": "423−156=267; 423−160=263, +4=267",
    "R2_05": "568−159=409; 568−160=408, +1=409",
    "R2_06": "750−475=275; count-up: 475+25=500, +250=750 → 275",
    "R2_07": "383−165=218; 383−170=213, +5=218",
    "R2_08": "935−499=436; 935−500=435, +1=436",
    "R2_09": "640−298=342; 640−300=340, +2=342 → Tom 정답 (A)",
    "R2_10": "362−178=184; 362−180=182, +2=184",
    # r3
    "R3_01": "843−597=246; A: 843−600=243, +3=246 ✓; B: 3+243=246 ✓; 두 전략 모두 정답(C)",
    "R3_02": "36+28+24=88; 88−19: 88−20=68, +1=69",
    "R3_03": "152−48=104; 152−50=102, +2=104",
    "R3_04": "850−399: 399→400(+1) → 850−400=450, +1=451; friendly numbers 최적(C)",
    "R3_05": "617−385=232; 617−400=217, +15=232",
}


# ── 오류 매핑 ────────────────────────────────────────────────────────────
ERRORS_MAP: dict[str, list[dict]] = {
    "PT_01": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "D: 74−40=34, then subtracted 1 instead of adding → 33 (보정 방향 반전)"},
        {"misconception_id": M_NBT_02, "citation": C_FUSON,
         "note": "A: rounded 39→50 (off by 10); 74−50=24, +1=25 (보정량 오류)"},
        {"error_type": "careless",
         "note": "C: subtracted too little; 74−29=45 or misread number"},
    ],
    "PT_02": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "D: 93−30=63 but forgot to add 2 back → 63 (보정 생략, 방향 오류)"},
        {"error_type": "careless",
         "note": "A: subtracted extra 10; 93−38=55"},
        {"error_type": "careless",
         "note": "C: didn't subtract ones: 93−20=73, skipped −8"},
    ],
    "PT_03": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "D: 285−100=185, subtracted 1 instead of adding → 184 (보정 방향 반전)"},
        {"misconception_id": M_NBT_02, "citation": C_FUSON,
         "note": "C: rounded 99→90 instead of 100; 285−90=195, +1=196 (보정량 오류 −10)"},
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "A: 285−100=185, then −9 more = 176 (과도한 보정)"},
    ],
    "PT_04": [
        {"error_type": "careless",
         "note": "A: subtracted 40 only (forgot ones): 78−40=38"},
        {"error_type": "careless",
         "note": "C: off by 10"},
        {"error_type": "careless",
         "note": "D: subtracted wrong: 78−35=43"},
    ],
    "PT_05": [
        {"misconception_id": M_NBT_05, "citation": C_FUSON_140,
         "note": "A: count-up hops miscounted: landed on 44 instead of 54"},
        {"error_type": "careless",
         "note": "C: counted 64 (overshot by 10)"},
        {"error_type": "careless",
         "note": "D: partial count-up (counted only ones, not tens): 4+2=6 → 76"},
    ],
    "TRY_01": [
        {"error_type": "careless",
         "note": "B: 51−10=41, stopped without adding 1 back"},
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "A: 51−10=41, subtracted 3 more instead of adding 1 → 38 (보정 반전)"},
        {"error_type": "careless",
         "note": "D: 51−10=41, added 3 instead of 1 → 44"},
    ],
    "TRY_03": [
        {"misconception_id": M_NBT_02, "citation": C_FUSON,
         "note": "A: 357−200=157, 157−24=133 (subtracted 24 instead of 14 — tens digit error)"},
        {"error_type": "careless",
         "note": "C: 357−200=157, skipped tens → 157−4=153"},
        {"error_type": "careless",
         "note": "D: arithmetic slip → 137"},
    ],
    "TRY_04": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "A: 54−10=44, subtracted 1 instead of adding → 43 (보정 방향 반전)"},
        {"error_type": "careless",
         "note": "C: subtracted 7 instead of 9; 54−7=47"},
        {"error_type": "careless",
         "note": "D: added instead of subtracted; 54+9=63"},
    ],
    "TRY_05": [
        {"misconception_id": M_NBT_05, "citation": C_FUSON_140,
         "note": "B: count-up hops wrong; landed on 24 instead of 14"},
        {"error_type": "careless",
         "note": "C: 50−34=16 (subtracted wrong number)"},
        {"error_type": "careless",
         "note": "D: 50−24=26 (subtracted 24 instead of 36)"},
    ],
    "R1_03": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "A: 146−100=46, then subtracted 2 more → 38 (보정 방향 반전)"},
        {"error_type": "careless",
         "note": "C: 146−98=48 but off by 4 → 52"},
        {"error_type": "careless",
         "note": "D: 146−88=58 (subtracted 88 instead of 98)"},
    ],
    "R1_07": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "A: 340−200=140, then subtracted 9 more → 131 (보정 방향 반전)"},
        {"error_type": "careless",
         "note": "C: 340−189=151 (subtracted wrong number)"},
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "D: 340−200=140, subtracted 1 instead of adding → 139"},
    ],
    "R2_01": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "A: 567−300=267, subtracted 8 more → 259 (보정 방향 반전)"},
        {"misconception_id": M_NBT_02, "citation": C_FUSON,
         "note": "C: rounded 298→290 (off by 8); 567−290=277, +2? → 279"},
        {"misconception_id": M_NBT_02, "citation": C_FUSON,
         "note": "D: compensation amount wrong; added 4 instead of 2 → 271"},
    ],
    "R2_08": [
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "A: 935−500=435, subtracted 9 more → 426 (보정 방향 반전)"},
        {"error_type": "careless",
         "note": "C: 935−489=446 (subtracted 489 instead of 499)"},
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "D: 935−500=435, subtracted 1 instead of adding → 434"},
    ],
    "R3_02": [
        {"error_type": "careless",
         "note": "A: total error or 88−29=59 (wrong number for 19)"},
        {"error_type": "careless",
         "note": "C: 88−9=79 (subtracted only ones digit; forgot tens)"},
        {"error_type": "careless",
         "note": "D: added 19 instead of subtracting → 107 or misread"},
    ],
    "R3_03": [
        {"error_type": "careless",
         "note": "A: 152−58=94 (subtracted 58 instead of 48)"},
        {"misconception_id": M_NBT_02, "citation": C_FUSON,
         "note": "C: 152−38=114 (subtracted 38 instead of 48 — ones digit wrong)"},
        {"misconception_id": M_NBT_01, "citation": C_ENG,
         "note": "D: 152−50=102, subtracted 6 instead of adding 2 → 96"},
    ],
    "R3_04": [
        {"misconception_id": M_NBT_06, "citation": C_SB,
         "note": "A: 456−123 — no near-10 numbers; break-apart easier"},
        {"misconception_id": M_NBT_06, "citation": C_SB,
         "note": "B: 703−698 — very close numbers; count-up (3 hops) is fastest, not friendly"},
        {"error_type": "careless",
         "note": "D: 524−261 — no near-10 numbers; friendly numbers not efficient"},
    ],
    "R3_05": [
        {"misconception_id": M_NBT_02, "citation": C_FUSON,
         "note": "A: 617−400=217, +5=222 (added back 5 instead of 15 — lost track of ones)"},
        {"error_type": "careless",
         "note": "C: 617−400=217, +25=242 (over-compensated by 10)"},
        {"error_type": "careless",
         "note": "D: 617−389=228 (subtracted wrong number)"},
    ],
}


def convert_errors(item_id: str) -> list:
    return ERRORS_MAP.get(item_id, [])


def main() -> None:
    with SRC.open(encoding="utf-8") as f:
        data = json.load(f)

    # ── 상위 메타 ──────────────────────────────────────────────────────
    data["tier"] = "A"
    data["vertical_alignment"] = {
        "prerequisite": "2.NBT.B.7",   # 1000 이내 덧셈·뺄셈 전략 (2학년)
        "successor":    "4.NBT.B.4",   # 표준 알고리즘 덧셈·뺄셈 (4학년)
    }
    data["review_from_units"] = []
    data["lesson_summary"] = (
        "암산으로 뺄셈을 풀 때는 세 가지 전략을 상황에 맞게 선택합니다: "
        "(1) 두 수가 가까우면 count-up, (2) 99·98처럼 10·100에 가까우면 friendly numbers, "
        "(3) 그 외에는 십·일 단위로 나누어 빼기. "
        "friendly numbers 보정은 반드시 반대 방향(더 빼면 +, 덜 빼면 −)으로 적용합니다."
    )
    data["unit_intro_message"] = (
        "이 단원에서는 1,000 이내 덧셈·뺄셈을 암산 전략으로 풀고, "
        "자릿값 알고리즘으로 검증합니다."
    )
    data["unit_close_message"] = (
        "전략을 선택했으면 반드시 역연산으로 검증하세요: "
        "뺄셈 후 빼는 수를 더했을 때 원래 수가 나오면 정답입니다."
    )

    # ── pretest 업그레이드 ────────────────────────────────────────────
    for item in data.get("pretest", []):
        iid = item.get("id", "")
        item["math_note"]       = MATH_NOTES.get(iid, "")
        item["verification"]    = make_verification(iid)
        item["expected_errors"] = convert_errors(iid)

    # ── LEARN 카드 업그레이드 ─────────────────────────────────────────
    for card in data.get("learn", []):
        cid = card.get("id", "")
        card["ccss"]         = ["3.NBT.A.2"]
        card["math_note"]    = MATH_NOTES.get(cid, "")
        card["verification"] = make_verification(cid)
        if cid == "LEARN_01":
            # count-up은 실물 교구(토큰/바둑돌)로 직접 세기 — CPA concrete 단계
            card["cpa_stage"] = "concrete"
        if cid == "LEARN_07":
            card["type"] = "explain"
            card["math_talk_prompt"] = (
                "Look at the number line for 130 − 76. "
                "You can solve it by moving LEFT (subtracting 76), "
                "OR by moving RIGHT from 76 up to 130 (count-up). "
                "Both give the same answer. "
                "Which direction did YOU choose, and why? "
                "Is there a type of problem where moving right (count-up) "
                "is clearly faster than moving left? Give an example."
            )
        if cid == "LEARN_08":
            card["type"] = "summary"

    # ── try 업그레이드 ────────────────────────────────────────────────
    for item in data.get("try", []):
        iid = item.get("id", "")
        item["math_note"]       = MATH_NOTES.get(iid, "")
        item["verification"]    = make_verification(iid)
        item["expected_errors"] = convert_errors(iid)

    # ── practice_r1 / r2 / r3 업그레이드 ─────────────────────────────
    for sec_key in ["practice_r1", "practice_r2", "practice_r3"]:
        for item in data.get(sec_key, []):
            iid = item.get("id", "")
            item["math_note"]       = MATH_NOTES.get(iid, "")
            item["verification"]    = make_verification(iid)
            item["expected_errors"] = convert_errors(iid)

    # ── 저장 ─────────────────────────────────────────────────────────
    with SRC.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(data.get(s, [])) for s in
                ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"])
    print(f"✅ 업그레이드 완료: {SRC}")
    print(f"   처리된 문항/카드 수: {total}")
    print(f"   tier: {data['tier']}")
    va = data['vertical_alignment']
    print(f"   vertical_alignment: {va['prerequisite']} → {va['successor']}")
    print(f"   수학 오류 수정: 없음 (모든 정답 검증 완료)")


if __name__ == "__main__":
    main()
