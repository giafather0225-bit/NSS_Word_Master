/* ================================================================
   child-bootstrap.js — DOMContentLoaded entry point for the learner shell.
   Section: English / System
   Dependencies: child.js, navigation.js, navigation-sidebar.js,
                 navigation-dropdown.js, child-calendar.js,
                 child-keyboard.js, child-text.js, core.js
   API endpoints: none (wires existing functions)
   ================================================================ */

// ─── DOMContentLoaded bootstrap ──────────────────────────────
/**
 * Application entry point: wire all UI, restore state, load initial data.
 * @tag SYSTEM NAVIGATION
 */
document.addEventListener("DOMContentLoaded", async () => {
    // Textbook change handler
    const textbookSel = $("textbook-select");
    if (textbookSel) {
        textbookSel.addEventListener("change", async () => {
            const tb = textbookSel.value;
            if (!tb) return;
            sessionActive   = false;
            roadmapComplete = false;
            stage           = null;
            stageIndex      = 0;
            currentPhaseIndex  = 0;
            unlockedPhaseIndex = 0;
            spState.pass    = 1;
            wrongMap        = {};
            items           = [];
            wordVaultSet.clear();
            renderWordVault();
            renderIdleStage();
            updateRoadmapUI();
            updateProgressPct();
            updateChallengeMeta();
            await loadLessons(currentSubject, tb);
            refreshStartLabel();
            setStatus(`${tb} selected — choose a lesson.`);
        });
    }

    await loadTextbooks(currentSubject);

    // XP is now fetched from API via renderSummaryBar → _updateTopBarXP (home.js)

    wireTutorModal();

    const btnParent = $("btn-parent");
    if (btnParent) {
        // Phase 7: open in-app Parent Dashboard overlay (PIN verified via backend)
        btnParent.addEventListener("click", () => {
            if (typeof openParentPanel === "function") openParentPanel();
        });
    }

    // Restore state from localStorage
    sessionActive      = false;
    roadmapComplete    = allStagesDone();
    currentPhaseIndex  = 0;
    unlockedPhaseIndex = 0;
    stageIndex         = 0;
    stage              = null;
    spState.pass       = 1;

    const ex = $("btn-exam");
    if (ex) ex.disabled = !allStagesDone();

    renderIdleStage();
    updateRoadmapUI();
    updateProgressPct();
    updateChallengeMeta();
    renderWordVault();
    refreshStartLabel();
    if (typeof initWeeklyCalendar === "function") initWeeklyCalendar();

    const previewDone = getCompletedStages().has(STAGE.PREVIEW);
    if (previewDone && selectedLesson) {
        setStatus(`${selectedLesson} — Step 1 complete! Press Start to repeat.`);
    } else {
        setStatus("Select a lesson and press Start.");
    }

    // Word Match: flash animation on correct match
    (function() {
        const stageEl = document.getElementById('stage-content');
        if (!stageEl) return;
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                if (m.type !== 'attributes' || m.attributeName !== 'class') return;
                const el = m.target;
                if (!el.classList.contains('wm-word-btn') && !el.classList.contains('wm-meaning-btn')) return;
                if (!el.classList.contains('wm-matched')) return;
                el.classList.add('wm-flash');
                setTimeout(function() { el.classList.remove('wm-flash'); }, 400);
            });
        });
        observer.observe(stageEl, { subtree: true, attributes: true, attributeFilter: ['class'] });
    })();

    // Sidebar toggle
    const _sidebar = document.getElementById('sidebar');
    const _toggle  = document.getElementById('sidebar-toggle');
    if (_toggle && _sidebar) {
        _toggle.addEventListener('click', () => {
            if (document.body.classList.contains('ckla-active')) {
                if (typeof hideCKLAView === 'function') hideCKLAView();
            } else {
                _sidebar.classList.toggle('collapsed');
            }
        });
    }

    // Restore subject
    const savedSubject = localStorage.getItem('subject_mode') || 'eng';
    window.setSubject(savedSubject);

    // Init dropdown UIs
    initLessonDropdownUI();
    initTextbookDropdownUI();

    // OCR button
    initOcrButton();

    // Progress bar sync (ring + top bar fill)
    (function() {
        const fill  = document.getElementById('progress-ring-fill');
        const label = document.getElementById('progress-pct');
        const bar   = document.getElementById('top-progress-fill');
        const CIRC  = 2 * Math.PI * 16;

        function updateProgress() {
            const pct = parseFloat(label ? label.textContent : '0') || 0;
            if (fill) fill.style.strokeDashoffset = CIRC - (pct / 100) * CIRC;
            if (bar)  bar.style.width = pct + '%';
        }

        if (label) {
            new MutationObserver(updateProgress)
                .observe(label, { childList: true, characterData: true, subtree: true });
        }
        updateProgress();
    })();

    // Stars mirror disabled — top-bar XP now driven by API via home.js _updateTopBarXP
    // (sidebar star-count kept for legacy compat but no longer mirrors to top-bar)

    // fx-wrong propagation: stage → stage-card
    (function() {
        const stageObs = document.getElementById('stage');
        const card     = document.getElementById('stage-card');
        if (!stageObs || !card) return;
        new MutationObserver(() => {
            if (stageObs.classList.contains('fx-wrong')) {
                card.classList.remove('fx-wrong');
                void card.offsetWidth;
                card.classList.add('fx-wrong');
                card.addEventListener('animationend', () => card.classList.remove('fx-wrong'), { once: true });
            }
        }).observe(stageObs, { attributes: true, attributeFilter: ['class'] });
    })();

    // fx-correct → perfect banner
    (function() {
        const stageObs = document.getElementById('stage');
        const banner   = document.getElementById('perfect-banner');
        if (!stageObs || !banner) return;
        new MutationObserver(() => {
            if (stageObs.classList.contains('fx-correct')) {
                banner.classList.remove('fire');
                void banner.offsetWidth;
                banner.classList.add('fire');
            }
        }).observe(stageObs, { attributes: true, attributeFilter: ['class'] });
    })();

    // Keyboard shortcuts
    initKeyboardShortcuts();

    // Text-replacement observer
    const stageEl = document.getElementById('stage') || document.getElementById('stage-card');
    if (stageEl) {
        const textObserver = new MutationObserver(() => replaceDescriptionTexts());
        textObserver.observe(stageEl, { childList: true, subtree: true, characterData: true });
        replaceDescriptionTexts();
    }

    // Auto-open parent panel when redirected from Folder Browser (?parent=1)
    if (new URLSearchParams(window.location.search).get("parent") === "1") {
        history.replaceState({}, "", window.location.pathname);
        if (typeof openParentPanel === "function") openParentPanel();
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
});
