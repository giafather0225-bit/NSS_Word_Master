/* ================================================================
   math-academy-shell.js — Math-mode DOM shell (sidebar + lesson header)
   Section: Math
   Dependencies: math-academy.js (mathState), math-academy-ui.js (exitMathLesson)
   API endpoints: none (client-only DOM restructure)

   Restructures #stage-card into a left sidebar rail (200px, stage progress)
   + right body (lesson header + #stage). Unmount restores DOM for English stages.

   Also exports showLessonStage() / hideLessonStage() — the single entry
   point all math sub-flows (academy, fluency, glossary, kangaroo, placement,
   daily, review) use when entering / leaving the shared #stage-card chrome.
   Cross-view container visibility is handled by CSS (see main-idle.css).
   ================================================================ */

/* global mathState */

// ── Shared stage chrome helpers ─────────────────────────────

/**
 * Show the shared lesson stage chrome (#stage-card + .top-bar) and hide
 * the math-idle landing card. Cross-view hides (home-dashboard, idle-wrapper)
 * are CSS-driven, so JS only manages the in-math sub-state here.
 * Idempotent. Pair with hideLessonStage() on exit.
 * @tag MATH @tag NAVIGATION
 */
function showLessonStage({ collapseSidebar = true } = {}) {
    const stageCard = document.getElementById('stage-card');
    const topBar    = document.querySelector('.top-bar');
    const mathIdle  = document.getElementById('math-idle-wrapper');

    if (mathIdle)  mathIdle.style.display = 'none';
    if (stageCard) {
        stageCard.classList.remove('hidden');
        stageCard.style.display = '';
    }
    if (topBar) topBar.style.display = '';

    if (collapseSidebar) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.add('collapsed');
            localStorage.setItem('sb_collapsed', '1');
        }
    }
}

/**
 * Hide the lesson stage chrome and restore the math-idle landing card.
 * @tag MATH @tag NAVIGATION
 */
function hideLessonStage() {
    const stageCard = document.getElementById('stage-card');
    const mathIdle  = document.getElementById('math-idle-wrapper');
    if (stageCard) {
        stageCard.classList.add('hidden');
        stageCard.style.display = 'none';
    }
    if (mathIdle) mathIdle.style.display = '';
    // Math EXIT: restore sidebar + clear persisted state
    const _sb = document.getElementById('sidebar');
    if (_sb) _sb.classList.remove('collapsed');
    localStorage.removeItem('sb_collapsed');
}

/**
 * Restructure `#stage-card` for the math lesson layout.
 * Idempotent: safe to call multiple times.
 * @tag MATH @tag ACADEMY
 */
