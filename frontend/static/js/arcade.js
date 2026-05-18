/* ================================================================
   arcade.js — Arcade overlay shell + game lobby
   Section: Arcade
   Dependencies: core.js, arcade-sfx.js, arcade-word-invaders.js,
                 arcade-definition-match.js, arcade-spell-rush.js,
                 arcade-crossword.js, arcade-math-invaders.js,
                 arcade-sudoku.js, arcade-make24.js,
                 arcade-word-builder.js, arcade-memory-match.js
   API endpoints: GET /api/arcade/words, GET /api/arcade/best/{game},
                  POST /api/arcade/score
   ================================================================ */

/* Lucide SVG strings (stroke-width 1.5, currentColor) */
const _SVG = {
  crosshair: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" x2="18" y1="12" y2="12"/><line x1="6" x2="2" y1="12" y2="12"/><line x1="12" x2="12" y1="6" y2="2"/><line x1="12" x2="12" y1="22" y2="18"/></svg>`,
  helpCircle: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>`,
  keyboard: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2" ry="2"/><path d="M6 8h.001"/><path d="M10 8h.001"/><path d="M14 8h.001"/><path d="M18 8h.001"/><path d="M8 12h.001"/><path d="M12 12h.001"/><path d="M16 12h.001"/><path d="M7 16h10"/></svg>`,
  layoutGrid: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>`,
  layers: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
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
  { id: 'word_invaders',    category: 'english', title: 'Word Invaders', icon: _SVG.crosshair,   sub: 'Type the falling word before it hits the ground', enabled: true,  defaultLevel: 'normal' },
  { id: 'definition_match', category: 'english', title: 'Match or Not',  icon: _SVG.helpCircle,  sub: 'Does the definition match? Tap Yes or No.', enabled: true, defaultLevel: 'normal' },
  { id: 'spell_rush',       category: 'english', title: 'Spell Rush',    icon: _SVG.keyboard,    sub: 'Spell each word letter-by-letter. Beat the clock.', enabled: true, defaultLevel: 'normal' },
  { id: 'crossword',        category: 'english', title: 'Crossword',     icon: _SVG.layoutGrid,  sub: 'Fill the grid using definitions as clues.', enabled: true, defaultLevel: 'normal' },
  { id: 'word_builder',     category: 'english', title: 'Word Builder',  icon: _SVG.keyboard,    sub: 'Rearrange the scrambled tiles to spell the word.', enabled: true, defaultLevel: 'normal' },
  { id: 'memory_match',     category: 'english', title: 'Memory Match',  icon: _SVG.layers,      sub: 'Flip cards to pair each word with its definition.', enabled: true,  defaultLevel: 'easy' },
  { id: 'math_invaders',    category: 'math',    title: 'Math Invaders', icon: _SVG.zap,         sub: 'Type the answer before the equation lands.', enabled: true },
  { id: 'sudoku',           category: 'math',    title: 'Sudoku',        icon: _SVG.hash,        sub: '4x4, 6x6, or 9x9 — classic number puzzle.', enabled: true,  defaultLevel: 'easy' },
  { id: 'make24',           category: 'math',    title: 'Make 24',       icon: _SVG.target,      sub: 'Combine four numbers to reach 24. 90 seconds.', enabled: true,  defaultLevel: 'normal' },
];

let _arcadeInGame = false;

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
  if (_arcadeInGame) { arcadeReturnToLobby(); return; }
  if (typeof wiStop === 'function') wiStop();
  if (typeof dmStop === 'function') dmStop();
  if (typeof srStop === 'function') srStop();
  if (typeof cwStop === 'function') cwStop();
  if (typeof miStop === 'function') miStop();
  if (typeof suStop === 'function') suStop();
  if (typeof mkStop === 'function') mkStop();
  if (typeof wbStop === 'function') wbStop();
  if (typeof mmStop === 'function') mmStop();
  const el = document.getElementById('arcade-overlay');
  if (el) el.classList.add('hidden');
}

/** Render the arcade game list. @tag ARCADE */
async function _renderArcadeLobby() {
  const body = document.getElementById('arcade-body');
  if (!body) return;
  delete body.dataset.game;
  body.classList.add('arcade-body--lobby');

  const bests = await Promise.all(
    ARCADE_GAMES.map((g) => {
      if (!g.enabled) return Promise.resolve({ score: 0, daily_cap: 10 });
      const lvParam = g.defaultLevel ? `?level=${g.defaultLevel}` : '';
      return fetch(`/api/arcade/best/${g.id}${lvParam}`)
        .then((r) => r.ok ? r.json() : { score: 0, daily_cap: 10 })
        .catch(() => ({ score: 0, daily_cap: 10 }));
    })
  );

  // daily_cap is included in every best response — read from first enabled game result.
  const dailyCap = (bests.find((b) => b.daily_cap != null) || {}).daily_cap ?? 10;

  // Today's best: find the highest-scoring game played today
  const todayStr = new Date().toISOString().slice(0, 10);
  let todayBest = null;
  ARCADE_GAMES.forEach((g, i) => {
    if (!g.enabled) return;
    const b = bests[i];
    if (b && b.date === todayStr && b.score > 0) {
      if (!todayBest || b.score > todayBest.score) {
        todayBest = { title: g.title, score: b.score };
      }
    }
  });
  const todayBanner = todayBest
    ? `<div class="arcade-today-best">${_SVG.trophy} Today's Best — <b>${todayBest.title}</b>: <b>${todayBest.score.toLocaleString()}</b> pts</div>`
    : '';

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

  // Popular section: top 3 most-played games (localStorage play counts)
  let playCounts;
  try {
    playCounts = ARCADE_GAMES.map((g) =>
      parseInt(localStorage.getItem(`arcade_plays_${g.id}`) || '0', 10)
    );
  } catch (_) {
    playCounts = ARCADE_GAMES.map(() => 0);
  }
  const popularGames = ARCADE_GAMES
    .map((g, i) => ({ g, i, plays: playCounts[i] }))
    .filter(({ g, plays }) => g.enabled && plays > 0)
    .sort((a, b) => b.plays - a.plays)
    .slice(0, 3);
  const popularSection = popularGames.length >= 2
    ? `<div class="arcade-section-label arcade-section-label--popular">
         <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
         Popular
       </div>
       <div class="arcade-list">${popularGames.map(({ g, i }) => cardFor(g, i)).join('')}</div>`
    : '';

  body.innerHTML = `
    ${todayBanner}
    <div class="arcade-xp-note">
      XP per round — 500+: <b>+1</b>, 1000+: <b>+2</b>, 2000+: <b>+3</b>. Daily max <b>${dailyCap}</b> XP.
    </div>
    ${popularSection}
    <div class="arcade-section-label arcade-section-label--english">${_SVG.bookOpen} English</div>
    <div class="arcade-list">${byCat('english')}</div>
    <div class="arcade-section-label arcade-section-label--math">${_SVG.calculator} Math</div>
    <div class="arcade-list">${byCat('math')}</div>
  `;
}

