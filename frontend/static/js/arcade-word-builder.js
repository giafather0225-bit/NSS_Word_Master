/* ================================================================
   arcade-word-builder.js — Tile-based anagram / word-building game
   Section: Arcade
   Dependencies: arcade.js, arcade-sfx.js
   API endpoints: POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const WB_CFG = {
  roundMs: 60000,
  baseScore: 15,         // per letter
  streakLevels: [0, 3, 6, 10],
  streakMults:  [1.0, 1.2, 1.5, 2.0],
  wrongPenalty: 10,
  maxHints: 3,
  feedbackMs: 400,
  minLen: 4,
  maxLen: 9,
};

let _wb = null;

/** Start Word Builder. @tag ARCADE */
async function wbStart() {
  wbStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="wb-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SCORE</span><b id="wb-score">0</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">TIME</span><b id="wb-time">60</b>s</div>
        <div class="wi-hud-item"><span class="wi-hud-label">STREAK</span><b id="wb-streak">0</b>x</div>
        <button type="button" class="wi-hud-quit" onclick="arcadeReturnToLobby()" aria-label="Quit">✕</button>
      </div>
      <div class="wb-loading">Loading words…</div>
    </div>`;

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('word_builder');

  const words = await _arcadeFetchWords(80);
  const pool = words.filter((w) => {
    const len = w.word.replace(/[^a-zA-Z]/g, '').length;
    return len >= WB_CFG.minLen && len <= WB_CFG.maxLen && w.definition;
  });

  if (pool.length < 3) {
    body.innerHTML = `
      <div class="wi-gameover">
        <h2>Not enough words</h2>
        <div class="stat">Need at least 3 words (4–9 letters).</div>
        <button class="wi-btn" onclick="arcadeReturnToLobby()">Back</button>
      </div>`;
    return;
  }

  _wb = {
    pool,
    used: new Set(),
    score: 0,
    streak: 0,
    correct: 0,
    total: 0,
    running: true,
    startedAt: performance.now(),
    current: null,
    lock: false,
  };

  if (typeof sfxStart === 'function') sfxStart();
  _wbRenderShell();
  _wbNextWord();
  _wbTick();
}

/** Stop Word Builder. @tag ARCADE */
function wbStop() {
  if (!_wb) return;
  _wb.running = false;
  _wb = null;
}

function _wbTick() {
  if (!_wb || !_wb.running) return;
  if (document.hidden) { requestAnimationFrame(_wbTick); return; }
  const elapsed = performance.now() - _wb.startedAt;
  const remain = Math.max(0, WB_CFG.roundMs - elapsed);
  const el = document.getElementById('wb-time');
  if (el) el.textContent = String(Math.ceil(remain / 1000));
  if (remain <= 0) { _wbGameOver(); return; }
  requestAnimationFrame(_wbTick);
}

function _wbRenderShell() {
  const body = document.getElementById('arcade-body');
  if (!body || !_wb) return;
  body.innerHTML = `
    <div class="wb-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SCORE</span><b id="wb-score">0</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">TIME</span><b id="wb-time">60</b>s</div>
        <div class="wi-hud-item"><span class="wi-hud-label">STREAK</span><b id="wb-streak">0</b>x</div>
        <button type="button" class="wi-hud-quit" onclick="arcadeReturnToLobby()" aria-label="Quit">✕</button>
      </div>
      <div class="wb-card">
        <div class="wb-def" id="wb-def">—</div>
        <div class="wb-answer-row" id="wb-answer-row"></div>
        <div class="wb-divider"></div>
        <div class="wb-tiles" id="wb-tiles"></div>
        <div class="wb-actions">
          <button type="button" class="wi-btn secondary wb-hint-btn" id="wb-hint-btn" onclick="_wbHint()">
            Hint (<span id="wb-hints-left">${WB_CFG.maxHints}</span>)
          </button>
          <button type="button" class="wi-btn secondary" onclick="_wbClear()">Clear</button>
          <button type="button" class="wi-btn secondary" onclick="_wbShuffleTiles()">Shuffle</button>
        </div>
      </div>
    </div>`;
}

function _wbNextWord() {
  if (!_wb) return;
  let available = _wb.pool.filter((w) => !_wb.used.has(w.word));
  if (available.length === 0) {
    _wb.used.clear();
    available = _wb.pool.slice();
  }
  const entry = available[Math.floor(Math.random() * available.length)];
  _wb.used.add(entry.word);

  const clean = entry.word.toUpperCase().replace(/[^A-Z]/g, '');
  const letters = clean.split('');
  const shuffled = _wbFisherYates(letters.slice());
  // ensure shuffle is different from the answer
  let tries = 0;
  while (shuffled.join('') === clean && tries < 20) {
    _wbFisherYates(shuffled);
    tries++;
  }

  _wb.current = {
    word: clean,
    definition: entry.definition,
    tiles: shuffled.map((l, i) => ({ id: i, letter: l, placed: false, revealed: false })),
    answer: [],
    hints: 0,
  };
  _wb.lock = false;
  _wbUpdateBoard();
}

function _wbFisherYates(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function _wbUpdateBoard() {
  if (!_wb || !_wb.current) return;
  const { current } = _wb;

  const defEl = document.getElementById('wb-def');
  if (defEl) defEl.textContent = current.definition;

  const answerRow = document.getElementById('wb-answer-row');
  if (answerRow) {
    const placed = current.answer.map((t) =>
      `<div class="wb-tile wb-answer-tile${t.revealed ? ' wb-tile--revealed' : ''}" data-id="${t.id}" onclick="_wbReturnTile(${t.id})">${t.letter}</div>`
    ).join('');
    const blanks = Array.from(
      { length: current.tiles.length - current.answer.length },
      () => `<div class="wb-tile wb-blank-tile"></div>`
    ).join('');
    answerRow.innerHTML = placed + blanks;
  }

  const tilesEl = document.getElementById('wb-tiles');
  if (tilesEl) {
    tilesEl.innerHTML = current.tiles
      .filter((t) => !t.placed)
      .map((t) => `<div class="wb-tile wb-pool-tile" data-id="${t.id}" onclick="_wbPlaceTile(${t.id})">${t.letter}</div>`)
      .join('');
  }

  const hintsLeft = document.getElementById('wb-hints-left');
  if (hintsLeft) hintsLeft.textContent = String(WB_CFG.maxHints - (current.hints || 0));

  const hintBtn = document.getElementById('wb-hint-btn');
  if (hintBtn) hintBtn.disabled = (current.hints || 0) >= WB_CFG.maxHints;

  _wbUpdateHUD();
}

function _wbPlaceTile(id) {
  if (!_wb || !_wb.current || _wb.lock) return;
  const tile = _wb.current.tiles.find((t) => t.id === id);
  if (!tile || tile.placed) return;
  tile.placed = true;
  _wb.current.answer.push(tile);
  _wbUpdateBoard();
  if (_wb.current.answer.length === _wb.current.tiles.length) {
    _wbCheck();
  }
}

function _wbReturnTile(id) {
  if (!_wb || !_wb.current || _wb.lock) return;
  const idx = _wb.current.answer.findIndex((t) => t.id === id);
  if (idx < 0) return;
  const [tile] = _wb.current.answer.splice(idx, 1);
  tile.placed = false;
  tile.revealed = false;
  _wbUpdateBoard();
}

function _wbClear() {
  if (!_wb || !_wb.current || _wb.lock) return;
  _wb.current.answer.forEach((t) => { t.placed = false; t.revealed = false; });
  _wb.current.answer = [];
  _wbUpdateBoard();
}

function _wbShuffleTiles() {
  if (!_wb || !_wb.current || _wb.lock) return;
  _wbFisherYates(_wb.current.tiles);
  _wbUpdateBoard();
}

function _wbHint() {
  if (!_wb || !_wb.current || _wb.lock) return;
  if ((_wb.current.hints || 0) >= WB_CFG.maxHints) return;
  _wb.current.hints = (_wb.current.hints || 0) + 1;

  const answerLen = _wb.current.answer.length;
  const nextLetter = _wb.current.word[answerLen];
  // find first unplaced tile matching the needed letter
  const tile = _wb.current.tiles.find((t) => !t.placed && t.letter === nextLetter);
  if (tile) {
    tile.placed = true;
    tile.revealed = true;
    _wb.current.answer.push(tile);
    _wbUpdateBoard();
    if (_wb.current.answer.length === _wb.current.tiles.length) _wbCheck();
  }
}

function _wbCheck() {
  if (!_wb || !_wb.current) return;
  _wb.lock = true;
  const built = _wb.current.answer.map((t) => t.letter).join('');
  const correct = built === _wb.current.word;
  _wb.total += 1;

  const answerRow = document.getElementById('wb-answer-row');

  if (correct) {
    _wb.correct += 1;
    _wb.streak += 1;
    const mult = _wbStreakMult(_wb.streak);
    const pts = Math.round(_wb.current.tiles.length * WB_CFG.baseScore * mult);
    _wb.score += pts;
    if (answerRow) {
      answerRow.classList.add('wb-answer--correct');
      answerRow.querySelectorAll('.wb-answer-tile').forEach((el, i) => {
        el.style.animationDelay = `${i * 55}ms`;
        el.classList.add('wb-tile--burst');
      });
    }
    if (typeof sfxHit === 'function') sfxHit(_wb.streak);
    if (_wb.streak > 0 && _wb.streak % 5 === 0 && typeof sfxCombo === 'function') sfxCombo();
    _wbUpdateHUD();
    setTimeout(() => {
      if (!_wb || !_wb.running) return;
      _wbRenderShell();
      _wbNextWord();
    }, WB_CFG.feedbackMs);
  } else {
    _wb.streak = 0;
    _wb.score = Math.max(0, _wb.score - WB_CFG.wrongPenalty);
    if (answerRow) {
      answerRow.classList.add('wb-answer--wrong');
      setTimeout(() => {
        if (!_wb || !_wb.current) return;
        answerRow.classList.remove('wb-answer--wrong');
        _wb.current.answer.forEach((t) => { t.placed = false; t.revealed = false; });
        _wb.current.answer = [];
        _wb.lock = false;
        _wbUpdateBoard();
      }, WB_CFG.feedbackMs * 1.5);
    }
    if (typeof sfxMiss === 'function') sfxMiss();
    _wbUpdateHUD();
  }
}

function _wbStreakMult(streak) {
  const { streakLevels, streakMults } = WB_CFG;
  let mult = streakMults[0];
  for (let i = 0; i < streakLevels.length; i++) {
    if (streak >= streakLevels[i]) mult = streakMults[i];
  }
  return mult;
}

function _wbUpdateHUD() {
  if (!_wb) return;
  const s = document.getElementById('wb-score');
  const st = document.getElementById('wb-streak');
  if (s) s.textContent = String(_wb.score);
  if (st) st.textContent = String(_wb.streak);
}

async function _wbGameOver() {
  if (!_wb) return;
  const state = _wb;
  _wb.running = false;
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('word_builder', state.score, state.correct, state.total, accuracy);
  _arcadeRenderGameOver({ state, accuracy, result, replayFn: () => wbStart() });
}
