/* ================================================================
   math-kangaroo.js — Math Kangaroo Practice (set picker + runner)
   Section: Math
   Dependencies: core.js
   API endpoints: /api/math/kangaroo/sets, /api/math/kangaroo/set/{id},
                  /api/math/kangaroo/submit-answer, /api/math/kangaroo/submit
   ================================================================ */

// ── State ──────────────────────────────────────────────────

const kangarooState = {
    setId: '',
    title: '',
    problems: [],
    idx: 0,
    correct: 0,
};

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
async function startMathKangaroo() {
    _showKangStage();
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-kang"><p>Loading sets…</p></div>`;
    try {
        const res = await fetch('/api/math/kangaroo/sets');
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        if (!data.sets || !data.sets.length) {
            stage.innerHTML = `
                <div class="math-kang math-kang-empty">
                    <h2 class="math-kang-title">🧩 Kangaroo Practice</h2>
                    <p>No sets available yet.</p>
                </div>`;
            return;
        }
        _renderKangPicker(data.sets);
    } catch (err) {
        console.warn('[math] kangaroo load failed', err);
        stage.innerHTML = `<div class="math-kang"><p class="math-err">Failed to load.</p></div>`;
    }
}

// ── Stage helper ───────────────────────────────────────────

function _showKangStage() {
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

// ── Picker ─────────────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
function _renderKangPicker(sets) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `
        <div class="math-kang math-kang-picker">
            <h2 class="math-kang-title">🧩 Kangaroo Practice</h2>
            <p class="math-kang-sub">Pick a set to begin.</p>
            <div class="math-kang-grid">
                ${sets.map(s => `
                    <button class="math-kang-card" data-set="${_escAttrK(s.set_id)}">
                        <div class="math-kang-card-title">${_escK(s.title)}</div>
                        <div class="math-kang-card-meta">
                            <span>${_escK(s.category || '')}</span>
                            <span>${s.problem_count} problems</span>
                        </div>
                        ${s.completed ? `<div class="math-kang-card-badge">✓ Best: ${s.score}/${s.total}</div>` : ''}
                    </button>
                `).join('')}
            </div>
        </div>`;
    stage.querySelectorAll('.math-kang-card').forEach(btn => {
        btn.addEventListener('click', () => _startKangSet(btn.dataset.set));
    });
}

// ── Load a set ─────────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
async function _startKangSet(setId) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-kang"><p>Loading problems…</p></div>`;
    try {
        const res = await fetch(`/api/math/kangaroo/set/${encodeURIComponent(setId)}`);
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        kangarooState.setId = setId;
        kangarooState.title = data.title;
        kangarooState.problems = data.problems || [];
        kangarooState.idx = 0;
        kangarooState.correct = 0;
        _renderKangProblem();
    } catch (err) {
        console.warn('[math] kangaroo set failed', err);
        stage.innerHTML = `<div class="math-kang"><p class="math-err">Failed to load.</p></div>`;
    }
}

// ── Problem ────────────────────────────────────────────────

/** @tag MATH @tag KANGAROO */
function _renderKangProblem() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const total = kangarooState.problems.length;
    if (kangarooState.idx >= total) {
        _finishKang();
        return;
    }
    const p = kangarooState.problems[kangarooState.idx];
    const counter = `${kangarooState.idx + 1} / ${total}`;

    let body = '';
    if (p.type === 'mc' && Array.isArray(p.options) && p.options.length) {
        body = `
            <div class="math-kang-options">
                ${p.options.map(o => `<button class="math-kang-opt" data-val="${_escAttrK(o)}">${_escK(o)}</button>`).join('')}
            </div>`;
    } else {
        body = `
            <div class="math-kang-input-wrap">
                <input type="text" class="math-kang-input" id="math-kang-input" placeholder="Type answer" autofocus>
                <button class="math-btn-primary" id="math-kang-submit">Check</button>
            </div>`;
    }

    stage.innerHTML = `
        <div class="math-kang math-kang-problem">
            <div class="math-kang-header">
                <span class="math-kang-set-title">${_escK(kangarooState.title)}</span>
                <span class="math-kang-counter">${counter}</span>
            </div>
            <div class="math-kang-q">${_escK(p.question || '')}</div>
            ${body}
            <div class="math-kang-feedback" id="math-kang-feedback"></div>
        </div>`;

    stage.querySelectorAll('.math-kang-opt').forEach(btn => {
        btn.addEventListener('click', () => _submitKangAnswer(p, btn.dataset.val));
    });
    const submitBtn = document.getElementById('math-kang-submit');
    const inputEl = document.getElementById('math-kang-input');
    if (submitBtn && inputEl) {
        submitBtn.addEventListener('click', () => _submitKangAnswer(p, inputEl.value));
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') _submitKangAnswer(p, inputEl.value);
        });
        inputEl.focus();
    }
}

