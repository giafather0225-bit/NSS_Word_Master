/* ================================================================
   math-review.js — My Problems (Wrong Review) UI
   Section: Math
   Dependencies: core.js, math-problem-ui.js (_renderMC/_renderTF/_renderInput/_renderDragSort)
   API endpoints: /api/math/my-problems/summary,
                  /api/math/my-problems/review,
                  /api/math/my-problems/submit-answer
   ================================================================ */

/* global _renderMC, _renderTF, _renderInput, _renderDragSort */

// ── State ──────────────────────────────────────────────────

const mathReviewState = {
    items: [],
    idx: 0,
    correct: 0,
    wrong: 0,
    mastered: 0,
    advanced: 0,
};

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag MY_PROBLEMS */
async function startMathReview() {
    // Show stage card same way lessons do
    const stageCard = document.getElementById('stage-card');
    const idleWrap = document.getElementById('idle-wrapper');
    const homeDash = document.getElementById('home-dashboard');
    const topBar = document.querySelector('.top-bar');
    if (homeDash) homeDash.style.display = 'none';
    if (idleWrap) idleWrap.style.display = 'none';
    if (stageCard) { stageCard.classList.remove('hidden'); stageCard.style.display = ''; }
    if (topBar) topBar.style.display = '';

    const sidebar = document.getElementById('sidebar');
    if (sidebar) { sidebar.classList.add('collapsed'); localStorage.setItem('sb_collapsed', '1'); }

    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-wrong-review"><p>Loading your review problems…</p></div>`;

    try {
        const res = await fetch('/api/math/my-problems/review');
        const data = await res.json();
        mathReviewState.items = data.items || [];
        mathReviewState.idx = 0;
        mathReviewState.correct = 0;
        mathReviewState.wrong = 0;
        mathReviewState.mastered = 0;
        mathReviewState.advanced = 0;

        if (mathReviewState.items.length === 0) {
            _renderReviewEmpty();
            return;
        }
        _renderReviewProblem();
    } catch (err) {
        console.warn('[math-review] load failed', err);
        stage.innerHTML = `<div class="math-wrong-review"><p>Could not load review. Try again later.</p></div>`;
    }
}

// ── Empty state ────────────────────────────────────────────

/** @tag MATH @tag MY_PROBLEMS */
function _renderReviewEmpty() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `
        <div class="math-wrong-review">
            <div class="math-feedback-icon">🎉</div>
            <h2>All caught up!</h2>
            <p>No problems due for review today.</p>
            <p class="math-wrong-list">New wrong answers get scheduled automatically after each lesson.</p>
        </div>
    `;
}

// ── Problem renderer (reuse problem-ui renderers) ─────────

/** @tag MATH @tag MY_PROBLEMS */
function _renderReviewProblem() {
    const stage = document.getElementById('stage');
    if (!stage) return;

    const items = mathReviewState.items;
    const idx = mathReviewState.idx;
    if (idx >= items.length) {
        _renderReviewSummary();
        return;
    }

    const item = items[idx];
    const p = item.problem;
    const total = items.length;

    stage.innerHTML = `
        <div class="math-problem-wrap">
            <div class="math-problem-header">
                <span class="math-problem-stage">🔁 Review</span>
                <span class="math-problem-counter">${idx + 1} / ${total}</span>
            </div>
            <div class="math-problem-card">
                <div class="math-review-origin">
                    ${_mathEsc(item.grade)} · ${_mathEsc((item.unit || '').replace(/_/g, ' '))} · ${_mathEsc((item.lesson || '').replace(/_/g, ' '))}
                </div>
                <div class="math-problem-question">${_mathEsc(p.question)}</div>
                <div class="math-problem-body" id="math-problem-body"></div>
            </div>
        </div>
    `;

    const body = document.getElementById('math-problem-body');
    const onSubmit = async function (_problem, answer) {
        const bodyEl = document.getElementById('math-problem-body');
        if (bodyEl) bodyEl.querySelectorAll('button, input').forEach(el => { el.disabled = true; });
        await _submitReviewAnswer(item, answer);
    };

    switch (p.type) {
        case 'mc':        _renderMC(body, p, onSubmit); break;
        case 'tf':        _renderTF(body, p, onSubmit); break;
        case 'drag_sort': _renderDragSort(body, p, onSubmit); break;
        case 'input':
        default:          _renderInput(body, p, onSubmit); break;
    }
}

