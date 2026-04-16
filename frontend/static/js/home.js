/* ================================================================
   home.js — Home Dashboard: tasks, section cards, summary bar
   Section: Home
   Dependencies: core.js
   API endpoints: GET /api/tasks/today, GET /api/xp/summary,
                  GET /api/ai-coach/today, GET /api/reminders/today
   ================================================================ */

// Current view state
let currentView = 'home'; // 'home' | 'english' | 'diary'

/**
 * Switch the app to the given view.
 * @tag HOME_DASHBOARD @tag NAVIGATION
 * @param {'home'|'english'|'diary'} view
 */
function switchView(view) {
  currentView = view;
  document.body.dataset.view = view;

  // Children that may live inside .stage-area — keep .stage-area itself visible
  // (home-dashboard is INSIDE stage-area, so hiding the parent hides home too)
  const homeDash    = document.getElementById('home-dashboard');
  const idleWrap    = document.getElementById('idle-wrapper');
  const stageCard   = document.getElementById('stage-card');
  const dailyView   = document.getElementById('daily-words-view');
  const diaryView   = document.getElementById('diary-view');
  const topBar      = document.querySelector('.top-bar');
  const sidebar     = document.getElementById('sidebar');

  // Helper: set inline display, defaulting to '' (use stylesheet default)
  const show = (el, mode = '') => { if (el) el.style.display = mode; };
  const hide = (el) => { if (el) el.style.display = 'none'; };

  if (view === 'home') {
    show(homeDash, 'flex');
    hide(idleWrap);
    hide(stageCard);
    hide(dailyView);
    hide(diaryView);
    hide(topBar);                  // roadmap tabs not relevant on home
    sidebar.dataset.mode = 'home';
    updateSidebarMode('home');
    renderHomeDashboard();
  } else if (view === 'english') {
    hide(homeDash);
    show(idleWrap);                // Select a lesson card
    hide(dailyView);
    hide(diaryView);
    show(topBar);                  // roadmap tabs visible during lesson flow
    sidebar.dataset.mode = 'english';
    updateSidebarMode('english');
  } else if (view === 'diary') {
    hide(homeDash);
    hide(idleWrap);
    hide(stageCard);
    hide(dailyView);
    show(diaryView, 'flex');
    hide(topBar);                  // roadmap tabs not relevant on diary
    sidebar.dataset.mode = 'diary';
    updateSidebarMode('diary');
    if (typeof openDiarySection === 'function') openDiarySection('journal');
  }
}

/**
 * Toggle sidebar into the correct mode.
 * @tag SIDEBAR @tag NAVIGATION
 */
function updateSidebarMode(mode) {
  const engSection = document.getElementById('sb-english-section');
  const homeSection = document.getElementById('sb-home-section');
  const diarySection = document.getElementById('sb-diary-section');

  if (homeSection) homeSection.style.display = mode === 'home' ? '' : 'none';
  if (engSection) engSection.style.display = mode === 'english' ? '' : 'none';
  if (diarySection) diarySection.style.display = mode === 'diary' ? '' : 'none';
}

/**
 * Render the Home Dashboard with stub data (real data fetched from API).
 * @tag HOME_DASHBOARD @tag TODAY_TASKS
 */
async function renderHomeDashboard() {
  await renderAICoach();
  await renderReminders();
  await renderTodayTasks();
  renderSectionCards();
  renderGrowthTheme();
  await renderSummaryBar();
}

/**
 * Render AI coach message card.
 * @tag HOME_DASHBOARD @tag AI_COACH
 */
