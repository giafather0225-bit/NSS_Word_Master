/* ================================================================
   math-academy.js — Math Academy lesson flow controller (core)
   Section: Math
   Dependencies: core.js, math-learn-cards.js, math-problem-ui.js,
                 math-academy-ui.js, math-academy-feedback.js,
                 math-academy-submit.js (submitMathAnswer, handleMathAnswerResult,
                                         _submitExitQuiz, _renderExitQuizResult)
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
    stage: '',           // pre_test|pretest | learn | try | exit_quiz | practice_r1 | practice_r2 | practice_r3 | wrong_review | complete
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
    hintTimer: null,     // hint countdown interval (cleared on stage transition)
    learnCards: [],      // cached learn cards (for CPA Fallback feedback)
    // ── v2.0 ──
    tryAttemptCounts: {},   // {problemId: attemptCount} — tracks 1st vs 2nd attempt in try stage
    exitQuizAnswers: [],     // collected answers for batch exit-quiz submit
    _v2Flow: false,          // true when lesson uses pre_test → learn → try → exit_quiz flow
    preTestCorrect: 0,       // correct count during pre_test (diagnostic only — never shown to user)
    spacedReviewDate: '',    // next spaced review date from exit_quiz/submit response
    xpEarned: 0,             // XP awarded on lesson completion (from exit_quiz submit)
};

const MATH_STAGES = ['pre_test', 'learn', 'try', 'exit_quiz', 'complete', 'practice_r1', 'practice_r2', 'practice_r3', 'wrong_review'];
const MATH_STAGE_LABELS = {
    pre_test: 'Pre-Test',
    pretest: 'Pretest',
    learn: 'Learn',
    try: 'Try',
    exit_quiz: 'Exit Quiz',
    practice_r1: 'Practice R1',
    practice_r2: 'Practice R2',
    practice_r3: 'Practice R3',
    wrong_review: 'Wrong Review',
    complete: 'Complete!',
    unit_test: 'Unit Test',
};

// ── Start lesson ────────────────────────────────────────────

/**
 * Start (or resume) a math lesson.
 * @param {string} grade
 * @param {string} unit
 * @param {string} lesson
 * @param {string} [stage='pretest'] — stage to resume from
 * @tag MATH @tag ACADEMY
 */
async function startMathLesson(grade, unit, lesson, stage = 'pretest') {
    mathState.grade = grade;
    mathState.unit = unit;
    mathState.lesson = lesson;
    mathState.stage = stage;
    mathState.currentIdx = 0;
    mathState.correct = 0;
    mathState.wrong = [];
    mathState.pretestScore = 0;
    mathState._allWrong = [];
    mathState.learnCards = null;
    mathState.tryAttemptCounts = {};
    mathState.exitQuizAnswers = [];
    mathState._v2Flow = false;

    // Resume: ask server for current progress stage
    try {
        const rres = await fetch(
            `/api/math/academy/lesson/${encodeURIComponent(grade)}/${encodeURIComponent(unit)}/${encodeURIComponent(lesson)}/stage`
        );
        if (rres.ok) {
            const info = await rres.json();
            const srv = info.stage || 'pretest';
            // v2.0 stages signal the new flow
            if (srv === 'pre_test' || srv === 'exit_quiz' || srv === 'learn' || srv === 'try') {
                mathState._v2Flow = true;
            }
            // Map server stage names to internal load-stage names
            if (srv === 'pre_test') stage = 'pretest';
            else if (srv === 'completed') stage = 'complete';
            else stage = srv;
        }
    } catch (_) { /* use caller default */ }

    if (typeof showLessonStage === 'function') showLessonStage();

    if (typeof mathHomeSaveLesson === 'function') mathHomeSaveLesson(grade, unit, lesson);
    if (typeof mountMathShell === 'function') mountMathShell();
    renderMathRoadmap();
    await loadMathStage(stage);
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
    if (mathState.hintTimer) { clearInterval(mathState.hintTimer); mathState.hintTimer = null; }
    if (stageName === 'pretest' || stageName === 'pre_test') {
        mathState._allWrong = [];
        mathState.learnCards = null;
        mathState.tryAttemptCounts = {};
        mathState.preTestCorrect = 0;
    }
    if (stageName === 'exit_quiz') {
        mathState.exitQuizAnswers = [];
        mathState.tryAttemptCounts = {};
    }

    if (stageName === 'complete') { renderMathComplete(); return; }
    if (stageName === 'wrong_review') { renderMathWrongReview(); return; }

    // Normalize pre_test → pretest for JSON file key lookup
    const stageUrl = stageName === 'pre_test' ? 'pretest' : stageName;

    try {
        const url = `/api/math/academy/${encodeURIComponent(mathState.grade)}/${encodeURIComponent(mathState.unit)}/${encodeURIComponent(mathState.lesson)}/${stageUrl}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Failed to load ${stageName}`);
        const data = await res.json();
        mathState.problems = data.problems || [];
    } catch (err) {
        console.error('[math] Load stage failed:', err);
        mathState.problems = [];
        mathState.wrongConcepts = [];
        mathState._allWrong     = [];
        mathState.consecCorrect = 0;
        mathState.consecWrong   = 0;
        mathState.forceHints    = false;
        mathState.learnCards    = null;
    }

    // Cache learn cards on first fetch so Practice feedback can use CPA Fallback
    if (stageName === 'learn') {
        mathState.learnCards = mathState.problems.slice();
    }

    renderMathRoadmap();

    if (stageName === 'learn') {
        if (mathState.problems.length === 0) {
            _showMathStageError(stageName);
        } else {
            renderMathLearnCards(mathState.problems);
        }
    } else {
        if (mathState.problems.length === 0) {
            _showMathStageError(stageName);
        } else {
            renderMathProblem();
        }
    }
}

