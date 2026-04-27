/* ================================================================
   sound.js — UI sound effects via Web Audio API
   Section: System
   Dependencies: none (pure Web Audio API, no server)
   API endpoints: none

   Rules:
   - 유아틱한 효과음 금지 — 깔끔한 UI 피드백 톤
   - 기본 볼륨 0.30 (30%)
   - 사용자가 한 번이라도 interact 해야 AudioContext 활성화됨
   - window.SoundFX.correct() / wrong() / levelUp() / star() / click()
   ================================================================ */

const SoundFX = (() => {
  /** @tag SYSTEM */
  let _ctx = null;
  let _volume = 0.30;
  let _enabled = true;

  // localStorage에서 설정 복원
  try {
    const saved = localStorage.getItem('gia-sound');
    if (saved !== null) _enabled = saved !== '0';
    const vol = parseFloat(localStorage.getItem('gia-sound-vol'));
    if (!isNaN(vol)) _volume = Math.min(1, Math.max(0, vol));
  } catch (_) {}

  function _context() {
    if (!_ctx) _ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (_ctx.state === 'suspended') _ctx.resume();
    return _ctx;
  }

  /**
   * 단순 사인파 음 생성
   * @param {number}   freq      주파수 (Hz)
   * @param {number}   duration  재생 시간 (초)
   * @param {number}   gain      볼륨 배율 (0–1)
   * @param {number}   startTime AudioContext 시작 시각
   * @param {'sine'|'triangle'|'square'} type 파형
   */
  function _tone(freq, duration, gain = 1.0, startTime = 0, type = 'sine') {
    if (!_enabled) return;
    const ctx  = _context();
    const t    = ctx.currentTime + startTime;
    const osc  = ctx.createOscillator();
    const amp  = ctx.createGain();

    osc.type      = type;
    osc.frequency.setValueAtTime(freq, t);

    amp.gain.setValueAtTime(0, t);
    amp.gain.linearRampToValueAtTime(_volume * gain, t + 0.01);
    amp.gain.exponentialRampToValueAtTime(0.0001, t + duration);

    osc.connect(amp);
    amp.connect(ctx.destination);
    osc.start(t);
    osc.stop(t + duration + 0.02);
  }

  // ── Public sounds ──────────────────────────────────────

  /**
   * 정답 — 맑은 상승 차임 (440 → 660 Hz)
   * @tag ENGLISH MATH
   */
  function correct() {
    _tone(440, 0.12, 0.8, 0.00, 'sine');
    _tone(660, 0.18, 0.7, 0.10, 'sine');
  }

  /**
   * 오답 — 낮은 하강 덜컥음 (220 → 180 Hz)
   * @tag ENGLISH MATH
   */
  function wrong() {
    _tone(220, 0.08, 0.6, 0.00, 'triangle');
    _tone(180, 0.14, 0.5, 0.07, 'triangle');
  }

  /**
   * 레벨업 — 3음 상승 멜로디 (C5 → E5 → G5)
   * @tag XP AWARD
   */
  function levelUp() {
    _tone(523, 0.14, 0.75, 0.00, 'sine'); // C5
    _tone(659, 0.14, 0.75, 0.16, 'sine'); // E5
    _tone(784, 0.24, 0.80, 0.32, 'sine'); // G5
  }

  /**
   * 스테이지 완료 — 짧고 깔끔한 확인음
   * @tag ENGLISH MATH
   */
  function stageComplete() {
    _tone(440, 0.10, 0.65, 0.00, 'sine');
    _tone(550, 0.10, 0.65, 0.12, 'sine');
    _tone(660, 0.20, 0.70, 0.24, 'sine');
  }

  /**
   * 즐겨찾기 — 부드러운 팝음
   * @tag ENGLISH
   */
  function star() {
    _tone(880, 0.06, 0.50, 0.00, 'sine');
    _tone(1100, 0.10, 0.35, 0.06, 'sine');
  }

  /**
   * 버튼 클릭 — 아주 짧은 틱
   * @tag SYSTEM
   */
  function click() {
    _tone(600, 0.05, 0.25, 0.00, 'sine');
  }

  /**
   * XP 획득 — 밝은 단음
   * @tag XP AWARD
   */
  function xpGain() {
    _tone(740, 0.08, 0.45, 0.00, 'sine');
    _tone(880, 0.12, 0.40, 0.09, 'sine');
  }

  /**
   * 스트릭 유지 — 따뜻한 확인음
   * @tag STREAK
   */
  function streakKeep() {
    _tone(392, 0.10, 0.55, 0.00, 'sine'); // G4
    _tone(494, 0.16, 0.55, 0.12, 'sine'); // B4
  }

  // ── Settings ───────────────────────────────────────────

  /** 사운드 on/off 토글. @tag SYSTEM */
  function toggle() {
    _enabled = !_enabled;
    try { localStorage.setItem('gia-sound', _enabled ? '1' : '0'); } catch (_) {}
    return _enabled;
  }

  /** 볼륨 설정 (0.0 – 1.0). @tag SYSTEM */
  function setVolume(v) {
    _volume = Math.min(1, Math.max(0, v));
    try { localStorage.setItem('gia-sound-vol', String(_volume)); } catch (_) {}
  }

  /** 현재 상태 반환. @tag SYSTEM */
  function getState() {
    return { enabled: _enabled, volume: _volume };
  }

  // 첫 번째 사용자 인터랙션에서 AudioContext 준비
  const _initOnce = () => {
    _context();
    document.removeEventListener('pointerdown', _initOnce);
  };
  document.addEventListener('pointerdown', _initOnce, { once: true });

  return { correct, wrong, levelUp, stageComplete, star, click, xpGain, streakKeep, toggle, setVolume, getState };
})();

window.SoundFX = SoundFX;
