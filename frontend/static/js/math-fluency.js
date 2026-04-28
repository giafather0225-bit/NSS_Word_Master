/* ================================================================
   math-fluency.js — Fact Fluency (timed rounds) UI
   Section: Math
   Dependencies: core.js
   API endpoints: /api/math/fluency/catalog, /api/math/fluency/start-round,
                  /api/math/fluency/submit-round, /api/math/fluency/summary
   ================================================================ */

// ── State ──────────────────────────────────────────────────

const fluencyState = {
    factSet: '',
    questions: [],
    idx: 0,
    correct: 0,
    answered: 0,
    startedAt: 0,
    endsAt: 0,
    timerId: null,
    timeLimit: 60,
};

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag FLUENCY */
async function startMathFluency() {
    _showMathStage();
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-wrong-review"><p>Loading fact sets…</p></div>`;
    try {
        const res = await fetch('/api/math/fluency/catalog');
        const data = await res.json();
        _renderFluencyPicker(data.fact_sets || []);
    } catch (err) {
        console.warn('[fluency] catalog failed', err);
        stage.innerHTML = `<div class="math-wrong-review"><p>Could not load fact sets.</p></div>`;
    }
}

/** @tag MATH @tag FLUENCY */
function _showMathStage() {
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

// ── Fact set picker ────────────────────────────────────────

/** @tag MATH @tag FLUENCY */
function _renderFluencyPicker(factSets) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `
        <div class="math-fluency-picker">
            <div class="math-fluency-picker-header">
                <h2 class="math-fluency-title">Fact Fluency</h2>
                <p class="math-fluency-sub">Pick a fact set and practice for speed.</p>
            </div>
            <div class="math-fluency-grid">
                ${factSets.map(fs => {
                    const bestPct = fs.best_score != null ? Math.round(fs.best_score / 10 * 100) : 0;
                    return `
                    <button class="math-fluency-card" data-set="${_mathEscAttr(fs.fact_set)}">
                        <div class="math-fluency-card-op">${_mathEsc(fs.op)}</div>
                        <div class="math-fluency-card-label">${_mathEsc(fs.label)}</div>
                        <div class="math-fluency-card-bar-wrap">
                            <div class="math-fluency-card-bar" style="width:${bestPct}%"></div>
                        </div>
                        <div class="math-fluency-card-meta">
                            <span class="math-fluency-phase">Phase ${_mathEsc(fs.current_phase)}</span>
                            <span class="math-fluency-card-meta-right">Best ${fs.best_score}/10</span>
                        </div>
                    </button>
                `}).join('')}
            </div>
        </div>
    `;
    stage.querySelectorAll('.math-fluency-card').forEach(btn => {
        btn.addEventListener('click', () => _startRound(btn.dataset.set));
    });
}

// ── Round ──────────────────────────────────────────────────

/** @tag MATH @tag FLUENCY */
async function _startRound(factSet) {
    try {
        const res = await fetch(`/api/math/fluency/start-round?fact_set=${encodeURIComponent(factSet)}&count=10`);
        const data = await res.json();
        fluencyState.factSet = factSet;
        fluencyState.questions = data.questions || [];
        fluencyState.idx = 0;
        fluencyState.correct = 0;
        fluencyState.answered = 0;
        // Phase A is untimed: backend returns time_limit_sec === 0.
        fluencyState.timeLimit = Number(data.time_limit_sec) || 0;
        fluencyState.untimed = fluencyState.timeLimit <= 0;
        fluencyState.phase = data.phase || 'A';
        fluencyState.startedAt = Date.now();
        fluencyState.endsAt = fluencyState.untimed
            ? 0
            : fluencyState.startedAt + fluencyState.timeLimit * 1000;
        _renderRoundFrame(data.label || factSet);
        _renderCurrentQuestion();
        _startTimer();
    } catch (err) {
        console.warn('[fluency] start-round failed', err);
    }
}

// SVG ring constants: r=36 → circumference ≈ 226.2px
const _FL_CIRC = 2 * Math.PI * 36;

