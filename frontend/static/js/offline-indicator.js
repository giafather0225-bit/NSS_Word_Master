/* ================================================================
   offline-indicator.js — SW registration + online/offline banner
   Section: System
   Dependencies: none
   API endpoints: none
   ================================================================ */

// ── Register Service Worker (idempotent) ───────────────────
/** @tag SYSTEM @tag OFFLINE */
(function registerSW() {
    if (!('serviceWorker' in navigator)) return;
    // Skip if another script on the page is already registering the same SW.
    if (navigator.serviceWorker.controller) return;
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .catch((err) => console.warn('[sw] register failed', err));
    });
})();

// ── Online/offline banner ──────────────────────────────────
/** @tag SYSTEM @tag OFFLINE */
(function offlineBanner() {
    const BANNER_ID = 'gia-offline-banner';

    const mount = () => {
        if (document.getElementById(BANNER_ID)) return;
        const el = document.createElement('div');
        el.id = BANNER_ID;
        el.style.cssText = [
            'position:fixed', 'left:50%', 'top:12px',
            'transform:translateX(-50%)',
            'background:var(--color-warning)', 'color:var(--color-warning-ink)',
            'padding:6px 14px', 'border-radius:9999px',
            'font-size:13px', 'font-weight:600',
            'box-shadow:0 4px 16px rgba(0,0,0,0.18)',
            'z-index:9999', 'display:none',
            'font-family:-apple-system,BlinkMacSystemFont,sans-serif',
        ].join(';');
        el.textContent = '⚡ Offline — showing cached content';
        document.body.appendChild(el);
    };

    const update = () => {
        const el = document.getElementById(BANNER_ID);
        if (!el) return;
        el.style.display = navigator.onLine ? 'none' : 'block';
    };

    const boot = () => { mount(); update(); };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
})();
