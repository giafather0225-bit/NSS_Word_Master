/* ================================================================
   home.js — Home Dashboard: tasks, section cards, summary bar
   Section: Home
   Dependencies: core.js
   API endpoints: GET /api/tasks/today, GET /api/xp/summary,
                  GET /api/xp/weekly, GET /api/ai-coach/today,
                  GET /api/reminders/today
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
    if (typeof openDiarySection === 'function') openDiarySection('today');
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
  const mathSection = document.getElementById('sb-math-section');

  if (homeSection) homeSection.style.display = mode === 'home' ? '' : 'none';
  if (engSection) engSection.style.display = mode === 'english' ? '' : 'none';
  if (diarySection) diarySection.style.display = mode === 'diary' ? '' : 'none';
  if (mathSection) mathSection.style.display = mode === 'math' ? '' : 'none';
}

/**
 * Render the Home Dashboard with stub data (real data fetched from API).
 * @tag HOME_DASHBOARD @tag TODAY_TASKS
 */
async function renderHomeDashboard() {
  renderGreeting();
  await renderAICoach();
  await renderReminders();
  await renderTodayTasks();
  renderSectionCards();
  renderGrowthTheme();
  await renderWeeklyStrip();
  bindTopRightMenu();
  await renderSummaryBar();
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/**
 * Render greeting block — date + time-of-day salutation.
 * @tag HOME_DASHBOARD
 */
function renderGreeting() {
  const dateEl = document.getElementById('greeting-date');
  const timeEl = document.getElementById('greeting-time');
  const nameEl = document.getElementById('greeting-name');
  if (dateEl) {
    const d = new Date();
    const fmt = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    dateEl.textContent = fmt.toUpperCase();
  }
  if (timeEl) {
    const h = new Date().getHours();
    let phrase = 'Hello,';
    if (h >= 5 && h < 12) phrase = 'Good morning,';
    else if (h >= 12 && h < 18) phrase = 'Good afternoon,';
    else phrase = 'Good evening,';
    timeEl.textContent = phrase;
  }
  if (nameEl && !nameEl.textContent.trim()) nameEl.textContent = 'Gia';
}

/**
 * Wire up the top-right ⋯ menu (open/close + outside click + Esc).
 * @tag HOME_DASHBOARD @tag NAVIGATION
 */
function bindTopRightMenu() {
  const btn = document.getElementById('trm-btn');
  const dd  = document.getElementById('trm-dropdown');
  if (!btn || !dd || btn.dataset.bound === '1') return;
  btn.dataset.bound = '1';

  const setOpen = (open) => {
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    dd.setAttribute('aria-hidden',  open ? 'false' : 'true');
  };

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = btn.getAttribute('aria-expanded') !== 'true';
    setOpen(open);
  });

  document.addEventListener('click', (e) => {
    if (!dd.contains(e.target) && !btn.contains(e.target)) setOpen(false);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setOpen(false);
  });
}

/** Placeholder entry point — wired in Phase 3. */
function openSettings() {
  if (typeof openSettingsModal === 'function') return openSettingsModal();
  console.info('[home] Settings — coming soon');
}

/**
 * Render AI coach message card.
 * @tag HOME_DASHBOARD @tag AI_COACH
 */
