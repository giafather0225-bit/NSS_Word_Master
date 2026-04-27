/* ================================================================
   math-problem-types.js — Per-type problem body renderers
   Section: Math
   Dependencies: core.js, math-katex-utils.js (_mathEsc, _mathEscAttr), math-problem-ui.js (_submitProblemAnswer)
   API endpoints: none
   Dispatcher: math-problem-ui.js (renderMathProblem)

   Renderers in this file:
     _renderMC        — multiple choice grid + A–D keyboard shortcut
     _renderTF        — True / False buttons
     _renderInput     — free-text input + Enter-to-submit
     _renderDragSort  — drag-and-drop ordering (M4 schema)
   ================================================================ */

/* global _submitProblemAnswer, _mathEsc, _mathEscAttr */

// ── Drag-sort (M4) ─────────────────────────────────────────

/**
 * Render a drag-and-drop sort problem. Expects:
 *   problem.items: [{id, label}, ...] (shuffled for display)
 *   problem.answer: ordered array of item ids (or labels) representing correct sequence
 * @tag MATH @tag PROBLEM @tag DRAG_SORT
 */
function _renderDragSort(body, problem, onSubmit) {
    const _doSubmit = onSubmit || _submitProblemAnswer;
    const items = (problem.items || []).slice();
    // Ensure shuffled display order
    items.sort(() => Math.random() - 0.5);

    body.innerHTML = `
        <p class="math-drag-hint">Drag items into the correct order (top = first).</p>
        <ul class="math-drag-list" id="math-drag-list">
            ${items.map(it => {
                const id = typeof it === 'string' ? it : it.id;
                const label = typeof it === 'string' ? it : (it.label || it.id);
                return `<li class="math-drag-item" draggable="true" data-id="${_mathEscAttr(id)}">
                          <span class="math-drag-handle">\u2630</span>
                          <span class="math-drag-label">${_mathEsc(label)}</span>
                        </li>`;
            }).join('')}
        </ul>
        <button class="math-btn-primary math-submit-btn" id="math-drag-submit">Submit Order</button>
    `;

    const listEl = document.getElementById('math-drag-list');
    if (typeof window.mathRenderIn === 'function') window.mathRenderIn(listEl);
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
        _doSubmit(problem, order.join('|'));
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
function _renderMC(body, problem, onSubmit) {
    const _doSubmit = onSubmit || _submitProblemAnswer;
    const opts = problem.options || [];
    body.innerHTML = `
        <div class="math-mc-grid">
            ${opts.map((o, i) => `
                <button class="math-mc-btn" data-val="${_mathEscAttr(o)}" data-idx="${i}">
                    ${_mathEsc(o)}
                </button>
            `).join('')}
        </div>
    `;

    body.querySelectorAll('.math-mc-btn').forEach(btn => {
        btn.addEventListener('click', () => _doSubmit(problem, btn.dataset.val));
    });

    // KaTeX on option labels
    if (typeof window.mathRenderIn === 'function') window.mathRenderIn(body);

    // Keyboard shortcuts A-D
    const handler = (e) => {
        const key = e.key.toUpperCase();
        const idx = key.charCodeAt(0) - 65;
        if (idx >= 0 && idx < opts.length) {
            document.removeEventListener('keydown', handler);
            _doSubmit(problem, opts[idx]);
        }
    };
    document.addEventListener('keydown', handler);
}

// ── True/False ─────────────────────────────────────────────

/** @tag MATH @tag PROBLEM @tag TF */
function _renderTF(body, problem, onSubmit) {
    const _doSubmit = onSubmit || _submitProblemAnswer;
    body.innerHTML = `
        <div class="math-tf-grid">
            <button class="math-tf-btn math-tf-true" data-val="true">True</button>
            <button class="math-tf-btn math-tf-false" data-val="false">False</button>
        </div>
    `;

    body.querySelectorAll('.math-tf-btn').forEach(btn => {
        btn.addEventListener('click', () => _doSubmit(problem, btn.dataset.val));
    });
}

// ── Input (free text) ──────────────────────────────────────

/** @tag MATH @tag PROBLEM @tag INPUT */
function _renderInput(body, problem, onSubmit) {
    const _doSubmit = onSubmit || _submitProblemAnswer;
    let _inputSubmitted = false; // PHASE-0 FIX P3: prevent double submit
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
        if (_inputSubmitted) return; // P3 guard
        const val = input.value.trim();
        if (!val) { input.focus(); return; }
        _inputSubmitted = true; // P3 lock
        _doSubmit(problem, val);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            if (_inputSubmitted) return; // P3 guard
            const val = input.value.trim();
            if (!val) return;
            _inputSubmitted = true; // P3 lock
            _doSubmit(problem, val);
        }
    });

    // Auto-focus
    setTimeout(() => input.focus(), 100);
}
