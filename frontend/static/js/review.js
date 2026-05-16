/**
 * Today's Review — SM-2 flashcard (word → reveal → rate)
 * NSS Word Master Phase 2
 */
(function () {
  "use strict";

  let reviewWords = [];
  let currentIdx = 0;
  let sessionCorrect = 0;
  let sessionTotal = 0;
  let cardOverlay = null;
  let doneOverlay = null;
  let badgeTimer = null;
  let badgeInFlight = false;
  let openReviewInFlight = false;
  let submitInFlight = false;
  let _lastIslandData = null;

  const POS_MAP = {
    n:"noun", v:"verb", adj:"adjective", adv:"adverb", prep:"preposition",
    noun:"noun", verb:"verb", adjective:"adjective", adverb:"adverb",
    preposition:"preposition", conj:"conjunction", conjunction:"conjunction",
    pron:"pronoun", pronoun:"pronoun", interj:"interjection"
  };

  function escapeHtml(s) {
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  function reopenSidebar() {
    var sidebar = document.getElementById("sidebar");
    if (sidebar && sidebar.classList.contains("collapsed")) {
      sidebar.classList.remove("collapsed");
    }
  }

  function getPOS(extraData) {
    try {
      var extra = typeof extraData === "string" ? JSON.parse(extraData || "{}") : (extraData || {});
      var raw = (extra.pos || "").replace(/[.\s]/g, "").toLowerCase();
      return POS_MAP[raw] || raw || "";
    } catch (_) { return ""; }
  }

  /* ── Build flashcard overlay (word front → reveal back) ── */
  function buildCardOverlay() {
    if (document.getElementById("rv-card-overlay")) {
      cardOverlay = document.getElementById("rv-card-overlay");
      return;
    }
    cardOverlay = document.createElement("div");
    cardOverlay.id = "rv-card-overlay";
    cardOverlay.className = "rv-card-overlay";
    cardOverlay.innerHTML = [
      '<div class="rv-card-shell">',
      '  <div class="rv-card-header">',
      '    <span class="rv-progress" id="rv-progress"></span>',
      '    <button class="rv-close-btn" id="rv-close-btn" aria-label="End session">',
      '      <i data-lucide="x"></i>',
      '    </button>',
      '  </div>',
      '  <!-- FRONT -->',
      '  <div class="rv-front" id="rv-front">',
      '    <div class="rv-word" id="rv-word"></div>',
      '    <div class="rv-pos-pill" id="rv-pos-pill"></div>',
      '    <div class="rv-front-actions">',
      '      <button class="rv-listen-btn" id="rv-listen-btn" aria-label="Listen">',
      '        <i data-lucide="volume-2"></i>',
      '      </button>',
      '      <button class="rv-reveal-btn" id="rv-reveal-btn">',
      '        <i data-lucide="eye"></i> Show Answer',
      '      </button>',
      '    </div>',
      '  </div>',
      '  <!-- BACK -->',
      '  <div class="rv-back hidden" id="rv-back">',
      '    <div class="rv-word-sm" id="rv-word-sm"></div>',
      '    <div class="rv-pos-pill rv-pos-pill--sm" id="rv-pos-pill-sm"></div>',
      '    <div class="rv-definition" id="rv-definition"></div>',
      '    <div class="rv-example" id="rv-example"></div>',
      '    <div class="rv-divider"></div>',
      '    <p class="rv-rate-prompt">How well did you know this word?</p>',
      '    <div class="rv-rate-row">',
      '      <button class="rv-rate-btn rv-rate-again" data-quality="1">',
      '        <span class="rv-rate-label">Again</span>',
      '        <span class="rv-rate-days">&lt;1 min</span>',
      '      </button>',
      '      <button class="rv-rate-btn rv-rate-hard" data-quality="3">',
      '        <span class="rv-rate-label">Hard</span>',
      '        <span class="rv-rate-days">tomorrow</span>',
      '      </button>',
      '      <button class="rv-rate-btn rv-rate-good" data-quality="4">',
      '        <span class="rv-rate-label">Good</span>',
      '        <span class="rv-rate-days">3 days</span>',
      '      </button>',
      '      <button class="rv-rate-btn rv-rate-easy" data-quality="5">',
      '        <span class="rv-rate-label">Easy</span>',
      '        <span class="rv-rate-days">7 days</span>',
      '      </button>',
      '    </div>',
      '  </div>',
      '</div>'
    ].join("\n");
    document.body.appendChild(cardOverlay);
    if (typeof lucide !== "undefined") lucide.createIcons();

    document.getElementById("rv-close-btn").addEventListener("click", function() {
      cardOverlay.classList.remove("active");
      reopenSidebar();
      updateBadge();
    });

    document.getElementById("rv-listen-btn").addEventListener("click", function() {
      var word = document.getElementById("rv-word").textContent;
      if (word && typeof apiWordOnly === "function") apiWordOnly(word);
    });

    document.getElementById("rv-reveal-btn").addEventListener("click", revealBack);

    cardOverlay.querySelectorAll(".rv-rate-btn").forEach(function(btn) {
      btn.addEventListener("click", function(e) {
        var quality = parseInt(e.currentTarget.dataset.quality);
        submitRating(quality);
      });
    });
  }

  /* ── Build done overlay ── */
  function buildDoneOverlay() {
    if (document.getElementById("review-done-overlay")) {
      doneOverlay = document.getElementById("review-done-overlay");
      return;
    }
    doneOverlay = document.createElement("div");
    doneOverlay.id = "review-done-overlay";
    doneOverlay.className = "review-done-overlay";
    doneOverlay.innerHTML = [
      '<div class="review-done-content">',
      '  <div class="review-done-icon"><i data-lucide="check-circle"></i></div>',
      '  <h2>All Done!</h2>',
      '  <p id="review-done-summary"></p>',
      '  <button class="review-done-btn" id="review-done-close">Back to Study</button>',
      '</div>'
    ].join("\n");
    document.body.appendChild(doneOverlay);
    if (typeof lucide !== "undefined") lucide.createIcons();
    document.getElementById("review-done-close").addEventListener("click", function() {
      doneOverlay.classList.remove("active");
      if (typeof window._reviewHubOnClose === "function") {
        window._reviewHubOnClose();
      } else {
        reopenSidebar();
      }
      updateBadge();
    });
  }

  /* ── Fetch due words ── */
  async function fetchDueWords(source) {
    try {
      var url = "/api/review/today" + (source ? "?source=" + encodeURIComponent(source) : "");
      var res = await fetch(url);
      if (!res.ok) return [];
      var data = await res.json();
      return data.reviews || [];
    } catch (e) {
      console.error("Review fetch error:", e);
      return [];
    }
  }

  /* ── Badge ── */
  /** @tag REVIEW @tag SM2 — guarded against overlapping calls */
  async function updateBadge() {
    if (badgeInFlight) return;
    badgeInFlight = true;
    try {
      var count = 0;
      try {
        var res = await fetch("/api/review/hub-status");
        if (res.ok) {
          var data = await res.json();
          count = data.total_due || 0;
        }
      } catch (_) {}
      var badges = [
        document.getElementById("review-badge"),
        document.getElementById("section-card-review-badge")
      ];
      badges.forEach(function (badge) {
        if (!badge) return;
        if (count > 0) {
          badge.textContent = count;
          badge.style.display = "inline-block";
        } else {
          badge.style.display = "none";
        }
      });
    } finally {
      badgeInFlight = false;
    }
  }

  /** @tag REVIEW — pause/resume badge polling on tab visibility */
  function startBadgeTimer() {
    if (badgeTimer) return;
    badgeTimer = setInterval(updateBadge, 5 * 60 * 1000);
  }
  function stopBadgeTimer() {
    if (badgeTimer) { clearInterval(badgeTimer); badgeTimer = null; }
  }

  /* ── Open review session ── */
  /** @tag REVIEW — guarded against double-click opening two sessions */
  async function openReview(source) {
    if (openReviewInFlight) return;
    openReviewInFlight = true;
    try {
      buildCardOverlay();
      buildDoneOverlay();
      reviewWords = await fetchDueWords(source);
      currentIdx = 0;
      sessionCorrect = 0;
      sessionTotal = 0;

      var sidebar = document.getElementById("sidebar");
      if (sidebar && !sidebar.classList.contains("collapsed")) {
        sidebar.classList.add("collapsed");
      }

      if (reviewWords.length === 0) {
        document.getElementById("review-done-summary").textContent =
          "No words to review today. Great job!";
        doneOverlay.classList.add("active");
        return;
      }

      showNextCard();
    } finally {
      openReviewInFlight = false;
    }
  }

  /* ── Populate and show flashcard front ── */
  function showNextCard() {
    if (currentIdx >= reviewWords.length) {
      cardOverlay.classList.remove("active");
      showDone();
      return;
    }

    var item = reviewWords[currentIdx];
    var word = item.answer || item.word || "";
    var pos  = getPOS(item.extra_data);

    // Progress
    document.getElementById("rv-progress").textContent =
      (currentIdx + 1) + " / " + reviewWords.length;

    // Front
    document.getElementById("rv-word").textContent = word;
    var posFront = document.getElementById("rv-pos-pill");
    if (pos) { posFront.textContent = pos; posFront.style.display = ""; }
    else      { posFront.style.display = "none"; }

    // Back
    document.getElementById("rv-word-sm").textContent = word;
    var posBack = document.getElementById("rv-pos-pill-sm");
    if (pos) { posBack.textContent = pos; posBack.style.display = ""; }
    else     { posBack.style.display = "none"; }
    document.getElementById("rv-definition").textContent = item.question || "";
    var exEl = document.getElementById("rv-example");
    if (item.hint) {
      exEl.textContent = "“" + item.hint + "”";
      exEl.style.display = "";
    } else {
      exEl.style.display = "none";
    }

    // Reset to front view
    document.getElementById("rv-front").classList.remove("hidden");
    document.getElementById("rv-back").classList.add("hidden");
    cardOverlay.classList.add("active");
    if (typeof lucide !== "undefined") lucide.createIcons();
  }

  /* ── Flip to back ── */
  function revealBack() {
    document.getElementById("rv-front").classList.add("hidden");
    var back = document.getElementById("rv-back");
    back.classList.remove("hidden");
    back.classList.add("rv-back--reveal");
    setTimeout(function() { back.classList.remove("rv-back--reveal"); }, 350);
  }

  /* ── Submit rating ── */
  async function submitRating(quality) {
    if (submitInFlight) return;
    submitInFlight = true;
    var item = reviewWords[currentIdx];
    sessionTotal++;
    if (quality >= 3) sessionCorrect++;

    var isCorrect = quality >= 3;
    var attempts = quality <= 1 ? 3 : quality <= 3 ? 2 : 1;

    try {
      const res = await fetch("/api/review/result", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          review_id: item.review_id,
          is_correct: isCorrect,
          attempts: attempts
        })
      });
      if (res.ok) {
        try {
          const d = await res.json();
          if (d?.island) _lastIslandData = d.island;
        } catch (_) {}
      }
    } catch (e) {
      console.error("Review submit error:", e);
    } finally {
      submitInFlight = false;
    }

    currentIdx++;
    showNextCard();
  }

  /* ── Done ── */
  async function showDone() {
    var pct = sessionTotal > 0 ? Math.round((sessionCorrect / sessionTotal) * 100) : 0;
    document.getElementById("review-done-summary").textContent =
      sessionCorrect + " / " + sessionTotal + " correct (" + pct + "%)";
    doneOverlay.classList.add("active");

    if (typeof window._reviewHubOnDone === "function") {
      window._reviewHubOnDone({ correct: sessionCorrect, total: sessionTotal });
    }

    var islandSlot = doneOverlay.querySelector("#rv-island-update");
    if (!islandSlot) {
      islandSlot = document.createElement("div");
      islandSlot.id = "rv-island-update";
      var content = doneOverlay.querySelector(".review-done-content");
      if (content) content.appendChild(islandSlot);
    }
    if (typeof _appendIslandUpdate === "function") _appendIslandUpdate(islandSlot, _lastIslandData);
  }

  /* ── Init ── */
  function init() {
    var btn = document.getElementById("btn-review");
    if (btn) btn.addEventListener("click", openReview);
    updateBadge();
    startBadgeTimer();

    document.addEventListener("visibilitychange", function() {
      if (document.hidden) {
        stopBadgeTimer();
      } else {
        updateBadge();
        startBadgeTimer();
      }
    });
    window.addEventListener("pagehide", stopBadgeTimer);

    document.addEventListener("keydown", function(e) {
      var card = document.getElementById("rv-card-overlay");
      var isCardActive = card && card.classList.contains("active");

      if (e.key === "Escape") {
        if (isCardActive) {
          card.classList.remove("active");
          reopenSidebar();
          updateBadge();
          return;
        }
        var done = document.getElementById("review-done-overlay");
        if (done && done.classList.contains("active")) {
          done.classList.remove("active");
          reopenSidebar();
          updateBadge();
        }
        return;
      }

      if (!isCardActive) return;

      var frontVisible = !document.getElementById("rv-front").classList.contains("hidden");

      // Space / Enter → reveal when front is showing
      if ((e.key === " " || e.key === "Enter") && frontVisible) {
        e.preventDefault();
        revealBack();
        return;
      }

      // 1/2/3/4 → rate when back is showing
      if (!frontVisible && !submitInFlight) {
        var qualityMap = { "1": 1, "2": 3, "3": 4, "4": 5 };
        if (qualityMap[e.key] !== undefined) {
          submitRating(qualityMap[e.key]);
        }
      }
    });
  }

  window.openReview = openReview;

  window.ReviewModule = {
    updateBadge: updateBadge,
    registerLesson: async function(subject, textbook, lesson) {
      try {
        await fetch("/api/review/register-lesson", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({subject: subject, textbook: textbook, lesson: lesson})
        });
        updateBadge();
      } catch (e) {
        console.error("Register lesson error:", e);
      }
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
