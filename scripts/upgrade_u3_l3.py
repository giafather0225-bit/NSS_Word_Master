"""
G3 U3 L3 — Skip Count on a Number Line 7단계 업그레이드 스크립트
================================================================
40개 → 43개 (PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
표준: 3.OA.A.3 (수직선 건너뛰며 세기로 곱셈 모델링)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "backend/data/math/G3/U3_understand_multiplication/L3_skip_count_on_number_line.json"

ERRORS_MAP = {
    "PT_01": ["3.OA.A.3.M03"],                          # +3 패턴 마지막 점
    "PT_02": ["3.OA.A.3.M03"],                          # 4 jumps of 5
    "PT_03": ["3.OA.A.3.M04"],                          # 5×4 점프 횟수
    "PT_04": ["3.OA.A.3.M01", "3.OA.A.3.M03"],          # 4 boards × 3 ft
    "PT_05": ["3.OA.A.3.M03"],                          # 3 jumps of 6
    "LEARN_01": [], "LEARN_02": [], "LEARN_03": [],
    "LEARN_04": [], "LEARN_05": [], "LEARN_06": [],
    "LEARN_07": [], "LEARN_08": [],
    "TRY_01": ["3.OA.A.3.M03"],                         # 6 jumps of 2
    "TRY_02": ["3.OA.A.3.M04"],                         # 7×3 점프 수
    "TRY_03": ["3.OA.A.3.M03"],                         # 5 jumps → ?×4
    "TRY_04": ["3.OA.A.3.M03"],                         # 3 jumps of 5
    "TRY_05": ["3.OA.A.3.M04"],                         # 9×4 양방향
    "R1_01": ["3.OA.A.3.M03"],                          # 점프 수 세기
    "R1_02": ["3.OA.A.3.M03"],                          # 4 jumps of 3
    "R1_03": ["3.OA.A.3.M03"],                          # 3 jumps of 10
    "R1_04": ["3.OA.A.3.M03"],                          # 8×2 8 jumps
    "R1_05": ["3.OA.A.3.M03"],                          # 빠진 수 (8+4=12)
    "R1_06": ["3.OA.A.3.M07"],                          # 24÷6=4 inverse
    "R1_07": ["3.OA.A.3.M03"],                          # 2 jumps of 7
    "R1_08": ["3.OA.A.3.M04"],                          # 3 jumps of 8 매칭
    "R1_09": ["3.OA.A.3.M03"],                          # 4 jumps of 9
    "R1_10": ["3.OA.A.3.M01", "3.OA.A.3.M05"],          # frog 6 jumps × 5
    "R2_01": ["3.OA.A.3.M07"],                          # 32÷4=8 inverse
    "R2_02": ["3.OA.A.3.M04"],                          # 5×6 양방향
    "R2_03": ["3.OA.A.3.M03"],                          # 5 jumps of 7
    "R2_04": ["3.OA.A.3.M03"],                          # 3 jumps of 8
    "R2_05": ["3.OA.A.3.M04"],                          # 6×3 두 패턴
    "R2_06": ["3.OA.A.3.M07"],                          # 45 → 5×9
    "R2_07": ["3.OA.A.3.M01", "3.OA.A.3.M05"],          # bike 7×4
    "R2_08": ["3.NBT.2.M01"],                           # U1 복습
    "R2_09": ["3.NBT.2.M01"],                           # U1 복습
    "R2_10": ["3.NBT.2.M01"],                           # U1 복습
    "R3_01": ["3.OA.A.3.M07", "3.OA.A.3.M04"],          # +8 패턴 분석
    "R3_02": ["3.OA.A.3.M07"],                          # 27 ÷ 3 vs ÷ 9
    "R3_03": ["3.OA.A.3.M01", "3.OA.A.3.M05"],          # picture graph 3×2
    "R3_04": ["3.OA.A.3.M01"],                          # 7 cartons × 6
    "R3_05": ["3.OA.A.3.M04"],                          # 9×4 vs 4×9
}

SKILL_TAGS = {
    "PT_01": "skip_count_pattern",
    "PT_02": "skip_count_landing",
    "PT_03": "jump_count_for_product",
    "PT_04": "skip_count_word_problem",
    "PT_05": "skip_count_landing",
    "LEARN_01": "number_line_basics",
    "LEARN_02": "jumps_vs_jump_size",
    "LEARN_03": "number_line_steps",
    "LEARN_04": "inverse_skip_count",
    "LEARN_05": "skip_count_word_problem",
    "LEARN_06": "starting_zero_rule",
    "LEARN_07": "jump_count_for_product",
    "LEARN_08": "number_line_steps",
    "TRY_01": "skip_count_landing",
    "TRY_02": "jump_count_for_product",
    "TRY_03": "inverse_skip_count",
    "TRY_04": "skip_count_landing",
    "TRY_05": "commutative_jumps",
    "R1_01": "count_jumps",
    "R1_02": "skip_count_landing",
    "R1_03": "skip_count_landing",
    "R1_04": "skip_count_landing",
    "R1_05": "missing_step_pattern",
    "R1_06": "inverse_skip_count",
    "R1_07": "skip_count_landing",
    "R1_08": "pattern_to_multiplication",
    "R1_09": "skip_count_landing",
    "R1_10": "skip_count_word_problem",
    "R2_01": "inverse_skip_count",
    "R2_02": "pattern_to_multiplication",
    "R2_03": "skip_count_landing",
    "R2_04": "skip_count_landing",
    "R2_05": "commutative_jumps",
    "R2_06": "inverse_skip_count",
    "R2_07": "skip_count_word_problem",
    "R2_08": "addition_3digit",       # U1
    "R2_09": "subtraction_3digit",    # U1
    "R2_10": "two_step_add_sub",      # U1
    "R3_01": "pattern_analysis",
    "R3_02": "inverse_skip_count",
    "R3_03": "picture_graph_to_multiplication",
    "R3_04": "skip_count_word_problem",
    "R3_05": "commutative_jumps",
}

CPA_MAP = {
    "PT_01": "pictorial",
    "PT_02": "pictorial",
    "PT_03": "pictorial",
    "PT_04": "pictorial",
    "PT_05": "pictorial",
    "LEARN_01": "concrete",
    "LEARN_02": "concrete",
    "LEARN_03": "pictorial",
    "LEARN_04": "abstract",
    "LEARN_05": "abstract",
    "LEARN_06": "concrete",
    "LEARN_07": "pictorial",
    "LEARN_08": "abstract",
    "TRY_01": "pictorial",
    "TRY_02": "pictorial",
    "TRY_03": "pictorial",
    "TRY_04": "pictorial",
    "TRY_05": "abstract",
    "R1_01": "pictorial",
    "R1_02": "pictorial",
    "R1_03": "pictorial",
    "R1_04": "pictorial",
    "R1_05": "pictorial",
    "R1_06": "abstract",
    "R1_07": "pictorial",
    "R1_08": "abstract",
    "R1_09": "pictorial",
    "R1_10": "abstract",
    "R2_01": "abstract",
    "R2_02": "abstract",
    "R2_03": "abstract",
    "R2_04": "abstract",
    "R2_05": "abstract",
    "R2_06": "abstract",
    "R2_07": "abstract",
    "R2_08": "abstract",
    "R2_09": "abstract",
    "R2_10": "abstract",
    "R3_01": "abstract",
    "R3_02": "abstract",
    "R3_03": "abstract",
    "R3_04": "abstract",
    "R3_05": "abstract",
}


def make_verification(item_id: str) -> dict:
    return {
        "concept_source": "Go Math Grade 3 Ch.3 Lesson 3.3 'Skip Count on a Number Line' pp.109-112",
        "procedure_source": "EngageNY Grade 3 Module 1 Topic E — Multiplication Using a Number Line",
        "assessment_source": "Smarter Balanced Grade 3 Mathematics Item Specifications 2015",
    }


def add_item_fields(item: dict) -> dict:
    item_id = item["id"]
    if "cpa_phase" in item:
        item["cpa_stage"] = item.pop("cpa_phase")
    elif "cpa_stage" not in item:
        item["cpa_stage"] = CPA_MAP.get(item_id, "abstract")
    if item_id in CPA_MAP:
        item["cpa_stage"] = CPA_MAP[item_id]
    if "skill_tag" not in item:
        item["skill_tag"] = SKILL_TAGS.get(item_id, "skip_count_landing")
    if item.get("hints") and not item.get("feedback_correct"):
        item["feedback_correct"] = (
            item.get("feedback", {}).get("correct")
            or "정답입니다! 잘 했어요."
        )
    item["expected_errors"] = ERRORS_MAP.get(item_id, [])
    item.setdefault("math_note", "")
    item["verification"] = make_verification(item_id)
    return item


# ── 신규 LEARN 카드 (LEARN_06 ~ LEARN_08) ─────────────────────────────────
NEW_LEARN_CARDS = [
    {
        "id": "LEARN_06",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "0은 점프가 아니라 출발점입니다",
        "content": (
            "수직선에서 0은 출발점일 뿐, 점프 횟수에 포함되지 않습니다. "
            "5 × 3을 그릴 때: 0에서 시작 → 첫 번째 점프 → 5 (점프 1) → "
            "10 (점프 2) → 15 (점프 3). 총 3번 점프하여 15에 도착. "
            "흔한 실수: 0을 1번째 점프로 세어 4번 점프하면 20에 도착하는 오류. "
            "팁: 점프(arc, 곡선)를 세고, 도착점(점)을 세지 마세요."
        ),
        "cpa_stage": "concrete",
        "visual_type": "manipulative",
        "visual_data": {"tool": "number_line", "config": {"min": 0, "max": 20, "step": 5}},
    },
    {
        "id": "LEARN_07",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "점프 크기 먼저, 점프 횟수 다음",
        "content": (
            "곱셈식 a × b를 수직선으로 그릴 때 — "
            "첫 번째 인자 a = 점프 횟수, 두 번째 인자 b = 점프 크기. "
            "예: 4 × 5 → 5씩 4번 점프 (5, 10, 15, 20). "
            "흔한 실수: 4씩 5번 점프하면 (4, 8, 12, 16, 20) 답은 같지만 "
            "모델이 다르므로 '몇 그룹?' 물으면 틀립니다. "
            "팁: 'b'를 화살표 위에 적고, 'a'번만큼 화살표를 그리세요."
        ),
        "cpa_stage": "pictorial",
        "visual_type": "manipulative",
        "visual_data": {"tool": "number_line", "config": {"min": 0, "max": 20, "step": 5}},
    },
    {
        "id": "LEARN_08",
        "section": "learn",
        "difficulty": 0,
        "type": "concept_card",
        "title": "수직선 곱셈 — 4단계 요약",
        "content": (
            "1단계: 0에서 시작. "
            "2단계: 점프 크기 정하기 (= 한 그룹의 크기). "
            "3단계: 그 크기만큼 점프 — '몇 그룹'만큼 반복. "
            "4단계: 도착한 수 = 곱(product). "
            "역방향: 도착한 수 ÷ 점프 크기 = 점프 횟수 (나눗셈 미리보기). "
            "검증: '점프 호'의 개수 = 첫 번째 인자인지 확인!"
        ),
        "cpa_stage": "abstract",
        "visual_type": "strategy_summary",
    },
]

# ── R2_08/09/10 U1 복습 항목 ────────────────────────────────────────────
U1_REVIEW_R2 = [
    {
        "id": "R2_08",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the sum: 458 + 367.",
        "choices": ["A. 715", "B. 725", "C. 815", "D. 825"],
        "answer": "D",
        "explanation": "458+367: 8+7=15 (carry 1), 5+6+1=12 (carry 1), 4+3+1=8. Result: 825.",
        "hints": [
            "Line up the digits — ones, tens, hundreds.",
            "Carry when a column total reaches 10.",
        ],
        "feedback": {
            "correct": "Right — 825.",
            "incorrect": "458+367=825. Watch the carries.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_09",
        "section": "practice_r2",
        "difficulty": 2,
        "question": "Find the difference: 600 − 247.",
        "choices": ["A. 343", "B. 353", "C. 363", "D. 453"],
        "answer": "B",
        "explanation": "600−247: borrow across zeros. 0−7 → 10−7=3 (borrow); tens 0−4 → 10−5=5; hundreds 5−2=3. Result: 353.",
        "hints": [
            "Borrowing across zeros is tricky — work right to left.",
            "Once you borrow from the hundreds, the tens become 10 and then 9 after lending to ones.",
        ],
        "feedback": {
            "correct": "Right — 353.",
            "incorrect": "600−247=353. Borrow across the zeros.",
        },
        "review_from": "U1",
    },
    {
        "id": "R2_10",
        "section": "practice_r2",
        "difficulty": 3,
        "question": "Sara had 736 stickers. She gave 158 to a friend, then bought 92 more. How many stickers does she have now?",
        "choices": ["A. 486", "B. 578", "C. 670", "D. 886"],
        "answer": "C",
        "explanation": "Step 1: 736−158=578. Step 2: 578+92=670.",
        "hints": [
            "Two steps: subtract first (gave away), then add (bought).",
            "736−158=578, then 578+92=670.",
        ],
        "feedback": {
            "correct": "Right — 670 stickers.",
            "incorrect": "736−158=578, then +92=670.",
        },
        "review_from": "U1",
    },
]


def upgrade():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)
    if "pretest" in d:
        print("⚠️  이미 업그레이드됨.")
        return

    raw_items = d.pop("items", [])
    for item in raw_items:
        if item["id"].startswith("LN_"):
            item["id"] = f"LEARN_{item['id'][3:]}"

    sections_map: dict = {
        "pretest": [], "learn": [], "try": [],
        "practice_r1": [], "practice_r2": [], "practice_r3": [],
    }
    for item in raw_items:
        sec = item.get("section", "")
        if sec in sections_map:
            sections_map[sec].append(item)

    sections_map["learn"].extend(NEW_LEARN_CARDS)

    r2_keep_ids = {f"R2_0{i}" for i in range(1,8)}
    sections_map["practice_r2"] = [
        i for i in sections_map["practice_r2"] if i["id"] in r2_keep_ids
    ]
    sections_map["practice_r2"].extend(U1_REVIEW_R2)

    for sec_key, items in sections_map.items():
        sections_map[sec_key] = [add_item_fields(item) for item in items]

    counts = {k: len(v) for k, v in sections_map.items()}
    print("섹션별 문항 수:", counts)
    total = sum(counts.values())
    print(f"총 문항 수: {total} (목표: 43)")
    assert counts == {"pretest":5,"learn":8,"try":5,"practice_r1":10,"practice_r2":10,"practice_r3":5}

    u1 = [i["id"] for i in sections_map["practice_r2"] if i.get("review_from") == "U1"]
    print(f"R2 U1 복습: {u1}")

    d["pretest"]     = sections_map["pretest"]
    d["learn"]       = sections_map["learn"]
    d["try"]         = sections_map["try"]
    d["practice_r1"] = sections_map["practice_r1"]
    d["practice_r2"] = sections_map["practice_r2"]
    d["practice_r3"] = sections_map["practice_r3"]

    d["vertical_alignment"] = {
        "prerequisite": "G3 U3 L1-L2 — 등량 그룹·반복 덧셈을 곱셈으로 (3.OA.A.1)",
        "current":      "G3 — 수직선 건너뛰며 세기로 곱셈 모델링 (3.OA.A.3)",
        "successor":    "G3 U3 L4-L5 — 곱셈 모델링·배열 (3.OA.A.3)",
    }

    d.setdefault("metadata", {})
    d["metadata"]["total_items"] = total
    d["metadata"]["upgraded"] = True
    d["metadata"]["upgrade_script"] = "scripts/upgrade_u3_l3.py"
    d["metadata"]["review_from_units"] = ["U1"]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ 업그레이드 완료: {SRC}")


if __name__ == "__main__":
    upgrade()
