/* ================================================================
   update-banner.js — Floating "New version" badge + Update button
   Section: System
   Dependencies: none (loaded directly via child.html, before bundles)
   API endpoints: GET /api/system/check-update, POST /api/system/self-update

   UX flow:
     1. On DOMContentLoaded → GET /api/system/check-update
     2. If update_available → inject fixed badge top-right with version arrow
     3. Click badge → full-screen overlay + POST /api/system/self-update
     4. Wait ~12s then location.reload() — server restart serves new app
   ================================================================ */

(function () {
  "use strict";

  if (window.__updateBannerInit) return;
  window.__updateBannerInit = true;

  const CHECK_URL  = "/api/system/check-update";
  const APPLY_URL  = "/api/system/self-update";
  const RELOAD_MS  = 12000;

  function injectStyles() {
    if (document.getElementById("upd-banner-style")) return;
    const style = document.createElement("style");
    style.id = "upd-banner-style";
    style.textContent = `
      .upd-badge {
        position: fixed; top: 14px; right: 14px;
        z-index: 7000;
        display: inline-flex; align-items: center; gap: 8px;
        padding: 8px 14px;
        background: var(--color-primary, #E09AAE);
        color: var(--text-on-primary, #fff);
        border-radius: 9999px;
        font: 600 13px/1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        cursor: pointer; user-select: none;
        box-shadow: 0 4px 14px rgba(120, 90, 60, 0.25);
        animation: upd-pop 0.4s ease-out;
      }
      .upd-badge:hover { filter: brightness(1.08); }
      .upd-badge-ver { font-size: 11px; opacity: 0.85; font-family: ui-monospace, Menlo, monospace; }
      .upd-badge-icon { width: 16px; height: 16px; flex-shrink: 0; }

      .upd-overlay {
        position: fixed; inset: 0; z-index: 9500;
        background: rgba(43, 39, 34, 0.45);
        backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
        display: flex; align-items: center; justify-content: center;
        animation: upd-fade 0.2s ease-out;
      }
      .upd-card {
        background: var(--bg-card, #fff);
        color: var(--text-primary, #2B2722);
        padding: 36px 44px;
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(90, 65, 40, 0.25);
        display: flex; flex-direction: column; align-items: center; gap: 14px;
        max-width: 420px; text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      .upd-spinner {
        width: 48px; height: 48px;
        border: 4px solid var(--color-primary, #E09AAE);
        border-top-color: transparent;
        border-radius: 50%;
        animation: upd-spin 0.9s linear infinite;
      }
      .upd-card h2 { margin: 4px 0 0; font-size: 22px; font-weight: 700; }
      .upd-card p  { margin: 0; color: var(--text-secondary, #706659); font-size: 14px; line-height: 1.5; }
      .upd-card .ver { font-family: ui-monospace, Menlo, monospace; font-size: 12px; color: var(--text-hint, #A79A89); margin-top: 4px; }

      @keyframes upd-spin { to { transform: rotate(360deg); } }
      @keyframes upd-pop  { from { transform: translateY(-12px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
      @keyframes upd-fade { from { opacity: 0; } to { opacity: 1; } }
    `;
    document.head.appendChild(style);
  }

  function showBadge(localHead, remoteHead) {
    if (document.getElementById("upd-badge")) return;
    injectStyles();

    const badge = document.createElement("button");
    badge.id = "upd-badge";
    badge.className = "upd-badge";
    badge.type = "button";
    badge.title = "A new version of the app is available — click to update";
    badge.innerHTML = `
      <svg class="upd-badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="23 4 23 10 17 10"></polyline>
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
      </svg>
      <span>New version</span>
      <span class="upd-badge-ver">${escapeText(localHead)} → ${escapeText(remoteHead)}</span>
    `;
    badge.addEventListener("click", () => applyUpdate(localHead, remoteHead));
    document.body.appendChild(badge);
  }

  function showOverlay(localHead, remoteHead) {
    injectStyles();
    const overlay = document.createElement("div");
    overlay.className = "upd-overlay";
    overlay.id = "upd-overlay";
    overlay.innerHTML = `
      <div class="upd-card" role="dialog" aria-live="polite" aria-label="Updating GIA Learning App">
        <div class="upd-spinner"></div>
        <h2>Updating…</h2>
        <p>The app will reload automatically in a few seconds.</p>
        <div class="ver">${escapeText(localHead)} → ${escapeText(remoteHead)}</div>
      </div>`;
    document.body.appendChild(overlay);
  }

  function escapeText(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  async function applyUpdate(localHead, remoteHead) {
    const badge = document.getElementById("upd-badge");
    if (badge) badge.remove();
    showOverlay(localHead, remoteHead);

    try {
      await fetch(APPLY_URL, { method: "POST" });
    } catch (_) {
      // Server might have already restarted before responding — that's fine.
    }
    // Server lifespan + uvicorn restart takes ~5-10s. Pad to RELOAD_MS and reload.
    setTimeout(() => {
      window.location.reload();
    }, RELOAD_MS);
  }

  async function checkOnLoad() {
    try {
      const res = await fetch(CHECK_URL, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      if (data && data.update_available) {
        showBadge(data.local_head || "", data.remote_head || "");
      }
    } catch (_) { /* silent — offline or check failed */ }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", checkOnLoad);
  } else {
    checkOnLoad();
  }
})();
