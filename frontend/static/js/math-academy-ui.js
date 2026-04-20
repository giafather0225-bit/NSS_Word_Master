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
// renderMathRoadmap() lives in math-academy-shell.js (rail renderer).

// ── Round summary (M4) ─────────────────────────────────────

/**
 * Render a round summary after a Practice round — score, accuracy, weak concepts.
 * @tag MATH @tag ACADEMY @tag ROUND_SUMMARY
 */
function _renderRoundSummary({ stageLabel, correct, total, pct, passed, weakConcepts, onContinue }) {
    const stageEl = document.getElementById('stage');
    if (!stageEl) return;

    const chipLabel = passed ? `\u2713 ${stageLabel} Passed` : `Need 80%`;
    const segments = [];
    for (let i = 0; i < total; i++) {
        segments.push(`<div class="math-summary-segment ${i < correct ? 'correct' : 'wrong'}"></div>`);
    }
    const weakHtml = weakConcepts.length > 0
        ? `<div class="math-summary-weak">
              <div class="math-summary-weak-label">\u{1F4CD} Focus areas</div>
              <div class="math-summary-weak-list">${weakConcepts.map(c => `<div class="math-summary-weak-row"><span>${_escS(c)}</span></div>`).join('')}</div>
           </div>`
        : '';

    stageEl.innerHTML = `
        <div class="math-round-summary">
            <span class="math-summary-chip ${passed ? '' : 'is-fail'}">${chipLabel}</span>
            <div class="math-summary-hero">
                <div class="math-summary-hero-row">
                    <div>
                        <div class="math-summary-label">Accuracy</div>
                        <div class="math-summary-pct ${passed ? '' : 'is-fail'}">${pct}<span class="math-summary-pct-unit">%</span></div>
                    </div>
                    <div style="text-align:right;">
                        <div class="math-summary-label">Score</div>
                        <div class="math-summary-score">${correct}<span class="math-summary-score-total"> / ${total}</span></div>
                    </div>
                </div>
                <div class="math-summary-segments">${segments.join('')}</div>
                <div class="math-summary-meta-row">
                    <span>${stageLabel}</span>
                    <span>${passed ? '\u2022 Passed' : '\u2022 Keep practicing'}</span>
                </div>
            </div>
            ${weakHtml}
            <div class="math-summary-actions">
                <button class="math-btn-primary" id="math-summary-continue">
                    ${passed ? 'Continue \u2192' : 'Try Again'}
                </button>
            </div>
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

    const lessonName = (mathState.lesson || '').replace(/_/g, ' ');
    const pretestPct = Math.round((mathState.pretestScore || 0) / 5 * 100);
    stage.innerHTML = `
        <div class="math-complete">
            <div class="math-complete-hero">
                <div class="math-complete-icon">\u{1F389}</div>
                <h2>Lesson Complete!</h2>
                <p>${_escS(lessonName)}</p>
                <div class="math-complete-stats">
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Pretest</div>
                        <div class="math-complete-stat-val">${mathState.pretestScore}/5</div>
                        <div class="math-complete-stat-sub">${pretestPct}%</div>
                    </div>
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Rounds</div>
                        <div class="math-complete-stat-val">3</div>
                        <div class="math-complete-stat-sub">Completed</div>
                    </div>
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Mastery</div>
                        <div class="math-complete-stat-val">\u2713</div>
                        <div class="math-complete-stat-sub">Unlocked</div>
                    </div>
                </div>
            </div>
            <div class="math-complete-actions">
                <button class="math-btn-primary" onclick="exitMathLesson()">Back to Math</button>
            </div>
        </div>
    `;
}

/** @tag MATH @tag ACADEMY */
function exitMathLesson() {
    if (typeof unmountMathShell === 'function') unmountMathShell();
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

    _loadWrongReviewProblems(wrongIds).then(problems => {
        if (problems.length === 0) {
            loadMathStage('complete');
            return;
        }
        mathState.problems = problems;
        mathState.currentIdx = 0;
        mathState.correct = 0;
        mathState.wrong = [];
        mathState.wrongConcepts = [];
        renderMathProblem();
    });
}

/** @tag MATH @tag ACADEMY */
async function _loadWrongReviewProblems(wrongIds) {
    const problems = [];
    for (const round of ['practice_r1', 'practice_r2', 'practice_r3']) {
        try {
            const url = '/api/math/academy/'
                + encodeURIComponent(mathState.grade) + '/'
                + encodeURIComponent(mathState.unit) + '/'
                + encodeURIComponent(mathState.lesson) + '/' + round;
            const res = await fetch(url);
            if (!res.ok) continue;
            const data = await res.json();
            (data.problems || []).forEach(p => {
                if (wrongIds.includes(p.id) && !problems.find(x => x.id === p.id)) {
                    problems.push(p);
                }
            });
        } catch (_) {}
    }
    return problems;
}
