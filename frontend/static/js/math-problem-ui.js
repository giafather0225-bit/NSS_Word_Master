/* ================================================================
   math-problem-ui.js — Math problem renderers (MC, input, TF)
   Section: Math
   Dependencies: core.js, math-academy.js
   API endpoints: none (uses submitMathAnswer from math-academy.js)
   ================================================================ */

/* global mathState, submitMathAnswer, handleMathAnswerResult, renderMathRoadmap */

/**
 * Normalize a problem object so the renderer sees a canonical shape.
 * Absorbs schema variance across authors:
 *   - choices[] ("A) ..") → options[] (label stripped)
 *   - type: "true_false"/"MC"/etc → "tf"/"mc"/... (lowercase)
 *   - hint → hints[]
 *   - feedback: {correct, incorrect} → feedback_correct / feedback_wrong
 * @tag MATH @tag PROBLEM
 */
function _normalizeProblem(p) {
    if (!p) return p;

    // choices → options 변환 (앞의 "A) " 레이블 제거)
    if (!p.options && p.choices) {
        p.options = p.choices.map(function(c) {
            return typeof c === 'string' ? c.replace(/^[A-Z]\)\s*/, '') : c;
        });
    }

    // type 정규화
    var typeMap = {
        'true_false': 'tf',
        'TRUE_FALSE': 'tf',
        'MC': 'mc',
        'INPUT': 'input',
        'DRAG_SORT': 'drag_sort'
    };
    if (p.type && typeMap[p.type]) {
        p.type = typeMap[p.type];
    }
    if (p.type) p.type = p.type.toLowerCase();

    // hint(단수) → hints(배열)
    if (p.hint && !p.hints) {
        p.hints = [p.hint];
    }

    // feedback 객체를 flat 필드로 분리
    if (p.feedback && typeof p.feedback === 'object' && !Array.isArray(p.feedback)) {
        if (!p.feedback_correct) p.feedback_correct = p.feedback.correct || '';
        if (!p.feedback_wrong) p.feedback_wrong = p.feedback.incorrect || p.feedback.wrong || '';
    }

    return p;
}

/**
 * Render the current problem based on its type.
 * @tag MATH @tag PROBLEM
 */
function renderMathProblem() {
    const stage = document.getElementById('stage');
    if (!stage) return;

    const problems = mathState.problems;
    const idx = mathState.currentIdx;

    if (idx >= problems.length) return;

    const p = _normalizeProblem(problems[idx]);
    const total = problems.length;
    const num = idx + 1;
    const stageLabel = _mathStageLabel(mathState.stage);

    renderMathRoadmap();

    // Hints (Try stage only). Per MATH_SPEC §Pillar 7, delay the hint by
    // ~30s to encourage productive struggle. When the adaptive `forceHints`
    // flag is on (after 3 consecutive wrong), surface it immediately.
    const hintsHtml = (p.hints && p.hints.length > 0 && mathState.stage === 'try')
        ? `<button class="math-btn-ghost math-hint-btn" id="math-hint-btn" disabled>💡 Hint <span class="math-hint-countdown" id="math-hint-countdown">(30s)</span></button>
           <div class="math-hint-box hidden" id="math-hint-box"></div>`
        : '';

    // 3-Read (word problem heuristic — Try & Practice stages)
    const isWord = (typeof isWordProblem === 'function') && isWordProblem(p.question || '');
    const threeReadHtml = (isWord && mathState.stage !== 'pretest')
        ? `<button class="math-btn-ghost math-3read-btn" id="math-3read-btn" type="button">📖 3-Read</button>`
        : '';

    // Tools panel (Try stage only — optional scaffolding)
    const toolsHtml = (mathState.stage === 'try') ? _renderMathToolsPanel() : '';

    stage.innerHTML = `
        <div class="math-problem-wrap">
            <div class="math-problem-header">
                <span class="math-problem-stage">${stageLabel}</span>
                <span class="math-problem-counter">${num} / ${total}</span>
            </div>

            <div class="math-problem-card">
                <div class="math-problem-question">
                    ${_escP(p.question)}
                    ${threeReadHtml}
                </div>
                <div class="math-problem-body" id="math-problem-body"></div>
                ${hintsHtml}
            </div>

            ${toolsHtml}
        </div>
    `;

    if (toolsHtml) _wireMathToolsPanel(p);

    const body = document.getElementById('math-problem-body');

    // Render based on type
    switch (p.type) {
        case 'mc':
            _renderMC(body, p);
            break;
        case 'tf':
            _renderTF(body, p);
            break;
        case 'drag_sort':
            _renderDragSort(body, p);
            break;
        case 'input':
            _renderInput(body, p);
            break;
        default:
            _renderInput(body, p);
            break;
    }

    // Wire hint button
    const hintBtn = document.getElementById('math-hint-btn');
    if (hintBtn && p.hints) {
        let hintIdx = 0;
        const showNextHint = () => {
            const box = document.getElementById('math-hint-box');
            if (!box) return;
            if (hintIdx < p.hints.length) {
                box.classList.remove('hidden');
                box.innerHTML += `<p class="math-hint-item">💡 ${_escP(p.hints[hintIdx])}</p>`;
                hintIdx++;
            }
            if (hintIdx >= p.hints.length) hintBtn.disabled = true;
        };
        hintBtn.addEventListener('click', showNextHint);

        // Productive-struggle gate: unlock the hint after a short delay.
        // Clear any prior countdown so re-renders don't leak intervals.
        const countdownEl = document.getElementById('math-hint-countdown');
        if (window._mathHintTimer) { clearInterval(window._mathHintTimer); window._mathHintTimer = null; }
        const forceNow = (typeof mathState !== 'undefined' && mathState.forceHints);
        if (forceNow) {
            // 3 consecutive wrong → unlock immediately and auto-show first hint.
            hintBtn.disabled = false;
            if (countdownEl) countdownEl.remove();
            showNextHint();
        } else {
            let remaining = 30;
            window._mathHintTimer = setInterval(() => {
                remaining -= 1;
                if (countdownEl) countdownEl.textContent = `(${remaining}s)`;
                if (remaining <= 0) {
                    clearInterval(window._mathHintTimer);
                    window._mathHintTimer = null;
                    hintBtn.disabled = false;
                    if (countdownEl) countdownEl.remove();
                }
            }, 1000);
        }
    }

    // Wire 3-Read button
    const threeBtn = document.getElementById('math-3read-btn');
    if (threeBtn && typeof show3ReadModal === 'function') {
        threeBtn.addEventListener('click', () => {
            show3ReadModal(p.question || '');
        });
    }
}

