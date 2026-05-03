/* ================================================================
   math-unit-test.js — Unit test start + client-side answer grading
   Section: Math
   Dependencies: math-academy.js (mathState, renderMathProblem,
                 renderMathRoadmap, advanceMathStage),
                 math-academy-shell.js (mountMathShell),
                 math-academy-ui.js (_renderRoundSummary, _topWeakConcepts),
                 math-lesson-complete.js (exitMathLesson)
   API endpoints: GET /api/math/academy/{grade}/{unit}/unit-test,
                  POST /api/math/academy/unit-test/submit
   ================================================================ */

/* global mathState, renderMathProblem, renderMathRoadmap,
          mountMathShell, _showMathLoading, _hideMathLoading,
          _showMathStageError, _renderRoundSummary, _topWeakConcepts,
          exitMathLesson */

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
 * Client-side answer check for unit test problems.
 * Correct answer lives in problem JSON (correct_answer or answer field).
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

    const fbObj = (problem.feedback && typeof problem.feedback === 'object') ? problem.feedback : null;
    const feedback = isCorrect
        ? (problem.feedback_correct || fbObj?.correct || '')
        : (problem.feedback_wrong || fbObj?.incorrect || fbObj?.wrong || '');
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
