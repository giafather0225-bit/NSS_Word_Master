/* ================================================================
   arcade.js — Arcade overlay shell + game lobby
   Section: Arcade
   Dependencies: core.js, arcade-word-invaders.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/* Lucide SVG strings (stroke-width 1.5, currentColor) */
const _SVG = {
  crosshair: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" x2="18" y1="12" y2="12"/><line x1="6" x2="2" y1="12" y2="12"/><line x1="12" x2="12" y1="6" y2="2"/><line x1="12" x2="12" y1="22" y2="18"/></svg>`,
  helpCircle: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>`,
  keyboard: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2" ry="2"/><path d="M6 8h.001"/><path d="M10 8h.001"/><path d="M14 8h.001"/><path d="M18 8h.001"/><path d="M8 12h.001"/><path d="M12 12h.001"/><path d="M16 12h.001"/><path d="M7 16h10"/></svg>`,
  layoutGrid: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>`,
  zap: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  hash: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/></svg>`,
  target: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
  volume2: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>`,
  volumeX: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" x2="17" y1="9" y2="15"/><line x1="17" x2="23" y1="9" y2="15"/></svg>`,
  lightbulb: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>`,
  trophy: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/></svg>`,
  bookOpen: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  calculator: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2"/><line x1="8" x2="16" y1="6" y2="6"/><line x1="8" x2="8.01" y1="10" y2="10"/><line x1="12" x2="12.01" y1="10" y2="10"/><line x1="16" x2="16.01" y1="10" y2="10"/><line x1="8" x2="8.01" y1="14" y2="14"/><line x1="12" x2="12.01" y1="14" y2="14"/><line x1="16" x2="16.01" y1="14" y2="14"/><line x1="8" x2="8.01" y1="18" y2="18"/><line x1="12" x2="12.01" y1="18" y2="18"/><line x1="16" x2="16.01" y1="18" y2="18"/></svg>`,
};

/** @tag ARCADE */
const ARCADE_GAMES = [
  { id: 'word_invaders',    category: 'english', title: 'Word Invaders', icon: _SVG.crosshair,   sub: 'Type the falling word before it hits the ground', enabled: true },
  { id: 'definition_match', category: 'english', title: 'Match or Not',  icon: _SVG.helpCircle,  sub: 'Does the definition match? Tap Yes or No. 60 seconds.', enabled: true },
  { id: 'spell_rush',       category: 'english', title: 'Spell Rush',    icon: _SVG.keyboard,    sub: 'Spell each word letter-by-letter. Beat the clock.', enabled: true },
  { id: 'crossword',        category: 'english', title: 'Crossword',     icon: _SVG.layoutGrid,  sub: 'Fill the grid using definitions as clues.', enabled: true },
  { id: 'math_invaders',    category: 'math',    title: 'Math Invaders', icon: _SVG.zap,         sub: 'Type the answer before the equation lands.', enabled: true },
  { id: 'sudoku',           category: 'math',    title: 'Sudoku',        icon: _SVG.hash,        sub: '4x4, 6x6, or 9x9 — classic number puzzle.', enabled: true },
  { id: 'make24',           category: 'math',    title: 'Make 24',       icon: _SVG.target,      sub: 'Combine four numbers to reach 24. 90 seconds.', enabled: true },
];

/**
 * Open the arcade overlay and show the game lobby.
 * @tag ARCADE @tag NAVIGATION
 */
function openArcade() {
  const el = document.getElementById('arcade-overlay');
  if (!el) return;
  el.classList.remove('hidden');
  _updateMuteButton();
  _renderArcadeLobby();
}

/** Toggle arcade SFX on/off and update the button icon. @tag ARCADE */
function toggleArcadeMute() {
  if (typeof arcadeSfxSetMuted !== 'function') return;
  arcadeSfxSetMuted(!arcadeSfxIsMuted());
  _updateMuteButton();
}

function _updateMuteButton() {
  const btn = document.getElementById('arcade-mute');
  if (!btn || typeof arcadeSfxIsMuted !== 'function') return;
  btn.innerHTML = arcadeSfxIsMuted() ? _SVG.volumeX : _SVG.volume2;
}

