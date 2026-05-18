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

const WB_LEVELS = {
  easy:   { label: 'Easy',   roundMs: 90000, timeLabel: '90s' },
  normal: { label: 'Normal', roundMs: 60000, timeLabel: '60s' },
  hard:   { label: 'Hard',   roundMs: 45000, timeLabel: '45s' },
};

let _wb = null;
let _wbDragId = null;
let _wbDragFromAnswer = false;

/** Level picker for Word Builder. @tag ARCADE */
async function wbShowLevelPicker() {
  wbStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Difficulty</h2>
      <div class="wi-level-sub">Word Builder</div>
      <div class="wi-level-list" id="wb-level-list">Loading…</div>
      <div class="arcade-how-to-play">
        <div class="arcade-htp-title">How to play</div>
        <ul class="arcade-htp-list">
          <li>Scrambled letters are shown — arrange them to spell the target word.</li>
          <li>A definition clue is provided to help you identify the word.</li>
          <li>Click letters to build your answer, then submit.</li>
          <li>Complete all words before time runs out for a time bonus.</li>
        </ul>
      </div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;

  const bests = await Promise.all(
    Object.keys(WB_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/word_builder?level=${lv}`)
        .then((r) => (r.ok ? r.json() : { score: 0 }))
        .catch(() => ({ score: 0 }))
    )
  );

  const list = document.getElementById('wb-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(WB_LEVELS)
    .map(([key, cfg], i) => {
      const pb = bests[i].score || 0;
      const pbAcc = bests[i].accuracy || 0;
      return `
        <div class="wi-level-card" onclick="wbStart('${key}')">
          <div class="wi-level-icon wi-level-icon--${key}">${key[0].toUpperCase()}</div>
          <div class="wi-level-name">${cfg.label}</div>
          <div class="wi-level-spec">${cfg.timeLabel} round</div>
          <div class="wi-level-pb">Best: ${pb}${_arcadeLevelStarsHTML(pbAcc)}</div>
        </div>`;
    })
    .join('');
}

/** Start Word Builder. @tag ARCADE */
async function wbStart(level = 'normal') {
  wbStop();
  const lv = WB_LEVELS[level] || WB_LEVELS.normal;
  WB_CFG.roundMs = lv.roundMs;
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="wb-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SCORE</span><b id="wb-score">0</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">TIME</span><b id="wb-time">${Math.round(lv.roundMs / 1000)}</b>s</div>
        <div class="wi-hud-item"><span class="wi-hud-label">STREAK</span><b id="wb-streak">0</b>x</div>
        <button type="button" class="wi-hud-quit" onclick="arcadeReturnToLobby()" aria-label="Quit"><i data-lucide="x"></i></button>
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
    wordHistory: [],   // Fix #18: track {word, correct, pts}
    tickHandle: null,
    level,
    milestonesHit: new Set(),
  };

  if (typeof sfxStart === 'function') sfxStart();
  _wbRenderShell();
  _wbNextWord();
  _wb.tickHandle = setInterval(_wbTick, 500);  // Fix #19: setInterval instead of rAF
  document.addEventListener('keydown', _wbKeydown);
}

/** Stop Word Builder. @tag ARCADE */
function wbStop() {
  if (!_wb) return;
  _wb.running = false;
  if (_wb.tickHandle) { clearInterval(_wb.tickHandle); _wb.tickHandle = null; }
  document.removeEventListener('keydown', _wbKeydown);
  _wb = null;
}

function _wbKeydown(e) {
  if (!_wb || !_wb.running || _wb.lock) return;
  if (e.key === 'Backspace') {
    e.preventDefault();
    for (let i = _wb.current.answer.length - 1; i >= 0; i--) {
      if (!_wb.current.answer[i].revealed) { _wbReturnTile(_wb.current.answer[i].id); return; }
    }
    return;
  }
  if (e.key.length !== 1 || !/^[a-zA-Z]$/.test(e.key)) return;
  const letter = e.key.toUpperCase();
  const tile = _wb.current.tiles.find((t) => !t.placed && t.letter === letter);
  if (tile) _wbPlaceTile(tile.id);
}

// Fix #19: setInterval-based tick (500ms) — no rAF waste
function _wbTick() {
  if (!_wb || !_wb.running) return;
  if (document.hidden) return;
  const elapsed = performance.now() - _wb.startedAt;
  const remain = Math.max(0, WB_CFG.roundMs - elapsed);
  const el = document.getElementById('wb-time');
  if (el) {
    el.textContent = String(Math.ceil(remain / 1000));
    el.classList.toggle('wb-time--urgent', remain <= 10000);
  }
  if (remain <= 0) {
    if (_wb.tickHandle) { clearInterval(_wb.tickHandle); _wb.tickHandle = null; }
    _wbGameOver();
  }
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
        <button type="button" class="wi-hud-quit" onclick="arcadeReturnToLobby()" aria-label="Quit"><i data-lucide="x"></i></button>
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
        <p class="wb-keyboard-hint">Type letters &nbsp;·&nbsp; Backspace to undo</p>
      </div>
    </div>`;
  if (typeof lucide !== 'undefined') lucide.createIcons();
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

/**
 * Shuffle array in place using Fisher-Yates algorithm.
 * Also returns the same array for convenience (mirrors Array.prototype.sort).
 * @param {Array} arr - mutated in place
 * @returns {Array} the same arr reference
 */
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
      `<div class="wb-tile wb-answer-tile${t.revealed ? ' wb-tile--revealed' : ''}" data-id="${t.id}" draggable="true"
        onclick="_wbReturnTile(${t.id})" ondragstart="_wbDragStart(event,${t.id},true)"
        ondragend="_wbDragEnd(event)">${t.letter}</div>`
    ).join('');
    const blanks = Array.from(
      { length: current.tiles.length - current.answer.length },
      () => `<div class="wb-tile wb-blank-tile"></div>`
    ).join('');
    answerRow.innerHTML = placed + blanks;
    answerRow.ondragover  = (e) => _wbDragOver(e);
    answerRow.ondragenter = (e) => _wbDragEnter(e, answerRow);
    answerRow.ondragleave = (e) => _wbDragLeave(e, answerRow);
    answerRow.ondrop      = (e) => _wbDrop(e, false, answerRow);
  }

  const tilesEl = document.getElementById('wb-tiles');
  if (tilesEl) {
    tilesEl.innerHTML = current.tiles
      .filter((t) => !t.placed)
      .map((t) => `<div class="wb-tile wb-pool-tile" data-id="${t.id}" draggable="true"
        onclick="_wbPlaceTile(${t.id})" ondragstart="_wbDragStart(event,${t.id},false)"
        ondragend="_wbDragEnd(event)">${t.letter}</div>`)
      .join('');
    tilesEl.ondragover  = (e) => _wbDragOver(e);
    tilesEl.ondragenter = (e) => _wbDragEnter(e, tilesEl);
    tilesEl.ondragleave = (e) => _wbDragLeave(e, tilesEl);
    tilesEl.ondrop      = (e) => _wbDrop(e, true, tilesEl);
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
  const answerRow = document.getElementById('wb-answer-row');
  if (answerRow && !tile.revealed) {
    const tiles = answerRow.querySelectorAll('.wb-answer-tile');
    const last = tiles[tiles.length - 1];
    if (last) last.classList.add('wb-tile--just-placed');
  }
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

/* ── Drag-and-drop handlers ────────────────────────────────────── */

function _wbDragStart(e, id, fromAnswer) {
  _wbDragId = id;
  _wbDragFromAnswer = fromAnswer;
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', String(id));
  requestAnimationFrame(() => { if (e.target) e.target.classList.add('wb-tile--dragging'); });
}

function _wbDragEnd(e) {
  if (e.target) e.target.classList.remove('wb-tile--dragging');
}

function _wbDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
}

function _wbDragEnter(e, zone) {
  e.preventDefault();
  zone.classList.add('wb-drop-active');
}

function _wbDragLeave(e, zone) {
  if (!zone.contains(e.relatedTarget)) {
    zone.classList.remove('wb-drop-active');
  }
}

function _wbDrop(e, toPool, zone) {
  e.preventDefault();
  zone.classList.remove('wb-drop-active');
  if (_wbDragId === null) return;
  const id = _wbDragId;
  const fromAnswer = _wbDragFromAnswer;
  _wbDragId = null;
  _wbDragFromAnswer = false;
  if (toPool && fromAnswer) {
    _wbReturnTile(id);
  } else if (!toPool && !fromAnswer) {
    _wbPlaceTile(id);
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
    const pts = _wbCalcScore(_wb.current.tiles.length, _wb.streak);  // Fix #26
    const prevScore = _wb.score;
    _wb.score += pts;
    if (typeof _arcadeCheckMilestone === 'function') _arcadeCheckMilestone(_wb.milestonesHit, prevScore, _wb.score, _wb.streak);
    _wb.wordHistory.push({ word: _wb.current.word, correct: true, pts });  // Fix #18
    if (answerRow) {
      answerRow.classList.add('wb-answer--correct');
      answerRow.querySelectorAll('.wb-answer-tile').forEach((el, i) => {
        el.style.animationDelay = `${i * 55}ms`;
        el.classList.add('wb-tile--burst');
      });
    }
    if (typeof _arcadeFloatScore === 'function') _arcadeFloatScore(pts);
    if (typeof sfxHit === 'function') sfxHit(_wb.streak);
    if (_wb.streak > 0 && _wb.streak % 5 === 0) {
      if (typeof sfxCombo === 'function') sfxCombo();
      if (typeof _arcadeShowCombo === 'function') _arcadeShowCombo(_wb.streak);
    }
    _wbUpdateHUD();
    if (typeof _arcadeScorePop === 'function') _arcadeScorePop(document.getElementById('wb-score'));
    _wbRenderHistory();  // Fix #18
    setTimeout(() => {
      if (!_wb || !_wb.running) return;
      _wbRenderShell();
      _wbNextWord();
      _wbRenderHistory();  // M4: re-render history after shell rebuild (shell wipes arcade-body)
    }, WB_CFG.feedbackMs);
  } else {
    _wb.streak = 0;
    _wb.score = Math.max(0, _wb.score - WB_CFG.wrongPenalty);
    _wb.wordHistory.push({ word: _wb.current.word, correct: false, pts: 0 });  // Fix #18
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
    // QW1: "Almost!" toast if only 1 letter wrong
    if (typeof _arcadeLetterDiff === 'function') {
      const diff = _arcadeLetterDiff(built.toLowerCase(), _wb.current.word.toLowerCase());
      if (diff === 1 && typeof _arcadeFloatScore === 'function') _arcadeFloatScore('Almost!');
    }
    _wbUpdateHUD();
    _wbRenderHistory();  // Fix #18
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

/** Fix #26: centralized score calculation for a solved word. @tag ARCADE */
function _wbCalcScore(wordLen, streak) {
  return Math.round(wordLen * WB_CFG.baseScore * _wbStreakMult(streak));
}

/** Fix #18: render word history panel below the card. @tag ARCADE */
function _wbRenderHistory() {
  const body = document.getElementById('arcade-body');
  if (!body || !_wb || _wb.wordHistory.length === 0) return;
  let panel = document.getElementById('wb-history');
  if (!panel) {
    panel = document.createElement('div');
    panel.id = 'wb-history';
    panel.className = 'wb-history';
    body.querySelector('.wb-view')?.appendChild(panel);
  }
  panel.innerHTML = `<div class="wb-history-title">Recent</div>` +
    _wb.wordHistory.slice(-6).reverse().map((h) =>
      `<div class="wb-history-row ${h.correct ? 'wb-history--ok' : 'wb-history--miss'}">
        <span class="wb-history-word">${h.word}</span>
        <span class="wb-history-pts">${h.correct ? `+${h.pts}` : '—'}</span>
      </div>`
    ).join('');
}

function _wbUpdateHUD() {
  if (!_wb) return;
  const s = document.getElementById('wb-score');
  const st = document.getElementById('wb-streak');
  if (s) s.textContent = String(_wb.score);
  if (st) { st.textContent = String(_wb.streak); if (typeof _arcadeApplyStreakStyle === 'function') _arcadeApplyStreakStyle(st, _wb.streak); }
}

async function _wbGameOver() {
  if (!_wb) return;
  _wb.running = false;
  if (_wb.tickHandle) { clearInterval(_wb.tickHandle); _wb.tickHandle = null; }  // H-1: clear interval
  const state = { ..._wb };  // H-1: snapshot before null
  _wb = null;                 // H-1: null immediately to prevent stale callbacks
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('word_builder', state.score, state.correct, state.total, accuracy, state.level || 'normal');
  _arcadeRenderGameOver({ state, accuracy, result, replayFn: () => wbStart(state.level || 'normal') });
}
