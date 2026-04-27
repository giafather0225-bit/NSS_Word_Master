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
    concrete:  { label: 'Concrete',  icon: 'blocks', cls: 'cpa-concrete'  },
    pictorial: { label: 'Pictorial', icon: 'image',  cls: 'cpa-pictorial' },
    abstract:  { label: 'Abstract',  icon: 'hash',   cls: 'cpa-abstract'  },
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
                <span class="math-learn-cpa ${cpa.cls}"><i data-lucide="${cpa.icon}" style="width:13px;height:13px;vertical-align:-2px;stroke-width:1.5"></i> ${cpa.label}</span>
            </div>

            <div class="math-learn-card ${cpa.cls}">
                <h2 class="math-learn-title">${_mathEsc(card.title || '')}</h2>
                <div class="math-learn-content">${_formatLearnContent(card.content || '')}</div>
                ${_renderLearnVisual(card)}
                ${card.interaction === 'quiz_mini' ? _renderMiniQuiz(card) : ''}
            </div>

            <div class="math-learn-actions">
                <button class="math-btn-secondary" id="math-learn-tts" title="Listen">
                    <i data-lucide="volume-2" style="width:15px;height:15px;vertical-align:-3px;stroke-width:1.5"></i> Listen
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

    // KaTeX: render any math in title/content/mini-quiz
    if (typeof window.mathRenderIn === 'function') {
        const cardEl = stage.querySelector('.math-learn-card');
        if (cardEl) window.mathRenderIn(cardEl);
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();

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

    // Hydrate visual widget based on visual_type
    const vtype = card.visual_type;
    const vdata = card.visual_data || {};
    if (vtype && vtype !== 'none') {
        const slot = document.getElementById('math-learn-manip');
        if (slot) {
            if (vtype === 'manipulative' && typeof renderManipulative === 'function') {
                renderManipulative(slot, vdata);
            } else if (vtype === 'addition_table' && typeof _renderAdditionTable === 'function') {
                _renderAdditionTable(slot, vdata);
            } else if (vtype === 'bar_model' && Array.isArray(vdata.parts) && vdata.parts.length
                       && typeof renderManipulative === 'function') {
                renderManipulative(slot, { tool: 'bar_model', config: vdata });
            }
            // svg/png <img> and other static types render inline via _renderLearnVisual
        }
    }

    // Auto-play TTS on card load
    setTimeout(() => _playLearnTTS(card), 400);
}

// ── Visual block renderer ─────────────────────────────────
/** @tag MATH @tag LEARN @tag VISUAL */
function _renderLearnVisual(card) {
    if (!card) return '';
    const vtype = card.visual_type;
    const vdata = card.visual_data || {};
    if (!vtype || vtype === 'none') return '';
    if (vtype === 'svg' || vtype === 'png') {
        const src = vdata.src || vdata.url || '';
        const alt = vdata.alt || card.title || '';
        if (!src) return '';
        return `<div class="math-learn-visual"><img src="${_mathEsc(src)}" alt="${_mathEsc(alt)}" /></div>`;
    }
    if (vtype === 'manipulative' || vtype === 'addition_table') {
        // Slot hydrated post-render
        return `<div class="math-learn-manip" id="math-learn-manip"></div>`;
    }
    // Delegate static visuals (equation, step_by_step, etc.) to math-learn-visuals.js
    if (typeof renderLearnStaticVisual === 'function') {
        const html = renderLearnStaticVisual(vtype, vdata, card);
        if (html) return html;
    }
    // Last-resort text fallback
    if (typeof vdata.description === 'string') {
        return `<div class="math-learn-visual">${_mathEsc(vdata.description)}</div>`;
    }
    return '';
}

// ── TTS helper ─────────────────────────────────────────────

/** @tag MATH @tag LEARN @tag TTS */
async function _playLearnTTS(card) {
    const text = card.tts || card.content || '';
    if (!text) return;

    const btn = document.getElementById('math-learn-tts');
    if (btn) { btn.disabled = true; btn.textContent = '...'; }

    try {
        const res = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audio.onended = () => URL.revokeObjectURL(url);
            audio.onerror = () => URL.revokeObjectURL(url);
            await audio.play().catch(() => URL.revokeObjectURL(url));
        }
    } catch (err) {
        console.warn('[math] TTS failed:', err);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="volume-2" style="width:15px;height:15px;vertical-align:-3px;stroke-width:1.5"></i> Listen'; if (typeof lucide !== "undefined") lucide.createIcons(); }
    }
}

// ── Mini quiz (for interactive cards) ──────────────────────

/** @tag MATH @tag LEARN */
function _renderMiniQuiz(card) {
    // Placeholder for interactive quiz_mini cards — Phase M5 will add full interaction
    return `
        <div class="math-learn-mini-quiz">
            <p class="math-mini-label">Think about it, then tap Next to continue.</p>
        </div>
    `;
}

// escape → _mathEsc / _mathEscAttr (math-katex-utils.js)

/**
 * Format Learn-card body: escape first, then decorate math expressions,
 * keywords, step numbers, and inline headers. Safe because all decoration
 * uses literal strings / regex captures over already-escaped text.
 * @tag MATH @tag LEARN
 */
function _formatLearnContent(text) {
    if (!text) return '';
    var safe = _mathEsc(text);
    return safe
        .replace(/(For example:|Example:|Remember:|Rule:|Tip:)/gi, '<strong class="math-learn-highlight">$1</strong>')
        .replace(/(\d+\s*[\+\-\×\÷\*\/]\s*\d+\s*=\s*\d+)/g, '<code class="math-expr">$1</code>')
        .replace(/(\d+\s*[\+\-\×\÷\*\/]\s*\d+)/g, '<code class="math-expr">$1</code>')
        .replace(/\((\d+)\)\s/g, '<span class="math-learn-step-num">$1</span> ')
        .replace(/(Commutative Property of Addition|Commutative Property|Identity Property of Addition|Identity Property|even \+ even|odd \+ odd|even \+ odd|odd \+ even|addition table|pattern|sum|addend|doubles)/gi, '<strong class="math-keyword">$1</strong>')
        .replace(/\. /g, '.<br>');
}
