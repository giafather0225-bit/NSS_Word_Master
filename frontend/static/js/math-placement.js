/* ================================================================
   math-placement.js — Math Placement Test UI
   Section: Math
   Dependencies: core.js
   API endpoints: /api/math/placement/status, /api/math/placement/start,
                  /api/math/placement/save, /api/math/placement/results
   ================================================================ */

// ── State ──────────────────────────────────────────────────

const placementState = {
    domains: [],      // [{domain, label, questions}]
    answers: {},      // {domain: {qid: userAnswer}}
    dIdx: 0,
    qIdx: 0,
};

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
async function startPlacementTest() {
    _showMathStageP();
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-wrong-review"><p>Loading placement test…</p></div>`;
    try {
        const res = await fetch('/api/math/placement/start');
        const data = await res.json();
        placementState.domains = data.domains || [];
        placementState.answers = {};
        placementState.domains.forEach(d => { placementState.answers[d.domain] = {}; });
        placementState.dIdx = 0;
        placementState.qIdx = 0;
        _renderPlacementIntro();
    } catch (err) {
        console.warn('[placement] start failed', err);
        stage.innerHTML = `<div class="math-wrong-review"><p>Could not load placement test.</p></div>`;
    }
}

/** @tag MATH @tag PLACEMENT */
function _showMathStageP() {
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

// ── Intro ──────────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
function _renderPlacementIntro() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const total = placementState.domains.reduce((n, d) => n + d.questions.length, 0);
    stage.innerHTML = `
        <div class="math-round-summary">
            <div class="math-summary-icon">🎯</div>
            <h2 class="math-summary-title">Placement Test</h2>
            <p class="math-fluency-sub">
                ${placementState.domains.length} domains · ${total} questions.<br>
                Answer what you can — skip if unsure (leave blank).
            </p>
            <div class="math-summary-weak">
                <div class="math-summary-weak-label">Domains</div>
                <div class="math-summary-weak-list">
                    ${placementState.domains.map(d =>
                        `<span class="math-summary-chip">${_escPl(d.label)}</span>`
                    ).join('')}
                </div>
            </div>
            <button class="math-btn-primary math-summary-cta" id="math-placement-begin">Begin</button>
        </div>
    `;
    document.getElementById('math-placement-begin').addEventListener('click', () => _renderPlacementQ());
}

// ── Question ───────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
function _renderPlacementQ() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const d = placementState.domains[placementState.dIdx];
    if (!d) { _submitPlacement(); return; }
    const q = d.questions[placementState.qIdx];
    if (!q) {
        placementState.dIdx += 1;
        placementState.qIdx = 0;
        _renderPlacementQ();
        return;
    }

    const totalInDomain = d.questions.length;
    const totalDomains = placementState.domains.length;
    const savedAnswer = placementState.answers[d.domain][q.id] || '';

    const body = q.type === 'mc'
        ? `<div class="math-mc-grid">
               ${(q.options || []).map((o, i) => `
                   <button class="math-mc-btn" data-val="${_escAttrPl(o)}">
                       <span class="math-mc-letter">${String.fromCharCode(65 + i)}</span>
                       <span class="math-mc-text">${_escPl(o)}</span>
                   </button>
               `).join('')}
           </div>`
        : `<div class="math-input-group">
               <input type="text" class="math-input-field" id="math-placement-input"
                      placeholder="Type your answer (or skip)…"
                      value="${_escAttrPl(savedAnswer)}" autocomplete="off">
               <button class="math-btn-primary" id="math-placement-submit">Next</button>
           </div>`;

    stage.innerHTML = `
        <div class="math-problem-wrap">
            <div class="math-problem-header">
                <span class="math-problem-stage">🎯 Placement · ${_escPl(d.label)}</span>
                <span class="math-problem-counter">
                    D${placementState.dIdx + 1}/${totalDomains} · Q${placementState.qIdx + 1}/${totalInDomain}
                </span>
            </div>
            <div class="math-problem-card">
                <div class="math-review-origin">Grade ${_escPl(q.grade)}</div>
                <div class="math-problem-question">${_escPl(q.question)}</div>
                <div class="math-problem-body">${body}</div>
                <div class="math-fluency-actions" style="justify-content:space-between;">
                    <button class="math-btn-ghost" id="math-placement-skip">Skip</button>
                    ${q.type === 'mc' ? '' : ''}
                </div>
            </div>
        </div>
    `;

    if (q.type === 'mc') {
        stage.querySelectorAll('.math-mc-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                placementState.answers[d.domain][q.id] = btn.dataset.val;
                _advance();
            });
        });
    } else {
        const input = document.getElementById('math-placement-input');
        const submit = document.getElementById('math-placement-submit');
        const doSubmit = () => {
            placementState.answers[d.domain][q.id] = (input.value || '').trim();
            _advance();
        };
        submit.addEventListener('click', doSubmit);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSubmit(); });
        setTimeout(() => input.focus(), 30);
    }

    document.getElementById('math-placement-skip').addEventListener('click', () => {
        placementState.answers[d.domain][q.id] = '';
        _advance();
    });
}

