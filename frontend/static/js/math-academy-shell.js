/* ================================================================
   math-academy-shell.js — Math-mode DOM shell (rail + lesson header)
   Section: Math
   Dependencies: math-academy.js (mathState), math-academy-ui.js (renderMathRoadmap, exitMathLesson)
   API endpoints: none (client-only DOM restructure)

   Adds a `.math-mode` class to `#stage-card` and restructures it into
   a left rail (containing `#roadmap`) + body column (containing a new
   `.math-lesson-header` + the existing `#stage`). Unmount restores the
   original DOM so English stages are unaffected.
   ================================================================ */

/* global mathState */

/**
 * Restructure `#stage-card` for the math lesson layout.
 * Idempotent: safe to call multiple times.
 * @tag MATH @tag ACADEMY
 */
function mountMathShell() {
    const card = document.getElementById('stage-card');
    if (!card) return;
    card.classList.add('math-mode');

    // Already mounted — just refresh the lesson header text
    if (card.querySelector('.math-rail')) {
        renderMathLessonHeader();
        return;
    }

    const stageHeader = card.querySelector('.stage-header');
    const roadmap = document.getElementById('roadmap');
    const stage = document.getElementById('stage');

    const rail = document.createElement('div');
    rail.className = 'math-rail';
    if (roadmap) rail.appendChild(roadmap);

    const body = document.createElement('div');
    body.className = 'math-body';

    const lh = document.createElement('div');
    lh.className = 'math-lesson-header';
    lh.id = 'math-lesson-header';
    body.appendChild(lh);

    if (stage) body.appendChild(stage);

    card.appendChild(rail);
    card.appendChild(body);

    // Hide legacy stage-header but keep it in DOM so unmount can restore
    if (stageHeader) stageHeader.style.display = 'none';

    renderMathLessonHeader();
}

/**
 * Revert `#stage-card` to its original DOM so non-math stages render correctly.
 * @tag MATH @tag ACADEMY
 */
function unmountMathShell() {
    const card = document.getElementById('stage-card');
    if (!card) return;
    card.classList.remove('math-mode');

    const rail = card.querySelector('.math-rail');
    const body = card.querySelector('.math-body');
    const stageHeader = card.querySelector('.stage-header');
    const roadmap = document.getElementById('roadmap');
    const stage = document.getElementById('stage');
    const lh = document.getElementById('math-lesson-header');

    if (stageHeader) {
        stageHeader.style.display = '';
        if (roadmap) stageHeader.insertBefore(roadmap, stageHeader.firstChild);
    }
    if (lh) lh.remove();
    if (stage) card.appendChild(stage);
    if (rail) rail.remove();
    if (body) body.remove();
}

/**
 * Populate the lesson header with unit / lesson / Exit button.
 * Reads from `mathState`; called on mount and whenever the stage changes.
 * @tag MATH @tag ACADEMY
 */
function renderMathLessonHeader() {
    const el = document.getElementById('math-lesson-header');
    if (!el) return;

    const gradeRaw = String(mathState.grade || '');
    const gradeNum = gradeRaw.replace(/^grade[_-]?/i, '');
    const gradeDisplay = gradeNum ? `Grade ${gradeNum}` : '';
    const unit = (mathState.unit || '').replace(/_/g, ' ');
    const lesson = (mathState.lesson || '').replace(/_/g, ' ');
    const eyebrow = [gradeDisplay, unit].filter(Boolean).join(' \u00B7 ');

    el.innerHTML = `
        <div class="math-lh-info">
            <div class="math-lh-eyebrow">${_escShell(eyebrow)}</div>
            <div class="math-lh-title">${_escShell(lesson)}</div>
        </div>
        <button class="math-lh-exit" type="button" id="math-lh-exit-btn">Exit</button>
    `;

    const exitBtn = document.getElementById('math-lh-exit-btn');
    if (exitBtn && typeof exitMathLesson === 'function') {
        exitBtn.addEventListener('click', exitMathLesson);
    }
}

/** @tag MATH @tag ACADEMY */
function _escShell(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

// ── Rail renderer (8-stage vertical pill list) ──────────────

/**
 * Render the math stage rail into `#roadmap`. Called by math-academy.js
 * and after every stage transition.
 * @tag MATH @tag NAVIGATION
 */
function renderMathRoadmap() {
    const rm = document.getElementById('roadmap');
    if (!rm) return;
    rm.innerHTML = '';

    const rail = [
        { key: 'pretest', label: 'Pretest' },
        { key: 'learn', label: 'Learn' },
        { key: 'try', label: 'Try' },
        { key: 'practice_r1', label: 'R1' },
        { key: 'practice_r2', label: 'R2' },
        { key: 'practice_r3', label: 'R3' },
        { key: 'wrong_review', label: 'Review' },
        { key: 'complete', label: 'Done' },
    ];
    const currentIdx = rail.findIndex(s => s.key === mathState.stage);

    rail.forEach((s, i) => {
        const done = currentIdx >= 0 && i < currentIdx;
        const current = i === currentIdx;

        const item = document.createElement('div');
        item.className = 'math-rail-item';
        item.dataset.key = s.key;
        if (done) item.classList.add('done');
        if (current) item.classList.add('current');
        if (!done && !current) item.classList.add('locked');

        const badge = document.createElement('div');
        badge.className = 'math-rail-badge';
        badge.textContent = done ? '\u2713'
            : (s.key === 'complete' && current) ? '\u2713'
            : String(i + 1);
        item.appendChild(badge);

        const label = document.createElement('div');
        label.className = 'math-rail-label';
        label.textContent = s.label;
        item.appendChild(label);

        if (s.key === 'pretest' && (done || (current && mathState.correct > 0))) {
            const meta = document.createElement('div');
            meta.className = 'math-rail-meta';
            const score = done ? mathState.pretestScore : mathState.correct;
            meta.textContent = `${score}/5`;
            item.appendChild(meta);
        }

        rm.appendChild(item);

        if (i < rail.length - 1) {
            const conn = document.createElement('div');
            conn.className = 'math-rail-connector' + (done ? ' done' : '');
            rm.appendChild(conn);
        }
    });

    const fill = document.getElementById('top-progress-fill');
    const pct = document.getElementById('progress-pct');
    if (fill && mathState.problems && mathState.problems.length > 0) {
        const p = Math.round(mathState.currentIdx / mathState.problems.length * 100);
        fill.style.width = p + '%';
        if (pct) pct.textContent = p + '%';
    }
}