async function renderAICoach() {
  const el = document.getElementById('coach-message');
  if (!el) return;
  try {
    const data = await apiFetchJSON('/api/ai-coach/today');
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
 * Map a task key to a section bucket used by the grouped UI.
 * Backend API is currently flat; Phase 3 will add explicit `section` field.
 * @tag HOME_DASHBOARD @tag TODAY_TASKS
 */
function _sectionOfTask(key) {
  if (key === 'review') return 'review';
  if (key === 'journal') return 'diary';
  if (key === 'daily_words' || key === 'academy' || key === 'english') return 'english';
  if (key === 'math') return 'math';
  if (key === 'arcade') return 'arcade';
  return 'english';
}

const _SECTION_LABELS = {
  english: 'English',
  math:    'Math',
  diary:   'Diary',
  review:  'Review',
  arcade:  'Arcade',
};

const _SECTION_ORDER = ['english', 'math', 'diary', 'review', 'arcade'];

function _escape(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

/**
 * Render Today's Tasks list — grouped by section, with progress bar + XP pills.
 * @tag HOME_DASHBOARD @tag TODAY_TASKS @tag XP
 */
async function renderTodayTasks() {
  const list = document.getElementById('today-task-list');
  if (!list) return;

  // Stub tasks (replaced by API in Phase 3)
  const tasks = [
    { key: 'review', label: 'Review', detail: '', xp: 2, is_required: true, is_done: false },
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

  // Group by section
  const groups = {};
  tasks.forEach(t => {
    const sec = t.section || _sectionOfTask(t.key);
    (groups[sec] ||= []).push(t);
  });

  const groupHtml = _SECTION_ORDER
    .filter(sec => groups[sec] && groups[sec].length)
    .map(sec => {
      const items = groups[sec];
      const done  = items.filter(t => t.is_done).length;
      const rows = items.map(t => {
        const detail = t.detail ? ` (${_escape(t.detail)})` : '';
        const dueNow = !t.is_done && (t.due === 'now' || t.is_required);
        const pill   = dueNow ? `<span class="tc-now-pill">NOW</span>` : '';
        return `
          <div class="tc-row${t.is_done ? ' done' : ''}${dueNow ? ' is-due-now' : ''}"
               data-key="${_escape(t.key)}" data-section="${sec}">
            <span class="tc-check" aria-hidden="true"></span>
            <span class="tc-label">${_escape(t.label)}${detail}</span>
            ${pill}
            <span class="tc-xp-pill">+${Number(t.xp) || 0}</span>
          </div>
        `;
      }).join('');
      return `
        <div class="tc-group" data-section="${sec}">
          <div class="tc-group-head">
            <span class="tc-group-label"><span class="tc-group-dot"></span>${_SECTION_LABELS[sec] || sec}</span>
            <span class="tc-group-count">${done}/${items.length}</span>
          </div>
          ${rows}
        </div>
      `;
    }).join('');

  list.innerHTML = groupHtml || '<div class="tc-sub">No tasks for today.</div>';

  // Summary counts + progress bar
  const total = tasks.length;
  const doneCount = tasks.filter(t => t.is_done).length;
  const totalXp  = tasks.reduce((s, t) => s + (Number(t.xp) || 0), 0);
  const earnedXp = tasks.filter(t => t.is_done).reduce((s, t) => s + (Number(t.xp) || 0), 0);

  const countEl = document.getElementById('today-tasks-count');
  if (countEl) countEl.textContent = `${doneCount} / ${total} done`;
  const xpEl = document.getElementById('today-tasks-xp');
  if (xpEl) xpEl.textContent = `Set by parent · ${earnedXp} / ${totalXp} XP earned`;
  const fillEl = document.getElementById('today-tasks-progress-fill');
  const pct = total ? Math.round((doneCount / total) * 100) : 0;
  if (fillEl) fillEl.style.width = pct + '%';
  const progressBar = fillEl ? fillEl.parentElement : null;
  if (progressBar) progressBar.setAttribute('aria-valuenow', String(pct));

  window._todayTaskCounts = { total, done: doneCount };
  const doneStatEl = document.getElementById('summary-done');
  if (doneStatEl) doneStatEl.textContent = `${doneCount}/${total}`;

  // Wire click handlers
  list.querySelectorAll('.tc-row').forEach(el => {
    if (el.classList.contains('done')) return;
    el.addEventListener('click', () => _navigateTask(el.dataset.key));
  });
}

/**
 * Render the weekly activity bar chart.
 * @tag HOME_DASHBOARD @tag STREAK
 */
async function renderWeeklyStrip() {
  const container = document.getElementById('weekly-bars');
  if (!container) return;

  // Fetch real 7-day activity. On failure, fall back to an empty week.
  let days = Array.from({ length: 7 }, () => ({ label: '·', value: 0 }));
  try {
    const res = await fetch('/api/xp/weekly');
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length) {
        days = data.map(d => ({ label: d.label || '·', value: Number(d.value) || 0 }));
      }
    }
  } catch { /* fall back to empty */ }

  const MAX_H = 56; // px
  container.innerHTML = days.map(d => {
    const h = Math.max(4, Math.round(d.value * MAX_H));
    let tone = '';
    if (d.value >= 0.9) tone = 'ws-bar--t3';
    else if (d.value >= 0.5) tone = 'ws-bar--t2';
    else if (d.value > 0) tone = 'ws-bar--t1';
    return `
      <div class="ws-day">
        <div class="ws-bar ${tone}" style="height:${h}px"></div>
        <div class="ws-label">${d.label}</div>
      </div>
    `;
  }).join('');
}

/**
 * Navigate to the appropriate screen when a task item is clicked.
 * @tag HOME_DASHBOARD @tag TODAY_TASKS @tag NAVIGATION
 * @param {string} key - task key from API (review|daily_words|academy|journal)
 */
function _navigateTask(key) {
  switch (key) {
    case 'review':
      switchView('english');
      setTimeout(() => { const btn = document.getElementById('btn-review'); if (btn) btn.click(); }, 300);
      break;
    case 'daily_words':
      switchView('english');
      setTimeout(() => { toggleAccordion('daily-words'); if (typeof showDailyWordsView === 'function') showDailyWordsView(); }, 300);
      break;
    case 'academy':
      switchView('english');
      break;
    case 'journal':
      switchView('diary');
      break;
    default:
      break;
  }
}

/**
 * Render section cards (English, GIA's Diary, Math).
 * @tag HOME_DASHBOARD @tag NAVIGATION
 */
function renderSectionCards() {
  // Cards are static HTML; just wire click handlers
  const engCard = document.getElementById('section-card-english');
  const diaryCard = document.getElementById('section-card-diary');
  const mathCard = document.getElementById('section-card-math');
  if (engCard) engCard.onclick = () => switchView('english');
  if (diaryCard) diaryCard.onclick = () => switchView('diary');
  if (mathCard) mathCard.onclick = () => switchView('math');

  // Reward Shop shortcut card
  const rewardCard = document.getElementById('home-reward-card');
  if (rewardCard) rewardCard.onclick = () => {
    if (typeof openRewardShop === 'function') openRewardShop();
  };

  // Arcade card → overlay (arcade.js). Enabled per dashboard redesign.
  const arcadeCard = document.getElementById('section-card-arcade');
  if (arcadeCard) {
    arcadeCard.disabled = false;
    arcadeCard.onclick = () => {
      if (typeof openArcade === 'function') openArcade();
    };
  }

  // Review card — placeholder until review hub is built.
  const reviewCard = document.getElementById('section-card-review');
  if (reviewCard) {
    reviewCard.onclick = () => { /* coming soon */ };
  }

  // Ocean World card → open growth theme detail modal (growth-theme.js)
  const oceanCard = document.getElementById('ocean-world-card');
  if (oceanCard) {
    oceanCard.onclick = () => {
      if (typeof gtOpenThemeDetail === 'function') gtOpenThemeDetail();
    };
  }
}

/**
 * Render growth theme widget — delegates to growth-theme.js (Phase 8).
 * @tag HOME_DASHBOARD @tag GROWTH_THEME
 */
function renderGrowthTheme() {
  if (typeof gtRenderTheme === 'function') {
    gtRenderTheme();
  }
  _loadOceanImage();
}

/**
 * Load the current Ocean World (growth theme) image into the dashboard card.
 * @tag HOME_DASHBOARD @tag GROWTH_THEME
 */
async function _loadOceanImage() {
  const card = document.getElementById('ocean-world-img');
  const FALLBACK = '/static/img/themes/ocean/step_0_v1.svg';
  // Show fallback immediately so the card never renders as a blank white box.
  if (card && !card.getAttribute('src')) card.src = FALLBACK;
  try {
    const data = await apiFetchJSON('/api/growth/theme');
    const url = data?.active?.img_url || FALLBACK;
    if (card) card.src = url;
  } catch {
    if (card) card.src = FALLBACK;
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
      if (xpEl) xpEl.textContent = (d.total_xp ?? 0).toLocaleString();
      const streakDays = d.streak_days ?? 0;
      if (streakEl) streakEl.textContent = `${streakDays} day${streakDays === 1 ? '' : 's'}`;
      if (wordsEl) wordsEl.textContent = (d.words_known ?? 0).toLocaleString();

      // Sub-labels for the Stats stack
      const xpToday = document.getElementById('summary-xp-today');
      if (xpToday && typeof d.xp_today === 'number') xpToday.textContent = `+${d.xp_today} today`;
      const streakBest = document.getElementById('summary-streak-best');
      if (streakBest && typeof d.streak_best === 'number') streakBest.textContent = `best: ${d.streak_best}`;
      const weeklyStreakEl = document.getElementById('weekly-streak-days');
      if (weeklyStreakEl) weeklyStreakEl.textContent = String(streakDays);

      // Level + Progress (XP per level = 100)
      const totalXP = d.total_xp ?? 0;
      const level = d.level ?? (Math.floor(totalXP / 100) + 1);
      const xpInLevel = totalXP - ((level - 1) * 100);
      const pct = Math.min(100, Math.round((xpInLevel / 100) * 100));
      const lblEl  = document.getElementById('growth-level-label');
      const pillEl = document.getElementById('growth-level-xp');
      const fillEl = document.getElementById('growth-progress-fill');
      const hintEl = document.getElementById('growth-level-hint');
      if (lblEl)  lblEl.textContent  = `Level ${level}`;
      if (pillEl) pillEl.textContent = `${xpInLevel}/100 XP`;
      if (fillEl) fillEl.style.width = `${pct}%`;
      if (hintEl) hintEl.textContent = `${100 - xpInLevel} XP to Level ${level + 1}`;

      // Done count — reuse latest task counts if available
      const counts = window._todayTaskCounts;
      const doneEl = document.getElementById('summary-done');
      if (doneEl && counts) doneEl.textContent = `${counts.done}/${counts.total}`;

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

    // #stars-count is a hidden legacy compat element. Mirror its hidden state
    // onto #top-xp-meta so the "Lv.1 · 0d" pill doesn't bleed through on home.
    const starsHidden = getComputedStyle(starsEl).display === 'none';
    let metaEl = document.getElementById('top-xp-meta');
    if (!metaEl) {
        metaEl = document.createElement('span');
        metaEl.id = 'top-xp-meta';
        metaEl.className = 'top-xp-meta';
        starsEl.parentNode.insertBefore(metaEl, starsEl.nextSibling);
    }
    metaEl.textContent = `Lv.${level} · ${streak}d`;
    metaEl.style.display = starsHidden ? 'none' : '';
    // Sync sidebar star-count
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
    try {
        const res = await fetch('/api/xp/summary');
        if (res.ok) {
            const d = await res.json();
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
