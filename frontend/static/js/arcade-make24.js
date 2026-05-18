/* ================================================================
   arcade-make24.js — Combine 4 numbers to reach 24
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const MK_CFG = {
  roundMs: 90000,
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

// Fix #25: memoize solution checks (sorted-nums key → bool)
const _mkSolveCache = new Map();

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
      <div class="arcade-how-to-play">
        <div class="arcade-htp-title">How to play</div>
        <ul class="arcade-htp-list">
          <li>Use all four numbers with +, −, ×, ÷ to reach the target number.</li>
          <li>Click a number card, then click an operator (+, −, ×, ÷), then the next number.</li>
          <li>Parentheses are handled automatically — e.g. (3+1)×(2+4) = 24.</li>
          <li>A hint appears if you are stuck for too long — use it wisely!</li>
          <li>Solve streaks give bonus points. Skip costs points.</li>
        </ul>
      </div>
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
      <div class="wi-level-pb">Best: ${bests[i].score || 0}${_arcadeLevelStarsHTML(bests[i].accuracy || 0)}</div>
    </div>`).join('');
}

/** Start Make 24. @tag ARCADE */
function mkStart(level = 'normal') {
  mkStop();
  _mkSolveCache.clear();  // M2: clear solve cache between sessions (stale entries from prev level)
  _mkLevel = MK_LEVELS[level] ? level : 'normal';
  const lv = MK_LEVELS[_mkLevel];
  const body = document.getElementById('arcade-body');
  if (!body) return;

  _mk = {
    score: 0, streak: 0, correct: 0, total: 0,
    startedAt: performance.now(), running: true,
    current: null, expr: [],
    tickHandle: null,
    handStartedAt: null,  // Fix #31: track per-hand start time for hint
    hintShown: false,
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
          <button type="button" class="wi-btn secondary" id="mk-hint-btn" style="display:none" title="Shows one step toward the solution">Hint</button>
        </div>
        <div class="mk-hint-note" id="mk-hint-note">Stuck? A hint appears after 30 seconds.</div>
        <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Quit</button>
      </div>
    </div>`;

  document.getElementById('mk-undo').addEventListener('click', _mkUndo);
  document.getElementById('mk-clear').addEventListener('click', _mkClear);
  document.getElementById('mk-submit').addEventListener('click', _mkSubmit);
  document.getElementById('mk-skip').addEventListener('click', _mkSkip);
  document.getElementById('mk-hint-btn').addEventListener('click', _mkShowHint);  // Fix #31
  document.querySelectorAll('.mk-op').forEach((b) => b.addEventListener('click', () => _mkPush({ kind: 'op', v: b.dataset.op })));

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('make24');

  if (typeof sfxStart === 'function') sfxStart();
  _mkNextHand();
  _mk.tickHandle = setInterval(_mkTick, 500);  // Fix #19: setInterval instead of rAF
}

/** Stop. @tag ARCADE */
function mkStop() {
  if (_mk) {
    _mk.running = false;
    if (_mk.tickHandle) { clearInterval(_mk.tickHandle); _mk.tickHandle = null; }
  }
  _mk = null;
}

// Fix #19: setInterval-based tick (500ms) — no rAF waste
function _mkTick() {
  if (!_mk || !_mk.running) return;
  if (document.hidden) return;
  const remain = Math.max(0, MK_CFG.roundMs - (performance.now() - _mk.startedAt));
  const el = document.getElementById('mk-time');
  if (el) {
    el.textContent = String(Math.ceil(remain / 1000));
    el.classList.toggle('mk-time--urgent', remain <= 10000);
  }

  // Fix #31: show hint button 30s after hand started
  if (_mk.handStartedAt && !_mk.hintShown &&
      performance.now() - _mk.handStartedAt >= 30000) {
    _mk.hintShown = true;
    const hintEl = document.getElementById('mk-hint-btn');
    if (hintEl) hintEl.style.display = '';
    const noteEl = document.getElementById('mk-hint-note');
    if (noteEl) noteEl.style.display = 'none';
  }

  if (remain <= 0) {
    if (_mk.tickHandle) { clearInterval(_mk.tickHandle); _mk.tickHandle = null; }
    _mkGameOver();
  }
}

function _mkNextHand() {
  if (!_mk) return;
  _mk.current = _mkGenSolvable();
  _mk.expr = [];
  _mk.handStartedAt = performance.now();  // Fix #31: reset per-hand timer
  _mk.hintShown = false;
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
    const handler = () => {
      const i = Number(b.dataset.i);
      if (_mk.expr.some((t) => t.kind === 'num' && t.i === i)) return;
      _mkPush({ kind: 'num', i, v: _mk.current[i] });
    };
    b.addEventListener('click', handler);
    // Fix #16: touch support for mobile drag/tap
    b.addEventListener('touchend', (e) => { e.preventDefault(); handler(); }, { passive: false });
  });
  _mkRenderExpr();
}

function _mkRenderExpr() {
  const exprEl = document.getElementById('mk-expr');
  const prev = document.getElementById('mk-preview');
  if (!exprEl || !prev || !_mk) return;  // C: guard prev (mk-preview) against null
  if (!_mk.expr.length) { exprEl.textContent = '—'; prev.textContent = ''; return; }
  exprEl.textContent = _mk.expr.map((t) => t.v === '*' ? '×' : t.v === '/' ? '÷' : t.v === '-' ? '−' : t.v).join(' ');
  const val = _mkEval(_mk.expr);
  const target = MK_LEVELS[_mkLevel].target;
  if (val === null) prev.textContent = '…';
  else if (Math.abs(val - target) < 1e-9) { prev.innerHTML = `= ${val} <i data-lucide="check" style="width:14px;height:14px;vertical-align:-2px;stroke-width:2.5"></i>`; if (typeof lucide !== 'undefined') lucide.createIcons(); }
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
  _mk.total += 1;          // skipped puzzle counts as an attempt (not correct)
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

/* ── Expression eval (shunting-yard, no eval/Function) ──────── */

function _mkApplyOp(a, op, b) {
  if (op === '+') return a + b;
  if (op === '-') return a - b;
  if (op === '*') return a * b;
  if (op === '/') return Math.abs(b) < 1e-10 ? null : a / b;
  return null;
}

function _mkEval(tokens) {
  const prec = { '+': 1, '-': 1, '*': 2, '/': 2 };
  const output = [];
  const opStack = [];

  for (const tok of tokens) {
    if (tok.kind === 'num') {
      output.push(tok.v);
    } else if (tok.v === '(') {
      opStack.push('(');
    } else if (tok.v === ')') {
      while (opStack.length && opStack[opStack.length - 1] !== '(') {
        output.push(opStack.pop());
      }
      if (!opStack.length) return null;
      opStack.pop();
    } else {
      const op = tok.v;
      while (
        opStack.length &&
        opStack[opStack.length - 1] !== '(' &&
        (prec[opStack[opStack.length - 1]] || 0) >= (prec[op] || 0)
      ) {
        output.push(opStack.pop());
      }
      opStack.push(op);
    }
  }
  while (opStack.length) {
    const op = opStack.pop();
    if (op === '(') return null;
    output.push(op);
  }

  const stack = [];
  for (const item of output) {
    if (typeof item === 'number') {
      stack.push(item);
    } else {
      if (stack.length < 2) return null;
      const b = stack.pop();
      const a = stack.pop();
      const r = _mkApplyOp(a, item, b);
      if (r === null) return null;
      stack.push(r);
    }
  }
  if (stack.length !== 1) return null;
  return Number.isFinite(stack[0]) ? stack[0] : null;
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
  // Fallback pool: pre-verified solvable hands for each mode
  // Easy (target=20, +/-): all sum exactly to 20
  // Normal (target=24, +/-/*/÷): each verified with a concrete solution
  //   [3,3,8,8]: 8÷(3-8÷3)=24  [1,2,3,4]: 1×2×3×4=24
  //   [3,6,8,8]: (8÷8+3)×6=24  [2,2,4,8]: 8×2+2×4=24  [6,6,6,6]: 6+6+6+6=24
  const fallbacks = _mkLevel === 'easy'
    ? [[5, 6, 4, 5], [4, 8, 4, 4], [6, 7, 3, 4], [5, 5, 5, 5], [9, 1, 6, 4]]
    : [[3, 3, 8, 8], [1, 2, 3, 4], [3, 6, 8, 8], [2, 2, 4, 8], [6, 6, 6, 6]];
  return fallbacks[Math.floor(Math.random() * fallbacks.length)];
}

function _mkHasSolution(nums, ops, target) {
  // Fix #25: memoize by sorted nums + ops + target to avoid repeated permutation search
  const key = [...nums].sort((a, b) => a - b).join(',') + '|' + ops.join('') + '|' + target;
  if (_mkSolveCache.has(key)) return _mkSolveCache.get(key);
  let found = false;
  outer: for (const [a, b, c, d] of _perm(nums)) {
    for (const o1 of ops) for (const o2 of ops) for (const o3 of ops) {
      // ((a o1 b) o2 c) o3 d
      const ab = _mkApplyOp(a, o1, b);
      const abc1 = ab !== null ? _mkApplyOp(ab, o2, c) : null;
      if (abc1 !== null) { const r = _mkApplyOp(abc1, o3, d); if (r !== null && Math.abs(r - target) < 1e-9) { found = true; break outer; } }
      // (a o1 (b o2 c)) o3 d
      const bc = _mkApplyOp(b, o2, c);
      const abc2 = bc !== null ? _mkApplyOp(a, o1, bc) : null;
      if (abc2 !== null) { const r = _mkApplyOp(abc2, o3, d); if (r !== null && Math.abs(r - target) < 1e-9) { found = true; break outer; } }
      // (a o1 b) o2 (c o3 d)
      const cd = _mkApplyOp(c, o3, d);
      if (ab !== null && cd !== null) { const r = _mkApplyOp(ab, o2, cd); if (r !== null && Math.abs(r - target) < 1e-9) { found = true; break outer; } }
      // a o1 ((b o2 c) o3 d)
      const bcd1 = bc !== null ? _mkApplyOp(bc, o3, d) : null;
      if (bcd1 !== null) { const r = _mkApplyOp(a, o1, bcd1); if (r !== null && Math.abs(r - target) < 1e-9) { found = true; break outer; } }
      // a o1 (b o2 (c o3 d))
      const bcd2 = cd !== null ? _mkApplyOp(b, o2, cd) : null;
      if (bcd2 !== null) { const r = _mkApplyOp(a, o1, bcd2); if (r !== null && Math.abs(r - target) < 1e-9) { found = true; break outer; } }
    }
  }
  _mkSolveCache.set(key, found);  // Fix #25: cache result
  return found;
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

/**
 * Format a number for display (strip floating-point noise).
 * @param {number} v
 * @returns {string}
 */
function _mkFmt(v) { return String(Math.round(v * 10000) / 10000); }

/**
 * Search all 5 parenthesization structures for a valid solution.
 * Returns { hint: string } on success, or null if none found.
 * @param {number[]} nums
 * @returns {{hint: string}|null}
 */
function _mkFindHint(nums) {
  const lv = MK_LEVELS[_mkLevel];
  const fmtOp = (o) => o === '*' ? '×' : o === '/' ? '÷' : o === '-' ? '−' : o;
  for (const [a, b, c, d] of _perm(nums)) {
    for (const o1 of lv.ops) for (const o2 of lv.ops) for (const o3 of lv.ops) {
      const ab = _mkApplyOp(a, o1, b);
      const bc = _mkApplyOp(b, o2, c);
      const cd = _mkApplyOp(c, o3, d);
      // 1: ((a o1 b) o2 c) o3 d
      if (ab !== null) {
        const abc = _mkApplyOp(ab, o2, c);
        if (abc !== null) {
          const r = _mkApplyOp(abc, o3, d);
          if (r !== null && Math.abs(r - lv.target) < 1e-9)
            return { hint: `Try: ${a} ${fmtOp(o1)} ${b} = ${_mkFmt(ab)}` };
        }
      }
      // 2: (a o1 (b o2 c)) o3 d
      if (bc !== null) {
        const abc = _mkApplyOp(a, o1, bc);
        if (abc !== null) {
          const r = _mkApplyOp(abc, o3, d);
          if (r !== null && Math.abs(r - lv.target) < 1e-9)
            return { hint: `Try: ${b} ${fmtOp(o2)} ${c} = ${_mkFmt(bc)}` };
        }
      }
      // 3: (a o1 b) o2 (c o3 d)
      if (ab !== null && cd !== null) {
        const r = _mkApplyOp(ab, o2, cd);
        if (r !== null && Math.abs(r - lv.target) < 1e-9)
          return { hint: `Try: ${a} ${fmtOp(o1)} ${b} = ${_mkFmt(ab)}` };
      }
      // 4: a o1 ((b o2 c) o3 d)
      if (bc !== null) {
        const bcd = _mkApplyOp(bc, o3, d);
        if (bcd !== null) {
          const r = _mkApplyOp(a, o1, bcd);
          if (r !== null && Math.abs(r - lv.target) < 1e-9)
            return { hint: `Try: ${b} ${fmtOp(o2)} ${c} = ${_mkFmt(bc)}` };
        }
      }
      // 5: a o1 (b o2 (c o3 d))
      if (cd !== null) {
        const bcd = _mkApplyOp(b, o2, cd);
        if (bcd !== null) {
          const r = _mkApplyOp(a, o1, bcd);
          if (r !== null && Math.abs(r - lv.target) < 1e-9)
            return { hint: `Try: ${c} ${fmtOp(o3)} ${d} = ${_mkFmt(cd)}` };
        }
      }
    }
  }
  return null;
}

/** Fix #31: reveal one solution step as a text hint (all 5 structures). @tag ARCADE */
function _mkShowHint() {
  if (!_mk || !_mk.current) return;
  const found = _mkFindHint(_mk.current);
  const prev = document.getElementById('mk-preview');
  if (!prev) return;
  if (found) {
    prev.textContent = `Hint: ${found.hint}`;
    prev.style.color = 'var(--arcade-ink)';
  } else {
    prev.textContent = 'No hint available';
    prev.style.color = 'var(--text-hint)';
  }
}

async function _mkGameOver() {
  if (!_mk) return;
  _mk.running = false;
  const state = { ..._mk };  // M-4: snapshot before null
  _mk = null;                 // M-4: null immediately to prevent stale callbacks
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('make24', state.score, state.correct, state.total, accuracy, _mkLevel);
  _arcadeRenderGameOver({ state, accuracy, result, replayFn: () => mkStart(_mkLevel) });
}