/** @tag ARCADE */
function _launchArcadeGame(id) {
  _arcadeInGame = true;
  const body = document.getElementById('arcade-body');
  if (body) {
    body.classList.remove('arcade-body--lobby');
    body.dataset.game = id;
  }
  try {
    const key = `arcade_plays_${id}`;
    localStorage.setItem(key, String((parseInt(localStorage.getItem(key) || '0', 10) + 1)));
  } catch (_) {}
  if (id === 'word_invaders' && typeof wiShowLevelPicker === 'function') wiShowLevelPicker();
  else if (id === 'definition_match' && typeof dmShowLevelPicker === 'function') dmShowLevelPicker();
  else if (id === 'spell_rush' && typeof srShowLevelPicker === 'function') srShowLevelPicker();
  else if (id === 'crossword' && typeof cwShowLevelPicker === 'function') cwShowLevelPicker();
  else if (id === 'math_invaders' && typeof miShowLevelPicker === 'function') miShowLevelPicker();
  else if (id === 'sudoku' && typeof suShowLevelPicker === 'function') suShowLevelPicker();
  else if (id === 'make24' && typeof mkShowLevelPicker === 'function') mkShowLevelPicker();
  else if (id === 'word_builder' && typeof wbShowLevelPicker === 'function') wbShowLevelPicker();
  else if (id === 'memory_match' && typeof mmShowLevelPicker === 'function') mmShowLevelPicker();
}

