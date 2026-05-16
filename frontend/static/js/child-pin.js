/* ================================================================
   child-pin.js — GIA secret PIN entry / first-time setup screen
   Section: System
   Dependencies: none (runs before all other scripts)
   API endpoints:
     GET  /api/parent/child-pin-status
     POST /api/parent/child-pin-setup
     POST /api/parent/child-pin-verify
   ================================================================ */

/**
 * Blocks splash auto-start until PIN is verified.
 * child-pin.js must be loaded BEFORE splash.js in child.html.
 * @tag SYSTEM
 */
window.GIA_PIN_MODE = true;

const GIAPin = (() => {
  let _mode = 'verify'; // 'setup' | 'confirm' | 'verify'
  let _currentPin = '';
  let _confirmPin = '';
  let _overlay = null;
  let _titleEl = null;
  let _subtitleEl = null;
  let _dots = [];

  // ── API ────────────────────────────────────────────────────────
  async function _checkStatus() {
    try {
      const res = await fetch('/api/parent/child-pin-status');
      if (!res.ok) return false;
      const data = await res.json();
      return data.pin_set === true;
    } catch {
      return false;
    }
  }

  async function _setupPin(pin) {
    const res = await fetch('/api/parent/child-pin-setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin })
    });
    return res.ok;
  }

  async function _verifyPin(pin) {
    try {
      const res = await fetch('/api/parent/child-pin-verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin })
      });
      if (!res.ok) return false;
      const data = await res.json();
      return data.ok === true;
    } catch {
      return false;
    }
  }

  // ── DOM helpers ────────────────────────────────────────────────
  function _renderDots(len) {
    _dots.forEach((dot, i) => {
      dot.classList.toggle('filled', i < len);
    });
  }

  function _shake() {
    const card = _overlay.querySelector('.gpin-card');
    card.classList.remove('shake');
    void card.offsetWidth; // force reflow
    card.classList.add('shake');
    setTimeout(() => card.classList.remove('shake'), 500);
  }

  function _clearPin() {
    _currentPin = '';
    _renderDots(0);
  }

  function _setTitle(title, subtitle) {
    if (_titleEl) _titleEl.textContent = title;
    if (_subtitleEl) _subtitleEl.textContent = subtitle;
  }

  // ── Input handling ─────────────────────────────────────────────
  async function _handleDigit(digit) {
    if (_currentPin.length >= 4) return;
    _currentPin += digit;
    _renderDots(_currentPin.length);
    if (_currentPin.length === 4) await _handleComplete();
  }

  function _handleDelete() {
    if (_currentPin.length > 0) {
      _currentPin = _currentPin.slice(0, -1);
      _renderDots(_currentPin.length);
    }
  }

  async function _handleComplete() {
    if (_mode === 'setup') {
      _confirmPin = _currentPin;
      _mode = 'confirm';
      _setTitle('Enter it again', 'Confirm your secret code');
      _clearPin();

    } else if (_mode === 'confirm') {
      if (_currentPin === _confirmPin) {
        // Flash green then proceed
        _dots.forEach(d => d.classList.add('success'));
        const ok = await _setupPin(_currentPin);
        if (ok) {
          // First time — after success, show guide then splash
          setTimeout(() => _onSuccess(true), 500);
        } else {
          _dots.forEach(d => d.classList.remove('success'));
          _shake();
          _clearPin();
          _setTitle('Something went wrong', 'Try again');
        }
      } else {
        _shake();
        _clearPin();
        _setTitle("That didn't match", 'Try again');
        setTimeout(() => {
          _mode = 'setup';
          _confirmPin = '';
          _setTitle('Create your secret code', 'Choose 4 numbers');
        }, 1000);
      }

    } else if (_mode === 'verify') {
      const ok = await _verifyPin(_currentPin);
      if (ok) {
        _dots.forEach(d => d.classList.add('success'));
        setTimeout(() => _onSuccess(false), 400);
      } else {
        _shake();
        _clearPin();
      }
    }
  }

  // ── Completion: dismiss overlay, start splash ──────────────────
  function _onSuccess(isFirstTime) {
    _overlay.classList.add('gpin-exit');
    setTimeout(() => {
      _overlay.remove();
      _overlay = null;
      // Start splash
      if (window.GIASplash) {
        GIASplash.init().then(() => {
          // After splash finishes, show onboarding guide if first time
          if (isFirstTime && window.GIAGuide) {
            GIAGuide.openIfFirstTime();
          }
        });
      } else {
        // Fallback: splash script not yet available
        if (isFirstTime && window.GIAGuide) {
          GIAGuide.openIfFirstTime();
        }
      }
    }, 480);
  }

  // ── Build overlay DOM ──────────────────────────────────────────
  function _buildOverlay() {
    const el = document.createElement('div');
    el.id = 'gpin-overlay';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-label', 'Enter your secret code');
    el.innerHTML = `
      <div class="gpin-card">
        <img src="/static/img/GIA_Logo.png" alt="GIA" class="gpin-logo">
        <div class="gpin-title" id="gpin-title"></div>
        <div class="gpin-subtitle" id="gpin-subtitle"></div>
        <div class="gpin-dots" id="gpin-dots" aria-hidden="true">
          <span class="gpin-dot"></span>
          <span class="gpin-dot"></span>
          <span class="gpin-dot"></span>
          <span class="gpin-dot"></span>
        </div>
        <div class="gpin-numpad" id="gpin-numpad" role="group" aria-label="Number pad">
          ${[1,2,3,4,5,6,7,8,9].map(n =>
            `<button class="gpin-key" data-digit="${n}" aria-label="${n}">${n}</button>`
          ).join('')}
          <div aria-hidden="true"></div>
          <button class="gpin-key" data-digit="0" aria-label="0">0</button>
          <button class="gpin-key gpin-key--del" id="gpin-del" aria-label="Delete">
            <i data-lucide="delete" width="20" height="20"></i>
          </button>
        </div>
      </div>
    `;
    return el;
  }

  // ── Init ───────────────────────────────────────────────────────
  /**
   * @tag SYSTEM
   */
  async function init() {
    const pinSet = await _checkStatus();

    _overlay = _buildOverlay();
    document.body.appendChild(_overlay);

    _titleEl    = document.getElementById('gpin-title');
    _subtitleEl = document.getElementById('gpin-subtitle');
    _dots       = Array.from(_overlay.querySelectorAll('.gpin-dot'));

    if (pinSet) {
      _mode = 'verify';
      _setTitle('Welcome back, GIA!', 'Enter your secret code');
    } else {
      _mode = 'setup';
      _setTitle('Create your secret code', 'Choose 4 numbers');
    }

    // Bind numpad clicks
    _overlay.querySelector('#gpin-numpad').addEventListener('click', e => {
      const key = e.target.closest('[data-digit]');
      if (key) { _handleDigit(key.dataset.digit); return; }
      if (e.target.closest('#gpin-del')) _handleDelete();
    });

    // Keyboard support
    document.addEventListener('keydown', _onKeyDown);

    // Lucide icons
    if (window.lucide) lucide.createIcons({ el: _overlay });
  }

  function _onKeyDown(e) {
    if (!_overlay) return;
    if (e.key >= '0' && e.key <= '9') { _handleDigit(e.key); return; }
    if (e.key === 'Backspace' || e.key === 'Delete') { _handleDelete(); return; }
  }

  return { init };
})();

// ── Bootstrap ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Parent mode: skip PIN entirely
  if (new URLSearchParams(window.location.search).get('parent') === '1') {
    window.GIA_PIN_MODE = false;
    return;
  }
  GIAPin.init();
});
