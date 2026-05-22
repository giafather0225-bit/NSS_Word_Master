/* ================================================================
   home.js — Home Dashboard: view switching, section cards, settings
   Section: Home
   Dependencies: core.js, home-tasks.js, home-stats.js
   API endpoints: none (delegates to home-tasks.js / home-stats.js)
   ================================================================ */

// Current view state
let currentView = 'home'; // 'home' | 'english' | 'math' | 'diary'

// Compatibility shim — bare openIsland() calls (source in minified third-party
// or service-worker cached chunk) redirect to the real entry point.
if (typeof window.openIsland === 'undefined') {
    window.openIsland = function () {
        if (typeof openIslandMain === 'function') openIslandMain();
    };
}

// Cached review counts — set by renderTodayTasks, used by renderSectionCards
let _mathReviewDue = 0;
let _englishReviewDue = 0;

/**
 * Switch the app to the given view.
 *
 * Container visibility is owned by CSS (main-idle.css body:not([data-view])
 * rules). This function only sets data-view, the sidebar mode, and runs
 * each view's entry action. It clears any stale inline `display` on the
 * incoming view's primary container so the CSS default applies.
 *
 * @tag HOME_DASHBOARD @tag NAVIGATION
 * @param {'home'|'english'|'math'|'diary'} view
 */
function switchView(view) {
  // P1-11: race-condition guard — bail out if we're already on this view to
  // prevent duplicate API calls and state resets on rapid navigation clicks.
  if (view === currentView) return;
  currentView = view;
  document.body.dataset.view = view;

  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.dataset.mode = view;

  // Force-close any active lesson stage on every view change, so stale
  // math/english/daily-words content never bleeds across views even when
  // the user navigates without using the explicit Exit/Back button.
  if (typeof unmountMathShell === 'function') unmountMathShell();
  if (typeof hideLessonStage === 'function') hideLessonStage();
  const stageInner = document.getElementById('stage');
  if (stageInner) stageInner.innerHTML = '';
  const dwView = document.getElementById('daily-words-view');
  if (dwView && dwView.classList.contains('active')) {
    dwView.classList.remove('active');
    dwView.style.display = 'none';
  }

  // Clear inline display on this view's primary container — CSS hides all
  // other primaries via body:not([data-view="..."]) rules.
  const primaryId = {
    home:    'home-dashboard',
    english: 'idle-wrapper',
    math:    'math-idle-wrapper',
    diary:   'diary-view',
  }[view];
  if (primaryId) {
    const el = document.getElementById(primaryId);
    if (el) el.style.display = '';
  }

  if (view === 'home') {
    renderHomeDashboard();
  } else if (view === 'math') {
    const _mathSb = document.getElementById('sidebar');
    if (_mathSb) _mathSb.classList.remove('collapsed');
    localStorage.removeItem('sb_collapsed');
    if (typeof loadMathGrades === 'function') loadMathGrades();
    if (typeof loadMathSidebarStatus === 'function') loadMathSidebarStatus();
    if (typeof lucide !== 'undefined') lucide.createIcons();
    _renderIslandSubjectWidget('island-widget-math', 'ocean');
  } else if (view === 'english') {
    const _engSb = document.getElementById('sidebar');
    if (_engSb) _engSb.classList.remove('collapsed');
    localStorage.removeItem('sb_collapsed');
    if (typeof window._clearEnglishSessionState === 'function') window._clearEnglishSessionState();
    if (typeof initCKLA === 'function') initCKLA();
    if (typeof lucide !== 'undefined') lucide.createIcons();
    _renderIslandSubjectWidget('island-widget-english', 'forest');
  } else if (view === 'diary') {
    if (typeof openDiarySection === 'function') openDiarySection('today');
  }
}

// updateSidebarMode() removed in Phase 4 — sidebar section visibility is
// now CSS-driven via body[data-view] rules in main-idle.css.

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
  if (typeof window.refreshStreakFreeze === "function") window.refreshStreakFreeze();
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

/** @tag SETTINGS @tag THEME — Settings modal with dark mode toggle. */
function openSettingsModal() {
  document.getElementById("gia-settings-modal")?.remove();

  const isDark = (localStorage.getItem("gia-theme") || "light") === "dark";

  const modal = document.createElement("div");
  modal.id = "gia-settings-modal";
  modal.className = "gs-modal";
  modal.innerHTML = `
    <div class="gs-card" role="dialog" aria-modal="true" aria-labelledby="gs-title">
      <div class="gs-header">
        <span class="gs-title" id="gs-title">
          <i data-lucide="settings" width="18" height="18"></i>
          Settings
        </span>
        <button type="button" class="gs-close" aria-label="Close settings"
                onclick="document.getElementById('gia-settings-modal').remove()">
          <i data-lucide="x" width="18" height="18"></i>
        </button>
      </div>
      <div class="gs-row">
        <div>
          <div class="gs-row-label">
            <i data-lucide="moon" width="16" height="16"></i>
            Dark Mode
          </div>
          <div class="gs-row-hint">Switch to dark theme</div>
        </div>
        <label class="gs-switch">
          <input type="checkbox" id="gia-dark-toggle" ${isDark ? "checked" : ""}
                 onchange="_giaToggleDark(this.checked)" aria-label="Toggle dark mode">
          <span class="gs-switch-track"></span>
          <span class="gs-switch-thumb"></span>
        </label>
      </div>
    </div>`;
  modal.addEventListener("click", e => { if (e.target === modal) modal.remove(); });
  document.body.appendChild(modal);
  if (typeof lucide !== "undefined" && lucide.createIcons) lucide.createIcons();
}