// ── Drag-sort (M4) ─────────────────────────────────────────

/**
 * Render a drag-and-drop sort problem. Expects:
 *   problem.items: [{id, label}, ...] (shuffled for display)
 *   problem.answer: ordered array of item ids (or labels) representing correct sequence
 * @tag MATH @tag PROBLEM @tag DRAG_SORT
 */
function _renderDragSort(body, problem) {
    const items = (problem.items || []).slice();
    // Ensure shuffled display order
    items.sort(() => Math.random() - 0.5);

    body.innerHTML = `
        <p class="math-drag-hint">Drag items into the correct order (top = first).</p>
        <ul class="math-drag-list" id="math-drag-list">
            ${items.map(it => {
                const id = typeof it === 'string' ? it : it.id;
                const label = typeof it === 'string' ? it : (it.label || it.id);
                return `<li class="math-drag-item" draggable="true" data-id="${_escAttr(id)}">
                          <span class="math-drag-handle">\u2630</span>
                          <span class="math-drag-label">${_escP(label)}</span>
                        </li>`;
            }).join('')}
        </ul>
        <button class="math-btn-primary math-submit-btn" id="math-drag-submit">Submit Order</button>
    `;

    const listEl = document.getElementById('math-drag-list');
    let draggingEl = null;

    listEl.querySelectorAll('.math-drag-item').forEach(el => {
        el.addEventListener('dragstart', (e) => {
            draggingEl = el;
            el.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });
        el.addEventListener('dragend', () => {
            el.classList.remove('dragging');
            draggingEl = null;
        });
    });

    listEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (!draggingEl) return;
        const afterEl = _getDragAfterElement(listEl, e.clientY);
        if (afterEl == null) {
            listEl.appendChild(draggingEl);
        } else {
            listEl.insertBefore(draggingEl, afterEl);
        }
    });

    document.getElementById('math-drag-submit').addEventListener('click', () => {
        const order = Array.from(listEl.querySelectorAll('.math-drag-item')).map(el => el.dataset.id);
        _submitProblemAnswer(problem, order.join('|'));
    });
}

function _getDragAfterElement(container, y) {
    const els = Array.from(container.querySelectorAll('.math-drag-item:not(.dragging)'));
    return els.reduce((closest, el) => {
        const box = el.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset, element: el };
        }
        return closest;
    }, { offset: Number.NEGATIVE_INFINITY }).element || null;
}

// ── Multiple Choice ────────────────────────────────────────

/** @tag MATH @tag PROBLEM @tag MC */
function _renderMC(body, problem) {
    const opts = problem.options || [];
    body.innerHTML = `
        <div class="math-mc-grid">
            ${opts.map((o, i) => `
                <button class="math-mc-btn" data-val="${_escAttr(o)}" data-idx="${i}">
                    <span class="math-mc-letter">${String.fromCharCode(65 + i)}</span>
                    <span class="math-mc-text">${_escP(o)}</span>
                </button>
            `).join('')}
        </div>
    `;

    body.querySelectorAll('.math-mc-btn').forEach(btn => {
        btn.addEventListener('click', () => _submitProblemAnswer(problem, btn.dataset.val));
    });

    // Keyboard shortcuts A-D
    const handler = (e) => {
        const key = e.key.toUpperCase();
        const idx = key.charCodeAt(0) - 65;
        if (idx >= 0 && idx < opts.length) {
            document.removeEventListener('keydown', handler);
            _submitProblemAnswer(problem, opts[idx]);
        }
    };
    document.addEventListener('keydown', handler);
}

