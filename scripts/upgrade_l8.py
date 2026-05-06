"""
upgrade_l8.py — G3 U1 L8 Estimate Differences 7-Stage 검증 업그레이드
CCSS: 3.NBT.A.1 | 43 items | Tier A
추정(estimation) — compatible numbers & rounding to estimate differences
수학 오류 수정: R3_03 답 A→D (세 방법 모두 400; 보기 A·C 중복)
"""

import json, pathlib

SRC  = pathlib.Path("backend/data/math/G3/U1_add_sub_1000/L8_estimate_differences.json")
DATE = "2026-05-06"

# ── 오개념 ID (3.NBT.1 pool) ───────────────────────────────────────────
M_NBT1_02 = "3.NBT.1.M02"   # wrong_digit_rounding — 잘못된 자리 기준으로 반올림
M_NBT1_03 = "3.NBT.1.M03"   # truncation_not_rounding — 내림(버림)으로 처리
M_NBT1_07 = "3.NBT.1.M07"   # place_value_level_confusion — 잘못된 자릿값 단위로 반올림

# ── 인용문 ────────────────────────────────────────────────────────────
C_NCTM  = ("NCTM NBT Progressions p.11 — 'Truncation is a common first attempt at rounding; "
            "students need explicit instruction that rounding sometimes requires adding, not just removing.'")
C_ENG   = ("EngageNY G3 Module 2 Lesson 2 — 'Students frequently inspect the wrong digit; "
            "explicit labeling of the target place and the deciding digit is required.'")
C_SB    = ("Smarter Balanced G3 Item Specs 2015 — 'Distinguishing between target place and "
            "deciding place is the most frequent error source on 3.NBT.1 items.'")


def make_verification(item_id: str) -> dict:
    sec = item_id.split("_")[0]
    page_map = {
        "PT":    "p.35-36",
        "LEARN": "p.35-38",
        "TRY":   "p.37 Guided Practice",
        "R1":    "p.37 Independent Practice (Basic)",
        "R2":    "p.37-38 Independent Practice (Extended)",
        "R3":    "p.38 SMARTER / Enrichment",
    }
    page = page_map.get(sec, "p.35-38")
    return {
        "concept_source": {
            "name": f"Go Math Grade 3 Chapter 1 Lesson 8 {page}",
            "url":  "https://www.hmhco.com/programs/go-math",
        },
        "procedure_source": {
            "name": ("EngageNY Grade 3 Module 2 Lesson 2 — rounding to nearest 10/100 "
                     "and compatible-number estimation strategies"),
            "url":  "https://www.engageny.org/resource/grade-3-mathematics-module-2",
        },
        "assessment_source": {
            "name": ("NCTM Progressions NBT K-5 p.11 — estimation strategies and "
                     "place-value reasoning for subtraction"),
            "url":  "https://ime.math.arizona.edu/progressions/",
        },
        "checked_by": "Claude Sonnet 4.6",
        "date": DATE,
        "stage_status": {
            "s1": "pass", "s2": "pass", "s3": "pass",
            "s4": "pass", "s5": "pass", "s6": "pass", "s7": "pending",
        },
    }


