/* ================================================================
   math-kangaroo.js — Math Kangaroo Practice (set picker)
   Section: Math
   Dependencies: core.js, math-kangaroo-exam.js, math-kangaroo-result.js
   API endpoints: GET /api/math/kangaroo/sets
   ================================================================ */

const kangState = {
    sets: [],
    level: 'ecolier',      // 'pre_ecolier' | 'ecolier' | 'benjamin' | 'cadet' | 'all'
    tab: 'full_test',      // 'full_test' | 'drill' | 'past_paper'
};

const KANG_LEVELS = [
    { key: 'pre_ecolier', label: 'Pre-Écolier (Grades 1-2)' },
    { key: 'ecolier',     label: 'Écolier (Grades 3-4)' },
    { key: 'benjamin',    label: 'Benjamin (Grades 5-6)' },
    { key: 'cadet',       label: 'Cadet (Grades 7-8)' },
];

const KANG_PP_FILTERS = [
    { key: 'all',         label: 'All' },
    { key: 'pre_ecolier', label: 'Pre-Écolier' },
    { key: 'ecolier',     label: 'Écolier' },
    { key: 'benjamin',    label: 'Benjamin' },
    { key: 'cadet',       label: 'Cadet' },
];

// ── Stage helper ───────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
function _kangShowStage() {
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
}

/** @tag MATH @tag KANGAROO */
function _kangEsc(s) {
    return String(s ?? '').replace(/[&<>"']/g, ch => (
        { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]
    ));
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
    const levels = (kangState.tab === 'past_paper') ? KANG_PP_FILTERS : KANG_LEVELS;
    const levelTabs = levels.map(lv => `
        <button class="kang-tab ${lv.key === kangState.level ? 'is-active' : ''}"
                data-level="${lv.key}">${_kangEsc(lv.label)}</button>
    `).join('');
    const subTabs = `
        <button class="kang-subtab ${kangState.tab === 'full_test' ? 'is-active' : ''}" data-tab="full_test">Full Tests</button>
        <button class="kang-subtab ${kangState.tab === 'drill' ? 'is-active' : ''}" data-tab="drill">Topic Drills</button>
        <button class="kang-subtab ${kangState.tab === 'past_paper' ? 'is-active' : ''}" data-tab="past_paper">Past Papers</button>
    `;
    stage.innerHTML = `
        <div class="kang-wrap kang-picker">
            <header class="kang-picker-head">
                <h1 class="kang-title">Math Kangaroo Practice</h1>
                <p class="kang-sub">Choose your level and pick a set.</p>
            </header>
            <nav class="kang-tabs" role="tablist">${levelTabs}</nav>
            <nav class="kang-subtabs" role="tablist">${subTabs}</nav>
            <div class="kang-grid" id="kang-grid"></div>
        </div>
    `;
    stage.querySelectorAll('.kang-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            kangState.level = btn.dataset.level;
            _kangRenderPicker();
        });
    });
    stage.querySelectorAll('.kang-subtab').forEach(btn => {
        btn.addEventListener('click', () => {
            kangState.tab = btn.dataset.tab;
            // When switching to past_paper, reset level to "all"; else default to ecolier
            if (kangState.tab === 'past_paper') kangState.level = 'all';
            else if (kangState.level === 'all') kangState.level = 'ecolier';
            _kangRenderPicker();
        });
    });
    _kangRenderGrid();
}