/** @tag MATH @tag FLUENCY */
function _renderRoundFrame(label) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const untimed = fluencyState.untimed;
    stage.innerHTML = `
        <div class="math-fluency-round">
            <div class="math-fluency-round-top">
                <div class="math-fluency-score-pill">
                    <span id="math-fluency-correct">0</span>
                    <span class="math-fluency-score-sep">/</span>
                    <span>${fluencyState.questions.length}</span>
                </div>
                ${untimed
                    ? `<div class="math-fluency-timer-ring untimed">
                           <span class="math-fluency-timer-text">∞</span>
                       </div>`
                    : `<div class="math-fluency-timer-ring" id="math-fluency-ring-wrap">
                           <svg class="math-fluency-ring-svg" viewBox="0 0 80 80">
                               <circle class="math-fluency-ring-track" cx="40" cy="40" r="36"/>
                               <circle class="math-fluency-ring-fill" id="math-fluency-ring-fill"
                                       cx="40" cy="40" r="36"
                                       stroke-dasharray="${_FL_CIRC}"
                                       stroke-dashoffset="0"/>
                           </svg>
                           <span class="math-fluency-timer-text" id="math-fluency-timer">${fluencyState.timeLimit}</span>
                       </div>`
                }
                <span class="math-fluency-round-label">${_mathEsc(label)}</span>
            </div>
            <div class="math-fluency-card-big" id="math-fluency-card"></div>
            <button class="math-btn-ghost math-fluency-stop-btn" id="math-fluency-quit">
                <i data-lucide="square" style="width:12px;height:12px;vertical-align:-1px;stroke-width:2;fill:currentColor"></i>
                Stop
            </button>
        </div>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    document.getElementById('math-fluency-quit').addEventListener('click', () => _finishRound(true));
}

/** @tag MATH @tag FLUENCY */
function _renderCurrentQuestion() {
    const card = document.getElementById('math-fluency-card');
    if (!card) return;
    const q = fluencyState.questions[fluencyState.idx];
    if (!q) { _finishRound(false); return; }
    card.innerHTML = `
        <div class="math-fluency-question">${_mathEsc(q.question)} = ?</div>
        <input type="tel" inputmode="numeric" pattern="-?[0-9]*"
               class="math-fluency-input" id="math-fluency-input"
               placeholder="?" autocomplete="off">
    `;
    const input = document.getElementById('math-fluency-input');
    setTimeout(() => input?.focus(), 30);

    // Auto-submit when valid answer typed + Enter
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') _submitCurrent();
    });
    // Also auto-submit when length matches expected digit count
    input.addEventListener('input', () => {
        const val = input.value.trim();
        const expected = String(q.answer);
        if (val.length >= expected.length && val === expected) {
            _submitCurrent();
        }
    });
}

/** @tag MATH @tag FLUENCY */
function _submitCurrent() {
    const input = document.getElementById('math-fluency-input');
    if (!input) return;
    const val = input.value.trim();
    if (val === '') return;
    const q = fluencyState.questions[fluencyState.idx];
    const isCorrect = String(parseInt(val, 10)) === String(q.answer);
    if (isCorrect) fluencyState.correct += 1;
    fluencyState.answered += 1;
    fluencyState.idx += 1;

    // Flash
    const card = document.getElementById('math-fluency-card');
    if (card) {
        card.classList.add(isCorrect ? 'flash-correct' : 'flash-wrong');
        setTimeout(() => card?.classList.remove('flash-correct', 'flash-wrong'), 140);
    }

    _updateScoreDisplay();
    if (fluencyState.idx >= fluencyState.questions.length) {
        _finishRound(false);
    } else {
        _renderCurrentQuestion();
    }
}

/** @tag MATH @tag FLUENCY */
function _updateScoreDisplay() {
    const c = document.getElementById('math-fluency-correct');
    if (c) c.textContent = String(fluencyState.correct);
}

// ── Timer ──────────────────────────────────────────────────

/** @tag MATH @tag FLUENCY */
function _startTimer() {
    _clearTimer();
    if (fluencyState.untimed) return;
    fluencyState.timerId = setInterval(() => {
        const left = Math.max(0, (fluencyState.endsAt - Date.now()) / 1000);
        const leftRounded = Math.ceil(left);
        const pctLeft = left / fluencyState.timeLimit;

        const tEl = document.getElementById('math-fluency-timer');
        if (tEl) tEl.textContent = String(leftRounded);

        // Drive SVG ring: offset goes from 0 (full) to _FL_CIRC (empty)
        const ringEl = document.getElementById('math-fluency-ring-fill');
        if (ringEl) ringEl.style.strokeDashoffset = String(_FL_CIRC * (1 - pctLeft));

        // Color ring red in last 10 seconds
        const wrap = document.getElementById('math-fluency-ring-wrap');
        if (wrap) wrap.classList.toggle('urgent', left <= 10);

        if (left <= 0) _finishRound(false);
    }, 100);
}

/** @tag MATH @tag FLUENCY */
function _clearTimer() {
    if (fluencyState.timerId) { clearInterval(fluencyState.timerId); fluencyState.timerId = null; }
}

// ── Finish ─────────────────────────────────────────────────

/** @tag MATH @tag FLUENCY */
async function _finishRound(aborted) {
    _clearTimer();
    const elapsed = Math.round((Date.now() - fluencyState.startedAt) / 1000);
    const total = fluencyState.questions.length;
    const score = fluencyState.correct;
    let submitData = null;
    if (!aborted && fluencyState.answered > 0) {
        try {
            const res = await fetch('/api/math/fluency/submit-round', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fact_set: fluencyState.factSet,
                    score,
                    total,
                    time_sec: elapsed,
                }),
            });
            submitData = await res.json();
        } catch (err) {
            console.warn('[fluency] submit failed', err);
        }
    }
    _renderFluencySummary({ score, total, elapsed, aborted, submitData });
    if (typeof loadMathSidebarStatus === 'function') loadMathSidebarStatus();
}

/** @tag MATH @tag FLUENCY */
function _renderFluencySummary({ score, total, elapsed, aborted, submitData }) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const pct = total ? Math.round((score / total) * 100) : 0;
    const passed = pct >= 80;
    const phase = submitData?.current_phase ? `Phase ${submitData.current_phase}` : '';
    const newBest = submitData?.new_best;
    const mastered = submitData?.mastered;

    const iconName = aborted ? 'circle-x' : passed ? 'zap' : 'refresh-cw';
    const titleText = aborted ? 'Round Stopped' : passed ? 'Nice work!' : 'Keep going!';

    stage.innerHTML = `
        <div class="math-fluency-summary">
            <div class="math-fluency-summary-icon ${passed && !aborted ? 'pass' : aborted ? 'stopped' : 'retry'}">
                <i data-lucide="${iconName}" style="width:28px;height:28px;stroke-width:1.5"></i>
            </div>
            <h2 class="math-fluency-summary-title">${titleText}</h2>
            <div class="math-fluency-summary-score">${score}<span class="math-fluency-summary-total"> / ${total}</span></div>
            <div class="math-fluency-summary-meta">${pct}%${elapsed ? ' · ' + elapsed + 's' : ''}${phase ? ' · ' + _mathEsc(phase) : ''}</div>
            <div class="math-fluency-summary-bar-wrap">
                <div class="math-fluency-summary-bar ${passed ? 'pass' : 'fail'}" style="width:${pct}%"></div>
            </div>
            ${(newBest || mastered) ? `
                <div class="math-fluency-milestones">
                    ${newBest ? `<span class="math-fluency-milestone-chip"><i data-lucide="trophy" style="width:12px;height:12px;vertical-align:-1px;stroke-width:1.5"></i> Personal Best</span>` : ''}
                    ${mastered ? `<span class="math-fluency-milestone-chip"><i data-lucide="graduation-cap" style="width:12px;height:12px;vertical-align:-1px;stroke-width:1.5"></i> Mastered</span>` : ''}
                </div>` : ''}
            <div class="math-fluency-summary-actions">
                <button class="math-btn-ghost" id="math-fluency-back">Back</button>
                <button class="math-btn-primary" id="math-fluency-again">Try Again</button>
            </div>
        </div>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    document.getElementById('math-fluency-again')?.addEventListener('click', () => startMathFluency());
    document.getElementById('math-fluency-back')?.addEventListener('click', () => {
        if (typeof switchView === 'function') switchView('math');
        const stageCard = document.getElementById('stage-card');
        if (stageCard) stageCard.style.display = 'none';
        const idleWrap = document.getElementById('idle-wrapper');
        if (idleWrap) idleWrap.style.display = '';
    });
}

// ── Wiring ─────────────────────────────────────────────────

/** @tag MATH @tag FLUENCY */
(function wireFluencyBtn() {
    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('math-btn-fluency');
        if (btn) btn.addEventListener('click', () => startMathFluency());
    });
})();

// escape → _mathEsc / _mathEscAttr (math-katex-utils.js)