function mountMathShell() {
    const card = document.getElementById('stage-card');
    if (!card) return;
    card.classList.add('math-mode');

    if (card.querySelector('.math-rail')) {
        renderMathLessonHeader();
        return;
    }

    const stageHeader = card.querySelector('.stage-header');
    const roadmap = document.getElementById('roadmap');
    const stage = document.getElementById('stage');

    const rail = document.createElement('div');
    rail.className = 'math-rail';

    const sectionLabel = document.createElement('div');
    sectionLabel.className = 'math-rail-section-label';
    sectionLabel.textContent = 'Lesson Progress';
    rail.appendChild(sectionLabel);

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
 * Populate the lesson header with breadcrumb + title + progress + Exit.
 * @tag MATH @tag ACADEMY
 */
function renderMathLessonHeader() {
    const el = document.getElementById('math-lesson-header');
    if (!el) return;

    const gradeRaw = String(mathState.grade || '');
    const gradeNum = gradeRaw.replace(/^grade[_-]?/i, '');
    const gradeDisplay = gradeNum ? `Grade ${gradeNum}` : 'Math';
    const unit = (mathState.unit || '').replace(/_/g, ' ');
    const lesson = (mathState.lesson || '').replace(/_/g, ' ');
    const eyebrow = [gradeDisplay, unit].filter(Boolean).join(' · ');

    const pct = _shellProgressPct();

    el.innerHTML = `
        <div class="math-lh-info">
            <div class="math-lh-eyebrow">${_escShell(eyebrow)}</div>
            <div class="math-lh-title">${_escShell(lesson)}</div>
        </div>
        <div class="math-lh-progress">
            <div class="math-lh-progress-bar">
                <div class="math-lh-progress-fill" style="width:${pct}%"></div>
            </div>
            <span class="math-lh-progress-pct">${pct}%</span>
        </div>
        <button class="math-lh-exit" type="button" id="math-lh-exit-btn">Exit</button>
    `;

    const exitBtn = document.getElementById('math-lh-exit-btn');
    if (exitBtn && typeof exitMathLesson === 'function') {
        exitBtn.addEventListener('click', exitMathLesson);
    }
}

/** @tag MATH */
function _shellProgressPct() {
    if (!mathState.problems || mathState.problems.length === 0) return 0;
    return Math.round((mathState.currentIdx / mathState.problems.length) * 100);
}

/** @tag MATH */
function _escShell(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

// ── Rail renderer (vertical stage list with horizontal items) ──

/**
 * Render the math stage rail into `#roadmap`.
 * Called by math-academy.js and after every stage transition.
 * @tag MATH @tag NAVIGATION
 */
function renderMathRoadmap() {
    const rm = document.getElementById('roadmap');
    if (!rm) return;
    rm.innerHTML = '';

    const stages = [
        { key: 'pretest',     label: 'Pretest',   desc: 'Check what you know' },
        { key: 'learn',       label: 'Learn',     desc: 'Study the concept' },
        { key: 'try',         label: 'Try It',    desc: 'Practice with help' },
        { key: 'practice_r1', label: 'Round 1',   desc: 'Practice problems' },
        { key: 'practice_r2', label: 'Round 2',   desc: 'More practice' },
        { key: 'practice_r3', label: 'Round 3',   desc: 'Challenge round' },
        { key: 'wrong_review',label: 'Review',    desc: 'Fix mistakes' },
        { key: 'complete',    label: 'Complete',  desc: 'Lesson done' },
    ];

    const currentIdx = stages.findIndex(s => s.key === mathState.stage);

    stages.forEach((s, i) => {
        const done    = currentIdx >= 0 && i < currentIdx;
        const current = i === currentIdx;

        // connector above each item (except the first)
        if (i > 0) {
            const conn = document.createElement('div');
            conn.className = 'math-rail-connector' + (done || (current && i > 0) ? ' done' : '');
            rm.appendChild(conn);
        }

        const item = document.createElement('div');
        item.className = 'math-rail-item';
        item.dataset.key = s.key;
        if (done)    item.classList.add('done');
        if (current) item.classList.add('current');
        if (!done && !current) item.classList.add('locked');

        // Badge (circle with number or checkmark)
        const badge = document.createElement('div');
        badge.className = 'math-rail-badge';
        if (done) {
            badge.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
        } else if (s.key === 'complete' && current) {
            badge.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
        } else {
            badge.textContent = String(i + 1);
        }
        item.appendChild(badge);

        // Label + optional meta
        const labelWrap = document.createElement('div');
        labelWrap.className = 'math-rail-label-wrap';

        const label = document.createElement('div');
        label.className = 'math-rail-label';
        label.textContent = s.label;
        labelWrap.appendChild(label);

        if (s.key === 'pretest' && (done || (current && mathState.correct > 0))) {
            const meta = document.createElement('div');
            meta.className = 'math-rail-meta';
            const score = done ? (mathState.pretestScore ?? mathState.correct) : mathState.correct;
            meta.textContent = `${score} / 5`;
            labelWrap.appendChild(meta);
        }

        item.appendChild(labelWrap);
        rm.appendChild(item);
    });

    // Sync top progress bar (used elsewhere in the app)
    const fill = document.getElementById('top-progress-fill');
    const pct  = document.getElementById('progress-pct');
    const p    = _shellProgressPct();
    if (fill) fill.style.width = p + '%';
    if (pct)  pct.textContent  = p + '%';

    // Refresh header progress fill too
    const hFill = document.querySelector('.math-lh-progress-fill');
    const hPct  = document.querySelector('.math-lh-progress-pct');
    if (hFill) hFill.style.width = p + '%';
    if (hPct)  hPct.textContent  = p + '%';
}
