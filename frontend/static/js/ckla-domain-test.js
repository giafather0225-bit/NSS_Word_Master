/* ================================================================
   ckla-domain-test.js — CKLA Domain Test screen
   Section: Academy
   Dependencies: ckla.js (cklaNav, _renderTestResult, escapeHtml), core.js
   API endpoints: GET  /api/academy/ckla/domain-test/:id
                  POST /api/academy/ckla/domain-test/:id/submit
                  POST /api/academy/ckla/badges/check
   ================================================================ */

/** Open the domain test screen for a completed domain. @tag ACADEMY CKLA */
async function openDomainTest(domainNum) {
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading domain test…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/domain-test/${domainNum}?grade=${cklaNav.grade}`);
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    _renderDomainTest(domainNum, data);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load test. ${e.message}</div>`;
  }
}

/** @tag ACADEMY CKLA */
function _renderDomainTest(domainNum, data) {
  const view = document.getElementById('ckla-view');
  const answers = {};

  /** Persist current textarea/input value before navigating away. */
  function _saveCurrentInput() {
    const st = window._domainTestState;
    if (!st) return;
    const q = st.data.questions[st.currentIdx];
    if (!q) return;
    if (q.type === 'qa') {
      const ta = document.getElementById('ckla-test-qa-input');
      if (ta) answers[q.id] = ta.value;
    } else if (q.type === 'vocab_fill') {
      const inp = document.getElementById('ckla-test-fill-input');
      if (inp) answers[q.id] = inp.value;
    }
  }

  function renderQ() {
    const st = window._domainTestState;
    const q = st.data.questions[st.currentIdx];
    const total = st.data.questions.length;
    const idx = st.currentIdx;

    let bodyHtml = '';
    if (q.type === 'vocab_mc') {
      // Definition → choose the word
      const choiceHtml = (q.choices || []).map((opt, i) => {
        const sel = answers[q.id] === opt ? ' selected' : '';
        return `<button class="ckla-test-option${sel}"
                  data-answer="${escapeHtml(opt)}"
                  onclick="selectTestAnswer(${q.id}, this)">
                  ${String.fromCharCode(65 + i)}. ${escapeHtml(opt)}
                </button>`;
      }).join('');
      bodyHtml = `
        <div class="ckla-test-type-label">Vocabulary — Choose the Word</div>
        <div class="ckla-test-question">${q.question_text}</div>
        <div class="ckla-test-options">${choiceHtml}</div>`;

    } else if (q.type === 'vocab_fill') {
      // Definition → type the word
      const saved = answers[q.id] || '';
      bodyHtml = `
        <div class="ckla-test-type-label">Vocabulary — Spell the Word</div>
        <div class="ckla-test-question">${q.question_text}</div>
        <div class="ckla-test-fill-wrap">
          <input id="ckla-test-fill-input" class="ckla-test-fill-input"
                 type="text" placeholder="Type the word…"
                 value="${saved.replace(/"/g, '&quot;')}"
                 oninput="window._domainTestState && (window._domainTestState.answers[${q.id}] = this.value)" />
        </div>`;

    } else {
      // Q&A — textarea
      const saved = answers[q.id] || '';
      bodyHtml = `
        <div class="ckla-test-type-label">${q.kind ? q.kind.replace(/_/g, ' ') : 'Comprehension'}</div>
        <div class="ckla-test-question">${q.question_text}</div>
        <textarea id="ckla-test-qa-input" class="ckla-test-qa" rows="4"
                  placeholder="Write your answer…"
                  oninput="window._domainTestState && (window._domainTestState.answers[${q.id}] = this.value)"
        >${saved}</textarea>`;
    }

    view.innerHTML = `
      <div class="ckla-header">
        <button class="ckla-back-btn" onclick="loadCKLADomains()">← Back</button>
        <h2 class="ckla-title">Domain ${domainNum} Test (${idx + 1}/${total})</h2>
      </div>
      <div class="ckla-test-body">
        ${bodyHtml}
        <div class="ckla-test-nav">
          ${idx > 0
            ? `<button class="ckla-test-nav-btn" onclick="domainTestNav(-1)">← Prev</button>`
            : '<span></span>'}
          ${idx < total - 1
            ? `<button class="ckla-test-nav-btn" onclick="domainTestNav(1)">Next →</button>`
            : `<button class="ckla-test-nav-btn ckla-test-submit-btn" onclick="submitDomainTest(${domainNum})">Submit</button>`}
        </div>
      </div>`;

    // Enter key advances vocab_fill to next question (or submits on last)
    if (q.type === 'vocab_fill') {
      const inp = view.querySelector('#ckla-test-fill-input');
      if (inp) {
        inp.focus();
        inp.addEventListener('keydown', e => {
          if (e.key !== 'Enter') return;
          st._saveCurrentInput();
          if (st.currentIdx < st.data.questions.length - 1) {
            domainTestNav(1);
          } else {
            submitDomainTest(domainNum);
          }
        });
      }
    }
  }

  window._domainTestState = {
    domainNum, data, answers,
    currentIdx: 0,
    renderQ,
    _saveCurrentInput,
    startTime: Date.now(),
  };
  renderQ();
}

/** @tag ACADEMY CKLA */
function selectTestAnswer(qId, btn) {
  if (!window._domainTestState) return;
  window._domainTestState.answers[qId] = btn.dataset.answer;
  btn.closest('.ckla-test-options').querySelectorAll('.ckla-test-option').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
}

/** @tag ACADEMY CKLA */
function domainTestNav(delta) {
  if (!window._domainTestState) return;
  window._domainTestState._saveCurrentInput();
  window._domainTestState.currentIdx += delta;
  window._domainTestState.renderQ();
}

/** @tag ACADEMY CKLA */
async function submitDomainTest(domainNum) {
  if (!window._domainTestState) return;
  // Save any unsaved text input on the current question before submitting
  window._domainTestState._saveCurrentInput();
  const { data, answers, startTime } = window._domainTestState;
  const answersMap = {};
  data.questions.forEach(q => { answersMap[q.id] = answers[q.id] || ''; });
  const timeTaken = startTime ? Math.round((Date.now() - startTime) / 1000) : null;
  const view = document.getElementById('ckla-view');
  view.innerHTML = '<div class="ckla-loading">Grading…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/domain-test/${domainNum}/submit?grade=${cklaNav.grade}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: answersMap, time_taken_seconds: timeTaken }),
    });
    if (!res.ok) throw new Error('Submit failed');
    const result = await res.json();
    // Check for newly earned badges (awarded when all domain lessons complete)
    try {
      const br = await fetch(`/api/academy/ckla/badges/check?grade=${cklaNav.grade}`, { method: 'POST' });
      if (br.ok) {
        const bd = await br.json();
        if (bd.newly_earned && bd.newly_earned.length > 0) {
          result.badge_earned = true;
          result.badge_name = bd.newly_earned.map(b => b.badge_name).join(', ');
        }
      }
    } catch (_) { /* badge check is best-effort */ }
    const retryFn = result.passed ? null : () => openDomainTest(domainNum);
    _renderTestResult(result, () => loadCKLADomains(), retryFn);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Submit failed. ${e.message}</div>`;
  }
}
