/* ================================================================
   arcade-crossword.js — Crossword: config, public API, puzzle generator
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   Split: rendering + input handling in arcade-crossword-ui.js
   ================================================================ */

/** @tag ARCADE */
const CW_CFG = {
  targetWords: 10,        // try to place up to this many
  minLen: 3,
  maxLen: 10,
  internalSize: 15,       // working grid before crop
  pointsPerWord: 80,      // on word complete (was 40)
  pointsPerLetter: 15,    // per letter on complete (was 8)
  fullBonus: 500,         // all words done bonus (was 300)
  hintThreshold: 2,       // wrong entries per word before hint appears
};

const CW_LEVELS = {
  easy:   { label: 'Easy',   targetWords:  8, spec: '8 words' },
  normal: { label: 'Normal', targetWords: 10, spec: '10 words' },
  hard:   { label: 'Hard',   targetWords: 12, spec: '12 words' },
};

let _cw = null;

/** Level picker for Crossword. @tag ARCADE */
async function cwShowLevelPicker() {
  cwStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Difficulty</h2>
      <div class="wi-level-sub">Crossword</div>
      <div class="wi-level-list" id="cw-level-list">Loading…</div>
      <div class="arcade-how-to-play">
        <div class="arcade-htp-title">How to play</div>
        <ul class="arcade-htp-list">
          <li>Click a clue or a cell to select a word slot on the grid.</li>
          <li>Type the answer letter by letter — correct letters turn green.</li>
          <li>Fill every slot correctly to complete the puzzle.</li>
          <li>Use the Reveal button for a hint if you get stuck.</li>
        </ul>
      </div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;

  const bests = await Promise.all(
    Object.keys(CW_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/crossword?level=${lv}`)
        .then((r) => (r.ok ? r.json() : { score: 0 }))
        .catch(() => ({ score: 0 }))
    )
  );

  const list = document.getElementById('cw-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(CW_LEVELS)
    .map(([key, cfg], i) => {
      const pb = bests[i].score || 0;
      const pbAcc = bests[i].accuracy || 0;
      return `
        <div class="wi-level-card" onclick="cwStart('${key}')">
          <div class="wi-level-icon wi-level-icon--${key}">${key[0].toUpperCase()}</div>
          <div class="wi-level-name">${cfg.label}</div>
          <div class="wi-level-spec">${cfg.spec}</div>
          <div class="wi-level-pb">Best: ${pb}${_arcadeLevelStarsHTML(pbAcc)}</div>
        </div>`;
    })
    .join('');
}

/** Start Crossword. @tag ARCADE */
async function cwStart(level = 'normal') {
  cwStop();
  const lv = CW_LEVELS[level] || CW_LEVELS.normal;
  CW_CFG.targetWords = lv.targetWords;
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `<div class="cw-view"><div class="cw-loading">Generating puzzle…</div></div>`;

  const pool = await _arcadeFetchWords(120);
  const puzzle = _cwGenerate(pool);
  if (!puzzle || puzzle.placed.length < 4) {
    body.innerHTML = `
      <div class="wi-gameover">
        <h2>Not enough words</h2>
        <div class="stat">Need at least 4 words with 3–10 letters in the pool.</div>
        <button class="wi-btn" onclick="arcadeReturnToLobby()">Back</button>
      </div>`;
    return;
  }

  _cw = {
    grid: puzzle.grid,          // rows × cols, cell: null (block) or {ans, num, wordsAt:[idx], input:''}
    placed: puzzle.placed,      // [{word, def, r, c, dir, num, len, completed:false}]
    rows: puzzle.rows,
    cols: puzzle.cols,
    score: 0,
    correct: 0,
    total: 0,
    completed: 0,
    activeWord: 0,
    wrongAttempts: new Array(puzzle.placed.length).fill(0), // Fix #15: per-word wrong count
    startedAt: performance.now(),
    running: true,
    level,
  };

  _cwRender();
  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('crossword');
}

/** Stop & release listeners. @tag ARCADE */
function cwStop() {
  if (!_cw) return;
  _cw.running = false;
  // E: explicitly remove per-cell listeners to mirror addEventListener calls in _cwRenderGrid
  document.querySelectorAll('.cw-inp').forEach((el) => {
    el.removeEventListener('input', _cwOnInput);
    el.removeEventListener('keydown', _cwOnKey);
    el.removeEventListener('focus', _cwOnFocus);
  });
  _cw = null;
}

/* ── Puzzle generator ────────────────────────────────────────── */

function _cwGenerate(pool) {
  const candidates = pool
    .filter((w) => {
      const s = (w.word || '').toLowerCase();
      return /^[a-z]+$/.test(s) && s.length >= CW_CFG.minLen && s.length <= CW_CFG.maxLen;
    })
    .map((w) => ({ word: w.word.toLowerCase(), def: w.definition }))
    .sort((a, b) => b.word.length - a.word.length);

  if (candidates.length < 4) return null;

  const N = CW_CFG.internalSize;
  const grid = Array.from({ length: N }, () => Array(N).fill(null));
  const placed = [];

  // Place first word horizontally in center
  const first = candidates.shift();
  const r0 = Math.floor(N / 2);
  const c0 = Math.floor((N - first.word.length) / 2);
  _cwPlace(grid, first, r0, c0, 'H', placed);

  for (const cand of candidates) {
    if (placed.length >= CW_CFG.targetWords) break;
    const w = cand.word;
    let best = null;
    for (let i = 0; i < w.length; i++) {
      for (const p of placed) {
        for (let j = 0; j < p.word.length; j++) {
          if (p.word[j] !== w[i]) continue;
          const dir = p.dir === 'H' ? 'V' : 'H';
          let r, c;
          if (dir === 'H') {
            r = p.r + j;
            c = p.c - i;
          } else {
            r = p.r - i;
            c = p.c + j;
          }
          if (_cwCanPlace(grid, w, r, c, dir)) {
            const score = _cwFitScore(grid, w, r, c, dir);
            if (!best || score > best.score) best = { r, c, dir, score };
          }
        }
      }
    }
    if (best) _cwPlace(grid, cand, best.r, best.c, best.dir, placed);
  }

  // Crop bounding box
  let rMin = N, rMax = -1, cMin = N, cMax = -1;
  for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) {
    if (grid[r][c]) {
      if (r < rMin) rMin = r;
      if (r > rMax) rMax = r;
      if (c < cMin) cMin = c;
      if (c > cMax) cMax = c;
    }
  }
  const rows = rMax - rMin + 1;
  const cols = cMax - cMin + 1;
  const out = Array.from({ length: rows }, () => Array(cols).fill(null));
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const src = grid[r + rMin][c + cMin];
    if (src) out[r][c] = { ans: src.ans, input: '' };
  }
  placed.forEach((p) => { p.r -= rMin; p.c -= cMin; });

  // Assign clue numbers and tag words to cells
  let num = 1;
  placed.sort((a, b) => (a.r - b.r) || (a.c - b.c));
  const numAt = new Map();
  placed.forEach((p, idx) => {
    const key = `${p.r},${p.c}`;
    if (!numAt.has(key)) numAt.set(key, num++);
    p.num = numAt.get(key);
    p.idx = idx;
    p.len = p.word.length;
    p.completed = false;
    for (let k = 0; k < p.word.length; k++) {
      const rr = p.r + (p.dir === 'V' ? k : 0);
      const cc = p.c + (p.dir === 'H' ? k : 0);
      const cell = out[rr][cc];
      if (!cell.num && numAt.has(`${rr},${cc}`)) cell.num = numAt.get(`${rr},${cc}`);
      cell.wordsAt = cell.wordsAt || [];
      if (!cell.wordsAt.includes(idx)) cell.wordsAt.push(idx);
    }
  });

  return { grid: out, placed, rows, cols };
}

function _cwPlace(grid, cand, r, c, dir, placed) {
  const w = cand.word;
  for (let k = 0; k < w.length; k++) {
    const rr = r + (dir === 'V' ? k : 0);
    const cc = c + (dir === 'H' ? k : 0);
    grid[rr][cc] = { ans: w[k] };
  }
  placed.push({ word: w, def: cand.def, r, c, dir });
}

function _cwCanPlace(grid, w, r, c, dir) {
  const N = grid.length;
  const dr = dir === 'V' ? 1 : 0;
  const dc = dir === 'H' ? 1 : 0;
  // Out of bounds
  const endR = r + dr * (w.length - 1);
  const endC = c + dc * (w.length - 1);
  if (r < 0 || c < 0 || endR >= N || endC >= N) return false;
  // Before/after must be empty or edge
  const beforeR = r - dr, beforeC = c - dc;
  const afterR = endR + dr, afterC = endC + dc;
  if (beforeR >= 0 && beforeC >= 0 && grid[beforeR][beforeC]) return false;
  if (afterR < N && afterC < N && grid[afterR][afterC]) return false;

  let intersections = 0;
  for (let k = 0; k < w.length; k++) {
    const rr = r + dr * k;
    const cc = c + dc * k;
    const cell = grid[rr][cc];
    if (cell) {
      if (cell.ans !== w[k]) return false;
      intersections += 1;
    } else {
      // Perpendicular neighbors must be empty to avoid kissing parallel words
      if (dir === 'H') {
        if (rr - 1 >= 0 && grid[rr - 1][cc]) return false;
        if (rr + 1 < N && grid[rr + 1][cc]) return false;
      } else {
        if (cc - 1 >= 0 && grid[rr][cc - 1]) return false;
        if (cc + 1 < N && grid[rr][cc + 1]) return false;
      }
    }
  }
  return intersections >= 1;
}

function _cwFitScore(grid, w, r, c, dir) {
  let s = 0;
  const dr = dir === 'V' ? 1 : 0;
  const dc = dir === 'H' ? 1 : 0;
  for (let k = 0; k < w.length; k++) {
    if (grid[r + dr * k][c + dc * k]) s += 2;
  }
  return s;
}

// Rendering, input handling, HUD, hint, and game-over split into arcade-crossword-ui.js