/** Close arcade and stop any running game. @tag ARCADE */
function closeArcade() {
  if (typeof wiStop === 'function') wiStop();
  if (typeof dmStop === 'function') dmStop();
  if (typeof srStop === 'function') srStop();
  if (typeof cwStop === 'function') cwStop();
  if (typeof miStop === 'function') miStop();
  if (typeof suStop === 'function') suStop();
  if (typeof mkStop === 'function') mkStop();
  const el = document.getElementById('arcade-overlay');
  if (el) el.classList.add('hidden');
}

/** Render the arcade game list. @tag ARCADE */
async function _renderArcadeLobby() {
  const body = document.getElementById('arcade-body');
  if (!body) return;

  const bests = await Promise.all(
    ARCADE_GAMES.map((g) =>
      g.enabled
        ? fetch(`/api/arcade/best/${g.id}`).then((r) => r.ok ? r.json() : { score: 0 }).catch(() => ({ score: 0 }))
        : Promise.resolve({ score: 0 })
    )
  );

  const cardFor = (g, i) => {
    const catCls = g.category === 'math' ? 'cat-math' : 'cat-english';
    const cls = `arcade-game-card ${catCls}${g.enabled ? '' : ' disabled'}`;
    const click = g.enabled ? `onclick="_launchArcadeGame('${g.id}')"` : '';
    const pb = bests[i].score || 0;
    const pbLine = g.enabled
      ? `<div class="arcade-game-pb">Best: <b>${pb}</b></div>`
      : '';
    return `
      <div class="${cls}" ${click}>
        <div class="arcade-game-icon">${g.icon}</div>
        <div class="arcade-game-title">${g.title}</div>
        <div class="arcade-game-sub">${g.sub}</div>
        ${pbLine}
      </div>`;
  };

  const byCat = (cat) => ARCADE_GAMES
    .map((g, i) => g.category === cat ? cardFor(g, i) : null)
    .filter(Boolean)
    .join('');

  body.innerHTML = `
    <div class="arcade-xp-note">
      XP per round — 500+: <b>+1</b>, 1000+: <b>+2</b>, 2000+: <b>+3</b>. Daily max 10 XP.
    </div>
    <div class="arcade-section-label">${_SVG.bookOpen} English</div>
    <div class="arcade-list">${byCat('english')}</div>
    <div class="arcade-section-label">${_SVG.calculator} Math</div>
    <div class="arcade-list">${byCat('math')}</div>
  `;
}

/** @tag ARCADE */
function _launchArcadeGame(id) {
  if (id === 'word_invaders' && typeof wiShowLevelPicker === 'function') wiShowLevelPicker();
  else if (id === 'definition_match' && typeof dmStart === 'function') dmStart();
  else if (id === 'spell_rush' && typeof srStart === 'function') srStart();
  else if (id === 'crossword' && typeof cwStart === 'function') cwStart();
  else if (id === 'math_invaders' && typeof miShowLevelPicker === 'function') miShowLevelPicker();
  else if (id === 'sudoku' && typeof suShowLevelPicker === 'function') suShowLevelPicker();
  else if (id === 'make24' && typeof mkShowLevelPicker === 'function') mkShowLevelPicker();
}

/** Return to arcade lobby from a game. @tag ARCADE */
function arcadeReturnToLobby() {
  if (typeof wiStop === 'function') wiStop();
  if (typeof dmStop === 'function') dmStop();
  if (typeof srStop === 'function') srStop();
  if (typeof cwStop === 'function') cwStop();
  if (typeof miStop === 'function') miStop();
  if (typeof suStop === 'function') suStop();
  if (typeof mkStop === 'function') mkStop();
  _renderArcadeLobby();
}

/* ── Shared helpers for all arcade games ─────────────────────── */

const _ARCADE_TIPS = {
  word_invaders: 'Type the falling word before it hits the ground. Power-ups drop in gold pills — type their keyword to use them.',
  math_invaders: 'Type the answer to the falling equation, then press Enter.',
  definition_match: 'Tap Yes if the definition matches the word, No if it does not. 60 seconds.',
  spell_rush: 'Type each word letter-by-letter. Press Enter to submit.',
  crossword: 'Click a square to highlight the word. Type letters in the boxes. Green = correct!',
  sudoku: 'Every row, column, and box must have each number once. Green cells are right, red are wrong.',
  make24: 'Tap numbers and operators to build an expression that equals the target. Use all four numbers.',
};