async function renderAICoach() {
  const el = document.getElementById('coach-message');
  if (!el) return;
  try {
    const res = await fetch('/api/ai-coach/today');
    const data = await res.json();
    el.textContent = data.message || 'Keep up the great work!';
  } catch {
    el.textContent = 'Ready to learn today? Let\'s go!';
  }

  // Coach sub-message
  const COACH_SUB_MSGS = [
    "Tap me anytime for help!",
    "I'm here whenever you need me!",
    "Let's learn something awesome!",
    "Ready when you are!",
    "What shall we discover today?"
  ];
  const subEl = document.getElementById('coach-sub-message');
  if (subEl) {
    subEl.textContent = COACH_SUB_MSGS[Math.floor(Math.random() * COACH_SUB_MSGS.length)];
  }

  // Activate glow ring (for direct load without splash)
  const glowRing = document.querySelector('.coach-glow-ring');
  if (glowRing) {
    setTimeout(() => glowRing.classList.add('active'), 500);
  }
}

/**
 * Render reminder banners.
 * @tag HOME_DASHBOARD @tag REMINDER
 */
async function renderReminders() {
  const container = document.getElementById('reminder-banners');
  if (!container) return;
  container.innerHTML = '';
  try {
    const res = await fetch('/api/reminders/today');
    if (!res.ok) return;
    const banners = await res.json();
    banners.forEach(b => {
      const div = document.createElement('div');
      div.className = 'reminder-banner' + (b.severity === 'danger' ? ' danger' : '');
      div.innerHTML = `<span>${b.message}</span><button class="reminder-close" onclick="this.parentElement.remove()">×</button>`;
      container.appendChild(div);
    });
  } catch { /* no reminders */ }
}

/**
 * Render Today's Tasks list.
 * @tag HOME_DASHBOARD @tag TODAY_TASKS @tag XP
 */
async function renderTodayTasks() {
  const list = document.getElementById('today-task-list');
  if (!list) return;

  // Stub tasks (replaced by API in Phase 3)
  const tasks = [
    { key: 'review', label: 'Review', detail: '—', xp: 2, is_required: true, is_done: false },
    { key: 'daily_words', label: 'Daily Words', detail: '0/10', xp: 5, is_required: false, is_done: false },
    { key: 'journal', label: 'Daily Journal', detail: '', xp: 10, is_required: false, is_done: false },
  ];

  try {
    const res = await fetch('/api/tasks/today');
    if (res.ok) {
      const data = await res.json();
      if (data && data.length) tasks.splice(0, tasks.length, ...data);
    }
  } catch { /* use stubs */ }

  list.innerHTML = tasks.map(t => `
    <div class="task-item${t.is_done ? ' done' : ''}" data-key="${t.key}">
      <span class="${t.is_required ? 'task-required' : 'task-optional'}">${t.is_required ? '★' : '○'}</span>
      <span class="task-label">${t.label}${t.detail ? ` <span class="task-detail">(${t.detail})</span>` : ''}</span>
      <span class="task-xp">+${t.xp} XP</span>
      ${t.is_done ? '<span class="task-check">✅</span>' : ''}
    </div>
  `).join('') + `
    <div class="task-divider"></div>
    <div class="bonus-row"><span class="task-optional">○</span><span class="task-label">Must Do bonus</span><span class="task-xp">+5 XP</span></div>
    <div class="bonus-row"><span class="task-optional">○</span><span class="task-label">All complete bonus</span><span class="task-xp">+15 XP</span></div>
  `;
}

/**
 * Render section cards (English, GIA's Diary, Math).
 * @tag HOME_DASHBOARD @tag NAVIGATION
 */
function renderSectionCards() {
  // Cards are static HTML; just wire click handlers
  const engCard = document.getElementById('section-card-english');
  const diaryCard = document.getElementById('section-card-diary');
  if (engCard) engCard.onclick = () => switchView('english');
  if (diaryCard) diaryCard.onclick = () => switchView('diary');
}

/**
 * Render growth theme widget — delegates to growth-theme.js (Phase 8).
 * @tag HOME_DASHBOARD @tag GROWTH_THEME
 */
function renderGrowthTheme() {
  if (typeof gtRenderTheme === 'function') {
    gtRenderTheme();
  } else {
    const el = document.getElementById('growth-theme-display');
    if (el) el.innerHTML = `<div class="theme-placeholder" style="padding:12px;text-align:center">🌱</div>`;
  }
}