function _advance() {
    const d = placementState.domains[placementState.dIdx];
    placementState.qIdx += 1;
    if (placementState.qIdx >= d.questions.length) {
        placementState.dIdx += 1;
        placementState.qIdx = 0;
    }
    if (placementState.dIdx >= placementState.domains.length) {
        _submitPlacement();
    } else {
        _renderPlacementQ();
    }
}

// ── Submit ─────────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
async function _submitPlacement() {
    const stage = document.getElementById('stage');
    if (stage) stage.innerHTML = `<div class="math-wrong-review"><p>Scoring your test…</p></div>`;
    try {
        const payload = {
            results: placementState.domains.map(d => ({
                domain: d.domain,
                answers: placementState.answers[d.domain] || {},
            })),
        };
        const res = await fetch('/api/math/placement/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        _renderPlacementResults(data);
        if (typeof loadMathPlacementStatus === 'function') loadMathPlacementStatus();
    } catch (err) {
        console.warn('[placement] save failed', err);
        if (stage) stage.innerHTML = `<div class="math-wrong-review"><p>Could not save results.</p></div>`;
    }
}

// ── Results ────────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
function _renderPlacementResults(data) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const suggested = data.suggested_grade || 'G3';
    const rows = (data.results || []).map(r => {
        const pct = r.total_questions ? Math.round((r.raw_score / r.total_questions) * 100) : 0;
        return `
            <div class="math-placement-row">
                <div class="math-placement-row-label">${_escPl(r.label)}</div>
                <div class="math-placement-row-meta">
                    <span class="math-summary-chip">${_escPl(r.estimated_grade)}</span>
                    <span class="math-placement-row-score">${r.raw_score}/${r.total_questions} · ${pct}%</span>
                </div>
            </div>
        `;
    }).join('');

    stage.innerHTML = `
        <div class="math-round-summary">
            <div class="math-summary-icon">🎯</div>
            <h2 class="math-summary-title">Placement Complete</h2>
            <div class="math-summary-score">${_escPl(suggested)}</div>
            <div class="math-summary-pct">Suggested starting grade</div>
            <div class="math-placement-results">${rows}</div>
            <div class="math-fluency-actions">
                <button class="math-btn-ghost" id="math-placement-back">Back</button>
                <button class="math-btn-primary" id="math-placement-go">Go to ${_escPl(suggested)} Academy</button>
            </div>
        </div>
    `;
    document.getElementById('math-placement-back').addEventListener('click', () => {
        if (typeof switchView === 'function') switchView('math');
        const stageCard = document.getElementById('stage-card');
        if (stageCard) stageCard.style.display = 'none';
        const idleWrap = document.getElementById('idle-wrapper');
        if (idleWrap) idleWrap.style.display = '';
    });
    document.getElementById('math-placement-go').addEventListener('click', () => {
        if (typeof switchView === 'function') switchView('math');
        const stageCard = document.getElementById('stage-card');
        if (stageCard) stageCard.style.display = 'none';
        const idleWrap = document.getElementById('idle-wrapper');
        if (idleWrap) idleWrap.style.display = '';
        // Pre-select grade dropdown
        const sel = document.getElementById('math-grade-select');
        if (sel) {
            setTimeout(() => {
                const opt = Array.from(sel.options).find(o => o.value === suggested);
                if (opt) {
                    sel.value = suggested;
                    sel.dispatchEvent(new Event('change'));
                }
            }, 300);
        }
    });
}

// ── Sidebar status ─────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
async function loadMathPlacementStatus() {
    try {
        const res = await fetch('/api/math/placement/results');
        if (!res.ok) {
            const s = document.getElementById('math-placement-status');
            const g = document.getElementById('math-placement-suggested');
            if (s) s.textContent = 'Not taken';
            if (g) g.textContent = '—';
            return;
        }
        const data = await res.json();
        const results = data.results || [];
        const grades = ['G2','G3','G4','G5','G6'];
        const lowest = results.length
            ? results.reduce((a, b) => grades.indexOf(a.estimated_grade) < grades.indexOf(b.estimated_grade) ? a : b).estimated_grade
            : '—';
        const s = document.getElementById('math-placement-status');
        const g = document.getElementById('math-placement-suggested');
        if (s) s.textContent = results.length ? `${results.length} domains` : 'Not taken';
        if (g) g.textContent = lowest;
        const btn = document.getElementById('math-btn-placement');
        if (btn && results.length) btn.textContent = 'Retake';
    } catch (_) { /* silent */ }
}

// ── Wiring ─────────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
(function wirePlacement() {
    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('math-btn-placement');
        if (btn) btn.addEventListener('click', () => startPlacementTest());
    });
})();

// Hook into existing loadMathSidebarStatus if available
if (typeof window !== 'undefined') {
    const prev = window.loadMathSidebarStatus;
    window.loadMathSidebarStatus = function () {
        if (typeof prev === 'function') try { prev(); } catch (_) {}
        loadMathPlacementStatus();
    };
}

// ── Escape helpers ─────────────────────────────────────────

function _escPl(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
}

function _escAttrPl(str) {
    return String(str == null ? '' : str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
