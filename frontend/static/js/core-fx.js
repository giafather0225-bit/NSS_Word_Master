/* ================================================================
   core-fx.js — Audio fx + particle burst (extracted from core.js)
   Section: English / System
   Dependencies: core.js ($(), CONF), sound.js (window.SoundFX optional)
   API endpoints: none
   ================================================================ */

// ─── Audio FX ─────────────────────────────────────────────────
/**
 * Play a short synthesised tone via Web Audio API.
 * Legacy shim — kept for backward compat; new code uses SoundFX directly.
 * @tag SYSTEM
 */
function _playTone(freq, dur, type) {
    if (window.SoundFX) return;
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type || "sine";
        osc.frequency.value = freq;
        gain.gain.value = 0.18;
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
        osc.stop(ctx.currentTime + dur);
    } catch (e) {}
}

/**
 * Flash the stage element green and play a correct-answer tone.
 * @tag SYSTEM
 */
function stageFxCorrect() {
    const s = $("stage");
    if (!s) return;
    s.classList.remove("fx-wrong");
    s.classList.add("fx-correct");
    setTimeout(() => s.classList.remove("fx-correct"), 650);
    if (window.SoundFX) { SoundFX.correct(); } else {
        _playTone(523, 0.12, "sine");
        setTimeout(() => _playTone(784, 0.18, "sine"), 120);
    }
}

/**
 * Flash the stage element red, play a wrong-answer tone, and vibrate.
 * @tag SYSTEM
 */
function stageFxWrong() {
    const s = $("stage");
    if (!s) return;
    s.classList.remove("fx-correct");
    s.classList.remove("fx-wrong");
    void s.offsetWidth;
    s.classList.add("fx-wrong");
    setTimeout(() => s.classList.remove("fx-wrong"), 350);
    if (window.SoundFX) { SoundFX.wrong(); } else {
        _playTone(200, 0.25, "square");
    }
    if (navigator.vibrate) navigator.vibrate(150);
}

// ─── Particle system ──────────────────────────────────────────
/** @tag SYSTEM */
const _particleTimers = [];

/**
 * Show the "Perfect!" banner briefly.
 * @tag SYSTEM XP
 */
function showPerfectBanner(text) {
    const el = $("perfect-banner");
    if (!el) return;
    el.style.display = "";
    el.textContent = text;
    el.classList.remove("fire");
    void el.offsetWidth;
    el.classList.add("fire");
    setTimeout(() => { el.style.display = "none"; }, 3000);
}

/**
 * Spawn a particle burst at the centre of the particle layer.
 * @tag SYSTEM XP
 */
function particleBurst(count) {
    const layer = $("particle-layer");
    if (!layer) return;
    const n = Math.min(CONF.PARTICLE_MAX, Math.max(8, count | 0));
    const rect = layer.getBoundingClientRect();
    const cx = rect.width * 0.5;
    const cy = rect.height * 0.35;
    for (let i = 0; i < n; i++) {
        const p = document.createElement("div");
        p.className = "particle";
        const ang = (Math.PI * 2 * i) / n + Math.random() * 0.4;
        const dist = 80 + Math.random() * 120;
        p.style.left = `${cx + (Math.random() - 0.5) * 40}px`;
        p.style.top = `${cy + (Math.random() - 0.5) * 40}px`;
        p.style.setProperty("--dx", `${Math.cos(ang) * dist}px`);
        p.style.setProperty("--dy", `${Math.sin(ang) * dist - 20}px`);
        layer.appendChild(p);
        const tid = setTimeout(() => {
            p.remove();
            const idx = _particleTimers.indexOf(tid);
            if (idx !== -1) _particleTimers.splice(idx, 1);
        }, CONF.PARTICLE_LIFETIME);
        _particleTimers.push(tid);
    }
}

window.addEventListener("pagehide", () => {
    _particleTimers.forEach(clearTimeout);
    _particleTimers.length = 0;
    const layer = $("particle-layer");
    if (layer) layer.innerHTML = "";
});
