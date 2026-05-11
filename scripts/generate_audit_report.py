#!/usr/bin/env python3
"""
G3 Math Lesson 7-Stage Audit Report Generator
사용법: python3 scripts/generate_audit_report.py G3 U1 L1
출력: 각 Stage 통과/실패 상세 + 다음 액션 제안
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# 저장소 루트
REPO_ROOT = Path(__file__).parent.parent
G3_ROOT = REPO_ROOT / "backend" / "data" / "math" / "G3"
MISCONCEPTION_DIR = G3_ROOT / "misconceptions"

# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────

def load_lesson(grade: str, unit_num: str, lesson_num: str) -> tuple[dict, Path]:
    """JSON 파일 로드. (lesson_data, file_path) 반환."""
    unit_dirs = [d for d in G3_ROOT.iterdir() if d.is_dir() and d.name.startswith(f"U{unit_num}_")]
    if not unit_dirs:
        raise FileNotFoundError(f"Unit U{unit_num} 폴더를 찾을 수 없습니다: {G3_ROOT}")
    unit_dir = unit_dirs[0]

    lesson_files = list(unit_dir.glob(f"L{lesson_num}_*.json"))
    if not lesson_files:
        raise FileNotFoundError(f"Lesson L{lesson_num} JSON을 찾을 수 없습니다: {unit_dir}")
    lesson_path = lesson_files[0]

    with open(lesson_path, encoding="utf-8") as f:
        return json.load(f), lesson_path


def load_misconception_pool(ccss_code: str) -> list[dict]:
    """misconceptions/[CCSS_CODE].json 로드."""
    pool_path = MISCONCEPTION_DIR / f"{ccss_code}.json"
    if not pool_path.exists():
        return []
    with open(pool_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("misconceptions", [])


def all_items(lesson: dict) -> list[dict]:
    """pretest + learn + try + practice_r1/r2/r3 모든 문항 수집."""
    items = []
    # JSON 키는 "try" (try_problems 아님)
    for section in ("pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"):
        items.extend(lesson.get(section, []))
    return items


# ─────────────────────────────────────────────
# Stage 1 — Standards Alignment
# ─────────────────────────────────────────────

def check_stage1(lesson: dict) -> dict:
    """CCSS 코드 유효성, vertical_alignment 필드 존재 여부 확인."""
    issues = []

    # 레슨 레벨 CCSS
    lesson_ccss = lesson.get("ccss", [])
    if not lesson_ccss:
        issues.append("lesson.ccss 필드 없음")

    # 레슨 레벨 vertical_alignment
    va = lesson.get("vertical_alignment")
    if not va:
        issues.append("lesson.vertical_alignment 필드 없음")
    else:
        if not va.get("prerequisite"):
            issues.append("vertical_alignment.prerequisite 없음")
        if not va.get("successor"):
            issues.append("vertical_alignment.successor 없음")

    # tier 필드
    if not lesson.get("tier"):
        issues.append("lesson.tier 필드 없음 (A/B/C 필요)")

    # essential_question
    if not lesson.get("essential_question"):
        issues.append("lesson.essential_question 없음")

    # 각 문항의 ccss 태그
    item_missing_ccss = []
    for item in all_items(lesson):
        item_id = item.get("id", "?")
        if not item.get("ccss"):
            item_missing_ccss.append(item_id)
    if item_missing_ccss:
        issues.append(f"문항 ccss 누락: {item_missing_ccss[:5]}{'...' if len(item_missing_ccss) > 5 else ''}")

    passed = len(issues) == 0
    return {"stage": 1, "name": "Standards Alignment", "passed": passed, "issues": issues}


# ─────────────────────────────────────────────
# Stage 2 — Triple-Source Verification
# ─────────────────────────────────────────────

def check_stage2(lesson: dict) -> dict:
    """각 문항의 concept_source, procedure_source, assessment_source 채움 여부."""
    issues = []
    missing_sources: dict[str, list[str]] = {"concept": [], "procedure": [], "assessment": []}

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        v = item.get("verification", {})
        if isinstance(v, str):
            # 이전 포맷 (문자열) — 아직 업그레이드 안 됨
            missing_sources["concept"].append(item_id)
            missing_sources["procedure"].append(item_id)
            missing_sources["assessment"].append(item_id)
            continue

        if not v.get("concept_source", {}).get("url"):
            missing_sources["concept"].append(item_id)
        if not v.get("procedure_source", {}).get("url"):
            missing_sources["procedure"].append(item_id)
        # assessment_source는 선택적이지만 존재 여부 확인
        # (없어도 S2 통과 — concept+procedure 2개면 충분)

    # 2개 이상 출처 충족: concept + procedure 모두 있으면 통과
    for src_type, ids in missing_sources.items():
        if src_type == "assessment":
            continue  # assessment는 경고만
        if ids:
            short = ids[:5]
            suffix = "..." if len(ids) > 5 else ""
            issues.append(f"{src_type}_source 누락 ({len(ids)}개): {short}{suffix}")

    # assessment_source 누락은 경고로만
    warnings = []
    if missing_sources["assessment"]:
        warnings.append(f"assessment_source 누락 ({len(missing_sources['assessment'])}개) — 권장사항")

    passed = len(issues) == 0
    return {"stage": 2, "name": "Triple-Source Verification", "passed": passed,
            "issues": issues, "warnings": warnings}


# ─────────────────────────────────────────────
# Stage 3 — Mathematical Correctness
# ─────────────────────────────────────────────

def check_stage3(lesson: dict) -> dict:
    """sympy로 수식 정답 검증. 기본 산수 MC 문항만 자동 검증."""
    issues = []
    skipped = []

    try:
        import sympy
    except ImportError:
        return {"stage": 3, "name": "Mathematical Correctness",
                "passed": False, "issues": ["sympy 미설치 — pip install sympy"],
                "skipped": []}

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        q = item.get("question", "")
        correct = item.get("correct_answer", item.get("answer", ""))
        choices = item.get("choices", [])

        # "X op Y (op Z ...) = ?" 형식만 자동 검증 (추정/호환수 문항은 건너뜀)
        import re
        if re.search(r'estim|compatible', q, re.IGNORECASE):
            skipped.append(item_id)
            continue

        # bar model 선택 / 개념 문항 스킵: 수식이 따옴표 안에 있으면 묘사용이므로 자동 검증 대상 아님
        # 예) "Which bar model shows '348 + 156 = ?'?" → 스킵
        if re.search(r"['\"][\d\s\+\-\×\*\/x]+(?:\s*=\s*\?)?\s*['\"]", q):
            skipped.append(item_id)
            continue

        # 다중 피연산자 덧셈/뺄셈: "a + b + c (+ d) = ?" 전체 추출
        ma = re.search(r'([\d]+(?:\s*[\+\-\×\*\/x]\s*[\d]+)+)\s*=\s*\?', q)
        if not ma:
            skipped.append(item_id)
            continue
        expr_str = ma.group(1)
        # × → * 변환
        expr_str = re.sub(r'[×x]', '*', expr_str)

        try:
            expected = int(sympy.sympify(expr_str))
        except Exception:
            skipped.append(item_id)
            continue

        # MC: correct_answer는 "B" 같은 레이블 — choices에서 실제 값 추출
        # choices는 list 또는 {"A": ..., "B": ...} dict 두 형식 모두 지원
        actual_val = None
        if choices and len(correct) == 1 and correct.upper() in "ABCD":
            key = correct.upper()
            if isinstance(choices, dict):
                choice_text = choices.get(key, "")
            else:
                idx = ord(key) - ord("A")
                choice_text = choices[idx] if idx < len(choices) else ""
            nums = re.findall(r'\d+', choice_text)
            if nums:
                actual_val = int(nums[-1])
        elif correct.lstrip("-").isdigit():
            actual_val = int(correct)

        if actual_val is not None and actual_val != expected:
            issues.append(f"{item_id}: 기대={expected}, JSON답={actual_val} (문제: '{q}')")

    passed = len(issues) == 0
    return {"stage": 3, "name": "Mathematical Correctness", "passed": passed,
            "issues": issues, "skipped": skipped}


# ─────────────────────────────────────────────
# Stage 4 — Solution-Explanation Consistency
# ─────────────────────────────────────────────

def check_stage4(lesson: dict) -> dict:
    """hint와 feedback이 정답과 일관된 풀이 경로를 가지는지 기본 패턴 확인."""
    issues = []

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        correct = str(item.get("correct_answer", item.get("answer", "")))
        hints = item.get("hints", [])
        feedback_correct = item.get("feedback_correct", "")
        feedback_wrong = item.get("feedback_wrong", "")

        # hint가 있지만 feedback_correct가 없는 경우
        if hints and not feedback_correct:
            issues.append(f"{item_id}: hints 있지만 feedback_correct 없음")

        # feedback_wrong에 올바른 답이 전혀 언급되지 않는 경우 (단순 텍스트 포함 여부)
        # — 완전한 AI 검증 아님, 기본 패턴만 확인
        if feedback_wrong and len(feedback_wrong) < 10:
            issues.append(f"{item_id}: feedback_wrong이 너무 짧음 ('{feedback_wrong}')")

        # solution_steps가 있을 때 hints와 최소 1개 공통 키워드 확인 (선택적)
        # Phase 1에서는 수동 검토 표시만
        solution_steps = item.get("solution_steps", [])
        if hints and solution_steps:
            pass  # TODO Phase 2: AI 패턴 매칭으로 일관성 점수 계산

    passed = len(issues) == 0
    return {"stage": 4, "name": "Solution-Explanation Consistency",
            "passed": passed, "issues": issues,
            "note": "AI 패턴 매칭은 Phase 2에서 활성화 예정. 현재는 구조적 완전성만 검사."}


# ─────────────────────────────────────────────
# Stage 5 — Pedagogical Validity (7 sub-items)
# ─────────────────────────────────────────────

def check_stage5(lesson: dict) -> dict:
    """7개 교수법 기준 확인."""
    sub_results = {}
    issues = []
    warnings = []

    learn_cards = lesson.get("learn", [])
    try_items = lesson.get("try", [])  # JSON 키는 "try"
    pretest = lesson.get("pretest", [])
    r2 = lesson.get("practice_r2", [])

    # 1. CPA 순서: LEARN 카드에 concrete, pictorial, abstract 모두 있는가
    cpa_stages = [c.get("cpa_stage") or c.get("cpa_phase") for c in learn_cards]
    has_concrete = "concrete" in cpa_stages
    has_pictorial = "pictorial" in cpa_stages
    has_abstract = "abstract" in cpa_stages
    cpa_ok = has_concrete and has_pictorial and has_abstract
    sub_results["cpa_order"] = cpa_ok
    if not cpa_ok:
        missing = [s for s, present in [("concrete", has_concrete), ("pictorial", has_pictorial), ("abstract", has_abstract)] if not present]
        issues.append(f"CPA 순서 불완전 — 누락 단계: {missing}")

    # 2. Bloom 분포: pretest difficulty 1→3 누진
    if pretest:
        diffs = [item.get("difficulty", 0) for item in pretest]
        bloom_ok = len(diffs) >= 3 and diffs[0] <= diffs[-1]
        sub_results["bloom_distribution"] = bloom_ok
        if not bloom_ok:
            issues.append(f"Pretest Bloom 레벨 비누진: {diffs}")
    else:
        sub_results["bloom_distribution"] = False
        issues.append("pretest 없음 (Bloom 분포 확인 불가)")

    # 3. Worked Example fade: TRY 카드 hint_level 감소 (full→weak→independent)
    if try_items and len(try_items) >= 3:
        hint_levels = [t.get("hint_level", t.get("scaffold_level", None)) for t in try_items]
        valid_levels = [h for h in hint_levels if h is not None]
        if valid_levels:
            fade_ok = valid_levels == sorted(valid_levels, reverse=True)
            if not fade_ok:
                issues.append(f"TRY hint_level 감소 순서 불일치: {valid_levels}")
        else:
            # hint_level 필드 자체 없으면 구조로 확인 (향후 세분화)
            fade_ok = True  # 필드 없으면 패스 (경고만)
            warnings.append("TRY 문항 hint_level 필드 없음 — Worked Example fade 수동 확인 필요 [REVIEW NEEDED]")
        sub_results["worked_example_fade"] = fade_ok
    else:
        sub_results["worked_example_fade"] = False
        issues.append(f"TRY 문항 부족 ({len(try_items)}개, 최소 3개 필요)")

    # 4. Math Talk: LEARN 카드에 type="explain" 또는 explain 키워드 ≥1
    explain_cards = [c for c in learn_cards if c.get("type") == "explain" or "explain" in str(c.get("interaction", "")).lower()]
    math_talk_ok = len(explain_cards) >= 1
    sub_results["math_talk"] = math_talk_ok
    if not math_talk_ok:
        issues.append("Math Talk (type='explain') LEARN 카드 없음")

    # 5. Interleaving: R2 마지막 25%에 review_from 문항 있는지
    review_from = lesson.get("review_from_units", [])
    if r2:
        cutoff = max(1, len(r2) * 3 // 4)
        tail = r2[cutoff:]
        tail_has_review = any(item.get("review_from") or item.get("from_unit") for item in tail)
        interleave_ok = tail_has_review if review_from else True  # review_from 지정 없으면 패스
        sub_results["interleaving"] = interleave_ok
        if review_from and not tail_has_review:
            issues.append(f"R2 마지막 25% interleave 문항 없음 (review_from_units={review_from})")
    else:
        sub_results["interleaving"] = False
        issues.append("practice_r2 없음 (interleave 확인 불가)")

    # 6. Lesson Summary card: 마지막 LEARN 카드가 type="summary"
    if learn_cards:
        last_card = learn_cards[-1]
        summary_ok = last_card.get("type") == "summary"
        sub_results["lesson_summary"] = summary_ok
        if not summary_ok:
            issues.append(f"마지막 LEARN 카드 type!=summary (현재: '{last_card.get('type')}')")
    else:
        sub_results["lesson_summary"] = False
        issues.append("LEARN 카드 없음")

    # 7. Unit messages: essential_question + unit_intro_message + unit_close_message
    eq_ok = bool(lesson.get("essential_question"))
    ui_ok = bool(lesson.get("unit_intro_message"))
    uc_ok = bool(lesson.get("unit_close_message"))
    messages_ok = eq_ok and ui_ok and uc_ok
    sub_results["unit_messages"] = messages_ok
    if not eq_ok:
        issues.append("essential_question 없음")
    if not ui_ok:
        issues.append("unit_intro_message 없음")
    if not uc_ok:
        issues.append("unit_close_message 없음")

    passed = len(issues) == 0
    return {"stage": 5, "name": "Pedagogical Validity",
            "passed": passed, "issues": issues, "warnings": warnings, "sub_results": sub_results}


# ─────────────────────────────────────────────
# Stage 6 — Misconception Validity
# ─────────────────────────────────────────────

def check_stage6(lesson: dict) -> dict:
    """expected_errors의 모든 항목이 misconception_id + citation을 가지는지 확인."""
    issues = []

    # 레슨의 CCSS 코드로 misconception pool 로드
    lesson_ccss = lesson.get("ccss", [])
    pool_ids: set[str] = set()
    for ccss in lesson_ccss:
        pool = load_misconception_pool(ccss)
        for m in pool:
            pool_ids.add(m["misconception_id"])

    for item in all_items(lesson):
        item_id = item.get("id", "?")
        expected_errors = item.get("expected_errors", {})

        # expected_errors가 dict (이전 포맷) or list (새 포맷)
        if isinstance(expected_errors, dict):
            error_list = list(expected_errors.values())
        elif isinstance(expected_errors, list):
            error_list = expected_errors
        else:
            continue

        for err in error_list:
            if not isinstance(err, dict):
                continue
            # 순수 careless 에러는 misconception_id 불필요
            if err.get("error_type") == "careless":
                continue
            mid = err.get("misconception_id")
            citation = err.get("citation")
            if not mid:
                # 이전 포맷 (error_type/note만 있음) — 업그레이드 필요
                if "error_type" in err:
                    issues.append(f"{item_id}: 이전 포맷 expected_error — misconception_id + citation 추가 필요")
                else:
                    issues.append(f"{item_id}: expected_error에 misconception_id 없음")
            elif pool_ids and mid not in pool_ids:
                issues.append(f"{item_id}: misconception_id '{mid}'이 pool에 없음")
            if mid and not citation:
                issues.append(f"{item_id}: expected_error에 citation 없음 (mid={mid})")

    passed = len(issues) == 0
    return {"stage": 6, "name": "Misconception Validity", "passed": passed, "issues": issues,
            "pool_size": len(pool_ids)}


# ─────────────────────────────────────────────
# Stage 7 — Learner Validation (수동)
# ─────────────────────────────────────────────

def check_stage7(lesson: dict) -> dict:
    """시범 운영 전까지 pending. stage_status.s7 확인만."""
    s7_values = []
    for item in all_items(lesson):
        v = item.get("verification", {})
        if isinstance(v, dict):
            ss = v.get("stage_status", {})
            s7_values.append(ss.get("s7"))

    all_pending = all(v is None for v in s7_values)
    all_passed = all(v is True for v in s7_values) if s7_values else False

    return {
        "stage": 7,
        "name": "Learner Validation",
        "passed": all_passed,
        "pending": all_pending,
        "note": "시범 운영 2026-06-13~19 또는 First Pass 완료 후 측정. 현재 pending 정상."
    }


# ─────────────────────────────────────────────
# 보고서 출력
# ─────────────────────────────────────────────

def print_report(lesson: dict, lesson_path: Path, results: list[dict]) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    tier = lesson.get("tier", "?")
    title = lesson.get("title", lesson.get("lesson_id", "?"))

    print("\n" + "=" * 60)
    print(f"  G3 Math 7-Stage Audit Report")
    print(f"  Lesson : {lesson_path.parent.name} / {lesson_path.name}")
    print(f"  Title  : {title}   [Tier {tier}]")
    print(f"  Date   : {now}")
    print("=" * 60)

    overall_pass = True
    for r in results:
        stage_num = r["stage"]
        name = r["name"]
        passed = r.get("passed", False)
        pending = r.get("pending", False)

        if pending:
            icon = "⏳"
            status = "PENDING"
        elif passed:
            icon = "✅"
            status = "PASS"
        else:
            icon = "❌"
            status = "FAIL"
            if stage_num != 7:
                overall_pass = False

        print(f"\nStage {stage_num} — {name}")
        print(f"  {icon} {status}")

        for issue in r.get("issues", []):
            print(f"    ⚠  {issue}")
        for warn in r.get("warnings", []):
            print(f"    💡 {warn}")
        if r.get("note"):
            print(f"    ℹ  {r['note']}")

        # Stage 5 sub-results
        if stage_num == 5 and "sub_results" in r:
            print("  Sub-items:")
            labels = {
                "cpa_order": "CPA 순서",
                "bloom_distribution": "Bloom 분포",
                "worked_example_fade": "Worked Example fade",
                "math_talk": "Math Talk",
                "interleaving": "Interleaving",
                "lesson_summary": "Lesson Summary 카드",
                "unit_messages": "Unit 메시지",
            }
            for key, label in labels.items():
                ok = r["sub_results"].get(key, False)
                print(f"    {'✅' if ok else '❌'} {label}")

        # Stage 3 skipped
        if stage_num == 3 and r.get("skipped"):
            print(f"    ℹ  자동 검증 불가 문항 {len(r['skipped'])}개 (수식 없음 또는 복잡한 형식)")

        # Stage 6 pool size
        if stage_num == 6:
            print(f"    ℹ  Misconception pool 크기: {r.get('pool_size', 0)}개")

    print("\n" + "=" * 60)
    print(f"  최종 결과: {'✅ 통과 (Stage 7 pending)' if overall_pass else '❌ 실패 — 아래 액션 필요'}")
    print("=" * 60)

    # 다음 액션 제안
    failed_stages = [r["stage"] for r in results if not r.get("passed") and not r.get("pending") and r["stage"] != 7]
    if failed_stages:
        print("\n다음 액션:")
        action_map = {
            1: "lesson JSON에 tier, vertical_alignment, essential_question, 문항 ccss 필드 추가",
            2: "각 문항 verification 객체에 concept_source + procedure_source URL 추가",
            3: "정답 불일치 항목 수정 (sympy 검증 기준)",
            4: "hints/feedback 검토: 정답과 동일한 풀이 경로 사용하는지 확인",
            5: "LEARN 카드 CPA 순서, Math Talk, Summary 카드, unit_intro/close_message 추가",
            6: "expected_errors에 misconception_id + citation 추가 (misconceptions/ 풀 참조)",
        }
        for s in failed_stages:
            print(f"  Stage {s}: {action_map.get(s, '수동 확인 필요')}")

    if overall_pass:
        print("\n커밋 명령:")
        lesson_name = lesson_path.stem
        unit_name = lesson_path.parent.name
        print(f"  git add backend/data/math/G3/{unit_name}/{lesson_name}.json")
        print(f"  git commit -m 'verify: G3 {unit_name} {lesson_name} 7-stage pass'")
        print(f"  git push")
    print()


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print("사용법: python3 scripts/generate_audit_report.py G3 U<N> L<N>")
        print("예시:   python3 scripts/generate_audit_report.py G3 U1 L1")
        sys.exit(1)

    grade = sys.argv[1]
    unit_arg = sys.argv[2].lstrip("Uu")
    lesson_arg = sys.argv[3].lstrip("Ll")

    try:
        lesson, lesson_path = load_lesson(grade, unit_arg, lesson_arg)
    except FileNotFoundError as e:
        print(f"오류: {e}")
        sys.exit(1)

    results = [
        check_stage1(lesson),
        check_stage2(lesson),
        check_stage3(lesson),
        check_stage4(lesson),
        check_stage5(lesson),
        check_stage6(lesson),
        check_stage7(lesson),
    ]

    print_report(lesson, lesson_path, results)

    # 실패 Stage 있으면 exit code 1
    failed = [r for r in results if not r.get("passed") and not r.get("pending") and r["stage"] != 7]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
