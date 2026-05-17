/* ================================================================
   arcade-sudoku.js — 4×4 / 6×6 / 9×9 sudoku
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const SU_LEVELS = {
  easy:    { label: '4×4', N: 4, br: 2, bc: 2, holes: 6,  baseScore: 1500, timeBonus: 4 },
  medium:  { label: '6×6', N: 6, br: 2, bc: 3, holes: 18, baseScore: 2500, timeBonus: 3 },
  hard:    { label: '9×9', N: 9, br: 3, bc: 3, holes: 40, baseScore: 4000, timeBonus: 2 },
};

let _su = null;
let _suLevel = 'easy';

/** Show picker. @tag ARCADE */
async function suShowLevelPicker() {
  suStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;
  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Size</h2>
      <div class="wi-level-sub">Sudoku</div>
      <div class="wi-level-list" id="su-level-list">Loading…</div>
      <div class="arcade-how-to-play">
        <div class="arcade-htp-title">How to play</div>
        <ul class="arcade-htp-list">
          <li>Fill every row, column, and box with each number exactly once.</li>
          <li>Click a blank cell, then type a number (or use the on-screen pad).</li>
          <li>Use Arrow keys to move between cells.</li>
          <li>Green = correct · Red = conflict — fix red cells to continue.</li>
          <li>Finish faster for a higher time bonus!</li>
        </ul>
      </div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;
  const bests = await Promise.all(
    Object.keys(SU_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/sudoku?level=${lv}`).then((r) => r.ok ? r.json() : { score: 0 }).catch(() => ({ score: 0 }))
    )
  );
  const list = document.getElementById('su-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(SU_LEVELS).map(([key, cfg], i) => `
    <div class="wi-level-card" onclick="suStart('${key}')">
      <div class="wi-level-icon wi-level-icon--${key}">${key[0].toUpperCase()}</div>
      <div class="wi-level-name">${cfg.label}</div>
      <div class="wi-level-spec">${cfg.holes} blanks</div>
      <div class="wi-level-pb">Best: ${bests[i].score || 0}</div>
    </div>`).join('');
}

/** Start sudoku. @tag ARCADE */
function suStart(level = 'easy') {
  suStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;
  _suLevel = SU_LEVELS[level] ? level : 'easy';
  const lv = SU_LEVELS[_suLevel];

  const solution = _suGenSolved(lv);
  const puzzle = _suMakePuzzle(solution, lv.holes);

  _su = {
    solution, puzzle,
    input: puzzle.map((row) => row.slice()),
    lv, startedAt: performance.now(),
    running: true, mistakes: 0, wrongCells: new Set(), completed: false,
    hints: 0, tickHandle: null,
  };

  _suRender();
  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('sudoku');
  _su.tickHandle = setInterval(_suTick, 1000);
  if (typeof sfxStart === 'function') sfxStart();
}

/** Stop. @tag ARCADE */
function suStop() {
  if (!_su) return;
  _su.running = false;
  if (_su.tickHandle) clearInterval(_su.tickHandle);
  _su = null;
}

/* ── Generator ───────────────────────────────────────────────── */

function _suGenSolved(lv) {
  const { N } = lv;
  const grid = Array.from({ length: N }, () => Array(N).fill(0));
  _suFill(grid, 0, lv);
  return grid;
}

function _suFill(grid, idx, lv) {
  const { N } = lv;
  if (idx >= N * N) return true;
  const r = Math.floor(idx / N), c = idx % N;
  const nums = _shuffle(Array.from({ length: N }, (_, i) => i + 1));
  for (const n of nums) {
    if (_suCanPlace(grid, r, c, n, lv)) {
      grid[r][c] = n;
      if (_suFill(grid, idx + 1, lv)) return true;
      grid[r][c] = 0;
    }
  }
  return false;
}

function _suCanPlace(grid, r, c, n, lv) {
  const { N, br, bc } = lv;
  for (let i = 0; i < N; i++) {
    if (grid[r][i] === n) return false;
    if (grid[i][c] === n) return false;
  }
  const br0 = Math.floor(r / br) * br;
  const bc0 = Math.floor(c / bc) * bc;
  for (let i = 0; i < br; i++)
    for (let j = 0; j < bc; j++)
      if (grid[br0 + i][bc0 + j] === n) return false;
  return true;
}

function _shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function _suMakePuzzle(solution, holes) {
  const N = solution.length;
  const puz = solution.map((row) => row.slice());
  const cells = [];
  for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) cells.push([r, c]);
  _shuffle(cells);
  for (let i = 0; i < Math.min(holes, cells.length); i++) {
    const [r, c] = cells[i];
    puz[r][c] = 0;
  }
  return puz;
}

/* ── Render ──────────────────────────────────────────────────── */

function _suRender() {
  const body = document.getElementById('arcade-body');
  if (!body || !_su) return;
  const { N, br, bc } = _su.lv;

  const rows = [];
  for (let r = 0; r < N; r++) {
    const cells = [];
    for (let c = 0; c < N; c++) {
      const given = _su.puzzle[r][c] !== 0;
      const val = _su.input[r][c] || '';
      const borderR = (c + 1) % bc === 0 && c !== N - 1 ? ' su-border-r' : '';
      const borderB = (r + 1) % br === 0 && r !== N - 1 ? ' su-border-b' : '';
      if (given) {
        cells.push(`<div class="su-cell su-cell--given${borderR}${borderB}" data-r="${r}" data-c="${c}">${val}</div>`);  // M-6: add data-r/data-c for peer highlighting
      } else {
        cells.push(`<input class="su-cell su-inp${borderR}${borderB}" maxlength="1" inputmode="numeric"
          data-r="${r}" data-c="${c}" value="${val || ''}">`);
      }
    }
    rows.push(cells.join(''));
  }

  body.innerHTML = `
    <div class="su-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SIZE</span><b>${_su.lv.label}</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">TIME</span><b id="su-time">0</b>s</div>
        <div class="wi-hud-item"><span class="wi-hud-label">MISS</span><b id="su-miss">0</b></div>
        <button type="button" class="wi-btn secondary" id="su-hint-btn" onclick="_suHint()">Hint (3)</button>
        <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Quit</button>
      </div>
      <div class="su-grid" style="grid-template-columns:repeat(${N},var(--su-cell,40px))">
        ${rows.join('')}
      </div>
      <div class="su-hint">Fill each row, column, and box (${br}×${bc}) with 1–${N}.</div>
    </div>`;

  body.querySelectorAll('.su-inp').forEach((el) => {
    el.addEventListener('input', _suOnInput);
    el.addEventListener('keydown', _suOnKey);
    el.addEventListener('focus', _suOnFocus);
    el.addEventListener('blur', _suOnBlur);
  });
  const first = body.querySelector('.su-inp');
  if (first) first.focus();
}

function _suTick() {
  if (!_su || !_su.running) return;
  const sec = Math.floor((performance.now() - _su.startedAt) / 1000);
  const t = document.getElementById('su-time');
  if (t) t.textContent = String(sec);
}

function _suOnInput(e) {
  if (!_su || !_su.running) return;
  const r = Number(e.target.dataset.r), c = Number(e.target.dataset.c);
  const { N } = _su.lv;
  const raw = (e.target.value || '').replace(/[^0-9]/g, '').slice(-1);
  const n = Number(raw);
  if (!raw || n < 1 || n > N) {
    e.target.value = '';
    _su.input[r][c] = 0;
    e.target.classList.remove('su-inp--ok', 'su-inp--bad');
    _suClearConflicts();
    return;
  }
  e.target.value = String(n);
  // Constraint-based validation: temporarily clear cell then check
  _su.input[r][c] = 0;
  const valid = _suCanPlace(_su.input, r, c, n, _su.lv);
  _su.input[r][c] = n;
  if (valid) {
    e.target.classList.remove('su-inp--bad');
    e.target.classList.add('su-inp--ok');
    _suClearConflicts();
    if (typeof sfxHit === 'function') sfxHit(1);
    if (typeof _arcadeFloatScore === 'function') _arcadeFloatScore(10);
  } else {
    e.target.classList.remove('su-inp--ok');
    e.target.classList.add('su-inp--bad');
    // W2: track unique wrong cells (Set) — repeated wrong inputs in the same cell count once
    _su.wrongCells.add(`${r},${c}`);
    _su.mistakes = _su.wrongCells.size;
    const m = document.getElementById('su-miss');
    if (m) m.textContent = String(_su.mistakes);
    _suHighlightConflicts(r, c, n);  // Fix #17: highlight conflicting peers
    if (typeof sfxMiss === 'function') sfxMiss();
  }
  _suCheckComplete();
}

/** Highlight peers that conflict with value n at (r,c). @tag ARCADE */
function _suHighlightConflicts(r, c, n) {
  _suClearConflicts();
  const { br, bc } = _su.lv;
  const boxR = Math.floor(r / br) * br;
  const boxC = Math.floor(c / bc) * bc;
  document.querySelectorAll('.su-cell, .su-inp').forEach((el) => {
    if (el.dataset.r === undefined) return;
    const er = Number(el.dataset.r), ec = Number(el.dataset.c);
    if (er === r && ec === c) return;
    const inRow = er === r, inCol = ec === c;
    const inBox = er >= boxR && er < boxR + br && ec >= boxC && ec < boxC + bc;
    if ((inRow || inCol || inBox) && _su.input[er][ec] === n) {
      el.classList.add('su-cell--conflict');
    }
  });
}

function _suClearConflicts() {
  document.querySelectorAll('.su-cell--conflict')
    .forEach((el) => el.classList.remove('su-cell--conflict'));
}

function _suOnKey(e) {
  if (!_su) return;
  const r = Number(e.target.dataset.r), c = Number(e.target.dataset.c);
  const { N } = _su.lv;
  if (e.key === 'ArrowRight') _suFocus(r, Math.min(N - 1, c + 1));
  else if (e.key === 'ArrowLeft') _suFocus(r, Math.max(0, c - 1));
  else if (e.key === 'ArrowUp') _suFocus(Math.max(0, r - 1), c);
  else if (e.key === 'ArrowDown') _suFocus(Math.min(N - 1, r + 1), c);
  else return;
  e.preventDefault();
}

function _suFocus(r, c) {
  const el = document.querySelector(`.su-inp[data-r="${r}"][data-c="${c}"]`);
  if (el) el.focus();
}

function _suOnFocus(e) {
  if (!_su) return;
  const r = Number(e.target.dataset.r), c = Number(e.target.dataset.c);
  const { N, br, bc } = _su.lv;
  const boxR = Math.floor(r / br) * br, boxC = Math.floor(c / bc) * bc;
  const focusVal = _su.input[r][c];
  document.querySelectorAll('.su-cell, .su-inp').forEach((el) => {
    const er = Number(el.dataset.r), ec = Number(el.dataset.c);
    if (isNaN(er) || isNaN(ec)) return;  // M-6: guard against elements missing data-r/data-c
    const peer = er === r || ec === c ||
      (er >= boxR && er < boxR + br && ec >= boxC && ec < boxC + bc);
    el.classList.toggle('su-cell--peer', peer && el !== e.target);
    const elVal = _su.input[er][ec];
    el.classList.toggle('su-cell--same', !peer && el !== e.target && focusVal !== 0 && elVal === focusVal);
  });
}

function _suOnBlur() {
  document.querySelectorAll('.su-cell--peer, .su-cell--same').forEach((el) => {
    el.classList.remove('su-cell--peer', 'su-cell--same');
  });
}

/** Reveal one correct cell (prefer wrong cells; max 3 hints; -200 pts each). @tag ARCADE */
function _suHint() {
  if (!_su || !_su.running) return;
  if (_su.hints >= 3) return;
  const { N } = _su.lv;

  // Prefer incorrectly filled cells; fall back to empty cells
  const bad = [], empty = [];
  for (let r = 0; r < N; r++) {
    for (let c = 0; c < N; c++) {
      if (_su.puzzle[r][c] !== 0) continue;
      if (_su.input[r][c] === 0) empty.push([r, c]);
      else if (_su.input[r][c] !== _su.solution[r][c]) bad.push([r, c]);
    }
  }
  const pool = bad.length > 0 ? bad : empty;
  if (pool.length === 0) return;

  const [r, c] = pool[Math.floor(Math.random() * pool.length)];
  const correct = _su.solution[r][c];
  _su.input[r][c] = correct;
  _su.hints += 1;

  const el = document.querySelector(`.su-inp[data-r="${r}"][data-c="${c}"]`);
  if (el) {
    el.value = String(correct);
    el.classList.remove('su-inp--ok', 'su-inp--bad');
    el.classList.add('su-inp--hint');
    el.readOnly = true;
  }
  _suClearConflicts();

  const btn = document.getElementById('su-hint-btn');
  const left = 3 - _su.hints;
  if (btn) {
    btn.textContent = left > 0 ? `Hint (${left})` : 'No hints left';
    if (left <= 0) btn.disabled = true;
  }

  if (typeof sfxHit === 'function') sfxHit(1);
  _suCheckComplete();
}

function _suCheckComplete() {
  const { N } = _su.lv;
  // All cells must be filled
  for (let r = 0; r < N; r++)
    for (let c = 0; c < N; c++)
      if (!_su.input[r][c]) return;
  // Validate by constraint check, not by comparing to the stored solution.
  // This intentionally accepts any valid alternative solution: the simple
  // backtracking generator (_suGenSolved) does not guarantee a unique
  // solution for all hole counts, so constraint-validity is the correct
  // acceptance criterion.
  for (let r = 0; r < N; r++) {
    for (let c = 0; c < N; c++) {
      const n = _su.input[r][c];
      _su.input[r][c] = 0;
      const ok = _suCanPlace(_su.input, r, c, n, _su.lv);
      _su.input[r][c] = n;
      if (!ok) return;
    }
  }
  _su.completed = true;
  setTimeout(_suFinish, 200);
}

async function _suFinish() {
  if (!_su) return;
  _su.running = false;
  if (_su.tickHandle) { clearInterval(_su.tickHandle); _su.tickHandle = null; }
  const state = { ..._su, wrongCells: new Set(_su.wrongCells) };  // M-3: snapshot (clone Set) before null
  _su = null;                                                       // M-3: null immediately

  const seconds = Math.floor((performance.now() - state.startedAt) / 1000);
  // W2: use wrongCells.size (unique cells, bounded by holes) instead of raw mistakes counter
  const uniqueWrong = Math.min(state.wrongCells.size, state.lv.holes);
  const timePenalty = seconds * state.lv.timeBonus;
  const missPenalty = uniqueWrong * 25;
  const hintPenalty = (state.hints || 0) * 200;
  const score = Math.max(50, state.lv.baseScore - timePenalty - missPenalty - hintPenalty);

  const total = state.lv.holes;
  const correct = total - uniqueWrong;   // always in [0, total]
  const accuracy = total > 0 ? correct / total : 1;

  // B: show "Solved!" first — then report score in background — then transition to game-over
  const body = document.getElementById('arcade-body');
  if (body) {
    const hintsUsed = state.hints || 0;
    body.innerHTML = `
      <div class="su-finish">
        <h2>Solved!</h2>
        <div class="stat">Time: <b>${seconds}s</b></div>
        <div class="stat">Mistakes: <b>${uniqueWrong}</b></div>
        ${hintsUsed > 0 ? `<div class="stat su-finish--hint">Hints used: <b>${hintsUsed}</b> (−${hintsUsed * 200} pts)</div>` : ''}
      </div>`;
  }
  const result = await _arcadeReportScore('sudoku', score, correct, total, accuracy, _suLevel);
  setTimeout(() => {
    _arcadeRenderGameOver({
      state: { score, correct, total },
      accuracy, result, replayFn: () => suStart(_suLevel),
    });
  }, 1500);  // B: give player 1.5s to see the Solved screen before game-over panel
}
