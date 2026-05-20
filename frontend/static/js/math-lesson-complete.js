/* ================================================================
   math-lesson-complete.js — Lesson complete screen and exit
   Section: Math
   Dependencies: math-academy.js (mathState), math-academy-shell.js
                 (unmountMathShell), math-academy-ui.js (renderMathRoadmap),
                 math-katex-utils.js (_mathEsc), island-result.js (_appendIslandUpdate)
   API endpoints: POST /api/math/academy/complete-lesson (v1 flow only)
   ================================================================ */

/* global mathState, unmountMathShell, hideLessonStage, switchView,
          renderMathRoadmap, _appendIslandUpdate, _mathEsc */

/**
 * Render lesson complete screen.
 * v1 flow: calls complete-lesson to award XP + mark complete.
 * v2 flow: exit_quiz/submit already handled completion — skips to avoid double XP.
 * @tag MATH @tag ACADEMY
 */
async function renderMathComplete() {
    if (!mathState._v2Flow) {
        try {
            await fetch('/api/math/academy/complete-lesson', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grade: mathState.grade, unit: mathState.unit, lesson: mathState.lesson })
            });
        } catch (e) { console.error('complete-lesson failed', e); }
    }

    const stage = document.getElementById('stage');
    if (!stage) return;
    renderMathRoadmap();

    const lessonName = (mathState.lesson || '').replace(/_/g, ' ');
    const pretestPct = Math.round((mathState.pretestScore || 0) / 5 * 100);
    const reviewDate = mathState.spacedReviewDate || '';
    let reviewHtml = '';
    if (reviewDate) {
        const d = new Date(reviewDate);
        const label = isNaN(d.getTime()) ? reviewDate : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        reviewHtml = `<div class="math-complete-review-date">Next review: ${_mathEsc(label)}</div>`;
    }

    const xpEarned = mathState.xpEarned || 0;
    const exitScore = mathState._v2Flow ? mathState.correct : null;
    const midStat = mathState._v2Flow
        ? `<div class="math-complete-stat">
               <div class="math-complete-stat-label">Exit Quiz</div>
               <div class="math-complete-stat-val">${exitScore}/5</div>
               <div class="math-complete-stat-sub">${Math.round((exitScore / 5) * 100)}%</div>
           </div>`
        : `<div class="math-complete-stat">
               <div class="math-complete-stat-label">Rounds</div>
               <div class="math-complete-stat-val">3</div>
               <div class="math-complete-stat-sub">Completed</div>
           </div>`;

    stage.innerHTML = `
        <div class="math-complete">
            <div class="math-complete-hero">
                <div class="math-complete-icon"><i data-lucide="star"></i></div>
                <h2>Lesson Complete!</h2>
                <p>${_mathEsc(lessonName)}</p>
                <div class="math-complete-stats">
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Pre-Test</div>
                        <div class="math-complete-stat-val">${mathState.pretestScore}/5</div>
                        <div class="math-complete-stat-sub">${pretestPct}%</div>
                    </div>
                    ${midStat}
                    <div class="math-complete-stat">
                        <div class="math-complete-stat-label">Mastery</div>
                        <div class="math-complete-stat-val"><i data-lucide="check" style="width:18px;height:18px;stroke-width:2.5"></i></div>
                        <div class="math-complete-stat-sub">Unlocked</div>
                    </div>
                </div>
                ${reviewHtml}
                ${xpEarned > 0 ? `<div class="math-complete-xp">+${xpEarned} XP</div>` : ''}
            </div>
            <div class="math-complete-actions">
                <button class="math-btn-primary" id="math-complete-back-btn">Back to Math</button>
                <div id="math-island-update"></div>
            </div>
        </div>
    `;
    document.getElementById('math-complete-back-btn')
        .addEventListener('click', () => exitMathLesson());
    if (typeof _appendIslandUpdate === 'function') {
        _appendIslandUpdate(document.getElementById('math-island-update'), mathState.islandData ?? null);
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Ocean-zone character pops in to cheer the finished lesson, then fades.
    if (window.IslandGuide && typeof window.IslandGuide.celebrate === 'function') {
        try {
            window.IslandGuide.celebrate('math_lesson', {
                subject: 'math', floating: true, autoHide: true,
            });
        } catch (_) {}
    }
}

/** @tag MATH @tag ACADEMY */
function exitMathLesson() {
    if (typeof unmountMathShell === 'function') unmountMathShell();
    if (typeof hideLessonStage === 'function') hideLessonStage();
    switchView('math');
}
