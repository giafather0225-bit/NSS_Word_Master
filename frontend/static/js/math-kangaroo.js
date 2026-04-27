/* ================================================================
   math-kangaroo.js — Math Kangaroo Practice (set picker)
   Section: Math
   Dependencies: core.js, math-kangaroo-exam.js, math-kangaroo-pdf-exam.js
   API endpoints: GET /api/math/kangaroo/sets
   ================================================================ */

const kangState = {
    sets: [],
    level: 'ecolier',
};

const KANG_LEVELS = [
    { key: 'pre_ecolier', label: 'Pre-Écolier', grades: '1–2' },
    { key: 'ecolier',     label: 'Écolier',     grades: '3–4' },
    { key: 'benjamin',    label: 'Benjamin',     grades: '5–6' },
    { key: 'cadet',       label: 'Cadet',        grades: '7–8' },
    { key: 'junior',      label: 'Junior',       grades: '9–10' },
    { key: 'student',     label: 'Student',      grades: '11–12' },
];

/** Map raw source_country strings → short display labels */
function _kangSrcLabel(country) {
    if (!country) return '';
    if (country.startsWith('International')) return 'IKMC';
    if (country.startsWith('Cyprus')) return 'Cyprus';
    return country; // India, Lebanon, USA, etc.
}

// ── Stage helper ───────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
function _kangShowStage() {
    const stageCard = document.getElementById('stage-card');
    const idleWrap  = document.getElementById('idle-wrapper');
    const homeDash  = document.getElementById('home-dashboard');
    const topBar    = document.querySelector('.top-bar');
    if (homeDash)  homeDash.style.display  = 'none';
    if (idleWrap)  idleWrap.style.display  = 'none';
    if (stageCard) { stageCard.classList.remove('hidden'); stageCard.style.display = ''; }
    if (topBar)    topBar.style.display    = 'none';
    const sidebar = document.getElementById('sidebar');
    if (sidebar) { sidebar.classList.add('collapsed'); localStorage.setItem('sb_collapsed', '1'); }
}

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
async function startMathKangaroo() {
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
        <button class="kang-lvl-tab ${lv.key === kangState.level ? 'is-active' : ''}"
                data-level="${_mathEscAttr(lv.key)}">
            <span class="kang-lvl-name">${_mathEsc(lv.label)}</span>
            <span class="kang-lvl-grades">Grades ${_mathEsc(lv.grades)}</span>
        </button>
    `).join('');

    stage.innerHTML = `
        <div class="kang-wrap kang-picker">
            <header class="kang-picker-head">
                <div class="kang-picker-icon">
                    <i data-lucide="award" style="width:26px;height:26px;stroke-width:1.5"></i>
                </div>
                <div>
                    <h1 class="kang-title">Math Kangaroo</h1>
                    <p class="kang-sub">Past competition problems — choose your level</p>
                </div>
            </header>
            <div class="kang-scoring-rules">
                <i data-lucide="info" style="width:13px;height:13px;stroke-width:2;flex-shrink:0"></i>
                <span>Section 1 = <strong>3 pts</strong> &nbsp;·&nbsp; Section 2 = <strong>4 pts</strong> &nbsp;·&nbsp; Section 3 = <strong>5 pts</strong></span>
                <span class="kang-rules-sep">|</span>
                <span>Wrong = <strong>&minus;¼ pt</strong> &nbsp;·&nbsp; Blank = <strong>0 pts</strong></span>
            </div>
            <nav class="kang-lvl-tabs" role="tablist">${levelTabs}</nav>
            <div class="kang-grid" id="kang-grid"></div>
        </div>`;

    if (typeof lucide !== 'undefined') lucide.createIcons();

    stage.querySelectorAll('.kang-lvl-tab').forEach(btn => {
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
        grid.innerHTML = `<p class="kang-empty">No sets available for this level yet.</p>`;
        return;
    }
    grid.innerHTML = filtered.map(s => _kangCardHtml(s)).join('');
    grid.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.disabled) return;
            const setId = btn.dataset.setId;
            const mode  = btn.dataset.action;
            if (typeof startKangarooPdfExam === 'function') {
                startKangarooPdfExam(setId, mode);
            } else if (typeof startKangarooExam === 'function') {
                startKangarooExam(setId, mode);
            }
        });
    });
}

/** @tag MATH @tag KANGAROO */
function _kangCardHtml(s) {
    const src      = _kangSrcLabel(s.source_country);
    const year     = s.source_year || '';
    const qs       = s.total_questions || 0;
    const mins     = s.time_limit_minutes || 0;
    const maxPts   = s.max_score || 0;
    const pct      = (s.best_score != null && maxPts)
        ? Math.round(s.best_score * 100 / maxPts) : null;
    const bestHtml = s.best_score != null
        ? `<div class="kang-card-best">
               <i data-lucide="star" style="width:11px;height:11px;stroke-width:2;vertical-align:-1px"></i>
               Best: ${s.best_score}/${maxPts}${pct != null ? ` (${pct}%)` : ''}
           </div>` : '';

    const pdfMissing     = (s.pdf_available === false);
    const answersPending = !!s.answers_pending;
    const disabled       = pdfMissing || answersPending;
    const warningHtml    = pdfMissing
        ? `<div class="kang-card-warning">PDF not on this device</div>`
        : answersPending
        ? `<div class="kang-card-warning">Answer key coming soon</div>` : '';

    return `
        <article class="kang-card">
            <div class="kang-card-top">
                ${year ? `<span class="kang-card-year">${_mathEsc(year)}</span>` : ''}
                ${src  ? `<span class="kang-card-source">${_mathEsc(src)}</span>` : ''}
            </div>
            <h3 class="kang-card-title">${_mathEsc(s.title)}</h3>
            <div class="kang-card-meta">${qs} questions &middot; ${mins} min &middot; ${maxPts} pts max</div>
            ${bestHtml}
            ${warningHtml}
            <div class="kang-card-actions">
                <button class="kang-btn kang-btn-primary" data-action="test"
                        data-set-id="${_mathEscAttr(s.set_id)}"${disabled ? ' disabled' : ''}>
                    Test Mode
                </button>
                <button class="kang-btn kang-btn-ghost" data-action="practice"
                        data-set-id="${_mathEscAttr(s.set_id)}"${disabled ? ' disabled' : ''}>
                    Practice
                </button>
            </div>
        </article>`;
}

window.startMathKangaroo = startMathKangaroo;