// ── Submit + feedback ──────────────────────────────────────

/** @tag MATH @tag MY_PROBLEMS */
async function _submitReviewAnswer(item, userAnswer) {
    try {
        const res = await fetch('/api/math/my-problems/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ review_id: item.review_id, user_answer: String(userAnswer) }),
        });
        const data = await res.json();

        if (data.is_correct) mathReviewState.correct += 1;
        else mathReviewState.wrong += 1;
        if (data.is_mastered) mathReviewState.mastered += 1;
        else if (!data.is_correct) mathReviewState.advanced += 1;

        _showReviewFeedback(data, () => {
            mathReviewState.idx += 1;
            _renderReviewProblem();
        });
    } catch (err) {
        console.warn('[math-review] submit failed', err);
        mathReviewState.idx += 1;
        _renderReviewProblem();
    }
}

/** @tag MATH @tag MY_PROBLEMS */
function _showReviewFeedback(data, onContinue) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const klass = data.is_correct ? 'math-feedback-correct' : 'math-feedback-wrong';
    const label = data.is_correct
        ? (data.is_mastered ? '✓ Mastered!' : '✓ Correct')
        : '❌ Try again next time';
    const sub = data.is_correct
        ? (data.is_mastered ? 'Removed from review list.' : 'Nice — keep it up.')
        : `Answer: ${_mathEsc(data.correct_answer || '')}`;

    const overlay = document.createElement('div');
    overlay.className = `math-feedback-overlay ${klass}`;
    overlay.innerHTML = `
        <div class="math-feedback-card">
            <div class="math-feedback-result">${label}</div>
            <div class="math-feedback-answer">${sub}</div>
            ${data.feedback ? `<div class="math-feedback-text">${_mathEsc(data.feedback)}</div>` : ''}
            <button class="math-btn-primary" id="math-review-continue">Continue</button>
        </div>
    `;
    stage.appendChild(overlay);
    document.getElementById('math-review-continue').addEventListener('click', () => {
        overlay.remove();
        onContinue();
    });
}

// ── Summary ────────────────────────────────────────────────

/** @tag MATH @tag MY_PROBLEMS */
function _renderReviewSummary() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const total = mathReviewState.items.length;
    const correct = mathReviewState.correct;
    const pct = total ? Math.round((correct / total) * 100) : 0;
    stage.innerHTML = `
        <div class="math-round-summary">
            <div class="math-summary-icon">🎯</div>
            <h2 class="math-summary-title">Review Complete</h2>
            <div class="math-summary-score">${correct} / ${total}</div>
            <div class="math-summary-pct">${pct}% correct today</div>
            <div class="math-summary-bar">
                <div class="math-summary-bar-fill ${pct >= 70 ? 'pass' : 'fail'}" style="width:${pct}%"></div>
            </div>
            <div class="math-summary-weak">
                <div class="math-summary-weak-label">Result</div>
                <div class="math-summary-weak-list">
                    <span class="math-summary-chip">✓ Mastered: ${mathReviewState.mastered}</span>
                    <span class="math-summary-chip">🔁 Scheduled again: ${mathReviewState.advanced}</span>
                </div>
            </div>
            <button class="math-btn-primary math-summary-cta" id="math-review-done">Back</button>
        </div>
    `;
    document.getElementById('math-review-done').addEventListener('click', () => {
        // Go back to math sidebar view; reload counts
        if (typeof loadMathSidebarStatus === 'function') loadMathSidebarStatus();
        if (typeof switchView === 'function') switchView('math');
        const stageCard = document.getElementById('stage-card');
        if (stageCard) stageCard.style.display = 'none';
        const idleWrap = document.getElementById('idle-wrapper');
        if (idleWrap) idleWrap.style.display = '';
    });
}

// ── Wiring ─────────────────────────────────────────────────

/** @tag MATH @tag MY_PROBLEMS */
(function wireMathReviewBtn() {
    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('math-btn-review');
        if (btn) {
            btn.addEventListener('click', () => startMathReview());
        }
    });
})();

// ── Escape helper ──────────────────────────────────────────

function _mathEsc(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
}
