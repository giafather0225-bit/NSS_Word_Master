"""
G3 U10 unit_test 7단계 재마이그레이션
==============================================================================
20개 → 30개 (모든 6개 레슨 통합 평가, U1 복습 3문항 포함)
표준: 3.MD.D.8 (둘레 단원 종합)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U10_perimeter/unit_test.json"


TYPE_MAP = {
    "multiple_choice": "MC",
    "compare": "MC",
    "word_problem": "MC",
    "fill_in": "fill_in",
    "open_response": "open_response",
    "ordering": "ordering",
}


def make_verification() -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.10 Unit Assessment 'Perimeter' pp.437-440",
        "procedure_source": "EngageNY Grade 3 Module 7 End-of-Module Assessment — Perimeter",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


LESSON_TO_ERR = {
    "L1": ["3.MD.D.8.M05"],
    "L2": ["3.MD.D.8.M02"],
    "L3": ["3.MD.D.8.M06"],
    "L4": ["3.MD.D.8.M01"],
    "L5": ["3.MD.D.8.M01"],
    "L6": ["3.MD.D.8.M01"],
}


def normalize_question(item: dict, idx: int) -> dict:
    item["id"] = f"UT_{idx:02d}"
    if item.get("type") in TYPE_MAP:
        item["type"] = TYPE_MAP[item["type"]]
    if "stem" in item and "question" not in item:
        item["question"] = item.pop("stem")
    item.setdefault("cpa_stage", "abstract")
    lesson_ref = item.get("lesson_ref", "")
    if "expected_errors" not in item:
        item["expected_errors"] = LESSON_TO_ERR.get(lesson_ref, ["3.MD.D.8.M01"])
    item.setdefault("skill_tag", "perimeter_unit_test")
    item.setdefault("math_note", "")
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )
    item["verification"] = make_verification()
    return item


NEW_QUESTIONS = [
    {
        "type": "MC",
        "lesson_ref": "L1",
        "question": "Which is the correct unit for perimeter?",
        "choices": ["A. cm² (제곱 단위)", "B. cm (길이 단위)", "C. cubic cm", "D. degrees"],
        "answer": "B",
        "explanation": "둘레는 거리(길이) → 길이 단위 cm. cm²는 넓이.",
        "difficulty": 1,
        "hints": ["둘레 = 거리.", "1차원 단위."],
        "feedback": {"correct": "정답! cm.", "incorrect": "둘레 단위는 cm."},
        "expected_errors": ["3.MD.D.8.M03"],
        "skill_tag": "units_distinction",
    },
    {
        "type": "MC",
        "lesson_ref": "L1",
        "question": "An L-shape has 6 sides: 4, 2, 2, 2, 2, 4 cm. What is the perimeter?",
        "choices": ["A. 12 cm", "B. 14 cm", "C. 16 cm", "D. 20 cm"],
        "answer": "C",
        "explanation": "4+2+2+2+2+4 = 16. 6변 모두 (안쪽 굴곡 변 누락 주의 — M07).",
        "difficulty": 2,
        "hints": ["6변 모두.", "안쪽 변 빼먹지 않기."],
        "feedback": {"correct": "정답! 16 cm.", "incorrect": "6변 합 16 cm."},
        "expected_errors": ["3.MD.D.8.M07"],
        "skill_tag": "irregular_polygon",
    },
    {
        "type": "fill_in",
        "lesson_ref": "L2",
        "question": "A regular pentagon has 5 equal sides of 8 m. What is the perimeter?",
        "answer": "40 m",
        "accept": ["40", "40 m"],
        "explanation": "8 × 5 = 40 m.",
        "difficulty": 1,
        "hints": ["5변 모두 같음.", "변×5."],
        "feedback": {"correct": "정답! 40 m.", "incorrect": "8×5 = 40."},
        "expected_errors": ["3.MD.D.8.M02"],
        "skill_tag": "regular_polygon",
    },
    {
        "type": "MC",
        "lesson_ref": "L4",
        "question": "Maria computes a 6×4 rectangle: P=24 and A=20. Where did she go wrong?",
        "choices": [
            "A. P 정답, A 오답: 6×4=24가 P, 24가 A",
            "B. P 정답(20), A 오답: P=2×(6+4)=20, A=24",
            "C. P 오답(24)이 A이고, P=20",
            "D. 모두 정답"
        ],
        "answer": "C",
        "explanation": "맞는 값: P = 2×(6+4) = 20, A = 6×4 = 24. Maria가 둘을 바꿈 (M01).",
        "difficulty": 3,
        "hints": ["P = 더하기, A = 곱하기.", "값 다시 계산."],
        "feedback": {"correct": "정답!", "incorrect": "P=20, A=24 — 그녀는 바꿔 씀."},
        "expected_errors": ["3.MD.D.8.M01"],
        "skill_tag": "perimeter_vs_area",
    },
    {
        "type": "MC",
        "lesson_ref": "L5",
        "question": "A rectangular pen has perimeter 18 ft. Which dimensions give the LEAST area?",
        "choices": ["A. 8×1 (8 sq ft)", "B. 7×2 (14)", "C. 6×3 (18)", "D. 5×4 (20)"],
        "answer": "A",
        "explanation": "P=18 → l+w=9. 가장 길쭉한 8×1이 최소 넓이 8 sq ft.",
        "difficulty": 2,
        "hints": ["가장 길쭉 = 최소 A."],
        "feedback": {"correct": "정답! 8×1.", "incorrect": "8×1=8 최소."},
        "expected_errors": ["3.MD.D.8.M01"],
        "skill_tag": "same_P_diff_A",
    },
    {
        "type": "MC",
        "lesson_ref": "L6",
        "question": "A 24 sq cm rug. Which dimensions need the LEAST trim around the edge?",
        "choices": ["A. 24×1 (P=50)", "B. 12×2 (P=28)", "C. 8×3 (P=22)", "D. 6×4 (P=20)"],
        "answer": "D",
        "explanation": "6×4가 정사각에 가장 가까움 → P=20 cm 최소.",
        "difficulty": 2,
        "hints": ["정사각에 가까울수록 P 작음."],
        "feedback": {"correct": "정답! 6×4.", "incorrect": "6×4 P=20 최소."},
        "expected_errors": ["3.MD.D.8.M01"],
        "skill_tag": "same_A_diff_P",
    },
    {
        "type": "open_response",
        "lesson_ref": "L5_L6",
        "question": "Lily has 16 ft of fence AND wants 16 sq ft of garden. She thinks she can choose ONE rectangle that satisfies BOTH. Find such a rectangle if possible.",
        "answer": "4×4 정사각형 (P=16, A=16). 정사각형은 P와 A가 같은 단위 수치 가능 (변=4일 때).",
        "accept": [
            "4×4 정사각형",
            "4 by 4",
            "4×4 P=16 A=16",
            "정사각형 4×4"
        ],
        "explanation": "P=16 직사각형 중 5×3(A=15), 4×4(A=16), 6×2(A=12). 정사각형 4×4가 둘 다 만족 (P=16=A).",
        "difficulty": 3,
        "hints": ["정사각형 시도.", "변 = 4."],
        "feedback": {"correct": "정확! 4×4.", "incorrect": "정사각 4×4 P=16, A=16."},
        "expected_errors": ["3.MD.D.8.M01"],
        "skill_tag": "perimeter_area_combined",
    },
    # U1 복습 3문항 (마지막)
    {
        "type": "MC",
        "lesson_ref": "U1_review",
        "question": "Find the sum: 482 + 367.",
        "choices": ["A. 749", "B. 759", "C. 849", "D. 859"],
        "answer": "C",
        "explanation": "482+367: 2+7=9, 8+6=14 (carry 1), 4+3+1=8. Result: 849.",
        "difficulty": 2,
        "hints": ["One carry.", "482+367=849."],
        "feedback": {"correct": "Right — 849.", "incorrect": "482+367=849."},
        "expected_errors": ["3.NBT.2.M01"],
        "skill_tag": "addition_3digit",
        "review_from": "U1",
    },
    {
        "type": "MC",
        "lesson_ref": "U1_review",
        "question": "Find the difference: 802 − 358.",
        "choices": ["A. 444", "B. 454", "C. 544", "D. 554"],
        "answer": "A",
        "explanation": "802−358: borrow across zero. 802−358=444.",
        "difficulty": 2,
        "hints": ["Borrow across zero.", "802−358=444."],
        "feedback": {"correct": "Right — 444.", "incorrect": "802−358=444."},
        "expected_errors": ["3.NBT.2.M01"],
        "skill_tag": "subtraction_3digit",
        "review_from": "U1",
    },
    {
        "type": "MC",
        "lesson_ref": "U1_review",
        "question": "A school had 567 students. 138 transferred out, then 245 new students joined. How many students now?",
        "choices": ["A. 184", "B. 429", "C. 674", "D. 950"],
        "answer": "C",
        "explanation": "Step 1: 567−138=429. Step 2: 429+245=674.",
        "difficulty": 3,
        "hints": ["Subtract then add.", "567−138=429, +245=674."],
        "feedback": {"correct": "Right — 674.", "incorrect": "567−138=429, +245=674."},
        "expected_errors": ["3.NBT.2.M01"],
        "skill_tag": "two_step_add_sub",
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("metadata", {}).get("upgraded"):
        print("⚠️  이미 업그레이드됨.")
        return

    questions = list(d.get("questions", []))
    questions.extend(NEW_QUESTIONS)
    questions = [normalize_question(q, i + 1) for i, q in enumerate(questions)]

    # ID uniqueness
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "ID 중복"

    d["questions"] = questions

    d["vertical_alignment"] = {
        "prerequisite": "G3 U10 L1~L6 — 둘레 6개 레슨 (3.MD.D.8)",
        "current":      "G3 U10 unit_test — 둘레 단원 평가 (3.MD.D.8 종합)",
        "successor":    "G3 U11 — 다음 단원 (3.G.A.1 도형 분류)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_questions"] = len(questions)
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u10_unit_test.py"
    d["metadata"]["review_from_units"] = ["U1"]

    print(f"총 {len(questions)} 문항 (이전 20 + 추가 {len(NEW_QUESTIONS)}).")

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
