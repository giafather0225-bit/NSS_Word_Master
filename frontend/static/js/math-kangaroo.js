/* ================================================================
   math-kangaroo.js — Math Kangaroo Past Papers Picker
   Section: Math
   Dependencies: core.js, math-kangaroo-exam.js, math-kangaroo-result.js
   API endpoints: GET /api/math/kangaroo/sets
   ================================================================ */

const kangState = {
    sets: [],
    level: 'ecolier',  // 'pre_ecolier' | 'ecolier' | 'benjamin' | 'cadet' | 'junior' | 'student'
};

// All 6 competition levels in order
const KANG_LEVELS = [
    { key: 'pre_ecolier', label: 'Pre-Écolier',  sub: 'Gr 1–2' },
    { key: 'ecolier',     label: 'Écolier',       sub: 'Gr 3–4' },
    { key: 'benjamin',    label: 'Benjamin',       sub: 'Gr 5–6' },
    { key: 'cadet',       label: 'Cadet',          sub: 'Gr 7–8' },
    { key: 'junior',      label: 'Junior',         sub: 'Gr 9–10' },
    { key: 'student',     label: 'Student',        sub: 'Gr 11–12' },
];

// ── Stage helper ───────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
function _kangShowStage() {
    if (typeof showLessonStage === 'function') showLessonStage();
}

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
async function startMathKangaroo() {
    // Clear any running exam timer before entering the set picker
    if (typeof examState !== 'undefined' && examState.timerHandle) {
        clearInterval(examState.timerHandle);
        examState.timerHandle = null;
    }
    _kangShowStage();
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="kang-wrap"><p class="kang-loading">Loading sets…</p></div>`;
    try {
        const res = await fetch('/api/math/kangaroo/sets');
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        kangState.sets = Array.isArray(data.sets) ? data.sets : [];
        _kangRenderPicker();
    } catch (err) {
        console.warn('[kangaroo] load failed', err);
        stage.innerHTML = `
            <div class="kang-wrap">
                <p class="kang-error">Hmm, that didn't load.</p>
                <button class="kang-btn kang-btn-primary" onclick="startMathKangaroo()">↻ Try Again</button>
            </div>`;
    }
}

// ── Picker UI ──────────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
function _kangRenderPicker() {
    const stage = document.getElementById('stage');
    if (!stage) return;

    const levelTabs = KANG_LEVELS.map(lv => `
        <button class="kang-tab ${lv.key === kangState.level ? 'is-active' : ''}"
                data-level="${lv.key}">
            ${_mathEsc(lv.label)}
            <span class="kang-tab-sub">${_mathEsc(lv.sub)}</span>
        </button>
    `).join('');

    stage.innerHTML = `
        <div class="kang-wrap kang-picker">
            <header class="kang-picker-head">
                <h1 class="kang-title">Math Kangaroo</h1>
                <p class="kang-sub">Past Papers — pick your level</p>
            </header>
            <nav class="kang-tabs" role="tablist">${levelTabs}</nav>
            <div class="kang-grid" id="kang-grid"></div>
        </div>
    `;

    stage.querySelectorAll('.kang-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            kangState.level = btn.dataset.level;
            _kangRenderPicker();
        });
    });

    _kangRenderGrid();
}

/** @tag MATH @tag KANGAROO */
function _kangRenderGrid() {
    const grid = document.getElementById('kang-grid');
    if (!grid) return;

    const filtered = kangState.sets
        .filter(s => s.level === kangState.level)
        .sort((a, b) => (b.source_year || 0) - (a.source_year || 0));

    if (!filtered.length) {
        grid.innerHTML = `<p class="kang-empty">No past papers available for this level yet.</p>`;
        return;
    }

    grid.innerHTML = filtered.map(s => _kangCardHtml(s)).join('');

    grid.querySelectorAll('[data-action="start"]').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.disabled) return;
            const setId = btn.dataset.setId;
            if (typeof startKangarooPdfExam === 'function') {
                startKangarooPdfExam(setId);
            } else if (typeof startKangarooExam === 'function') {
                startKangarooExam(setId);
            }
        });
    });
}

/** @tag MATH @tag KANGAROO */
function _kangCardHtml(s) {
    const qs   = s.total_questions || 0;
    const mins = s.time_limit_minutes || 0;
    const maxPts = s.max_score || 0;

    const pct = (s.best_score != null && maxPts)
        ? Math.round(s.best_score * 100 / maxPts) : null;
    const best = (s.best_score != null)
        ? `<div class="kang-card-best">Best: ${s.best_score}/${maxPts}${pct != null ? ` (${pct}%)` : ''}</div>`
        : '';

    const pdfMissing = (s.pdf_available === false);
    const pending    = !!s.answers_pending;
    const disabled   = pdfMissing || pending;

    let warning = '';
    if (pdfMissing) {
        warning = `<div class="kang-card-warning">PDF not available on this device</div>`;
    } else if (pending) {
        warning = `<div class="kang-card-warning">Answer key coming soon</div>`;
    }

    // Badges row: year + competition
    const yearBadge = s.source_year
        ? `<span class="kang-card-year">${_mathEsc(s.source_year)}</span>` : '';
    const compBadge = s.competition
        ? `<span class="kang-card-competition">${_mathEsc(s.competition)}</span>` : '';

    // Level label line
    const levelLine = s.level_label
        ? `<div class="kang-card-contest">${_mathEsc(s.level_label)}${s.grade_range ? ` · Gr ${_mathEsc(s.grade_range)}` : ''}</div>`
        : '';

    const actions = `
        <button class="kang-btn kang-btn-primary" data-action="start"
            data-set-id="${_mathEsc(s.set_id)}"${disabled ? ' disabled' : ''}>Start</button>
    `;

    return `
        <article class="kang-card">
            <div class="kang-card-badges">${yearBadge}${compBadge}</div>
            <h3 class="kang-card-title">${_mathEsc(s.title)}</h3>
            ${levelLine}
            <div class="kang-card-meta">${qs} questions · ${mins} min · ${maxPts} pts</div>
            ${best}
            ${warning}
            <div class="kang-card-actions">${actions}</div>
        </article>
    `;
}

// Expose entry
window.startMathKangaroo = startMathKangaroo;
