/* ================================================================
   ckla.js — CKLA grade-aware domain/lesson navigation
   Section: Academy
   Dependencies: core.js
   API endpoints: /api/academy/ckla/grades, /api/academy/ckla/domains,
                  /api/academy/ckla/domains/{n}/lessons,
                  /api/academy/ckla/lessons/{id},
                  /api/academy/ckla/badges, /api/academy/ckla/badges/check
   ================================================================ */

/** @type {{ screen: string, domainNum: number|null, domainTitle: string, grade: number }} */
let cklaNav = { screen: 'domains', domainNum: null, domainTitle: '', grade: 3 };


/* ── Init ──────────────────────────────────────────────────────────────────── */

/** Load grades and render pills in the sidebar on English section open. @tag ACADEMY CKLA */
async function initCKLA() {
  await loadCKLAGrades();
  loadCKLAReviewBadge();
}

/** Fetch available grades and populate grade pills. @tag ACADEMY CKLA */
async function loadCKLAGrades() {
  try {
    const res = await fetch('/api/academy/ckla/grades');
    if (!res.ok) return;
    const data = await res.json();
    // API returns [{grade, title, lesson_count}, ...] or {grades: [...]}
    const grades = Array.isArray(data)
      ? data.map(g => g.grade || g)
      : (data.grades || [3]);
    renderGradePills(grades);
  } catch {
    renderGradePills([3]);
  }
}

/** Render grade pill buttons in #ckla-grade-pills. @tag ACADEMY CKLA */
function renderGradePills(grades) {
  const container = document.getElementById('ckla-grade-pills');
  if (!container) return;
  container.innerHTML = grades.map(g => `
    <button class="ckla-grade-pill${g === cklaNav.grade ? ' active' : ''}"
            onclick="selectGrade(${g})">G${g}</button>
  `).join('');
  updateCKLATitle(cklaNav.grade);
}

/** Switch active grade and update sidebar title. @tag ACADEMY CKLA */
function selectGrade(grade) {
  cklaNav.grade = grade;
  document.querySelectorAll('.ckla-grade-pill').forEach(el => {
    el.classList.toggle('active', Number(el.textContent.replace('G', '')) === grade);
  });
  updateCKLATitle(grade);
}

/** Update the grade title label in the sidebar. @tag ACADEMY CKLA */
async function updateCKLATitle(grade) {
  const el = document.getElementById('ckla-section-title');
  if (!el) return;
  try {
    const res = await fetch(`/api/academy/ckla/title?grade=${grade}`);
    if (res.ok) {
      const data = await res.json();
      el.textContent = data.title || `Grade ${grade}`;
      return;
    }
  } catch { /* fall through */ }
  el.textContent = `Grade ${grade}`;
}


/* ── Entry / Exit ──────────────────────────────────────────────────────────── */

/** Show the CKLA view and render domain list. @tag ACADEMY CKLA */
function showCKLAView() {
  ['idle-wrapper', 'stage-card', 'daily-words-view'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  const view = document.getElementById('ckla-view');
  if (view) { view.style.display = 'flex'; }
  if (typeof switchView === 'function') switchView('english');
  loadCKLADomains();
}

/** Return to the idle screen from CKLA. @tag ACADEMY CKLA */
function hideCKLAView() {
  const view = document.getElementById('ckla-view');
  if (view) view.style.display = 'none';
  const idle = document.getElementById('idle-wrapper');
  if (idle) idle.style.display = '';
}


/* ── Domain list ───────────────────────────────────────────────────────────── */

/** Fetch and render all CKLA domains for the active grade. @tag ACADEMY CKLA */
async function loadCKLADomains() {
  cklaNav.screen = 'domains';
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/domains?grade=${cklaNav.grade}`);
    if (!res.ok) throw new Error('Failed to load');
    const domains = await res.json();
    _renderDomains(domains);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load domains. ${e.message}</div>`;
  }
}

