/* ================================================================
   arcade-memory-match.js — Memory Card Match: flip word ↔ definition pairs
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/** Level configs for Memory Card Match. @tag ARCADE */
const MM_LEVELS = {
  easy:  { rows: 4, cols: 4, timeMs: 120_000, pairs: 8,  label: 'Easy',   spec: '8 pairs · 2 min' },
  hard:  { rows: 4, cols: 6, timeMs: 180_000, pairs: 12, label: 'Hard',   spec: '12 pairs · 3 min' },
  xhard: { rows: 5, cols: 6, timeMs: 240_000, pairs: 15, label: 'Expert', spec: '15 pairs · 4 min' },
};

/** Game-wide constants for Memory Card Match. @tag ARCADE */
const MM_CFG = {
  flipCloseMs:     750,  // delay before a non-matching flip closes
  matchPoints:     150,  // points per matched pair
  timeBonusPerSec:   5,  // bonus points per remaining second at completion
  extraFlipPenalty:  5,  // penalty per flip above the theoretical minimum
  defMaxLen:        42,  // characters to show on a definition card
};

let _mm = null;

/** L-4: Fisher-Yates shuffle — unbiased, in-place. Returns same array. @tag ARCADE */
function _mmShuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

/* ── Level picker ──────────────────────────────────────────────── */

