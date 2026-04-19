/* ================================================================
   toast.js — Lightweight non-blocking toast notifications.
   Section: System
   Dependencies: none (loaded early, before feature modules)
   API endpoints: none
   ================================================================ */

(function () {
    "use strict";

    let _container = null;

    /**
     * Lazy-create the toast stack container appended to <body>.
     * @tag SYSTEM
     */
    function _ensureContainer() {
        if (_container) return _container;
        _container = document.createElement("div");
        _container.className = "toast-stack";
        _container.setAttribute("role", "status");
        _container.setAttribute("aria-live", "polite");
        document.body.appendChild(_container);
        return _container;
    }

    /**
     * Show a non-blocking toast.
     * @param {string} msg   message text (will be text-content, no HTML)
     * @param {string} [type] one of "info" | "success" | "error" | "warn" (default "info")
     * @param {number} [ms]   auto-dismiss ms (default 3200; errors get 5000)
     * @tag SYSTEM
     */
    function toast(msg, type, ms) {
        if (!msg) return;
        type = type || "info";
        if (typeof ms !== "number") ms = (type === "error") ? 5000 : 3200;

        const root = _ensureContainer();
        const el = document.createElement("div");
        el.className = "toast toast-" + type;
        el.textContent = String(msg);
        root.appendChild(el);

        // Trigger enter transition on next frame
        requestAnimationFrame(() => el.classList.add("toast-show"));

        const remove = () => {
            el.classList.remove("toast-show");
            el.addEventListener("transitionend", () => el.remove(), { once: true });
            // Safety net: if transitionend never fires
            setTimeout(() => el.remove(), 400);
        };

        el.addEventListener("click", remove);
        setTimeout(remove, ms);
    }

    // Expose globally (vanilla JS shared-window pattern per CLAUDE.md)
    window.toast = toast;

    // ─── Global 422 interceptor ────────────────────────────────
    // Backend `_validation_error_handler` returns
    //   { "message": "Title is too long — …", "field": "title", "errors": [...] }
    // on HTTP 422. Wrap `fetch` so every caller gets a toast for free; the
    // original response still flows through so ok-checks / retries keep working.
    if (typeof window.fetch === "function" && !window.__toast_fetch_patched) {
        const _origFetch = window.fetch.bind(window);
        window.fetch = async function patchedFetch(...args) {
            const res = await _origFetch(...args);
            if (res && res.status === 422) {
                try {
                    const cloned = res.clone();
                    const data = await cloned.json();
                    if (data && typeof data.message === "string") {
                        toast(data.message, "warn", 4500);
                    }
                } catch (_) { /* non-JSON 422 — ignore */ }
            }
            return res;
        };
        window.__toast_fetch_patched = true;
    }
})();
