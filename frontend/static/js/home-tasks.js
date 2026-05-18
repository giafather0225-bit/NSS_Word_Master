/* ================================================================
   home-tasks.js — Today's Tasks, reminders, weekly strip, task navigation
   Section: Home
   Dependencies: core.js, home.js (switchView, toggleAccordion, _mathReviewDue, _englishReviewDue)
   API endpoints: GET /api/tasks/today, GET /api/reminders/today,
                  GET /api/xp/weekly
   ================================================================ */

/**
 * Render reminder banners.
 * @tag HOME_DASHBOARD @tag REMINDER
 */
async function renderReminders() {
  const container = document.getElementById('reminder-banners');
  if (!container) return;
  container.innerHTML = '';
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const res = await fetch('/api/reminders/today', { signal: ctrl.signal });
    clearTimeout(timer);
    if (!res.ok) return;
    const banners = await res.json();
    banners.forEach(b => {
      const div = document.createElement('div');
      div.className = 'reminder-banner' + (b.severity === 'danger' ? ' danger' : '');
      const closeBtn = document.createElement('button');
      closeBtn.className = 'reminder-close';
      closeBtn.setAttribute('aria-label', 'Dismiss');
      closeBtn.addEventListener('click', () => div.remove());
      closeBtn.textContent = '×';
      div.appendChild(document.createTextNode(b.message || ''));
      div.appendChild(closeBtn);
      container.appendChild(div);
    });
  } catch { /* no reminders */ }
}

/**
 * Map a task key to a section bucket used by the grouped UI.
 * @tag HOME_DASHBOARD @tag TODAY_TASKS
 */
function _sectionOfTask(key) {
  if (key === 'review') return 'review';
  if (key === 'journal') return 'diary';
  if (key === 'daily_words' || key === 'academy' || key === 'english') return 'english';
  if (key === 'math') return 'math';
  if (key === 'arcade') return 'arcade';
  if (key === 'ckla') return 'ckla';
  return 'english';
}

const _SECTION_LABELS = {
  english: 'English',
  ckla:    'CKLA',
  math:    'Math',
  diary:   'Diary',
  review:  'Review',
  arcade:  'Arcade',
};

const _SECTION_ORDER = ['english', 'ckla', 'math', 'diary', 'review', 'arcade'];

function _homeEscape(s) {
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

  const tasks = [
    { key: 'review', label: 'Review', detail: '', xp: 2, is_required: true, is_done: false },
    { key: 'daily_words', label: 'Daily Words', detail: '0/10', xp: 5, is_required: false, is_done: false },
    { key: 'journal', label: 'Daily Journal', detail: '', xp: 10, is_required: false, is_done: false },
  ];

  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const res = await fetch('/api/tasks/today', { signal: ctrl.signal });
    clearTimeout(timer);
    if (res.ok) {
      const data = await res.json();
      if (data && data.length) tasks.splice(0, tasks.length, ...data);
    }
  } catch { /* use stubs */ }

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
        const detail = t.detail ? ` (${_homeEscape(t.detail)})` : '';
        const dueNow = !t.is_done && (t.due === 'now' || t.is_required);
        const pill   = dueNow ? `<span class="tc-now-pill">NOW</span>` : '';
        return `
          <div class="tc-row${t.is_done ? ' done' : ''}${dueNow ? ' is-due-now' : ''}"
               data-key="${_homeEscape(t.key)}" data-section="${sec}">
            <span class="tc-check" aria-hidden="true"></span>
            <span class="tc-label">${_homeEscape(t.label)}${detail}</span>
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
  if (fillEl) {
    fillEl.style.width = pct + '%';
    fillEl.classList.toggle('tc-progress-fill--half', pct >= 50 && pct < 100);
    fillEl.classList.toggle('tc-progress-fill--done', pct === 100);
  }
  const progressBar = fillEl ? fillEl.parentElement : null;
  if (progressBar) progressBar.setAttribute('aria-valuenow', String(pct));

  window._todayTaskCounts = { total, done: doneCount };
  const doneStatEl = document.getElementById('summary-done');
  if (doneStatEl) doneStatEl.textContent = `${doneCount}/${total}`;

  const reviewTask = tasks.find(t => t.key === 'review');
  _mathReviewDue    = reviewTask ? (reviewTask.math_review_count    || 0) : 0;
  _englishReviewDue = reviewTask ? (reviewTask.english_review_count || 0) : 0;
  const badge = document.getElementById('section-card-review-badge');
  if (badge) {
    const totalDue = _mathReviewDue + _englishReviewDue;
    badge.textContent = totalDue;
    badge.style.display = totalDue > 0 ? '' : 'none';
  }

  list.querySelectorAll('.tc-row').forEach(el => {
    if (el.classList.contains('done')) return;
    el.addEventListener('click', () => _navigateTask(el.dataset.key));
  });
}

/**
 * Navigate to the appropriate screen when a task item is clicked.
 * @tag HOME_DASHBOARD @tag TODAY_TASKS @tag NAVIGATION
 * @param {string} key - task key from API (review|daily_words|academy|journal)
 */
function _navigateTask(key) {
  switch (key) {
    case 'review':
      if (typeof ReviewHub !== 'undefined') ReviewHub.open();
      break;
    case 'daily_words':
      switchView('english');
      setTimeout(() => { toggleAccordion('daily-words'); if (typeof showDailyWordsView === 'function') showDailyWordsView(); }, 300);
      break;
    case 'academy':
      switchView('english');
      break;
    case 'ckla':
      switchView('english');
      setTimeout(() => { if (typeof showCKLAView === 'function') showCKLAView(); }, 300);
      break;
    case 'journal':
      switchView('diary');
      break;
    default:
      break;
  }
}

/**
 * Render the weekly activity bar chart.
 * @tag HOME_DASHBOARD @tag STREAK
 */
async function renderWeeklyStrip() {
  const container = document.getElementById('weekly-bars');
  if (!container) return;

  let days = Array.from({ length: 7 }, () => ({ label: '·', value: 0 }));
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const res = await fetch('/api/xp/weekly', { signal: ctrl.signal });
    clearTimeout(timer);
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
