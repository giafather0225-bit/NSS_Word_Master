"""
G3 U1 unit_test 7단계 마이그레이션 (검증 메타 추가)
==============================================================================
22문항 (이미 UT_NN 형식 + lesson_ref/skill_tag/difficulty 보유).
추가: verification, expected_errors, cpa_stage, math_note, hints, feedback_correct,
vertical_alignment, metadata.upgraded.
표준: 3.OA.D.9 (산술 패턴), 3.NBT.A.1 (반올림), 3.NBT.A.2 (덧셈/뺄셈)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U1_add_sub_1000/unit_test.json"

LESSON_TO_ERR = {
    "L1":  ["3.OA.D.9.M01"],
    "L2":  ["3.NBT.1.M01"],
    "L3":  ["3.NBT.1.M02"],
    "L4":  ["3.NBT.2.M01"],
    "L5":  ["3.NBT.2.M02"],
    "L6":  ["3.NBT.2.M01"],
    "L7":  ["3.NBT.2.M01"],
    "L8":  ["3.NBT.1.M02"],
    "L9":  ["3.NBT.2.M01"],
    "L10": ["3.NBT.2.M01"],
    "L11": ["3.NBT.2.M01"],
    "L12": ["3.NBT.2.M01"],
}


def make_verification() -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.1 Unit Assessment 'Addition and Subtraction within 1,000'",
        "procedure_source": "EngageNY Grade 3 Module 2 End-of-Module Assessment — Place Value, Rounding, Add/Sub",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_problem(p: dict) -> dict:
    p.setdefault("cpa_stage", "abstract")
    lesson_ref = p.get("lesson_ref", "")
    if "expected_errors" not in p:
        p["expected_errors"] = LESSON_TO_ERR.get(lesson_ref, ["3.NBT.2.M01"])
    p.setdefault("math_note", "")
    # hint (단일) → hints (리스트)
    if "hint" in p and "hints" not in p:
        h = p.pop("hint")
        p["hints"] = [h] if isinstance(h, str) else list(h)
    # feedback_correct 보충
    if (p.get("hints") or p.get("feedback")) and not p.get("feedback_correct"):
        p["feedback_correct"] = (
            (p.get("feedback") or {}).get("correct")
            or "정답입니다! 잘 했어요."
        )
    p["verification"] = make_verification()
    return p


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("metadata", {}).get("upgraded"):
        print("⚠️  이미 업그레이드됨.")
        return

    problems = [normalize_problem(p) for p in d.get("problems", [])]
    d["problems"] = problems

    ids = [p["id"] for p in problems]
    assert len(ids) == len(set(ids)), "ID 중복"

    d["vertical_alignment"] = {
        "prerequisite": "G2 — 1,000 이내 자릿값/덧셈/뺄셈",
        "current":      "G3 U1 — 1,000 이내 덧셈/뺄셈 단원 평가 (3.OA.D.9, 3.NBT.A.1, 3.NBT.A.2)",
        "successor":    "G3 U2 — 데이터 표현/해석 (3.MD.B.3, 3.MD.B.4)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_questions"] = len(problems)
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u1_unit_test.py"

    print(f"문항 수: {len(problems)}")

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
