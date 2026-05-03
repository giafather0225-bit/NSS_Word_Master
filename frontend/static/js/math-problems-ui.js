/* ================================================================
   math-problems-ui.js — My Problems (wrong review) session UI
   Section: Math
   Dependencies: math-academy.js (mathState, renderMathProblem,
                 renderMathRoadmap, handleMathAnswerResult),
                 math-academy-shell.js (mountMathShell, unmountMathShell),
                 math-lesson-complete.js (exitMathLesson)
   API endpoints: GET /api/math/my-problems/review,
                  POST /api/math/my-problems/submit-answer
   ================================================================ */

/* global mathState, renderMathProblem, renderMathRoadmap,
          mountMathShell, unmountMathShell, exitMathLesson, _mathEsc */

/**
 * Start a My Problems review session.
 * Fetches due review items, injects them into mathState, and launches
 * the normal renderMathProblem loop with stage='my_problems'.
 * @tag MATH @tag MATH_PROBLEMS
 */
async function startMathProblemsReview() {
    if (typeof mountMathShell === 'function') mountMathShell();

    const stageEl = document.getElementById('stage');
    if (stageEl) stageEl.innerHTML = '<div class="math-loading">Loading your problems…</div>';

    let items = [];
    try {
        const res = await fetch('/api/math/my-problems/review');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        items = data.items || [];
    } catch (err) {
        console.error('[math] My Problems load failed:', err);
        if (stageEl) stageEl.innerHTML = `
            <div class="math-stage-error">
                <p>Could not load problems. Please try again.</p>
                <div class="math-stage-error-actions">
                    <button class="math-btn-ghost" onclick="startMathProblemsReview()">Retry</button>
                    <button class="math-btn-ghost" onclick="exitMathLesson()">Back to Math</button>
                </div>
            </div>`;
        return;
    }

    if (items.length === 0) {
        _renderMyProblemsEmpty(stageEl);
        return;
    }

    // Inject review_id into each problem for submit routing
    const problems = items.map(item => {
        const p = item.problem || {};
        p._reviewId = item.review_id;
        p._grade = item.grade;
        p._unit = item.unit;
        p._lesson = item.lesson;
        return p;
    });

    mathState.stage = 'my_problems';
    mathState.problems = problems;
    mathState.currentIdx = 0;
    mathState.correct = 0;
    mathState.wrong = [];
    mathState.wrongConcepts = [];
    mathState.consecCorrect = 0;
    mathState.consecWrong = 0;
    mathState._myProblemsMastered = 0;
    mathState._myProblemsTotal = problems.length;

    renderMathRoadmap();
    renderMathProblem();
}

/**
 * Submit a My Problems answer to the review endpoint.
 * Called from submitMathAnswer when stage='my_problems'.
 * Returns a result object compatible with handleMathAnswerResult.
 * @tag MATH @tag MATH_PROBLEMS
 */
async function _submitMyProblemAnswer(problemId, userAnswer) {
    const problem = mathState.problems.find(p => p.id === problemId);
    const reviewId = problem ? problem._reviewId : null;
    if (!reviewId) return { is_correct: false, correct_answer: '?', feedback: 'Problem not found.' };

    try {
        const res = await fetch('/api/math/my-problems/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ review_id: reviewId, user_answer: userAnswer }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error('[math] My Problems submit failed:', err);
        return { is_correct: false, correct_answer: '?', feedback: 'Error submitting answer.' };
    }
}

/**
 * Show a brief "Problem mastered!" banner inside the stage area.
 * Auto-removes after 1.6 s and calls onDone.
 * @tag MATH @tag MATH_PROBLEMS
 */
function _showMasteryNote(onDone) {
    const stageEl = document.getElementById('stage');
    if (!stageEl) { onDone(); return; }

    const banner = document.createElement('div');
    banner.className = 'math-mastery-note';
    banner.innerHTML = `
        <div class="math-mastery-note-inner">
            <i data-lucide="check-circle-2"></i>
            <span>Problem mastered!</span>
        </div>`;
    stageEl.appendChild(banner);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    setTimeout(() => {
        banner.classList.add('math-mastery-note-fade');
        setTimeout(() => { banner.remove(); onDone(); }, 300);
    }, 1300);
}

/**
 * Render empty state when no problems are due today.
 * @tag MATH @tag MATH_PROBLEMS
 */
function _renderMyProblemsEmpty(stageEl) {
    if (!stageEl) return;
    stageEl.innerHTML = `
        <div class="math-problems-empty">
            <div class="math-problems-empty-icon"><i data-lucide="check-circle-2"></i></div>
            <h2>All caught up!</h2>
            <p>No problems due today. Keep up the great work.</p>
            <div class="math-summary-actions">
                <button class="math-btn-primary" onclick="exitMathLesson()">Back to Math</button>
            </div>
        </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/**
 * Render session complete screen after all review items answered.
 * @tag MATH @tag MATH_PROBLEMS
 */
function _renderMyProblemsComplete() {
    const stageEl = document.getElementById('stage');
    if (!stageEl) return;

    const mastered = mathState._myProblemsMastered || 0;
    const total = mathState._myProblemsTotal || 0;
    const pct = total > 0 ? Math.round((mathState.correct / total) * 100) : 0;

    stageEl.innerHTML = `
        <div class="math-complete">
            <div class="math-complete-hero">
                <div class="math-complete-icon"><i data-lucide="award"></i></div>
                <h2>Review Done!</h2>
                <p>You reviewed ${total} problem${total !== 1 ? 's' : ''}</p>
                <div class="math-complete-stats">
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Accuracy</div>
                        <div class="math-complete-stat-val">${pct}<span style="font-size:14px;font-weight:600">%</span></div>
                        <div class="math-complete-stat-sub">${mathState.correct}/${total}</div>
                    </div>
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Mastered</div>
                        <div class="math-complete-stat-val">${mastered}</div>
                        <div class="math-complete-stat-sub">Removed</div>
                    </div>
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Remaining</div>
                        <div class="math-complete-stat-val">${total - mastered}</div>
                        <div class="math-complete-stat-sub">In queue</div>
                    </div>
                </div>
            </div>
            <div class="math-complete-actions">
                <button class="math-btn-primary" onclick="exitMathLesson()">Back to Math</button>
            </div>
        </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}
