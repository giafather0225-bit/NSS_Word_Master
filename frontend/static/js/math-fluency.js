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
            <h2 class="math-fluency-title">🔢 Fact Fluency</h2>
            <p class="math-fluency-sub">Pick a fact set — 60 seconds, 10 questions.</p>
            <div class="math-fluency-grid">
                ${factSets.map(fs => `
                    <button class="math-fluency-card" data-set="${_escF(fs.fact_set)}">
                        <div class="math-fluency-card-op">${_escF(fs.op)}</div>
                        <div class="math-fluency-card-label">${_escF(fs.label)}</div>
                        <div class="math-fluency-card-meta">
                            <span class="math-fluency-phase">Phase ${_escF(fs.current_phase)}</span>
                            <span>${fs.total_rounds} rounds</span>
                            <span>Best ${fs.best_score}/10</span>
                        </div>
                    </button>
                `).join('')}
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
        fluencyState.timeLimit = data.time_limit_sec || 60;
        fluencyState.startedAt = Date.now();
        fluencyState.endsAt = fluencyState.startedAt + fluencyState.timeLimit * 1000;
        _renderRoundFrame(data.label || factSet);
        _renderCurrentQuestion();
        _startTimer();
    } catch (err) {
        console.warn('[fluency] start-round failed', err);
    }
}

/** @tag MATH @tag FLUENCY */
function _renderRoundFrame(label) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `
        <div class="math-fluency-round">
            <div class="math-fluency-header">
                <span class="math-fluency-label">${_escF(label)}</span>
                <span class="math-fluency-timer" id="math-fluency-timer">${fluencyState.timeLimit}s</span>
            </div>
            <div class="math-fluency-bar">
                <div class="math-fluency-bar-fill" id="math-fluency-bar-fill" style="width:100%"></div>
            </div>
            <div class="math-fluency-card-big" id="math-fluency-card"></div>
            <div class="math-fluency-score">
                ✓ <span id="math-fluency-correct">0</span>
                &nbsp;·&nbsp;
                <span id="math-fluency-answered">0</span> / ${fluencyState.questions.length}
            </div>
            <button class="math-btn-ghost" id="math-fluency-quit">Stop</button>
        </div>
    `;
    document.getElementById('math-fluency-quit').addEventListener('click', () => _finishRound(true));
}

/** @tag MATH @tag FLUENCY */
function _renderCurrentQuestion() {
    const card = document.getElementById('math-fluency-card');
    if (!card) return;
    const q = fluencyState.questions[fluencyState.idx];
    if (!q) { _finishRound(false); return; }
    card.innerHTML = `
        <div class="math-fluency-question">${_escF(q.question)} = ?</div>
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
    const a = document.getElementById('math-fluency-answered');
    if (c) c.textContent = String(fluencyState.correct);
    if (a) a.textContent = String(fluencyState.answered);
}

// ── Timer ──────────────────────────────────────────────────

/** @tag MATH @tag FLUENCY */
function _startTimer() {
    _clearTimer();
    fluencyState.timerId = setInterval(() => {
        const left = Math.max(0, Math.round((fluencyState.endsAt - Date.now()) / 1000));
        const tEl = document.getElementById('math-fluency-timer');
        const barEl = document.getElementById('math-fluency-bar-fill');
        if (tEl) tEl.textContent = `${left}s`;
        if (barEl) barEl.style.width = `${(left / fluencyState.timeLimit) * 100}%`;
        if (left <= 0) _finishRound(false);
    }, 200);
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
    stage.innerHTML = `
        <div class="math-round-summary">
            <div class="math-summary-icon">${aborted ? '🛑' : (passed ? '⚡' : '🔁')}</div>
            <h2 class="math-summary-title">${aborted ? 'Round Stopped' : 'Round Complete'}</h2>
            <div class="math-summary-score">${score} / ${total}</div>
            <div class="math-summary-pct">${pct}% · ${elapsed}s${phase ? ' · ' + _escF(phase) : ''}</div>
            <div class="math-summary-bar">
                <div class="math-summary-bar-fill ${passed ? 'pass' : 'fail'}" style="width:${pct}%"></div>
            </div>
            ${(newBest || mastered) ? `
                <div class="math-summary-weak">
                    <div class="math-summary-weak-label">Milestones</div>
                    <div class="math-summary-weak-list">
                        ${newBest ? '<span class="math-summary-chip">🏆 Personal Best</span>' : ''}
                        ${mastered ? '<span class="math-summary-chip">🎓 Mastered</span>' : ''}
                    </div>
                </div>` : ''}
            <div class="math-fluency-actions">
                <button class="math-btn-ghost" id="math-fluency-back">Back</button>
                <button class="math-btn-primary" id="math-fluency-again">Try Another</button>
            </div>
        </div>
    `;
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

// ── Escape helper ──────────────────────────────────────────

function _escF(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
}