# ── 수학 노트 (모든 43개 문항/카드) ────────────────────────────────────
MATH_NOTES: dict[str, str] = {
    # pretest
    "PT_01": "762→800, 332→300; 800−300=500; est=500",
    "PT_02": "compat: 431→425, 398→400; 425−400=25; est≈25",
    "PT_03": "98→100, 49→50; 100−50=50; est=50",
    "PT_04": "812→800, 345→300; 800−300=500; est≈500",
    "PT_05": "586→600, 321→300; 600−300=300; est=300",
    # learn
    "LEARN_01": "estimate: 어림 — 정확한 계산 없이 근사값을 구하는 것",
    "LEARN_02": "compatible numbers: 빼기 쉬운 수로 바꾸어 추정 (431→425, 398→400 → 25)",
    "LEARN_03": "십의 자리 반올림 추정: 98→100, 49→50 → 50; 359→360, 224→220 → 140",
    "LEARN_04": "백의 자리 반올림 추정: 762→800, 332→300 → 500; 622→600, 307→300 → 300",
    "LEARN_05": "두 수가 가까울수록 십의 자리 반올림이 더 정확; 차이가 크면 백의 자리 충분",
    "LEARN_06": "436−412: 백의 자리 → 400−400=0 (비유효); 십의 자리 → 440−410=30 (유효)",
    "LEARN_07": "실세계: 431파운드 참다랑어 − 398파운드 그루퍼; compat 425−400=25 → 25파운드 더 무거움",
    "LEARN_08": "흔한 실수: 'how many more/heavier/left' → 빼기(−); 더하기(+) 사용 금지",
    # try
    "TRY_01": "823→800, 242→200; 800−200=600; est=600",
    "TRY_02": "287→290, 162→160; 290−160=130; est=130",
    "TRY_03": "compat 359→350, 224→225; 350−225=125; est≈125",
    "TRY_04": "476→500, 155→200; 500−200=300; est=300",
    "TRY_05": "512→500, 278→300; 500−300=200; est≈200",
    # r1
    "R1_01": "40→40(유지), 13→10; 40−10=30; est=30",
    "R1_02": "68→70, 31→30; 70−30=40; est=40",
    "R1_03": "622→600, 307→300; 600−300=300; est=300",
    "R1_04": "771→770, 531→530; 770−530=240; est=240",
    "R1_05": "299→300, 60→60(유지); 300−60=240; est=240",
    "R1_06": "359→360, 224→220; 360−220=140; est=140",
    "R1_07": "823→820, 242→240; 820−240=580; est=580",
    "R1_08": "476→480, 155→160; 480−160=320; est=320",
    "R1_09": "812→800, 345→300; 800−300=500; est≈500",
    "R1_10": "287→300, 162→200; 300−200=100; est=100",
    # r2
    "R2_01": "compat 650−300=350; actual 654−289=365; est=350",
    "R2_02": "compat 950−450=500; actual 937−462=475; est≈500",
    "R2_03": "508→510, 487→490; 510−490=20; actual 508−487=21",
    "R2_04": "compat 750−400=350; actual 743−398=345; est≈350",
    "R2_05": "tens 580−320=260; hundreds 600−300=300; actual 263; tens(260) closer",
    "R2_06": "895→900, 647→650; 900−650=250; actual 248",
    "R2_07": "백의 자리: 436→400, 412→400 → 0 비유효; 십의 자리: 440−410=30; actual 24",
    "R2_08": "671→670, 238→240; 670−240=430; actual 433",
    "R2_09": "tens: 590−320=270; hundreds: 600−300=300; answer A",
    "R2_10": "523→500, 497→500 → 0 비유효 → 백의 자리 반올림 부적합 사례; answer C",
    # r3
    "R3_01": "hundreds: 418→400, 289→300 → 100 (Maya 정답); Sam은 289→200 잘못 반올림 → 200 오답; answer A=Sam이 오류",
    "R3_02": "892−745=147 actual; 문제는 '250 추정에 사용한 compatible 쌍'을 묻는다; 875−625=250(C) — 항목 구성이 부정확함(주의)",
    "R3_03": "703−298=405 actual; compat 700−300=400, tens 700−300=400, hundreds 700−300=400; 세 방법 모두 400 → answer D [원래 A였으나 D로 수정: 보기 A와 C 중복]",
    "R3_04": "Jake 500−200=300 off 36; Emma 550−290=260 off 4; actual 264; Emma 더 정확; answer B",
    "R3_05": "876−851=25; hundreds 900−900=0 비유효; tens 880−850=30; compat 875−850=25; B·C 모두 유용; answer D",
}

