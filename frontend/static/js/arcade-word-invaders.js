/* ================================================================
   arcade-word-invaders.js — Typing shooter: destroy falling definitions
   Section: Arcade
   Dependencies: arcade.js, core.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const WI_LEVELS = {
  easy:   { label: 'Easy',   fallPxPerSec: 20, spawnMinMs: 3500, spawnMaxMs: 5500, speedRampPerSec: 0.10, maxActive: 3 },
  normal: { label: 'Normal', fallPxPerSec: 28, spawnMinMs: 2600, spawnMaxMs: 4200, speedRampPerSec: 0.25, maxActive: 4 },
  hard:   { label: 'Hard',   fallPxPerSec: 40, spawnMinMs: 1800, spawnMaxMs: 3000, speedRampPerSec: 0.40, maxActive: 5 },
};

/** @tag ARCADE */
const WI_CFG = {
  maxLives: 3,
  waveSize: 10,            // kills per wave
  bossEveryWaves: 3,       // boss appears on every Nth wave
  powerupDropRate: 0.12,   // chance of dropping a power-up on kill
  powerupFallPxPerSec: 30,
  slowDurationMs: 5000,
  slowFactor: 0.4,
  bossMinLen: 7,
  bossScoreBonus: 100,
  waveBonus: 25,
};

/** Read a CSS custom property at runtime (canvas can't use var()). @tag ARCADE */
function _wiCssVar(name, fallback) {
  try {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  } catch (_e) { return fallback; }
}

/** Centralized color palette — semantic tokens read from theme.css, arcade-only
 * game tokens (boss gold, deep-space bg, ice blue) kept named as exemptions
 * since the Apple-minimal theme has no equivalents. @tag ARCADE @tag THEME */
const WI_COLORS = {
  success: _wiCssVar('--color-success', '#34C759'),
  error:   _wiCssVar('--color-error',   '#FF3B30'),
  white:   '#FFFFFF',
  // arcade-only game palette
  bgTop:   '#1A1033',
  bgBot:   '#0A0818',
  ink:     '#1A1033',
  boss:    '#FFD700',
  bombRed: '#FF6B6B',
  ice:     '#4FC3F7',
};

/** @tag ARCADE */
const WI_POWERUPS = {
  ice:    { label: 'ICE',    color: WI_COLORS.ice },
  bomb:   { label: 'BOMB',   color: WI_COLORS.bombRed },
  shield: { label: 'SHIELD', color: WI_COLORS.success },
};

let _wi = null; // state container
let _wiLevel = 'normal';

