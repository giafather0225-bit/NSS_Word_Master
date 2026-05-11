"""G3 U11 unit_test 검증 메타 정합화 (3.MD.A.1·A.2)"""
import json, pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U11_time_mass_volume/unit_test.json"

VERIFICATION = {
    "concept_source": "Go Math Grade 3 Ch.10 Unit Assessment 'Time, Length, Liquid Volume, and Mass'",
    "procedure_source": "EngageNY Grade 3 Module 2 End-of-Module Assessment — Measurement",
    "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
}

LESSON_TO_ERR = {
    "L1": ["3.MD.A.1.M01"],
    "L2": ["3.MD.A.1.M02"],
    "L3": ["3.MD.A.1.M03"],
    "L4": ["3.MD.A.2.M01"],
    "L5": ["3.MD.A.2.M02"],
    "L6": ["3.MD.A.2.M01"],
    "L7": ["3.MD.A.2.M02"],
    "L8": ["3.MD.A.2.M01"],
}


def normalize_problem(p: dict) -> dict:
    p.setdefault("cpa_stage", "abstract")
    if "expected_errors" not in p:
        p["expected_errors"] = LESSON_TO_ERR.get(p.get("lesson_ref",""), ["3.MD.A.1.M01"])
    p.setdefault("math_note", "")
    if "hint" in p and "hints" not in p:
        h = p.pop("hint")
        p["hints"] = [h] if isinstance(h, str) else list(h)
    if (p.get("hints") or p.get("feedback")) and not p.get("feedback_correct"):
        p["feedback_correct"] = (p.get("feedback") or {}).get("correct") or "정답입니다! 잘 했어요."
    orig = p.get("verification") if isinstance(p.get("verification"), str) else ""
    p["verification"] = {**VERIFICATION, "original_ref": orig}
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
        "prerequisite": "G3 U11 L1~L8 — 시간·질량·부피 (3.MD.A.1·A.2)",
        "current":      "G3 U11 unit_test — 측정 단원 평가",
        "successor":    "G3 U12 — 넓이 (3.MD.C.5·6·7)",
    }
    d.setdefault("metadata", {})
    d["metadata"]["total_questions"] = len(problems)
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u11_unit_test.py"
    print(f"문항 수: {len(problems)}")
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
