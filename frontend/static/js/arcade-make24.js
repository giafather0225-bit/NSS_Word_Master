/* ================================================================
   arcade-make24.js — Combine 4 numbers to reach 24
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const MK_CFG = {
  roundMs: 90000,
  target: 24,
  solvePoints: 120,
  streakBonus: 20,
  streakCap: 8,
  skipPenalty: 40,
};

/** @tag ARCADE */
const MK_LEVELS = {
  easy:   { label: 'Easy',   ops: ['+', '-'],             target: 20, numbersMin: 1, numbersMax: 9 },
  normal: { label: 'Normal', ops: ['+', '-', '*', '/'],   target: 24, numbersMin: 1, numbersMax: 9 },
};

let _mk = null;
let _mkLevel = 'normal';

/** Show Make 24 level picker. @tag ARCADE */
async function mkShowLevelPicker() {
  mkStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;
  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Difficulty</h2>
      <div class="wi-level-sub">Make 24</div>
      <div class="wi-level-list" id="mk-level-list">Loading…</div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;
  const bests = await Promise.all(
    Object.keys(MK_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/make24?level=${lv}`).then((r) => r.ok ? r.json() : { score: 0 }).catch(() => ({ score: 0 }))
    )
  );
  const list = document.getElementById('mk-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(MK_LEVELS).map(([key, cfg], i) => `
    <div class="wi-level-card" onclick="mkStart('${key}')">
      <div class="wi-level-icon wi-level-icon--${key}">${key[0].toUpperCase()}</div>
      <div class="wi-level-name">${cfg.label}</div>
      <div class="wi-level-spec">${cfg.ops.join(' ')} · target ${cfg.target}</div>
      <div class="wi-level-pb">Best: ${bests[i].score || 0}</div>
    </div>`).join('');
}

/** Start Make 24. @tag ARCADE */
function mkStart(level = 'normal') {
  mkStop();
  _mkLevel = MK_LEVELS[level] ? level : 'normal';
  const lv = MK_LEVELS[_mkLevel];
  const body = document.getElementById('arcade-body');
  if (!body) return;

  _mk = {
    score: 0, streak: 0, correct: 0, total: 0,
    startedAt: performance.now(), running: true,
    current: null, expr: [],
  };

  body.innerHTML = `
    <div class="mk-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SCORE</span><b id="mk-score">0</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">TIME</span><b id="mk-time">90</b>s</div>
        <div class="wi-hud-item"><span class="wi-hud-label">STREAK</span><b id="mk-streak">0</b></div>
      </div>
      <div class="mk-stage">
        <div class="mk-target">Make <b>${lv.target}</b></div>
        <div class="mk-nums" id="mk-nums"></div>
        <div class="mk-expr" id="mk-expr">—</div>
        <div class="mk-preview" id="mk-preview"></div>
        <div class="mk-ops">
          <button type="button" class="mk-op" data-op="(">(</button>
          <button type="button" class="mk-op" data-op=")">)</button>
          <button type="button" class="mk-op" data-op="+">+</button>
          <button type="button" class="mk-op" data-op="-">−</button>
          ${lv.ops.includes('*') ? '<button type="button" class="mk-op" data-op="*">×</button>' : ''}
          ${lv.ops.includes('/') ? '<button type="button" class="mk-op" data-op="/">÷</button>' : ''}
        </div>
        <div class="mk-actions">
          <button type="button" class="wi-btn" id="mk-undo">↶ Undo</button>
          <button type="button" class="wi-btn" id="mk-clear">Clear</button>
          <button type="button" class="wi-btn" id="mk-submit">Submit</button>
          <button type="button" class="wi-btn secondary" id="mk-skip">Skip (−${MK_CFG.skipPenalty})</button>
        </div>
        <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Quit</button>
      </div>
    </div>`;

  document.getElementById('mk-undo').addEventListener('click', _mkUndo);
  document.getElementById('mk-clear').addEventListener('click', _mkClear);
  document.getElementById('mk-submit').addEventListener('click', _mkSubmit);
  document.getElementById('mk-skip').addEventListener('click', _mkSkip);
  document.querySelectorAll('.mk-op').forEach((b) => b.addEventListener('click', () => _mkPush({ kind: 'op', v: b.dataset.op })));

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('make24');

  if (typeof sfxStart === 'function') sfxStart();
  _mkNextHand();
  _mkTick();
}

/** Stop. @tag ARCADE */
function mkStop() {
  if (_mk) _mk.running = false;
  _mk = null;
}

function _mkTick() {
  if (!_mk || !_mk.running) return;
  if (document.hidden) { requestAnimationFrame(_mkTick); return; }
  const remain = Math.max(0, MK_CFG.roundMs - (performance.now() - _mk.startedAt));
  const el = document.getElementById('mk-time');
  if (el) el.textContent = String(Math.ceil(remain / 1000));
  if (remain <= 0) { _mkGameOver(); return; }
  requestAnimationFrame(_mkTick);
}

function _mkNextHand() {
  if (!_mk) return;
  _mk.current = _mkGenSolvable();
  _mk.expr = [];
  _mkRender();
}

function _mkRender() {
  const nums = document.getElementById('mk-nums');
  if (!nums || !_mk) return;
  nums.innerHTML = _mk.current.map((n, i) => {
    const used = _mk.expr.some((t) => t.kind === 'num' && t.i === i);
    return `<button type="button" class="mk-num ${used ? 'used' : ''}" data-i="${i}">${n}</button>`;
  }).join('');
  nums.querySelectorAll('.mk-num').forEach((b) => {
    b.addEventListener('click', () => {
      const i = Number(b.dataset.i);
      if (_mk.expr.some((t) => t.kind === 'num' && t.i === i)) return;
      _mkPush({ kind: 'num', i, v: _mk.current[i] });
    });
  });
  _mkRenderExpr();
}

function _mkRenderExpr() {
  const exprEl = document.getElementById('mk-expr');
  const prev = document.getElementById('mk-preview');
  if (!exprEl || !_mk) return;
  if (!_mk.expr.length) { exprEl.textContent = '—'; prev.textContent = ''; return; }
  exprEl.textContent = _mk.expr.map((t) => t.v === '*' ? '×' : t.v === '/' ? '÷' : t.v === '-' ? '−' : t.v).join(' ');
  const val = _mkEval(_mk.expr);
  const target = MK_LEVELS[_mkLevel].target;
  if (val === null) prev.textContent = '…';
  else if (Math.abs(val - target) < 1e-9) prev.textContent = `= ${val} ✓`;
  else prev.textContent = `= ${Math.round(val * 100) / 100}`;
}

function _mkPush(tok) {
  if (!_mk) return;
  _mk.expr.push(tok);
  _mkRender();
}

function _mkUndo() { if (_mk && _mk.expr.length) { _mk.expr.pop(); _mkRender(); } }
function _mkClear() { if (_mk) { _mk.expr = []; _mkRender(); } }

function _mkSubmit() {
  if (!_mk || !_mk.running) return;
  const nums = _mk.expr.filter((t) => t.kind === 'num').length;
  if (nums !== 4) {
    _mkShake();
    return;
  }
  const val = _mkEval(_mk.expr);
  _mk.total += 1;
  const target = MK_LEVELS[_mkLevel].target;
  if (val !== null && Math.abs(val - target) < 1e-9) {
    _mk.correct += 1;
    _mk.streak += 1;
    const bonus = Math.min(MK_CFG.streakCap, _mk.streak) * MK_CFG.streakBonus;
    _mk.score += MK_CFG.solvePoints + bonus;
    if (typeof sfxHit === 'function') sfxHit(_mk.streak);
    if (_mk.streak > 0 && _mk.streak % 3 === 0 && typeof sfxCombo === 'function') sfxCombo();
    _mkUpdateHUD();
    _mkNextHand();
  } else {
    _mk.streak = 0;
    _mkUpdateHUD();
    _mkShake();
    if (typeof sfxMiss === 'function') sfxMiss();
  }
}

function _mkSkip() {
  if (!_mk || !_mk.running) return;
  _mk.score = Math.max(0, _mk.score - MK_CFG.skipPenalty);
  _mk.streak = 0;
  _mkUpdateHUD();
  _mkNextHand();
}

function _mkShake() {
  const el = document.getElementById('mk-expr');
  if (!el) return;
  el.classList.add('mk-shake');
  setTimeout(() => el.classList.remove('mk-shake'), 300);
}

function _mkUpdateHUD() {
  const s = document.getElementById('mk-score');
  const st = document.getElementById('mk-streak');
  if (s) s.textContent = String(_mk.score);
  if (st) st.textContent = String(_mk.streak);
}

/* ── Expression eval (safe) ──────────────────────────────────── */

function _mkEval(tokens) {
  // Build string "a + b * ( c - d )"
  const str = tokens.map((t) => t.kind === 'num' ? `(${t.v})` : t.v).join(' ');
  if (!/^[0-9+\-*/() .]+$/.test(str)) return null;
  try {
    // eslint-disable-next-line no-new-func
    const v = Function(`"use strict"; return (${str});`)();
    return Number.isFinite(v) ? v : null;
  } catch {
    return null;
  }
}

/* ── Solvable hand generator ─────────────────────────────────── */

function _mkGenSolvable() {
  const lv = MK_LEVELS[_mkLevel];
  for (let attempt = 0; attempt < 80; attempt++) {
    const nums = Array.from({ length: 4 }, () =>
      lv.numbersMin + Math.floor(Math.random() * (lv.numbersMax - lv.numbersMin + 1))
    );
    if (_mkHasSolution(nums, lv.ops, lv.target)) return nums;
  }
  return _mkLevel === 'easy' ? [5, 6, 4, 5] : [3, 3, 8, 8];
}

function _mkHasSolution(nums, ops, target) {
  const perms = _perm(nums);
  for (const [a, b, c, d] of perms) {
    for (const o1 of ops) for (const o2 of ops) for (const o3 of ops) {
      const exprs = [
        `((${a}${o1}${b})${o2}${c})${o3}${d}`,
        `(${a}${o1}(${b}${o2}${c}))${o3}${d}`,
        `(${a}${o1}${b})${o2}(${c}${o3}${d})`,
        `${a}${o1}((${b}${o2}${c})${o3}${d})`,
        `${a}${o1}(${b}${o2}(${c}${o3}${d}))`,
      ];
      for (const e of exprs) {
        try {
          const v = Function(`"use strict"; return (${e});`)();
          if (Number.isFinite(v) && Math.abs(v - target) < 1e-9) return true;
        } catch {}
      }
    }
  }
  return false;
}

function _perm(arr) {
  if (arr.length <= 1) return [arr.slice()];
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    const rest = arr.slice(0, i).concat(arr.slice(i + 1));
    for (const p of _perm(rest)) out.push([arr[i], ...p]);
  }
  return out;
}

async function _mkGameOver() {
  if (!_mk) return;
  const state = _mk;
  _mk.running = false;
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('make24', state.score, state.correct, state.total, accuracy, _mkLevel);
  _arcadeRenderGameOver({ state, accuracy, result, replay: `mkStart('${_mkLevel}')` });
}
