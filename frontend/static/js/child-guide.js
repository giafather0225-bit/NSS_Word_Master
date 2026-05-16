/* ================================================================
   child-guide.js — GIA onboarding guide & Help slides
   Section: System
   Dependencies: child-guide.css, lucide
   API endpoints: none (localStorage only)
   ================================================================ */

/**
 * Slide-based onboarding guide.
 * First visit → auto-opens after splash (mandatory, no close X).
 * Subsequent visits → opened by the Help button (closeable).
 * @tag HOME_DASHBOARD @tag SYSTEM
 */
const GIAGuide = (() => {

  const STORAGE_KEY = 'gia-guide-done';

  // ── Slide definitions ────────────────────────────────────────
  const SLIDES = [
    {
      theme:    'welcome',
      icon:     'star',
      title:    'Welcome to GIA Learning!',
      subtitle: 'Your secret learning adventure starts here',
      bullets:  [
        'This is your own private learning app',
        'Earn XP and level up every day you study',
        'Explore all the sections using the sidebar'
      ]
    },
    {
      theme:    'home',
      icon:     'home',
      title:    'Home Dashboard',
      subtitle: 'Your daily mission control',
      bullets:  [
        "See today's tasks and tick them off one by one",
        'Check your XP total and your study streak',
        'Read your daily message from your AI coach'
      ]
    },
    {
      theme:    'english',
      icon:     'book-open',
      title:    'English — CKLA',
      subtitle: 'Stories, words, and ideas',
      bullets:  [
        'Read exciting Grade 3 stories and passages',
        'Learn vocabulary words with quizzes and activities',
        'Answer questions to show what you understand'
      ]
    },
    {
      theme:    'math',
      icon:     'calculator',
      title:    'Math',
      subtitle: 'Step-by-step learning, your pace',
      bullets:  [
        'Work through lessons in Academy at your own speed',
        'Practice multiplication and addition in Fact Fluency',
        'Challenge yourself with Math Kangaroo problems'
      ]
    },
    {
      theme:    'diary',
      icon:     'book-heart',
      title:    "GIA's Diary",
      subtitle: 'Your thoughts, your stories, your world',
      bullets:  [
        'Write your daily journal — every entry earns XP',
        'Create stories in Free Writing with no rules',
        'Collect your best sentences from English lessons'
      ]
    },
    {
      theme:    'island',
      icon:     'map-pin',
      title:    'My Island',
      subtitle: 'Raise characters, build your world',
      bullets:  [
        'Take care of adorable island characters by studying',
        'Earn Lumi gems to buy food, evolutions, and decorations',
        'Unlock new zones and collect all the characters'
      ]
    },
    {
      theme:    'arcade',
      icon:     'gamepad-2',
      title:    'Arcade & Review',
      subtitle: 'Play games, remember everything',
      bullets:  [
        'Play Word Invaders, Crossword, Sudoku and more',
        'Review words and lessons with spaced repetition',
        'Earn bonus XP — there is a daily cap, so keep playing!'
      ]
    }
  ];

  // ── State ────────────────────────────────────────────────────
  let _current  = 0;
  let _helpMode = false; // true = closeable (help button); false = mandatory
  let _overlay  = null;

  // ── Build overlay ─────────────────────────────────────────────
  function _buildOverlay() {
    const el = document.createElement('div');
    el.id = 'gguide-overlay';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-label', 'GIA Guide');
    el.innerHTML = `
      <div class="gguide-modal">
        <div class="gguide-slide-wrap" id="gguide-slide-wrap">
          <div class="gguide-header" id="gguide-header">
            <button class="gguide-close" id="gguide-close" aria-label="Close guide">
              <i data-lucide="x" width="16" height="16"></i>
            </button>
            <div class="gguide-icon-wrap" id="gguide-icon-wrap">
              <i id="gguide-icon" width="28" height="28"></i>
            </div>
            <div class="gguide-slide-title"  id="gguide-title"></div>
            <div class="gguide-slide-subtitle" id="gguide-subtitle"></div>
          </div>
          <div class="gguide-body" id="gguide-body"></div>
        </div>
        <div class="gguide-progress" id="gguide-progress"></div>
        <div class="gguide-footer">
          <button class="gguide-btn-skip" id="gguide-skip">Skip</button>
          <button class="gguide-btn-next" id="gguide-next">Next</button>
          <button class="gguide-btn-done" id="gguide-done" style="display:none">Got it!</button>
        </div>
      </div>
    `;
    return el;
  }

  // ── Render a slide ────────────────────────────────────────────
  function _renderSlide(idx) {
    const slide = SLIDES[idx];
    const isLast = idx === SLIDES.length - 1;

    // Animate wrap
    const wrap = document.getElementById('gguide-slide-wrap');
    wrap.classList.remove('gguide-slide-wrap');
    void wrap.offsetWidth;
    wrap.classList.add('gguide-slide-wrap');

    // Theme class on modal
    const modal = _overlay.querySelector('.gguide-modal');
    modal.className = `gguide-modal gguide-theme--${slide.theme}`;

    // Icon
    const iconEl = document.getElementById('gguide-icon');
    iconEl.setAttribute('data-lucide', slide.icon);
    iconEl.setAttribute('width', '28');
    iconEl.setAttribute('height', '28');

    // Text
    document.getElementById('gguide-title').textContent    = slide.title;
    document.getElementById('gguide-subtitle').textContent = slide.subtitle;

    // Bullets
    const body = document.getElementById('gguide-body');
    body.innerHTML = slide.bullets.map(b => `
      <div class="gguide-bullet">
        <span class="gguide-bullet-dot"></span>
        <span>${b}</span>
      </div>
    `).join('');

    // Progress dots
    const prog = document.getElementById('gguide-progress');
    prog.innerHTML = SLIDES.map((_, i) => `
      <span class="gguide-prog-dot${i === idx ? ' active' : ''}"></span>
    `).join('');

    // Next / Done buttons
    document.getElementById('gguide-next').style.display = isLast ? 'none' : '';
    document.getElementById('gguide-done').style.display = isLast ? '' : 'none';

    // Close button (only in help mode)
    const closeBtn = document.getElementById('gguide-close');
    closeBtn.style.display = _helpMode ? 'flex' : 'none';

    // Skip button (only in help mode)
    document.getElementById('gguide-skip').style.display = _helpMode ? '' : 'none';

    // Rebuild Lucide icons for updated icon
    if (window.lucide) lucide.createIcons({ el: _overlay });
  }

  // ── Event handlers ────────────────────────────────────────────
  function _next() {
    if (_current < SLIDES.length - 1) {
      _current++;
      _renderSlide(_current);
    }
  }

  function _done() {
    localStorage.setItem(STORAGE_KEY, '1');
    _close();
  }

  function _close() {
    if (!_overlay) return;
    _overlay.classList.add('gguide-exit');
    setTimeout(() => {
      if (_overlay) {
        _overlay.remove();
        _overlay = null;
      }
    }, 280);
  }

  function _bindEvents() {
    document.getElementById('gguide-next').addEventListener('click', _next);
    document.getElementById('gguide-done').addEventListener('click', _done);
    document.getElementById('gguide-close').addEventListener('click', _done);
    document.getElementById('gguide-skip').addEventListener('click', _done);

    // Progress dots are clickable in help mode
    document.getElementById('gguide-progress').addEventListener('click', e => {
      if (!_helpMode) return;
      const dots = Array.from(e.currentTarget.querySelectorAll('.gguide-prog-dot'));
      const idx = dots.indexOf(e.target);
      if (idx >= 0) { _current = idx; _renderSlide(_current); }
    });

    // Keyboard: right/left arrow, Escape
    _overlay.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight') { _next(); return; }
      if (e.key === 'ArrowLeft' && _current > 0) { _current--; _renderSlide(_current); return; }
      if (e.key === 'Escape' && _helpMode) { _done(); }
    });
  }

  // ── Public API ────────────────────────────────────────────────
  /**
   * Always open the guide (help button path).
   * @tag HOME_DASHBOARD
   */
  function open() {
    if (_overlay) return; // already open
    _current  = 0;
    _helpMode = true;
    _overlay  = _buildOverlay();
    document.body.appendChild(_overlay);
    _renderSlide(0);
    _bindEvents();
    _overlay.querySelector('.gguide-modal').focus();
  }

  /**
   * Open only if first time (mandatory, no skip/close).
   * Called from child-pin.js after first PIN setup.
   * @tag SYSTEM
   */
  function openIfFirstTime() {
    if (localStorage.getItem(STORAGE_KEY)) return;
    if (_overlay) return;
    _current  = 0;
    _helpMode = false;
    _overlay  = _buildOverlay();
    document.body.appendChild(_overlay);
    _renderSlide(0);
    _bindEvents();
  }

  return { open, openIfFirstTime };
})();
window.GIAGuide = GIAGuide;