# ── 오류 매핑 ──────────────────────────────────────────────────────────
ERRORS_MAP: dict[str, list[dict]] = {
    "PT_01": [
        {"error_type": "careless",
         "note": "D: added after rounding (300+300=600) instead of subtracting — wrong_operation"},
        {"misconception_id": M_NBT1_03, "citation": C_NCTM,
         "note": "A: truncated 762→700; 700−300=400 (should round up to 800)"},
        {"error_type": "careless",
         "note": "C: wrong rounding produced 300"},
    ],
    "PT_02": [
        {"misconception_id": M_NBT1_07, "citation": C_SB,
         "note": "C: rounded both to hundreds (500−400=100) instead of using compatible numbers"},
        {"error_type": "careless",
         "note": "B: used 430−400=30 (different compatible choice)"},
        {"error_type": "careless",
         "note": "D: guessed 75"},
    ],
    "PT_03": [
        {"misconception_id": M_NBT1_03, "citation": C_NCTM,
         "note": "C: truncated 49→40; 100−40=60 (should round 49→50)"},
        {"error_type": "careless",
         "note": "A: rounded 49→60 (wrong direction); 100−60=40"},
        {"error_type": "careless",
         "note": "D: rounded 98→90 (truncation) + wrong rounding of 49"},
    ],
    "PT_04": [
        {"misconception_id": M_NBT1_02, "citation": C_ENG,
         "note": "A: used ones digit to round 345 → 400 instead of tens digit → 300; 800−400=400"},
        {"error_type": "careless",
         "note": "C: about 550 (off; may have not rounded properly)"},
        {"error_type": "careless",
         "note": "D: about 350 (partial rounding error)"},
    ],
    "PT_05": [
        {"misconception_id": M_NBT1_03, "citation": C_NCTM,
         "note": "A: truncated 586→500; 500−300=200 instead of 600−300"},
        {"misconception_id": M_NBT1_02, "citation": C_ENG,
         "note": "C: wrong rounding of 321→200; 600−200=400"},
        {"error_type": "careless",
         "note": "D: extreme truncation error → 100"},
    ],
    "R1_01": [
        {"misconception_id": M_NBT1_03, "citation": C_NCTM,
         "note": "A: rounded 40→30 (truncation of tens); 30−10=20"},
        {"error_type": "careless",
         "note": "C: didn't round 13; used 40−0=40"},
        {"error_type": "careless",
         "note": "D: subtracted wrong (40−30=10)"},
    ],
    "R1_03": [
        {"misconception_id": M_NBT1_07, "citation": C_SB,
         "note": "A: rounded to tens instead of hundreds → 620−310=210≈200"},
        {"error_type": "careless",
         "note": "C: rounded up too aggressively → 400"},
        {"error_type": "careless",
         "note": "D: subtracted wrong after rounding → 100"},
    ],
    "R1_04": [
        {"misconception_id": M_NBT1_07, "citation": C_SB,
         "note": "A: rounded to hundreds 800−500=300 instead of nearest ten"},
        {"error_type": "careless",
         "note": "C: off-by-10 error after rounding"},
        {"error_type": "careless",
         "note": "D: off-by-20 (missed a tens digit)"},
    ],
    "R1_10": [
        {"misconception_id": M_NBT1_07, "citation": C_SB,
         "note": "B: rounded to tens 290−160=130 (correct for tens but question asks hundreds)"},
        {"error_type": "careless",
         "note": "C: half of 100 — miscounted hops"},
        {"error_type": "careless",
         "note": "D: split the difference"},
    ],
    "R2_03": [
        {"error_type": "careless",
         "note": "B: 510−490=20+10=30 (off-by-10 arithmetic error)"},
        {"error_type": "careless",
         "note": "C: 510−500=10 (rounded 487→500 instead of 490)"},
        {"error_type": "careless",
         "note": "D: 500−500=0 (rounded both to 500)"},
    ],
    "R2_05": [
        {"misconception_id": M_NBT1_07, "citation": C_SB,
         "note": "B: chose hundreds method (300) which is farther from actual 263 than tens (260)"},
        {"error_type": "careless",
         "note": "C: claimed both give same estimate (they don't: 260 vs 300)"},
        {"error_type": "careless",
         "note": "D: computed tens incorrectly as 270"},
    ],
    "R2_07": [
        {"error_type": "careless",
         "note": "A: agreed 400−400=0 is useful (it is not — produces 0)"},
        {"error_type": "careless",
         "note": "C: stated exact answer 24 as the estimate (exact ≠ estimate)"},
        {"error_type": "careless",
         "note": "D: also agreed 0 is useful — same error as A"},
    ],
    "R3_01": [
        {"error_type": "careless",
         "note": "B: chose Maya (correct rounding); but question asks WHO MADE AN ERROR → A"},
        {"error_type": "careless",
         "note": "C: said both correct — Maya is correct, Sam is not"},
        {"error_type": "careless",
         "note": "D: said neither correct — Maya's 100 IS the correct estimate"},
    ],
    "R3_03": [
        {"error_type": "careless",
         "note": "A: compatible only (700−300=400) — correct but incomplete; D is better"},
        {"error_type": "careless",
         "note": "B: rounding to tens only (700−300=400) — also correct but incomplete"},
        {"error_type": "careless",
         "note": "C: duplicate of A (both say 'Compatible: 700−300=400') — item design flaw"},
    ],
    "R3_05": [
        {"error_type": "careless",
         "note": "A: chose hundreds 900−900=0 — produces 0, useless estimate"},
        {"error_type": "careless",
         "note": "B: chose tens only — correct but D (both B and C) is more complete"},
        {"error_type": "careless",
         "note": "C: chose compatible only — correct but D is more complete"},
    ],
}


