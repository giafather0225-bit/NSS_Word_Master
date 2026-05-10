"""
G3 U6 unit_test 7단계 마이그레이션 (검증 메타 추가)
==============================================================================
20문항. 표준: 3.OA.A.2 (나눗셈 의미), 3.OA.A.3 (문장제), 3.OA.B.6 (역연산)
"""

import json, pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U6_understand_division/unit_test.json"

LESSON_TO_ERR = {
    "L1": ["3.OA.A.2.M01"],
    "L2": ["3.OA.A.2.M01"],
    "L3": ["3.OA.A.2.M01"],
    "L4": ["3.OA.A.3.M01"],
    "L5": ["3.OA.A.2.M02"],
    "L6": ["3.OA.A.2.M01"],
    "L7": ["3.OA.B.6.M01"],
    "L8": ["3.OA.B.6.M01"],
    "L9": ["3.OA.A.2.M03"],
}


def make_verification() -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.6 Unit Assessment 'Understand Division'",
        "procedure_source": "EngageNY Grade 3 Module 1 End-of-Module — Division",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_problem(p: dict) -> dict:
    p.setdefault("cpa_stage", "abstract")
    if "expected_errors" not in p:
        p["expected_errors"] = LESSON_TO_ERR.get(p.get("lesson_ref",""), ["3.OA.A.2.M01"])
    p.setdefault("math_note", "")
    if "hint" in p and "hints" not in p:
        h = p.pop("hint")
        p["hints"] = [h] if isinstance(h, str) else list(h)
    if (p.get("hints") or p.get("feedback")) and not p.get("feedback_correct"):
        p["feedback_correct"] = (p.get("feedback") or {}).get("correct") or "정답입니다! 잘 했어요."
    p["verification"] = make_verification()
    return p


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("metadata", {}).get("upgraded"):
        print("⚠️  이미 업그레이드됨."); return
    problems = [normalize_problem(p) for p in d.get("problems", [])]
    d["problems"] = problems
    assert len({p["id"] for p in problems}) == len(problems)
    d["vertical_alignment"] = {
        "prerequisite": "G3 U5 — 곱셈 활용 (3.NBT.A.3)",
        "current":      "G3 U6 — 나눗셈 의미 단원 평가 (3.OA.A.2, 3.OA.A.3, 3.OA.B.6)",
        "successor":    "G3 U7 — 나눗셈 사실 전략 (3.OA.C.7)",
    }
    d.setdefault("metadata", {})
    d["metadata"]["total_questions"] = len(problems)
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u6_unit_test.py"
    print(f"문항 수: {len(problems)}")
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
