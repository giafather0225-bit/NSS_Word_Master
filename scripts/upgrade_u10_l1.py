"""
G3 U10 L1 — Model Perimeter 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.MD.D.8 (둘레 — 도형 주변의 거리)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U10_perimeter/L1_model_perimeter.json"

ID_PREFIX_MAP = {
    "c10_l1_pre_":   "PT_",
    "c10_l1_learn_": "LEARN_",
    "c10_l1_try_":   "TRY_",
    "c10_l1_pr1_":   "R1_",
    "c10_l1_pr2_":   "R2_",
    "c10_l1_pr3_":   "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.MD.D.8.M01"] for i in range(1, 6)},
    **{f"LEARN_0{i}": [] for i in range(1, 9)},
    **{f"TRY_0{i}": ["3.MD.D.8.M02"] for i in range(1, 6)},
    **{f"R1_{i:02d}": ["3.MD.D.8.M01"] for i in range(1, 11)},
    **{f"R2_0{i}": ["3.MD.D.8.M02"] for i in range(1, 8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.MD.D.8.M07"] for i in range(1, 6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "perimeter_intro" for i in range(1, 6)},
    "LEARN_01": "perimeter_definition",
    "LEARN_02": "linear_units",
    "LEARN_03": "add_all_sides",
    "LEARN_04": "grid_unit_count",
    "LEARN_05": "rectangle_pattern",
    "LEARN_06": "square_x4",
    "LEARN_07": "irregular_polygon",
    "LEARN_08": "perimeter_vs_area",
    **{f"TRY_0{i}": "perimeter_compute" for i in range(1, 6)},
    **{f"R1_{i:02d}": "perimeter_compute" for i in range(1, 11)},
    **{f"R2_0{i}": "perimeter_word_problem" for i in range(1, 8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "perimeter_irregular" for i in range(1, 6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1, 6)},
    "LEARN_01": "concrete", "LEARN_02": "abstract", "LEARN_03": "abstract",
    "LEARN_04": "pictorial", "LEARN_05": "abstract", "LEARN_06": "abstract",
    "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1, 6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R3_0{i}": "abstract" for i in range(1, 6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Lesson 10.1 'Model Perimeter' pp.413-416",
        "procedure_source": "EngageNY Grade 3 Module 7 Topic D — Perimeter of Polygons",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def remap_id(old_id: str) -> str:
    for prefix, new_prefix in ID_PREFIX_MAP.items():
        if old_id.startswith(prefix):
            num = old_id[len(prefix):]
            return f"{new_prefix}{num.zfill(2) if new_prefix == 'R1_' else num}"
    return old_id


LEARN_TITLE_MAP = {
    "LEARN_01": "둘레란 무엇인가? — 도형 주변의 거리",
    "LEARN_02": "둘레의 단위 — 길이 단위 (cm/m/in/ft)",
    "LEARN_03": "모든 변의 합 — 다각형 둘레 공식",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "둘레"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "perimeter_definition"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "perimeter_concept",
    }


TYPE_MAP = {
    "multiple_choice": "MC",
    "compare": "MC",
    "word_problem": "MC",
    "fill_in": "fill_in",
    "open_response": "open_response",
    "ordering": "ordering",
}


def normalize_item(item: dict) -> dict:
    old_id = item["id"]
    item_id = remap_id(old_id)
    item["id"] = item_id

    if item_id.startswith("LEARN_") and item.get("type") == "instruction_check":
        return normalize_existing_learn(item, item_id)
    if item_id.startswith("LEARN_") and item.get("type") == "card":
        item["type"] = "concept_card"

    if item.get("type") in TYPE_MAP:
        item["type"] = TYPE_MAP[item["type"]]
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "perimeter_compute")
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
        "id": "LEARN_04",
        "type": "concept_card",
        "title": "격자 위의 둘레 — 단위 길이 세기",
        "content": (
            "격자(grid) 종이에서 둘레: 도형의 가장자리를 따라 작은 단위 칸의 변을 센다. "
            "  ⚠️ 점(꼭짓점)이 아니라 변(선분)을 세는 것! "
            "예: 4×3 직사각형 → 4+3+4+3 = 12 단위. "
            "🖍️ 팁: 색연필로 한 변씩 색칠하며 세면 누락 방지."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "grid_unit_count",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "직사각형 둘레 — 가로+세로+가로+세로",
        "content": (
            "직사각형은 마주 보는 변이 같음 → 4변 모두 라벨이 없어도 가로 2번 + 세로 2번. "
            "  공식: P = 2×(가로 + 세로) = 가로+가로+세로+세로. "
            "예: 가로 6cm, 세로 4cm → P = 2×(6+4) = 20cm. "
            "⚠️ 자주 하는 실수(M02): 라벨된 두 변만 더해서 6+4=10이라 하기. 4변 모두 더해야 함!"
        ),
        "cpa_stage": "abstract",
        "visual_type": "rectangle_formula",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "정사각형 둘레 — 한 변 × 4",
        "content": (
            "정사각형은 4변이 모두 같음 → P = 변 × 4 = 변+변+변+변. "
            "예: 한 변 5cm → P = 5×4 = 20cm. "
            "⚠️ 자주 하는 실수(M04): 5+5 = 10 (변 2개만 더함). "
            "4변이 다 같다고 해서 2변만 세면 안 됨! 항상 ×4."
        ),
        "cpa_stage": "abstract",
        "visual_type": "square_x4",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "불규칙 다각형 — 모든 변 빠짐없이",
        "content": (
            "L자, T자 모양처럼 변이 많은 도형: 모든 변을 빠짐없이 더해야 함. "
            "  방법: 꼭짓점에 1, 2, 3, … 번호 붙이며 한 바퀴 돌기. "
            "  변의 개수 = 꼭짓점 개수. "
            "예: L자 (6변, 4+2+2+2+2+4) → P = 16. "
            "⚠️ 자주 하는 실수(M07): 안쪽 굴곡 변 빠뜨리기. 손가락으로 한 번에 외곽 따라가기."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "irregular_polygon",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "둘레 vs 넓이 — 절대 헷갈리지 말기 (M01)",
        "content": (
            "  📏 둘레(perimeter): 도형 가장자리의 거리 = 변의 합 = 더하기. 단위: cm, m, in, ft. "
            "  🟦 넓이(area): 도형이 차지하는 공간 = 가로×세로 = 곱하기. 단위: cm², sq ft. "
            "🐜 비유: 개미가 도형 가장자리를 걸어간 거리 = 둘레. 도형 안을 타일로 채운 개수 = 넓이. "
            "🔍 검산: '안쪽이냐 가장자리냐?' 가장자리 → 더하기 → 둘레."
        ),
        "cpa_stage": "abstract",
        "visual_type": "perimeter_vs_area",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "fill_in",
        "question": "A square has sides of 7 cm each. What is the perimeter?",
        "answer": "28 cm",
        "accept": ["28", "28 cm"],
        "explanation": "정사각형 4변 같음 → 7×4 = 28 cm.",
        "difficulty": 2,
        "hints": ["정사각형은 4변이 같음.", "변 × 4."],
        "feedback": {"correct": "정답! 28 cm.", "incorrect": "7+7+7+7 = 28 또는 7×4 = 28."},
    },
    {
        "id": "TRY_05",
        "type": "fill_in",
        "question": "A triangle has sides of 4 cm, 5 cm, and 6 cm. What is the perimeter?",
        "answer": "15 cm",
        "accept": ["15", "15 cm"],
        "explanation": "모든 변 더하기: 4+5+6 = 15 cm.",
        "difficulty": 1,
        "hints": ["3변 모두 더함."],
        "feedback": {"correct": "정답! 15 cm.", "incorrect": "4+5+6 = 15 cm."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "fill_in",
        "question": "A square has sides of 9 m. What is the perimeter?",
        "answer": "36 m",
        "accept": ["36", "36 m"],
        "explanation": "9 × 4 = 36 m.",
        "difficulty": 1,
        "hints": ["변 × 4."],
        "feedback": {"correct": "정답! 36 m.", "incorrect": "9×4 = 36."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "A rectangle is 8 cm long and 6 cm wide. What is the perimeter?",
        "answer": "28 cm",
        "accept": ["28", "28 cm"],
        "explanation": "8+6+8+6 = 28 또는 2×(8+6) = 28 cm.",
        "difficulty": 2,
        "hints": ["가로+세로+가로+세로."],
        "feedback": {"correct": "정답! 28 cm.", "incorrect": "2×(8+6) = 28."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "A pentagon has sides of 3, 4, 5, 6, and 7 in. What is the perimeter?",
        "choices": ["A. 21 in", "B. 25 in", "C. 26 in", "D. 30 in"],
        "answer": "B",
        "explanation": "3+4+5+6+7 = 25 in.",
        "difficulty": 2,
        "hints": ["5변 모두 더함."],
        "feedback": {"correct": "정답! 25 in.", "incorrect": "3+4+5+6+7=25."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Maya wants to put a fence around her square garden. Each side is 12 ft. How many feet of fence does she need?",
        "choices": ["A. 24 ft", "B. 36 ft", "C. 48 ft", "D. 144 ft"],
        "answer": "C",
        "explanation": "정사각형 둘레 = 12×4 = 48 ft. (144는 넓이 — 함정!)",
        "difficulty": 2,
        "hints": ["펜스 = 가장자리 거리 = 둘레.", "정사각형 변 ×4."],
        "feedback": {"correct": "정답! 48 ft 펜스.", "incorrect": "둘레 = 12×4 = 48 ft."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "A rectangular pool is 20 m long and 8 m wide. What is the perimeter?",
        "choices": ["A. 28 m", "B. 56 m", "C. 96 m", "D. 160 m"],
        "answer": "B",
        "explanation": "2×(20+8) = 2×28 = 56 m. (28은 가로+세로만 — 함정 M02)",
        "difficulty": 2,
        "hints": ["라벨 안된 변도 같음.", "4변 모두."],
        "feedback": {"correct": "정답! 56 m.", "incorrect": "2×(20+8) = 56 m."},
    },
    {
        "id": "R2_07",
        "type": "fill_in",
        "question": "A hexagon has 6 equal sides of 5 cm each. What is the perimeter?",
        "answer": "30 cm",
        "accept": ["30", "30 cm"],
        "explanation": "5×6 = 30 cm.",
        "difficulty": 2,
        "hints": ["6변이 모두 같음.", "변 × 6."],
        "feedback": {"correct": "정답! 30 cm.", "incorrect": "5×6 = 30."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "An L-shape has sides 4, 2, 2, 2, 2, 4 (six sides total). What is the perimeter?",
        "choices": ["A. 12", "B. 14", "C. 16", "D. 20"],
        "answer": "C",
        "explanation": "4+2+2+2+2+4 = 16. (12은 안쪽 굴곡 변 2개 빠뜨림 — M07 함정)",
        "difficulty": 3,
        "hints": ["6변 모두 빠짐없이.", "안쪽 굴곡 변도 포함."],
        "feedback": {"correct": "정답! 16.", "incorrect": "L자 6변 합 = 16."},
    },
    {
        "id": "R3_05",
        "type": "open_response",
        "question": "Sam says: 'A rectangle 5 cm by 4 cm has perimeter 9 cm because 5+4=9.' Explain Sam's mistake and find the correct perimeter.",
        "answer": "Sam은 마주 보는 변(가로 2번, 세로 2번)을 빼먹음. 정확한 둘레 = 5+4+5+4 = 18 cm.",
        "accept": [
            "Sam은 4변 중 2변만 더함. 정답: 5+4+5+4 = 18 cm.",
            "직사각형은 4변, 18 cm.",
            "M02 오류 — 18 cm.",
            "마주 보는 변 빼먹음, 18 cm."
        ],
        "explanation": "직사각형은 마주 보는 변이 같으므로 가로 2개 + 세로 2개 = 4변 모두 더해야 함. 5+4+5+4 = 18 cm.",
        "difficulty": 3,
        "hints": ["직사각형 변은 몇 개?", "마주 보는 변은 같음."],
        "feedback": {"correct": "정확히 분석!", "incorrect": "4변 모두 → 5+4+5+4 = 18 cm."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 348 + 275.",
        "choices": ["A. 513", "B. 523", "C. 613", "D. 623"],
        "answer": "D",
        "explanation": "348+275: 8+5=13 (carry 1), 4+7+1=12 (carry 1), 3+2+1=6. Result: 623.",
        "difficulty": 2,
        "hints": ["Two carries.", "348+275=623."],
        "feedback": {"correct": "Right — 623.", "incorrect": "348+275=623."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 706 − 248.",
        "choices": ["A. 458", "B. 462", "C. 468", "D. 542"],
        "answer": "A",
        "explanation": "706−248: borrow across zero. 706−248=458.",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "706−248=458."],
        "feedback": {"correct": "Right — 458.", "incorrect": "706−248=458."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A school had 538 students. 167 students went on a field trip, then 89 returned early. How many students remained on the trip?",
        "choices": ["A. 78", "B. 256", "C. 282", "D. 460"],
        "answer": "A",
        "explanation": "Step 1: 167−89=78 (returned subtracted). Or: trip group = 167, returned 89, still on trip = 167−89 = 78.",
        "difficulty": 3,
        "hints": ["First find trip group.", "Subtract returned: 167−89=78."],
        "feedback": {"correct": "Right — 78 still on trip.", "incorrect": "167−89=78."},
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "vertical_alignment" in d:
        print("⚠️  이미 업그레이드됨.")
        return

    sm = {
        "pretest": list(d.get("pretest", [])),
        "learn": list(d.get("learn", [])),
        "try": list(d.get("try", [])),
        "practice_r1": list(d.get("practice_r1", [])),
        "practice_r2": list(d.get("practice_r2", [])),
        "practice_r3": list(d.get("practice_r3", [])),
    }

    sm["learn"].extend(NEW_LEARN_CARDS)
    sm["try"].extend(NEW_TRY_ITEMS)
    sm["practice_r1"].extend(NEW_R1_ITEMS)
    sm["practice_r2"].extend(NEW_R2_ITEMS)
    sm["practice_r2"].extend(U1_REVIEW_R2)
    sm["practice_r3"].extend(NEW_R3_ITEMS)

    for sec_key in sm:
        sm[sec_key] = [normalize_item(it) for it in sm[sec_key]]

    counts = {k: len(v) for k, v in sm.items()}
    print("섹션별:", counts)
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    for k in sm:
        d[k] = sm[k]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U9 L7 — 동치 분수 (3.NF.A.3b)",
        "current":      "G3 U10 L1 — 둘레 모델: 도형 주변의 거리 (3.MD.D.8)",
        "successor":    "G3 U10 L2 — 둘레 구하기 — 공식과 단위 (3.MD.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u10_l1.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
