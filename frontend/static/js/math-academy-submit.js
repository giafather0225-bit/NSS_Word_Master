/* ================================================================
   math-academy-submit.js — Answer submission, result handling, exit quiz
   Section: Math
   Dependencies: math-academy.js (mathState, loadMathStage, advanceMathStage,
                 renderMathProblem, renderMathRoadmap),
                 math-academy-feedback.js (showMathFeedback),
                 math-academy-ui.js (_findCpaFallback, _showEarlyBumpPrompt),
                 math-unit-test.js (_checkUnitTestAnswer),
                 math-problems-ui.js (_submitMyProblemAnswer, _showMasteryNote,
                                      _renderMyProblemsComplete),
                 math-unit-test.js (startMathUnitTest)
   API endpoints: POST /api/math/academy/submit-answer,
                  POST /api/math/academy/try/submit,
                  POST /api/math/academy/exit-quiz/submit
   ================================================================ */

/* global mathState, loadMathStage, advanceMathStage, renderMathProblem,
          renderMathRoadmap, showMathFeedback, _findCpaFallback,
          _showEarlyBumpPrompt, _checkUnitTestAnswer, _submitMyProblemAnswer,
          _showMasteryNote, _renderMyProblemsComplete, startMathUnitTest */

// ── Submit answer ───────────────────────────────────────────

/**
 * Submit a math answer to the API and return a result object.
 * Routes to the correct endpoint based on mathState.stage.
 * @tag MATH @tag ACADEMY
 */
async function submitMathAnswer(problemId, userAnswer) {
    if (mathState.stage === 'unit_test') {
        return _checkUnitTestAnswer(problemId, userAnswer);
    }
    if (mathState.stage === 'my_problems') {
        return _submitMyProblemAnswer(problemId, userAnswer);
    }
    // v2.0: try stage uses dedicated endpoint with attempt tracking
    if (mathState.stage === 'try' && mathState._v2Flow) {
        return _submitTryAnswer(problemId, userAnswer);
    }
    // v2.0: pre_test collects answers silently — diagnostic only, no per-question feedback
    if ((mathState.stage === 'pretest' || mathState.stage === 'pre_test') && mathState._v2Flow) {
        return _collectPreTestAnswer(problemId, userAnswer);
    }
    // v2.0: exit_quiz collects answers client-side for batch submit
    if (mathState.stage === 'exit_quiz') {
        return _collectExitQuizAnswer(problemId, userAnswer);
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

/** @tag MATH @tag ACADEMY */
async function _submitTryAnswer(problemId, userAnswer) {
    const prev = mathState.tryAttemptCounts[problemId] || 0;
    const attemptNum = prev + 1;
    mathState.tryAttemptCounts[problemId] = attemptNum;
    try {
        const res = await fetch('/api/math/academy/try/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grade: mathState.grade,
                unit: mathState.unit,
                lesson: mathState.lesson,
                problem_id: problemId,
                user_answer: userAnswer,
                attempt_number: attemptNum,
                time_spent_sec: 0,
            }),
        });
        if (!res.ok) throw new Error('Submit failed');
        return await res.json();
    } catch (err) {
        console.error('[math] Try submit failed:', err);
        return { is_correct: false, correct_answer: '?', feedback_stage: null, feedback: 'Error submitting answer.' };
    }
}

/** Client-side answer collection for exit quiz — no per-problem server call. @tag MATH @tag ACADEMY */
function _collectExitQuizAnswer(problemId, userAnswer) {
    mathState.exitQuizAnswers.push({ problem_id: problemId, user_answer: userAnswer, time_spent_sec: 0 });
    return Promise.resolve({ is_correct: null, _exitQuizCollect: true });
}

/**
 * Client-side answer collection for pre_test — grades locally for diagnostic score,
 * never shows feedback. Score is sent to server after all questions complete.
 * @tag MATH @tag ACADEMY
 */
function _collectPreTestAnswer(problemId, userAnswer) {
    const problem = mathState.problems[mathState.currentIdx];
    if (problem) {
        const ca = String(problem.correct_answer != null ? problem.correct_answer : '').trim().toUpperCase();
        const ua = String(userAnswer != null ? userAnswer : '').trim().toUpperCase();
        if (ca === ua) mathState.preTestCorrect = (mathState.preTestCorrect || 0) + 1;
    }
    return Promise.resolve({ is_correct: null, _preTestCollect: true });
}

// ── Handle answer result ────────────────────────────────────

/**
 * Handle answer result: show feedback, advance or record wrong.
 * @tag MATH @tag ACADEMY
 */