/** Show a one-time tutorial banner above a game. Dismissed forever after tap. @tag ARCADE */
function _arcadeShowTutorialOnce(gameId) {
  try {
    const key = `arcade_tutorial_seen_${gameId}`;
    if (localStorage.getItem(key) === '1') return;
    const body = document.getElementById('arcade-body');
    const tip = _ARCADE_TIPS[gameId];
    if (!body || !tip) return;
    const el = document.createElement('div');
    el.className = 'arcade-tip';
    el.innerHTML = `<span class="arcade-tip-icon">${_SVG.lightbulb}</span><span class="arcade-tip-text">${tip}</span><button type="button" class="arcade-tip-x" aria-label="Dismiss">✕</button>`;
    body.insertBefore(el, body.firstChild);
    const dismiss = () => {
      try { localStorage.setItem(key, '1'); } catch (_) {}
      el.remove();
    };
    el.querySelector('.arcade-tip-x').addEventListener('click', dismiss);
    setTimeout(dismiss, 8000);
  } catch (_) { /* localStorage blocked — silently skip */ }
}

/** Fetch arcade word pool. @tag ARCADE */
async function _arcadeFetchWords(count = 40) {
  try {
    const r = await fetch(`/api/arcade/words?count=${count}`);
    if (!r.ok) return [];
    const data = await r.json();
    return data.words || [];
  } catch (e) {
    console.error('[arcade] word fetch failed', e);
    if (typeof toast === 'function') toast('Could not load words — check connection.', 'error');
    return [];
  }
}

/** Report a game result; returns tier/xp/best payload. @tag ARCADE @tag XP */
async function _arcadeReportScore(game, score, correct, total, accuracy, level = '') {
  const fallback = { tier: 0, xp_awarded: 0, daily_total: 0, daily_cap: 10, best_score: 0, new_best: false };
  try {
    const r = await fetch('/api/arcade/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ game, score, correct, total, accuracy, level }),
    });
    if (!r.ok) return fallback;
    return await r.json();
  } catch (e) {
    console.error('[arcade] score report failed', e);
    if (typeof toast === 'function') toast('Score not saved — network error.', 'error');
    return fallback;
  }
}

/** Render the shared game-over panel. @tag ARCADE */
function _arcadeRenderGameOver({ state, accuracy, result, replay }) {
  const body = document.getElementById('arcade-body');
  if (!body) return;
  const pct = Math.round(accuracy * 100);
  const tierLabels = { 0: '', 1: 'Bronze', 2: 'Silver', 3: 'Gold' };
  const tierLabel = tierLabels[result.tier] || '';
  const tierLine = result.tier > 0
    ? `<div class="stat">Tier: <b>${tierLabel}</b></div>`
    : `<div class="stat">Tier: — (500+ for Bronze)</div>`;

  let xpLine;
  if (result.xp_awarded > 0) {
    xpLine = `<div class="xp-line">+${result.xp_awarded} XP (${result.daily_total}/${result.daily_cap} today)</div>`;
  } else if (result.tier > 0) {
    xpLine = `<div class="xp-line">Daily cap reached (${result.daily_cap} XP max)</div>`;
  } else {
    xpLine = `<div class="xp-line">No XP — score 500+ to earn Bronze tier</div>`;
  }

  const bestBanner = result.new_best
    ? `<div class="wi-new-best">${_SVG.trophy} New Personal Best!</div>`
    : `<div class="stat">Best: <b>${result.best_score}</b></div>`;

  body.innerHTML = `
    <div class="wi-gameover">
      <h2>Game Over</h2>
      ${bestBanner}
      <div class="stat">Score: <b>${state.score}</b></div>
      <div class="stat">Correct: <b>${state.correct}</b> / ${state.total}</div>
      <div class="stat">Accuracy: <b>${pct}%</b></div>
      ${tierLine}
      ${xpLine}
      <div style="display:flex; gap:12px; margin-top:8px;">
        <button class="wi-btn" onclick="${replay}">Play again</button>
        <button class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
      </div>
    </div>`;

  if (typeof refreshXPSummary === 'function') refreshXPSummary();

  if (result.new_best && typeof sfxNewBest === 'function') {
    sfxNewBest();
  } else if (typeof sfxGameOver === 'function') {
    sfxGameOver();
  }
}
