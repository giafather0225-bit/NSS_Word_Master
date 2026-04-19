/* ================================================================
   math-academy.js — Math Academy lesson flow controller (core)
   Section: Math
   Dependencies: core.js, math-learn-cards.js, math-problem-ui.js,
                 math-academy-ui.js, math-academy-feedback.js
   API endpoints: /api/math/academy/* (all)
   ================================================================ */

/* global mathGrade, mathUnit, mathLesson,
          renderMathRoadmap, renderMathLearnCards, renderMathProblem,
          renderMathComplete, renderMathWrongReview, _renderRoundSummary,
          _topWeakConcepts, _findCpaFallback, _showEarlyBumpPrompt,
          showMathFeedback */

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
    wrongConcepts: [],   // wrong concepts for round summary
    pretestScore: 0,
    // ── M4 adaptive difficulty ──
    consecCorrect: 0,    // current consecutive correct (resets on wrong)
    consecWrong: 0,      // current consecutive wrong (resets on correct)
    forceHints: false,   // auto-expand hints after 3 consecutive wrong
    learnCards: [],      // cached learn cards (for CPA Fallback feedback)
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

    renderMathRoadmap();
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
    mathState.wrong = [];
    mathState.wrongConcepts = [];
    mathState.consecCorrect = 0;
    mathState.consecWrong = 0;
    mathState.forceHints = false;

    if (stageName === 'complete') { renderMathComplete(); return; }
    if (stageName === 'wrong_review') { renderMathWrongReview(); return; }

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

    // Cache learn cards on first fetch so Practice feedback can use CPA Fallback
    if (stageName === 'learn') {
        mathState.learnCards = mathState.problems.slice();
    }

    renderMathRoadmap();

    if (stageName === 'learn') {
        renderMathLearnCards(mathState.problems);
    } else {
        renderMathProblem();
    }
}

/** @tag MATH @tag CPA_FALLBACK */
async function _prefetchLearnCards() {
    if (mathState.learnCards && mathState.learnCards.length > 0) return;
    try {
        const url = `/api/math/academy/${encodeURIComponent(mathState.grade)}/${encodeURIComponent(mathState.unit)}/${encodeURIComponent(mathState.lesson)}/learn`;
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        mathState.learnCards = data.problems || [];
    } catch (_) { /* best-effort */ }
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
            _prefetchLearnCards();
            loadMathStage('practice_r1');
        } else {
            loadMathStage('learn');
        }
        return;
    }

    if (s === 'learn') { loadMathStage('try'); return; }
    if (s === 'try') { loadMathStage('practice_r1'); return; }

    // Practice rounds: need >= 80% to pass
    if (s === 'practice_r1' || s === 'practice_r2' || s === 'practice_r3') {
        if (mathState.wrong.length > 0) {
            if (!mathState._allWrong) mathState._allWrong = [];
            mathState._allWrong.push(...mathState.wrong);
        }

        const nextStage = s === 'practice_r1' ? 'practice_r2'
                        : s === 'practice_r2' ? 'practice_r3'
                        : null;
        const passed = pct >= 80;
        _renderRoundSummary({
            stageLabel: MATH_STAGE_LABELS[s],
            correct: mathState.correct,
            total,
            pct,
            passed,
            weakConcepts: _topWeakConcepts(mathState.wrongConcepts),
            onContinue: () => {
                if (!passed) { loadMathStage(s); return; }
                if (nextStage) {
                    loadMathStage(nextStage);
                } else if (mathState._allWrong && mathState._allWrong.length > 0) {
                    loadMathStage('wrong_review');
                } else {
                    loadMathStage('complete');
                }
            },
        });
        return;
    }

    if (s === 'wrong_review') { loadMathStage('complete'); return; }
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
    const isPractice = mathState.stage.startsWith('practice_');

    if (result.is_correct) {
        mathState.correct++;
        mathState.consecCorrect++;
        mathState.consecWrong = 0;
        if (mathState.consecCorrect >= 2) mathState.forceHints = false;
    } else {
        mathState.wrong.push(problem.id);
        if (problem.concept) mathState.wrongConcepts.push(problem.concept);
        mathState.consecCorrect = 0;
        mathState.consecWrong++;
        if (isPractice && mathState.consecWrong >= 3) mathState.forceHints = true;
    }

    // CPA Fallback: attach a pictorial hint for Practice wrong answers
    if (isPractice && !result.is_correct) {
        result._cpaFallback = _findCpaFallback(problem);
    }

    showMathFeedback(result, problem, () => {
        // Adaptive: 5 consecutive correct -> bump to next round early
        if (isPractice && mathState.consecCorrect >= 5 && mathState.currentIdx + 1 < mathState.problems.length) {
            _showEarlyBumpPrompt();
            return;
        }

        mathState.currentIdx++;
        if (mathState.currentIdx >= mathState.problems.length) {
            advanceMathStage();
        } else {
            renderMathProblem();
            renderMathRoadmap();
        }
    });
}
