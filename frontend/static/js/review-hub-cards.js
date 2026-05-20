/* ================================================================
   review-hub-cards.js — Review Hub card builders (extracted from review-hub.js)
   Section: Review
   Dependencies: review-hub.js (calls these helpers; loaded first in bundle)
   ================================================================ */

/**
 * Shared DOM-creation helper for Review Hub card builders.
 * @tag REVIEW
 */
function _rhHtml(tag, cls, inner) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (inner !== undefined) e.innerHTML = inner;
    return e;
}

/**
 * Build the English Review card.
 * @tag REVIEW
 * @param {object} status  - hub-status response
 * @param {boolean} isDone - whether english session is complete
 * @param {Function} onStart - click handler for Start button
 */
function _rhBuildEnglishCard(status, isDone, onStart) {
    var due = (status.english && status.english.due) || 0;
    var breakdown = (status.english && status.english.breakdown) || {};

    var card = _rhHtml("div", "rh-card rh-card--english" + (isDone ? " rh-card--done" : "") + (due === 0 && !isDone ? " rh-card--empty" : ""), "");
    card.id = "rh-english-card";

    var icon = _rhHtml("div", "rh-card-icon");
    var lucideIcon = document.createElement("i");
    lucideIcon.setAttribute("data-lucide", isDone ? "check-circle" : "book-open");
    icon.appendChild(lucideIcon);
    card.appendChild(icon);

    var info = _rhHtml("div", "rh-card-info", "");
    info.appendChild(_rhHtml("div", "rh-card-label", "English Review"));

    var countEl = _rhHtml("div", "rh-card-count" + (isDone ? " rh-card-count--done" : ""), "");
    if (isDone) {
        countEl.textContent = "Completed";
    } else if (due === 0) {
        countEl.textContent = "Nothing due today";
    } else {
        countEl.textContent = due + " word" + (due === 1 ? "" : "s") + " due";
    }
    info.appendChild(countEl);

    if (!isDone && due > 0 && Object.keys(breakdown).length > 0) {
        var tags = _rhHtml("div", "rh-tags", "");
        Object.keys(breakdown).forEach(function (src) {
            var n = breakdown[src];
            if (!n) return;
            tags.appendChild(_rhHtml("span", "rh-tag rh-tag--" + src, src.toUpperCase() + " " + n));
        });
        info.appendChild(tags);
    }

    var acc7d = status.english && status.english.accuracy_7d;
    if (acc7d != null) {
        var accChip = _rhHtml("div", "rh-accuracy-chip", "");
        var accIcon = document.createElement("i");
        accIcon.setAttribute("data-lucide", "trending-up");
        accChip.appendChild(accIcon);
        var accLabel = document.createElement("span");
        accLabel.textContent = "7d accuracy: " + acc7d + "%";
        accChip.appendChild(accLabel);
        info.appendChild(accChip);
    }
    card.appendChild(info);

    if (isDone) {
        var check = _rhHtml("div", "rh-done-checkmark", "");
        var ci = document.createElement("i");
        ci.setAttribute("data-lucide", "check");
        check.appendChild(ci);
        var sp = document.createElement("span");
        sp.textContent = "Done";
        check.appendChild(sp);
        card.appendChild(check);
    } else {
        var btn = _rhHtml("button", "rh-start-btn", "Start");
        btn.disabled = due === 0;
        btn.addEventListener("click", onStart);
        card.appendChild(btn);
    }
    return card;
}

/**
 * Build the Math Review card.
 * @tag REVIEW @tag MATH
 * @param {object} status  - hub-status response
 * @param {boolean} isDone - whether math session is complete
 * @param {Function} onStart - click handler for Start button
 */