/** Return to arcade lobby from a game. @tag ARCADE */
function arcadeReturnToLobby() {
  _arcadeInGame = false;
  const body = document.getElementById('arcade-body');
  if (body) delete body.dataset.game;
  if (typeof wiStop === 'function') wiStop();
  if (typeof dmStop === 'function') dmStop();
  if (typeof srStop === 'function') srStop();
  if (typeof cwStop === 'function') cwStop();
  if (typeof miStop === 'function') miStop();
  if (typeof suStop === 'function') suStop();
  if (typeof mkStop === 'function') mkStop();
  if (typeof wbStop === 'function') wbStop();
  if (typeof mmStop === 'function') mmStop();
  _renderArcadeLobby();
}

/* ── Shared helpers for all arcade games ─────────────────────── */

const _ARCADE_TIPS = {
  word_invaders: 'Type the falling word before it lands. Hit multiple words in a row to build a COMBO multiplier — higher combos = more points! Power-ups drop in gold pills; type their keyword to use them.',
  math_invaders: 'Type the answer to the falling equation, then press Enter.',
  definition_match: 'Tap Yes if the definition matches the word, No if it does not. Build streaks for bonus points!',
  spell_rush: 'Type each word letter-by-letter. Press Enter to submit. Correct answers build streaks for bonus points!',
  crossword: 'Click a cell to select the word. Type letters to fill it in. Use Arrow keys to move between cells. Green = correct! Fill all words for a bonus.',
  sudoku: 'Every row, column, and box must contain each number exactly once. Click a cell, then type a number. Use Arrow keys to move. Green = correct, red = conflict.',
  make24: 'Use all four numbers with +, −, ×, ÷ to reach the target (e.g. (3+1)×(2+4)=24). Click numbers and operators to build your expression. A hint appears if you are stuck.',
  word_builder: 'Click the scrambled letter tiles in the right order to spell the word shown by its definition.',
  memory_match: 'Flip cards to find matching word and definition pairs. Fewer flips = higher score.',
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
    el.innerHTML = `<span class="arcade-tip-icon">${_SVG.lightbulb}</span><span class="arcade-tip-text">${tip}</span><button type="button" class="arcade-tip-x" aria-label="Dismiss"><i data-lucide="x"></i></button>`;
    body.insertBefore(el, body.firstChild);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    const dismiss = () => {
      try { localStorage.setItem(key, '1'); } catch (_) {}
      el.remove();
    };
    el.querySelector('.arcade-tip-x').addEventListener('click', dismiss);
    setTimeout(dismiss, 12000);
  } catch (_) { /* localStorage blocked — silently skip */ }
}

