/* ================================================================
   island-guide.js — In-lesson Island character cheer widget (L2)
   Section: Island / Navigation
   Dependencies: core.js (apiFetchJSON, STAGE), child.html (#island-guide
                 DOM injected once on first ensure())
   API endpoints: GET /api/island/active-guide
   ================================================================ */

/** @tag ISLAND NAVIGATION ENGLISH MATH DIARY */
(function () {
    const STORAGE_KEY = "ig_subject";
    const VISIBLE_MS  = 2000;     // total time the bubble is shown
    const FADE_MS     = 250;      // CSS transition duration (mirror in CSS)
    const IMG_PREFIX  = "/static/img/island/";

    let _state = null;            // { subject, name, image, stage, mood }
    let _hideTimer = null;

    // Per-stage messages. STAGE keys come from core.js (STAGE.PREVIEW = 'PREVIEW',
    // STAGE.A/B/C/D for steps 2~5). 'final_test' is our own bonus key.
    const _MSGS = {
        PREVIEW:      "All set!",
        A:            "Match made!",
        B:            "Filled in!",
        C:            "Spelled it!",
        D:            "Sentence ready!",
        final_test:   "Amazing!",
    };

    function _$(id) { return document.getElementById(id); }

    function _ensureDom() {
        if (_$("island-guide")) return;
        const host = _$("stage-card") || document.body;
        const root = document.createElement("div");
        root.id = "island-guide";
        root.className = "ig-root hidden";
        root.setAttribute("aria-hidden", "true");
        root.innerHTML = `
            <div class="ig-bubble hidden" id="ig-bubble" role="status" aria-live="polite"></div>
            <img class="ig-img" id="ig-img" alt="" />
        `;
        host.appendChild(root);
    }

    function _resolveImage(rel) {
        if (!rel) return "";
        if (rel.startsWith("/") || rel.startsWith("http")) return rel;
        return IMG_PREFIX + rel;
    }

    async function _loadGuide(subject) {
        try {
            const data = await apiFetchJSON(
                `/api/island/active-guide?subject=${encodeURIComponent(subject)}`
            );
            _state = data;
            const img = _$("ig-img");
            if (img) {
                img.src = _resolveImage(data.image);
                img.alt = data.nickname || data.name || "guide";
            }
            const root = _$("island-guide");
            if (root) {
                root.dataset.mood = data.mood || "happy";
                root.classList.remove("hidden");
            }
        } catch (err) {
            // Quiet failure — guide is optional, lesson must still work.
            console.warn("[island-guide] load failed:", err && err.message);
        }
    }

    function setSubject(subject) {
        if (!subject) return;
        try { localStorage.setItem(STORAGE_KEY, subject); } catch (_) {}
        _ensureDom();
        _loadGuide(subject);
    }

    function _showBubble(text) {
        const bubble = _$("ig-bubble");
        const img    = _$("ig-img");
        if (!bubble || !img) return;
        bubble.textContent = text;
        bubble.classList.remove("hidden");
        // Force reflow so the fade-in transition runs even if we just hid it.
        void bubble.offsetWidth;
        bubble.classList.add("ig-bubble--show");
        img.classList.remove("ig-bounce");
        void img.offsetWidth;
        img.classList.add("ig-bounce");

        if (_hideTimer) clearTimeout(_hideTimer);
        _hideTimer = setTimeout(() => {
            bubble.classList.remove("ig-bubble--show");
            // Wait for the fade-out before hiding for screen readers.
            setTimeout(() => bubble.classList.add("hidden"), FADE_MS);
            img.classList.remove("ig-bounce");
            _hideTimer = null;
        }, VISIBLE_MS);
    }

    /**
     * Trigger a cheer for a stage completion. Safe to call before the
     * guide has loaded — it'll just no-op until a subject is set.
     */
    function celebrate(stageKey) {
        if (!_state) return;
        const msg = _MSGS[stageKey] || _MSGS.PREVIEW;
        _ensureDom();
        _showBubble(msg);
    }

    function hide() {
        const root = _$("island-guide");
        if (root) root.classList.add("hidden");
    }

    // Auto-init from last known subject if the widget loads mid-session.
    function _autoInit() {
        _ensureDom();
        try {
            const last = localStorage.getItem(STORAGE_KEY);
            if (last) _loadGuide(last);
        } catch (_) {}
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", _autoInit);
    } else {
        _autoInit();
    }

    window.IslandGuide = { setSubject, celebrate, hide };
})();