function _rhBuildMathCard(status, isDone, onStart) {
    var due = (status.math && status.math.due) || 0;

    var card = _rhHtml("div", "rh-card rh-card--math" + (isDone ? " rh-card--done" : "") + (due === 0 && !isDone ? " rh-card--empty" : ""), "");
    card.id = "rh-math-card";

    var icon = _rhHtml("div", "rh-card-icon");
    var lucideIcon = document.createElement("i");
    lucideIcon.setAttribute("data-lucide", isDone ? "check-circle" : "calculator");
    icon.appendChild(lucideIcon);
    card.appendChild(icon);

    var info = _rhHtml("div", "rh-card-info", "");
    info.appendChild(_rhHtml("div", "rh-card-label", "Math Review"));

    var countEl = _rhHtml("div", "rh-card-count" + (isDone ? " rh-card-count--done" : ""), "");
    if (isDone) {
        countEl.textContent = "Completed";
    } else if (due === 0) {
        countEl.textContent = "Nothing due today";
    } else {
        countEl.textContent = due + " problem" + (due === 1 ? "" : "s") + " due";
    }
    info.appendChild(countEl);

    var mathAcc7d = status.math && status.math.accuracy_7d;
    if (mathAcc7d != null) {
        var mathAccChip = _rhHtml("div", "rh-accuracy-chip", "");
        var mathAccIcon = document.createElement("i");
        mathAccIcon.setAttribute("data-lucide", "trending-up");
        mathAccChip.appendChild(mathAccIcon);
        var mathAccLabel = document.createElement("span");
        mathAccLabel.textContent = "7d accuracy: " + mathAcc7d + "%";
        mathAccChip.appendChild(mathAccLabel);
        info.appendChild(mathAccChip);
    }
    card.appendChild(info);

    if (isDone) {
        var check = _rhHtml("div", "rh-done-checkmark", "");
        var ci = document.createElement("i");
        ci.setAttribute("data-lucide", "check");
        check.appendChild(ci);
        var sp = document.createElement("span");
        sp.textContent = "Done";
        check.appendChild(sp);
        card.appendChild(check);
    } else {
        var btn = _rhHtml("button", "rh-start-btn", "Start");
        btn.disabled = due === 0;
        btn.addEventListener("click", onStart);
        card.appendChild(btn);
    }
    return card;
}

/**
 * Build the CKLA Review card.
 * @tag REVIEW @tag CKLA
 * @param {object} status  - hub-status response
 * @param {boolean} isDone - whether CKLA session is complete
 * @param {Function} onStart - click handler for Start button
 */
function _rhBuildCklaCard(status, isDone, onStart) {
    var due = (status.ckla && status.ckla.due) || 0;

    var card = _rhHtml("div", "rh-card rh-card--ckla" + (isDone ? " rh-card--done" : "") + (due === 0 && !isDone ? " rh-card--empty" : ""), "");
    card.id = "rh-ckla-card";

    var icon = _rhHtml("div", "rh-card-icon");
    var lucideIcon = document.createElement("i");
    lucideIcon.setAttribute("data-lucide", isDone ? "check-circle" : "graduation-cap");
    icon.appendChild(lucideIcon);
    card.appendChild(icon);

    var info = _rhHtml("div", "rh-card-info", "");
    info.appendChild(_rhHtml("div", "rh-card-label", "CKLA Review"));

    var countEl = _rhHtml("div", "rh-card-count" + (isDone ? " rh-card-count--done" : ""), "");
    if (isDone) {
        countEl.textContent = "Completed";
    } else if (due === 0) {
        countEl.textContent = "Nothing due today";
    } else {
        countEl.textContent = due + " word" + (due === 1 ? "" : "s") + " due";
    }
    info.appendChild(countEl);
    card.appendChild(info);

    if (isDone) {
        var check = _rhHtml("div", "rh-done-checkmark", "");
        var ci = document.createElement("i");
        ci.setAttribute("data-lucide", "check");
        check.appendChild(ci);
        var sp = document.createElement("span");
        sp.textContent = "Done";
        check.appendChild(sp);
        card.appendChild(check);
    } else {
        var btn = _rhHtml("button", "rh-start-btn", "Start");
        btn.disabled = due === 0;
        btn.addEventListener("click", onStart);
        card.appendChild(btn);
    }
    return card;
}

/**
 * Build the all-done banner shown when every review session is complete.
 * @tag REVIEW
 * @param {object|null} islandData - island gain data (may be null)
 * @param {Function} onClose       - handler for Back to Home button
 */
function _rhBuildAllDoneBanner(islandData, onClose) {
    var banner = _rhHtml("div", "rh-all-done", "");
    banner.innerHTML = [
        '<i data-lucide="star" class="rh-all-done-icon"></i>',
        '<div class="rh-all-done-title">All Reviews Complete!</div>',
        '<div class="rh-all-done-sub">Great job! Come back tomorrow for your next session.</div>',
        '<div id="rh-island-slot"></div>',
        '<button class="rh-back-btn" id="rh-all-done-back">Back to Home</button>',
    ].join("\n");

    var backBtn = banner.querySelector("#rh-all-done-back");
    if (backBtn) backBtn.addEventListener("click", onClose);

    setTimeout(function () {
        var slot = document.getElementById("rh-island-slot");
        if (slot && typeof _appendIslandUpdate === "function") {
            _appendIslandUpdate(slot, islandData);
        }
    }, 0);

    return banner;
}
