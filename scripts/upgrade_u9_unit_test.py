"""
G3 U9 unit_test 7단계 마이그레이션
==============================================================================
20문항 (c9_ut_NN → UT_NN, 레거시 schema 정규화).
표준: 3.NF.A.3 (분수 비교/동치)
"""

import json, pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U9_compare_fractions/unit_test.json"

LESSON_TO_ERR = {
    "L1": ["3.NF.A.3.M01"],
    "L2": ["3.NF.A.3.M01"],
    "L3": ["3.NF.A.3.M02"],
    "L4": ["3.NF.A.3.M01"],
    "L5": ["3.NF.A.3.M01"],
    "L6": ["3.NF.A.3.M03"],
    "L7": ["3.NF.A.3.M03"],
}

TYPE_MAP = {
    "compare": "MC",
    "multiple_choice": "MC",
    "word_problem": "MC",
    "fill_in": "fill_in",
    "open_response": "open_response",
    "ordering": "ordering",
    "mc": "MC",
    "input": "fill_in",
    "tf": "MC",
}


def make_verification() -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.9 Unit Assessment 'Compare Fractions'",
        "procedure_source": "EngageNY Grade 3 Module 5 Topic G End-of-Module — Compare Fractions",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_question(q: dict, idx: int) -> dict:
    q["id"] = f"UT_{idx:02d}"
    if q.get("type") in TYPE_MAP:
        q["type"] = TYPE_MAP[q["type"]]
    q.setdefault("cpa_stage", "abstract")
    if "expected_errors" not in q:
        q["expected_errors"] = LESSON_TO_ERR.get(q.get("lesson_ref",""), ["3.NF.A.3.M01"])
    q.setdefault("skill_tag", "compare_fractions")
    q.setdefault("math_note", "")
    if "hint" in q and "hints" not in q:
        h = q.pop("hint")
        q["hints"] = [h] if isinstance(h, str) else list(h)
    if (q.get("hints") or q.get("feedback")) and not q.get("feedback_correct"):
        q["feedback_correct"] = (q.get("feedback") or {}).get("correct") or "정답입니다! 잘 했어요."
    q["verification"] = make_verification()
    return q


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("metadata", {}).get("upgraded"):
        print("⚠️  이미 업그레이드됨."); return

    questions = list(d.get("questions", []))
    questions = [normalize_question(q, i+1) for i, q in enumerate(questions)]
    d["questions"] = questions
    assert len({q["id"] for q in questions}) == len(questions)

    d["vertical_alignment"] = {
        "prerequisite": "G3 U8 — 분수의 의미 (3.NF.A.1, 3.NF.A.2)",
        "current":      "G3 U9 — 분수 비교 단원 평가 (3.NF.A.3 동치/비교)",
        "successor":    "G3 U10 — 둘레 (3.MD.D.8)",
    }
    d.setdefault("metadata", {})
    d["metadata"]["total_questions"] = len(questions)
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u9_unit_test.py"
    print(f"문항 수: {len(questions)}")
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
