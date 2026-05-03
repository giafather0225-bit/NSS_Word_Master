/* ================================================================
   math-spaced-review.js — Math spaced review session UI
   Section: Math
   Dependencies: core.js (toast), bundle-a (review.js done overlay hook)
   API endpoints:
     GET  /api/math/spaced-review/today
     POST /api/math/spaced-review/submit
   ================================================================ */

/** @tag MATH @tag REVIEW */
(function () {
  'use strict';

  // ── State ────────────────────────────────────────────────────────
  let _problems = [];
  let _currentIdx = 0;
  let _answers = [];
  let _overlay = null;

  // ── Lifecycle ────────────────────────────────────────────────────

  /**
   * @tag MATH @tag REVIEW
   * Load due problems from backend. Caches count for badge display.
   */
  async function loadDueProblems() {
    try {
      const res = await fetch('/api/math/spaced-review/today');
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data.problems) ? data.problems : [];
    } catch { return []; }
  }

  /**
   * @tag MATH @tag REVIEW
   * Start a math spaced review session. Creates full-screen overlay.
   */
  async function startMathReview() {
    if (_overlay) return; // already open
    _problems = await loadDueProblems();
    if (!_problems.length) {
      _showToast('No math reviews due today.');
      return;
    }
    _currentIdx = 0;
    _answers = [];
    _buildOverlay();
    _showProblem(_currentIdx);
  }

  // ── Overlay ──────────────────────────────────────────────────────

  function _buildOverlay() {
    const el = document.createElement('div');
    el.id = 'math-sr-overlay';
    el.className = 'math-sr-overlay';
    el.innerHTML = `
      <div class="math-sr-panel">
        <div class="math-sr-header">
          <span class="math-sr-title">Math Review</span>
          <span class="math-sr-progress" id="math-sr-progress"></span>
        </div>
        <div class="math-sr-body" id="math-sr-body"></div>
      </div>
    `;
    document.body.appendChild(el);
    _overlay = el;
  }

  function _removeOverlay() {
    if (_overlay) { _overlay.remove(); _overlay = null; }
  }

  // ── Problem rendering ─────────────────────────────────────────────

  function _showProblem(idx) {
    if (idx >= _problems.length) {
      _submitSession();
      return;
    }
    const p = _problems[idx];
    const prog = document.getElementById('math-sr-progress');
    if (prog) prog.textContent = `${idx + 1} / ${_problems.length}`;

    const body = document.getElementById('math-sr-body');
    if (!body) return;

    const lessonChip = _esc(p.lesson_title || p.lesson_id || '');
    const stem = _esc(p.stem || '');
    const isChoice = p.choices && p.choices.length > 0;

    let answersHtml = '';
    if (isChoice) {
      answersHtml = `<div class="math-sr-choices" id="math-sr-choices">` +
        p.choices.map((c, i) => {
          const letter = String.fromCharCode(65 + i);
          const label = c.includes(')') ? c.split(')').slice(1).join(')').trim() : c.trim();
          return `<button class="math-sr-choice" data-letter="${letter}" data-text="${_esc(label)}">${_esc(c)}</button>`;
        }).join('') +
        `</div>`;
    } else {
      answersHtml = `
        <div class="math-sr-short">
          <input id="math-sr-input" class="math-sr-input" type="text"
                 placeholder="Your answer" autocomplete="off" />
          <button class="math-btn-primary" id="math-sr-check">Check</button>
        </div>
      `;
    }

    body.innerHTML = `
      <div class="math-sr-lesson-chip">${lessonChip}</div>
      <div class="math-sr-stem">${stem}</div>
      ${answersHtml}
      <div class="math-sr-feedback hidden" id="math-sr-feedback"></div>
    `;

    if (isChoice) {
      body.querySelectorAll('.math-sr-choice').forEach(btn => {
        btn.addEventListener('click', () => _gradeChoice(p, btn.dataset.letter, btn.dataset.text, idx));
      });
    } else {
      const input = body.querySelector('#math-sr-input');
      const checkBtn = body.querySelector('#math-sr-check');
      if (checkBtn) checkBtn.addEventListener('click', () => {
        _gradeShort(p, input ? input.value : '', idx);
      });
      if (input) input.addEventListener('keydown', e => {
        if (e.key === 'Enter') _gradeShort(p, input.value, idx);
      });
      if (input) setTimeout(() => input.focus(), 80);
    }
  }

  function _gradeChoice(p, letter, text, idx) {
    const correct = (p.correct_answer || '').trim().toUpperCase();
    const isCorrect = letter.toUpperCase() === correct;
    _recordAnswer(p, isCorrect, letter);
    _showFeedback(p, isCorrect, p.answer_display || correct, idx);
  }

  function _gradeShort(p, userAnswer, idx) {
    const ua = (userAnswer || '').trim();
    const ca = (p.correct_answer || '').trim();
    const isCorrect = ua.toLowerCase() === ca.toLowerCase()
      || (parseFloat(ua) === parseFloat(ca) && !isNaN(parseFloat(ua)));
    _recordAnswer(p, isCorrect, ua);
    _showFeedback(p, isCorrect, p.answer_display || ca, idx);
  }

  function _recordAnswer(p, isCorrect, userAnswer) {
    _answers.push({
      lesson_id: p.lesson_id,
      unit_id: p.unit_id,
      grade: p.grade,
      problem_id: p.problem_id,
      user_answer: String(userAnswer),
    });
  }

  function _showFeedback(p, isCorrect, correctDisplay, idx) {
    // Disable all answer inputs
    const body = document.getElementById('math-sr-body');
    if (body) {
      body.querySelectorAll('.math-sr-choice, #math-sr-check, #math-sr-input').forEach(el => {
        el.disabled = true;
      });
      // Highlight correct choice
      body.querySelectorAll('.math-sr-choice').forEach(btn => {
        if (btn.dataset.letter === (p.correct_answer || '').trim().toUpperCase()) {
          btn.classList.add('is-correct');
        } else if (btn.disabled && btn.classList.contains('selected')) {
          btn.classList.add('is-wrong');
        }
      });
    }

    const fb = document.getElementById('math-sr-feedback');
    if (!fb) return;
    fb.classList.remove('hidden');
    const explanation = p.explanation || '';
    fb.innerHTML = isCorrect
      ? `<div class="math-sr-fb-correct">Correct! ${_esc(explanation)}</div>`
      : `<div class="math-sr-fb-wrong">The answer is <strong>${_esc(correctDisplay)}</strong>. ${_esc(explanation)}</div>`;

    const nextBtn = document.createElement('button');
    nextBtn.className = 'math-btn-primary math-sr-next';
    nextBtn.textContent = idx + 1 < _problems.length ? 'Next' : 'Finish';
    nextBtn.addEventListener('click', () => _showProblem(idx + 1));
    fb.appendChild(nextBtn);
    setTimeout(() => nextBtn.focus(), 50);
  }

  // ── Submit + complete ─────────────────────────────────────────────

  async function _submitSession() {
    const body = document.getElementById('math-sr-body');
    if (body) body.innerHTML = '<div class="math-sr-loading">Saving results...</div>';

    let xpEarned = 0;
    let updatedLessons = [];

    try {
      const res = await fetch('/api/math/spaced-review/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: _answers }),
      });
      if (res.ok) {
        const data = await res.json();
        xpEarned = data.xp_earned || 0;
        updatedLessons = data.lessons_updated || [];
      }
    } catch { /* show done anyway */ }

    _showComplete(xpEarned, updatedLessons);
  }

  function _showComplete(xpEarned, updatedLessons) {
    const body = document.getElementById('math-sr-body');
    if (!body) return;

    const correct = _answers.filter((a, i) => {
      // Re-check correct count from problems list (we graded client-side)
      const p = _problems[i];
      if (!p) return false;
      const ca = (p.correct_answer || '').trim();
      const ua = (a.user_answer || '').trim();
      return ua.toUpperCase() === ca.toUpperCase()
        || (parseFloat(ua) === parseFloat(ca) && !isNaN(parseFloat(ua)));
    }).length;
    const total = _answers.length;

    const nextDates = updatedLessons.map(l => {
      const d = new Date(l.next_review_date);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    const nextDateText = nextDates.length
      ? `Next review: ${nextDates.join(', ')}`
      : '';

    body.innerHTML = `
      <div class="math-sr-complete">
        <div class="math-sr-complete-score">${correct} / ${total}</div>
        <div class="math-sr-complete-label">Math Review Complete</div>
        ${xpEarned ? `<div class="math-sr-complete-xp">+${xpEarned} XP</div>` : ''}
        ${nextDateText ? `<div class="math-sr-complete-next">${_esc(nextDateText)}</div>` : ''}
        <button class="math-btn-primary math-sr-done-btn" id="math-sr-done">Done</button>
      </div>
    `;

    const doneBtn = body.querySelector('#math-sr-done');
    if (doneBtn) doneBtn.addEventListener('click', () => {
      _removeOverlay();
      // Refresh home dashboard badge if available
      if (typeof renderTodayTasks === 'function') renderTodayTasks();
    });
  }

  // ── Hook: chain after English review done overlay ──────────────────

  /**
   * @tag MATH @tag REVIEW
   * Intercept the English review done-overlay close button.
   * If math reviews are due, auto-start math review after English review closes.
   */
  function _installReviewChainHook() {
    document.addEventListener('click', async function (e) {
      const closeBtn = e.target.closest('#review-done-close');
      if (!closeBtn) return;
      // Check if math review is due
      try {
        const res = await fetch('/api/math/spaced-review/count');
        if (!res.ok) return;
        const { count } = await res.json();
        if (count > 0) {
          // Small delay so the English overlay finishes closing
          setTimeout(() => startMathReview(), 350);
        }
      } catch { /* no-op */ }
    });
  }

  // ── Utility ──────────────────────────────────────────────────────

  function _esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function _showToast(msg) {
    if (typeof window.showToast === 'function') { window.showToast(msg); return; }
    const t = document.createElement('div');
    t.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:10px 20px;border-radius:8px;z-index:9999;font-size:14px;';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
  }

  // ── Init ──────────────────────────────────────────────────────────

  function _init() {
    _installReviewChainHook();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _init);
  } else {
    _init();
  }

  // Public API
  window.MathSpacedReview = { start: startMathReview, load: loadDueProblems };
})();
