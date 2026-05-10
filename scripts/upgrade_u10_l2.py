"""
G3 U10 L2 — Find Perimeter 7단계 재마이그레이션
==============================================================================
25개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.MD.D.8 (둘레 구하기 — 자/공식 활용)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U10_perimeter/L2_find_perimeter.json"

ID_PREFIX_MAP = {
    "c10_l2_pre_":   "PT_",
    "c10_l2_learn_": "LEARN_",
    "c10_l2_try_":   "TRY_",
    "c10_l2_pr1_":   "R1_",
    "c10_l2_pr2_":   "R2_",
    "c10_l2_pr3_":   "R3_",
}

ERRORS_MAP = {
    **{f"PT_0{i}": ["3.MD.D.8.M02"] for i in range(1, 6)},
    **{f"LEARN_0{i}": [] for i in range(1, 9)},
    **{f"TRY_0{i}": ["3.MD.D.8.M04"] for i in range(1, 6)},
    **{f"R1_{i:02d}": ["3.MD.D.8.M02"] for i in range(1, 11)},
    **{f"R2_0{i}": ["3.MD.D.8.M03"] for i in range(1, 8)},
    "R2_08": ["3.NBT.2.M01"],
    "R2_09": ["3.NBT.2.M01"],
    "R2_10": ["3.NBT.2.M01"],
    **{f"R3_0{i}": ["3.MD.D.8.M07"] for i in range(1, 6)},
}

SKILL_TAGS = {
    **{f"PT_0{i}": "perimeter_compute" for i in range(1, 6)},
    "LEARN_01": "rectangle_formula",
    "LEARN_02": "square_formula",
    "LEARN_03": "ruler_measure",
    "LEARN_04": "formula_2lw",
    "LEARN_05": "two_methods_check",
    "LEARN_06": "real_world_units",
    "LEARN_07": "irregular_polygon_sum",
    "LEARN_08": "estimate_check",
    **{f"TRY_0{i}": "perimeter_compute" for i in range(1, 6)},
    **{f"R1_{i:02d}": "perimeter_compute" for i in range(1, 11)},
    **{f"R2_0{i}": "perimeter_word_problem" for i in range(1, 8)},
    "R2_08": "addition_3digit",
    "R2_09": "subtraction_3digit",
    "R2_10": "two_step_add_sub",
    **{f"R3_0{i}": "perimeter_complex" for i in range(1, 6)},
}

CPA_MAP = {
    **{f"PT_0{i}": "abstract" for i in range(1, 6)},
    "LEARN_01": "abstract", "LEARN_02": "abstract", "LEARN_03": "concrete",
    "LEARN_04": "abstract", "LEARN_05": "abstract", "LEARN_06": "abstract",
    "LEARN_07": "pictorial", "LEARN_08": "abstract",
    **{f"TRY_0{i}": "abstract" for i in range(1, 6)},
    **{f"R1_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R2_{i:02d}": "abstract" for i in range(1, 11)},
    **{f"R3_0{i}": "abstract" for i in range(1, 6)},
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Lesson 10.2 'Find Perimeter' pp.417-420",
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
    "LEARN_01": "직사각형 둘레 — P = (가로+세로) × 2",
    "LEARN_02": "정사각형 둘레 — P = 변 × 4",
    "LEARN_03": "자로 측정 — 모든 변 같은 단위",
}


def normalize_existing_learn(item: dict, new_id: str) -> dict:
    instr = item.get("instruction", "")
    q = item.get("question", "")
    ans = item.get("answer", "")
    expl = item.get("explanation", "")
    return {
        "id": new_id,
        "type": "concept_card",
        "title": LEARN_TITLE_MAP.get(new_id, "둘레 구하기"),
        "content": f"{instr} 예: {q} → {ans}. ({expl})",
        "cpa_stage": CPA_MAP.get(new_id, "abstract"),
        "skill_tag": SKILL_TAGS.get(new_id, "perimeter_compute"),
        "expected_errors": [],
        "math_note": "",
        "verification": make_verification(new_id),
        "visual_type": "perimeter_formula",
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
        "title": "공식 P = 2(l+w) — 직사각형 빠른 계산",
        "content": (
            "직사각형 둘레 공식 두 가지 (같은 결과): "
            "  ① P = l + w + l + w (네 변 차례로 더하기) "
            "  ② P = 2 × (l + w) (가로+세로 합 × 2) "
            "예: l=7, w=3 → ② 2×(7+3) = 2×10 = 20. "
            "🔍 ②번이 큰 수에서 더 빠름."
        ),
        "cpa_stage": "abstract",
        "visual_type": "rectangle_formula",
    },
    {
        "id": "LEARN_05",
        "type": "concept_card",
        "title": "두 방법으로 검산 — 같은 답 나와야",
        "content": (
            "공식 ①과 ② 결과가 같은지 확인. "
            "예: l=8, w=5 → ① 8+5+8+5 = 26 → ② 2×(8+5) = 26 ✓ "
            "🔍 검산 습관: 답이 다르면 어딘가 계산 오류. "
            "정사각형도 마찬가지: 변+변+변+변 = 변×4."
        ),
        "cpa_stage": "abstract",
        "visual_type": "two_methods_check",
    },
    {
        "id": "LEARN_06",
        "type": "concept_card",
        "title": "실생활 단위 — cm/m/in/ft 통일",
        "content": (
            "실제 물건 둘레 측정: 모든 변을 같은 단위로 측정 후 합. "
            "  ⚠️ cm와 m, in과 ft 섞으면 안 됨. "
            "예: 책상 가로 80 cm, 세로 60 cm → P = 2×(80+60) = 280 cm = 2.8 m. "
            "🔍 실수 방지: 단위 통일 후 계산."
        ),
        "cpa_stage": "abstract",
        "visual_type": "real_world_units",
    },
    {
        "id": "LEARN_07",
        "type": "concept_card",
        "title": "불규칙 다각형 — 한 바퀴 + 단위",
        "content": (
            "오각형, 육각형, L자 등 변이 많은 도형: 한 꼭짓점부터 시계방향으로 한 바퀴 돌며 더함. "
            "예: 오각형 변 3, 4, 5, 6, 7 in → P = 3+4+5+6+7 = 25 in. "
            "🖍️ 팁: 변마다 ✓ 표시 — 누락 방지(M07). "
            "  단위는 길이 단위 (cm/in 등) — 절대 cm² ❌."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "irregular_polygon_sum",
    },
    {
        "id": "LEARN_08",
        "type": "concept_card",
        "title": "추정으로 검산 — 합리적인 답인가?",
        "content": (
            "계산 후 '말이 되나?' 검산. "
            "예: 가로 10, 세로 5 직사각형 → P가 100? ❌ 너무 큼 (그건 넓이!). "
            "  추정: 모든 변 ≈ 10이면 P ≈ 4×10 = 40. 실제 30. 가까움. ✓ "
            "🔍 100이 나오면 곱했을 가능성 (M01: 둘레↔넓이 혼동)."
        ),
        "cpa_stage": "abstract",
        "visual_type": "estimate_check",
    },
]


NEW_TRY_ITEMS = [
    {
        "id": "TRY_04",
        "type": "fill_in",
        "question": "A rectangle has l = 12 cm, w = 8 cm. Use P = 2×(l+w). What is the perimeter?",
        "answer": "40 cm",
        "accept": ["40", "40 cm"],
        "explanation": "2×(12+8) = 2×20 = 40 cm.",
        "difficulty": 2,
        "hints": ["가로+세로 먼저, 그리고 ×2."],
        "feedback": {"correct": "정답! 40 cm.", "incorrect": "2×(12+8) = 40."},
    },
    {
        "id": "TRY_05",
        "type": "MC",
        "question": "A square has perimeter that you measure as side+side+side+side. Which formula is the SAME?",
        "choices": ["A. side × 2", "B. side × 3", "C. side × 4", "D. side + 4"],
        "answer": "C",
        "explanation": "정사각형 4변 같음 → ×4.",
        "difficulty": 1,
        "hints": ["정사각형 변 개수?"],
        "feedback": {"correct": "정답! ×4.", "incorrect": "정사각형 4변 → ×4."},
    },
]


NEW_R1_ITEMS = [
    {
        "id": "R1_08",
        "type": "fill_in",
        "question": "A rectangle is 15 m long and 10 m wide. P = __ m.",
        "answer": "50 m",
        "accept": ["50", "50 m"],
        "explanation": "2×(15+10) = 50 m.",
        "difficulty": 2,
        "hints": ["2×(l+w)."],
        "feedback": {"correct": "정답! 50 m.", "incorrect": "2×(15+10) = 50."},
    },
    {
        "id": "R1_09",
        "type": "fill_in",
        "question": "A square has side 11 in. P = __ in.",
        "answer": "44 in",
        "accept": ["44", "44 in"],
        "explanation": "11×4 = 44 in.",
        "difficulty": 1,
        "hints": ["변×4."],
        "feedback": {"correct": "정답! 44 in.", "incorrect": "11×4 = 44."},
    },
    {
        "id": "R1_10",
        "type": "MC",
        "question": "A pentagon has sides 4, 6, 8, 5, 7 cm. What is the perimeter?",
        "choices": ["A. 26 cm", "B. 28 cm", "C. 30 cm", "D. 32 cm"],
        "answer": "C",
        "explanation": "4+6+8+5+7 = 30 cm.",
        "difficulty": 2,
        "hints": ["5변 모두."],
        "feedback": {"correct": "정답! 30 cm.", "incorrect": "4+6+8+5+7=30."},
    },
]


NEW_R2_ITEMS = [
    {
        "id": "R2_05",
        "type": "MC",
        "question": "Tom's rectangular yard is 25 ft long and 15 ft wide. He wants to put a fence around it. How many feet of fence does he need?",
        "choices": ["A. 40 ft", "B. 75 ft", "C. 80 ft", "D. 375 ft"],
        "answer": "C",
        "explanation": "2×(25+15) = 80 ft. (375는 넓이 — 함정 M01)",
        "difficulty": 2,
        "hints": ["펜스 = 둘레.", "2×(l+w)."],
        "feedback": {"correct": "정답! 80 ft.", "incorrect": "2×(25+15) = 80 ft."},
    },
    {
        "id": "R2_06",
        "type": "MC",
        "question": "Lisa is putting trim around a square photo frame. Each side is 8 in. How many inches of trim does she need?",
        "choices": ["A. 16 in", "B. 24 in", "C. 32 in", "D. 64 in"],
        "answer": "C",
        "explanation": "8×4 = 32 in. (64는 넓이 — M01 함정)",
        "difficulty": 2,
        "hints": ["정사각형 변×4."],
        "feedback": {"correct": "정답! 32 in.", "incorrect": "8×4 = 32 in."},
    },
    {
        "id": "R2_07",
        "type": "fill_in",
        "question": "A triangular garden has sides 12 ft, 9 ft, and 15 ft. What is the perimeter?",
        "answer": "36 ft",
        "accept": ["36", "36 ft"],
        "explanation": "12+9+15 = 36 ft.",
        "difficulty": 2,
        "hints": ["3변 모두 더함."],
        "feedback": {"correct": "정답! 36 ft.", "incorrect": "12+9+15=36."},
    },
]


NEW_R3_ITEMS = [
    {
        "id": "R3_04",
        "type": "MC",
        "question": "A rectangular pool has length 20 m and width 12 m. Maria says perimeter = 240 m. What was her mistake?",
        "choices": [
            "A. 그녀는 둘레 대신 넓이를 계산함 (M01)",
            "B. 그녀는 한 변을 빼먹음",
            "C. 그녀는 단위를 잘못 씀",
            "D. 정답이 맞음"
        ],
        "answer": "A",
        "explanation": "20×12 = 240 → 넓이. 둘레는 2×(20+12) = 64 m. 흔한 M01 함정.",
        "difficulty": 3,
        "hints": ["240은 어떻게 나옴?", "곱하면 넓이."],
        "feedback": {"correct": "정확! 넓이를 계산함.", "incorrect": "20×12=240은 넓이. 둘레는 64 m."},
    },
    {
        "id": "R3_05",
        "type": "open_response",
        "question": "A regular hexagon has each side measuring 7 cm. Find the perimeter using TWO different methods and show both calculations.",
        "answer": "방법1: 7+7+7+7+7+7 = 42 cm. 방법2: 7×6 = 42 cm.",
        "accept": [
            "7+7+7+7+7+7=42, 7×6=42, 42 cm",
            "더하기 방법 42 cm, 곱하기 방법 42 cm",
            "방법1 7+7+7+7+7+7=42 cm 방법2 7×6=42 cm",
            "42 cm (두 방법 동일)"
        ],
        "explanation": "정육각형 6변이 모두 같음 → 더하기와 곱하기 결과 동일. 42 cm.",
        "difficulty": 3,
        "hints": ["6변이 모두 같으면?", "더하기 또는 곱하기."],
        "feedback": {"correct": "정확! 두 방법 모두 42 cm.", "incorrect": "7+7+7+7+7+7 = 42 또는 7×6 = 42."},
    },
]


U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "type": "MC",
        "question": "Find the sum: 567 + 289.",
        "choices": ["A. 746", "B. 756", "C. 846", "D. 856"],
        "answer": "D",
        "explanation": "567+289: 7+9=16 (carry 1), 6+8+1=15 (carry 1), 5+2+1=8. Result: 856.",
        "difficulty": 2,
        "hints": ["Two carries.", "567+289=856."],
        "feedback": {"correct": "Right — 856.", "incorrect": "567+289=856."},
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "type": "MC",
        "question": "Find the difference: 905 − 376.",
        "choices": ["A. 529", "B. 539", "C. 629", "D. 631"],
        "answer": "A",
        "explanation": "905−376: borrow across zero. 905−376=529.",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "905−376=529."],
        "feedback": {"correct": "Right — 529.", "incorrect": "905−376=529."},
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "type": "MC",
        "question": "A bookstore had 425 books. They received 198 more, then sold 327. How many books remain?",
        "choices": ["A. 96", "B. 254", "C. 296", "D. 623"],
        "answer": "C",
        "explanation": "Step 1: 425+198=623. Step 2: 623−327=296.",
        "difficulty": 3,
        "hints": ["Add then subtract.", "425+198=623, 623−327=296."],
        "feedback": {"correct": "Right — 296.", "incorrect": "425+198=623, then −327=296."},
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
        "prerequisite": "G3 U10 L1 — 둘레 모델: 도형 주변의 거리 (3.MD.D.8)",
        "current":      "G3 U10 L2 — 둘레 구하기: 공식과 자 측정 (3.MD.D.8)",
        "successor":    "G3 U10 L3 — 미지의 변 길이 구하기 (3.MD.D.8)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = sum(counts.values())
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u10_l2.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