/** Fetch arcade word pool. @tag ARCADE */
async function _arcadeFetchWords(count = 40) {
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), 8000);
  try {
    const r = await fetch(`/api/arcade/words?count=${count}`, { signal: controller.signal });
    clearTimeout(tid);
    if (!r.ok) return [];
    const data = await r.json();
    return data.words || [];
  } catch (e) {
    clearTimeout(tid);
    console.error('[arcade] word fetch failed', e);
    const msg = e.name === 'AbortError'
      ? 'Connection is slow — please try again.'
      : 'Could not load words — check connection.';
    if (typeof toast === 'function') toast(msg, 'error');
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

/** Compute S/A/B/C grade and message from accuracy. @tag ARCADE */
function _arcadeGrade(accuracy) {
  const pct = accuracy * 100;
  if (pct >= 90) return { grade: 'S', cls: 'grade--s', msg: 'Outstanding! You\'re unstoppable!' };
  if (pct >= 75) return { grade: 'A', cls: 'grade--a', msg: 'Great work! Keep it up!' };
  if (pct >= 60) return { grade: 'B', cls: 'grade--b', msg: 'Good effort! Practice makes perfect.' };
  return          { grade: 'C', cls: 'grade--c', msg: 'Keep going! You\'re getting better!' };
}

/** Compute 0–3 star count from accuracy. @tag ARCADE */
function _arcadeStars(accuracy) {
  const pct = accuracy * 100;
  if (pct >= 90) return 3;
  if (pct >= 70) return 2;
  if (pct >= 50) return 1;
  return 0;
}

/** Build star-rating HTML (3 stars). @tag ARCADE */
function _arcadeStarsHTML(accuracy) {
  const count = _arcadeStars(accuracy);
  return `<div class="arcade-stars" data-stars="${count}" aria-label="${count} out of 3 stars">` +
    [0, 1, 2].map(i => `<span class="arcade-star ${i < count ? 'arcade-star--filled' : 'arcade-star--empty'}">★</span>`).join('') +
  `</div>`;
}

/** Render the shared game-over panel. @tag ARCADE */
function _arcadeRenderGameOver({ state, accuracy, result, replayFn, extras = '' }) {
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
    ? (() => {
        const delta = result.prev_best > 0 ? state.score - result.prev_best : 0;
        const deltaStr = delta > 0 ? ` (+${delta})` : '';
        return `<div class="wi-new-best">${_SVG.trophy} New Personal Best!${deltaStr}</div>`;
      })()
    : `<div class="stat">Best: <b>${result.best_score}</b></div>`;

  const nudgeLine = !result.new_best && result.best_score > 0
    ? (() => {
        const gap = result.best_score - state.score;
        if (gap > 0 && gap < result.best_score * 0.20)
          return `<div class="stat wi-nudge">Only <b>${gap} pts</b> from your best — play again!</div>`;
        return '';
      })()
    : '';

  const { grade, cls, msg } = _arcadeGrade(accuracy);

  const flipLine = state.flips != null
    ? (() => {
        const minFlips = state.correct * 2;
        const extra = Math.max(0, state.flips - minFlips);
        const effPct = state.flips > 0 ? Math.round((minFlips / state.flips) * 100) : 100;
        const effLabel = effPct >= 90 ? 'Perfect' : effPct >= 70 ? 'Great' : 'Keep practicing';
        return `<div class="stat">Flip efficiency: <b>${effPct}%</b> <span class="stat-sub">${effLabel} (${extra} extra)</span></div>`;
      })()
    : '';

  const starsHTML = _arcadeStarsHTML(accuracy);

  body.innerHTML = `
    <div class="wi-gameover wi-gameover--${cls.replace('grade--', '')}">
      ${starsHTML}
      <div class="arcade-grade ${cls}">${grade}</div>
      <div class="arcade-grade-msg">${msg}</div>
      ${bestBanner}
      ${nudgeLine}
      <div class="stat">Score: <b>${state.score}</b></div>
      <div class="stat">Correct: <b>${state.correct}</b> / ${state.total}</div>
      <div class="stat">Accuracy: <b>${pct}%</b></div>
      ${flipLine}
      ${tierLine}
      ${xpLine}
      ${extras}
      <div class="wi-gameover-actions">
        <button class="wi-btn" id="arcade-replay-btn">Play again</button>
        <button class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
      </div>
    </div>`;

  const replayBtn = document.getElementById('arcade-replay-btn');
  if (replayBtn && typeof replayFn === 'function') {
    replayBtn.addEventListener('click', replayFn);
  }

  if (typeof refreshXPSummary === 'function') refreshXPSummary();

  if (result.new_best && typeof sfxNewBest === 'function') {
    sfxNewBest();
    _arcadeConfetti();
  } else if (_arcadeStars(accuracy) === 3) {
    // 3-star clear that isn't a new best still deserves confetti
    _arcadeConfetti();
    if (typeof sfxGameOver === 'function') sfxGameOver();
  } else if (typeof sfxGameOver === 'function') {
    sfxGameOver();
  }
}

/** Burst confetti particles over the game-over screen when a new personal best is set. @tag ARCADE */
function _arcadeConfetti() {
  const body = document.getElementById('arcade-body');
  if (!body) return;
  const colors = ['var(--arcade-primary)', 'var(--rewards-primary)', 'var(--english-primary)', 'var(--math-primary)', 'var(--diary-primary)'];
  for (let i = 0; i < 36; i++) {
    const el = document.createElement('div');
    el.className = 'arcade-confetti-piece';
    el.style.setProperty('--x', `${Math.random() * 100}%`);
    el.style.setProperty('--delay', `${(Math.random() * 0.5).toFixed(2)}s`);
    el.style.setProperty('--color', colors[i % colors.length]);
    el.style.setProperty('--rot', `${Math.floor(Math.random() * 720)}deg`);
    body.appendChild(el);
    setTimeout(() => el.remove(), 1600);
  }
}

/** Float a "+N pts" text upward in the active game view. @tag ARCADE */
function _arcadeFloatScore(pts) {
  const body = document.getElementById('arcade-body');
  if (!body) return;
  const el = document.createElement('div');
  el.className = 'arcade-float-score';
  el.textContent = `+${pts}`;
  body.appendChild(el);
  setTimeout(() => el.remove(), 750);
}

/** Flash a big "COMBO ×N!" overlay in the center of the game view. @tag ARCADE */
function _arcadeShowCombo(n) {
  const body = document.getElementById('arcade-body');
  if (!body) return;
  const existing = body.querySelector('.arcade-combo');
  if (existing) existing.remove();
  const el = document.createElement('div');
  el.className = 'arcade-combo';
  el.textContent = `COMBO ×${n}!`;
  body.appendChild(el);
  setTimeout(() => el.remove(), 900);
}

/** Count positional letter mismatches between two same-length strings. @tag ARCADE */
function _arcadeLetterDiff(a, b) {
  if (a.length !== b.length) return Infinity;
  let d = 0;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) d++;
  return d;
}

