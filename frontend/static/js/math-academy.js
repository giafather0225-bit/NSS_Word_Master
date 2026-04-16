/* ================================================================
   math-academy.js — Math Academy lesson flow controller
   Section: Math
   Dependencies: core.js, math-learn-cards.js, math-problem-ui.js
   API endpoints: /api/math/academy/* (all)
   ================================================================ */

/* global mathGrade, mathUnit, mathLesson */

// ── Math lesson state ───────────────────────────────────────
const mathState = {
    grade: '',
    unit: '',
    lesson: '',
    stage: '',           // pretest | learn | try | practice_r1 | practice_r2 | practice_r3 | wrong_review | complete
    problems: [],
    currentIdx: 0,
    correct: 0,
    wrong: [],           // wrong problem ids for review
    pretestScore: 0,
};

const MATH_STAGES = ['pretest', 'learn', 'try', 'practice_r1', 'practice_r2', 'practice_r3', 'wrong_review', 'complete'];
const MATH_STAGE_LABELS = {
    pretest: 'Pretest',
    learn: 'Learn',
    try: 'Try',
    practice_r1: 'Practice R1',
    practice_r2: 'Practice R2',
    practice_r3: 'Practice R3',
    wrong_review: 'Wrong Review',
    complete: 'Complete!',
};

// ── Start lesson ────────────────────────────────────────────

/**
 * Start a math lesson from the beginning (pretest).
 * @tag MATH @tag ACADEMY
 */
async function startMathLesson(grade, unit, lesson) {
    mathState.grade = grade;
    mathState.unit = unit;
    mathState.lesson = lesson;
    mathState.stage = 'pretest';
    mathState.currentIdx = 0;
    mathState.correct = 0;
    mathState.wrong = [];
    mathState.pretestScore = 0;

    // Show stage card, hide others
    const stageCard = document.getElementById('stage-card');
    const stage = document.getElementById('stage');
    const idleWrap = document.getElementById('idle-wrapper');
    const homeDash = document.getElementById('home-dashboard');
    const topBar = document.querySelector('.top-bar');

    if (homeDash) homeDash.style.display = 'none';
    if (idleWrap) idleWrap.style.display = 'none';
    if (stageCard) { stageCard.classList.remove('hidden'); stageCard.style.display = ''; }
    if (topBar) topBar.style.display = '';

    // Collapse sidebar
    const sidebar = document.getElementById('sidebar');
    if (sidebar) { sidebar.classList.add('collapsed'); localStorage.setItem('sb_collapsed', '1'); }

    // Render math roadmap
    renderMathRoadmap();

    // Load pretest
    await loadMathStage('pretest');
}

// ── Load stage data ─────────────────────────────────────────

/**
 * Load problems for the current stage from API.
 * @tag MATH @tag ACADEMY
 */
async function loadMathStage(stageName) {
    mathState.stage = stageName;
    mathState.currentIdx = 0;
    mathState.correct = 0;

    if (stageName === 'complete') {
        renderMathComplete();
        return;
    }

    if (stageName === 'wrong_review') {
        renderMathWrongReview();
        return;
    }

    try {
        const url = `/api/math/academy/${encodeURIComponent(mathState.grade)}/${encodeURIComponent(mathState.unit)}/${encodeURIComponent(mathState.lesson)}/${stageName}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Failed to load ${stageName}`);
        const data = await res.json();
        mathState.problems = data.problems || [];
    } catch (err) {
        console.error('[math] Load stage failed:', err);
        mathState.problems = [];
    }

    renderMathRoadmap();

    if (stageName === 'learn') {
        renderMathLearnCards(mathState.problems);
    } else {
        renderMathProblem();
    }
}

// ── Advance to next stage ───────────────────────────────────

/**
 * Called when a stage is completed. Determines the next stage.
 * @tag MATH @tag ACADEMY
 */
