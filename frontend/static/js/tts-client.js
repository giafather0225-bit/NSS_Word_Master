/* ================================================================
   tts-client.js — Text-to-speech client helpers (fetch → Blob → Audio).
   Section: English / TTS
   Dependencies: core.js
   API endpoints: /api/tts/preview_sequence, /api/tts/word_only,
                  /api/tts/example_full, /api/tutor
   ================================================================ */

// ─── Module-level audio state ─────────────────────────────────
// NOTE: ttsAbort and currentAudio are also used inside openPreviewModal
// as local variables; these module-level ones serve the global helpers.
/** @tag TTS */
let _globalCurrentAudio = null;

/**
 * Preview TTS — fire-and-forget server-side sequence trigger.
 * @tag TTS PREVIEW
 */
async function apiPreviewTTS(item) {
    try {
        await fetch("/api/tts/preview_sequence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word: item.answer, meaning: item.question, example: item.hint }),
        });
    } catch (err) {
        console.warn('[TTS] Preview failed:', err.message || err);
    }
}

// ─── Word-only TTS ────────────────────────────────────────────
/** @tag TTS */
let _wordOnlyInFlight = false;

/**
 * Fetch and play a single-word TTS audio clip.
 * Debounced: ignores concurrent calls while one is in-flight.
 * @tag TTS SPELLING WORD_MATCH
 */
async function apiWordOnly(word) {
    if (_wordOnlyInFlight) return;
    _wordOnlyInFlight = true;
    try {
        const res = await fetch("/api/tts/word_only", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word }),
        });
        if (!res.ok) return;
        const blob = await res.blob();
        if (blob.size === 0) return;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        _globalCurrentAudio = audio;
        await new Promise((resolve, reject) => {
            audio.onended = () => { URL.revokeObjectURL(url); _globalCurrentAudio = null; resolve(); };
            audio.onerror = (e) => { URL.revokeObjectURL(url); _globalCurrentAudio = null; reject(e); };
            audio.play().catch(reject);
        });
    } catch (err) {
        if (err.name !== 'AbortError') console.warn('[TTS] apiWordOnly failed:', err.message || err);
    } finally {
        _wordOnlyInFlight = false;
    }
}

// ─── Example-sentence TTS ─────────────────────────────────────
/** @tag TTS */
let _exampleFullInFlight = false;

/**
 * Fetch and play a full-sentence TTS audio clip.
 * Debounced: ignores concurrent calls while one is in-flight.
 * @tag TTS FILL_BLANK FINAL_TEST SENTENCE
 */
async function apiExampleFull(sentence) {
    if (_exampleFullInFlight) return;
    _exampleFullInFlight = true;
    try {
        const res = await fetch("/api/tts/example_full", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sentence }),
        });
        if (!res.ok) return;
        const blob = await res.blob();
        if (blob.size === 0) return;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        _globalCurrentAudio = audio;
        await new Promise((resolve, reject) => {
            audio.onended = () => { URL.revokeObjectURL(url); _globalCurrentAudio = null; resolve(); };
            audio.onerror = (e) => { URL.revokeObjectURL(url); _globalCurrentAudio = null; reject(e); };
            audio.play().catch(reject);
        });
    } catch (err) {
        console.warn('[TTS] apiExampleFull failed:', err.message || err);
    } finally {
        _exampleFullInFlight = false;
    }
}

/**
 * Ask the AI tutor for sentence feedback (Ollama primary, Gemini fallback).
 * Returns a plain-text feedback string.
 * @tag AI OLLAMA GEMINI SENTENCE
 */
async function apiTutorReply(word, sentence) {
    try {
        const res = await fetch("/api/tutor", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word, sentence }),
        });
        if (!res.ok) throw new Error(`tutor ${res.status}`);
        const d = await res.json();
        return d.feedback || "";
    } catch {
        return `🪄 Great sentence using "${word}"! 💖\n✨ Ollama is sleeping — try again in a moment.`;
    }
}