/** @tag MATH @tag KANGAROO */
function _kangRenderGrid() {
    const grid = document.getElementById('kang-grid');
    if (!grid) return;
    const filtered = kangState.sets.filter(s => {
        const cat = s.category || 'full_test';
        if (cat !== kangState.tab) return false;
        if (kangState.tab === 'past_paper' && kangState.level === 'all') return true;
        return s.level === kangState.level;
    });
    if (kangState.tab === 'past_paper') {
        filtered.sort((a, b) => {
            const yd = (b.source_year || 0) - (a.source_year || 0);
            if (yd !== 0) return yd;
            return String(a.level).localeCompare(String(b.level));
        });
    }
    if (!filtered.length) {
        grid.innerHTML = `<p class="kang-empty">No sets available for this level yet.</p>`;
        return;
    }
    grid.innerHTML = filtered.map(s => _kangCardHtml(s)).join('');
    grid.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.disabled) return;
            const setId = btn.dataset.setId;
            const mode = btn.dataset.action;
            const isPp = btn.dataset.kind === 'past_paper';
            if (isPp && typeof startKangarooPdfExam === 'function') {
                startKangarooPdfExam(setId, mode);
            } else if (typeof startKangarooExam === 'function') {
                startKangarooExam(setId, mode);
            }
        });
    });
}

/** @tag MATH @tag KANGAROO */
function _kangCardHtml(s) {
    const qs = s.total_questions || 0;
    const mins = s.time_limit_minutes || 0;
    const maxPts = s.max_score || 0;
    const isPp = (s.category === 'past_paper');
    const meta = `${qs} questions · ${mins} min`;
    const pct = (s.best_score != null && maxPts)
        ? Math.round(s.best_score * 100 / maxPts) : null;
    const best = (s.best_score != null)
        ? `<div class="kang-card-best">Best: ${s.best_score}/${maxPts}${pct != null ? ` (${pct}%)` : ''}</div>`
        : '';
    const topic = s.drill_topic
        ? `<div class="kang-card-topic">Focus: ${_kangEsc(s.drill_topic.replace(/_/g, ' '))}</div>` : '';
    const country = isPp && s.source_country
        ? _kangEsc(s.source_country === 'International' ? 'IKMC' : s.source_country)
        : '';
    const yearBadge = (isPp && s.source_year)
        ? `<span class="kang-card-year">${_kangEsc(s.source_year)}${country ? ` · ${country}` : ''}</span>`
        : (s.source_year ? `<span class="kang-card-year">${_kangEsc(s.source_year)}</span>` : '');
    const contest = (!isPp && s.source_contest)
        ? `<div class="kang-card-contest">${_kangEsc(s.source_contest)}</div>` : '';
    const levelLine = isPp
        ? `<div class="kang-card-contest">${_kangEsc(s.level_label || '')}${s.grade_range ? ` (Grades ${_kangEsc(s.grade_range)})` : ''}</div>`
        : '';

    let actions = '';
    let warning = '';
    if (isPp) {
        const pdfMissing = (s.pdf_available === false);
        const pending = !!s.answers_pending;
        const disabled = pdfMissing || pending;
        if (pdfMissing) {
            warning = `<div class="kang-card-warning">PDF not available on this device</div>`;
        } else if (pending) {
            warning = `<div class="kang-card-warning">Answer key coming soon</div>`;
        }
        actions = `
            <button class="kang-btn kang-btn-primary" data-action="test" data-kind="past_paper"
                data-set-id="${_kangEsc(s.set_id)}"${disabled ? ' disabled' : ''}>Test Mode</button>
            <button class="kang-btn kang-btn-secondary" data-action="practice" data-kind="past_paper"
                data-set-id="${_kangEsc(s.set_id)}"${disabled ? ' disabled' : ''}>Practice</button>
        `;
    } else {
        actions = `
            <button class="kang-btn kang-btn-primary" data-action="test" data-set-id="${_kangEsc(s.set_id)}">Test Mode</button>
            <button class="kang-btn kang-btn-secondary" data-action="practice" data-set-id="${_kangEsc(s.set_id)}">Practice Mode</button>
        `;
    }

    return `
        <article class="kang-card">
            ${yearBadge}
            <h3 class="kang-card-title">${_kangEsc(s.title)}</h3>
            ${contest}
            ${levelLine}
            <div class="kang-card-meta">${_kangEsc(meta)}${!isPp ? ' · ' + maxPts + ' pts max' : ''}</div>
            ${topic}
            ${best}
            ${warning}
            <div class="kang-card-actions">${actions}</div>
        </article>
    `;
}

// Expose entry
window.startMathKangaroo = startMathKangaroo;
