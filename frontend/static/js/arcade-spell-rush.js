/* ================================================================
   arcade-spell-rush.js — Wordle-style letter-by-letter spelling race
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const SR_CFG = {
  roundMs: 60000,
  minLen: 3,
  maxLen: 10,
  perLetterPoints: 8,
  wordCompleteBase: 60,
  wrongPenalty: 10,
  hintPenalty: 20,
};

const SR_LEVELS = {
  easy:   { label: 'Easy',   roundMs: 90000, timeLabel: '90s' },
  normal: { label: 'Normal', roundMs: 60000, timeLabel: '60s' },
  hard:   { label: 'Hard',   roundMs: 45000, timeLabel: '45s' },
};

let _sr = null;

/** Level picker for Spell Rush. @tag ARCADE */
async function srShowLevelPicker() {
  srStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Difficulty</h2>
      <div class="wi-level-sub">Spell Rush</div>
      <div class="wi-level-list" id="sr-level-list">Loading…</div>
      <div class="arcade-how-to-play">
        <div class="arcade-htp-title">How to play</div>
        <ul class="arcade-htp-list">
          <li>A definition appears — type the matching word as fast as you can.</li>
          <li>Score points for each correct spelling; the faster you type, the more points.</li>
          <li>Three wrong attempts on the same word ends your streak.</li>
          <li>Complete all words before time runs out to win.</li>
        </ul>
      </div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;

  const bests = await Promise.all(
    Object.keys(SR_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/spell_rush?level=${lv}`)
        .then((r) => (r.ok ? r.json() : { score: 0 }))
        .catch(() => ({ score: 0 }))
    )
  );

  const list = document.getElementById('sr-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(SR_LEVELS)
    .map(([key, cfg], i) => {
      const pb = bests[i].score || 0;
      return `
        <div class="wi-level-card" onclick="srStart('${key}')">
          <div class="wi-level-icon wi-level-icon--${key}">${key[0].toUpperCase()}</div>
          <div class="wi-level-name">${cfg.label}</div>
          <div class="wi-level-spec">${cfg.timeLabel} round</div>
          <div class="wi-level-pb">Best: ${pb}</div>
        </div>`;
    })
    .join('');
}

/** Start Spell Rush. @tag ARCADE */
async function srStart(level = 'normal') {
  srStop();
  const lv = SR_LEVELS[level] || SR_LEVELS.normal;
  SR_CFG.roundMs = lv.roundMs;
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="sr-view">
      <div class="wi-hud">
        <span>Score: <b id="sr-score">0</b></span>
        <span>Time: <b id="sr-time">${Math.round(lv.roundMs / 1000)}</b>s</span>
        <span>Streak: <b id="sr-streak">0</b></span>
      </div>
      <div class="sr-definition" id="sr-definition">Loading…</div>
      <div class="sr-boxes" id="sr-boxes"></div>
      <button type="button" class="sr-hint-btn" id="sr-hint-btn" onclick="_srHint()">? Hint <span class="sr-hint-cost">−${SR_CFG.hintPenalty} pts</span></button>
      <input type="text" id="sr-input" class="wi-input" autocomplete="off"
             autocapitalize="off" spellcheck="false"
             placeholder="Type the word" maxlength="20">
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Quit</button>
    </div>`;

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('spell_rush');

  const all = await _arcadeFetchWords(80);
  const words = all.filter((w) => {
    const len = w.word.length;
    return len >= SR_CFG.minLen && len <= SR_CFG.maxLen && /^[a-zA-Z]+$/.test(w.word);
  });
  if (words.length < 5) {
    body.innerHTML = `
      <div class="wi-gameover">
        <h2>Not enough words</h2>
        <div class="stat">Need ≥5 words (3–10 letters).</div>
        <button class="wi-btn" onclick="arcadeReturnToLobby()">Back</button>
      </div>`;
    return;
  }

  _sr = {
    pool: words,
    score: 0,
    streak: 0,
    correct: 0,
    total: 0,
    hints: 0,
    running: true,
    lock: false,       // C1: prevents _srOnInput + Enter double-submit
    startedAt: performance.now(),
    wordStartedAt: performance.now(),
    avgWordMs: 0,      // QW4: rolling avg solve time (ms) for speed bonus
    current: null,
    tickHandle: null,
    level,
    milestonesHit: new Set(),
  };

  if (typeof sfxStart === 'function') sfxStart();
  _srNextWord();

  const input = document.getElementById('sr-input');
  if (!input) return;
  input.focus();
  input.addEventListener('input', _srOnInput);
  input.addEventListener('keydown', _srOnKeydown);

  _sr.tickHandle = setInterval(_srTick, 500);  // Fix #19: setInterval instead of rAF
}

/** Stop Spell Rush. @tag ARCADE */
function srStop() {
  if (!_sr) return;
  _sr.running = false;
  if (_sr.tickHandle) { clearInterval(_sr.tickHandle); _sr.tickHandle = null; }
  const input = document.getElementById('sr-input');
  if (input) {
    input.removeEventListener('input', _srOnInput);
    input.removeEventListener('keydown', _srOnKeydown);
  }
  _sr = null;
}

// Fix #19: setInterval-based tick (500ms) — no rAF waste
function _srTick() {
  if (!_sr || !_sr.running) return;
  if (document.hidden) return;
  const elapsed = performance.now() - _sr.startedAt;
  const remain = Math.max(0, SR_CFG.roundMs - elapsed);
  const el = document.getElementById('sr-time');
  if (el) {
    el.textContent = String(Math.ceil(remain / 1000));
    el.classList.toggle('sr-time--urgent', remain <= 10000);
  }
  if (remain <= 0) {
    if (_sr.tickHandle) { clearInterval(_sr.tickHandle); _sr.tickHandle = null; }
    _srGameOver();
  }
}

function _srNextWord() {
  if (!_sr) return;
  _sr.lock = false;   // C1: release submit lock for the next word
  _sr.wordStartedAt = performance.now();
  const pick = _sr.pool[Math.floor(Math.random() * _sr.pool.length)];
  _sr.current = { word: pick.word.toLowerCase(), def: pick.definition, typed: '', hintUsed: false };

  const defEl = document.getElementById('sr-definition');
  if (defEl) defEl.textContent = pick.definition;

  _srRenderBoxes();
  const input = document.getElementById('sr-input');
  if (input) input.value = '';

  const hintBtn = document.getElementById('sr-hint-btn');
  if (hintBtn) { hintBtn.disabled = false; hintBtn.classList.remove('sr-hint-btn--used'); }
}

function _srRenderBoxes() {
  const box = document.getElementById('sr-boxes');
  if (!box || !_sr) return;
  const { word, typed } = _sr.current;
  const cells = [];
  for (let i = 0; i < word.length; i++) {
    const ch = typed[i] || '';
    let cls = 'sr-cell';
    if (ch) {
      cls += ch === word[i] ? ' sr-cell--ok' : ' sr-cell--bad';
    } else if (i === typed.length) {
      cls += ' sr-cell--active';
    }
    cells.push(`<span class="${cls}">${ch.toUpperCase()}</span>`);
  }
  box.innerHTML = cells.join('');
}

function _srOnInput(e) {
  if (!_sr || !_sr.running || _sr.lock) return;  // A: block input during lock (prevents overwriting correct/wrong feedback)
  const value = e.target.value.toLowerCase().replace(/[^a-z]/g, '');
  _sr.current.typed = value.slice(0, _sr.current.word.length);
  e.target.value = _sr.current.typed;
  _srRenderBoxes();

  // Auto-submit when length matches
  if (_sr.current.typed.length === _sr.current.word.length) {
    _srSubmit();
  }
}

function _srOnKeydown(e) {
  if (!_sr || !_sr.running) return;
  if (e.key === 'Enter') {
    e.preventDefault();
    _srSubmit();
  }
}

function _srSubmit() {
  if (!_sr || !_sr.running || _sr.lock) return;  // C1: lock prevents double-submit
  _sr.lock = true;
  const { word, typed } = _sr.current;
  _sr.total += 1;

  if (typed === word) {
    _sr.correct += 1;
    _sr.streak += 1;
    const letterPts = word.length * SR_CFG.perLetterPoints;
    const streakMult = 1 + Math.min(1.0, _sr.streak * 0.08); // Fix #10: capped at 2× (streak≥13)
    let gained = Math.round((SR_CFG.wordCompleteBase + letterPts) * streakMult);

    // QW4: speed bonus — if solved faster than 70% of rolling avg, award +FAST!
    const solveMs = performance.now() - (_sr.wordStartedAt || performance.now());
    if (_sr.avgWordMs > 0 && solveMs < _sr.avgWordMs * 0.70) {
      const fastBonus = Math.round(gained * 0.25);
      gained += fastBonus;
      if (typeof _arcadeFloatScore === 'function') {
        _arcadeFloatScore(`+${fastBonus} FAST!`);
        setTimeout(() => _arcadeFloatScore(gained), 250);
      }
    } else {
      if (typeof _arcadeFloatScore === 'function') _arcadeFloatScore(gained);
    }
    // Update rolling average (exponential moving avg, α=0.3)
    _sr.avgWordMs = _sr.avgWordMs === 0 ? solveMs : _sr.avgWordMs * 0.7 + solveMs * 0.3;

    const prevScore = _sr.score;
    _sr.score += gained;
    if (typeof _arcadeCheckMilestone === 'function') _arcadeCheckMilestone(_sr.milestonesHit, prevScore, _sr.score, _sr.streak);
    if (typeof sfxHit === 'function') sfxHit(_sr.streak);
    if (_sr.streak > 0 && _sr.streak % 5 === 0) {
      if (typeof sfxCombo === 'function') sfxCombo();
      if (typeof _arcadeShowCombo === 'function') _arcadeShowCombo(_sr.streak);
      const st = document.getElementById('sr-streak');
      if (st) { st.classList.remove('combo-burst'); void st.offsetWidth; st.classList.add('combo-burst'); }
    }
  } else {
    _sr.streak = 0;
    _sr.score = Math.max(0, _sr.score - SR_CFG.wrongPenalty);
    if (typeof sfxMiss === 'function') sfxMiss();
    if (navigator.vibrate) navigator.vibrate(80);  // Fix #14: haptic feedback on wrong
    const box = document.getElementById('sr-boxes');
    if (box) {
      box.classList.add('sr-shake');
      setTimeout(() => box.classList.remove('sr-shake'), 300);
      // QW1: "Almost!" if only 1 letter wrong
      const diff = typeof _arcadeLetterDiff === 'function' ? _arcadeLetterDiff(typed, word) : Infinity;
      const almostLabel = diff === 1 ? `<span class="sr-almost">Almost!</span>` : '';
      const { word: w } = _sr.current;
      box.innerHTML = almostLabel + w.split('').map((ch) =>
        `<span class="sr-cell sr-cell--ok">${ch.toUpperCase()}</span>`
      ).join('');
    }
    _srUpdateHUD();
    setTimeout(() => {
      if (!_sr || !_sr.running) return;
      _srNextWord();
      const inp = document.getElementById('sr-input');
      if (inp) inp.focus();
    }, 900);
    return;
  }
  _srUpdateHUD();
  _srNextWord();
}

function _srUpdateHUD() {
  const s = document.getElementById('sr-score');
  const st = document.getElementById('sr-streak');
  if (s) s.textContent = String(_sr.score);
  if (st) { st.textContent = String(_sr.streak); if (typeof _arcadeApplyStreakStyle === 'function') _arcadeApplyStreakStyle(st, _sr.streak); }
}

function _srHint() {
  if (!_sr || !_sr.running || _sr.lock || _sr.current.hintUsed) return;
  _sr.current.hintUsed = true;
  _sr.hints += 1;
  _sr.streak = 0;
  _sr.score = Math.max(0, _sr.score - SR_CFG.hintPenalty);
  _srUpdateHUD();

  // Reveal first letter into typed + input
  _sr.current.typed = _sr.current.word[0];
  const input = document.getElementById('sr-input');
  if (input) { input.value = _sr.current.word[0]; input.focus(); }
  _srRenderBoxes();

  const btn = document.getElementById('sr-hint-btn');
  if (btn) { btn.disabled = true; btn.classList.add('sr-hint-btn--used'); }
}

async function _srGameOver() {
  if (!_sr || !_sr.running) return;
  // C2: mirror srStop() cleanup — clear interval + remove listeners before nulling state
  _sr.running = false;
  if (_sr.tickHandle) { clearInterval(_sr.tickHandle); _sr.tickHandle = null; }
  const input = document.getElementById('sr-input');
  if (input) {
    input.removeEventListener('input', _srOnInput);
    input.removeEventListener('keydown', _srOnKeydown);
  }
  const state = { ..._sr };
  _sr = null;
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('spell_rush', state.score, state.correct, state.total, accuracy, state.level || 'normal');
  _arcadeRenderGameOver({ state, accuracy, result, replayFn: () => srStart(state.level || 'normal') });
}
