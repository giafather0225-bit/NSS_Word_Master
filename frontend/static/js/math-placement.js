/* ================================================================
   math-placement.js — Math Placement Test UI
   Section: Math
   Dependencies: core.js, math-placement-results.js (_renderPlacementResults)
   API endpoints: /api/math/placement/status, /api/math/placement/start,
                  /api/math/placement/next, /api/math/placement/check,
                  /api/math/placement/save, /api/math/placement/results
   ================================================================ */

// ── State ──────────────────────────────────────────────────

const placementState = {
    domains: [],      // [{domain, label}] — from /start (questions ignored in adaptive mode)
    answers: {},      // {domain: {qid: userAnswer}} — aggregated for /save
    history: {},      // {domain: [{id, grade, correct}]} — sent to /next for branching
    dIdx: 0,
    currentQ: null,   // {id, grade, type, question, options} — currently displayed
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
        placementState.domains = (data.domains || []).map(d => ({ domain: d.domain, label: d.label }));
        placementState.answers = {};
        placementState.history = {};
        placementState.domains.forEach(d => {
            placementState.answers[d.domain] = {};
            placementState.history[d.domain] = [];
        });
        placementState.dIdx = 0;
        placementState.currentQ = null;
        _renderPlacementIntro();
    } catch (err) {
        console.warn('[placement] start failed', err);
        stage.innerHTML = `<div class="math-wrong-review"><p>Could not load placement test.</p></div>`;
    }
}

/** @tag MATH @tag PLACEMENT */
function _showMathStageP() {
    if (typeof hideMathHome === 'function') hideMathHome();
    if (typeof hideMathAcademyHome === 'function') hideMathAcademyHome();
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
    stage.innerHTML = `
        <div class="math-placement-intro">
            <div class="math-placement-intro-icon">
                <i data-lucide="map-pin" style="width:32px;height:32px;stroke-width:1.5"></i>
            </div>
            <h2 class="math-placement-intro-title">Let's find out where you are</h2>
            <p class="math-placement-intro-sub">
                ${placementState.domains.length} topics · adaptive questions.<br>
                The test adjusts to your answers — skip anything you're not sure about.
            </p>
            <div class="math-placement-domains">
                ${placementState.domains.map(d =>
                    `<span class="math-placement-domain-chip">${_mathEsc(d.label)}</span>`
                ).join('')}
            </div>
            <button class="math-btn-primary math-placement-begin-btn" id="math-placement-begin">
                Start Placement
            </button>
        </div>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    document.getElementById('math-placement-begin').addEventListener('click', () => _fetchNextPlacementQ());
}

// ── Adaptive Question flow (CAT-lite) ──────────────────────
//
// Per MATH_SPEC §Placement Test Design: 15–20 adaptive questions, server
// branches grade on each answer. Client asks /next with current domain
// history, grades via /check, and advances to the next domain when the
// server signals done.

/** @tag MATH @tag PLACEMENT */
async function _fetchNextPlacementQ() {
    const d = placementState.domains[placementState.dIdx];
    if (!d) { _submitPlacement(); return; }

    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-wrong-review"><p>Loading…</p></div>`;

    try {
        const res = await fetch('/api/math/placement/next', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                domain: d.domain,
                history: placementState.history[d.domain] || [],
            }),
        });
        const data = await res.json();
        if (data.done || !data.question) {
            // Domain exhausted — move to next or finish.
            placementState.dIdx += 1;
            if (placementState.dIdx >= placementState.domains.length) {
                _submitPlacement();
            } else {
                _fetchNextPlacementQ();
            }
            return;
        }
        placementState.currentQ = data.question;
        _renderAdaptiveQ(d, data.question, data.target_grade);
    } catch (err) {
        console.warn('[placement] next failed', err);
        stage.innerHTML = `<div class="math-wrong-review"><p>Hmm, that didn't load. Let's try again!</p>
            <button class="math-btn-primary" onclick="_fetchNextPlacementQ()">↻ Try Again</button></div>`;
    }
}

