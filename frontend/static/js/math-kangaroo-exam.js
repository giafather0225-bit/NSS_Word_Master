/* ================================================================
   math-kangaroo-exam.js — Kangaroo exam screen (timer, navigator, answer)
   Section: Math
   Dependencies: core.js, math-kangaroo.js, math-kangaroo-result.js
   API endpoints: GET /api/math/kangaroo/set/{id},
                  POST /api/math/kangaroo/submit-answer,
                  POST /api/math/kangaroo/submit
   ================================================================ */

const examState = {
    setId: null,
    mode: 'test',           // 'test' | 'practice'
    title: '',
    timeLimitSec: 0,
    remainingSec: 0,
    questions: [],          // flat list with section info
    answers: {},            // qid -> 'A'..'E'
    flagged: {},            // qid -> bool
    practiceChecked: {},    // qid -> {correct_answer, solution, is_correct}
    idx: 0,
    timerHandle: null,
    startedAt: 0,
};

/** @tag MATH @tag KANGAROO */
function _examEsc(s) {
    return String(s ?? '').replace(/[&<>"']/g, ch => (
        { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]
    ));
}

/** @tag MATH @tag KANGAROO */
function _examFmt(sec) {
    const s = Math.max(0, Math.floor(sec));
    return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
}

/** @tag MATH @tag KANGAROO */
async function startKangarooExam(setId, mode) {
    examState.setId = setId;
    examState.mode = mode === 'practice' ? 'practice' : 'test';
    examState.answers = {};
    examState.flagged = {};
    examState.practiceChecked = {};
    examState.idx = 0;
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="kang-wrap"><p class="kang-loading">Loading exam…</p></div>`;
    try {
        const res = await fetch(`/api/math/kangaroo/set/${encodeURIComponent(setId)}`);
        if (!res.ok) throw new Error('load failed');
        const data = await res.json();
        examState.title = data.title || setId;
        examState.timeLimitSec = (data.time_limit_minutes || 75) * 60;
        examState.remainingSec = examState.timeLimitSec;
        const flat = [];
        (data.sections || []).forEach(sec => {
            (sec.questions || []).forEach(q => {
                flat.push({
                    ...q,
                    _section: sec.name,
                    _section_points: sec.points_per_question,
                });
            });
        });
        examState.questions = flat;
        examState.startedAt = Date.now();
        _examRender();
        if (examState.mode === 'test') _examStartTimer();
    } catch (err) {
        console.warn('[kangaroo] exam load failed', err);
        stage.innerHTML = `
            <div class="kang-wrap">
                <p class="kang-error">Couldn't load the set.</p>
                <button class="kang-btn kang-btn-primary" onclick="startMathKangaroo()">← Back</button>
            </div>`;
    }
}

/** @tag MATH @tag KANGAROO */
function _examStartTimer() {
    if (examState.timerHandle) clearInterval(examState.timerHandle);
    examState.timerHandle = setInterval(() => {
        examState.remainingSec -= 1;
        _examUpdateTimer();
        if (examState.remainingSec <= 0) {
            clearInterval(examState.timerHandle);
            examState.timerHandle = null;
            alert("Time's up! Your answers have been submitted automatically.");
            _examSubmit(true);
        }
    }, 1000);
}

/** @tag MATH @tag KANGAROO */
function _examUpdateTimer() {
    const el = document.getElementById('kang-timer');
    if (!el) return;
    el.textContent = _examFmt(examState.remainingSec);
    el.classList.remove('warn','crit');
    if (examState.remainingSec < 300) el.classList.add('crit');
    else if (examState.remainingSec < 600) el.classList.add('warn');
}

/** @tag MATH @tag KANGAROO */
function _examRender() {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `
        <div class="kang-wrap kang-exam">
            <header class="kang-exam-top">
                <div class="kang-exam-title">${_examEsc(examState.title)}</div>
                <div class="kang-exam-timer ${examState.mode==='practice'?'is-hidden':''}">
                    <span id="kang-timer" class="kang-timer">${_examFmt(examState.remainingSec)}</span>
                </div>
                <div class="kang-exam-actions">
                    ${examState.mode === 'test'
                        ? `<button id="kang-submit-btn" class="kang-btn kang-btn-primary">Submit Test</button>`
                        : `<button id="kang-finish-btn" class="kang-btn kang-btn-primary">Finish Practice</button>`}
                </div>
            </header>
            <div class="kang-nav" id="kang-nav"></div>
            <section class="kang-q" id="kang-q"></section>
            <footer class="kang-exam-bot">
                <button id="kang-prev" class="kang-btn kang-btn-ghost">← Previous</button>
                <span id="kang-pos" class="kang-pos"></span>
                <button id="kang-next" class="kang-btn kang-btn-ghost">Next →</button>
            </footer>
        </div>
    `;
    document.getElementById('kang-prev').addEventListener('click', () => _examGoto(examState.idx - 1));
    document.getElementById('kang-next').addEventListener('click', () => _examGoto(examState.idx + 1));
    if (examState.mode === 'test') {
        document.getElementById('kang-submit-btn').addEventListener('click', () => _examConfirmSubmit());
    } else {
        document.getElementById('kang-finish-btn').addEventListener('click', () => _examSubmit(false));
    }
    document.addEventListener('keydown', _examKeydown);
    _examRenderNav();
    _examRenderQuestion();
}

/** @tag MATH @tag KANGAROO */
function _examKeydown(e) {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    if (e.key === 'ArrowLeft') _examGoto(examState.idx - 1);
    else if (e.key === 'ArrowRight') _examGoto(examState.idx + 1);
}

/** @tag MATH @tag KANGAROO */
function _examRenderNav() {
    const nav = document.getElementById('kang-nav');
    if (!nav) return;
    let lastSection = null;
    let html = '';
    examState.questions.forEach((q, i) => {
        if (q._section !== lastSection) {
            html += `<span class="kang-nav-divider">── ${q._section_points} pts ──</span>`;
            lastSection = q._section;
        }
        const answered = examState.answers[q.id];
        const flagged = examState.flagged[q.id];
        const cur = i === examState.idx;
        const cls = [
            'kang-nav-btn',
            answered ? 'is-answered' : '',
            flagged ? 'is-flagged' : '',
            cur ? 'is-current' : '',
        ].filter(Boolean).join(' ');
        html += `<button class="${cls}" data-i="${i}" aria-label="Question ${q.number}">${q.number}${flagged?'<span class="kang-flag-icon">⚑</span>':''}</button>`;
    });
    nav.innerHTML = html;
    nav.querySelectorAll('.kang-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => _examGoto(parseInt(btn.dataset.i, 10)));
    });
}

/** @tag MATH @tag KANGAROO */
function _examRenderQuestion() {
    const host = document.getElementById('kang-q');
    const pos = document.getElementById('kang-pos');
    if (!host) return;
    const q = examState.questions[examState.idx];
    if (!q) return;
    const pts = q._section_points || q.points || 0;
    const sectionTint = pts === 3 ? 'kang-tint-3' : pts === 4 ? 'kang-tint-4' : 'kang-tint-5';
    const selected = examState.answers[q.id] || '';
    const flagged = !!examState.flagged[q.id];
    const optsHtml = Object.entries(q.options || {}).map(([k, v]) => `
        <button class="kang-opt ${selected === k ? 'is-selected' : ''}" data-opt="${k}">
            <span class="kang-opt-letter">(${k})</span>
            <span class="kang-opt-text">${_examEsc(v)}</span>
        </button>
    `).join('');
    const imgHtml = q.image_svg
        ? `<div class="kang-img" role="img" aria-label="${_examEsc(q.image_description || '')}">${q.image_svg}</div>`
        : '';
    const checkHtml = examState.mode === 'practice'
        ? `<div class="kang-practice">
             <button class="kang-btn kang-btn-secondary" id="kang-check-btn">Check Answer</button>
             <div class="kang-feedback" id="kang-feedback"></div>
           </div>`
        : '';
    host.innerHTML = `
        <div class="kang-section-label ${sectionTint}">${_examEsc(q._section)}</div>
        <div class="kang-q-head">
            <div class="kang-q-id">Q${q.number} · ${pts} pts</div>
            <div class="kang-q-topic">${_examEsc(q.topic || '')}</div>
            <button class="kang-flag ${flagged ? 'is-on' : ''}" id="kang-flag-btn">⚑ Flag</button>
        </div>
        <div class="kang-q-text">${_examEsc(q.question_text)}</div>
        ${imgHtml}
        <div class="kang-opts">${optsHtml}</div>
        ${checkHtml}
    `;
    if (pos) pos.textContent = `Question ${examState.idx + 1} of ${examState.questions.length}`;
    host.querySelectorAll('.kang-opt').forEach(btn => {
        btn.addEventListener('click', () => {
            examState.answers[q.id] = btn.dataset.opt;
            delete examState.practiceChecked[q.id];
            _examRenderNav();
            _examRenderQuestion();
        });
    });
    const flagBtn = document.getElementById('kang-flag-btn');
    if (flagBtn) flagBtn.addEventListener('click', () => {
        examState.flagged[q.id] = !examState.flagged[q.id];
        _examRenderNav();
        _examRenderQuestion();
    });
    if (examState.mode === 'practice') {
        const checkBtn = document.getElementById('kang-check-btn');
        if (checkBtn) checkBtn.addEventListener('click', () => _examCheckOne(q));
        const prior = examState.practiceChecked[q.id];
        if (prior) _examShowFeedback(prior);
    }
}

/** @tag MATH @tag KANGAROO */
async function _examCheckOne(q) {
    const ans = examState.answers[q.id];
    if (!ans) {
        const fb = document.getElementById('kang-feedback');
        if (fb) fb.innerHTML = `<div class="kang-fb kang-fb-warn">Select an option first.</div>`;
        return;
    }
    try {
        const res = await fetch('/api/math/kangaroo/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ set_id: examState.setId, question_id: q.id, answer: ans }),
        });
        const data = await res.json();
        examState.practiceChecked[q.id] = data;
        _examShowFeedback(data);
    } catch (err) {
        console.warn('[kangaroo] check failed', err);
    }
}

/** @tag MATH @tag KANGAROO */
function _examShowFeedback(data) {
    const fb = document.getElementById('kang-feedback');
    if (!fb) return;
    const cls = data.is_correct ? 'kang-fb-ok' : 'kang-fb-no';
    const head = data.is_correct ? '✓ Correct!' : `✗ Not quite — correct answer is (${_examEsc(data.correct_answer)})`;
    fb.innerHTML = `
        <div class="kang-fb ${cls}">
            <div class="kang-fb-head">${head}</div>
            ${data.solution ? `<div class="kang-fb-sol">${_examEsc(data.solution)}</div>` : ''}
        </div>
    `;
}

/** @tag MATH @tag KANGAROO */
function _examGoto(i) {
    if (i < 0 || i >= examState.questions.length) return;
    examState.idx = i;
    _examRenderNav();
    _examRenderQuestion();
}

/** @tag MATH @tag KANGAROO */
function _examConfirmSubmit() {
    const total = examState.questions.length;
    const answered = Object.keys(examState.answers).length;
    const flagged = Object.values(examState.flagged).filter(Boolean).length;
    const unanswered = total - answered;
    const host = document.getElementById('stage');
    const modal = document.createElement('div');
    modal.className = 'kang-modal-scrim';
    modal.innerHTML = `
        <div class="kang-modal">
            <h3>Submit your test?</h3>
            <p>Answered: <strong>${answered}</strong> of ${total}</p>
            <p>Flagged: <strong>${flagged}</strong></p>
            <p>Unanswered: <strong>${unanswered}</strong></p>
            <div class="kang-modal-actions">
                <button class="kang-btn kang-btn-ghost" data-act="cancel">Go Back</button>
                <button class="kang-btn kang-btn-secondary" data-act="review" ${flagged?'':'disabled'}>Review Flagged</button>
                <button class="kang-btn kang-btn-primary" data-act="submit">Submit</button>
            </div>
        </div>
    `;
    host.appendChild(modal);
    modal.querySelector('[data-act="cancel"]').addEventListener('click', () => modal.remove());
    modal.querySelector('[data-act="review"]').addEventListener('click', () => {
        modal.remove();
        const firstFlag = examState.questions.findIndex(q => examState.flagged[q.id]);
        if (firstFlag >= 0) _examGoto(firstFlag);
    });
    modal.querySelector('[data-act="submit"]').addEventListener('click', () => {
        modal.remove();
        _examSubmit(false);
    });
}

/** @tag MATH @tag KANGAROO */
async function _examSubmit(autoSubmit) {
    if (examState.timerHandle) { clearInterval(examState.timerHandle); examState.timerHandle = null; }
    document.removeEventListener('keydown', _examKeydown);
    const timeSpent = examState.mode === 'test'
        ? Math.max(0, examState.timeLimitSec - examState.remainingSec)
        : Math.floor((Date.now() - examState.startedAt) / 1000);
    const answers = Object.entries(examState.answers).map(([qid, a]) => ({ question_id: qid, answer: a }));
    const stage = document.getElementById('stage');
    if (stage) stage.innerHTML = `<div class="kang-wrap"><p class="kang-loading">Grading…</p></div>`;
    try {
        const res = await fetch('/api/math/kangaroo/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                set_id: examState.setId,
                answers,
                time_spent_seconds: timeSpent,
            }),
        });
        if (!res.ok) throw new Error('submit failed');
        const data = await res.json();
        if (typeof showKangarooResult === 'function') showKangarooResult(data);
    } catch (err) {
        console.warn('[kangaroo] submit failed', err);
        if (stage) stage.innerHTML = `
            <div class="kang-wrap">
                <p class="kang-error">Submission failed. Please try again.</p>
                <button class="kang-btn kang-btn-primary" onclick="startMathKangaroo()">← Back</button>
            </div>`;
    }
}

window.startKangarooExam = startKangarooExam;
