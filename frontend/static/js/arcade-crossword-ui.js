/* ================================================================
   arcade-crossword-ui.js — Crossword rendering, input, HUD, hint, finish
   Section: Arcade
   Dependencies: arcade-crossword.js (_cw, CW_CFG, cwStart), arcade.js, core.js
   API endpoints: POST /api/arcade/score (via _arcadeReportScore)
   ================================================================ */

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
    .map((p) => `<li data-idx="${p.idx}"><b>${p.num}.</b> ${_cwEscape(p.def)} <span class="cw-len">(${p.len})</span></li>`)
    .join('');
  const downClues = _cw.placed.filter((p) => p.dir === 'V')
    .map((p) => `<li data-idx="${p.idx}"><b>${p.num}.</b> ${_cwEscape(p.def)} <span class="cw-len">(${p.len})</span></li>`)
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

function _cwEscape(s) {
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
  if (bar) {
    const wrongCount = _cw.wrongAttempts[_cw.activeWord] || 0;
    const hintBtn = (!p.completed && wrongCount >= CW_CFG.hintThreshold)
      ? `<button class="cw-hint-btn" onclick="_cwHint(${_cw.activeWord})">Hint</button>`
      : '';
    bar.innerHTML = `<b>${p.num} ${p.dir === 'H' ? 'Across' : 'Down'}:</b> ${_cwEscape(p.def)} <span class="cw-len">(${p.len})</span>${hintBtn}`;
  }
}

/** Reveal + lock the first unresolved letter of the active word. @tag ARCADE */
function _cwHint(wordIdx) {
  if (!_cw) return;
  const p = _cw.placed[wordIdx];
  if (!p || p.completed) return;
  // Find first cell that isn't correct yet
  for (let k = 0; k < p.len; k++) {
    const rr = p.r + (p.dir === 'V' ? k : 0);
    const cc = p.c + (p.dir === 'H' ? k : 0);
    const cell = _cw.grid[rr][cc];
    if (cell.input === cell.ans) continue;
    // Reveal this letter
    cell.input = cell.ans;
    const el = document.querySelector(`.cw-inp[data-r="${rr}"][data-c="${cc}"]`);
    if (el) {
      el.value = cell.ans.toUpperCase();
      el.classList.add('cw-inp--ok', 'cw-inp--hint');
      el.disabled = true; // lock the hinted cell
    }
    _cwCheckWord(rr, cc);
    break;
  }
  _cwHighlight();
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
    // Fix #15: track wrong attempts per word
    const cell = _cw.grid[r][c];
    if (ch !== cell.ans) {
      const wordsHere = cell.wordsAt || [];
      if (wordsHere.includes(_cw.activeWord)) {
        _cw.wrongAttempts[_cw.activeWord] = (_cw.wrongAttempts[_cw.activeWord] || 0) + 1;
        _cwHighlight(); // refresh bar to maybe show hint button
      }
    }
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
  if (dir <= 0) { _cwMove(r, c, dr, dc); return; }
  // Forward: skip cells already correctly filled
  let nr = r + dr, nc = c + dc;
  while (nr >= 0 && nr < _cw.rows && nc >= 0 && nc < _cw.cols) {
    const cell = _cw.grid[nr]?.[nc];
    if (!cell) break;
    const inWord = p.dir === 'H'
      ? (nr === p.r && nc >= p.c && nc < p.c + p.len)
      : (nc === p.c && nr >= p.r && nr < p.r + p.len);
    if (inWord && cell.input && cell.input === cell.ans) { nr += dr; nc += dc; continue; }
    const el = document.querySelector(`.cw-inp[data-r="${nr}"][data-c="${nc}"]`);
    if (el && !el.disabled) el.focus();
    return;
  }
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
      const cwGained = CW_CFG.pointsPerWord + p.len * CW_CFG.pointsPerLetter;
      _cw.score += cwGained;
      if (typeof _arcadeFloatScore === 'function') _arcadeFloatScore(cwGained);
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
        _cwCelebrate();
        setTimeout(_cwFinish, 1200);
      }
    }
  });
}

function _cwCelebrate() {
  const view = document.querySelector('.cw-view');
  if (!view) return;
  const overlay = document.createElement('div');
  overlay.className = 'cw-celebrate';
  overlay.textContent = 'Puzzle Complete!';
  view.appendChild(overlay);
  if (typeof sfxHit === 'function') sfxHit(10);
}

function _cwUpdateHUD() {
  const s = document.getElementById('cw-score');
  const w = document.getElementById('cw-words');
  if (s) s.textContent = String(_cw.score);
  if (w) w.textContent = String(_cw.completed);
}

async function _cwFinish() {
  if (!_cw) return;
  _cw.running = false;
  const state = { ..._cw };  // M-2: snapshot before null
  _cw = null;                 // M-2: null immediately to prevent stale callbacks
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('crossword', state.score, state.correct, state.total, accuracy, state.level || 'normal');

  const missed = (state.placed || []).filter((p) => !p.completed);
  const extras = missed.length > 0
    ? `<div class="cw-missed">
        <div class="cw-missed-title">Answers (${missed.length} unsolved)</div>
        ${missed.map((p) => `<div class="cw-missed-row"><b>${p.word.toUpperCase()}</b> — ${_cwEscape(p.def)}</div>`).join('')}
      </div>`
    : '';

  _arcadeRenderGameOver({ state, accuracy, result, replayFn: () => cwStart(state.level || 'normal'), extras });
}
