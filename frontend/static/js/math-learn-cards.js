/* ================================================================
   math-learn-cards.js — CPA Learn card carousel with TTS
   Section: Math
   Dependencies: core.js, tts-client.js, math-academy.js
   API endpoints: none (data passed from math-academy.js)
   ================================================================ */

/* global mathState, advanceMathStage, renderMathRoadmap */

// ── Learn card state ───────────────────────────────────────
let _learnCards = [];
let _learnIdx = 0;
let _learnKeyHandler = null;

// ── CPA phase colours ──────────────────────────────────────
const CPA_META = {
    concrete:  { label: 'Concrete',  icon: '🧱', cls: 'cpa-concrete'  },
    pictorial: { label: 'Pictorial', icon: '🖼️', cls: 'cpa-pictorial' },
    abstract:  { label: 'Abstract',  icon: '🔢', cls: 'cpa-abstract'  },
};

// ── Render learn card carousel ─────────────────────────────

/**
 * Render the Learn stage: a swipeable card carousel.
 * @tag MATH @tag LEARN
 * @param {Array} cards — learn card objects from lesson JSON
 */
function renderMathLearnCards(cards) {
    _learnCards = cards || [];
    _learnIdx = 0;
    _renderCurrentLearnCard();
}

/** @tag MATH @tag LEARN */
function _renderCurrentLearnCard() {
    const stage = document.getElementById('stage');
    if (!stage) return;

    if (_learnIdx >= _learnCards.length) {
        // All cards done — detach any lingering keyboard handler and advance.
        if (_learnKeyHandler) {
            document.removeEventListener('keydown', _learnKeyHandler);
            _learnKeyHandler = null;
        }
        advanceMathStage();
        return;
    }

    const card = _learnCards[_learnIdx];
    const cpa = CPA_META[card.cpa_phase] || CPA_META.abstract;
    const total = _learnCards.length;
    const num = _learnIdx + 1;

    // Update roadmap progress
    mathState.currentIdx = _learnIdx;
    mathState.problems = _learnCards; // so roadmap shows correct count
    renderMathRoadmap();

    stage.innerHTML = `
        <div class="math-learn-wrap">
            <div class="math-learn-header">
                <span class="math-learn-counter">${num} / ${total}</span>
                <span class="math-learn-cpa ${cpa.cls}">${cpa.icon} ${cpa.label}</span>
            </div>

            <div class="math-learn-card ${cpa.cls}">
                <h2 class="math-learn-title">${_esc(card.title || '')}</h2>
                <div class="math-learn-content">${_esc(card.content || '')}</div>
                ${_renderLearnVisual(card.visual)}
                ${card.interaction === 'quiz_mini' ? _renderMiniQuiz(card) : ''}
            </div>

            <div class="math-learn-actions">
                <button class="math-btn-secondary" id="math-learn-tts" title="Listen">
                    🔊 Listen
                </button>
                <div class="math-learn-nav">
                    <button class="math-btn-ghost" id="math-learn-prev" ${_learnIdx === 0 ? 'disabled' : ''}>
                        ← Back
                    </button>
                    <button class="math-btn-primary" id="math-learn-next">
                        ${num === total ? 'Done ✓' : 'Next →'}
                    </button>
                </div>
            </div>

            <div class="math-learn-dots">
                ${_learnCards.map((_, i) => `<span class="math-dot ${i === _learnIdx ? 'active' : i < _learnIdx ? 'done' : ''}"></span>`).join('')}
            </div>
        </div>
    `;

    // Wire buttons
    document.getElementById('math-learn-tts').addEventListener('click', () => _playLearnTTS(card));
    document.getElementById('math-learn-next').addEventListener('click', () => {
        _learnIdx++;
        _renderCurrentLearnCard();
    });
    const prevBtn = document.getElementById('math-learn-prev');
    if (prevBtn && !prevBtn.disabled) {
        prevBtn.addEventListener('click', () => {
            _learnIdx--;
            _renderCurrentLearnCard();
        });
    }

    // Keyboard nav — always detach the prior handler before attaching a new
    // one so mouse-driven re-renders don't accumulate listeners on document.
    if (_learnKeyHandler) {
        document.removeEventListener('keydown', _learnKeyHandler);
    }
    _learnKeyHandler = (e) => {
        if (e.key === 'ArrowRight' || e.key === 'Enter') {
            document.removeEventListener('keydown', _learnKeyHandler);
            _learnKeyHandler = null;
            _learnIdx++;
            _renderCurrentLearnCard();
        } else if (e.key === 'ArrowLeft' && _learnIdx > 0) {
            document.removeEventListener('keydown', _learnKeyHandler);
            _learnKeyHandler = null;
            _learnIdx--;
            _renderCurrentLearnCard();
        }
    };
    document.addEventListener('keydown', _learnKeyHandler);

    // Hydrate manipulative widget if needed
    if (card.visual && typeof card.visual === 'object' && card.visual.tool) {
        const slot = document.getElementById('math-learn-manip');
        if (slot && typeof renderManipulative === 'function') {
            renderManipulative(slot, card.visual);
        }
    }

    // Auto-play TTS on card load
    setTimeout(() => _playLearnTTS(card), 400);
}

// ── Visual block renderer (string or manipulative) ────────
/** @tag MATH @tag LEARN @tag MANIPULATIVE */
function _renderLearnVisual(visual) {
    if (!visual) return '';
    if (typeof visual === 'string') {
        return `<div class="math-learn-visual">${_esc(visual)}</div>`;
    }
    if (typeof visual === 'object' && visual.tool) {
        // Slot to be hydrated post-render
        return `<div class="math-learn-manip" id="math-learn-manip"></div>`;
    }
    return '';
}

// ── TTS helper ─────────────────────────────────────────────

/** @tag MATH @tag LEARN @tag TTS */
async function _playLearnTTS(card) {
    const text = card.tts || card.content || '';
    if (!text) return;

    const btn = document.getElementById('math-learn-tts');
    if (btn) { btn.disabled = true; btn.textContent = '🔊 ...'; }

    try {
        if (typeof playTTS === 'function') {
            await playTTS(text);
        } else {
            const res = await fetch('/api/tts/speak', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, voice: 'en-US-AriaNeural' }),
            });
            if (res.ok) {
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const audio = new Audio(url);
                audio.play();
                audio.onended = () => URL.revokeObjectURL(url);
            }
        }
    } catch (err) {
        console.warn('[math] TTS failed:', err);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = '🔊 Listen'; }
    }
}

// ── Mini quiz (for interactive cards) ──────────────────────

/** @tag MATH @tag LEARN */
function _renderMiniQuiz(card) {
    // Placeholder for interactive quiz_mini cards — Phase M5 will add full interaction
    return `
        <div class="math-learn-mini-quiz">
            <p class="math-mini-label">💡 Think about it, then tap Next to continue.</p>
        </div>
    `;
}

// ── Escape helper ──────────────────────────────────────────
function _esc(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