/** @tag MATH @tag KANGAROO */
async function _submitKangAnswer(problem, answer) {
    if (!answer && answer !== 0) return;
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.querySelectorAll('.math-kang-opt').forEach(b => b.disabled = true);
    const submitBtn = document.getElementById('math-kang-submit');
    if (submitBtn) submitBtn.disabled = true;

    let result = null;
    try {
        const res = await fetch('/api/math/kangaroo/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                set_id: kangarooState.setId,
                problem_id: problem.id,
                answer: String(answer),
            }),
        });
        result = await res.json();
    } catch (err) {
        console.warn('[math] kangaroo submit failed', err);
        return;
    }
    if (result.is_correct) kangarooState.correct += 1;

    stage.querySelectorAll('.math-kang-opt').forEach(b => {
        if (b.dataset.val === String(answer)) {
            b.classList.add(result.is_correct ? 'math-kang-opt-correct' : 'math-kang-opt-wrong');
        } else if (!result.is_correct && b.dataset.val === String(result.correct_answer)) {
            b.classList.add('math-kang-opt-correct');
        }
    });

    const fb = document.getElementById('math-kang-feedback');
    if (fb) {
        fb.className = `math-kang-feedback ${result.is_correct ? 'math-fb-ok' : 'math-fb-no'}`;
        fb.innerHTML = `
            <div class="math-fb-line">${result.is_correct ? '✓ Correct!' : `✗ Answer: <strong>${_escK(result.correct_answer)}</strong>`}</div>
            ${result.feedback ? `<div class="math-fb-hint">${_escK(result.feedback)}</div>` : ''}
            <button class="math-btn-primary math-kang-next" id="math-kang-next">Next →</button>`;
        const nextBtn = document.getElementById('math-kang-next');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                kangarooState.idx += 1;
                _renderKangProblem();
            });
            nextBtn.focus();
        }
    }
}

// ── Finish + summary ───────────────────────────────────────

/** @tag MATH @tag KANGAROO */
async function _finishKang() {
    let xp = 0;
    try {
        const res = await fetch('/api/math/kangaroo/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                set_id: kangarooState.setId,
                score: kangarooState.correct,
                total: kangarooState.problems.length,
            }),
        });
        const data = await res.json();
        xp = data.xp || 0;
    } catch (err) {
        console.warn('[math] kangaroo complete failed', err);
    }
    _renderKangSummary(xp);
}

/** @tag MATH @tag KANGAROO */
function _renderKangSummary(xp) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const total = kangarooState.problems.length || 0;
    const correct = kangarooState.correct;
    const pct = total ? Math.round((correct / total) * 100) : 0;
    const perfect = total > 0 && correct === total;
    stage.innerHTML = `
        <div class="math-kang math-kang-summary">
            <h2 class="math-kang-title">🧩 ${_escK(kangarooState.title)} — Done</h2>
            <div class="math-kang-score">${correct} / ${total}</div>
            <div class="math-kang-pct">${pct}%</div>
            <div class="math-kang-chips">
                ${perfect ? '<span class="math-chip math-chip-ok">Perfect!</span>' : ''}
                ${xp ? `<span class="math-chip math-chip-ok">+${xp} XP</span>` : ''}
            </div>
            <button class="math-btn-primary" id="math-kang-again">Pick another set</button>
        </div>`;
    const btn = document.getElementById('math-kang-again');
    if (btn) btn.addEventListener('click', () => startMathKangaroo());
}

// ── Escape helpers ─────────────────────────────────────────

function _escK(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}
function _escAttrK(s) {
    return _escK(s).replace(/"/g, '&quot;');
}
