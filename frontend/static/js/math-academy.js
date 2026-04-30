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
    hintTimer: null,     // hint countdown interval (cleared on stage transition)
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
    if (stageName === 'pretest') { mathState._allWrong = []; mathState.learnCards = null; }

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
        // ── PHASE-0 FIX P1: reset missing state ──
        mathState.wrongConcepts = [];
        mathState._allWrong     = [];
        mathState.consecCorrect = 0;
        mathState.consecWrong   = 0;
        mathState.forceHints    = false;
        mathState.learnCards    = null;
        // ── END P1 ──
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

    if (s === 'unit_test') {
        const threshold = mathState._unitTestPassThreshold || 0.8;
        const passed = total > 0 && (mathState.correct / total) >= threshold;
        // Fire-and-forget score submission
        fetch('/api/math/academy/unit-test/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grade: mathState.grade,
                unit: mathState.unit,
                score: mathState.correct,
                total,
            }),
        }).catch(err => console.warn('[math] Unit test score submit failed:', err));

        _renderRoundSummary({
            stageLabel: 'Unit Test',
            correct: mathState.correct,
            total,
            pct,
            passed,
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

// ── Submit answer ───────────────────────────────────────────

/**
 * Submit a math answer to the API and handle result.
 * For unit_test stage, answers are checked client-side (problems include correct_answer).
 * @tag MATH @tag ACADEMY
 */
async function submitMathAnswer(problemId, userAnswer) {
    if (mathState.stage === 'unit_test') {
        return _checkUnitTestAnswer(problemId, userAnswer);
    }
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

// ── Unit Test ───────────────────────────────────────────────

/**
 * Start a unit test for the given grade + unit.
 * Problems come from unit_test.json; answers are checked client-side.
 * Final score is submitted to /api/math/academy/unit-test/submit.
 * @param {string} grade  e.g. "G3"
 * @param {string} unit   e.g. "U1_place_value"
 * @tag MATH @tag ACADEMY
 */
async function startMathUnitTest(grade, unit) {
    mathState.grade = grade;
    mathState.unit = unit;
    mathState.lesson = '';
    mathState.stage = 'unit_test';
    mathState.currentIdx = 0;
    mathState.correct = 0;
    mathState.wrong = [];
    mathState.wrongConcepts = [];
    mathState.consecCorrect = 0;
    mathState.consecWrong = 0;
    mathState.forceHints = false;
    mathState._allWrong = [];
    mathState._unitTestPassThreshold = 0.8;
    mathState._unitTestTimeLimitMin = 30;
    if (mathState.hintTimer) { clearInterval(mathState.hintTimer); mathState.hintTimer = null; }

    if (typeof mountMathShell === 'function') mountMathShell();
    renderMathRoadmap();

    const stageEl = document.getElementById('stage');
    if (stageEl && typeof _showMathLoading === 'function') _showMathLoading(stageEl);

    try {
        const url = `/api/math/academy/${encodeURIComponent(grade)}/${encodeURIComponent(unit)}/unit-test`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        mathState.problems = data.problems || [];
        mathState._unitTestPassThreshold = data.pass_threshold || 0.8;
        mathState._unitTestTimeLimitMin = data.time_limit_min || 30;
    } catch (err) {
        console.error('[math] Unit test load failed:', err);
        mathState.problems = [];
    }

    if (typeof _hideMathLoading === 'function') _hideMathLoading();

    if (mathState.problems.length === 0) {
        _showMathStageError('unit_test');
        return;
    }

    renderMathProblem();
}

/**
 * Client-side answer check for unit test problems (correct_answer lives in problem JSON).
 * @tag MATH @tag ACADEMY
 */
function _checkUnitTestAnswer(problemId, userAnswer) {
    const problem = mathState.problems.find(p => p.id === problemId);
    if (!problem) return { is_correct: false, correct_answer: '?', feedback: '' };

    const correctRaw = String(
        problem.correct_answer != null ? problem.correct_answer
        : (problem.answer != null ? problem.answer : '')
    ).trim();
    const userRaw = String(userAnswer).trim();
    const options = problem.options || [];

    let isCorrect = false;
    let correctDisplay = correctRaw;

    if (/^[A-Ha-h]$/.test(correctRaw) && options.length > 0) {
        const idx = correctRaw.toUpperCase().charCodeAt(0) - 65;
        if (idx >= 0 && idx < options.length) {
            const rawOpt = String(options[idx]);
            const cleanOpt = rawOpt.replace(/^[A-Za-z][\)\.\:]\s*/, '').trim();
            correctDisplay = cleanOpt || rawOpt;
            isCorrect = userRaw.toLowerCase() === correctRaw.toLowerCase()
                     || userRaw.toLowerCase() === cleanOpt.toLowerCase()
                     || userRaw.toLowerCase() === rawOpt.toLowerCase();
        } else {
            isCorrect = userRaw.toLowerCase() === correctRaw.toLowerCase();
        }
    } else if (correctRaw.toLowerCase() === 'true' || correctRaw.toLowerCase() === 'false') {
        isCorrect = userRaw.toLowerCase() === correctRaw.toLowerCase();
    } else {
        isCorrect = _mathAnswersEquivalent(userRaw, correctRaw);
    }

    const feedback = isCorrect
        ? (problem.feedback_correct || '')
        : (problem.feedback_wrong || '');
    return { is_correct: isCorrect, correct_answer: correctDisplay, feedback };
}

/**
 * Normalize numeric/text answers for loose comparison (strips whitespace, trailing zeros).
 * @tag MATH @tag ACADEMY
 */
function _mathAnswersEquivalent(a, b) {
    const norm = s => s.toLowerCase().replace(/\s+/g, '').replace(/,/g, '').replace(/\.?0+$/, '');
    return norm(a) === norm(b);
}
