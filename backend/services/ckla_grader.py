"""
services/ckla_grader.py — CKLA 문제 AI 채점 엔진
Section: Academy
Dependencies: ai_service._ollama_chat, ai_service._gemini_generate
API: none (service layer)

채점 기준 (0-2 scale):
  2: 정답 — 지문 근거 명확, 완전한 답
  1: 부분 — 방향 맞지만 근거/디테일 부족
  0: 오답 — 오해 또는 무관한 답

피드백 원칙:
  - 9살 native English speaker 수준 언어
  - Socratic: 답을 직접 주지 않고 유도 질문
  - 격려적 어조 유지
  - 60단어 이하

question kind별 전략:
  Literal     → 지문에서 직접 찾을 수 있는 사실 문제. 정확도 중심.
  Inferential → 지문을 바탕으로 한 추론. 논리적 과정 평가.
  Evaluative  → 의견 + 지문 근거. 근거 없는 의견은 점수 1.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from backend.ai_service import _ollama_chat, _gemini_generate

log = logging.getLogger(__name__)

# 지문 길이 제한 — 프롬프트 토큰 절약
PASSAGE_LIMIT = 3_000   # 프롬프트에 들어가는 지문 최대 길이 (모든 지문이 이 범위로 잘림)


# ── 결과 타입 ─────────────────────────────────────────────────────────────────

@dataclass
class GradeResult:
    score:               int    # 0 | 1 | 2
    feedback:            str    # 아이에게 보여줄 피드백 (영어)
    needs_parent_review: bool
    provider:            str    # "ollama" | "gemini" | "error"


# ── 프롬프트 ──────────────────────────────────────────────────────────────────

_GRADE_PROMPT = """\
You are a kind and thoughtful reading tutor for a 9-year-old native English speaker.
Grade the student's answer to a reading comprehension question.

━━ PASSAGE (may be truncated) ━━
{passage}

━━ QUESTION ({kind}) ━━
{question}

━━ REFERENCE ANSWER (NEVER share this with the student) ━━
{model_answer}

━━ STUDENT'S ANSWER ━━
{user_answer}

━━ SCORING GUIDE ━━
Score 2 — Correct and complete. Clearly supported by the passage.
Score 1 — Partially correct. Right direction but missing key detail or evidence.
Score 0 — Incorrect, off-topic, or shows misunderstanding of the passage.

━━ KIND-SPECIFIC RULES ━━
Literal:     The answer must come directly from the passage. Be strict.
Inferential: Value reasoning that connects ideas, even if wording differs from reference.
             Score 1 if the inference is plausible but lacks textual support.
Evaluative:  Accept any well-reasoned opinion. Score 1 if opinion is stated without
             citing any evidence from the passage. Score 2 requires opinion + evidence.

━━ FEEDBACK RULES ━━
- Write in simple English a 9-year-old can understand.
- Score 2: Confirm what they got right (1–2 sentences). Be enthusiastic!
- Score 1: Acknowledge what's right, then ask ONE guiding question to help find what's missing.
- Score 0: Give a gentle hint about where in the passage to look, then ask ONE guiding question.
- NEVER reveal the reference answer directly.
- Keep feedback under 60 words.
- Do not start with "I" as the first word.

━━ NEEDS_PARENT_REVIEW ━━
Set true if:
  - Score is 1 on an Evaluative question (nuanced judgment needed)
  - The student's answer seems confused, emotional, or off-task
Otherwise false.

━━ OUTPUT ━━
Return ONLY valid JSON, no markdown fences, no extra text:
{{"score": 0, "feedback": "...", "needs_parent_review": false}}
"""


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _build_prompt(
    question: str,
    kind: str,
    model_answer: str,
    passage: str,
    user_answer: str,
) -> str:
    truncated = passage[:PASSAGE_LIMIT]
    if len(passage) > PASSAGE_LIMIT:
        truncated += "\n[… passage continues …]"
    return _GRADE_PROMPT.format(
        passage=truncated,
        kind=kind,
        question=question,
        model_answer=model_answer or "(no reference answer provided)",
        user_answer=user_answer,
    )


def _parse_result(raw: str) -> dict | None:
    """JSON 파싱. 마크다운 펜스 있어도 허용."""
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
    # 첫 번째 { ... } 블록 추출
    m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
    except json.JSONDecodeError:
        return None

    score = data.get("score")
    feedback = data.get("feedback", "").strip()
    if score not in (0, 1, 2) or not feedback:
        return None
    return {
        "score":               int(score),
        "feedback":            feedback,
        "needs_parent_review": bool(data.get("needs_parent_review", False)),
    }


# ── 공개 API ──────────────────────────────────────────────────────────────────

# @tag ACADEMY @tag AI
async def grade_answer(
    question_text: str,
    kind: str,
    model_answer: str,
    passage: str,
    user_answer: str,
) -> GradeResult:
    """CKLA 문제 답변 AI 채점.

    Args:
        question_text: 문제 텍스트
        kind:          "Literal" | "Inferential" | "Evaluative"
        model_answer:  참고 정답 (AI에게만 보여줌)
        passage:       레슨 지문 (full, 내부에서 truncate)
        user_answer:   아이가 입력한 답변

    Returns:
        GradeResult(score, feedback, needs_parent_review, provider)
    """
    if not user_answer or not user_answer.strip():
        return GradeResult(
            score=0,
            feedback="Hmm, it looks like you didn't write an answer yet! "
                     "Give it a try — look back at the passage for clues.",
            needs_parent_review=False,
            provider="local",
        )

    prompt = _build_prompt(question_text, kind, model_answer, passage, user_answer)

    # Ollama 먼저 시도 (지문은 PASSAGE_LIMIT으로 이미 잘림 — 프롬프트 크기 제어됨)
    try:
        raw = await _ollama_chat(prompt, timeout=90.0)
        parsed = _parse_result(raw)
        if parsed:
            log.debug("CKLA grader: Ollama ok (score=%d)", parsed["score"])
            return GradeResult(**parsed, provider="ollama")
        log.info("CKLA grader: Ollama response unparseable — fallback to Gemini")
    except Exception as exc:
        log.warning("CKLA grader: Ollama error (%s) — fallback to Gemini", exc)

    # Gemini 폴백 (또는 긴 지문 직행)
    try:
        raw = await _gemini_generate(prompt, timeout=60.0)
        parsed = _parse_result(raw)
        if parsed:
            log.debug("CKLA grader: Gemini ok (score=%d)", parsed["score"])
            return GradeResult(**parsed, provider="gemini")
        log.error("CKLA grader: Gemini response also unparseable:\n%s", raw[:300])
    except Exception as exc:
        log.error("CKLA grader: Gemini error: %s", exc)

    # 완전 실패 → 인간 리뷰로 전달
    return GradeResult(
        score=0,
        feedback="Great effort! Your teacher will take a look at your answer soon.",
        needs_parent_review=True,
        provider="error",
    )