/** @tag THEME — Apply dark/light theme + persist. CSS handles toggle visuals. */
function _giaToggleDark(isDark) {
  document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
  localStorage.setItem("gia-theme", isDark ? "dark" : "light");
}

function openSettings() {
  openSettingsModal();
}

/**
 * Render section cards (English, GIA's Diary, Math).
 * @tag HOME_DASHBOARD @tag NAVIGATION
 */
function renderSectionCards() {
  const engCard   = document.getElementById('section-card-english');
  const diaryCard = document.getElementById('section-card-diary');
  const mathCard  = document.getElementById('section-card-math');
  if (engCard)   engCard.onclick   = () => switchView('english');
  if (diaryCard) diaryCard.onclick = () => switchView('diary');
  if (mathCard)  mathCard.onclick  = () => switchView('math');

  const rewardCard = document.getElementById('home-reward-card');
  if (rewardCard) rewardCard.onclick = () => {
    if (typeof openRewardShop === 'function') openRewardShop();
  };

  const arcadeCard = document.getElementById('section-card-arcade');
  if (arcadeCard) {
    arcadeCard.disabled = false;
    arcadeCard.onclick = () => {
      if (typeof openArcade === 'function') openArcade();
    };
  }

  const reviewCard = document.getElementById('section-card-review');
  if (reviewCard) {
    reviewCard.disabled = false;
    reviewCard.onclick = () => {
      if (typeof ReviewHub !== 'undefined') ReviewHub.open();
    };
  }

  const islandCard = document.getElementById('island-home-card');
  if (islandCard) {
    islandCard.onclick = () => {
      if (typeof openIslandMain === 'function') openIslandMain();
    };
  }
}

/**
 * Render island widget — loads live data into the island home card.
 * @tag HOME_DASHBOARD @tag SHOP
 */
function renderGrowthTheme() {
  if (typeof _loadIslandCard === 'function') _loadIslandCard();
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

// ─── Test Mode (God Mode) global utility ────────────────────────────────────
let _testModeActive = (localStorage.getItem('gia_test_mode') === 'true');

/**
 * Returns true when Test Mode is active.
 * @tag SETTINGS PARENT
 */
function isTestMode() { return _testModeActive; }

/**
 * Fetch the authoritative value from the server and apply it.
 * @tag SETTINGS PARENT
 */
async function _loadTestMode() {
  try {
    const d = await fetch('/api/parent/test-mode').then(r => r.json());
    _testModeActive = !!d.test_mode;
    localStorage.setItem('gia_test_mode', _testModeActive ? 'true' : 'false');
  } catch (_) {
    _testModeActive = localStorage.getItem('gia_test_mode') === 'true';
  }
  _applyTestModeBadge();
}

/** Show or hide the TEST badge in the topbar. @tag SETTINGS */
function _applyTestModeBadge() {
  const badge = document.getElementById('test-mode-badge');
  if (badge) badge.style.display = _testModeActive ? 'inline-flex' : 'none';
}

// ─── Home sections visibility ───────────────────────────────────────────────
/** Section key → DOM element ID map. @tag HOME_DASHBOARD SETTINGS */
const _HOME_SECTION_ID = {
  english: 'section-card-english',
  math:    'section-card-math',
  diary:   'section-card-diary',
  arcade:  'section-card-arcade',
  shop:    'home-reward-card',
  review:  'section-card-review',
};

/**
 * Fetch parent-configured section visibility and hide any disabled cards.
 * Falls back to showing all cards if the API is unreachable.
 * @tag HOME_DASHBOARD SETTINGS
 */
async function _applyHomeSections() {
  try {
    const data = await fetch('/api/parent/home-sections').then(r => r.json());
    const sections = data.sections || {};
    Object.entries(_HOME_SECTION_ID).forEach(([key, elId]) => {
      const el = document.getElementById(elId);
      if (!el) return;
      const visible = sections[key] !== false;
      el.style.display = visible ? '' : 'none';
    });
  } catch (_) {
    // API unreachable — leave all sections visible (safe default)
  }
}

// Initialize home view on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  switchView('home');
  if (typeof loadDailyWordsSection === 'function') loadDailyWordsSection();
  _loadTestMode();
  _applyHomeSections();
});
