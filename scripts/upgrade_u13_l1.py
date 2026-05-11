"""G3 U13 L1 — Describe Polygons 검증 메타 정합화 (3.G.A.1)"""
import json, pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U13_shapes/L1_describe_polygons.json"

VERIFICATION = {
    "concept_source": "Go Math Grade 3 Ch.12 Lesson 12.1 'Describe Plane Shapes'",
    "procedure_source": "EngageNY Grade 3 Module 7 Topic E — Polygon Properties",
    "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
}
VERT_ALIGN = {
    "prerequisite": "G3 U12 — 넓이 (3.MD.C.5·6·7)",
    "current":      "G3 U13 L1 — 다각형 설명 (3.G.A.1)",
    "successor":    "G3 U13 L2 — 다각형 분류 (3.G.A.1)",
}


def normalize_item(item: dict) -> dict:
    if "cpa_phase" in item and "cpa_stage" not in item:
        item["cpa_stage"] = item["cpa_phase"]
    item.setdefault("math_note", "")
    if (item.get("hints") or item.get("feedback")) and not item.get("feedback_correct"):
        item["feedback_correct"] = (item.get("feedback") or {}).get("correct") or "정답입니다! 잘 했어요."
    orig = item.get("verification") if isinstance(item.get("verification"), str) else ""
    item["verification"] = {**VERIFICATION, "original_ref": orig}
    return item


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("metadata", {}).get("upgraded"):
        print("⚠️  이미 업그레이드됨."); return
    sections = ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"]
    counts = {}
    for k in sections:
        d[k] = [normalize_item(it) for it in d.get(k, [])]; counts[k] = len(d[k])
    expected = {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}
    print("섹션별:", counts); assert counts == expected
    all_ids = [it["id"] for k in sections for it in d[k]]; assert len(all_ids) == len(set(all_ids))
    d["vertical_alignment"] = VERT_ALIGN
    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u13_l1.py"
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
