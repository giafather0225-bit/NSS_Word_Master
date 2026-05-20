/* ================================================================
   navigation-sidebar.js — Sidebar session-mode helpers.
   Section: English / Navigation
   Dependencies: navigation.js, child.js, core.js
   API endpoints: none
   Split from navigation.js (2026-05-20) when that file exceeded ~500 lines.
   ================================================================ */

// ─── Sidebar session helpers ──────────────────────────────────
/**
 * Return a human-readable "N / total left" string for the current stage.
 * @tag NAVIGATION SIDEBAR
 */
function wordsLeftDisplay() {
    if (!items.length) return "—";
    if (stage === STAGE.A) {
        const done = wmState.matched ? wmState.matched.size : 0;
        return `${items.length - done}/${items.length} left`;
    }
    if (stage === STAGE.PREVIEW) {
        const done = previewDoneMap ? previewDoneMap.size : 0;
        return `${items.length - done}/${items.length} left`;
    }
    if (stage === STAGE.EXAM) {
        if (!examQueue.length) return "—";
        const left = Math.max(0, examQueue.length - examIndex);
        return `${left}/${examQueue.length} left`;
    }
    const left = Math.max(0, items.length - stageIndex);
    return `${left}/${items.length} left`;
}

/**
 * Toggle keyboard-hint pill visibility based on current stage.
 * @tag NAVIGATION SIDEBAR
 */
function updateHints() {
    const container = $("sb-hints-container");
    if (!container) return;
    container.querySelectorAll(".kb[data-hint]").forEach(h => {
        const key = h.dataset.hint;
        let active = false;
        if (sessionActive) {
            if (key === "listen") active = true;
            if (key === "submit") active = stage !== STAGE.PREVIEW && stage !== STAGE.A;
            if (key === "next")   active = stage === STAGE.PREVIEW || stage === STAGE.A;
        }
        h.classList.toggle("kb-active", active);
    });
}

/**
 * Refresh the sidebar session-info rows (lesson, stage, progress, mistakes).
 * @tag NAVIGATION SIDEBAR
 */
function updateSessionSidebarInfo() {
    if (!sessionActive) return;
    const elLesson   = $("sb-info-lesson");
    const elStage    = $("sb-info-stage");
    const elProgress = $("sb-info-progress");
    const elWrong    = $("sb-info-wrong");
    const skipBtn    = $("sb-btn-skip");
    if (elLesson)   elLesson.textContent   = selectedLesson || "—";
    if (elStage)    elStage.textContent    = stageTitle();
    if (elProgress) elProgress.textContent = wordsLeftDisplay();
    if (elWrong) {
        const cnt = Object.keys(wrongMap).filter(k => wrongMap[k] > 0).length;
        elWrong.textContent = String(cnt);
        elWrong.classList.toggle("val-warn", cnt > 0);
    }
    if (skipBtn) skipBtn.classList.toggle("hidden", stage === STAGE.EXAM);
    updateHints();
}

/**
 * Wire the Listen and Skip buttons in the sidebar session panel.
 * @tag NAVIGATION SIDEBAR
 */
function wireSbSessionButtons() {
    const listenBtn = $("sb-btn-listen");
    const skipBtn   = $("sb-btn-skip");
    if (listenBtn) {
        listenBtn.onclick = async () => {
            const item = currentItem();
            if (item) await apiWordOnly(item.answer);
        };
    }
    if (skipBtn) {
        skipBtn.onclick = () => {
            if (stage === STAGE.EXAM) return;
            stageIndex++;
            if (stageIndex >= items.length) {
                advanceToNextStage();
            } else {
                renderStage();
            }
        };
    }
}

/**
 * Switch the sidebar into session mode (hide selection area, show info).
 * @tag NAVIGATION SIDEBAR
 */
function enterSessionSidebar() {
    const sel  = $("sb-selection-area");
    const info = $("sb-session-info");
    if (sel)  sel.classList.add("hidden");
    if (info) info.classList.remove("hidden");
    wireSbSessionButtons();
    updateSessionSidebarInfo();
}

/**
 * Switch the sidebar back to selection mode.
 * @tag NAVIGATION SIDEBAR
 */
function exitSessionSidebar() {
    const sel  = $("sb-selection-area");
    const info = $("sb-session-info");
    if (sel)  sel.classList.remove("hidden");
    if (info) info.classList.add("hidden");
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('collapsed');
    localStorage.removeItem('sb_collapsed');
    updateHints();
}

/**
 * Update the challenge-meta element (delegates to updateProgressPct).
 * @tag NAVIGATION
 */
function updateChallengeMeta_nav() {}