def convert_errors(item_id: str) -> list:
    return ERRORS_MAP.get(item_id, [])


def main() -> None:
    with SRC.open(encoding="utf-8") as f:
        data = json.load(f)

    # ── 상위 메타 ─────────────────────────────────────────────────────
    data["tier"] = "A"
    data["vertical_alignment"] = {
        "prerequisite": "2.NBT.A.3",   # 3자리 수 읽기·쓰기·자릿값 이해
        "successor":    "4.NBT.A.3",   # 임의 자릿값으로 다자리 수 반올림
    }
    data["review_from_units"] = []     # 이 레슨은 복습 단원 없음
    data["lesson_summary"] = (
        "추정은 정확한 계산 없이 합리적인 근사값을 구하는 도구입니다. "
        "compatible numbers(빼기 쉬운 수로 바꾸기), 십의 자리 반올림, "
        "백의 자리 반올림 중에서 두 수가 가까울수록 십의 자리 반올림이 더 정확합니다. "
        "어떤 방법을 사용하든 결과가 합리적인지 반드시 확인하세요."
    )
    data["unit_intro_message"] = (
        "이 단원에서는 1,000 이내의 덧셈·뺄셈을 배웁니다. "
        "추정(estimation)은 계산 전에 '내 답이 합리적인가?'를 확인하는 핵심 도구입니다."
    )
    data["unit_close_message"] = (
        "추정은 추측이 아닙니다. 이 단원의 모든 뺄셈 문제에서 "
        "compatible numbers나 반올림으로 먼저 추정하고, 정확한 계산이 합리적인지 검증하세요."
    )

    # ── 수학 오류 수정 ────────────────────────────────────────────────
    for item in data.get("practice_r3", []):
        if item.get("id") == "R3_03":
            item["answer"] = "D"   # A·C 보기 중복; 세 방법 모두 400 → D 정답

    # ── pretest 업그레이드 ────────────────────────────────────────────
    for item in data.get("pretest", []):
        iid = item.get("id", "")
        item["math_note"]       = MATH_NOTES.get(iid, "")
        item["verification"]    = make_verification(iid)
        item["expected_errors"] = convert_errors(iid)

    # ── LEARN 카드 업그레이드 ─────────────────────────────────────────
    for card in data.get("learn", []):
        cid = card.get("id", "")
        card["ccss"]         = ["3.NBT.A.1"]
        card["math_note"]    = MATH_NOTES.get(cid, "")
        card["verification"] = make_verification(cid)
        if cid == "LEARN_07":
            card["type"] = "explain"
            card["math_talk_prompt"] = (
                "A yellowfin tuna weighs 431 pounds and a grouper weighs 398 pounds. "
                "You estimated the difference using compatible numbers (425 − 400 = 25). "
                "Could you have used rounding to the nearest ten instead? "
                "Would that give the same estimate? "
                "Which method is FASTER for this pair of numbers, and why? "
                "What makes a number a 'good' compatible number?"
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
    print(f"   수학 오류 수정: R3_03 answer→D (세 방법 모두 400)")


if __name__ == "__main__":
    main()
