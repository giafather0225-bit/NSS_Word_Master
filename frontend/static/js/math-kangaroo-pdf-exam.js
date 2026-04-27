/* ================================================================
   math-kangaroo-pdf-exam.js — PDF-embedded past-paper exam UI
   Section: Math
   Dependencies: core.js, math-kangaroo.js, math-kangaroo-result.js
   API endpoints:
     GET  /api/math/kangaroo/set/{set_id}
     POST /api/math/kangaroo/submit-answer
     POST /api/math/kangaroo/submit
   ================================================================ */

const kangPdfState = {
    set: null,
    mode: 'test',           // 'test' | 'practice'
    answers: {},            // { "1": "A", ... }
    checked: {},            // { "1": { is_correct, correct } }  practice mode
    timerId: null,
    remainingSec: 0,
    startedAt: 0,
    beforeUnloadHandler: null,
};

/** @tag MATH @tag KANGAROO @tag PP */
function _ppEsc(s) {
    return String(s ?? '').replace(/[&<>"']/g, ch => (
        { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]
    ));
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppFmt(sec) {
    sec = Math.max(0, sec | 0);
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    return (h > 0 ? String(h).padStart(2, '0') + ':' : '')
         + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
}

// ── In-page modal helpers ──────────────────────────────────

/** Show a confirm modal; returns a Promise<boolean>. @tag MATH @tag KANGAROO */
function _ppConfirm(title, body, okLabel = 'OK', cancelLabel = 'Cancel') {
    return new Promise(resolve => {
        const scrim = document.createElement('div');
        scrim.className = 'kang-modal-scrim';
        scrim.innerHTML = `
            <div class="kang-modal" role="dialog" aria-modal="true">
                <h3>${_ppEsc(title)}</h3>
                <p style="margin:0 0 8px;color:var(--text-secondary);font-size:var(--font-size-sm)">${_ppEsc(body)}</p>
                <div class="kang-modal-actions">
                    <button class="kang-btn kang-btn-ghost" id="pp-modal-cancel">${_ppEsc(cancelLabel)}</button>
                    <button class="kang-btn kang-btn-primary" id="pp-modal-ok">${_ppEsc(okLabel)}</button>
                </div>
            </div>`;
        document.body.appendChild(scrim);
        scrim.querySelector('#pp-modal-ok').addEventListener('click', () => { scrim.remove(); resolve(true); });
        scrim.querySelector('#pp-modal-cancel').addEventListener('click', () => { scrim.remove(); resolve(false); });
    });
}

/** Show a brief inline notice in the answer panel. @tag MATH @tag KANGAROO */
function _ppNotice(msg, isError = false) {
    const bar = document.getElementById('kang-progress-bar');
    if (!bar) return;
    const prev = bar.querySelector('.kang-pp-notice');
    if (prev) prev.remove();
    const el = document.createElement('div');
    el.className = `kang-pp-notice ${isError ? 'kang-fb-no' : 'kang-fb-ok'}`;
    el.textContent = msg;
    bar.after(el);
    setTimeout(() => el.remove(), 2400);
}

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag KANGAROO @tag PP */
async function startKangarooPdfExam(setId, mode) {
    kangPdfState.mode = (mode === 'practice') ? 'practice' : 'test';
    kangPdfState.answers = {};
    kangPdfState.checked = {};
    _ppClearTimer();

    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="kang-wrap"><p class="kang-loading">Loading…</p></div>`;

    try {
        const res = await fetch(`/api/math/kangaroo/set/${encodeURIComponent(setId)}`);
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        kangPdfState.set = data;
        if (data.pdf_available === false) {
            _ppRenderUnavailable(data);
            return;
        }
        _ppRenderExam();
        _ppAttachBeforeUnload();
    } catch (err) {
        console.warn('[kangaroo pdf] load failed', err);
        stage.innerHTML = `
            <div class="kang-wrap">
                <p class="kang-error">Hmm, that didn't load.</p>
                <button class="kang-btn kang-btn-primary" onclick="startMathKangaroo()">← Back</button>
            </div>`;
    }
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppRenderUnavailable(data) {
    const stage = document.getElementById('stage');
    stage.innerHTML = `
        <div class="kang-wrap">
            <header class="kang-pdf-header">
                <div class="kang-pdf-title">${_ppEsc(data.title || '')}</div>
                <button class="kang-quit-btn" onclick="startMathKangaroo()">← Back</button>
            </header>
            <div class="kang-pdf-missing">
                <h2>PDF not available</h2>
                <p>PDF file is not on this device.</p>
                <p class="kang-pdf-missing-hint">Place PDF files in
                <code>frontend/static/math/kangaroo/pdf/</code> to use Past Papers.</p>
            </div>
        </div>`;
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppRenderExam() {
    const s = kangPdfState.set;
    const stage = document.getElementById('stage');
    const timerHtml = (kangPdfState.mode === 'test')
        ? `<span class="kang-timer" id="kang-pdf-timer">--:--</span>` : '';
    const modeBadge = `<span class="kang-mode-badge kang-mode-${kangPdfState.mode}">${
        kangPdfState.mode === 'test' ? 'Test Mode' : 'Practice Mode'}</span>`;

    const pdfSrc = `${s.pdf_file}#toolbar=1&navpanes=0&view=FitH`;
    stage.innerHTML = `
        <div class="kang-pdf-wrap">
            <header class="kang-pdf-header">
                <div class="kang-pdf-title">${_ppEsc(s.title || '')} ${modeBadge}</div>
                <div class="kang-pdf-controls">
                    ${timerHtml}
                    <button class="kang-quit-btn" id="kang-pdf-quit">Quit</button>
                    <button class="kang-submit-btn kang-pdf-submit-top" id="kang-pdf-submit-top">Submit</button>
                </div>
            </header>
            <div class="kang-pdf-exam">
                <div class="kang-pdf-viewer-wrap">
                    <iframe class="kang-pdf-viewer" id="kang-pdf-iframe"
                        src="${_ppEsc(pdfSrc)}" type="application/pdf"
                        title="Exam PDF"></iframe>
                    <a class="kang-pdf-open-btn" id="kang-pdf-open-fallback"
                       href="${_ppEsc(pdfSrc)}" target="_blank" rel="noopener"
                       style="display:none">Open Exam PDF in New Tab</a>
                </div>
                <aside class="kang-answer-panel" id="kang-answer-panel">
                    ${_ppBuildPanelHtml(s)}
                </aside>
            </div>
        </div>`;

    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    if (isIOS) {
        document.getElementById('kang-pdf-iframe').style.display = 'none';
        document.getElementById('kang-pdf-open-fallback').style.display = 'flex';
    }

    document.getElementById('kang-answer-panel').addEventListener('click', _ppPanelClick);
    document.getElementById('kang-pdf-quit').addEventListener('click', _ppQuit);
    document.getElementById('kang-pdf-submit-top').addEventListener('click', () => _ppSubmit());

    if (kangPdfState.mode === 'test') {
        kangPdfState.remainingSec = (s.time_limit_minutes || 0) * 60;
        kangPdfState.startedAt = Date.now();
        _ppStartTimer();
    } else {
        kangPdfState.startedAt = Date.now();
    }
    _ppUpdateProgress();
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppBuildPanelHtml(s) {
    const meta      = s.sections_meta || [];
    const isPractice = (kangPdfState.mode === 'practice');
    const style     = s.numbering_style || 'sequential';
    const sections  = meta.map(sec => {
        const rows = (sec.questions || []).map(lbl => _ppRowHtml(lbl, sec.points, isPractice, style)).join('');
        return `
            <div class="kang-section-block">
                <div class="kang-section-divider">${_ppEsc(sec.name)} (${sec.points} pts each)</div>
                ${rows}
            </div>`;
    }).join('');
    return `
        ${sections}
        <div class="kang-progress-bar" id="kang-progress-bar">
            Progress: 0/${s.total_questions} answered
        </div>
        <button class="kang-submit-btn" id="kang-pdf-submit-bottom">Submit Exam</button>
    `;
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppRowHtml(label, points, isPractice, style) {
    const opts = ['A','B','C','D','E'].map(letter => `
        <button class="kang-answer-btn" data-q="${_ppEsc(label)}" data-letter="${letter}">${letter}</button>
    `).join('');
    const checkBtn = isPractice
        ? `<button class="kang-check-btn" data-check="${_ppEsc(label)}">Check</button>` : '';
    const display = (style === 'sectioned') ? label : `Q${label}`;
    return `
        <div class="kang-answer-row" data-row="${_ppEsc(label)}">
            <span class="kang-q-num">${_ppEsc(display)}</span>
            ${opts}
            ${checkBtn}
        </div>`;
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppPanelClick(e) {
    const btn = e.target.closest('[data-letter]');
    if (btn) {
        const q = btn.dataset.q;
        const letter = btn.dataset.letter;
        if (kangPdfState.checked[q]) return;
        if (kangPdfState.answers[q] === letter) {
            delete kangPdfState.answers[q];
        } else {
            kangPdfState.answers[q] = letter;
        }
        _ppRefreshRow(q);
        _ppUpdateProgress();
        return;
    }
    const check = e.target.closest('[data-check]');
    if (check) {
        _ppCheckOne(check.dataset.check);
        return;
    }
    if (e.target.closest('#kang-pdf-submit-bottom')) {
        _ppSubmit();
    }
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppRefreshRow(q) {
    const row = document.querySelector(`[data-row="${q}"]`);
    if (!row) return;
    const ans = kangPdfState.answers[q];
    const checked = kangPdfState.checked[q];
    row.querySelectorAll('[data-letter]').forEach(b => {
        b.classList.remove('selected','correct','wrong');
        if (checked) {
            if (b.dataset.letter === checked.correct) b.classList.add('correct');
            if (!checked.is_correct && b.dataset.letter === ans) b.classList.add('wrong');
        } else if (b.dataset.letter === ans) {
            b.classList.add('selected');
        }
    });
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppUpdateProgress() {
    const bar = document.getElementById('kang-progress-bar');
    if (!bar) return;
    const total    = kangPdfState.set.total_questions || 0;
    const answered = Object.keys(kangPdfState.answers).length;
    bar.textContent = `Progress: ${answered}/${total} answered`;
}

/** @tag MATH @tag KANGAROO @tag PP */
async function _ppCheckOne(q) {
    const ans = kangPdfState.answers[q];
    if (!ans) { _ppNotice('Select an answer first.', true); return; }
    try {
        const res = await fetch('/api/math/kangaroo/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                set_id: kangPdfState.set.set_id,
                question_id: q,
                answer: ans,
            }),
        });
        if (!res.ok) throw new Error('bad response');
        const d = await res.json();
        kangPdfState.checked[q] = { is_correct: !!d.is_correct, correct: d.correct_answer || '' };
        _ppRefreshRow(q);
    } catch (err) {
        console.warn('[kangaroo pdf] check failed', err);
        _ppNotice('Could not check — please try again.', true);
    }
}

// ── Timer ──────────────────────────────────────────────────

/** @tag MATH @tag KANGAROO @tag PP */
function _ppStartTimer() {
    _ppClearTimer();
    _ppTick();
    kangPdfState.timerId = setInterval(_ppTick, 1000);
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppClearTimer() {
    if (kangPdfState.timerId) {
        clearInterval(kangPdfState.timerId);
        kangPdfState.timerId = null;
    }
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppTick() {
    const el = document.getElementById('kang-pdf-timer');
    if (!el) return;
    const left = Math.max(0, kangPdfState.remainingSec);
    el.textContent = _ppFmt(left);
    el.classList.toggle('warning', left > 0 && left <= 300);
    if (left <= 0) {
        _ppClearTimer();
        _ppSubmit(true);
        return;
    }
    kangPdfState.remainingSec -= 1;
}

// ── Submit / Quit ──────────────────────────────────────────

/** @tag MATH @tag KANGAROO @tag PP */
async function _ppSubmit(auto = false) {
    const total    = kangPdfState.set.total_questions || 0;
    const answered = Object.keys(kangPdfState.answers).length;
    if (!auto) {
        const ok = await _ppConfirm(
            'Submit Exam',
            `You answered ${answered} out of ${total} questions. Submit now?`,
            'Submit', 'Keep going'
        );
        if (!ok) return;
    }
    _ppClearTimer();
    const timeSpent = Math.max(0, Math.floor((Date.now() - kangPdfState.startedAt) / 1000));
    try {
        const res = await fetch('/api/math/kangaroo/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                set_id: kangPdfState.set.set_id,
                answers: kangPdfState.answers,
                time_spent_seconds: timeSpent,
            }),
        });
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        _ppDetachBeforeUnload();
        if (typeof showKangarooPdfResult === 'function') {
            showKangarooPdfResult(data, kangPdfState.set);
        } else if (typeof showKangarooResult === 'function') {
            showKangarooResult(data);
        }
    } catch (err) {
        console.warn('[kangaroo pdf] submit failed', err);
        _ppNotice('Submission failed — please try again.', true);
    }
}

/** @tag MATH @tag KANGAROO @tag PP */
async function _ppQuit() {
    const ok = await _ppConfirm(
        'Quit Exam',
        'Your progress will not be saved. Are you sure?',
        'Quit', 'Stay'
    );
    if (!ok) return;
    _ppClearTimer();
    _ppDetachBeforeUnload();
    kangPdfState.answers = {};
    kangPdfState.checked = {};
    if (typeof startMathKangaroo === 'function') startMathKangaroo();
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppAttachBeforeUnload() {
    const handler = (e) => {
        if (Object.keys(kangPdfState.answers).length > 0) {
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    };
    kangPdfState.beforeUnloadHandler = handler;
    window.addEventListener('beforeunload', handler);
}

/** @tag MATH @tag KANGAROO @tag PP */
function _ppDetachBeforeUnload() {
    if (kangPdfState.beforeUnloadHandler) {
        window.removeEventListener('beforeunload', kangPdfState.beforeUnloadHandler);
        kangPdfState.beforeUnloadHandler = null;
    }
}

window.startKangarooPdfExam = startKangarooPdfExam;
