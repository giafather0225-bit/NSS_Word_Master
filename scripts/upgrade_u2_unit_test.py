"""
G3 U2 unit_test 7단계 마이그레이션 (검증 메타 추가)
==============================================================================
20문항. 표준: 3.MD.B.3 (그래프 표현), 3.MD.B.4 (line plot)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U2_represent_interpret_data/unit_test.json"

LESSON_TO_ERR = {
    "L1": ["3.MD.B.3.M01"],   # tally 미스카운트
    "L2": ["3.MD.B.3.M02"],   # 그림 그래프 잘못 읽음
    "L3": ["3.MD.B.3.M02"],
    "L4": ["3.MD.B.3.M03"],   # bar graph 더하기/빼기 혼동
    "L5": ["3.MD.B.3.M06"],   # most/least 식별 오류
    "L6": ["3.MD.B.3.M07"],   # 2단계 데이터 문제
    "L7": ["3.MD.B.4.M01"],
}


def make_verification() -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.2 Unit Assessment 'Represent and Interpret Data'",
        "procedure_source": "EngageNY Grade 3 Module 6 End-of-Module Assessment — Data",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def normalize_problem(p: dict) -> dict:
    p.setdefault("cpa_stage", "abstract")
    lesson_ref = p.get("lesson_ref", "")
    if "expected_errors" not in p:
        p["expected_errors"] = LESSON_TO_ERR.get(lesson_ref, ["3.MD.B.3.M03"])
    p.setdefault("math_note", "")
    if "hint" in p and "hints" not in p:
        h = p.pop("hint")
        p["hints"] = [h] if isinstance(h, str) else list(h)
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
    assert len(ids) == len(set(ids))

    d["vertical_alignment"] = {
        "prerequisite": "G3 U1 — 1,000 이내 덧뺄셈 (3.NBT.A.2)",
        "current":      "G3 U2 — 데이터 표현/해석 단원 평가 (3.MD.B.3, 3.MD.B.4)",
        "successor":    "G3 U3 — 곱셈의 의미 (3.OA.A.1)",
    }
    d.setdefault("metadata", {})
    d["metadata"]["total_questions"] = len(problems)
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u2_unit_test.py"

    print(f"문항 수: {len(problems)}")
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
