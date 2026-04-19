/**
 * Today's Review — SM-2 using Preview modal
 * NSS Word Master Phase 2
 */
(function () {
  "use strict";

  let reviewWords = [];
  let currentIdx = 0;
  let sessionCorrect = 0;
  let sessionTotal = 0;
  let ratingOverlay = null;
  let doneOverlay = null;
  let badgeTimer = null;
  let badgeInFlight = false;
  let openReviewInFlight = false;

  function escapeHtml(s) {
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  function reopenSidebar() {
    var sidebar = document.getElementById("sidebar");
    if (sidebar && sidebar.classList.contains("collapsed")) {
      sidebar.classList.remove("collapsed");
    }
  }

  /* ── Build rating overlay (fullscreen) ── */
  function buildRatingOverlay() {
    if (document.getElementById("review-rating-overlay")) return;
    ratingOverlay = document.createElement("div");
    ratingOverlay.id = "review-rating-overlay";
    ratingOverlay.className = "review-rating-overlay";

    var item = reviewWords[currentIdx] || {};
    ratingOverlay.innerHTML = [
      '<div class="review-rating-content">',
      '  <div class="review-rating-word" id="review-rating-word"></div>',
      '  <h3 class="review-rating-title">How well did you know this word?</h3>',
      '  <p class="review-rating-desc">Rate your confidence to move to the next word.<br>Press <strong>&times;</strong> to end the session.</p>',
      '  <button class="review-rating-close" id="review-rating-close">&times;</button>',
      '  <div class="review-rating-row">',
      '    <button class="review-rate-btn wrong" data-quality="1">',
      '      <span class="rate-label">Again</span>',
      '      <span class="rate-days">&lt;1 min</span>',
      '    </button>',
      '    <button class="review-rate-btn hard" data-quality="3">',
      '      <span class="rate-label">Hard</span>',
      '      <span class="rate-days">tomorrow</span>',
      '    </button>',
      '    <button class="review-rate-btn good" data-quality="4">',
      '      <span class="rate-label">Good</span>',
      '      <span class="rate-days">3 days</span>',
      '    </button>',
      '    <button class="review-rate-btn easy" data-quality="5">',
      '      <span class="rate-label">Easy</span>',
      '      <span class="rate-days">7 days</span>',
      '    </button>',
      '  </div>',
      '  <p class="review-rating-progress" id="review-rating-progress"></p>',
      '</div>'
    ].join("\n");
    document.body.appendChild(ratingOverlay);

    document.getElementById("review-rating-close").addEventListener("click", function() {
      ratingOverlay.classList.remove("active");
      reopenSidebar();
      updateBadge();
    });

    ratingOverlay.querySelectorAll(".review-rate-btn").forEach(function(btn) {
      btn.addEventListener("click", function(e) {
        var quality = parseInt(e.currentTarget.dataset.quality);
        ratingOverlay.classList.remove("active");
        submitRating(quality);
      });
    });
  }

  /* ── Build done overlay ── */
  function buildDoneOverlay() {
    if (document.getElementById("review-done-overlay")) return;
    doneOverlay = document.createElement("div");
    doneOverlay.id = "review-done-overlay";
    doneOverlay.className = "review-done-overlay";
    doneOverlay.innerHTML = [
      '<div class="review-done-content">',
      '  <div class="review-done-icon">✓</div>',
      '  <h2>All Done!</h2>',
      '  <p id="review-done-summary"></p>',
      '  <button class="review-done-btn" id="review-done-close">Back to Study</button>',
      '</div>'
    ].join("\n");
    document.body.appendChild(doneOverlay);
    document.getElementById("review-done-close").addEventListener("click", function() {
      doneOverlay.classList.remove("active");
      reopenSidebar();
      updateBadge();
    });
  }

  /* ── Convert API response to Preview-compatible item ── */
  function toPreviewItem(r) {
    return {
      id: r.study_item_id || r.review_id,
      question: r.question || "",
      answer: r.answer || r.word || "",
      hint: r.hint || "",
      extra_data: r.extra_data || "{}"
    };
  }

  /* ── Fetch due words ── */
  async function fetchDueWords() {
    try {
      var res = await fetch("/api/review/today");
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
      var words = await fetchDueWords();
      var badge = document.getElementById("review-badge");
      if (!badge) return;
      if (words.length > 0) {
        badge.textContent = words.length;
        badge.style.display = "inline-block";
      } else {
        badge.style.display = "none";
      }
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

  /* ── Ensure Preview modal is fully hidden ── */
  function hidePreviewModal() {
    var modal = document.getElementById("preview-modal");
    if (modal) {
      modal.classList.add("hidden");
      modal.hidden = true;
      modal.style.display = "none";
    }
  }

  /* ── Open review session ── */
  /** @tag REVIEW — guarded against double-click opening two sessions */
  async function openReview() {
    if (openReviewInFlight) return;
    openReviewInFlight = true;
    try {
    buildRatingOverlay();
    buildDoneOverlay();
    reviewWords = await fetchDueWords();
    currentIdx = 0;
    sessionCorrect = 0;
    sessionTotal = 0;

    /* Close sidebar */
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

  /* ── Show next card using Preview modal ── */
  function showNextCard() {
    if (currentIdx >= reviewWords.length) {
      showDone();
      return;
    }

    var reviewItem = reviewWords[currentIdx];
    var previewItem = toPreviewItem(reviewItem);

    /* Reset Preview modal display */
    var modal = document.getElementById("preview-modal");
    if (modal) modal.style.display = "";

    if (typeof window.openPreviewModal === "function") {
      window.openPreviewModal(previewItem, function(status) {
        /* Preview modal closed — hide it completely, then show rating */
        hidePreviewModal();
        showRating(reviewItem);
      });
    } else {
      console.error("openPreviewModal not found on window");
    }
  }

  /* ── Show rating overlay ── */
  function showRating(reviewItem) {
    var wordEl = document.getElementById("review-rating-word");
    if (wordEl) wordEl.textContent = reviewItem.answer || reviewItem.word || "";
    var progEl = document.getElementById("review-rating-progress");
    if (progEl) progEl.textContent = (currentIdx + 1) + " / " + reviewWords.length;
    ratingOverlay.classList.add("active");
  }

  /* ── Submit rating ── */
  async function submitRating(quality) {
    var item = reviewWords[currentIdx];
    sessionTotal++;
    if (quality >= 3) sessionCorrect++;

    var isCorrect = quality >= 3;
    var attempts = quality <= 1 ? 3 : quality <= 3 ? 2 : 1;

    try {
      await fetch("/api/review/result", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          review_id: item.review_id,
          is_correct: isCorrect,
          attempts: attempts
        })
      });
    } catch (e) {
      console.error("Review submit error:", e);
    }

    currentIdx++;
    showNextCard();
  }

  /* ── Done ── */
  function showDone() {
    var pct = sessionTotal > 0 ? Math.round((sessionCorrect / sessionTotal) * 100) : 0;
    document.getElementById("review-done-summary").textContent =
      sessionCorrect + " / " + sessionTotal + " correct (" + pct + "%)";
    doneOverlay.classList.add("active");
  }

  /* ── Init ── */
  function init() {
    var btn = document.getElementById("btn-review");
    if (btn) btn.addEventListener("click", openReview);
    updateBadge();
    startBadgeTimer();

    // Pause polling when tab hidden; resume + immediate refresh on visible.
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
      if (e.key !== "Escape") return;
      var rating = document.getElementById("review-rating-overlay");
      if (rating && rating.classList.contains("active")) {
        rating.classList.remove("active");
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
    });
  }

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
