"""
G3 U8 L3 — Unit Fractions of a Whole 7단계 재마이그레이션
==============================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.NF.A.1 (단위분수 1/b — 전체를 b개의 같은 부분으로 나눈 것 중 한 부분)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U8_understand_fractions/L3_unit_fractions_of_a_whole.json"

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.NF.A.1.M01"] for i in range(1,6)},
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    **{f"TRY_0{i}": ["3.NF.A.1.M03"] for i in range(1,6)},
    **{f"R1_{i:02d}": ["3.NF.A.1.M02"] for i in range(1,11)},
    "R2_01": ["3.NF.A.1.M02"],
    "R2_02": ["3.NF.A.1.M03"],
    "R2_03": ["3.NF.A.1.M03"],
    "R2_04": ["3.NF.A.1.M04"],
    "R2_05": ["3.NF.A.1.M03"],
    "R2_06": ["3.NF.A.1.M01"],
    "R2_07": ["3.NF.A.1.M02"],
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.NF.A.1.M04"] for i in range(1,6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "unit_fraction" for i in range(1,6)},
    "LEARN_01": "unit_fraction_definition",
    "LEARN_02": "numerator_denominator",
    "LEARN_03": "compare_unit_fractions",
    "LEARN_04": "read_unit_fraction",
    "LEARN_05": "write_unit_fraction",
    "LEARN_06": "denominator_meaning",
    "LEARN_07": "unit_fraction_routine",
    "LEARN_08": "b_copies_make_whole",
    **{f"TRY_0{i}": "unit_fraction" for i in range(1,6)},
    **{f"R1_{i:02d}": "unit_fraction" for i in range(1,11)},
    **{f"R2_0{i}": "unit_fraction" for i in range(1,8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "unit_fraction" for i in range(1,6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "pictorial" for i in range(1,6)},
    "LEARN_01": "pictorial", "LEARN_02": "abstract", "LEARN_03": "pictorial",
    "LEARN_04": "abstract", "LEARN_05": "abstract",
    "LEARN_06": "abstract", "LEARN_07": "abstract", "LEARN_08": "pictorial",
    **{f"TRY_0{i}": "pictorial" for i in range(1,6)},
    **{f"R1_{i:02d}": "pictorial" for i in range(1,11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1,11)},
    **{f"R3_0{i}": "abstract" for i in range(1,6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.8 Lesson 8.3 'Unit Fractions of a Whole' pp.321-324",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic B — Unit Fractions and Their Relation to the Whole",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_item(item: dict) -> dict:
    item_id = item["id"]
    if item_id.startswith("LRN_"):
        item_id = f"LEARN_{item_id[4:]}"
        item["id"] = item_id
    elif item_id.startswith("LN_"):
        item_id = f"LEARN_{item_id[3:]}"
        item["id"] = item_id
    if item_id.startswith("LEARN_") and item.get("type") == "card":
        item["type"] = "concept_card"
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "unit_fraction")
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )
    item["expected_errors"] = ERRORS_MAP.get(item_id, [])
    item.setdefault("math_note", "")
    item["verification"] = make_verification(item_id)
    return item


NEW_LEARN_CARDS = [
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "분모의 의미 — '몇 등분 했나'",
        "content": (
            "단위분수 1/b에서 분모 b는 '전체를 몇 개의 같은 부분으로 나눴는지'를 알려줌. "
            "예: 1/4 → 전체를 4등분, 그 중 1조각. "
            "예: 1/8 → 전체를 8등분, 그 중 1조각. "
            "분모가 클수록 조각 수가 많아지고, 한 조각의 크기는 작아짐. "
            "🔍 빠른 확인: 분모를 읽으면 '몇 등분?'이 보임. "
            "흔한 실수 (M03): '1/4'을 '사분의 일' 대신 '일분의 사'로 읽음 — "
            "분모가 먼저 나오는 한국어 분수 읽기 순서 기억."
        ),
        "cpa_stage": "abstract",
        "visual_type": "denominator_meaning",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "단위분수 3단계 루틴",
        "content": (
            "단위분수 1/b를 정확히 만들려면 3단계: "
            "  단계 1) 전체(whole)를 정한다 — 무엇이 1인가? "
            "  단계 2) 같은 크기로 b등분한다 — 모든 부분이 똑같은 면적인지 확인. "
            "  단계 3) 그 중 한 부분을 표시 → 1/b. "
            "예: 케이크를 6등분 → 한 조각 = 1/6. "
            "흔한 실수 (M01): 부분이 다른 크기인데 '1/6'이라고 부름 — "
            "반드시 같은 크기로 나눴는지 먼저 검증."
        ),
        "cpa_stage": "abstract",
        "visual_type": "unit_fraction_routine",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "1/b를 b번 모으면 1 — 검산법",
        "content": (
            "단위분수의 핵심 성질: 1/b를 b번 모으면 전체(1)가 됨. "
            "  1/4 + 1/4 + 1/4 + 1/4 = 1 (4번) "
            "  1/6 + 1/6 + 1/6 + 1/6 + 1/6 + 1/6 = 1 (6번) "
            "🔍 검산: 한 조각을 분모만큼 복사해 전체를 덮을 수 있나? 덮이면 OK. "
            "흔한 실수 (M02): 부분 개수만 세고 같은 크기 조건은 잊음 — "
            "조각을 겹쳐 보거나 격자로 면적을 비교해 확인."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "b_copies_make_whole",
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 365 + 478.",
        "choices": ["A. 733", "B. 743", "C. 833", "D. 843"],
        "answer": "D",
        "explanation": "365+478: 5+8=13 (carry 1), 6+7+1=14 (carry 1), 3+4+1=8. Result: 843.",
        "difficulty": 2,
        "hints": ["Two carries.", "Ones: 13. Tens: 14. Hundreds: 8."],
        "feedback": {"correct": "Right — 843.", "incorrect": "365+478=843."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 702 − 369.",
        "choices": ["A. 333", "B. 343", "C. 433", "D. 443"],
        "answer": "A",
        "explanation": "702−369: 2−9 borrow → 12−9=3; tens 9−6=3 (after lending across zero); hundreds 6−3=3. Result: 333.",
        "difficulty": 2,
        "hints": ["Borrow across the zero.", "702−369=333."],
        "feedback": {"correct": "Right — 333.", "incorrect": "702−369=333."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A library had 524 books. They received 178 new books, then loaned out 246. How many books are in the library now?",
        "choices": ["A. 346", "B. 456", "C. 466", "D. 702"],
        "answer": "B",
        "explanation": "Step 1: 524+178=702. Step 2: 702−246=456.",
        "difficulty": 3,
        "hints": ["Add the new ones, then subtract the loans.", "524+178=702, 702−246=456."],
        "feedback": {"correct": "Right — 456 books.", "incorrect": "524+178=702, then −246=456."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 새 7단계 표준으로 업그레이드됨.")
        return

    nested = d.get("sections", {})
    sections_map = {
        "pretest": nested.get("pretest", d.get("pretest", [])),
        "learn": nested.get("learn", d.get("learn", [])),
        "try": nested.get("try", d.get("try", [])),
        "practice_r1": nested.get("practice_r1", d.get("practice_r1", [])),
        "practice_r2": nested.get("practice_r2", d.get("practice_r2", [])),
        "practice_r3": nested.get("practice_r3", d.get("practice_r3", [])),
    }

    learn_ids = set()
    for it in sections_map["learn"]:
        iid = it["id"]
        if iid.startswith("LRN_"):
            iid = f"LEARN_{iid[4:]}"
        elif iid.startswith("LN_"):
            iid = f"LEARN_{iid[3:]}"
        learn_ids.add(iid)
    for new_card in NEW_LEARN_CARDS:
        if new_card["id"] not in learn_ids:
            sections_map["learn"].append(new_card)

    sections_map["practice_r2"] = sections_map["practice_r2"][:7]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key in sections_map:
        sections_map[sec_key] = [normalize_item(it) for it in sections_map[sec_key]]

    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]
    if "sections" in d:
        del d["sections"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U8 L2 — 균등 공유: 음식·물체를 같은 양으로 나누기 (3.NF.A.1)",
        "current":      "G3 — 단위분수 1/b: 전체를 b등분한 것 중 한 부분 (3.NF.A.1)",
        "successor":    "G3 U8 L4 — 분수 a/b: 단위분수의 a개 모음 (3.NF.A.1)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u8_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
