/* ================================================================
   math-academy-ui.js — Roadmap, round summary, complete/wrong-review UI
   Section: Math
   Dependencies: math-academy.js (mathState, loadMathStage), core.js (switchView)
   API endpoints: none (client-only rendering)
   ================================================================ */

/* global mathState, loadMathStage, MATH_STAGE_LABELS, switchView */

// ── CPA Fallback lookup ─────────────────────────────────────

/**
 * Find a cached Learn card whose concept matches the problem, for Pictorial fallback.
 * @tag MATH @tag CPA_FALLBACK
 */
function _findCpaFallback(problem) {
    if (!mathState.learnCards || mathState.learnCards.length === 0) return null;
    const concept = (problem.concept || '').toLowerCase();
    const pictorialCards = mathState.learnCards.filter(c => c.cpa_phase === 'pictorial');
    const matched = pictorialCards.find(c => concept && (c.content || '').toLowerCase().includes(concept.split(' ')[0]));
    return matched || pictorialCards[0] || null;
}

// ── Early bump prompt (5 consecutive correct in Practice) ──

/** @tag MATH @tag ADAPTIVE */
function _showEarlyBumpPrompt() {
    const stage = document.getElementById('stage');
    if (!stage) return;

    const nextStage = mathState.stage === 'practice_r1' ? 'practice_r2'
                    : mathState.stage === 'practice_r2' ? 'practice_r3'
                    : null;

    const card = document.createElement('div');
    card.className = 'math-feedback-overlay math-feedback-correct';
    card.innerHTML = `
        <div class="math-feedback-card">
            <div class="math-feedback-icon">\u{1F680}</div>
            <div class="math-feedback-result">You're on fire!</div>
            <div class="math-feedback-text">5 correct in a row. ${nextStage ? 'Skip to the next round?' : 'Keep going!'}</div>
            <div class="math-learn-actions" style="margin-top:20px; justify-content:center;">
                ${nextStage ? '<button class="math-btn-primary" id="math-bump-yes">Yes, skip ahead</button>' : ''}
                <button class="math-btn-ghost" id="math-bump-no">${nextStage ? 'Keep practicing' : 'Continue'}</button>
            </div>
        </div>
    `;
    stage.appendChild(card);

    document.getElementById('math-bump-no').addEventListener('click', () => {
        card.remove();
        mathState.consecCorrect = 0;
        mathState.currentIdx++;
        if (mathState.currentIdx >= mathState.problems.length) {
            advanceMathStage();
        } else {
            renderMathProblem();
            renderMathRoadmap();
        }
    });

    const yesBtn = document.getElementById('math-bump-yes');
    if (yesBtn) {
        yesBtn.addEventListener('click', () => {
            card.remove();
            mathState.consecCorrect = 0;
            loadMathStage(nextStage);
        });
    }
}

// ── Roadmap ─────────────────────────────────────────────────

/**
 * Render the math roadmap pills in the top bar.
 * @tag MATH @tag NAVIGATION
 */
function renderMathRoadmap() {
    const rm = document.getElementById('roadmap');
    if (!rm) return;
    rm.innerHTML = '';

    const stagesVisible = ['pretest', 'learn', 'try', 'practice_r1', 'practice_r2', 'practice_r3'];
    const currentIdx = stagesVisible.indexOf(mathState.stage);

    stagesVisible.forEach((s, i) => {
        const div = document.createElement('div');
        div.className = 'road-pill';

        if (i < currentIdx) {
            div.classList.add('done');
            div.textContent = '\u2713 ' + MATH_STAGE_LABELS[s];
        } else if (i === currentIdx) {
            div.classList.add('current');
            const total = mathState.problems.length;
            const progress = total > 0 ? ` (${Math.min(mathState.currentIdx + 1, total)}/${total})` : '';
            div.textContent = MATH_STAGE_LABELS[s] + progress;
        } else {
            div.classList.add('locked');
            div.textContent = MATH_STAGE_LABELS[s];
        }

        rm.appendChild(div);
    });

    const fill = document.getElementById('top-progress-fill');
    const pct = document.getElementById('progress-pct');
    if (fill && mathState.problems.length > 0) {
        const p = Math.round(mathState.currentIdx / mathState.problems.length * 100);
        fill.style.width = p + '%';
        if (pct) pct.textContent = p + '%';
    }
}

// ── Round summary (M4) ─────────────────────────────────────

/**
 * Render a round summary after a Practice round — score, accuracy, weak concepts.
 * @tag MATH @tag ACADEMY @tag ROUND_SUMMARY
 */
