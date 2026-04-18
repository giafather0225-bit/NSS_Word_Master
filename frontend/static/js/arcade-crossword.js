/* ================================================================
   arcade-crossword.js — Crossword: definitions as clues, fill the grid
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const CW_CFG = {
  targetWords: 10,        // try to place up to this many
  minLen: 3,
  maxLen: 10,
  internalSize: 15,       // working grid before crop
  pointsPerWord: 40,      // on word complete
  pointsPerLetter: 8,
  fullBonus: 300,
};

let _cw = null;

/** Start Crossword. @tag ARCADE */
async function cwStart() {
  cwStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `<div class="cw-view"><div class="cw-loading">Generating puzzle…</div></div>`;

  const pool = await _arcadeFetchWords(120);
  const puzzle = _cwGenerate(pool);
  if (!puzzle || puzzle.placed.length < 3) {
    body.innerHTML = `
      <div class="wi-gameover">
        <h2>Not enough words</h2>
        <div class="stat">Need more 3–10 letter words in the pool.</div>
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
    startedAt: performance.now(),
    running: true,
  };

  _cwRender();
}

/** Stop & release listeners. @tag ARCADE */
function cwStop() {
  if (!_cw) return;
  _cw.running = false;
  document.removeEventListener('keydown', _cwGlobalKey);
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

/* ── Render + input ──────────────────────────────────────────── */

function _cwRender() {
  const body = document.getElementById('arcade-body');
  if (!body || !_cw) return;

  const gridHtml = [];
  for (let r = 0; r < _cw.rows; r++) {
    for (let c = 0; c < _cw.cols; c++) {
      const cell = _cw.grid[r][c];
      if (!cell) {
        gridHtml.push(`<div class="cw-cell cw-cell--block"></div>`);
      } else {
        const numBadge = cell.num ? `<span class="cw-num">${cell.num}</span>` : '';
        gridHtml.push(`
          <div class="cw-cell" data-r="${r}" data-c="${c}">
            ${numBadge}
            <input class="cw-inp" maxlength="1" autocomplete="off" spellcheck="false"
                   data-r="${r}" data-c="${c}" value="${cell.input}">
          </div>`);
      }
    }
  }

  const acrossClues = _cw.placed.filter((p) => p.dir === 'H')
    .map((p) => `<li data-idx="${p.idx}"><b>${p.num}.</b> ${_escape(p.def)} <span class="cw-len">(${p.len})</span></li>`)
    .join('');
  const downClues = _cw.placed.filter((p) => p.dir === 'V')
    .map((p) => `<li data-idx="${p.idx}"><b>${p.num}.</b> ${_escape(p.def)} <span class="cw-len">(${p.len})</span></li>`)
    .join('');

  body.innerHTML = `
    <div class="cw-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SCORE</span><b id="cw-score">0</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">WORDS</span><b id="cw-words">0</b>/${_cw.placed.length}</div>
        <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Quit</button>
      </div>
      <div class="cw-play">
        <div class="cw-grid-wrap">
          <div class="cw-grid" style="grid-template-columns:repeat(${_cw.cols},36px)">
            ${gridHtml.join('')}
          </div>
          <div class="cw-active" id="cw-active">Select a cell to see the clue.</div>
        </div>
        <div class="cw-clues">
          <div class="cw-clues-col">
            <h3>Across</h3>
            <ol class="cw-clues-list" id="cw-clues-across">${acrossClues}</ol>
          </div>
          <div class="cw-clues-col">
            <h3>Down</h3>
            <ol class="cw-clues-list" id="cw-clues-down">${downClues}</ol>
          </div>
        </div>
      </div>
    </div>`;

  // Wire inputs
  body.querySelectorAll('.cw-inp').forEach((inp) => {
    inp.addEventListener('input', _cwOnInput);
    inp.addEventListener('keydown', _cwOnKey);
    inp.addEventListener('focus', _cwOnFocus);
  });
  body.querySelectorAll('.cw-clues-list li').forEach((li) => {
    li.addEventListener('click', () => {
      const idx = Number(li.dataset.idx);
      _cwFocusWord(idx);
    });
  });

  if (typeof sfxStart === 'function') sfxStart();

  // Focus first cell
  const first = body.querySelector('.cw-inp');
  if (first) first.focus();
}

function _escape(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function _cwOnFocus(e) {
  if (!_cw) return;
  const r = Number(e.target.dataset.r);
  const c = Number(e.target.dataset.c);
  const cell = _cw.grid[r][c];
  if (!cell) return;
  // Prefer a word that isn't yet completed
  let idx = cell.wordsAt[0];
  for (const wi of cell.wordsAt) {
    if (!_cw.placed[wi].completed) { idx = wi; break; }
  }
  _cw.activeWord = idx;
  _cwHighlight();
}

function _cwFocusWord(idx) {
  if (!_cw) return;
  _cw.activeWord = idx;
  const p = _cw.placed[idx];
  const cell = document.querySelector(`.cw-inp[data-r="${p.r}"][data-c="${p.c}"]`);
  if (cell) cell.focus();
  _cwHighlight();
}

function _cwHighlight() {
  const p = _cw.placed[_cw.activeWord];
  document.querySelectorAll('.cw-cell').forEach((el) => el.classList.remove('cw-cell--active'));
  document.querySelectorAll('.cw-clues-list li').forEach((el) => el.classList.remove('active'));
  for (let k = 0; k < p.len; k++) {
    const rr = p.r + (p.dir === 'V' ? k : 0);
    const cc = p.c + (p.dir === 'H' ? k : 0);
    const el = document.querySelector(`.cw-cell[data-r="${rr}"][data-c="${cc}"]`);
    if (el) el.classList.add('cw-cell--active');
  }
  const clue = document.querySelector(`.cw-clues-list li[data-idx="${_cw.activeWord}"]`);
  if (clue) clue.classList.add('active');
  const bar = document.getElementById('cw-active');
  if (bar) bar.innerHTML = `<b>${p.num} ${p.dir === 'H' ? 'Across' : 'Down'}:</b> ${_escape(p.def)} <span class="cw-len">(${p.len})</span>`;
}

function _cwOnInput(e) {
  if (!_cw) return;
  const r = Number(e.target.dataset.r);
  const c = Number(e.target.dataset.c);
  const ch = (e.target.value || '').toLowerCase().replace(/[^a-z]/g, '').slice(-1);
  e.target.value = ch.toUpperCase();
  _cw.grid[r][c].input = ch;
  _cwValidateCell(r, c, e.target);
  if (ch) {
    _cwAdvance(r, c, +1);
    _cwCheckWord(r, c);
  }
}

function _cwOnKey(e) {
  if (!_cw) return;
  const r = Number(e.target.dataset.r);
  const c = Number(e.target.dataset.c);
  if (e.key === 'Backspace' && !e.target.value) {
    _cwAdvance(r, c, -1);
    e.preventDefault();
  } else if (e.key === 'ArrowRight') { _cwMove(r, c, 0, 1); e.preventDefault(); }
  else if (e.key === 'ArrowLeft')  { _cwMove(r, c, 0, -1); e.preventDefault(); }
  else if (e.key === 'ArrowUp')    { _cwMove(r, c, -1, 0); e.preventDefault(); }
  else if (e.key === 'ArrowDown')  { _cwMove(r, c, 1, 0); e.preventDefault(); }
  else if (e.key === 'Enter') {
    const others = _cw.grid[r][c].wordsAt.filter((i) => i !== _cw.activeWord);
    if (others.length) _cwFocusWord(others[0]);
    e.preventDefault();
  }
}

function _cwValidateCell(r, c, inputEl) {
  const cell = _cw.grid[r][c];
  inputEl.classList.remove('cw-inp--ok', 'cw-inp--bad');
  if (!cell.input) return;
  if (cell.input === cell.ans) inputEl.classList.add('cw-inp--ok');
  else inputEl.classList.add('cw-inp--bad');
}

function _cwAdvance(r, c, dir) {
  const p = _cw.placed[_cw.activeWord];
  const dr = p.dir === 'V' ? dir : 0;
  const dc = p.dir === 'H' ? dir : 0;
  _cwMove(r, c, dr, dc);
}

function _cwMove(r, c, dr, dc) {
  let nr = r + dr, nc = c + dc;
  while (nr >= 0 && nr < _cw.rows && nc >= 0 && nc < _cw.cols) {
    if (_cw.grid[nr][nc]) {
      const el = document.querySelector(`.cw-inp[data-r="${nr}"][data-c="${nc}"]`);
      if (el) el.focus();
      return;
    }
    nr += dr; nc += dc;
  }
}

function _cwCheckWord(r, c) {
  const cell = _cw.grid[r][c];
  cell.wordsAt.forEach((idx) => {
    const p = _cw.placed[idx];
    if (p.completed) return;
    let ok = true;
    for (let k = 0; k < p.len; k++) {
      const rr = p.r + (p.dir === 'V' ? k : 0);
      const cc = p.c + (p.dir === 'H' ? k : 0);
      const cc2 = _cw.grid[rr][cc];
      if (cc2.input !== cc2.ans) { ok = false; break; }
    }
    if (ok) {
      p.completed = true;
      _cw.completed += 1;
      _cw.correct += 1;
      _cw.total += 1;
      _cw.score += CW_CFG.pointsPerWord + p.len * CW_CFG.pointsPerLetter;
      for (let k = 0; k < p.len; k++) {
        const rr = p.r + (p.dir === 'V' ? k : 0);
        const cc = p.c + (p.dir === 'H' ? k : 0);
        const el = document.querySelector(`.cw-cell[data-r="${rr}"][data-c="${cc}"]`);
        if (el) el.classList.add('cw-cell--done');
      }
      const li = document.querySelector(`.cw-clues-list li[data-idx="${idx}"]`);
      if (li) li.classList.add('done');
      if (typeof sfxHit === 'function') sfxHit(_cw.completed);
      _cwUpdateHUD();
      if (_cw.completed === _cw.placed.length) {
        _cw.score += CW_CFG.fullBonus;
        _cwUpdateHUD();
        setTimeout(_cwFinish, 300);
      }
    }
  });
}

function _cwUpdateHUD() {
  const s = document.getElementById('cw-score');
  const w = document.getElementById('cw-words');
  if (s) s.textContent = String(_cw.score);
  if (w) w.textContent = String(_cw.completed);
}

async function _cwFinish() {
  if (!_cw) return;
  const state = _cw;
  _cw.running = false;
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('crossword', state.score, state.correct, state.total, accuracy);
  _arcadeRenderGameOver({ state, accuracy, result, replay: 'cwStart()' });
}

function _cwGlobalKey() { /* reserved */ }
