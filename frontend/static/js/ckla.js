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
    </div>`;
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


/* ── Onboarding ────────────────────────────────────────────────────────────── */

/** Show first-time onboarding modal for CKLA. @tag ACADEMY CKLA */
function showCKLAOnboarding() {
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
                onclick="document.getElementById('ckla-onboarding-modal').remove()">
          Maybe Later
        </button>
      </div>
    </div>`;
  document.body.appendChild(modal);
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** Dismiss onboarding and open CKLA view. @tag ACADEMY CKLA */
function startCKLA() {
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