function handleMathAnswerResult(result, problem) {
    // v2.0 pre_test collect mode: no feedback overlay — diagnostic only, always advances to learn
    if (result._preTestCollect) {
        mathState.currentIdx++;
        if (mathState.currentIdx >= mathState.problems.length) {
            _submitPreTest();
        } else {
            renderMathProblem();
            renderMathRoadmap();
        }
        return;
    }

    // v2.0 exit_quiz collect mode: no feedback overlay — just advance silently
    if (result._exitQuizCollect) {
        mathState.currentIdx++;
        if (mathState.currentIdx >= mathState.problems.length) {
            _submitExitQuiz();
        } else {
            renderMathProblem();
            renderMathRoadmap();
        }
        return;
    }

    // My Problems stage: feedback + mastery celebration + advance
    if (mathState.stage === 'my_problems') {
        showMathFeedback(result, problem, () => {
            const advance = () => {
                mathState.currentIdx++;
                if (mathState.currentIdx >= mathState.problems.length) {
                    _renderMyProblemsComplete();
                } else {
                    renderMathProblem();
                }
            };
            if (result.is_mastered) {
                mathState._myProblemsMastered = (mathState._myProblemsMastered || 0) + 1;
                _showMasteryNote(advance);
            } else {
                advance();
            }
        });
        return;
    }

    const isPractice = mathState.stage.startsWith('practice_');
    const isTry = mathState.stage === 'try';

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

    // v2.0 Try stage — first wrong: show feedback with Retry button
    if (isTry && result.feedback_stage === 'first_wrong') {
        showMathFeedback(
            result,
            problem,
            () => {
                mathState.currentIdx++;
                if (mathState.currentIdx >= mathState.problems.length) advanceMathStage();
                else { renderMathProblem(); renderMathRoadmap(); }
            },
            () => {
                renderMathProblem();
                renderMathRoadmap();
            }
        );
        return;
    }

    showMathFeedback(result, problem, () => {
        // Adaptive: 5 consecutive correct → bump to next round early
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

// ── v2.0 Pre-Test submit ────────────────────────────────────

/**
 * Submit pre_test diagnostic result to server, then advance to learn.
 * Non-blocking: failure is silently swallowed — the warm-up always proceeds.
 * @tag MATH @tag ACADEMY
 */
async function _submitPreTest() {
    const score = mathState.preTestCorrect || 0;
    const total = mathState.problems.length;
    try {
        await fetch('/api/math/academy/pre-test/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grade: mathState.grade,
                unit: mathState.unit,
                lesson: mathState.lesson,
                score,
                total,
                skipped: false,
            }),
        });
    } catch (_) { /* diagnostic — non-blocking */ }
    loadMathStage('learn');
}

// ── v2.0 Exit Quiz submit ───────────────────────────────────

/** Batch-submit all collected exit quiz answers. @tag MATH @tag ACADEMY */
async function _submitExitQuiz() {
    const stageEl = document.getElementById('stage');
    if (stageEl) stageEl.innerHTML = '<div class="math-loading">Checking your work…</div>';

    try {
        const res = await fetch('/api/math/academy/exit-quiz/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grade: mathState.grade,
                unit: mathState.unit,
                lesson: mathState.lesson,
                answers: mathState.exitQuizAnswers,
            }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        _renderExitQuizResult(data);
    } catch (err) {
        console.error('[math] Exit quiz submit failed:', err);
        if (stageEl) stageEl.innerHTML = `
            <div class="math-stage-error">
                <p>Something went wrong submitting your answers.</p>
                <div class="math-stage-error-actions">
                    <button class="math-btn-ghost" onclick="loadMathStage('exit_quiz')">Try Again</button>
                </div>
            </div>`;
    }
}

/** Render exit quiz pass/fail result screen. @tag MATH @tag ACADEMY */
function _renderExitQuizResult(data) {
    const stageEl = document.getElementById('stage');
    if (!stageEl) return;

    const passed = data.passed || data.force_unlocked;
    const score = data.score || 0;
    const total = data.total || 5;
    const attempts = data.exit_quiz_attempts || 1;

    const xp = data.xp_earned || 0;
    const reviewDate = data.next_review_date || '';

    if (passed) {
        if (data.unit_test_ready) {
            startMathUnitTest(mathState.grade, mathState.unit);
        } else {
            mathState.stage = 'complete';
            mathState.correct = score;
            mathState.spacedReviewDate = reviewDate;
            mathState.xpEarned = xp;
            mathState.islandData = data.island ?? null;  // passed to _appendIslandUpdate
            loadMathStage('complete');
        }
        return;
    }

    const attemptsLeft = Math.max(0, 3 - attempts);
    const need = Math.ceil(total * 0.8);

    stageEl.innerHTML = `
        <div class="math-exit-quiz-result">
            <div class="math-result-score">${score} / ${total}</div>
            <div class="math-result-msg">You need ${need} correct to move on. Keep going!</div>
            ${attemptsLeft > 0
                ? `<div class="math-attempts-left">${attemptsLeft} attempt${attemptsLeft !== 1 ? 's' : ''} remaining</div>`
                : '<div class="math-attempts-left">No attempts remaining</div>'}
            <div class="math-result-actions">
                ${attemptsLeft > 0
                    ? `<button class="math-btn-primary" onclick="loadMathStage('exit_quiz')">Try Again</button>`
                    : `<button class="math-btn-primary" onclick="loadMathStage('complete')">Continue</button>`}
                <button class="math-btn-ghost" onclick="loadMathStage('learn')">Review Lesson</button>
            </div>
        </div>`;
}