/**
 * Render summary bar (Words I Know, XP, Streak).
 * @tag HOME_DASHBOARD @tag XP @tag STREAK
 */
async function renderSummaryBar() {
  try {
    const res = await fetch('/api/xp/summary');
    if (res.ok) {
      const d = await res.json();
      const xpEl = document.getElementById('summary-xp');
      const streakEl = document.getElementById('summary-streak');
      const wordsEl = document.getElementById('summary-words');
      if (xpEl) xpEl.textContent = d.total_xp ?? 0;
      if (streakEl) streakEl.textContent = (d.streak_days ?? 0) + ' days';
      if (wordsEl) wordsEl.textContent = d.words_known ?? 0;
      // Update top bar XP display
      _updateTopBarXP(d);
    }
  } catch { /* stubs already in HTML */ }
}

/**
 * Update the top-bar stars area with XP, level, and streak.
 * @tag XP @tag HOME_DASHBOARD
 */
function _updateTopBarXP(data) {
    const starsEl = document.getElementById('stars-count');
    if (!starsEl) return;
    const totalXP = data.total_xp ?? 0;
    const level = data.level ?? (Math.floor(totalXP / 100) + 1);
    const streak = data.streak_days ?? 0;
    starsEl.textContent = `${totalXP} XP`;
    // Update the star icon to include level and streak
    const starIcon = document.querySelector('.top-star-icon');
    if (starIcon) starIcon.textContent = '⭐';
    // Add level + streak after the stars-count element
    let metaEl = document.getElementById('top-xp-meta');
    if (!metaEl) {
        metaEl = document.createElement('span');
        metaEl.id = 'top-xp-meta';
        metaEl.className = 'top-xp-meta';
        starsEl.parentNode.insertBefore(metaEl, starsEl.nextSibling);
    }
    metaEl.textContent = `Lv.${level} · 🔥 ${streak}d`;
    // Also sync sidebar star-count
    const sidebarStar = document.getElementById('star-count');
    if (sidebarStar) sidebarStar.textContent = String(totalXP);
}

/**
 * Toggle an accordion panel in the English sidebar.
 * @tag SIDEBAR @tag ACCORDION @tag ENGLISH
 * @param {string} key - 'academy' | 'daily-words' | 'my-words'
 */
function toggleAccordion(key) {
  const panels = document.querySelectorAll('.sb-accordion-panel');
  panels.forEach(p => {
    if (p.dataset.key === key) {
      const isOpen = p.classList.contains('open');
      p.classList.toggle('open', !isOpen);
      const btn = document.querySelector(`.sb-accordion-btn[data-key="${key}"]`);
      if (btn) btn.classList.toggle('open', !isOpen);
    } else {
      p.classList.remove('open');
      const btn = document.querySelector(`.sb-accordion-btn[data-key="${p.dataset.key}"]`);
      if (btn) btn.classList.remove('open');
    }
  });
}

/**
 * Refresh the summary bar XP/streak numbers when called from other modules.
 * @tag HOME_DASHBOARD @tag XP @tag STREAK
 */
async function refreshHomeStats() {
    await renderSummaryBar();
    // Also update the top badges in the Today section
    try {
        const res = await fetch('/api/xp/summary');
        if (res.ok) {
            const d = await res.json();
            const topXp = document.getElementById('summary-xp-top');
            const topStreak = document.getElementById('summary-streak-top');
            if (topXp) topXp.textContent = d.total_xp ?? 0;
            if (topStreak) topStreak.textContent = d.streak_days ?? 0;
            _updateTopBarXP(d);
        }
    } catch (_) {}
}

// Initialize home view on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  switchView('home');
  renderHomeDashboard();
  // Load Daily Words sidebar if function is available (daily-words.js)
  if (typeof loadDailyWordsSection === 'function') loadDailyWordsSection();
});