/** Show level picker for Memory Card Match. @tag ARCADE */
async function mmShowLevelPicker() {
  mmStop();  // W3: stop any running game before showing picker
  const body = document.getElementById('arcade-body');
  if (!body) return;
  // W4: show per-level best scores (same pattern as suShowLevelPicker)
  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Memory Card Match</h2>
      <p class="wi-level-sub">Flip cards to match each word with its definition.</p>
      <div class="wi-level-list" id="mm-level-list" style="grid-template-columns: repeat(3,1fr); max-width:540px;">Loading…</div>
      <div class="arcade-how-to-play">
        <div class="arcade-htp-title">How to play</div>
        <ul class="arcade-htp-list">
          <li>Flip two cards at a time — match each word with its definition.</li>
          <li>Matched pairs stay face-up; unmatched pairs flip back over.</li>
          <li>Find all pairs before time runs out to win.</li>
          <li>Fewer flips = higher score; a time bonus is added on completion.</li>
        </ul>
      </div>
      <button type="button" class="wi-btn secondary" style="margin-top:12px"
              onclick="arcadeReturnToLobby()">Back</button>
    </div>`;
  const levels = [
    { key: 'easy',  icon: '4×4', name: 'Easy',   spec: '8 pairs · 2 min' },
    { key: 'hard',  icon: '4×6', name: 'Hard',   spec: '12 pairs · 3 min' },
    { key: 'xhard', icon: '5×6', name: 'Expert', spec: '15 pairs · 4 min' },
  ];
  const bests = await Promise.all(
    levels.map((lv) =>
      fetch(`/api/arcade/best/memory_match?level=${lv.key}`)
        .then((r) => r.ok ? r.json() : { score: 0 })
        .catch(() => ({ score: 0 }))
    )
  );
  const list = document.getElementById('mm-level-list');
  if (!list) return;
  list.innerHTML = levels.map((lv, i) => `
    <div class="wi-level-card" onclick="mmStart('${lv.key}')">
      <div class="wi-level-icon wi-level-icon--${lv.key}">${lv.icon}</div>
      <div class="wi-level-name">${lv.name}</div>
      <div class="wi-level-spec">${lv.spec}</div>
      <div class="wi-level-pb">Best: ${bests[i].score || 0}</div>
    </div>`).join('');
}

/* ── Game start / stop ─────────────────────────────────────────── */

/** Start a Memory Card Match round. @tag ARCADE */
async function mmStart(level = 'easy') {
  mmStop();
  const cfg = MM_LEVELS[level] || MM_LEVELS.easy;
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `<div class="mm-loading">Loading cards…</div>`;

  const allWords = await _arcadeFetchWords(80);
  const pool = allWords.filter(
    (w) => w.word && w.definition && /^[a-zA-Z\s''-]+$/.test(w.word)
  );

  if (pool.length < cfg.pairs) {
    body.innerHTML = `
      <div class="wi-gameover">
        <h2>Not enough words</h2>
        <div class="stat">Need at least ${cfg.pairs} words in the pool.</div>
        <button class="wi-btn" onclick="arcadeReturnToLobby()">Back</button>
      </div>`;
    return;
  }

  // Pick the required number of word pairs at random
  const picks = _mmShuffle([...pool]).slice(0, cfg.pairs);  // L-4: Fisher-Yates (unbiased)

  // Each pair produces two cards: one 'word' card and one 'def' card
  const cards = [];
  picks.forEach((entry, pairId) => {
    const def = entry.definition.length > MM_CFG.defMaxLen
      ? entry.definition.slice(0, MM_CFG.defMaxLen).trimEnd() + '…'
      : entry.definition;
    cards.push({ pairId, type: 'word', text: entry.word });
    cards.push({ pairId, type: 'def',  text: def });
  });
  // Shuffle
  _mmShuffle(cards);  // L-4: Fisher-Yates (unbiased)

  _mm = {
    level,
    cfg,
    cards,                    // [{pairId, type, text}, ...]
    flipped: [],              // indices of currently face-up, unmatched cards (max 2)
    matched: new Set(),       // pairIds of found pairs
    score: 0,
    flips: 0,
    correct: 0,               // matched pair count
    total: cfg.pairs,
    running: true,
    locked: false,            // prevents clicks while flip-back is pending
    startedAt: performance.now(),
    tickHandle: null,
    milestonesHit: new Set(),
  };

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('memory_match');
  if (typeof sfxStart === 'function') sfxStart();

  _mmRender();
  _mm.tickHandle = setInterval(_mmTick, 500);  // Fix #19: setInterval instead of rAF
}

/** Stop Memory Card Match (called by hub on close/lobby return). @tag ARCADE */
function mmStop() {
  if (_mm) {
    _mm.running = false;
    if (_mm.tickHandle) { clearInterval(_mm.tickHandle); _mm.tickHandle = null; }
  }
  _mm = null;
}

/* ── Rendering ─────────────────────────────────────────────────── */

function _mmRender() {
  const body = document.getElementById('arcade-body');
  if (!body || !_mm) return;
  const { cfg, total } = _mm;
  const timeSec = Math.ceil(cfg.timeMs / 1000);

  body.innerHTML = `
    <div class="mm-view">
      <div class="mm-hud">
        <div class="mm-hud-item"><span class="mm-hud-label">SCORE</span><b id="mm-score">0</b></div>
        <div class="mm-hud-item"><span class="mm-hud-label">TIME</span><b id="mm-time">${timeSec}</b>s</div>
        <div class="mm-hud-item"><span class="mm-hud-label">PAIRS</span><b id="mm-pairs">0</b>/${total}</div>
        <div class="mm-hud-item"><span class="mm-hud-label">FLIPS</span><b id="mm-flips">0</b></div>
      </div>
      <div class="mm-grid" id="mm-grid" style="--mm-cols:${cfg.cols};"></div>
      <button type="button" class="wi-btn secondary mm-quit-btn"
              onclick="arcadeReturnToLobby()">Quit</button>
    </div>`;

  _mmRenderGrid();
}

function _mmRenderGrid() {
  const grid = document.getElementById('mm-grid');
  if (!grid || !_mm) return;
  const { cards, flipped, matched } = _mm;

  grid.innerHTML = cards.map((card, i) => {
    const isFlipped  = flipped.includes(i);
    const isMatched  = matched.has(card.pairId);
    const typeCls    = `mm-card--${card.type}`;
    const stateCls   = isMatched ? 'mm-card--matched' : (isFlipped ? 'mm-card--flipped' : '');
    return `
      <div class="mm-card ${typeCls} ${stateCls}" data-idx="${i}" onclick="_mmFlip(${i})">
        <div class="mm-card-inner">
          <div class="mm-card-back"></div>
          <div class="mm-card-front"><span>${card.text}</span></div>
        </div>
      </div>`;
  }).join('');
}

/* ── Flip logic ────────────────────────────────────────────────── */

/** Handle a card click. @tag ARCADE */
function _mmFlip(idx) {
  if (!_mm || !_mm.running || _mm.locked) return;
  if (_mm.matched.has(_mm.cards[idx].pairId)) return;
  if (_mm.flipped.includes(idx)) return;
  if (_mm.flipped.length >= 2) return;

  _mm.flipped.push(idx);
  _mm.flips += 1;

  // Immediately flip the card in DOM
  const grid = document.getElementById('mm-grid');
  const cardEl = grid?.querySelector(`[data-idx="${idx}"]`);
  if (cardEl) cardEl.classList.add('mm-card--flipped');

  _mmUpdateHUD();

  if (_mm.flipped.length < 2) return; // wait for second card

  // Two cards face-up — check match
  const [a, b] = _mm.flipped;
  const cA = _mm.cards[a];
  const cB = _mm.cards[b];

  if (cA.pairId === cB.pairId) {
    // Matched pair
    _mm.matched.add(cA.pairId);
    _mm.correct += 1;
    _mm.flipped = [];

    if (grid) {
      [a, b].forEach((i) => {
        const el = grid.querySelector(`[data-idx="${i}"]`);
        if (el) {
          el.classList.remove('mm-card--flipped');
          el.classList.add('mm-card--matched');
        }
      });
    }

    if (typeof sfxHit === 'function') sfxHit(_mm.correct);
    if (_mm.correct > 0 && _mm.correct % 4 === 0 && typeof sfxCombo === 'function') sfxCombo();

    const prevScore = _mm.score;
    _mmUpdateScore();
    _mmUpdateHUD();
    if (typeof _arcadeCheckMilestone === 'function') _arcadeCheckMilestone(_mm.milestonesHit, prevScore, _mm.score, 0);

    if (_mm.matched.size === _mm.total) {
      setTimeout(() => _mmComplete(), 400);
    }
  } else {
    // Not a match — lock board and flip back after delay
    _mm.locked = true;
    setTimeout(() => {
      if (!_mm) return;
      const g = document.getElementById('mm-grid');
      if (g) {
        [a, b].forEach((i) => {
          const el = g.querySelector(`[data-idx="${i}"]`);
          if (el) el.classList.remove('mm-card--flipped');
        });
      }
      _mm.flipped = [];
      _mm.locked = false;
      if (typeof sfxMiss === 'function') sfxMiss();
    }, MM_CFG.flipCloseMs);
  }
}

/* ── Score / HUD helpers ───────────────────────────────────────── */

function _mmUpdateScore() {
  if (!_mm) return;
  // Fix #12: live score = base only (no time bonus) — prevents visible score decreasing
  const minFlips  = _mm.correct * 2;                            // perfect = 2 per pair
  const extra     = Math.max(0, _mm.flips - minFlips);
  _mm.score = Math.max(0,
    _mm.correct * MM_CFG.matchPoints -
    extra * MM_CFG.extraFlipPenalty
  );
}

function _mmFinalScore() {
  // Fix #12: add time bonus only at game-end (complete or time-up)
  if (!_mm) return 0;  // L-3: simplified null guard
  const elapsed  = performance.now() - _mm.startedAt;
  const remainMs = Math.max(0, _mm.cfg.timeMs - elapsed);
  const remSec   = remainMs / 1000;
  return Math.max(0, _mm.score + Math.round(remSec * MM_CFG.timeBonusPerSec));
}

function _mmUpdateHUD() {
  if (!_mm) return;
  const s = document.getElementById('mm-score');
  const p = document.getElementById('mm-pairs');
  const f = document.getElementById('mm-flips');
  if (s) s.textContent = String(_mm.score);
  if (p) p.textContent = String(_mm.correct);
  if (f) f.textContent = String(_mm.flips);
}

/* ── Tick / timer ──────────────────────────────────────────────── */

// Fix #19: setInterval-based tick (500ms) — no rAF waste when board is idle
function _mmTick() {
  if (!_mm || !_mm.running) return;
  if (document.hidden) return;  // skip hidden tab ticks

  const elapsed = performance.now() - _mm.startedAt;
  const remain  = Math.max(0, _mm.cfg.timeMs - elapsed);
  const el      = document.getElementById('mm-time');
  if (el) {
    el.textContent = String(Math.ceil(remain / 1000));
    el.style.color = remain <= 20_000 ? 'var(--color-error)' : '';
  }
  _mmUpdateScore();
  _mmUpdateHUD();

  if (remain <= 0) {
    if (_mm.tickHandle) { clearInterval(_mm.tickHandle); _mm.tickHandle = null; }
    _mmGameOver();
  }
}

/* ── Game-over screens ─────────────────────────────────────────── */

/** All pairs found — player won. @tag ARCADE */
async function _mmComplete() {
  if (!_mm) return;
  _mmUpdateScore();
  const finalScore = _mmFinalScore();   // Fix #12: apply time bonus at completion only
  _mm.score = finalScore;
  _mm.running = false;
  const snap = { score: _mm.score, correct: _mm.correct, total: _mm.total, level: _mm.level, flips: _mm.flips };
  _mm = null;  // M-5: null immediately to prevent stale callbacks / double-call from tick
  const accuracy = snap.correct / snap.total;
  const result   = await _arcadeReportScore('memory_match', snap.score, snap.correct, snap.total, accuracy, snap.level);
  _arcadeRenderGameOver({ state: snap, accuracy, result, replayFn: () => mmStart(snap.level) });
}

/** Time ran out. @tag ARCADE */
async function _mmGameOver() {
  if (!_mm) return;
  _mmUpdateScore();
  // Fix #12: no time bonus on timeout (time already 0)
  _mm.running = false;
  const snap = { score: _mm.score, correct: _mm.correct, total: _mm.total, level: _mm.level, flips: _mm.flips };
  _mm = null;  // M-5: null immediately to prevent stale callbacks
  const accuracy = snap.total > 0 ? snap.correct / snap.total : 0;
  const result   = await _arcadeReportScore('memory_match', snap.score, snap.correct, snap.total, accuracy, snap.level);
  _arcadeRenderGameOver({ state: snap, accuracy, result, replayFn: () => mmStart(snap.level) });
}
