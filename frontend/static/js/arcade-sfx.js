/* ================================================================
   arcade-sfx.js — Web Audio synth SFX for arcade games (retro blips)
   Section: Arcade
   Dependencies: none
   API endpoints: none
   ================================================================ */

/** Lazy-initialised shared AudioContext. @tag ARCADE @tag SYSTEM */
let _arcadeCtx = null;
let _arcadeMuted = false;

/** Get or create the shared AudioContext. Safari needs user gesture. */
function _arcadeAudio() {
  if (_arcadeMuted) return null;
  if (!_arcadeCtx) {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      _arcadeCtx = new Ctx();
    } catch (e) {
      return null;
    }
  }
  if (_arcadeCtx.state === 'suspended') _arcadeCtx.resume();
  return _arcadeCtx;
}

/** Toggle arcade SFX on/off. @tag ARCADE */
function arcadeSfxSetMuted(muted) {
  _arcadeMuted = !!muted;
  try { localStorage.setItem('arcade_muted', _arcadeMuted ? '1' : '0'); } catch (e) {}
}

/** Is arcade SFX muted? @tag ARCADE */
function arcadeSfxIsMuted() {
  return _arcadeMuted;
}

// Restore persisted preference
try {
  _arcadeMuted = localStorage.getItem('arcade_muted') === '1';
} catch (e) {}

/**
 * Play a pitched blip.
 * @param {number} freq Hz
 * @param {number} dur seconds
 * @param {'sine'|'square'|'triangle'|'sawtooth'} type
 * @param {number} vol 0..1
 * @param {number} sweepTo optional end frequency for pitch sweep
 */
function _arcadeBlip(freq, dur, type = 'square', vol = 0.18, sweepTo = null) {
  const ctx = _arcadeAudio();
  if (!ctx) return;
  const t0 = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t0);
  if (sweepTo !== null) {
    osc.frequency.exponentialRampToValueAtTime(Math.max(40, sweepTo), t0 + dur);
  }
  gain.gain.setValueAtTime(0.0001, t0);
  gain.gain.exponentialRampToValueAtTime(vol, t0 + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start(t0);
  osc.stop(t0 + dur + 0.02);
}

/** Short noise burst (for explosions). */
function _arcadeNoise(dur = 0.25, vol = 0.3) {
  const ctx = _arcadeAudio();
  if (!ctx) return;
  const t0 = ctx.currentTime;
  const bufSize = Math.floor(ctx.sampleRate * dur);
  const buf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < bufSize; i++) {
    data[i] = (Math.random() * 2 - 1) * (1 - i / bufSize);
  }
  const src = ctx.createBufferSource();
  const filter = ctx.createBiquadFilter();
  const gain = ctx.createGain();
  src.buffer = buf;
  filter.type = 'lowpass';
  filter.frequency.value = 800;
  gain.gain.setValueAtTime(vol, t0);
  gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
  src.connect(filter);
  filter.connect(gain);
  gain.connect(ctx.destination);
  src.start(t0);
  src.stop(t0 + dur);
}

/* ── Arcade SFX primitives ───────────────────────────────────── */

/** Word destroyed — rising blip. Pitch rises with combo. @tag ARCADE */
function sfxHit(combo = 0) {
  const base = 520 + Math.min(12, combo) * 40;
  _arcadeBlip(base, 0.09, 'square', 0.16, base * 1.8);
}

/** Wrong typing — short low thud. @tag ARCADE */
function sfxMiss() {
  _arcadeBlip(180, 0.1, 'square', 0.14, 90);
}

/** Life lost — descending sweep + noise. @tag ARCADE */
function sfxExplode() {
  _arcadeBlip(300, 0.35, 'sawtooth', 0.2, 60);
  _arcadeNoise(0.3, 0.22);
}

/** Combo milestone chime — happy arpeggio. @tag ARCADE */
function sfxCombo() {
  _arcadeBlip(660, 0.08, 'triangle', 0.14);
  setTimeout(() => _arcadeBlip(880, 0.08, 'triangle', 0.14), 70);
  setTimeout(() => _arcadeBlip(1175, 0.12, 'triangle', 0.14), 140);
}

/** Game over — descending sad sequence. @tag ARCADE */
function sfxGameOver() {
  _arcadeBlip(440, 0.18, 'square', 0.18);
  setTimeout(() => _arcadeBlip(349, 0.2, 'square', 0.18), 180);
  setTimeout(() => _arcadeBlip(262, 0.4, 'square', 0.18, 200), 380);
}

/** Game start chime. @tag ARCADE */
function sfxStart() {
  _arcadeBlip(523, 0.1, 'triangle', 0.16);
  setTimeout(() => _arcadeBlip(784, 0.14, 'triangle', 0.16), 90);
}

/** New personal best fanfare. @tag ARCADE */
function sfxNewBest() {
  _arcadeBlip(523, 0.1, 'triangle', 0.16);
  setTimeout(() => _arcadeBlip(659, 0.1, 'triangle', 0.16), 90);
  setTimeout(() => _arcadeBlip(784, 0.1, 'triangle', 0.16), 180);
  setTimeout(() => _arcadeBlip(1047, 0.25, 'triangle', 0.18), 270);
}