/** Apply streak heat color to a streak HUD element. @tag ARCADE */
function _arcadeApplyStreakStyle(el, n) {
  if (!el) return;
  el.classList.remove('streak--warm', 'streak--hot', 'streak--fire');
  if (n >= 15) el.classList.add('streak--fire');
  else if (n >= 10) el.classList.add('streak--hot');
  else if (n >= 5)  el.classList.add('streak--warm');
}

const _SCORE_MILESTONES  = [100, 250, 500, 1000, 2000];
const _STREAK_MILESTONES = [10, 20, 30];

/** Show a temporary achievement banner over the game area. @tag ARCADE */
function _arcadeMilestone(text) {
  const body = document.getElementById('arcade-body');
  if (!body) return;
  const existing = body.querySelector('.arcade-milestone');
  if (existing) existing.remove();
  const el = document.createElement('div');
  el.className = 'arcade-milestone';
  el.textContent = text;
  body.appendChild(el);
  setTimeout(() => el.remove(), 1800);
}

/**
 * Fire a milestone banner the first time a score/streak threshold is crossed.
 * Call after every correct answer.  milestonesHit is a Set stored on the game state.
 * @tag ARCADE
 */
function _arcadeCheckMilestone(milestonesHit, prevScore, newScore, streak) {
  if (!milestonesHit) return;
  for (const m of _SCORE_MILESTONES) {
    const key = `score_${m}`;
    if (!milestonesHit.has(key) && prevScore < m && newScore >= m) {
      milestonesHit.add(key);
      _arcadeMilestone(`${m} pts reached!`);
      return;
    }
  }
  for (const s of _STREAK_MILESTONES) {
    const key = `streak_${s}`;
    if (!milestonesHit.has(key) && streak >= s) {
      milestonesHit.add(key);
      _arcadeMilestone(`${s}x streak!`);
      return;
    }
  }
}

/** Shared canvas rounded-rect path helper. @tag ARCADE */
function _arcadeRoundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
