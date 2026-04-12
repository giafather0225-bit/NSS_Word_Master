"""AI 서비스 테스트 — 품질 점수, 라우팅, Gemini 폴백."""
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from backend.ai_service import (
    quality_score,
    refine_ocr_text,
    enrich_words,
    generate_example,
    smart_refine,
    QUALITY_THRESHOLD,
)
from tests.conftest import MOCK_VOCAB_JSON, MOCK_POOR_JSON


# ── quality_score ────────────────────────────────────────────────

class TestQualityScore:
    def test_empty_returns_zero(self):
        assert quality_score([]) == 0.0

    def test_perfect_entries(self):
        entries = [
            {"word": "abundant", "pos": "adj.",
             "definition": "existing in large quantities",
             "example": "The forest has abundant wildlife."},
        ]
        score = quality_score(entries)
        assert score >= 0.9, f"Expected ≥0.9, got {score:.2f}"

    def test_missing_definition_scores_zero(self):
        entries = [{"word": "test", "pos": "n.", "definition": "", "example": ""}]
        assert quality_score(entries) == 0.0

    def test_short_definition_scores_low(self):
        entries = [{"word": "run", "pos": "v.", "definition": "go", "example": ""}]
        assert quality_score(entries) < QUALITY_THRESHOLD

    def test_definition_repeats_word_scores_low(self):
        entries = [
            {"word": "abundant", "pos": "adj.",
             "definition": "abundant means a lot", "example": ""}
        ]
        score = quality_score(entries)
        assert score < 0.6

    def test_example_with_word_boosts_score(self):
        with_word = [
            {"word": "swift", "pos": "adj.",
             "definition": "moving with great speed",
             "example": "The swift bird flew away."}
        ]
        without_word = [
            {"word": "swift", "pos": "adj.",
             "definition": "moving with great speed",
             "example": "It flew away quickly."}
        ]
        assert quality_score(with_word) > quality_score(without_word)

    def test_mixed_entries_averaged(self):
        entries = [
            {"word": "brave", "pos": "adj.",
             "definition": "showing courage", "example": "The brave soldier fought hard."},
            {"word": "x", "pos": "", "definition": "", "example": ""},
        ]
        score = quality_score(entries)
        assert 0.0 < score < 1.0


# ── refine_ocr_text ──────────────────────────────────────────────

@pytest.mark.asyncio
class TestRefineOcrText:

    async def test_uses_ollama_when_quality_good(self):
        """Ollama 결과가 품질 기준 통과 → Gemini 미호출."""
        with patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama, \
             patch("backend.ai_service._gemini_generate", new_callable=AsyncMock) as mock_gemini:

            mock_ollama.return_value = MOCK_VOCAB_JSON

            entries, provider = await refine_ocr_text("some ocr text with vocabulary words")

            assert provider == "ollama"
            assert len(entries) >= 1
            mock_gemini.assert_not_called()

    async def test_falls_back_to_gemini_on_poor_ollama_quality(self):
        """Ollama 품질 미달 → Gemini 호출."""
        with patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama, \
             patch("backend.ai_service._gemini_generate", new_callable=AsyncMock) as mock_gemini:

            mock_ollama.return_value  = MOCK_POOR_JSON
            mock_gemini.return_value  = MOCK_VOCAB_JSON

            entries, provider = await refine_ocr_text("text")

            assert provider == "gemini"
            assert len(entries) >= 1
            mock_gemini.assert_called_once()

    async def test_falls_back_to_gemini_on_ollama_error(self):
        """Ollama 오류 → Gemini 폴백."""
        with patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama, \
             patch("backend.ai_service._gemini_generate", new_callable=AsyncMock) as mock_gemini:

            mock_ollama.side_effect  = ConnectionError("Ollama offline")
            mock_gemini.return_value = MOCK_VOCAB_JSON

            entries, provider = await refine_ocr_text("text")

            assert provider == "gemini"
            mock_gemini.assert_called_once()

    async def test_force_gemini_skips_ollama(self):
        """force_gemini=True → Ollama 미호출."""
        with patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama, \
             patch("backend.ai_service._gemini_generate", new_callable=AsyncMock) as mock_gemini:

            mock_gemini.return_value = MOCK_VOCAB_JSON

            entries, provider = await refine_ocr_text("text", force_gemini=True)

            assert provider == "gemini"
            mock_ollama.assert_not_called()

    async def test_long_text_skips_ollama(self):
        """긴 텍스트(>LONG_TEXT_THRESHOLD) → Ollama 미호출."""
        from backend.ai_service import LONG_TEXT_THRESHOLD
        long_text = "word definition example. " * (LONG_TEXT_THRESHOLD // 20 + 10)

        with patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama, \
             patch("backend.ai_service._gemini_generate", new_callable=AsyncMock) as mock_gemini:

            mock_gemini.return_value = MOCK_VOCAB_JSON
            entries, provider = await refine_ocr_text(long_text)

            assert provider == "gemini"
            mock_ollama.assert_not_called()

    async def test_returns_normalized_entries(self):
        """반환된 항목은 word/pos/definition/example 키를 가져야 함."""
        with patch("backend.ai_service._ollama_chat", return_value=MOCK_VOCAB_JSON):
            entries, _ = await refine_ocr_text("text")
            for e in entries:
                assert "word" in e
                assert "definition" in e
                assert "example" in e
                assert "pos" in e


# ── generate_example ─────────────────────────────────────────────

@pytest.mark.asyncio
class TestGenerateExample:

    async def test_ollama_example_contains_word(self):
        with patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "The abundant harvest fed the village."
            sentence, provider = await generate_example("abundant", "existing in large quantities")
            assert provider == "ollama"
            assert "abundant" in sentence.lower()

    async def test_falls_back_to_gemini_when_word_missing(self):
        """Ollama 예문에 단어 미포함 → Gemini."""
        with patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama, \
             patch("backend.ai_service._gemini_generate", new_callable=AsyncMock) as mock_gemini:

            mock_ollama.return_value  = "It was very nice."   # 'abundant' 없음
            mock_gemini.return_value  = "There is abundant food at the feast."

            sentence, provider = await generate_example("abundant", "existing in large quantities")
            assert provider == "gemini"

    async def test_force_gemini(self):
        with patch("backend.ai_service._gemini_generate", new_callable=AsyncMock) as mock_gemini, \
             patch("backend.ai_service._ollama_chat", new_callable=AsyncMock) as mock_ollama:

            mock_gemini.return_value = "The abundant crops filled the barn."
            sentence, provider = await generate_example(
                "abundant", "existing in large quantities", force_gemini=True
            )
            assert provider == "gemini"
            mock_ollama.assert_not_called()


# ── smart_refine ─────────────────────────────────────────────────

@pytest.mark.asyncio
class TestSmartRefine:

    async def test_returns_complete_result(self):
        with patch("backend.ai_service._ollama_chat", return_value=MOCK_VOCAB_JSON):
            result = await smart_refine("vocabulary text")
            assert "entries"   in result
            assert "providers" in result
            assert "quality"   in result
            assert len(result["entries"]) >= 1
            assert 0.0 <= result["quality"] <= 1.0

    async def test_providers_list_is_populated(self):
        with patch("backend.ai_service._ollama_chat", return_value=MOCK_VOCAB_JSON):
            result = await smart_refine("text")
            assert len(result["providers"]) >= 1
            assert result["providers"][0] in ("ollama", "gemini")
