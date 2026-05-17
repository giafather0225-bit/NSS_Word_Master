/* ================================================================
   home-stats.js — Summary bar, AI Coach, Island subject widget
   Section: Home
   Dependencies: core.js, home.js (switchView)
   API endpoints: GET /api/ai-coach/today, GET /api/xp/summary,
                  GET /api/island/character/active
   ================================================================ */

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
    el.textContent = "Ready to learn today? Let's go!";
  }

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

  const glowRing = document.querySelector('.coach-glow-ring');
  if (glowRing) {
    setTimeout(() => glowRing.classList.add('active'), 500);
  }
}

/**
 * Render summary bar (Words I Know, XP, Streak).
 * @tag HOME_DASHBOARD @tag XP @tag STREAK
 */
async function renderSummaryBar() {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const res = await fetch('/api/xp/summary', { signal: ctrl.signal });
    clearTimeout(timer);
    if (res.ok) {
      const d = await res.json();
      const xpEl = document.getElementById('summary-xp');
      const streakEl = document.getElementById('summary-streak');
      const wordsEl = document.getElementById('summary-words');
      if (xpEl) xpEl.textContent = (d.total_xp ?? 0).toLocaleString();
      const streakDays = d.streak_days ?? 0;
      if (streakEl) streakEl.textContent = `${streakDays} day${streakDays === 1 ? '' : 's'}`;
      if (wordsEl) wordsEl.textContent = (d.words_known ?? 0).toLocaleString();

      const xpToday = document.getElementById('summary-xp-today');
      if (xpToday && typeof d.xp_today === 'number') xpToday.textContent = `+${d.xp_today} today`;
      const streakBest = document.getElementById('summary-streak-best');
      if (streakBest && typeof d.streak_best === 'number') streakBest.textContent = `best: ${d.streak_best}`;
      const weeklyStreakEl = document.getElementById('weekly-streak-days');
      if (weeklyStreakEl) weeklyStreakEl.textContent = String(streakDays);

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

      const counts = window._todayTaskCounts;
      const doneEl = document.getElementById('summary-done');
      if (doneEl && counts) doneEl.textContent = `${counts.done}/${counts.total}`;

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
  const sidebarStar = document.getElementById('star-count');
  if (sidebarStar) sidebarStar.textContent = String(totalXP);
}

/**
 * Refresh the summary bar XP/streak numbers when called from other modules.
 * @tag HOME_DASHBOARD @tag XP @tag STREAK
 */
async function refreshHomeStats() {
  await renderSummaryBar();
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const res = await fetch('/api/xp/summary', { signal: ctrl.signal });
    clearTimeout(timer);
    if (res.ok) {
      const d = await res.json();
      _updateTopBarXP(d);
    }
  } catch (_) {}
}

/**
 * Load and render the compact floating island character bubble into a subject-view container.
 * Compact state: avatar + Lv badge only. Click toggles expanded panel with name/gauges.
 * @tag ISLAND
 * @param {string} containerId - DOM element id to populate
 * @param {string} zone - island zone name (forest / ocean / savanna / space)
 */
async function _renderIslandSubjectWidget(containerId, zone) {
  const el = document.getElementById(containerId);
  if (!el) return;
  try {
    const res = await fetch(`/api/island/character/active?zone=${encodeURIComponent(zone)}`);
    if (!res.ok) { el.style.display = 'none'; return; }
    const data = await res.json();
    const chars = data.characters || [];
    const char = chars.find(c => !c.is_completed) || chars[0];
    if (!char) { el.style.display = 'none'; return; }

    let imgSrc = '';
    try {
      const imgs = JSON.parse(char.images || '{}');
      const imgPath = imgs[char.stage] || imgs['baby'] || '';
      if (imgPath) imgSrc = `/static/img/island/${imgPath}`;
    } catch (_) {}

    const hunger = Math.max(0, Math.min(100, char.hunger || 0));
    const happy  = Math.max(0, Math.min(100, char.happiness || 0));
    const name   = char.nickname || char.name || 'Character';
    const level  = char.level || 1;
    const evo    = !!char.ready_to_evolve;

    el.innerHTML = `
      <div class="isw-bubble" data-open="false" role="button" tabindex="0"
           aria-label="My Island — ${escapeHtml(name)}, Level ${level}">
        <div class="isw-avatar">
          ${imgSrc
            ? `<img src="${imgSrc}" class="isw-avatar-img" alt="${escapeHtml(name)}" />`
            : `<i data-lucide="star" class="isw-avatar-placeholder"></i>`}
          <span class="isw-lv">Lv.${level}</span>
          ${evo ? '<span class="isw-evo-dot"></span>' : ''}
        </div>
        <div class="isw-panel" aria-hidden="true">
          <div class="isw-panel-name">${escapeHtml(name)}</div>
          ${evo ? '<div class="isw-panel-evo">Ready to Evolve!</div>' : ''}
          <div class="isw-gauges">
            <div class="isw-gauge-row">
              <i data-lucide="utensils" width="10" height="10"></i>
              <div class="isw-gauge">
                <div class="isw-gauge-fill isw-gauge-fill--hunger" style="width:${hunger}%"></div>
              </div>
            </div>
            <div class="isw-gauge-row">
              <i data-lucide="heart" width="10" height="10"></i>
              <div class="isw-gauge">
                <div class="isw-gauge-fill isw-gauge-fill--happy" style="width:${happy}%"></div>
              </div>
            </div>
          </div>
          <div class="isw-panel-footer">Tap to open Island</div>
        </div>
      </div>`;

    if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [el] });

    const bubble = el.querySelector('.isw-bubble');
    const panel  = el.querySelector('.isw-panel');

    bubble.addEventListener('click', (e) => {
      const isOpen = bubble.dataset.open === 'true';
      if (isOpen) {
        // Second tap → open island
        if (typeof openIslandMain === 'function') openIslandMain();
        bubble.dataset.open = 'false';
        panel.setAttribute('aria-hidden', 'true');
      } else {
        bubble.dataset.open = 'true';
        panel.setAttribute('aria-hidden', 'false');
        e.stopPropagation();
      }
    });

    bubble.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        bubble.click();
      }
      if (e.key === 'Escape') {
        bubble.dataset.open = 'false';
        panel.setAttribute('aria-hidden', 'true');
      }
    });

    // Close panel when clicking anywhere outside
    document.addEventListener('click', function _iswOutside(e) {
      if (!el.contains(e.target)) {
        bubble.dataset.open = 'false';
        panel.setAttribute('aria-hidden', 'true');
      }
    });
  } catch (_) {
    el.style.display = 'none';
  }
}