function _renderRoundSummary({ stageLabel, correct, total, pct, passed, weakConcepts, onContinue }) {
    const stageEl = document.getElementById('stage');
    if (!stageEl) return;

    const icon = passed ? '\u{1F389}' : '\u{1F4AA}';
    const title = passed ? `${stageLabel} Complete!` : `Almost There!`;
    const weakHtml = weakConcepts.length > 0
        ? `<div class="math-summary-weak">
              <div class="math-summary-weak-label">Focus areas</div>
              <div class="math-summary-weak-list">${weakConcepts.map(c => `<span class="math-summary-chip">${_escS(c)}</span>`).join('')}</div>
           </div>`
        : '';

    stageEl.innerHTML = `
        <div class="math-round-summary">
            <div class="math-summary-icon">${icon}</div>
            <h2 class="math-summary-title">${title}</h2>
            <div class="math-summary-score">${correct} / ${total}</div>
            <div class="math-summary-pct">${pct}% accuracy ${passed ? '\u2022 Passed' : '\u2022 Need 80%'}</div>
            <div class="math-summary-bar">
                <div class="math-summary-bar-fill ${passed ? 'pass' : 'fail'}" style="width:${pct}%"></div>
            </div>
            ${weakHtml}
            <button class="math-btn-primary math-summary-cta" id="math-summary-continue">
                ${passed ? 'Continue \u2192' : 'Try Again'}
            </button>
        </div>
    `;

    document.getElementById('math-summary-continue').addEventListener('click', onContinue);
}

/**
 * Return top-3 most-frequent concepts from an array of wrong concept strings.
 * @tag MATH @tag ROUND_SUMMARY
 */
function _topWeakConcepts(concepts) {
    if (!concepts || concepts.length === 0) return [];
    const counts = {};
    concepts.forEach(c => { counts[c] = (counts[c] || 0) + 1; });
    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([c]) => c);
}

// ── Escape helpers (shared with math-academy-feedback.js) ──

function _escS(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function _escAttrS(s) {
    return String(s == null ? '' : s).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ── Stage feedback (pass/fail) ──────────────────────────────

/**
 * Show pass/fail feedback for a practice stage.
 * @tag MATH @tag ACADEMY
 */
function showMathStageFeedback(passed, pct) {
    const stage = document.getElementById('stage');
    if (!stage) return;

    stage.innerHTML = `
        <div class="math-stage-feedback">
            <div class="math-feedback-icon">${passed ? '\u2713' : '\u2717'}</div>
            <h2>${passed ? 'Stage Passed!' : 'Not Yet \u2014 Let\u2019s Try Again!'}</h2>
            <p>Score: ${pct}% ${passed ? '' : '(Need 80% to pass)'}</p>
            <button class="math-btn-primary" onclick="retryMathStage()">
                ${passed ? 'Continue' : 'Try Again'}
            </button>
        </div>
    `;
}

/** @tag MATH @tag ACADEMY */
function retryMathStage() {
    mathState.wrong = [];
    loadMathStage(mathState.stage);
}

// ── Complete ────────────────────────────────────────────────

/**
 * Render lesson complete screen.
 * @tag MATH @tag ACADEMY
 */
function renderMathComplete() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    renderMathRoadmap();

    stage.innerHTML = `
        <div class="math-complete">
            <div class="math-complete-icon">🎉</div>
            <h2>Lesson Complete!</h2>
            <p>${mathState.lesson.replace(/_/g, ' ')}</p>
            <p class="math-complete-detail">
                Pretest: ${mathState.pretestScore}/5
            </p>
            <button class="math-btn-primary" onclick="exitMathLesson()">Back to Math</button>
        </div>
    `;
}

/** @tag MATH @tag ACADEMY */
function exitMathLesson() {
    const stageCard = document.getElementById('stage-card');
    if (stageCard) stageCard.classList.add('hidden');
    switchView('math');
}

// ── Wrong Review ────────────────────────────────────────────

/**
 * Render wrong review stage (simplified for M3).
 * @tag MATH @tag ACADEMY
 */
function renderMathWrongReview() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    renderMathRoadmap();

    const wrongIds = mathState._allWrong || [];
    if (wrongIds.length === 0) {
        loadMathStage('complete');
        return;
    }

    stage.innerHTML = `
        <div class="math-wrong-review">
            <h2>Wrong Review</h2>
            <p>You got ${wrongIds.length} problem(s) wrong. Review them to continue!</p>
            <p class="math-wrong-list">${wrongIds.join(', ')}</p>
            <button class="math-btn-primary" onclick="loadMathStage('complete')">
                Continue (Phase M5 will add actual review)
            </button>
        </div>
    `;
}
