/* ================================================================
   math-daily.js — Daily Challenge (3 problems/day) UI
   Section: Math
   Dependencies: core.js
   API endpoints: /api/math/daily/today, /api/math/daily/submit-answer,
                  /api/math/daily/complete
   ================================================================ */

// ── State ──────────────────────────────────────────────────

const dailyState = {
    date: '',
    problems: [],
    idx: 0,
    correct: 0,
    completed: false,
};

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag DAILY */
async function startMathDaily() {
    _showDailyStage();
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-daily"><p>Loading today's challenge…</p></div>`;
    try {
        const res = await fetch('/api/math/daily/today');
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        if (!data.exists || !data.problems || !data.problems.length) {
            stage.innerHTML = `
                <div class="math-daily math-daily-empty">
                    <h2 class="math-daily-title">🌞 Daily Challenge</h2>
                    <p>No problems available yet. Add more lessons to enable daily challenges.</p>
                </div>`;
            return;
        }
        dailyState.date = data.date;
        dailyState.problems = data.problems;
        dailyState.idx = 0;
        dailyState.correct = data.score || 0;
        dailyState.completed = !!data.completed;

        if (dailyState.completed) {
            _renderDailySummary({ alreadyDone: true });
        } else {
            _renderDailyIntro();
        }
    } catch (err) {
        console.warn('[math] daily load failed', err);
        stage.innerHTML = `<div class="math-daily"><p class="math-err">Hmm, that didn't load. Let's try again!</p><button class="math-btn-primary" onclick="startMathDaily()">↻ Try Again</button></div>`;
    }
}

// ── Stage helper ───────────────────────────────────────────

/** @tag MATH @tag DAILY */
function _showDailyStage() {
    if (typeof showLessonStage === 'function') showLessonStage();
}

// ── Intro ──────────────────────────────────────────────────

/** @tag MATH @tag DAILY */
function _renderDailyIntro() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `
        <div class="math-daily math-daily-intro">
            <h2 class="math-daily-title">🌞 Daily Challenge</h2>
            <p class="math-daily-sub">${_mathEsc(dailyState.date)}</p>
            <p class="math-daily-desc">
                ${dailyState.problems.length} quick problems.<br>
                Complete all = <strong>+5 XP</strong>, perfect = <strong>+3 XP bonus</strong>.
            </p>
            <button class="math-btn-primary" id="math-daily-go">Start</button>
        </div>`;
    document.getElementById('math-daily-go').addEventListener('click', () => {
        dailyState.idx = 0;
        dailyState.correct = 0;
        _renderDailyProblem();
    });
}

// ── Problem render ─────────────────────────────────────────

/** @tag MATH @tag DAILY */
function _renderDailyProblem() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const total = dailyState.problems.length;
    if (dailyState.idx >= total) {
        _finishDaily();
        return;
    }
    const p = dailyState.problems[dailyState.idx];
    const counter = `${dailyState.idx + 1} / ${total}`;

    let body = '';
    if (p.type === 'mc' && Array.isArray(p.options) && p.options.length) {
        body = `
            <div class="math-daily-options">
                ${p.options.map(o => `<button class="math-daily-opt" data-val="${_mathEscAttr(o)}">${_mathEsc(o)}</button>`).join('')}
            </div>`;
    } else {
        body = `
            <div class="math-daily-input-wrap">
                <input type="text" class="math-daily-input" id="math-daily-input" placeholder="Type answer" autofocus>
                <button class="math-btn-primary" id="math-daily-submit">Check</button>
            </div>`;
    }

    stage.innerHTML = `
        <div class="math-daily math-daily-problem">
            <div class="math-daily-header">
                <span class="math-daily-counter">${counter}</span>
                <span class="math-daily-concept">${_mathEsc(p.concept || '')}</span>
            </div>
            <div class="math-daily-q">${_mathEsc(p.question || '')}</div>
            ${body}
            <div class="math-daily-feedback" id="math-daily-feedback"></div>
        </div>`;

    // Wire
    stage.querySelectorAll('.math-daily-opt').forEach(btn => {
        btn.addEventListener('click', () => _submitDailyAnswer(btn.dataset.val));
    });
    const submitBtn = document.getElementById('math-daily-submit');
    const inputEl = document.getElementById('math-daily-input');
    if (submitBtn && inputEl) {
        submitBtn.addEventListener('click', () => _submitDailyAnswer(inputEl.value));
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') _submitDailyAnswer(inputEl.value);
        });
        inputEl.focus();
    }
}

