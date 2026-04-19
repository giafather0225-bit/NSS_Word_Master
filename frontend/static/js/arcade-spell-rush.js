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
};

let _sr = null;

/** Start Spell Rush. @tag ARCADE */
async function srStart() {
  srStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="sr-view">
      <div class="wi-hud">
        <span>Score: <b id="sr-score">0</b></span>
        <span>Time: <b id="sr-time">60</b>s</span>
        <span>Streak: <b id="sr-streak">0</b></span>
      </div>
      <div class="sr-definition" id="sr-definition">Loading…</div>
      <div class="sr-boxes" id="sr-boxes"></div>
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
    running: true,
    startedAt: performance.now(),
    current: null,
  };

  if (typeof sfxStart === 'function') sfxStart();
  _srNextWord();

  const input = document.getElementById('sr-input');
  input.focus();
  input.addEventListener('input', _srOnInput);
  input.addEventListener('keydown', _srOnKeydown);

  _srTick();
}

/** Stop Spell Rush. @tag ARCADE */
function srStop() {
  if (!_sr) return;
  _sr.running = false;
  const input = document.getElementById('sr-input');
  if (input) {
    input.removeEventListener('input', _srOnInput);
    input.removeEventListener('keydown', _srOnKeydown);
  }
  _sr = null;
}

function _srTick() {
  if (!_sr || !_sr.running) return;
  const elapsed = performance.now() - _sr.startedAt;
  const remain = Math.max(0, SR_CFG.roundMs - elapsed);
  const el = document.getElementById('sr-time');
  if (el) el.textContent = String(Math.ceil(remain / 1000));
  if (remain <= 0) {
    _srGameOver();
    return;
  }
  requestAnimationFrame(_srTick);
}

function _srNextWord() {
  if (!_sr) return;
  const pick = _sr.pool[Math.floor(Math.random() * _sr.pool.length)];
  _sr.current = { word: pick.word.toLowerCase(), def: pick.definition, typed: '' };

  const defEl = document.getElementById('sr-definition');
  if (defEl) defEl.textContent = pick.definition;

  _srRenderBoxes();
  const input = document.getElementById('sr-input');
  if (input) input.value = '';
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
  if (!_sr || !_sr.running) return;
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
  if (!_sr || !_sr.running) return;
  const { word, typed } = _sr.current;
  _sr.total += 1;

  if (typed === word) {
    _sr.correct += 1;
    _sr.streak += 1;
    const letterPts = word.length * SR_CFG.perLetterPoints;
    const streakMult = 1 + Math.min(1.0, _sr.streak * 0.08); // up to 2x
    _sr.score += Math.round((SR_CFG.wordCompleteBase + letterPts) * streakMult);
    if (typeof sfxHit === 'function') sfxHit(_sr.streak);
    if (_sr.streak > 0 && _sr.streak % 5 === 0 && typeof sfxCombo === 'function') sfxCombo();
  } else {
    _sr.streak = 0;
    _sr.score = Math.max(0, _sr.score - SR_CFG.wrongPenalty);
    if (typeof sfxMiss === 'function') sfxMiss();
    // Flash the boxes red briefly
    const box = document.getElementById('sr-boxes');
    if (box) {
      box.classList.add('sr-shake');
      setTimeout(() => box.classList.remove('sr-shake'), 300);
    }
  }
  _srUpdateHUD();
  _srNextWord();
}

function _srUpdateHUD() {
  const s = document.getElementById('sr-score');
  const st = document.getElementById('sr-streak');
  if (s) s.textContent = String(_sr.score);
  if (st) st.textContent = String(_sr.streak);
}

async function _srGameOver() {
  if (!_sr) return;
  const state = _sr;
  _sr.running = false;
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('spell_rush', state.score, state.correct, state.total, accuracy);
  _arcadeRenderGameOver({ state, accuracy, result, replay: 'srStart()' });
}
