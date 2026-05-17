/* ================================================================
   ckla-grade-test.js — CKLA Grade Final Test screen
   Section: Academy
   Dependencies: ckla.js (cklaNav, _renderTestResult, escapeHtml), core.js
   API endpoints: GET  /api/academy/ckla/grade-final-test
                  POST /api/academy/ckla/grade-final-test/submit
                  GET  /api/academy/ckla/grade-final-test/status
                  POST /api/academy/ckla/badges/check
   ================================================================ */

/** Load and render the Grade Final Test question screen. @tag ACADEMY CKLA FINAL_TEST */
async function showGradeFinalTest() {
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading final test…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/grade-final-test?grade=${cklaNav.grade}`);
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    _renderGradeFinalTest(data);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load final test. ${e.message}</div>`;
  }
}

/** Render Grade Final Test question interface. @tag ACADEMY CKLA FINAL_TEST */
function _renderGradeFinalTest(data) {
  const view = document.getElementById('ckla-view');
  const questions = data.questions || [];
  if (!questions.length) {
    view.innerHTML = `<div class="ckla-empty">No questions available.<br><button class="ckla-btn" onclick="loadCKLADomains()">← Back</button></div>`;
    return;
  }

  const answers = {};
  let currentIdx = 0;

  function _gftSaveCurrentInput() {
    const q = questions[currentIdx];
    if (q.type === 'vocab_mc') return; // MC answers saved on click
    const inp = document.getElementById('gft-text-input');
    if (inp) answers[q.id] = inp.value.trim();
  }

  function renderQ() {
    const q = questions[currentIdx];
    const metaHtml = (q.domain_title || q.lesson_title)
      ? `<div class="ckla-test-meta">${[q.domain_title, q.lesson_title].filter(Boolean).join(' · ')}</div>`
      : '';

    let bodyHtml = '';
    if (q.type === 'vocab_mc') {
      const currentAns = answers[q.id] || '';
      const choicesHtml = (q.choices || []).map((ch, ci) => {
        const sel = currentAns === ch ? 'ckla-test-choice--selected' : '';
        return `<button class="ckla-test-choice ${sel}" data-choice-idx="${ci}" onclick="_gftPickChoice(${q.id}, this)">${escapeHtml(ch)}</button>`;
      }).join('');
      bodyHtml = `
        <span class="ckla-test-type-label">Vocabulary</span>
        <div class="ckla-test-question">${escapeHtml(q.question_text)}</div>
        <div class="ckla-test-choices" id="gft-choices">${choicesHtml}</div>`;
    } else if (q.type === 'word_work') {
      bodyHtml = `
        <span class="ckla-test-type-label">Word Work</span>
        <div class="ckla-test-question">${escapeHtml(q.question_text)}</div>
        ${q.hint ? `<div class="ckla-test-hint">${escapeHtml(q.hint)}</div>` : ''}
        <textarea id="gft-text-input" class="ckla-test-textarea"
          placeholder="Write your sentence here…">${escapeHtml(answers[q.id] || '')}</textarea>`;
    } else {
      // Q&A
      const kindLabel = (q.kind || 'qa').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      bodyHtml = `
        <span class="ckla-test-type-label">${kindLabel}</span>
        <div class="ckla-test-question">${escapeHtml(q.question_text)}</div>
        <textarea id="gft-text-input" class="ckla-test-textarea"
          placeholder="Type your answer…">${escapeHtml(answers[q.id] || '')}</textarea>`;
    }

    view.innerHTML = `
      <div class="ckla-header">
        <button class="ckla-back-btn" onclick="loadCKLADomains()">← Back</button>
        <h2 class="ckla-title">Grade ${data.grade} Final Test</h2>
        <span class="ckla-progress-pill">${currentIdx + 1} / ${questions.length}</span>
      </div>
      <div class="ckla-test-body">
        ${metaHtml}
        ${bodyHtml}
      </div>
      <div class="ckla-test-nav">
        ${currentIdx > 0
          ? `<button class="ckla-test-nav-btn" onclick="_gftNav(-1)">← Prev</button>`
          : '<span></span>'}
        ${currentIdx < questions.length - 1
          ? `<button class="ckla-test-nav-btn" onclick="_gftNav(1)">Next →</button>`
          : `<button class="ckla-btn" onclick="_gftSubmit()">Submit All</button>`}
      </div>`;
  }

  window._gftPickChoice = (qid, btnEl) => {
    const choice = btnEl.textContent.trim();
    answers[qid] = choice;
    const container = document.getElementById('gft-choices');
    if (!container) return;
    container.querySelectorAll('.ckla-test-choice').forEach(btn => {
      btn.classList.toggle('ckla-test-choice--selected', btn === btnEl);
    });
  };

  window._gftNav = (delta) => {
    _gftSaveCurrentInput();
    currentIdx = Math.max(0, Math.min(questions.length - 1, currentIdx + delta));
    renderQ();
  };

  window._gftSubmit = async () => {
    _gftSaveCurrentInput();
    view.innerHTML = '<div class="ckla-loading">Grading…</div>';
    try {
      const res = await fetch(`/api/academy/ckla/grade-final-test/submit?grade=${cklaNav.grade}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      });
      if (!res.ok) throw new Error('Submit failed');
      const result = await res.json();
      if (result.passed) {
        // Check for grade master badge on pass
        try {
          const br = await fetch(`/api/academy/ckla/badges/check?grade=${cklaNav.grade}`, { method: 'POST' });
          if (br.ok) {
            const bd = await br.json();
            if (bd.newly_earned && bd.newly_earned.length > 0) {
              result.badge_earned = true;
              result.badge_name = bd.newly_earned.map(b => b.badge_name).join(', ');
            }
          }
        } catch (_) { /* best-effort */ }
        _renderTestResult(result, () => loadCKLADomains());
      } else {
        _cklaRenderFinalTestWait(result);
      }
    } catch (e) {
      view.innerHTML = `<div class="ckla-empty">Submit failed. ${e.message}<br><button class="ckla-btn" onclick="loadCKLADomains()">← Back</button></div>`;
    }
  };

  renderQ();
}

/** Grade Final Test failure screen with countdown + wrong questions. @tag ACADEMY CKLA FINAL_TEST */
function _cklaRenderFinalTestWait(result) {
  const view = document.getElementById('ckla-view');
  if (!view) return;
  const pct = Math.round(result.score_pct || 0);
  const wrongList = (result.wrong_questions || []).map(q => `
    <div class="cfw-wrong-item">
      <div class="cfw-wrong-lesson">${q.lesson_title || 'Lesson'}</div>
      <div class="cfw-wrong-q">${q.question_text}</div>
      <div class="cfw-wrong-ans">Correct: ${q.correct_answer}</div>
    </div>`).join('');

  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="loadCKLADomains()">← Back</button>
      <h2 class="ckla-title">Final Test Result</h2>
    </div>
    <div class="ckla-finaltest-wait">
      <div class="cfw-score-row">
        <div class="cfw-score">${pct}%</div>
        <div class="cfw-score-label">Keep studying — you need 80% to pass!</div>
      </div>
      ${result.retry_after ? `
        <div class="cfw-timer-box">
          <div class="cfw-timer-label">Next attempt in</div>
          <div class="cfw-timer" id="cfw-countdown">…</div>
        </div>` : ''}
      ${wrongList ? `
        <div class="cfw-wrong-section">
          <div class="cfw-wrong-title">Missed Questions (${result.wrong_questions.length})</div>
          <div class="cfw-wrong-list">${wrongList}</div>
        </div>` : ''}
      <button class="cfw-review-btn" onclick="loadCKLADomains()">
        Back to Domains
      </button>
    </div>`;

  if (result.retry_after) {
    _cklaStartCountdown(new Date(result.retry_after), 'cfw-countdown');
  }
}

/** Countdown timer helper — also called from ckla.js _loadFinalTestRow. @tag ACADEMY CKLA FINAL_TEST */
function _cklaStartCountdown(targetTime, elementId) {
  function update() {
    const el = document.getElementById(elementId);
    if (!el) return;
    const diff = targetTime - Date.now();
    if (diff <= 0) {
      el.textContent = 'Ready to retry now!';
      return;
    }
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    el.textContent = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    setTimeout(update, 1000);
  }
  update();
}
