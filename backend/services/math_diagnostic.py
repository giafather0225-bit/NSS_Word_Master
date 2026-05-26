"""
backend/services/math_diagnostic.py — 수학 오답 진단 엔진.

학습자가 오답을 냈을 때:
1) 어느 선택지(A/B/C/D)를 골랐는지 추출
2) 해당 항목의 expected_errors[choice]에서 error_type + misconception_id 조회
3) misconception_id가 비어 있으면 후보(misconception_candidates)에서 error_type 기반 추론
4) 라이브러리에서 short_label/description/example 끌어와 진단 결과 합성

설계 원칙
- 순수 함수 (DB 없음): in/out으로 단위 테스트 용이
- 라이브러리는 모듈 임포트 시 한 번 로드 후 LRU 캐싱
- 매칭 실패 시 안전한 fallback (error_type='concept_gap', misconception_id=None)
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data" / "math"

# === 라이브러리 로더 ===

@lru_cache(maxsize=8)
def _load_misconception_library(grade: str) -> dict:
    """{ccss: {ids: {mid: misc_dict}, ets: {error_type: mid}}}"""
    lib_dir = _DATA_DIR / grade / "misconceptions"
    out: dict = {}
    if not lib_dir.exists():
        return out
    for path in lib_dir.glob("*.json"):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            logger.warning("misconception lib parse fail %s: %s", path, e)
            continue
        ccss = d.get("standard") or path.stem
        ids = {}
        ets = {}
        for m in d.get("misconceptions", []) or []:
            mid = m.get("misconception_id")
            et = m.get("error_type")
            if mid:
                ids[mid] = m
                if et:
                    ets[et] = mid
        out[ccss] = {"ids": ids, "ets": ets}
    return out


def clear_library_cache() -> None:
    """단위 테스트나 데이터 핫리로드 후 호출."""
    _load_misconception_library.cache_clear()


def _resolve_lib_entry(ccss: str, lib: dict):
    """exact match → 부모 fallback."""
    if not ccss:
        return None
    if ccss in lib:
        return lib[ccss]
    # 자식 → 부모: 마지막 소문자 한 글자 제거 (3.NF.A.3a → 3.NF.A.3)
    if ccss[-1].isalpha() and ccss[-1].islower():
        parent = ccss[:-1]
        if parent in lib:
            return lib[parent]
    return None


# === 선택지 추출 ===

def extract_user_choice(user_answer: str, choices: list, correct_raw: str = "") -> Optional[str]:
    """
    user_answer가 어느 선택지인지(A/B/C/D...) 결정. 매칭 실패 시 None.

    매칭 우선순위:
      1) user_answer가 정확히 한 글자 (A-H) 이고 choices 범위 내 → 그 글자
      2) user_answer가 "B) 588" 처럼 라벨 prefix → 첫 글자
      3) choices 중 텍스트 일치(라벨 떼고 비교) → 그 라벨
    """
    if not user_answer or not choices:
        return None
    ua = str(user_answer).strip()
    # 1) 한 글자 라벨
    if len(ua) == 1 and ua.upper() in "ABCDEFGH":
        idx = ord(ua.upper()) - 65
        if 0 <= idx < len(choices):
            return ua.upper()
    # 2) "B) 588" 같은 prefix
    if len(ua) >= 2 and ua[0].upper() in "ABCDEFGH" and ua[1] in ")":
        return ua[0].upper()
    # 3) 텍스트 매칭
    ua_lower = ua.lower()
    for c in choices:
        if not isinstance(c, str) or len(c) < 2:
            continue
        label = c[0].upper() if c[0].upper() in "ABCDEFGH" else None
        clean = c.split(")", 1)[-1].strip().lower() if ")" in c else c.strip().lower()
        if ua_lower == c.strip().lower() or ua_lower == clean:
            return label
    return None


# === 메인 진단 함수 ===

def diagnose(problem: dict, user_answer: str, grade: str = "G3", *, is_correct: bool = False) -> dict:
    """
    오답에 대한 진단 결과 합성.

    반환 dict (정답이면 빈 결과로 통과):
      {
        "error_type": "concept_gap",          # 항목·라이브러리 매칭 결과 (오답 시)
        "misconception_id": "3.NBT.A.2.M03" | None,
        "short_label": "..." | None,
        "note": "...",                         # 학습자에게 보여줄 짧은 설명
        "candidates": [...]                    # 다른 가능성 (UI에서 hint로 사용 가능)
      }
    """
    if is_correct:
        return {"error_type": "none", "misconception_id": None,
                "short_label": None, "note": "", "candidates": []}

    if not isinstance(problem, dict):
        return _generic_fallback()

    ccss = problem.get("ccss")
    if isinstance(ccss, list):
        ccss = ccss[0] if ccss else None
    expected_errors = problem.get("expected_errors") or {}
    # list-shape 방어: 일부 레거시 항목이 [strings] 형식 → _wrong 키로 변환
    if isinstance(expected_errors, list):
        joined = "; ".join(str(x) for x in expected_errors if x)
        expected_errors = {"_wrong": {"error_type": "concept_gap", "note": joined}} if joined else {}
    elif not isinstance(expected_errors, dict):
        expected_errors = {}
    candidates = problem.get("misconception_candidates") or []
    choices = problem.get("choices") or []

    lib = _load_misconception_library(grade)
    lib_entry = _resolve_lib_entry(ccss, lib)

    # 1) 선택지 식별 → expected_errors 조회
    choice_label = extract_user_choice(user_answer, choices, problem.get("correct_answer", ""))
    chosen_ee: dict = {}
    if choice_label and choice_label in expected_errors:
        chosen_ee = expected_errors[choice_label] or {}
    elif "_wrong" in expected_errors:
        chosen_ee = expected_errors["_wrong"] or {}
    else:
        # MC가 아니거나 매칭 실패 — 첫 expected_errors 엔트리 활용 시도
        for k, v in expected_errors.items():
            if isinstance(v, dict):
                chosen_ee = v
                break

    error_type = chosen_ee.get("error_type") or "concept_gap"
    misconception_id = chosen_ee.get("misconception_id")
    note = chosen_ee.get("note") or ""

    # 2) misconception_id 추론 (없으면 error_type → 라이브러리 매칭)
    if not misconception_id and lib_entry:
        ets = lib_entry.get("ets", {})
        if error_type in ets:
            misconception_id = ets[error_type]

    # 3) 라이브러리 상세 합성
    short_label = None
    if misconception_id and lib_entry:
        m = lib_entry.get("ids", {}).get(misconception_id)
        if m:
            short_label = m.get("short_label")
            # note 비어 있으면 라이브러리 description 일부 사용
            if not note:
                note = m.get("short_label") or m.get("description", "")[:160]

    return {
        "error_type": error_type,
        "misconception_id": misconception_id,
        "short_label": short_label,
        "note": note,
        "candidates": candidates,
    }


def _generic_fallback() -> dict:
    return {
        "error_type": "concept_gap",
        "misconception_id": None,
        "short_label": None,
        "note": "Review the concept and check each solution step carefully.",
        "candidates": [],
    }


def get_misconception(grade: str, misconception_id: str) -> Optional[dict]:
    """ID로 라이브러리 항목 전체 가져오기 (대시보드/코칭 UI용)."""
    if not misconception_id:
        return None
    lib = _load_misconception_library(grade)
    for ccss, entry in lib.items():
        m = entry.get("ids", {}).get(misconception_id)
        if m:
            return {"ccss": ccss, **m}
    return None
