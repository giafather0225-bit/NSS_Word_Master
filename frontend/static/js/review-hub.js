/* ================================================================
   review-hub.js — Review Hub full-screen overlay orchestrator
   Section: Review
   Dependencies: review.js (ReviewModule), math-spaced-review.js (MathSpacedReview), home.js (renderTodayTasks)
   API endpoints:
     GET  /api/review/hub-status
     POST /api/review/session-complete
   ================================================================ */

(function () {
  "use strict";

  // ── State ─────────────────────────────────────────────────────────

  var _overlay = null;
  var _status = null;   // last hub-status response
  var _englishDone = false;
  var _mathDone = false;
  var _islandData = null;  // island gain from the final session-complete

  // ── DOM helpers ───────────────────────────────────────────────────

  function _el(id) { return document.getElementById(id); }

  function _html(tag, cls, inner) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (inner !== undefined) e.innerHTML = inner;
    return e;
  }

  // ── Build overlay DOM (once) ──────────────────────────────────────

  function _build() {
    var existing = _el("review-hub-overlay");
    if (existing) {
      _overlay = existing;
    } else {
      _overlay = document.createElement("div");
      _overlay.id = "review-hub-overlay";
      _overlay.className = "hidden";
      _overlay.setAttribute("role", "dialog");
      _overlay.setAttribute("aria-modal", "true");
      _overlay.setAttribute("aria-label", "Review Hub");
      document.body.appendChild(_overlay);
    }

    // Always (re)inject inner HTML — pre-existing div from child.html is empty
    _overlay.innerHTML = [
      '<div class="rh-header">',
      '  <div class="rh-header-icon"><i data-lucide="refresh-cw"></i></div>',
      '  <span class="rh-title">Review Hub</span>',
      '  <span class="rh-est-time" id="rh-est-time"></span>',
      '  <button class="rh-close-btn" id="rh-close-btn" aria-label="Close">',
      '    <i data-lucide="x"></i>',
      '  </button>',
      '</div>',
      '<div class="rh-body" id="rh-body">',
      '  <div class="rh-loading">Loading...</div>',
      '</div>',
    ].join("\n");

    _el("rh-close-btn").addEventListener("click", close);

    if (!_overlay._escListenerAttached) {
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && _overlay && !_overlay.classList.contains("hidden")) {
          close();
        }
      });
      _overlay._escListenerAttached = true;
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
  }

  // ── Fetch hub status ──────────────────────────────────────────────

  async function _loadStatus() {
    var body = _el("rh-body");
    if (body) body.innerHTML = '<div class="rh-loading">Loading...</div>';

    try {
      var res = await fetch("/api/review/hub-status");
      if (!res.ok) throw new Error("status " + res.status);
      _status = await res.json();
    } catch (e) {
      console.error("[ReviewHub] hub-status failed:", e);
      if (body) body.innerHTML = '<div class="rh-loading">Could not load review status. Please try again.</div>';
      return;
    }

    // P3: restore completed-today state so reopening the hub shows correct status
    if (_status.english && _status.english.completed_today) _englishDone = true;
    if (_status.math && _status.math.completed_today) _mathDone = true;

    _render();
  }

  // ── Render cards ──────────────────────────────────────────────────

  function _render() {
    var body = _el("rh-body");
    if (!body || !_status) return;

    var est = _el("rh-est-time");
    if (est) {
      est.textContent = _status.estimated_minutes
        ? "~" + _status.estimated_minutes + " min"
        : "";
    }

    body.innerHTML = "";

    // English card
    body.appendChild(_buildEnglishCard());

    // Math card
    body.appendChild(_buildMathCard());

    // All-done banner (shown only when both are done at open time or after completion)
    if (_englishDone && _mathDone) {
      body.appendChild(_buildAllDoneBanner());
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
  }

  function _buildEnglishCard() {
    var due = (_status.english && _status.english.due) || 0;
    var breakdown = (_status.english && _status.english.breakdown) || {};
    var isDone = _englishDone || due === 0;

    var card = _html("div", "rh-card rh-card--english" + (isDone ? " rh-card--done" : "") + (due === 0 && !_englishDone ? " rh-card--empty" : ""), "");
    card.id = "rh-english-card";

    // Icon
    var icon = _html("div", "rh-card-icon");
    var lucideIcon = document.createElement("i");
    lucideIcon.setAttribute("data-lucide", isDone ? "check-circle" : "book-open");
    icon.appendChild(lucideIcon);
    card.appendChild(icon);

    // Info
    var info = _html("div", "rh-card-info", "");

    var label = _html("div", "rh-card-label", "English Review");
    info.appendChild(label);

    var countEl = _html("div", "rh-card-count" + (isDone ? " rh-card-count--done" : ""), "");
    if (_englishDone) {
      countEl.textContent = "Completed";
    } else if (due === 0) {
      countEl.textContent = "Nothing due today";
    } else {
      countEl.textContent = due + " word" + (due === 1 ? "" : "s") + " due";
    }
    info.appendChild(countEl);

    // Source tags
    if (!_englishDone && due > 0 && Object.keys(breakdown).length > 0) {
      var tags = _html("div", "rh-tags", "");
      Object.keys(breakdown).forEach(function (src) {
        var n = breakdown[src];
        if (!n) return;
        var tag = _html("span", "rh-tag rh-tag--" + src, src.toUpperCase() + " " + n);
        tags.appendChild(tag);
      });
      info.appendChild(tags);
    }

    card.appendChild(info);

    // Action
    if (_englishDone) {
      var check = _html("div", "rh-done-checkmark", "");
      var ci = document.createElement("i");
      ci.setAttribute("data-lucide", "check");
      check.appendChild(ci);
      var span = document.createElement("span");
      span.textContent = "Done";
      check.appendChild(span);
      card.appendChild(check);
    } else {
      var btn = _html("button", "rh-start-btn", "Start");
      btn.disabled = due === 0;
      btn.addEventListener("click", _startEnglish);
      card.appendChild(btn);
    }

    return card;
  }

  function _buildMathCard() {
    var due = (_status.math && _status.math.due) || 0;
    var isDone = _mathDone || due === 0;

    var card = _html("div", "rh-card rh-card--math" + (isDone ? " rh-card--done" : "") + (due === 0 && !_mathDone ? " rh-card--empty" : ""), "");
    card.id = "rh-math-card";

    // Icon
    var icon = _html("div", "rh-card-icon");
    var lucideIcon = document.createElement("i");
    lucideIcon.setAttribute("data-lucide", isDone ? "check-circle" : "calculator");
    icon.appendChild(lucideIcon);
    card.appendChild(icon);

    // Info
    var info = _html("div", "rh-card-info", "");

    var label = _html("div", "rh-card-label", "Math Review");
    info.appendChild(label);

    var countEl = _html("div", "rh-card-count" + (isDone ? " rh-card-count--done" : ""), "");
    if (_mathDone) {
      countEl.textContent = "Completed";
    } else if (due === 0) {
      countEl.textContent = "Nothing due today";
    } else {
      countEl.textContent = due + " problem" + (due === 1 ? "" : "s") + " due";
    }
    info.appendChild(countEl);

    card.appendChild(info);

    // Action
    if (_mathDone) {
      var check = _html("div", "rh-done-checkmark", "");
      var ci = document.createElement("i");
      ci.setAttribute("data-lucide", "check");
      check.appendChild(ci);
      var span = document.createElement("span");
      span.textContent = "Done";
      check.appendChild(span);
      card.appendChild(check);
    } else {
      var btn = _html("button", "rh-start-btn", "Start");
      btn.disabled = due === 0;
      btn.addEventListener("click", _startMath);
      card.appendChild(btn);
    }

    return card;
  }

  function _buildAllDoneBanner() {
    var banner = _html("div", "rh-all-done", "");
    banner.innerHTML = [
      '<i data-lucide="star" class="rh-all-done-icon"></i>',
      '<div class="rh-all-done-title">All Reviews Complete!</div>',
      '<div class="rh-all-done-sub">Great job! Come back tomorrow for your next session.</div>',
      '<div id="rh-island-slot"></div>',
      '<button class="rh-back-btn" id="rh-all-done-back">Back to Home</button>',
    ].join("\n");

    // Attach island update card if available
    setTimeout(function () {
      var slot = document.getElementById("rh-island-slot");
      if (slot && typeof _appendIslandUpdate === "function") {
        _appendIslandUpdate(slot, _islandData);
      }
    }, 0);

    return banner;
  }

  // ── Session starters ──────────────────────────────────────────────

  function _startEnglish() {
    // Raise preview-modal above hub overlay so it's visible during word study
    var pm = document.getElementById("preview-modal");
    if (pm) pm.style.zIndex = "1200";

    function _resetPmZ() {
      if (pm) pm.style.zIndex = "";
    }

    window._reviewHubOnDone = function (data) {
      _resetPmZ();
      _onEnglishDone(data);
    };
    window._reviewHubOnClose = function () {
      _resetPmZ();
      if (_overlay) _overlay.classList.remove("hidden");
    };

    // Open English review (review.js public API or btn-review click)
    if (typeof openReview === "function") {
      openReview();
    } else {
      var btn = document.getElementById("btn-review");
      if (btn) btn.click();
    }
  }

  function _startMath() {
    window._reviewHubOnMathDone = function () {
      _onMathDone();
    };

    if (typeof MathSpacedReview !== "undefined") {
      MathSpacedReview.start();
    }
  }

  // ── Session completion handlers ───────────────────────────────────

  async function _onEnglishDone(data) {
    // data = { correct, total } from review.js showDone hook
    try {
      var res = await fetch("/api/review/session-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "english" }),
      });
      if (res.ok) {
        var result = await res.json();
        if (result.xp_earned > 0 && typeof window.showToast === "function") {
          window.showToast("+" + result.xp_earned + " XP — English review complete!", "success");
        }
        if (result.island) _islandData = result.island;
        if (result.all_done) {
          _englishDone = true;
          _mathDone = true;
        }
      }
    } catch (e) {
      console.warn("[ReviewHub] session-complete english failed:", e);
    }

    _englishDone = true;
    _refreshCards();

    // If math is also due, auto-scroll / highlight math card
    if (_status && _status.math && _status.math.due > 0 && !_mathDone) {
      var mathCard = _el("rh-math-card");
      if (mathCard) mathCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  async function _onMathDone() {
    try {
      var res = await fetch("/api/review/session-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "math" }),
      });
      if (res.ok) {
        var result = await res.json();
        if (result.xp_earned > 0 && typeof window.showToast === "function") {
          window.showToast("+" + result.xp_earned + " XP — Math review complete!", "success");
        }
        if (result.island) _islandData = result.island;
      }
    } catch (e) {
      console.warn("[ReviewHub] session-complete math failed:", e);
    }

    _mathDone = true;
    _refreshCards();
  }

  // ── Refresh card area after one session finishes ──────────────────

  function _refreshCards() {
    var body = _el("rh-body");
    if (!body || !_status) return;

    // Re-render English card
    var oldEnglish = _el("rh-english-card");
    var newEnglish = _buildEnglishCard();
    if (oldEnglish) body.replaceChild(newEnglish, oldEnglish);

    // Re-render Math card
    var oldMath = _el("rh-math-card");
    var newMath = _buildMathCard();
    if (oldMath) body.replaceChild(newMath, oldMath);

    // Show all-done banner if both complete
    if (_englishDone && _mathDone) {
      var existing = body.querySelector(".rh-all-done");
      if (!existing) {
        body.appendChild(_buildAllDoneBanner());
        var backBtn = _el("rh-all-done-back");
        if (backBtn) backBtn.addEventListener("click", close);
      }
      if (typeof renderTodayTasks === "function") renderTodayTasks();
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
  }

  // ── Public API ────────────────────────────────────────────────────

  /**
   * Open the Review Hub overlay.
   * @tag REVIEW @tag HOME_DASHBOARD
   */
  function open() {
    _build();
    _englishDone = false;
    _mathDone = false;

    _overlay.classList.remove("hidden");
    if (typeof lucide !== "undefined") lucide.createIcons();

    _loadStatus();
  }

  /**
   * Close the Review Hub overlay and refresh the home dashboard.
   * @tag REVIEW @tag HOME_DASHBOARD
   */
  function close() {
    if (_overlay) _overlay.classList.add("hidden");

    // Clean up hub callbacks so stray review.js / math-spaced-review.js calls are no-ops
    delete window._reviewHubOnDone;
    delete window._reviewHubOnClose;
    delete window._reviewHubOnMathDone;

    if (typeof renderTodayTasks === "function") renderTodayTasks();
  }

  window.ReviewHub = { open: open, close: close };
})();
