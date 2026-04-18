/* ================================================================
   arcade.js — Arcade overlay shell + game lobby
   Section: Arcade
   Dependencies: core.js, arcade-word-invaders.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const ARCADE_GAMES = [
  { id: 'word_invaders',    category: 'english', title: 'Word Invaders', icon: '👾', sub: 'Type the falling word before it hits the ground', enabled: true },
  { id: 'definition_match', category: 'english', title: 'Match or Not',  icon: '✅', sub: 'Does the definition match? Tap ✓ or ✗. 60 seconds.', enabled: true },
  { id: 'spell_rush',       category: 'english', title: 'Spell Rush',    icon: '⌨️', sub: 'Spell each word letter-by-letter. Beat the clock.', enabled: true },
  { id: 'crossword',        category: 'english', title: 'Crossword',     icon: '🧩', sub: 'Fill the grid using definitions as clues.', enabled: true },
  { id: 'math_invaders',    category: 'math',    title: 'Math Invaders', icon: '🚀', sub: 'Type the answer before the equation lands.', enabled: true },
  { id: 'sudoku',           category: 'math',    title: 'Sudoku',        icon: '🔢', sub: '4×4, 6×6, or 9×9 — classic number puzzle.', enabled: true },
  { id: 'make24',           category: 'math',    title: 'Make 24',       icon: '🎯', sub: 'Combine four numbers to reach 24. 90 seconds.', enabled: true },
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
  btn.textContent = arcadeSfxIsMuted() ? '🔇' : '🔊';
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

  // Fetch personal bests in parallel
  const bests = await Promise.all(
    ARCADE_GAMES.map((g) =>
      g.enabled
        ? fetch(`/api/arcade/best/${g.id}`).then((r) => r.ok ? r.json() : { score: 0 }).catch(() => ({ score: 0 }))
        : Promise.resolve({ score: 0 })
    )
  );

  const cardFor = (g, i) => {
    const cls = g.enabled ? 'arcade-game-card' : 'arcade-game-card disabled';
    const click = g.enabled ? `onclick="_launchArcadeGame('${g.id}')"` : '';
    const pb = bests[i].score || 0;
    const pbLine = g.enabled
      ? `<div class="arcade-game-pb">🏆 Best: <b>${pb}</b></div>`
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
    <div class="arcade-section-label">📚 English</div>
    <div class="arcade-list">${byCat('english')}</div>
    <div class="arcade-section-label">📐 Math</div>
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

/** Fetch arcade word pool. @tag ARCADE */
async function _arcadeFetchWords(count = 40) {
  try {
    const r = await fetch(`/api/arcade/words?count=${count}`);
    if (!r.ok) return [];
    const data = await r.json();
    return data.words || [];
  } catch (e) {
    console.error('[arcade] word fetch failed', e);
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
    ? `<div class="wi-new-best">🏆 New Personal Best!</div>`
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

  // Audio stings
  if (result.new_best && typeof sfxNewBest === 'function') {
    sfxNewBest();
  } else if (typeof sfxGameOver === 'function') {
    sfxGameOver();
  }
}
