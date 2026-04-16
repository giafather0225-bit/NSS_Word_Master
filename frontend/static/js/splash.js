/* ================================================================
   splash.js — GIA Splash Screen
   Section: System
   Dependencies: none (runs before core.js)
   API endpoints: GET /api/xp/summary
   ================================================================ */

/**
 * GIA Splash Screen
 * - Time-based greeting (English)
 * - Data-driven daily message (API) + random cheer pool (fallback)
 * - Day-of-week gradient background
 * - Day-of-week sub text
 * - Logo → Coach card avatar fly transition
 * @tag HOME_DASHBOARD @tag SYSTEM
 */
const GIASplash = (() => {

  // ─── Random cheer pool ───
  const CHEER_POOL = [
    "Every word you learn is a superpower!",
    "Your brain grows stronger every day!",
    "Mistakes help you learn — don't be afraid!",
    "Today's effort is tomorrow's success!",
    "You're doing better than you think!",
    "Small steps every day lead to big results!",
    "Learning is your adventure — enjoy the journey!",
    "The more you practice, the easier it gets!",
    "You are braver than you believe!",
    "Great things take time — keep going!",
    "One new word a day = 365 words a year!",
    "Be proud of how far you've come!",
    "Curiosity is your greatest tool!",
    "You don't have to be perfect, just keep trying!",
    "Today is a perfect day to learn something new!",
    "Your hard work is paying off!",
    "Every expert was once a beginner!",
    "Believe in yourself — you've got this!",
    "The best time to learn is right now!",
    "You're building something amazing, word by word!"
  ];

  // ─── Day-of-week sub texts ───
  const DAY_TEXTS = [
    "Sunday — Relax and review!",
    "Monday — New week, new words!",
    "Tuesday — Keep the momentum!",
    "Wednesday — Halfway hero!",
    "Thursday — Almost there!",
    "Friday — Finish strong!",
    "Saturday — Weekend warrior!"
  ];

  /**
   * Get time-based greeting.
   * @tag HOME_DASHBOARD
   * @returns {string}
   */
  function _getGreeting() {
    const h = new Date().getHours();
    if (h < 12) return "Good morning, GIA!";
    if (h < 18) return "Good afternoon, GIA!";
    return "Good evening, GIA!";
  }

  /**
   * Build a data-driven message from API stats.
   * @tag XP @tag STREAK
   * @param {Object} data - XP summary data
   * @returns {string|null}
   */
  function _buildDataMessage(data) {
    const messages = [];

    // Streak-based
    if (data.streak_days !== undefined) {
      const streak = data.streak_days;
      if (streak === 0) {
        messages.push("Welcome back! Let's start a new streak today!");
      } else if (streak <= 4) {
        messages.push(`You're on a ${streak}-day streak! Keep it up!`);
      } else if (streak <= 9) {
        messages.push(`Amazing! ${streak} days in a row!`);
      } else {
        messages.push(`Incredible ${streak}-day streak! You're unstoppable!`);
      }
    }

    // Word count-based
    if (data.words_known > 100) {
      messages.push(`You already know ${data.words_known} words! Wow!`);
    } else if (data.words_known > 50) {
      messages.push(`${data.words_known} words learned — halfway to 100!`);
    } else if (data.words_known > 0) {
      messages.push(`${data.words_known} words and growing!`);
    }

    // XP-based
    if (data.total_xp > 1000) {
      messages.push(`Over ${Math.floor(data.total_xp / 100) * 100} XP earned! What a star!`);
    }

    // Level-based
    if (data.level && data.level > 1) {
      messages.push(`Level ${data.level} — you've come so far!`);
    }

    if (messages.length > 0) {
      return messages[Math.floor(Math.random() * messages.length)];
    }
    return null;
  }

  /**
   * Fetch splash data from XP summary API.
   * @tag XP @tag SYSTEM
   * @returns {Promise<Object|null>}
   */
  async function _fetchSplashData() {
    try {
      const res = await fetch('/api/xp/summary');
      if (!res.ok) throw new Error('API fail');
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Animate logo from splash center to coach card avatar position.
   * @tag HOME_DASHBOARD @tag SYSTEM
   * @param {HTMLElement} logoEl
   * @returns {Promise<void>}
   */
  function _flyLogoToCoach(logoEl) {
    return new Promise(resolve => {
      const coachIcon = document.querySelector('.coach-avatar');
      if (!coachIcon) {
        resolve();
        return;
      }

      const logoRect = logoEl.getBoundingClientRect();
      const targetRect = coachIcon.getBoundingClientRect();

      // Fix current position
      logoEl.style.position = 'fixed';
      logoEl.style.top = logoRect.top + 'px';
      logoEl.style.left = logoRect.left + 'px';
      logoEl.style.width = logoRect.width + 'px';
      logoEl.style.height = logoRect.height + 'px';
      logoEl.style.margin = '0';

      // Force reflow
      logoEl.offsetHeight;

      // Add fly class and set target position
      logoEl.classList.add('logo-fly');
      logoEl.style.top = targetRect.top + 'px';
      logoEl.style.left = targetRect.left + 'px';
      logoEl.style.width = targetRect.width + 'px';
      logoEl.style.height = targetRect.height + 'px';

      logoEl.addEventListener('transitionend', () => {
        logoEl.remove();
        // Activate glow ring on coach avatar
        const glowRing = document.querySelector('.coach-glow-ring');
        if (glowRing) glowRing.classList.add('active');
        resolve();
      }, { once: true });
    });
  }

  /**
   * Initialize and run the splash screen.
   * @tag HOME_DASHBOARD @tag SYSTEM
   */
  async function init() {
    const splash = document.getElementById('splash-screen');
    if (!splash) return;

    const day = new Date().getDay();
    splash.setAttribute('data-day', day);

    // Set greeting text
    const greetingEl = splash.querySelector('.splash-greeting');
    if (greetingEl) greetingEl.textContent = _getGreeting();

    // Set day-of-week text
    const dayTextEl = splash.querySelector('.splash-day-text');
    if (dayTextEl) dayTextEl.textContent = DAY_TEXTS[day];

    // Message: try API data, fallback to random pool
    const messageEl = splash.querySelector('.splash-message');
    const data = await _fetchSplashData();
    let msg = null;
    if (data) msg = _buildDataMessage(data);
    if (!msg) msg = CHEER_POOL[Math.floor(Math.random() * CHEER_POOL.length)];
    if (messageEl) messageEl.textContent = msg;

    // Ensure minimum 2.5s display
    const minTime = 2500;
    const startTime = performance.now();

    const elapsed = performance.now() - startTime;
    const remaining = Math.max(0, minTime - elapsed);
    await new Promise(r => setTimeout(r, remaining));

    // Hide loading dots
    const loader = splash.querySelector('.splash-loader');
    if (loader) loader.style.display = 'none';

    // Logo fly animation
    const logoEl = splash.querySelector('.splash-logo');
    if (logoEl) {
      await _flyLogoToCoach(logoEl);
    }

    // Exit splash
    splash.classList.add('splash-exit');
    setTimeout(() => {
      splash.remove();
    }, 700);
  }

  return { init };
})();

// Run on DOM ready — skip splash when returning from Folder Browser
document.addEventListener('DOMContentLoaded', () => {
  if (new URLSearchParams(window.location.search).get('parent') === '1') {
    const splash = document.getElementById('splash-screen');
    if (splash) splash.remove();
    return;
  }
  GIASplash.init();
});
