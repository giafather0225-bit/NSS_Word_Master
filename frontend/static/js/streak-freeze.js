/* ================================================================
   streak-freeze.js — Home widget for the Daily Streak Freeze feature
   Section: Home / Streak
   Dependencies: core.js (apiFetchJSON), toast.js (window.toast optional)
   API endpoints: GET /api/streak/freeze/status, POST /api/streak/freeze
   ================================================================ */

/** @tag STREAK STREAK_FREEZE HOME */
(function () {
    const ROW_ID   = "streak-freeze-row";
    const COUNT_ID = "freeze-count";
    const BTN_ID   = "freeze-use-btn";
    const TAG_ID   = "freeze-frozen-tag";

    function applyState(state) {
        const row   = document.getElementById(ROW_ID);
        if (!row) return;
        const count = document.getElementById(COUNT_ID);
        const btn   = document.getElementById(BTN_ID);
        const tag   = document.getElementById(TAG_ID);

        const available = Number(state.available_count || 0);
        const frozen    = !!state.today_frozen;

        // Only show the row at all if the child either owns a shield or
        // has already frozen today — keeps Home tidy for the common case.
        if (!available && !frozen) {
            row.classList.add("hidden");
            return;
        }
        row.classList.remove("hidden");
        if (count) count.textContent = String(available);

        if (frozen) {
            if (btn) btn.classList.add("hidden");
            if (tag) tag.classList.remove("hidden");
        } else {
            if (tag) tag.classList.add("hidden");
            if (btn) {
                if (available > 0) btn.classList.remove("hidden");
                else btn.classList.add("hidden");
            }
        }
    }

    async function refresh() {
        try {
            const state = await apiFetchJSON("/api/streak/freeze/status");
            applyState(state);
        } catch (err) {
            console.warn("[streak-freeze] status load failed:", err.message || err);
        }
    }

    async function useFreeze() {
        const btn = document.getElementById(BTN_ID);
        if (btn) btn.disabled = true;
        try {
            const state = await apiFetchJSON("/api/streak/freeze", { method: "POST" });
            applyState(state);
            if (window.toast) window.toast("Today's streak is safe.");
            // Other home widgets read streak count — trigger their refresh
            // hook if it's available.
            if (typeof window.refreshHomeStats === "function") {
                try { window.refreshHomeStats(); } catch (_) {}
            }
        } catch (err) {
            const msg = (err && err.message) || "Couldn't use Streak Shield.";
            if (window.toast) window.toast(msg);
            else console.warn("[streak-freeze]", msg);
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    // Wire up once the DOM has the button.
    function init() {
        const btn = document.getElementById(BTN_ID);
        if (btn) btn.addEventListener("click", useFreeze);
        refresh();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    // Expose a refresh hook so other modules (e.g. after a Reward Shop
    // purchase) can ask the widget to reload its state.
    window.refreshStreakFreeze = refresh;
})();
