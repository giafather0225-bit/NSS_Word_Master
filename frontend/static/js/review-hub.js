/* ================================================================
   review-hub.js — Review Hub full-screen overlay orchestrator
   Section: Review
   Dependencies: review-hub-cards.js (card builders, loaded first in bundle),
                 review.js (ReviewModule), math-spaced-review.js (MathSpacedReview),
                 home.js (renderTodayTasks)
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
  var _cklaDone = false;
  var _islandData = null;  // island gain from the final session-complete

  // ── DOM helper ────────────────────────────────────────────────────

  function _el(id) { return document.getElementById(id); }

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
      if (body) {
        body.innerHTML = '<div class="rh-load-error"><p>Could not load review status.</p><button class="rh-retry-btn" id="rh-retry-btn">Try again</button></div>';
        var retryBtn = body.querySelector("#rh-retry-btn");
        if (retryBtn) retryBtn.addEventListener("click", _loadStatus);
      }
      return;
    }

    // restore completed-today state so reopening the hub shows correct status
    if (_status.english && _status.english.completed_today) _englishDone = true;
    if (_status.math && _status.math.completed_today) _mathDone = true;
    if (_status.ckla && _status.ckla.completed_today) _cklaDone = true;

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
    body.appendChild(_rhBuildEnglishCard(_status, _englishDone, _startEnglish));

    // CKLA card (only when ckla words exist or completed today)
    var cklaDue = (_status.ckla && _status.ckla.due) || 0;
    if (cklaDue > 0 || _cklaDone) {
      body.appendChild(_rhBuildCklaCard(_status, _cklaDone, _startCkla));
    }

    // Math card
    body.appendChild(_rhBuildMathCard(_status, _mathDone, _startMath));

    // All-done banner (shown only when all are done at open time or after completion)
    if (_englishDone && _mathDone && (_cklaDone || cklaDue === 0)) {
      body.appendChild(_rhBuildAllDoneBanner(_islandData, close));
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
  }

  // ── Session starters ──────────────────────────────────────────────

  function _startEnglish() {
    window._reviewHubOnDone = function (data) {
      _onEnglishDone(data);
    };
    window._reviewHubOnClose = function () {
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

  function _startCkla() {
    window._reviewHubOnDone = function (data) {
      _onCklaDone(data);
    };
    window._reviewHubOnClose = function () {
      if (_overlay) _overlay.classList.remove("hidden");
    };

    if (typeof openReview === "function") {
      openReview("ckla");
    }
  }

  // ── Session completion handlers ───────────────────────────────────

  async function _onEnglishDone(data) {
    // data = { correct, total } from review.js showDone hook
    var xpEarned = 0;
    var sessionIsland = null;
    try {
      var res = await fetch("/api/review/session-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "english" }),
      });
      if (res.ok) {
        var result = await res.json();
        xpEarned = result.xp_earned || 0;
        if (xpEarned > 0 && typeof window.showToast === "function") {
          window.showToast("+" + xpEarned + " XP — English review complete!", "success");
        }
        if (result.island) { _islandData = result.island; sessionIsland = result.island; }
        if (result.all_done) { _englishDone = true; _mathDone = true; }
      }
    } catch (e) {
      console.warn("[ReviewHub] session-complete english failed:", e);
    }

    _englishDone = true;
    _refreshCards();
    _showSessionResult("English Review", xpEarned, sessionIsland);

    // If math is also due, auto-scroll / highlight math card
    if (_status && _status.math && _status.math.due > 0 && !_mathDone) {
      var mathCard = _el("rh-math-card");
      if (mathCard) mathCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  async function _onCklaDone() {
    var xpEarned = 0;
    var sessionIsland = null;
    try {
      var res = await fetch("/api/review/session-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "ckla" }),
      });
      if (res.ok) {
        var result = await res.json();
        xpEarned = result.xp_earned || 0;
        if (xpEarned > 0 && typeof window.showToast === "function") {
          window.showToast("+" + xpEarned + " XP — CKLA review complete!", "success");
        }
        if (result.island) { _islandData = result.island; sessionIsland = result.island; }
      }
    } catch (e) {
      console.warn("[ReviewHub] session-complete ckla failed:", e);
    }

    _cklaDone = true;
    _refreshCards();
    _showSessionResult("CKLA Review", xpEarned, sessionIsland);
  }

  async function _onMathDone() {
    var xpEarned = 0;
    var sessionIsland = null;
    try {
      var res = await fetch("/api/review/session-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "math" }),
      });
      if (res.ok) {
        var result = await res.json();
        xpEarned = result.xp_earned || 0;
        if (xpEarned > 0 && typeof window.showToast === "function") {
          window.showToast("+" + xpEarned + " XP — Math review complete!", "success");
        }
        if (result.island) { _islandData = result.island; sessionIsland = result.island; }
      }
    } catch (e) {
      console.warn("[ReviewHub] session-complete math failed:", e);
    }

    _mathDone = true;
    _refreshCards();
    _showSessionResult("Math Review", xpEarned, sessionIsland);
  }

  // ── Per-session result card ───────────────────────────────────────

  function _showSessionResult(label, xpEarned, island) {
    var body = _el("rh-body");
    if (!body) return;

    // Remove any previous per-session result card
    var old = body.querySelector(".rh-session-result");
    if (old) old.remove();

    var card = _rhHtml("div", "rh-session-result", "");

    var iconEl = document.createElement("i");
    iconEl.setAttribute("data-lucide", "check-circle-2");
    card.appendChild(iconEl);

    var info = _rhHtml("div", "rh-session-result-info", "");
    info.appendChild(_rhHtml("div", "rh-session-result-title", label + " Complete"));
    if (xpEarned > 0) {
      info.appendChild(_rhHtml("div", "rh-session-result-xp", "+" + xpEarned + " XP earned"));
    }
    card.appendChild(info);

    // Island gain slot
    if (typeof _appendIslandUpdate === "function" && island) {
      var islandSlot = document.createElement("div");
      card.appendChild(islandSlot);
      setTimeout(function () { _appendIslandUpdate(islandSlot, island); }, 0);
    }

    // Insert at top of body so it's immediately visible
    body.insertBefore(card, body.firstChild);
    if (typeof lucide !== "undefined") lucide.createIcons();
  }

  // ── Refresh card area after one session finishes ──────────────────

  function _refreshCards() {
    var body = _el("rh-body");
    if (!body || !_status) return;

    // Re-render English card
    var oldEnglish = _el("rh-english-card");
    var newEnglish = _rhBuildEnglishCard(_status, _englishDone, _startEnglish);
    if (oldEnglish) body.replaceChild(newEnglish, oldEnglish);

    // Re-render CKLA card (only if it was rendered)
    var oldCkla = _el("rh-ckla-card");
    if (oldCkla) {
      body.replaceChild(_rhBuildCklaCard(_status, _cklaDone, _startCkla), oldCkla);
    }

    // Re-render Math card
    var oldMath = _el("rh-math-card");
    var newMath = _rhBuildMathCard(_status, _mathDone, _startMath);
    if (oldMath) body.replaceChild(newMath, oldMath);

    // Show all-done banner if all complete
    var cklaDue = (_status.ckla && _status.ckla.due) || 0;
    var allDone = _englishDone && _mathDone && (_cklaDone || cklaDue === 0);
    if (allDone) {
      var existing = body.querySelector(".rh-all-done");
      if (!existing) {
        // Per-session result card is superseded by the all-done banner
        var prevResult = body.querySelector(".rh-session-result");
        if (prevResult) prevResult.remove();
        body.appendChild(_rhBuildAllDoneBanner(_islandData, close));
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
    _cklaDone = false;

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
    delete window._reviewHubOnCklaDone;

    if (typeof renderTodayTasks === "function") renderTodayTasks();
  }

  window.ReviewHub = { open: open, close: close };
})();