/** @tag ACADEMY CKLA */
function _renderDomains(domains) {
  const view = document.getElementById('ckla-view');
  const allComplete = domains.length > 0 && domains.every(d => d.all_complete);
  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="hideCKLAView()">← Back</button>
      <h2 class="ckla-title">CKLA Grade ${cklaNav.grade}</h2>
    </div>
    <div class="ckla-domain-grid">
      ${domains.map(d => `
        <div class="ckla-domain-card" onclick="loadCKLALessons(${d.domain_num})">
          <div class="ckla-domain-num">Domain ${d.domain_num}</div>
          <div class="ckla-domain-title">${d.title}</div>
          <div class="ckla-domain-lessons">${d.lesson_count} lessons</div>
          ${d.all_complete ? `<div class="ckla-domain-test-link"
            onclick="event.stopPropagation(); openDomainTest(${d.domain_num})">
            Domain Test →</div>` : ''}
        </div>
      `).join('')}
    </div>
    ${allComplete ? `
      <div class="ckla-final-test-row" id="ckla-final-test-row">
        <div class="ckla-loading" style="font-size:.82rem">Checking final test status…</div>
      </div>` : ''}`;

  if (allComplete) _loadFinalTestRow();
}

/** Load + render the Grade Final Test call-to-action row. @tag ACADEMY CKLA */
async function _loadFinalTestRow() {
  const row = document.getElementById('ckla-final-test-row');
  if (!row) return;
  try {
    const res = await fetch(`/api/academy/ckla/grade-final-test/status?grade=${cklaNav.grade}`);
    const status = res.ok ? await res.json() : { locked: false, retry_after: null };
    if (status.locked) {
      row.innerHTML = `
        <div class="ckla-final-locked">
          <i data-lucide="lock" width="16" height="16"></i>
          <span>Grade Final Test locked — retry after ${(status.retry_after || '').replace('T', ' ')}</span>
          <div class="ckla-final-countdown" id="ckla-final-countdown"></div>
        </div>`;
      if (typeof lucide !== 'undefined') lucide.createIcons();
      _cklaStartCountdown(new Date(status.retry_after), 'ckla-final-countdown');
    } else {
      row.innerHTML = `
        <button class="ckla-final-test-btn" onclick="showGradeFinalTest()">
          <i data-lucide="trophy" width="18" height="18"></i>
          Grade Final Test
        </button>`;
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }
  } catch {
    row.innerHTML = '';
  }
}

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

  function renderQ() {
    const q = questions[currentIdx];
    view.innerHTML = `
      <div class="ckla-header">
        <button class="ckla-back-btn" onclick="loadCKLADomains()">← Back</button>
        <h2 class="ckla-title">Grade ${data.grade} Final Test</h2>
        <span class="ckla-progress-pill">${currentIdx + 1} / ${questions.length}</span>
      </div>
      <div class="ckla-test-body">
        <div class="ckla-test-meta">${q.domain_title} · ${q.lesson_title}</div>
        <div class="ckla-test-question">${q.question}</div>
        <textarea id="gft-ans" class="ckla-test-textarea"
          placeholder="Type your answer…">${answers[q.id] || ''}</textarea>
      </div>
      <div class="ckla-test-nav">
        ${currentIdx > 0
          ? `<button class="ckla-test-nav-btn" onclick="_gftNav(-1)">← Prev</button>`
          : '<span></span>'}
        ${currentIdx < questions.length - 1
          ? `<button class="ckla-test-nav-btn" onclick="_gftNav(1)">Next →</button>`
          : `<button class="ckla-btn" onclick="_gftSubmit()">Submit All</button>`}
      </div>`;
    window._gftSave = () => {
      const ta = document.getElementById('gft-ans');
      if (ta) answers[q.id] = ta.value.trim();
    };
  }

  window._gftNav = (delta) => {
    window._gftSave?.();
    currentIdx = Math.max(0, Math.min(questions.length - 1, currentIdx + delta));
    renderQ();
  };

  window._gftSubmit = async () => {
    window._gftSave?.();
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

/** Grade Final Test 실패 후 대기 화면 (카운트다운 + 틀린 문제). @tag ACADEMY CKLA FINAL_TEST */
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

/** Countdown timer helper. @tag ACADEMY CKLA FINAL_TEST */
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


/* ── Domain test ───────────────────────────────────────────────────────────── */

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
  let currentIdx = 0;
  const answers = {};

  function renderQ() {
    const q = data.questions[currentIdx];
    const total = data.questions.length;
    view.innerHTML = `
      <div class="ckla-header">
        <button class="ckla-back-btn" onclick="loadCKLADomains()">← Back</button>
        <h2 class="ckla-title">Domain ${domainNum} Test (${currentIdx + 1}/${total})</h2>
      </div>
      <div class="ckla-test-body">
        <div class="ckla-test-passage">${q.passage_excerpt || ''}</div>
        <div class="ckla-test-question">${q.question_text}</div>
        <div class="ckla-test-options">
          ${(q.options || []).map((opt, i) => `
            <button class="ckla-test-option${answers[q.id] === opt ? ' selected' : ''}"
                    onclick="selectTestAnswer(${q.id}, '${opt.replace(/'/g, "\\'")}', this)">
              ${String.fromCharCode(65 + i)}. ${opt}
            </button>
          `).join('')}
        </div>
        <div class="ckla-test-nav">
          ${currentIdx > 0 ? `<button class="ckla-test-nav-btn" onclick="domainTestNav(-1)">← Prev</button>` : '<span></span>'}
          ${currentIdx < total - 1
            ? `<button class="ckla-test-nav-btn" onclick="domainTestNav(1)">Next →</button>`
            : `<button class="ckla-test-nav-btn ckla-test-submit-btn" onclick="submitDomainTest(${domainNum})">Submit</button>`}
        </div>
      </div>`;
  }

  window._domainTestState = { domainNum, data, answers, currentIdx, renderQ };
  renderQ();
}

/** @tag ACADEMY CKLA */
function selectTestAnswer(qId, answer, btn) {
  if (!window._domainTestState) return;
  window._domainTestState.answers[qId] = answer;
  btn.closest('.ckla-test-options').querySelectorAll('.ckla-test-option').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
}

/** @tag ACADEMY CKLA */
function domainTestNav(delta) {
  if (!window._domainTestState) return;
  window._domainTestState.currentIdx += delta;
  window._domainTestState.renderQ();
}

/** @tag ACADEMY CKLA */
async function submitDomainTest(domainNum) {
  if (!window._domainTestState) return;
  const { data, answers } = window._domainTestState;
  const responses = data.questions.map(q => ({ question_id: q.id, answer: answers[q.id] || '' }));
  const view = document.getElementById('ckla-view');
  view.innerHTML = '<div class="ckla-loading">Grading…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/domain-test/${domainNum}/submit?grade=${cklaNav.grade}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses }),
    });
    if (!res.ok) throw new Error('Submit failed');
    const result = await res.json();
    _renderTestResult(result, () => loadCKLADomains());
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Submit failed. ${e.message}</div>`;
  }
}