/** @tag MATH @tag PLACEMENT */
function _renderAdaptiveQ(d, q, targetGrade) {
    const stage = document.getElementById('stage');
    if (!stage) return;

    const totalDomains = placementState.domains.length;
    const askedInDomain = (placementState.history[d.domain] || []).length + 1;
    const qText = q.question || '';
    const isShort = qText.length <= 20;
    const qClass = `math-problem-question${isShort ? ' is-short' : ''}`;

    const body = q.type === 'mc'
        ? `<div class="math-mc-grid">
               ${(q.options || []).map(o => `
                   <button class="math-mc-btn" data-val="${_mathEscAttr(o)}">
                       ${_mathEsc(o)}
                   </button>
               `).join('')}
           </div>`
        : `<div class="math-input-group">
               <input type="text" class="math-input-field" id="math-placement-input"
                      placeholder="Type your answer…" autocomplete="off">
               <button class="math-btn-primary" id="math-placement-submit">Next</button>
           </div>`;

    stage.innerHTML = `
        <div class="math-problem-wrap">
            <div class="math-problem-header">
                <span class="math-problem-stage">${_mathEsc(d.label)}</span>
                <span class="math-problem-counter">
                    ${placementState.dIdx + 1}/${totalDomains} · Q${askedInDomain}
                </span>
            </div>
            <div class="math-problem-card">
                <div class="${qClass}">${_mathEsc(qText)}</div>
                <div class="math-problem-body">${body}</div>
            </div>
            <div class="math-placement-skip-row">
                <button class="math-btn-ghost" id="math-placement-skip">
                    <i data-lucide="skip-forward" style="width:13px;height:13px;vertical-align:-2px;stroke-width:1.5"></i>
                    Skip this question
                </button>
            </div>
        </div>
    `;

    if (typeof lucide !== 'undefined') lucide.createIcons();
    if (typeof window.mathRenderIn === 'function') {
        const qEl = stage.querySelector('.math-problem-question');
        if (qEl) window.mathRenderIn(qEl);
    }

    if (q.type === 'mc') {
        stage.querySelectorAll('.math-mc-btn').forEach(btn => {
            btn.addEventListener('click', () => _submitAdaptiveAnswer(d, q, btn.dataset.val));
        });
        if (typeof window.mathRenderIn === 'function') {
            const grid = stage.querySelector('.math-mc-grid');
            if (grid) window.mathRenderIn(grid);
        }
    } else {
        const input = document.getElementById('math-placement-input');
        const submit = document.getElementById('math-placement-submit');
        const doSubmit = () => _submitAdaptiveAnswer(d, q, (input.value || '').trim());
        submit.addEventListener('click', doSubmit);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSubmit(); });
        setTimeout(() => input.focus(), 30);
    }

    document.getElementById('math-placement-skip').addEventListener('click',
        () => _submitAdaptiveAnswer(d, q, ''));
}

/** @tag MATH @tag PLACEMENT */
async function _submitAdaptiveAnswer(d, q, answer) {
    // Record the answer locally (used by /save for per-domain scoring).
    placementState.answers[d.domain][q.id] = answer;

    // Ask server to grade so branching uses authoritative correctness.
    let isCorrect = false;
    if (answer !== '') {
        try {
            const res = await fetch('/api/math/placement/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: d.domain,
                    question_id: q.id,
                    answer: answer,
                }),
            });
            if (res.ok) {
                const data = await res.json();
                isCorrect = !!data.is_correct;
            }
        } catch (err) {
            console.warn('[placement] check failed', err);
            // Treat as wrong on network failure so branching stays conservative.
        }
    }

    placementState.history[d.domain].push({
        id: q.id,
        grade: q.grade,
        correct: isCorrect,
    });
    _fetchNextPlacementQ();
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

// ── Wiring ─────────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
(function wirePlacement() {
    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('math-btn-placement');
        if (btn) btn.addEventListener('click', () => startPlacementTest());
    });
})();

// escape → _mathEsc / _mathEscAttr (math-katex-utils.js)
