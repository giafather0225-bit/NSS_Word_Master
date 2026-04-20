/* ================================================================
   math-kangaroo.js — Math Kangaroo Practice (set picker)
   Section: Math
   Dependencies: core.js, math-kangaroo-exam.js, math-kangaroo-result.js
   API endpoints: GET /api/math/kangaroo/sets
   ================================================================ */

const kangState = {
    sets: [],
    level: 'ecolier',      // 'pre_ecolier' | 'ecolier' | 'benjamin'
    tab: 'full_test',      // 'full_test' | 'drill'
};

const KANG_LEVELS = [
    { key: 'pre_ecolier', label: 'Level 1-2 (Pre-Ecolier)' },
    { key: 'ecolier',     label: 'Level 3-4 (Ecolier)' },
    { key: 'benjamin',    label: 'Level 5-6 (Benjamin)' },
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
                data-level="${lv.key}">${_kangEsc(lv.label)}</button>
    `).join('');
    const subTabs = `
        <button class="kang-subtab ${kangState.tab === 'full_test' ? 'is-active' : ''}" data-tab="full_test">Full Tests</button>
        <button class="kang-subtab ${kangState.tab === 'drill' ? 'is-active' : ''}" data-tab="drill">Topic Drills</button>
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
            _kangRenderPicker();
        });
    });
    _kangRenderGrid();
}

/** @tag MATH @tag KANGAROO */
function _kangRenderGrid() {
    const grid = document.getElementById('kang-grid');
    if (!grid) return;
    const filtered = kangState.sets.filter(s =>
        (s.level === kangState.level) && ((s.category || 'full_test') === kangState.tab)
    );
    if (!filtered.length) {
        if (kangState.tab === 'drill') {
            grid.innerHTML = `<p class="kang-empty">Coming in Phase 4.</p>`;
        } else {
            grid.innerHTML = `<p class="kang-empty">No sets available for this level yet.</p>`;
        }
        return;
    }
    grid.innerHTML = filtered.map(s => _kangCardHtml(s)).join('');
    grid.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', () => {
            const setId = btn.dataset.setId;
            const mode = btn.dataset.action;
            if (typeof startKangarooExam === 'function') {
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
    const meta = `${qs} Qs · ${mins} min · ${maxPts} pts max`;
    const best = (s.best_score != null)
        ? `<div class="kang-card-best">Best: ${s.best_score}/${maxPts}</div>` : '';
    return `
        <article class="kang-card">
            <h3 class="kang-card-title">${_kangEsc(s.title)}</h3>
            <div class="kang-card-meta">${_kangEsc(meta)}</div>
            ${best}
            <div class="kang-card-actions">
                <button class="kang-btn kang-btn-primary" data-action="test" data-set-id="${_kangEsc(s.set_id)}">Test Mode</button>
                <button class="kang-btn kang-btn-secondary" data-action="practice" data-set-id="${_kangEsc(s.set_id)}">Practice Mode</button>
            </div>
        </article>
    `;
}

// Expose entry
window.startMathKangaroo = startMathKangaroo;
