/* ================================================================
   ckla.js — CKLA grade-aware domain/lesson navigation (shell)
   Section: Academy
   Dependencies: core.js
   Dependents: ckla-grade-test.js (Grade Final Test),
               ckla-domain-test.js (Domain Test)
   API endpoints: /api/academy/ckla/grades, /api/academy/ckla/title,
                  /api/academy/ckla/domains, /api/academy/ckla/domains/{n}/lessons,
                  /api/academy/ckla/lessons/{id},
                  /api/academy/ckla/badges, /api/academy/ckla/grade-final-test/status,
                  /api/review/today
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
  // switchView('english') clears idle-wrapper's inline style, so use .hidden
  // class which survives that clearing (display:none !important via legacy-app.css).
  if (typeof switchView === 'function') switchView('english');
  const iw = document.getElementById('idle-wrapper');
  if (iw) iw.classList.add('hidden');
  const sc = document.getElementById('stage-card');
  if (sc) sc.classList.add('hidden');
  const dw = document.getElementById('daily-words-view');
  if (dw) dw.style.display = 'none';
  const view = document.getElementById('ckla-view');
  if (view) { view.style.display = 'flex'; }
  const sidebar = document.getElementById('sidebar');
  if (sidebar) { sidebar.classList.add('collapsed'); localStorage.setItem('sb_collapsed', '1'); }
  document.body.classList.add('ckla-active');
  loadCKLADomains();
}

/** Return to the idle screen from CKLA. @tag ACADEMY CKLA */
function hideCKLAView() {
  const view = document.getElementById('ckla-view');
  if (view) view.style.display = 'none';
  // Remove .hidden added by showCKLAView so switchView can restore idle-wrapper.
  const iw = document.getElementById('idle-wrapper');
  if (iw) iw.classList.remove('hidden');
  document.body.classList.remove('ckla-active');
  if (typeof switchView === 'function') switchView('english');
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
    const data = await res.json();
    _renderDomains(data.domains || data, data.rank, data.completion_pct);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load domains. ${e.message}</div>`;
  }
}

/** @tag ACADEMY CKLA */
function _renderDomains(domains, rank, completionPct) {
  const view = document.getElementById('ckla-view');
  const allComplete = domains.length > 0 && domains.every(d => d.all_complete);
  const rankPill = rank
    ? `<span class="ckla-rank-pill ckla-rank-${rank.toLowerCase()}">${rank}</span>`
    : '';
  const progressLine = typeof completionPct === 'number'
    ? `<div class="ckla-grade-progress">
        <div class="ckla-grade-progress-bar" style="width:${completionPct}%"></div>
       </div>
       <div class="ckla-grade-progress-label">${completionPct}% complete</div>`
    : '';
  view.innerHTML = `
    <div class="ckla-header">
      <div class="ckla-header-info">
        <div class="ckla-header-title-row">
          <h2 class="ckla-title">CKLA Grade ${cklaNav.grade}</h2>
          ${rankPill}
        </div>
        ${progressLine}
      </div>
      <button class="eng-exit-btn" onclick="hideCKLAView()"><i data-lucide="x"></i> Exit</button>
    </div>
    <div class="ckla-domain-grid">
      ${domains.map(d => d.locked ? `
        <div class="ckla-domain-card ckla-domain-card--locked" title="Complete Domain ${d.domain_num - 1} first">
          <div class="ckla-domain-lock-icon"><i data-lucide="lock" width="18" height="18"></i></div>
          <div class="ckla-domain-num">Domain ${d.domain_num}</div>
          <div class="ckla-domain-title">${d.title}</div>
          <div class="ckla-domain-locked-hint">Complete Domain ${d.domain_num - 1} first</div>
        </div>
      ` : `
        <div class="ckla-domain-card" onclick="loadCKLALessons(${d.domain_num})">
          <div class="ckla-domain-num">Domain ${d.domain_num}</div>
          <div class="ckla-domain-title">${d.title}</div>
          <div class="ckla-domain-lessons">${d.completed_count != null ? `${d.completed_count}/` : ''}${d.lesson_count} lessons</div>
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

  if (typeof lucide !== 'undefined') lucide.createIcons();
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

// Grade Final Test implementation → ckla-grade-test.js

// Domain Test implementation → ckla-domain-test.js


/* ── Test result shared renderer ───────────────────────────────────────────── */

/**
 * @tag ACADEMY CKLA
 * @param result  — API response with score_pct, passed, correct, total, xp_awarded
 * @param backFn  — called when "← Back" is clicked
 * @param retryFn — optional; if provided, shows "Try Again" button (for fail case)
 */
function _renderTestResult(result, backFn, retryFn) {
  const view = document.getElementById('ckla-view');
  const passed = result.passed;
  const pct = Math.round(result.score_pct || 0);
  const detail = (result.correct != null && result.total != null)
    ? `${result.correct} / ${result.total} correct`
    : '';
  const retryBtn = (!passed && retryFn)
    ? `<button class="ckla-result-retry-btn" id="ckla-result-retry">Try Again</button>`
    : '';
  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" id="ckla-result-back">← Back</button>
      <h2 class="ckla-title">Test Result</h2>
    </div>
    <div class="ckla-test-result">
      <div class="ckla-result-score ${passed ? 'ckla-result-pass' : 'ckla-result-fail'}">${pct}%</div>
      ${detail ? `<div class="ckla-result-detail">${detail}</div>` : ''}
      <div class="ckla-result-label">${passed ? 'Passed!' : 'Not yet — keep studying'}</div>
      ${result.xp_awarded ? `<div class="ckla-result-xp">+${result.xp_awarded} XP</div>` : ''}
      ${result.badge_earned ? `<div class="ckla-result-badge">Badge earned: ${result.badge_name || ''}</div>` : ''}
      <div class="ckla-result-actions">
        ${retryBtn}
        <button class="ckla-back-btn" id="ckla-result-back2">← Back to Domains</button>
      </div>
    </div>`;
  view.querySelector('#ckla-result-back').addEventListener('click', backFn);
  view.querySelector('#ckla-result-back2').addEventListener('click', backFn);
  if (!passed && retryFn) {
    view.querySelector('#ckla-result-retry').addEventListener('click', retryFn);
  }
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
    { key: 'reading_done',  label: 'Read' },
    { key: 'vocab_done',    label: 'Words' },
    { key: 'qa_done',       label: 'Q&A' },
    { key: 'word_work_done', label: 'WW' },
  ];

  const domainNum = data.domain.domain_num;
  const allComplete = data.domain.all_complete;
  const bannerHtml = allComplete ? `
    <div class="ckla-domain-test-banner">
      <div class="ckla-domain-test-banner-text">
        <div class="ckla-domain-test-banner-title">All lessons complete!</div>
        <div class="ckla-domain-test-banner-sub">Take the Domain Test to earn your badge</div>
      </div>
      <button class="ckla-domain-test-banner-btn" onclick="openDomainTest(${domainNum})">
        Start Test
      </button>
    </div>` : '';

  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="loadCKLADomains()">← Domains</button>
      <h2 class="ckla-title">D${domainNum}: ${data.domain.title}</h2>
    </div>
    ${bannerHtml}
    <div class="ckla-lesson-list">
      ${data.lessons.map(l => {
        const p = l.progress;
        const chips = progressIcons.map(pi => {
          const done = !!p[pi.key];
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
              ${l.word_work_word ? `<span class="ckla-lesson-ww"><i data-lucide="star" style="width:12px;height:12px;vertical-align:-1px;stroke-width:1.5"></i> ${l.word_work_word}</span>` : ''}
            </div>
            <div class="ckla-lesson-title">${l.title}</div>
            <div class="ckla-lesson-chips">${chips}</div>
          </div>`;
      }).join('')}
    </div>`;
  if (typeof lucide !== 'undefined') lucide.createIcons();
}


/* ── Lesson detail ─────────────────────────────────────────────────────────── */

/** Fetch lesson data and enter lesson view (delegates to ckla-lesson.js). @tag ACADEMY CKLA */
async function openCKLALesson(lessonId) {
  cklaNav.screen = 'lesson';
  const sidebar = document.getElementById('sidebar');
  if (sidebar) { sidebar.classList.add('collapsed'); localStorage.setItem('sb_collapsed', '1'); }
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
    if (typeof lucide !== 'undefined') lucide.createIcons();
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
    const res = await fetch('/api/review/today?source=ckla');
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById('ckla-review-badge');
    if (!badge) return;
    if (data.count > 0) {
      badge.textContent = data.count;
      badge.style.display = 'inline-flex';
    } else {
      badge.style.display = 'none';
    }
  } catch { /* silent */ }
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
