/* ================================================================
   arcade-math-invaders.js — Falling equations typing game
   Section: Arcade
   Dependencies: arcade.js, arcade-sfx.js
   API endpoints: POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const MI_LEVELS = {
  easy:   { label: 'Easy',   icon: '🐢', ops: ['+','-'],            max: 10, fall: 22, spawnMin: 3200, spawnMax: 5000, ramp: 0.10, maxActive: 3 },
  normal: { label: 'Normal', icon: '🚀', ops: ['+','-','×'],        max: 10, fall: 30, spawnMin: 2400, spawnMax: 3800, ramp: 0.25, maxActive: 4 },
  hard:   { label: 'Hard',   icon: '🔥', ops: ['+','-','×','÷'],    max: 12, fall: 42, spawnMin: 1700, spawnMax: 2800, ramp: 0.40, maxActive: 5 },
};
const MI_CFG = { maxLives: 3 };
let _mi = null;
let _miLevel = 'normal';

/** Show level picker. @tag ARCADE */
async function miShowLevelPicker() {
  miStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;
  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Difficulty</h2>
      <div class="wi-level-sub">Math Invaders</div>
      <div class="wi-level-list" id="mi-level-list">Loading…</div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;
  const bests = await Promise.all(
    Object.keys(MI_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/math_invaders?level=${lv}`).then((r) => r.ok ? r.json() : { score: 0 }).catch(() => ({ score: 0 }))
    )
  );
  const list = document.getElementById('mi-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(MI_LEVELS).map(([key, cfg], i) => `
    <div class="wi-level-card" onclick="miStart('${key}')">
      <div class="wi-level-icon">${cfg.icon}</div>
      <div class="wi-level-name">${cfg.label}</div>
      <div class="wi-level-spec">${cfg.ops.join(' ')} · max ${cfg.max}</div>
      <div class="wi-level-pb">🏆 ${bests[i].score || 0}</div>
    </div>`).join('');
}

/** Start a run. @tag ARCADE */
function miStart(level = 'normal') {
  miStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;
  _miLevel = MI_LEVELS[level] ? level : 'normal';
  const lv = MI_LEVELS[_miLevel];

  body.classList.add('arcade-body--game');
  body.innerHTML = `
    <div class="wi-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SCORE</span><b id="mi-score">0</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">COMBO</span><b id="mi-streak">0</b>x</div>
        <div class="wi-hud-item wi-hud-lives" id="mi-lives">❤️❤️❤️</div>
        <button type="button" class="wi-hud-quit" onclick="arcadeReturnToLobby()" aria-label="Quit">✕</button>
      </div>
      <div class="wi-canvas-wrap">
        <canvas id="mi-canvas"></canvas>
        <div class="wi-input-wrap">
          <input type="number" inputmode="numeric" id="mi-input" class="wi-input"
                 autocomplete="off" placeholder="Type answer &amp; Enter">
        </div>
      </div>
    </div>`;

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('math_invaders');

  const canvas = document.getElementById('mi-canvas');
  _mi = {
    canvas, ctx: canvas.getContext('2d'),
    active: [], particles: [], nextId: 1,
    score: 0, lives: MI_CFG.maxLives, streak: 0, correct: 0, total: 0,
    fallSpeed: lv.fall, lastTs: performance.now(), lastSpawnAt: 0, nextSpawnDelay: 800,
    running: true, startedAt: performance.now(), shakeUntil: 0,
  };
  _miResizeCanvas();
  window.addEventListener('resize', _miResizeCanvas);
  const input = document.getElementById('mi-input');
  input.value = ''; input.focus();
  input.addEventListener('keydown', _miKeydown);
  if (typeof sfxStart === 'function') sfxStart();
  requestAnimationFrame(_miLoop);
}

function _miResizeCanvas() {
  if (!_mi) return;
  const wrap = _mi.canvas.parentElement;
  if (!wrap) return;
  const dpr = window.devicePixelRatio || 1;
  const w = wrap.clientWidth, h = wrap.clientHeight;
  _mi.canvas.width = Math.round(w * dpr);
  _mi.canvas.height = Math.round(h * dpr);
  _mi.canvas.style.width = w + 'px';
  _mi.canvas.style.height = h + 'px';
  _mi.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  _mi.viewW = w; _mi.viewH = h;
}

/** Stop run. @tag ARCADE */
function miStop() {
  if (!_mi) return;
  _mi.running = false;
  const input = document.getElementById('mi-input');
  if (input) input.removeEventListener('keydown', _miKeydown);
  window.removeEventListener('resize', _miResizeCanvas);
  const body = document.getElementById('arcade-body');
  if (body) body.classList.remove('arcade-body--game');
  _mi = null;
}

function _miKeydown(e) {
  if (!_mi || !_mi.running) return;
  if (e.key !== 'Enter') return;
  const input = e.target;
  const typed = (input.value || '').trim();
  input.value = '';
  if (!typed) return;
  const ans = Number(typed);
  if (!Number.isFinite(ans)) return;

  // Match lowest active equation with this answer
  let hitIdx = -1, lowestY = -1;
  _mi.active.forEach((en, i) => {
    if (en.answer === ans && en.y > lowestY) { hitIdx = i; lowestY = en.y; }
  });

  if (hitIdx >= 0) {
    const en = _mi.active[hitIdx];
    _miBurst(en.x, en.y + 18, '#34C759');
    _mi.active.splice(hitIdx, 1);
    _mi.score += 15 + Math.min(30, _mi.streak * 3);
    _mi.streak += 1; _mi.correct += 1; _mi.total += 1;
    if (typeof sfxHit === 'function') sfxHit(_mi.streak);
    if (_mi.streak > 0 && _mi.streak % 5 === 0 && typeof sfxCombo === 'function') sfxCombo();
  } else {
    _mi.streak = 0;
    if (typeof sfxMiss === 'function') sfxMiss();
  }
  _miUpdateHUD();
}

function _miBurst(x, y, color) {
  for (let i = 0; i < 14; i++) {
    const a = (Math.PI * 2 * i) / 14 + Math.random() * 0.4;
    const spd = 120 + Math.random() * 120;
    _mi.particles.push({ x, y, vx: Math.cos(a) * spd, vy: Math.sin(a) * spd, life: 0.6, maxLife: 0.6, color });
  }
}

function _miUpdateHUD() {
  const s = document.getElementById('mi-score');
  const l = document.getElementById('mi-lives');
  const st = document.getElementById('mi-streak');
  if (s) s.textContent = String(_mi.score);
  if (l) l.textContent = '❤️'.repeat(Math.max(0, _mi.lives)) + '🖤'.repeat(Math.max(0, MI_CFG.maxLives - _mi.lives));
  if (st) st.textContent = String(_mi.streak);
}

function _miGenEquation() {
  const lv = MI_LEVELS[_miLevel];
  const op = lv.ops[Math.floor(Math.random() * lv.ops.length)];
  const M = lv.max;
  let a, b, text, answer;
  if (op === '+') {
    a = 1 + Math.floor(Math.random() * M); b = 1 + Math.floor(Math.random() * M);
    answer = a + b; text = `${a} + ${b}`;
  } else if (op === '-') {
    a = 1 + Math.floor(Math.random() * M); b = 1 + Math.floor(Math.random() * M);
    if (b > a) [a, b] = [b, a];
    answer = a - b; text = `${a} − ${b}`;
  } else if (op === '×') {
    // Cap × operands so products stay mental-math friendly (max ≈ 9×9=81)
    const mulCap = Math.min(M, 9);
    a = 1 + Math.floor(Math.random() * mulCap); b = 1 + Math.floor(Math.random() * mulCap);
    answer = a * b; text = `${a} × ${b}`;
  } else {
    // ÷: ensure integer answer; keep divisor small (2–9) so answers fit in kid's head
    b = 2 + Math.floor(Math.random() * 8);
    answer = 1 + Math.floor(Math.random() * Math.min(M, 9));
    a = answer * b;
    text = `${a} ÷ ${b}`;
  }
  return { text, answer };
}

function _miSpawn() {
  const lv = MI_LEVELS[_miLevel];
  if (_mi.active.length >= lv.maxActive) return;
  const eq = _miGenEquation();
  const inUse = new Set(_mi.active.map((e) => e.text));
  if (inUse.has(eq.text)) return;
  const w = _mi.viewW || 720;
  const x = 80 + Math.random() * Math.max(40, w - 160);
  _mi.active.push({ id: _mi.nextId++, text: eq.text, answer: eq.answer, x, y: -30 });
}

function _miLoop(ts) {
  if (!_mi || !_mi.running) return;
  const dt = Math.min(100, ts - _mi.lastTs) / 1000;
  _mi.lastTs = ts;
  const elapsedSec = (ts - _mi.startedAt) / 1000;
  const lv = MI_LEVELS[_miLevel];
  _mi.fallSpeed = lv.fall + elapsedSec * lv.ramp;

  if (ts - _mi.lastSpawnAt > _mi.nextSpawnDelay) {
    _miSpawn();
    _mi.lastSpawnAt = ts;
    const rampFactor = Math.max(0.55, 1 - elapsedSec / 90);
    _mi.nextSpawnDelay = (lv.spawnMin + Math.random() * (lv.spawnMax - lv.spawnMin)) * rampFactor;
  }

  const floorY = (_mi.viewH || _mi.canvas.height) - 60;
  for (let i = _mi.active.length - 1; i >= 0; i--) {
    const en = _mi.active[i];
    en.y += _mi.fallSpeed * dt;
    if (en.y >= floorY) {
      _miBurst(en.x, floorY, '#FF3B30');
      _mi.active.splice(i, 1);
      _mi.lives -= 1; _mi.streak = 0; _mi.total += 1;
      _mi.shakeUntil = ts + 280;
      if (typeof sfxExplode === 'function') sfxExplode();
      _miUpdateHUD();
      if (_mi.lives <= 0) { _miGameOver(); return; }
    }
  }
  for (let i = _mi.particles.length - 1; i >= 0; i--) {
    const p = _mi.particles[i];
    p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 260 * dt; p.life -= dt;
    if (p.life <= 0) _mi.particles.splice(i, 1);
  }
  _miDraw(ts);
  requestAnimationFrame(_miLoop);
}

function _miDraw(ts) {
  const { ctx } = _mi;
  const W = _mi.viewW, H = _mi.viewH;
  let sx = 0, sy = 0;
  if (ts < _mi.shakeUntil) {
    const mag = 6 * ((_mi.shakeUntil - ts) / 280);
    sx = (Math.random() - 0.5) * mag * 2; sy = (Math.random() - 0.5) * mag * 2;
  }
  ctx.save(); ctx.translate(sx, sy);
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, '#0B1E3F'); grad.addColorStop(1, '#060B1A');
  ctx.fillStyle = grad; ctx.fillRect(0, 0, W, H);

  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  for (let i = 0; i < 40; i++) {
    const sxs = (i * 97) % W;
    const sys = ((i * 53 + ts * 0.02) % H);
    ctx.fillRect(sxs, sys, 1.5, 1.5);
  }
  const floorY = H - 60;
  const pulse = 0.5 + 0.5 * Math.sin(ts / 200);
  ctx.strokeStyle = `rgba(255, 59, 48, ${0.35 + pulse * 0.25})`;
  ctx.lineWidth = 2; ctx.setLineDash([8, 6]);
  ctx.beginPath(); ctx.moveTo(0, floorY); ctx.lineTo(W, floorY); ctx.stroke();
  ctx.setLineDash([]);

  ctx.font = '700 22px -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  _mi.active.forEach((en) => {
    const text = `${en.text} = ?`;
    const padX = 18;
    const w = ctx.measureText(text).width + padX * 2;
    const h = 42;
    const x = Math.max(6, Math.min(W - w - 6, en.x - w / 2));
    const y = en.y;
    const danger = Math.max(0, Math.min(1, (y - (H - 200)) / 140));
    const hue = 200 - danger * 200;
    ctx.shadowColor = `hsl(${hue}, 85%, 60%)`; ctx.shadowBlur = 18;
    ctx.fillStyle = `hsl(${hue}, 75%, 55%)`;
    _miRoundRect(ctx, x, y, w, h, 14); ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(text, x + w / 2, y + h / 2 + 1);
  });
  _mi.particles.forEach((p) => {
    const alpha = Math.max(0, p.life / p.maxLife);
    ctx.fillStyle = p.color; ctx.globalAlpha = alpha;
    ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fill();
  });
  ctx.globalAlpha = 1; ctx.restore();
}

function _miRoundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

async function _miGameOver() {
  const state = _mi;
  _mi.running = false;
  window.removeEventListener('resize', _miResizeCanvas);
  const body = document.getElementById('arcade-body');
  if (body) body.classList.remove('arcade-body--game');
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('math_invaders', state.score, state.correct, state.total, accuracy, _miLevel);
  _arcadeRenderGameOver({ state, accuracy, result, replay: `miStart('${_miLevel}')` });
}