function advanceMathStage() {
    const s = mathState.stage;
    const total = mathState.problems.length;
    const pct = total > 0 ? Math.round(mathState.correct / total * 100) : 0;

    if (s === 'pretest') {
        mathState.pretestScore = mathState.correct;
        if (mathState.correct === total && total > 0) {
            // 5/5 — skip Learn/Try, go to Practice R1
            loadMathStage('practice_r1');
        } else {
            loadMathStage('learn');
        }
        return;
    }

    if (s === 'learn') {
        loadMathStage('try');
        return;
    }

    if (s === 'try') {
        loadMathStage('practice_r1');
        return;
    }

    // Practice rounds: need >= 80% to pass
    if (s === 'practice_r1' || s === 'practice_r2' || s === 'practice_r3') {
        if (pct < 80) {
            // Failed — retry same stage
            showMathStageFeedback(false, pct);
            return;
        }

        // Collect wrong answers for review
        if (mathState.wrong.length > 0) {
            // Push to global wrong list (will be used in wrong_review)
            if (!mathState._allWrong) mathState._allWrong = [];
            mathState._allWrong.push(...mathState.wrong);
        }

        // Next practice round or wrong review
        if (s === 'practice_r1') {
            // Check if r2 exists
            loadMathStage('practice_r2');
        } else if (s === 'practice_r2') {
            // Check if r3 exists
            loadMathStage('practice_r3');
        } else {
            // After R3: wrong review if any, else complete
            if (mathState._allWrong && mathState._allWrong.length > 0) {
                loadMathStage('wrong_review');
            } else {
                loadMathStage('complete');
            }
        }
        return;
    }

    if (s === 'wrong_review') {
        loadMathStage('complete');
        return;
    }
}

// ── Submit answer ───────────────────────────────────────────

/**
 * Submit a math answer to the API and handle result.
 * @tag MATH @tag ACADEMY
 */
async function submitMathAnswer(problemId, userAnswer) {
    try {
        const res = await fetch('/api/math/academy/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                problem_id: problemId,
                grade: mathState.grade,
                unit: mathState.unit,
                lesson: mathState.lesson,
                stage: mathState.stage,
                user_answer: userAnswer,
                time_spent_sec: 0,
            }),
        });
        if (!res.ok) throw new Error('Submit failed');
        return await res.json();
    } catch (err) {
        console.error('[math] Submit answer failed:', err);
        return { is_correct: false, correct_answer: '?', feedback: 'Error submitting answer.' };
    }
}

/**
 * Handle answer result: show feedback, advance or record wrong.
 * @tag MATH @tag ACADEMY
 */
function handleMathAnswerResult(result, problem) {
    if (result.is_correct) {
        mathState.correct++;
    } else {
        mathState.wrong.push(problem.id);
    }

    // Show feedback overlay
    showMathFeedback(result, problem, () => {
        mathState.currentIdx++;
        if (mathState.currentIdx >= mathState.problems.length) {
            advanceMathStage();
        } else {
            renderMathProblem();
            renderMathRoadmap();
        }
    });
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

    // Progress bar
    const fill = document.getElementById('top-progress-fill');
    const pct = document.getElementById('progress-pct');
    if (fill && mathState.problems.length > 0) {
        const p = Math.round(mathState.currentIdx / mathState.problems.length * 100);
        fill.style.width = p + '%';
        if (pct) pct.textContent = p + '%';
    }
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

// ── Feedback overlay ────────────────────────────────────────

/**
 * Show answer feedback overlay.
 * @tag MATH @tag ACADEMY
 */
function showMathFeedback(result, problem, onNext) {
    const stage = document.getElementById('stage');
    if (!stage) return;

    const overlay = document.createElement('div');
    overlay.className = 'math-feedback-overlay ' + (result.is_correct ? 'math-feedback-correct' : 'math-feedback-wrong');

    const stepsHtml = (result.solution_steps || []).map(s => `<li>${s}</li>`).join('');

    overlay.innerHTML = `
        <div class="math-feedback-card">
            <div class="math-feedback-result">${result.is_correct ? '\u2713 Correct!' : '\u2717 Not quite'}</div>
            ${!result.is_correct ? `<div class="math-feedback-answer">Answer: ${result.correct_answer}</div>` : ''}
            <div class="math-feedback-text">${result.feedback || ''}</div>
            ${stepsHtml ? `<ol class="math-feedback-steps">${stepsHtml}</ol>` : ''}
            <button class="math-btn-primary" id="math-feedback-next">Next</button>
        </div>
    `;

    stage.appendChild(overlay);

    document.getElementById('math-feedback-next').addEventListener('click', () => {
        overlay.remove();
        onNext();
    });

    // Also allow Enter key
    const handler = (e) => {
        if (e.key === 'Enter') {
            document.removeEventListener('keydown', handler);
            overlay.remove();
            onNext();
        }
    };
    document.addEventListener('keydown', handler);
}