/* ── Test result shared renderer ───────────────────────────────────────────── */

/** @tag ACADEMY CKLA */
function _renderTestResult(result, backFn) {
  const view = document.getElementById('ckla-view');
  const passed = result.passed;
  const pct = Math.round(result.score_pct || 0);
  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="(${backFn.toString()})()">← Back</button>
      <h2 class="ckla-title">Test Result</h2>
    </div>
    <div class="ckla-test-result">
      <div class="ckla-result-score ${passed ? 'ckla-result-pass' : 'ckla-result-fail'}">${pct}%</div>
      <div class="ckla-result-label">${passed ? 'Passed!' : 'Not yet — keep studying'}</div>
      ${result.xp_awarded ? `<div class="ckla-result-xp">+${result.xp_awarded} XP</div>` : ''}
      ${result.badge_earned ? `<div class="ckla-result-badge">Badge earned: ${result.badge_name}</div>` : ''}
      <button class="ckla-back-btn" onclick="(${backFn.toString()})()">← Back</button>
    </div>`;
}


/* ── Lesson list ───────────────────────────────────────────────────────────── */

/** Fetch and render lessons for one domain. @tag ACADEMY CKLA */
async function loadCKLALessons(domainNum) {
  cklaNav.screen = 'lessons';
  cklaNav.domainNum = domainNum;
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/domains/${domainNum}/lessons?grade=${cklaNav.grade}`);
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    cklaNav.domainTitle = data.domain.title;
    _renderLessons(data);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load lessons. ${e.message}</div>`;
  }
}

/** @tag ACADEMY CKLA */
function _renderLessons(data) {
  const view = document.getElementById('ckla-view');
  const progressIcons = [
    { key: 'reading_done',        label: 'Read' },
    { key: 'vocab_done',          label: 'Words' },
    { key: 'questions_attempted', label: 'Q&A', isCount: true },
    { key: 'word_work_done',      label: 'WW' },
  ];

  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="loadCKLADomains()">← Domains</button>
      <h2 class="ckla-title">D${data.domain.domain_num}: ${data.domain.title}</h2>
    </div>
    <div class="ckla-lesson-list">
      ${data.lessons.map(l => {
        const p = l.progress;
        const chips = progressIcons.map(pi => {
          const done = pi.isCount ? (p[pi.key] > 0) : p[pi.key];
          return `<span class="ckla-chip ${done ? 'ckla-chip-done' : ''}" title="${pi.label}">${pi.label}</span>`;
        }).join('');
        const isDone = p.completed;
        const diff = p.difficulty_rating;
        const diffLabel = diff === 'easy' ? 'Easy' : diff === 'hard' ? 'Hard' : '';
        return `
          <div class="ckla-lesson-row${isDone ? ' ckla-lesson-done' : ''}"
               onclick="openCKLALesson(${l.id})">
            <div class="ckla-lesson-meta">
              <span class="ckla-lesson-num">Lesson ${l.lesson_num}</span>
              ${diffLabel ? `<span class="ckla-lesson-diff ckla-diff-${diff}">${diffLabel}</span>` : ''}
              ${l.word_work_word ? `<span class="ckla-lesson-ww">★ ${l.word_work_word}</span>` : ''}
            </div>
            <div class="ckla-lesson-title">${l.title}</div>
            <div class="ckla-lesson-chips">${chips}</div>
          </div>`;
      }).join('')}
    </div>`;
}


