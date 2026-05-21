/* ================================================================
   arcade-word-invaders-render.js — Canvas rendering + game-over handler
   Section: Arcade
   Dependencies: arcade-word-invaders.js (shares _wi state), arcade.js, core.js
   API endpoints: POST /api/arcade/score
   ================================================================ */

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
      _arcadeRoundRect(ctx, x, y, w, h, 16);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = WI_COLORS.ink;
    } else {
      const danger = Math.max(0, Math.min(1, (y - (H - 200)) / 140));
      const hue = 320 - danger * 320;
      ctx.shadowColor = `hsl(${hue}, 85%, 60%)`;
      ctx.shadowBlur = 18;
      ctx.fillStyle = `hsl(${hue}, 75%, 55%)`;
      _arcadeRoundRect(ctx, x, y, w, h, 14);
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
    _arcadeRoundRect(ctx, x, y + float, w, h, 10);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = WI_COLORS.bgBot;
    ctx.fillText(cfg.label, x + w / 2, y + float + h / 2 + 1);
  });

  // Expanding rings
  _wi.rings.forEach((rg) => {
    const alpha = Math.max(0, rg.life / rg.maxLife);
    const r = rg.r + (rg.maxR - rg.r) * (1 - alpha);
    ctx.strokeStyle = rg.color;
    ctx.lineWidth = 3 * alpha;
    ctx.globalAlpha = alpha * 0.8;
    ctx.beginPath();
    ctx.arc(rg.x, rg.y, r, 0, Math.PI * 2);
    ctx.stroke();
  });
  ctx.globalAlpha = 1;

  // Particles
  _wi.particles.forEach((p) => {
    const alpha = Math.max(0, p.life / (p.maxLife || 0.75));
    ctx.fillStyle = p.color;
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r || 3, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;

  // Floating score labels
  _wi.floats.forEach((f) => {
    ctx.globalAlpha = Math.max(0, f.life / f.maxLife);
    ctx.font = '700 20px -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = f.color;
    ctx.shadowColor = f.color;
    ctx.shadowBlur = 8;
    ctx.fillText(f.text, f.x, f.y);
    ctx.shadowBlur = 0;
  });
  ctx.globalAlpha = 1;

  // Banner (wave/bomb/shield notifications)
  if (_wi.banner && ts < _wi.banner.until) {
    const remain = (_wi.banner.until - ts) / (_wi.banner.duration || 1500);  // L-1: per-banner duration for correct alpha
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

  // Last-life danger vignette
  if (_wi.lives === 1) {
    const vigAlpha = 0.15 + 0.10 * Math.sin(ts * 0.004);
    const grad = ctx.createRadialGradient(W / 2, H / 2, H * 0.2, W / 2, H / 2, H * 0.85);
    grad.addColorStop(0, 'rgba(220,38,38,0)');
    grad.addColorStop(1, `rgba(220,38,38,${vigAlpha.toFixed(3)})`);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
  }

  ctx.restore();
}


async function _wiGameOver() {
  if (!_wi) return;
  _wi.running = false;
  window.removeEventListener('resize', _wiResizeCanvas);
  const inp = document.getElementById('wi-input');
  if (inp) inp.removeEventListener('keydown', _wiKeydown);  // D: mirror wiStop() cleanup
  const body = document.getElementById('arcade-body');
  if (body) body.classList.remove('arcade-body--game');
  const state = { ..._wi };
  _wi = null;  // M5: null state immediately to prevent stale callbacks
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('word_invaders', state.score, state.correct, state.total, accuracy, _wiLevel);
  _arcadeRenderGameOver({ state, accuracy, result, replayFn: () => wiStart(_wiLevel) });
}