// ── True/False ─────────────────────────────────────────────

/** @tag MATH @tag PROBLEM @tag TF */
function _renderTF(body, problem) {
    body.innerHTML = `
        <div class="math-tf-grid">
            <button class="math-tf-btn math-tf-true" data-val="true">
                <span class="math-tf-icon">⭕</span>
                <span>True</span>
            </button>
            <button class="math-tf-btn math-tf-false" data-val="false">
                <span class="math-tf-icon">❌</span>
                <span>False</span>
            </button>
        </div>
    `;

    body.querySelectorAll('.math-tf-btn').forEach(btn => {
        btn.addEventListener('click', () => _submitProblemAnswer(problem, btn.dataset.val));
    });
}

// ── Input (free text) ──────────────────────────────────────

/** @tag MATH @tag PROBLEM @tag INPUT */
function _renderInput(body, problem) {
    body.innerHTML = `
        <div class="math-input-group">
            <input type="text" class="math-input-field" id="math-answer-input"
                   placeholder="Type your answer..." autocomplete="off" inputmode="text">
            <button class="math-btn-primary math-submit-btn" id="math-submit-btn">
                Submit
            </button>
        </div>
    `;

    const input = document.getElementById('math-answer-input');
    const submitBtn = document.getElementById('math-submit-btn');

    submitBtn.addEventListener('click', () => {
        const val = input.value.trim();
        if (!val) { input.focus(); return; }
        _submitProblemAnswer(problem, val);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const val = input.value.trim();
            if (!val) return;
            _submitProblemAnswer(problem, val);
        }
    });

    // Auto-focus
    setTimeout(() => input.focus(), 100);
}

// ── Submit answer ──────────────────────────────────────────

/** @tag MATH @tag PROBLEM */
async function _submitProblemAnswer(problem, answer) {
    // Disable all buttons to prevent double-submit
    const body = document.getElementById('math-problem-body');
    if (body) body.querySelectorAll('button, input').forEach(el => { el.disabled = true; });

    const result = await submitMathAnswer(problem.id, answer);
    handleMathAnswerResult(result, problem);
}

// ── Stage label helper ─────────────────────────────────────

/** @tag MATH @tag PROBLEM */
function _mathStageLabel(stage) {
    const labels = {
        pretest: '📋 Pretest',
        try: '✏️ Try',
        practice_r1: '🏋️ Practice R1',
        practice_r2: '🏋️ Practice R2',
        practice_r3: '🏋️ Practice R3',
    };
    return labels[stage] || stage;
}

// ── Try-stage Tools panel (optional manipulatives) ────────

const _MATH_TOOL_DEFS = [
    { tool: 'number_line',   label: '📏 Number Line',  defaults: { min: 0, max: 20, step: 1 } },
    { tool: 'base10_blocks', label: '🧱 Base-10',      defaults: { start: 0, max: 999 } },
    { tool: 'fraction_bar',  label: '🧩 Fraction Bar', defaults: { denominator: 4, numerator: 1 } },
    { tool: 'array_grid',    label: '▦ Array',         defaults: { rows: 3, cols: 4 } },
    { tool: 'bar_model',     label: '▭ Bar Model',     defaults: { parts: [{ label: 'Part 1', value: 0 }, { label: 'Part 2', value: 0 }] } },
];

/** @tag MATH @tag PROBLEM @tag MANIPULATIVE */
function _renderMathToolsPanel() {
    const btns = _MATH_TOOL_DEFS
        .map(t => `<button class="math-btn-ghost math-tool-btn" data-tool="${t.tool}" type="button">${t.label}</button>`)
        .join('');
    return `
        <details class="math-tools-panel" id="math-tools-panel">
            <summary class="math-tools-summary">🧰 Tools <span class="math-tools-hint">— optional</span></summary>
            <div class="math-tools-buttons">${btns}</div>
            <div class="math-tools-slot" id="math-tools-slot"></div>
        </details>
    `;
}

/** @tag MATH @tag PROBLEM @tag MANIPULATIVE */
function _wireMathToolsPanel(problem) {
    const panel = document.getElementById('math-tools-panel');
    const slot = document.getElementById('math-tools-slot');
    if (!panel || !slot) return;

    // Problem-supplied tool configs (optional): p.tools = { number_line: {...}, ... }
    const overrides = (problem && typeof problem.tools === 'object') ? problem.tools : {};

    panel.querySelectorAll('.math-tool-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tool = btn.dataset.tool;
            const def = _MATH_TOOL_DEFS.find(t => t.tool === tool);
            if (!def) return;
            const cfg = Object.assign({}, def.defaults, overrides[tool] || {});
            slot.innerHTML = '';
            if (typeof renderManipulative === 'function') {
                renderManipulative(slot, { tool, config: cfg });
            }
            panel.querySelectorAll('.math-tool-btn').forEach(b => b.classList.toggle('active', b === btn));
        });
    });
}

// ── Escape helpers ─────────────────────────────────────────

function _escP(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function _escAttr(str) {
    return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