/* ── Lesson detail ─────────────────────────────────────────────────────────── */

/** Fetch lesson data and enter lesson view (delegates to ckla-lesson.js). @tag ACADEMY CKLA */
async function openCKLALesson(lessonId) {
  cklaNav.screen = 'lesson';
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading lesson…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/lessons/${lessonId}`);
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    renderCKLALesson(data);   // defined in ckla-lesson.js
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load lesson. ${e.message}</div>`;
  }
}


/* ── Badge gallery ─────────────────────────────────────────────────────────── */

/** Open the badge gallery modal. @tag ACADEMY CKLA */
async function showBadgeGallery() {
  const existing = document.getElementById('ckla-badge-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'ckla-badge-modal';
  modal.className = 'ckla-badge-modal';
  modal.innerHTML = `
    <div class="ckla-badge-modal-box">
      <div class="ckla-badge-modal-header">
        <h3 class="ckla-badge-modal-title">CKLA Badges</h3>
        <button class="ckla-badge-modal-close" onclick="document.getElementById('ckla-badge-modal').remove()">
          <i data-lucide="x" width="16" height="16"></i>
        </button>
      </div>
      <div class="ckla-badge-modal-body">
        <div class="ckla-loading">Loading badges…</div>
      </div>
    </div>`;
  document.body.appendChild(modal);
  if (typeof lucide !== 'undefined') lucide.createIcons();

  try {
    const res = await fetch(`/api/academy/ckla/badges?grade=${cklaNav.grade}`);
    if (!res.ok) throw new Error('Failed to load');
    const badges = await res.json();
    const body = modal.querySelector('.ckla-badge-modal-body');
    body.innerHTML = `
      <div class="ckla-badge-grid">
        ${(Array.isArray(badges) ? badges : badges.badges || []).map(b => `
          <div class="ckla-badge-card${b.earned ? ' ckla-badge-card--earned' : ''}">
            <div class="ckla-badge-icon">${getBadgeIcon(b.badge_key)}</div>
            <div class="ckla-badge-name">${b.badge_name}</div>
            ${b.earned ? `<div class="ckla-badge-earned-date">${formatDate(b.earned_at)}</div>` : ''}
          </div>
        `).join('')}
      </div>`;
  } catch {
    const body = modal.querySelector('.ckla-badge-modal-body');
    body.innerHTML = '<div class="ckla-empty">Could not load badges.</div>';
  }
}

/** Map badge key to a Lucide icon string. @tag ACADEMY CKLA */
function getBadgeIcon(badgeKey) {
  if (badgeKey === 'grade_3_master' || badgeKey.includes('grade')) {
    return '<i data-lucide="crown" width="28" height="28"></i>';
  }
  const num = parseInt(badgeKey.replace('domain_', '').replace('_complete', ''), 10);
  if (!isNaN(num)) {
    return `<i data-lucide="book-open" width="28" height="28"></i>`;
  }
  return '<i data-lucide="award" width="28" height="28"></i>';
}


/* ── SM-2 Review ───────────────────────────────────────────────────────────── */

/** Load due-review count and update sidebar badge. @tag ACADEMY CKLA SM2 */
async function loadCKLAReviewBadge() {
  try {
    const res = await fetch('/api/academy/ckla/review/due');
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById('ckla-review-badge');
    if (!badge) return;
    if (data.due_count > 0) {
      badge.textContent = data.due_count;
      badge.style.display = 'inline-flex';
    } else {
      badge.style.display = 'none';
    }
  } catch { /* silent */ }
}

/** Show the CKLA SM-2 review screen. @tag ACADEMY CKLA SM2 */
async function showCKLAReview() {
  const view = document.getElementById('ckla-view');
  if (!view) return;
  ['idle-wrapper', 'stage-card', 'daily-words-view'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  view.style.display = 'flex';
  if (typeof switchView === 'function') switchView('english');

  view.innerHTML = '<div class="ckla-loading">Loading review…</div>';
  try {
    const res = await fetch('/api/academy/ckla/review/due');
    if (!res.ok) throw new Error('Failed');
    const data = await res.json();
    _renderCKLAReview(data.words || []);
  } catch {
    view.innerHTML = `
      <div class="ckla-error">
        <i data-lucide="alert-triangle" width="24" height="24"></i>
        <p>Could not load review words.</p>
        <button class="ckla-btn" onclick="showCKLAView()">Back</button>
      </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }
}

/** Render SM-2 flashcard review for the given word list. @tag ACADEMY CKLA SM2 */
function _renderCKLAReview(words) {
  const view = document.getElementById('ckla-view');
  if (!view) return;

  if (!words.length) {
    view.innerHTML = `
      <div class="ckla-domain-view">
        <div class="ckla-domain-header">
          <button class="ckla-back-btn" onclick="showCKLAView()">
            <i data-lucide="arrow-left" width="16" height="16"></i> Back
          </button>
          <h2 class="ckla-domain-title">CKLA Review</h2>
        </div>
        <div class="ckla-empty">
          <i data-lucide="check-circle-2" width="40" height="40" style="color:var(--math-primary)"></i>
          <p>All caught up! No words due for review today.</p>
          <button class="ckla-btn" onclick="showCKLAView()">Back to Domains</button>
        </div>
      </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    return;
  }

  let idx = 0;
  let correct = 0;
  let flipped = false;

  function renderCard() {
    if (idx >= words.length) {
      view.innerHTML = `
        <div class="ckla-domain-view">
          <div class="ckla-domain-header">
            <button class="ckla-back-btn" onclick="showCKLAView()">
              <i data-lucide="arrow-left" width="16" height="16"></i> Back
            </button>
            <h2 class="ckla-domain-title">Review Complete</h2>
          </div>
          <div class="ckla-empty">
            <i data-lucide="trophy" width="40" height="40" style="color:var(--arcade-primary)"></i>
            <p style="font-size:1.1rem;font-weight:700;color:var(--text-primary);margin:8px 0">
              ${correct} / ${words.length} correct
            </p>
            <button class="ckla-btn" onclick="showCKLAView()">Back to Domains</button>
          </div>
        </div>`;
      loadCKLAReviewBadge();
      if (typeof lucide !== 'undefined') lucide.createIcons();
      return;
    }

    const w = words[idx];
    flipped = false;
    view.innerHTML = `
      <div class="ckla-domain-view">
        <div class="ckla-domain-header">
          <button class="ckla-back-btn" onclick="showCKLAView()">
            <i data-lucide="arrow-left" width="16" height="16"></i> Back
          </button>
          <h2 class="ckla-domain-title">CKLA Review</h2>
          <span class="ckla-progress-pill">${idx + 1} / ${words.length}</span>
        </div>
        <div class="ckla-review-card" id="ckla-rev-card" onclick="flipReviewCard()">
          <div class="ckla-review-front" id="ckla-rev-front">
            <div class="ckla-review-word">${w.word}</div>
            <div class="ckla-review-hint" style="color:var(--text-hint);font-size:.82rem;margin-top:8px">
              Tap to reveal definition
            </div>
          </div>
          <div class="ckla-review-back" id="ckla-rev-back" style="display:none">
            <div class="ckla-review-pos" style="font-size:.75rem;color:var(--text-hint);font-style:italic;margin-bottom:4px">
              ${w.part_of_speech || ''}
            </div>
            <div class="ckla-review-def">${w.definition}</div>
            ${w.example_1 ? `<div class="ckla-review-ex" style="font-style:italic;font-size:.82rem;color:var(--text-secondary);margin-top:8px">"${w.example_1}"</div>` : ''}
          </div>
        </div>
        <div class="ckla-review-actions" id="ckla-rev-actions" style="display:none">
          <button class="ckla-btn ckla-btn--wrong" onclick="submitReview(${w.id}, false)">
            <i data-lucide="x" width="16" height="16"></i> Missed it
          </button>
          <button class="ckla-btn ckla-btn--correct" onclick="submitReview(${w.id}, true)">
            <i data-lucide="check" width="16" height="16"></i> Got it
          </button>
        </div>
      </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }

  window.flipReviewCard = function () {
    if (flipped) return;
    flipped = true;
    const front = document.getElementById('ckla-rev-front');
    const back  = document.getElementById('ckla-rev-back');
    const acts  = document.getElementById('ckla-rev-actions');
    if (front) front.style.display = 'none';
    if (back)  back.style.display  = '';
    if (acts)  acts.style.display  = 'flex';
  };

  window.submitReview = async function (wordId, isCorrect) {
    if (isCorrect) correct++;
    idx++;
    try {
      await fetch('/api/academy/ckla/review/result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word_id: wordId, is_correct: isCorrect, attempts: 1 }),
      });
    } catch { /* non-blocking */ }
    renderCard();
  };

  renderCard();
}


/* ── Onboarding ────────────────────────────────────────────────────────────── */

/** Show first-time onboarding modal for CKLA. @tag ACADEMY CKLA */
function showCKLAOnboarding() {
  if (localStorage.getItem('ckla_onboarded') === '1') return;
  const existing = document.getElementById('ckla-onboarding-modal');
  if (existing) return;

  const modal = document.createElement('div');
  modal.id = 'ckla-onboarding-modal';
  modal.className = 'ckla-onboarding-modal';
  modal.innerHTML = `
    <div class="ckla-onboarding-content">
      <div class="ckla-onboarding-icon">
        <i data-lucide="book-open" width="28" height="28"></i>
      </div>
      <h3 class="ckla-onboarding-title">Welcome to CKLA!</h3>
      <p class="ckla-onboarding-desc">
        CKLA is your main reading and language arts program.
        Work through domains, complete lessons, and earn badges
        as you master each unit.
      </p>
      <div class="ckla-onboarding-actions">
        <button class="ckla-onboarding-btn ckla-onboarding-btn--primary" onclick="startCKLA()">
          Start Learning
        </button>
        <button class="ckla-onboarding-btn ckla-onboarding-btn--secondary"
                onclick="localStorage.setItem('ckla_onboarded','1'); document.getElementById('ckla-onboarding-modal').remove()">
          Maybe Later
        </button>
      </div>
    </div>`;
  document.body.appendChild(modal);
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** Dismiss onboarding and open CKLA view. @tag ACADEMY CKLA */
function startCKLA() {
  localStorage.setItem('ckla_onboarded', '1');
  const modal = document.getElementById('ckla-onboarding-modal');
  if (modal) modal.remove();
  showCKLAView();
}


/* ── DUX accordion init ────────────────────────────────────────────────────── */

/** Ensure DUX accordion state is restored on English section open. @tag ACADEMY CKLA */
function setupDUXAccordion() {
  // DUX accordion uses the shared toggleAccordion('dux') from home.js.
  // This hook is called from child.js when English section is shown
  // so DUX starts collapsed if nothing is selected.
  const panel = document.querySelector('.sb-accordion-panel[data-key="dux"]');
  if (panel && !panel.classList.contains('open')) {
    // Leave collapsed — user opens it when needed
  }
}


/* ── Utilities ─────────────────────────────────────────────────────────────── */

/** Format ISO date string to short readable form. @tag ACADEMY CKLA */
function formatDate(isoStr) {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return isoStr.slice(0, 10);
  }
}