// ── Submit answer ──────────────────────────────────────────

/** @tag MATH @tag DAILY */
async function _submitDailyAnswer(answer) {
    if (!answer && answer !== 0) return;
    const stage = document.getElementById('stage');
    if (!stage) return;
    // Lock inputs
    stage.querySelectorAll('.math-daily-opt').forEach(b => b.disabled = true);
    const submitBtn = document.getElementById('math-daily-submit');
    if (submitBtn) submitBtn.disabled = true;

    let result = null;
    try {
        const res = await fetch('/api/math/daily/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index: dailyState.idx, answer: String(answer) }),
        });
        result = await res.json();
    } catch (err) {
        console.warn('[math] daily submit failed', err);
        return;
    }
    if (result.is_correct) dailyState.correct += 1;

    // Highlight selected / correct options
    stage.querySelectorAll('.math-daily-opt').forEach(b => {
        if (b.dataset.val === String(answer)) {
            b.classList.add(result.is_correct ? 'math-daily-opt-correct' : 'math-daily-opt-wrong');
        } else if (!result.is_correct && b.dataset.val === String(result.correct_answer)) {
            b.classList.add('math-daily-opt-correct');
        }
    });

    const fb = document.getElementById('math-daily-feedback');
    if (fb) {
        fb.className = `math-daily-feedback ${result.is_correct ? 'math-fb-ok' : 'math-fb-no'}`;
        fb.innerHTML = `
            <div class="math-fb-line">${result.is_correct ? '✓ Correct!' : `✗ Answer: <strong>${_mathEsc(result.correct_answer)}</strong>`}</div>
            ${result.feedback ? `<div class="math-fb-hint">${_mathEsc(result.feedback)}</div>` : ''}
            <button class="math-btn-primary math-daily-next" id="math-daily-next">Next →</button>`;
        const nextBtn = document.getElementById('math-daily-next');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                dailyState.idx += 1;
                _renderDailyProblem();
            });
            nextBtn.focus();
        }
    }
}

// ── Finish + summary ───────────────────────────────────────

/** @tag MATH @tag DAILY */
async function _finishDaily() {
    try {
        await fetch('/api/math/daily/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ score: dailyState.correct, total: dailyState.problems.length }),
        });
    } catch (err) {
        console.warn('[math] daily complete failed', err);
    }
    _renderDailySummary({ alreadyDone: false });
}

/** @tag MATH @tag DAILY */
function _renderDailySummary({ alreadyDone }) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const total = dailyState.problems.length || 0;
    const correct = dailyState.correct;
    const pct = total ? Math.round((correct / total) * 100) : 0;
    const perfect = total > 0 && correct === total;

    stage.innerHTML = `
        <div class="math-daily math-daily-summary">
            <h2 class="math-daily-title">🌞 Daily Challenge — Done</h2>
            <div class="math-daily-score">${correct} / ${total}</div>
            <div class="math-daily-pct">${pct}%</div>
            <div class="math-daily-chips">
                ${perfect ? '<span class="math-chip math-chip-ok">Perfect! +3 XP bonus</span>' : ''}
                ${alreadyDone ? '<span class="math-chip">Already completed today</span>' : '<span class="math-chip math-chip-ok">+5 XP</span>'}
            </div>
            <p class="math-daily-sub">Come back tomorrow for a new set!</p>
        </div>`;
}

// escape → _mathEsc / _mathEscAttr (math-katex-utils.js)