/** Show a visible error state in #stage when problems fail to load. @tag MATH @tag ACADEMY */
function _showMathStageError(stageName) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `
        <div class="math-stage-error">
            <p>Could not load ${stageName} problems.</p>
            <div class="math-stage-error-actions">
                <button class="math-btn-ghost" onclick="loadMathStage('${stageName}')">Try Again</button>
                <button class="math-btn-ghost" onclick="exitMathLesson()">Go Back</button>
            </div>
        </div>
    `;
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
async function advanceMathStage() {
    const s = mathState.stage;
    const total = mathState.problems.length;
    const pct = total > 0 ? Math.round(mathState.correct / total * 100) : 0;

    if (s === 'pretest' || s === 'pre_test') {
        mathState.pretestScore = mathState.correct;
        if (mathState._v2Flow) {
            // v2.0: pre_test is diagnostic only — always go to learn
            loadMathStage('learn');
        } else if (mathState.correct === total && total > 0) {
            // v1: perfect pretest → skip learn
            _prefetchLearnCards();
            loadMathStage('practice_r1');
        } else {
            loadMathStage('learn');
        }
        return;
    }

    if (s === 'learn') { loadMathStage('try'); return; }

    if (s === 'try') {
        if (mathState._v2Flow) {
            loadMathStage('exit_quiz');
        } else {
            loadMathStage('practice_r1');
        }
        return;
    }

    // exit_quiz is submitted via _submitExitQuiz() — advanceMathStage should not be called for it
    if (s === 'exit_quiz') { return; }

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

    if (s === 'unit_test') {
        const threshold = mathState._unitTestPassThreshold || 0.8;
        const passed = total > 0 && (mathState.correct / total) >= threshold;
        let xpEarned = 0;
        try {
            const res = await fetch('/api/math/academy/unit-test/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    grade: mathState.grade,
                    unit: mathState.unit,
                    score: mathState.correct,
                    total,
                }),
            });
            if (res.ok) { const d = await res.json(); xpEarned = d.xp_earned || 0; }
        } catch (err) { console.warn('[math] Unit test score submit failed:', err); }

        _renderRoundSummary({
            stageLabel: 'Unit Test',
            correct: mathState.correct,
            total,
            pct,
            passed,
            xpEarned,
            weakConcepts: _topWeakConcepts(mathState.wrongConcepts),
            onContinue: () => {
                if (!passed) {
                    startMathUnitTest(mathState.grade, mathState.unit);
                } else if (typeof exitMathLesson === 'function') {
                    exitMathLesson();
                } else if (typeof loadMathHome === 'function') {
                    loadMathHome();
                }
            },
        });
        return;
    }
}