/** Show level picker before starting. @tag ARCADE */
async function wiShowLevelPicker() {
  wiStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Difficulty</h2>
      <div class="wi-level-sub">Word Invaders</div>
      <div class="wi-level-list" id="wi-level-list">Loading…</div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;

  const bests = await Promise.all(
    Object.keys(WI_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/word_invaders?level=${lv}`)
        .then((r) => (r.ok ? r.json() : { score: 0 }))
        .catch(() => ({ score: 0 }))
    )
  );

  const list = document.getElementById('wi-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(WI_LEVELS)
    .map(([key, cfg], i) => {
      const pb = bests[i].score || 0;
      return `
        <div class="wi-level-card" onclick="wiStart('${key}')">
          <div class="wi-level-icon wi-level-icon--${key}">${key[0].toUpperCase()}</div>
          <div class="wi-level-name">${cfg.label}</div>
          <div class="wi-level-spec">Speed ${cfg.fallPxPerSec} · Max ${cfg.maxActive}</div>
          <div class="wi-level-pb">Best: ${pb}</div>
        </div>`;
    })
    .join('');
}

/** Start a new Word Invaders run. @tag ARCADE */
async function wiStart(level = 'normal') {
  wiStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  _wiLevel = WI_LEVELS[level] ? level : 'normal';
  const lv = WI_LEVELS[_wiLevel];

  body.classList.add('arcade-body--game');
  body.innerHTML = `
    <div class="wi-view">
      <div class="wi-hud">
        <div class="wi-hud-item"><span class="wi-hud-label">SCORE</span><b id="wi-score">0</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">WAVE</span><b id="wi-wave">1</b></div>
        <div class="wi-hud-item"><span class="wi-hud-label">COMBO</span><b id="wi-streak">0</b>x</div>
        <div class="wi-hud-item" id="wi-shield-slot"><span class="wi-hud-label">SHIELD</span><b id="wi-shield">0</b></div>
        <div class="wi-hud-item wi-hud-lives" id="wi-lives"><span class="wi-life"></span><span class="wi-life"></span><span class="wi-life"></span></div>
        <button type="button" class="wi-hud-quit" onclick="arcadeReturnToLobby()" aria-label="Quit">✕</button>
      </div>
      <div class="wi-canvas-wrap">
        <canvas id="wi-canvas"></canvas>
        <div class="wi-input-wrap">
          <input type="text" id="wi-input" class="wi-input" autocomplete="off"
                 autocapitalize="off" spellcheck="false"
                 placeholder="Type word · ice / bomb / shield for power-ups">
        </div>
      </div>
    </div>`;

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('word_invaders');

  const words = await _arcadeFetchWords(60);
  if (!words.length) {
    body.innerHTML = `
      <div class="wi-gameover">
        <h2>No words available</h2>
        <div class="stat">Add words via the Word Manager first.</div>
        <button class="wi-btn" onclick="arcadeReturnToLobby()">Back</button>
      </div>`;
    return;
  }

  const canvas = document.getElementById('wi-canvas');
  _wi = {
    canvas,
    ctx: canvas.getContext('2d'),
    pool: words,
    active: [],
    particles: [],
    powerups: [],
    nextId: 1,
    score: 0,
    lives: WI_CFG.maxLives,
    streak: 0,
    correct: 0,
    total: 0,
    kills: 0,
    wave: 1,
    killsThisWave: 0,
    bossQueued: false,
    shieldCharges: 0,
    slowUntil: 0,
    banner: null,
    fallSpeed: lv.fallPxPerSec,
    lastTs: performance.now(),
    lastSpawnAt: 0,
    nextSpawnDelay: 800,
    running: true,
    startedAt: performance.now(),
    shakeUntil: 0,
  };

  _wiResizeCanvas();
  window.addEventListener('resize', _wiResizeCanvas);

  const input = document.getElementById('wi-input');
  input.value = '';
  input.focus();
  input.addEventListener('keydown', _wiKeydown);

  if (typeof sfxStart === 'function') sfxStart();
  requestAnimationFrame(_wiLoop);
}

function _wiResizeCanvas() {
  if (!_wi) return;
  const wrap = _wi.canvas.parentElement;
  if (!wrap) return;
  const dpr = window.devicePixelRatio || 1;
  const w = wrap.clientWidth;
  const h = wrap.clientHeight;
  _wi.canvas.width = Math.round(w * dpr);
  _wi.canvas.height = Math.round(h * dpr);
  _wi.canvas.style.width = w + 'px';
  _wi.canvas.style.height = h + 'px';
  _wi.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  _wi.viewW = w;
  _wi.viewH = h;
}

/** Stop the run and release listeners. @tag ARCADE */
function wiStop() {
  if (!_wi) return;
  _wi.running = false;
  const input = document.getElementById('wi-input');
  if (input) input.removeEventListener('keydown', _wiKeydown);
  window.removeEventListener('resize', _wiResizeCanvas);
  const body = document.getElementById('arcade-body');
  if (body) body.classList.remove('arcade-body--game');
  _wi = null;
}

function _wiKeydown(e) {
  if (!_wi || !_wi.running) return;
  if (e.key !== 'Enter') return;
  const input = e.target;
  const typed = (input.value || '').trim().toLowerCase();
  input.value = '';
  if (!typed) return;

  // 1) Power-up keyword collected?
  if (WI_POWERUPS[typed]) {
    const puIdx = _wi.powerups.findIndex((p) => p.type === typed);
    if (puIdx >= 0) {
      const pu = _wi.powerups[puIdx];
      _wi.powerups.splice(puIdx, 1);
      _wiActivatePowerup(pu.type, pu.x, pu.y);
      return;
    }
  }

  // 2) Match lowest active enemy
  let hitIdx = -1;
  let lowestY = -1;
  _wi.active.forEach((en, i) => {
    if (en.word.toLowerCase() === typed && en.y > lowestY) {
      hitIdx = i;
      lowestY = en.y;
    }
  });

  if (hitIdx >= 0) {
    _wiKill(hitIdx);
  } else {
    _wi.streak = 0;
    if (typeof sfxMiss === 'function') sfxMiss();
    _wiUpdateHUD();
  }
}

function _wiKill(idx) {
  const en = _wi.active[idx];
  const isBoss = !!en.isBoss;
  _wiBurst(en.x, en.y + 18, isBoss ? WI_COLORS.boss : WI_COLORS.success);
  _wi.active.splice(idx, 1);

  const base = 10 + Math.min(20, _wi.streak * 2);
  const gained = isBoss ? base + WI_CFG.bossScoreBonus : base;
  _wi.score += gained;
  _wi.streak += 1;
  _wi.correct += 1;
  _wi.total += 1;
  _wi.kills += 1;
  _wi.killsThisWave += 1;

  if (typeof sfxHit === 'function') sfxHit(_wi.streak);
  if (_wi.streak > 0 && _wi.streak % 5 === 0 && typeof sfxCombo === 'function') sfxCombo();

  // Maybe drop a power-up
  if (!isBoss && Math.random() < WI_CFG.powerupDropRate) {
    _wiSpawnPowerup(en.x, en.y);
  } else if (isBoss) {
    // Boss always drops one
    _wiSpawnPowerup(en.x, en.y);
  }

  // Wave complete?
  if (_wi.killsThisWave >= WI_CFG.waveSize) {
    _wi.killsThisWave = 0;
    _wi.wave += 1;
    _wi.score += WI_CFG.waveBonus;
    _wi.banner = { text: `WAVE ${_wi.wave - 1} CLEARED  +${WI_CFG.waveBonus}`, until: performance.now() + 1500 };
    if (_wi.wave % WI_CFG.bossEveryWaves === 0) {
      _wi.bossQueued = true;
    }
    if (typeof sfxCombo === 'function') sfxCombo();
  }

  _wiUpdateHUD();
}

function _wiSpawnPowerup(x, y) {
  const keys = Object.keys(WI_POWERUPS);
  const type = keys[Math.floor(Math.random() * keys.length)];
  _wi.powerups.push({ id: _wi.nextId++, type, x, y });
}

function _wiActivatePowerup(type, x, y) {
  const cfg = WI_POWERUPS[type];
  _wiBurst(x, y, cfg.color);
  if (typeof sfxCombo === 'function') sfxCombo();
  if (type === 'ice') {
    _wi.slowUntil = performance.now() + WI_CFG.slowDurationMs;
  } else if (type === 'bomb') {
    const count = _wi.active.length;
    _wi.active.forEach((en) => _wiBurst(en.x, en.y + 18, WI_COLORS.bombRed));
    _wi.score += count * 15;
    _wi.active = [];
    _wi.banner = { text: `BOOM! +${count * 15}`, until: performance.now() + 1000 };
  } else if (type === 'shield') {
    _wi.shieldCharges += 1;
  }
  _wiUpdateHUD();
}

function _wiBurst(x, y, color) {
  for (let i = 0; i < 14; i++) {
    const a = (Math.PI * 2 * i) / 14 + Math.random() * 0.4;
    const spd = 120 + Math.random() * 120;
    _wi.particles.push({
      x, y,
      vx: Math.cos(a) * spd,
      vy: Math.sin(a) * spd,
      life: 0.6,
      maxLife: 0.6,
      color,
    });
  }
}

function _wiUpdateHUD() {
  const s = document.getElementById('wi-score');
  const l = document.getElementById('wi-lives');
  const st = document.getElementById('wi-streak');
  const wv = document.getElementById('wi-wave');
  const sh = document.getElementById('wi-shield');
  if (s) s.textContent = String(_wi.score);
  if (l) { l.innerHTML = Array.from({ length: WI_CFG.maxLives }, (_, i) => `<span class="wi-life${i >= _wi.lives ? ' wi-life--lost' : ''}"></span>`).join(''); }
  if (st) st.textContent = String(_wi.streak);
  if (wv) wv.textContent = String(_wi.wave);
  if (sh) sh.textContent = String(_wi.shieldCharges);
}

function _wiSpawn() {
  const lv = WI_LEVELS[_wiLevel];
  if (_wi.active.length >= lv.maxActive) return;
  const inUse = new Set(_wi.active.map((e) => e.word.toLowerCase()));
  let candidates = _wi.pool.filter((w) => !inUse.has(w.word.toLowerCase()));
  if (!candidates.length) return;

  let isBoss = false;
  if (_wi.bossQueued) {
    const bossPool = candidates.filter((w) => w.word.length >= WI_CFG.bossMinLen);
    if (bossPool.length) {
      candidates = bossPool;
      isBoss = true;
      _wi.bossQueued = false;
    }
  }

  const pick = candidates[Math.floor(Math.random() * candidates.length)];
  const w = _wi.viewW || 720;
  const x = 80 + Math.random() * Math.max(40, w - 160);
  _wi.active.push({
    id: _wi.nextId++,
    word: pick.word,
    x,
    y: -30,
    isBoss,
  });
}

function _wiLoop(ts) {
  if (!_wi || !_wi.running) return;
  if (document.hidden) { requestAnimationFrame(_wiLoop); return; }
  const dt = Math.min(100, ts - _wi.lastTs) / 1000;
  _wi.lastTs = ts;
  const elapsedSec = (ts - _wi.startedAt) / 1000;

  const lv = WI_LEVELS[_wiLevel];
  // Ramp speed over time, apply slow if active
  let speed = lv.fallPxPerSec + elapsedSec * lv.speedRampPerSec;
  if (ts < _wi.slowUntil) speed *= WI_CFG.slowFactor;
  _wi.fallSpeed = speed;

  // Spawn cadence
  if (ts - _wi.lastSpawnAt > _wi.nextSpawnDelay) {
    _wiSpawn();
    _wi.lastSpawnAt = ts;
    const rampFactor = Math.max(0.55, 1 - elapsedSec / 90);
    _wi.nextSpawnDelay =
      (lv.spawnMinMs + Math.random() * (lv.spawnMaxMs - lv.spawnMinMs)) *
      rampFactor;
  }

  // Move + collide with floor
  const floorY = (_wi.viewH || _wi.canvas.height) - 60;
  for (let i = _wi.active.length - 1; i >= 0; i--) {
    const en = _wi.active[i];
    en.y += _wi.fallSpeed * dt;
    if (en.y >= floorY) {
      _wi.active.splice(i, 1);
      _wi.streak = 0;
      _wi.total += 1;
      if (_wi.shieldCharges > 0) {
        _wi.shieldCharges -= 1;
        _wiBurst(en.x, floorY, WI_COLORS.success);
        _wi.banner = { text: 'SHIELD ACTIVE', until: ts + 900 };
        if (typeof sfxCombo === 'function') sfxCombo();
      } else {
        _wiBurst(en.x, floorY, WI_COLORS.error);
        _wi.lives -= 1;
        _wi.shakeUntil = ts + 280;
        if (typeof sfxExplode === 'function') sfxExplode();
      }
      _wiUpdateHUD();
      if (_wi.lives <= 0) {
        _wiGameOver();
        return;
      }
    }
  }

  // Update power-up pickups (slow fall; vanish at floor)
  for (let i = _wi.powerups.length - 1; i >= 0; i--) {
    const p = _wi.powerups[i];
    p.y += WI_CFG.powerupFallPxPerSec * dt;
    if (p.y >= floorY) _wi.powerups.splice(i, 1);
  }

  // Update particles
  for (let i = _wi.particles.length - 1; i >= 0; i--) {
    const p = _wi.particles[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vy += 260 * dt;
    p.life -= dt;
    if (p.life <= 0) _wi.particles.splice(i, 1);
  }

  _wiDraw(ts);
  requestAnimationFrame(_wiLoop);
}

function _wiDraw(ts) {
  const { ctx } = _wi;
  const W = _wi.viewW;
  const H = _wi.viewH;

  // Screen shake offset
  let sx = 0, sy = 0;
  if (ts < _wi.shakeUntil) {
    const mag = 6 * ((_wi.shakeUntil - ts) / 280);
    sx = (Math.random() - 0.5) * mag * 2;
    sy = (Math.random() - 0.5) * mag * 2;
  }
  ctx.save();
  ctx.translate(sx, sy);

  // Background gradient
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, WI_COLORS.bgTop);
  grad.addColorStop(1, WI_COLORS.bgBot);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  // Starfield (deterministic)
  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  for (let i = 0; i < 40; i++) {
    const sxs = (i * 97) % W;
    const sys = ((i * 53 + ts * 0.02) % H);
    ctx.fillRect(sxs, sys, 1.5, 1.5);
  }

  // Danger floor
  const floorY = H - 60;
  const pulse = 0.5 + 0.5 * Math.sin(ts / 200);
  ctx.strokeStyle = `rgba(255, 59, 48, ${0.35 + pulse * 0.25})`;
  ctx.lineWidth = 2;
  ctx.setLineDash([8, 6]);
  ctx.beginPath();
  ctx.moveTo(0, floorY);
  ctx.lineTo(W, floorY);
  ctx.stroke();
  ctx.setLineDash([]);

  // Slow-time overlay
  if (ts < _wi.slowUntil) {
    ctx.fillStyle = 'rgba(79, 195, 247, 0.08)';
    ctx.fillRect(0, 0, W, H);
  }

  // Enemies (neon pill — boss is larger & gold)
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  _wi.active.forEach((en) => {
    const text = en.word;
    const fontPx = en.isBoss ? 28 : 22;
    ctx.font = `700 ${fontPx}px -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif`;
    const padX = en.isBoss ? 24 : 18;
    const w = ctx.measureText(text).width + padX * 2;
    const h = en.isBoss ? 54 : 42;
    const x = Math.max(6, Math.min(W - w - 6, en.x - w / 2));
    const y = en.y;

    if (en.isBoss) {
      const pulseB = 0.7 + 0.3 * Math.sin(ts / 120);
      ctx.shadowColor = `rgba(255, 215, 0, ${pulseB})`;
      ctx.shadowBlur = 28;
      ctx.fillStyle = WI_COLORS.boss;
      _wiRoundRect(ctx, x, y, w, h, 16);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = WI_COLORS.ink;
    } else {
      const danger = Math.max(0, Math.min(1, (y - (H - 200)) / 140));
      const hue = 320 - danger * 320;
      ctx.shadowColor = `hsl(${hue}, 85%, 60%)`;
      ctx.shadowBlur = 18;
      ctx.fillStyle = `hsl(${hue}, 75%, 55%)`;
      _wiRoundRect(ctx, x, y, w, h, 14);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = WI_COLORS.white;
    }
    ctx.fillText(text, x + w / 2, y + h / 2 + 1);
  });

  // Power-up pickups
  ctx.font = '700 14px -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif';
  _wi.powerups.forEach((p) => {
    const cfg = WI_POWERUPS[p.type];
    const w = 84, h = 36;
    const x = Math.max(6, Math.min(W - w - 6, p.x - w / 2));
    const y = p.y;
    const float = Math.sin(ts / 180 + p.id) * 3;
    ctx.shadowColor = cfg.color;
    ctx.shadowBlur = 16;
    ctx.fillStyle = cfg.color;
    _wiRoundRect(ctx, x, y + float, w, h, 10);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = WI_COLORS.bgBot;
    ctx.fillText(cfg.label, x + w / 2, y + float + h / 2 + 1);
  });

  // Particles
  _wi.particles.forEach((p) => {
    const alpha = Math.max(0, p.life / p.maxLife);
    ctx.fillStyle = p.color;
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;

  // Banner (wave/bomb/shield notifications)
  if (_wi.banner && ts < _wi.banner.until) {
    const remain = (_wi.banner.until - ts) / 1500;
    ctx.globalAlpha = Math.min(1, remain * 2);
    ctx.font = '800 34px -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = 'rgba(255,255,255,0.8)';
    ctx.shadowBlur = 20;
    ctx.fillStyle = WI_COLORS.white;
    ctx.fillText(_wi.banner.text, W / 2, H / 2);
    ctx.shadowBlur = 0;
    ctx.globalAlpha = 1;
  } else if (_wi.banner && ts >= _wi.banner.until) {
    _wi.banner = null;
  }

  ctx.restore();
}

function _wiRoundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

async function _wiGameOver() {
  const state = _wi;
  _wi.running = false;
  window.removeEventListener('resize', _wiResizeCanvas);
  const body = document.getElementById('arcade-body');
  if (body) body.classList.remove('arcade-body--game');
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('word_invaders', state.score, state.correct, state.total, accuracy, _wiLevel);
  _arcadeRenderGameOver({ state, accuracy, result, replay: `wiStart('${_wiLevel}')` });
}
