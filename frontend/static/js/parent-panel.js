/* ================================================================
   parent-panel.js — In-app Parent Dashboard overlay shell
   Section: Parent
   Dependencies: core.js
   API endpoints: /api/parent/verify-pin, /api/parent/day-off-requests,
                  /api/xp/summary
   Split: SVG/HTML chart helpers in parent-panel-charts.js
   ================================================================ */

// ─── PIN closure ──────────────────────────────────────────────
// Keeps the verified PIN off window so it isn't trivially readable from
// the browser console. Exposes only a setter + clearer + the fetch wrapper.
// parent-panel-settings.js also calls window._ppSetPin() after a successful
// PIN change to keep the in-memory value in sync.
(function () {
    let _pin = null;

    /** Store the verified parent PIN (called once after successful verify). @tag PARENT PIN */
    window._ppSetPin   = p  => { _pin = p; };
    /** Erase the verified PIN on panel close. @tag PARENT PIN */
    window._ppClearPin = () => { _pin = null; };

    /**
     * Authenticated fetch wrapper — injects X-Parent-Pin header automatically.
     * All parent mutation endpoints require this header for server-side auth.
     * @tag PARENT PIN
     */
    window._ppFetch = function (url, opts = {}) {
        const headers = Object.assign({}, opts.headers || {});
        if (_pin) headers["X-Parent-Pin"] = _pin;
        return fetch(url, Object.assign({}, opts, { headers }));
    };
}());

// ─── State ────────────────────────────────────────────────────
let _ppTab          = "home";
let _ppLiveInterval = null;

// ─── Tab registry ─────────────────────────────────────────────
const PP_TABS = [
    ["home",     "Home",     "home"],
    ["reading",  "Reading",  "book-open"],
    ["math",     "Math",     "calculator"],
    ["habits",   "Habits",   "flame"],
    ["island",   "Island",   "leaf"],
    ["settings", "Settings", "settings"],
];

// ─── Open / Close ─────────────────────────────────────────────

/** @tag PARENT PIN */
function openParentPanel() {
    _ppShowPinModal();
}

/** @tag PARENT */
function closeParentPanel() {
    const el = document.getElementById("parent-overlay");
    if (el) el.classList.add("hidden");
    _ppRemovePin();
    window._ppClearPin();
    window._ppDigits = "";
    _ppStopLivePoll();
}

// ─── PIN Modal ────────────────────────────────────────────────

/** @tag PARENT PIN */
function _ppShowPinModal() {
    const el = document.getElementById("parent-overlay");
    if (!el) return;
    el.classList.remove("hidden");
    el.innerHTML = `
        <div class="pp-pin-bg" id="pp-pin-bg">
            <div class="pp-pin-box">
                <div class="pp-pin-title">Parent Mode</div>
                <div class="pp-pin-sub">Enter your 4-digit PIN</div>
                <div class="pin-dots" id="pp-dots">
                    ${[0,1,2,3].map(() => `<div class="pin-dot"></div>`).join("")}
                </div>
                <div class="pin-error" id="pp-pin-err"></div>
                <div class="pin-pad">
                    ${[1,2,3,4,5,6,7,8,9].map(n =>
                        `<button class="pin-key" onclick="_ppPinKey('${n}')">${n}</button>`
                    ).join("")}
                    <button class="pin-key" aria-label="Clear" onclick="_ppPinKey('clear')"><i data-lucide="eraser" style="width:18px;height:18px"></i></button>
                    <button class="pin-key" onclick="_ppPinKey('0')">0</button>
                    <button class="pin-key delete" aria-label="Backspace" onclick="_ppPinKey('del')"><i data-lucide="delete" style="width:18px;height:18px"></i></button>
                </div>
                <button class="pp-btn secondary pp-pin-cancel" onclick="closeParentPanel()">Cancel</button>
            </div>
        </div>`;
    window._ppDigits = "";
    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** @tag PARENT PIN */
function _ppPinKey(key) {
    const digits = window._ppDigits || "";
    if (key === "del")        window._ppDigits = digits.slice(0, -1);
    else if (key === "clear") { window._ppDigits = ""; document.getElementById("pp-pin-err").textContent = ""; }
    else if (digits.length < 4) window._ppDigits = digits + key;
    _ppUpdateDots();
    if ((window._ppDigits || "").length === 4) setTimeout(_ppVerifyPin, 200);
}

/** @tag PARENT PIN */
function _ppUpdateDots() {
    const d = window._ppDigits || "";
    document.querySelectorAll(".pin-dot").forEach((el, i) => el.classList.toggle("filled", i < d.length));
}

/** @tag PARENT PIN */
async function _ppVerifyPin() {
    const enteredPin = window._ppDigits || "";
    try {
        const res = await fetch("/api/parent/verify-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pin: enteredPin }),
        });
        if (res.ok) {
            window._ppSetPin(enteredPin);
            _ppRemovePin();
            _ppRenderShell();
            _ppLoadTab("home");
        } else {
            window._ppDigits = "";
            _ppUpdateDots();
            const err = document.getElementById("pp-pin-err");
            if (err) err.textContent = "Wrong PIN. Try again.";
        }
    } catch (_) { window._ppDigits = ""; _ppUpdateDots(); }
}

/** @tag PARENT */
function _ppRemovePin() {
    const bg = document.getElementById("pp-pin-bg");
    if (bg) bg.remove();
}

// ─── PIN Re-confirmation for destructive actions ──────────────

/**
 * Show an inline PIN prompt overlay and call `onConfirmed()` only after the
 * user successfully re-enters the parent PIN.  Used for destructive actions
 * (XP rule reset, streak recalc) so an unattended open panel cannot be abused.
 *
 * @param {string} label     - Short description shown above the PIN pad.
 * @param {Function} onConfirmed - Zero-arg callback executed on correct PIN.
 * @tag PARENT PIN
 */
function _ppConfirmWithPin(label, onConfirmed) {
    // Remove any existing re-confirm overlay.
    const existing = document.getElementById("pp-reconfirm-bg");
    if (existing) existing.remove();

    const overlay = document.createElement("div");
    overlay.id = "pp-reconfirm-bg";
    overlay.style.cssText = [
        "position:fixed;inset:0;background:rgba(43,39,34,.55);",
        "display:flex;align-items:center;justify-content:center;z-index:3000;",
    ].join("");
    overlay.innerHTML = `
        <div class="pp-pin-box" style="background:var(--bg-card);padding:28px 24px;border-radius:var(--radius-xl);min-width:260px;text-align:center;box-shadow:var(--shadow-modal)">
            <div class="pp-pin-title">Confirm Action</div>
            <div class="pp-pin-sub" style="font-size:var(--font-size-sm);color:var(--text-secondary);margin-bottom:16px">${escapeHtml(label)}</div>
            <div class="pin-dots" id="pp-rc-dots">
                ${[0,1,2,3].map(() => `<div class="pin-dot"></div>`).join("")}
            </div>
            <div class="pin-error" id="pp-rc-err" style="min-height:18px"></div>
            <div class="pin-pad">
                ${[1,2,3,4,5,6,7,8,9].map(n =>
                    `<button class="pin-key" onclick="_ppRcKey('${n}')">${n}</button>`
                ).join("")}
                <button class="pin-key" aria-label="Clear" onclick="_ppRcKey('clear')"><i data-lucide="eraser" style="width:18px;height:18px"></i></button>
                <button class="pin-key" onclick="_ppRcKey('0')">0</button>
                <button class="pin-key delete" aria-label="Backspace" onclick="_ppRcKey('del')"><i data-lucide="delete" style="width:18px;height:18px"></i></button>
            </div>
            <button class="pp-btn secondary" style="margin-top:12px;width:100%" onclick="document.getElementById('pp-reconfirm-bg').remove()">Cancel</button>
        </div>`;
    document.body.appendChild(overlay);
    window._ppRcDigits = "";
    window._ppRcCallback = onConfirmed;
    if (typeof lucide !== "undefined") lucide.createIcons();
}
window._ppConfirmWithPin = _ppConfirmWithPin;

/** Handle keypad input for the re-confirm PIN overlay. @tag PARENT PIN */
function _ppRcKey(key) {
    const d = window._ppRcDigits || "";
    if (key === "del")        window._ppRcDigits = d.slice(0, -1);
    else if (key === "clear") { window._ppRcDigits = ""; const e = document.getElementById("pp-rc-err"); if (e) e.textContent = ""; }
    else if (d.length < 4)    window._ppRcDigits = d + key;

    // Update dots.
    const rc = window._ppRcDigits || "";
    document.querySelectorAll("#pp-rc-dots .pin-dot").forEach((el, i) => el.classList.toggle("filled", i < rc.length));

    if (rc.length === 4) setTimeout(_ppRcVerify, 200);
}
window._ppRcKey = _ppRcKey;

/** Verify the re-confirm PIN, then run the stored callback. @tag PARENT PIN */
async function _ppRcVerify() {
    const pin = window._ppRcDigits || "";
    try {
        const res = await fetch("/api/parent/verify-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pin }),
        });
        if (res.ok) {
            const bg = document.getElementById("pp-reconfirm-bg");
            if (bg) bg.remove();
            if (typeof window._ppRcCallback === "function") window._ppRcCallback();
        } else {
            window._ppRcDigits = "";
            document.querySelectorAll("#pp-rc-dots .pin-dot").forEach(el => el.classList.remove("filled"));
            const err = document.getElementById("pp-rc-err");
            if (err) err.textContent = "Wrong PIN.";
        }
    } catch (_) {
        window._ppRcDigits = "";
        document.querySelectorAll("#pp-rc-dots .pin-dot").forEach(el => el.classList.remove("filled"));
    }
}
window._ppRcVerify = _ppRcVerify;

// ─── Shell ────────────────────────────────────────────────────

/**
 * Standard empty-state markup used across all parent tabs.
 * @tag PARENT
 */
function _ppEmpty(icon, title, hint) {
    const t = escapeHtml(title || "Nothing here yet.");
    const h = hint ? escapeHtml(hint) : "";
    return `
        <div class="pp-empty">
            <i data-lucide="${icon || "inbox"}" class="pp-empty-icon"></i>
            <p class="pp-empty-title">${t}</p>
            ${h ? `<p class="pp-empty-hint">${h}</p>` : ""}
        </div>`;
}
window._ppEmpty = _ppEmpty;

/** @tag PARENT */
function _ppRenderShell() {
    const el = document.getElementById("parent-overlay");
    if (!el) return;

    const isRail  = localStorage.getItem("pp.sidebar") === "rail";
    const range   = localStorage.getItem("pp.range") || "weekly";
    const tabName = (PP_TABS.find(([k]) => k === _ppTab) || ["home", "Home"])[1];

    const navItems = PP_TABS.map(([key, label, icon]) => `
        <button class="pp-nav-item${key === _ppTab ? " active" : ""}"
                data-tab-key="${key}"
                onclick="_ppLoadTab('${key}')"
                title="${label}">
            <i data-lucide="${icon}" style="width:18px;height:18px;flex-shrink:0"></i>
            <span class="pp-nav-label">${label}</span>
            ${key === "habits" ? `<span class="pp-nav-badge" id="pp-habits-badge" style="display:none">0</span>` : ""}
        </button>`
    ).join("");

    el.innerHTML = `
        <aside class="pp-sidebar${isRail ? " pp-rail" : ""}" id="pp-sidebar">
            <div class="pp-brand">
                <div class="pp-brand-logo">G</div>
                <span class="pp-brand-text">Gia</span>
            </div>
            <nav class="pp-nav" style="flex:1;overflow-y:auto">
                ${navItems}
            </nav>
            <div class="pp-sidebar-foot">
                <button class="pp-nav-item" onclick="closeParentPanel()" title="Close">
                    <i data-lucide="log-out" style="width:18px;height:18px;flex-shrink:0"></i>
                    <span class="pp-nav-label">Close</span>
                </button>
            </div>
        </aside>
        <div class="pp-main">
            <header class="pp-topbar">
                <button class="pp-hamburger" onclick="_ppToggleSidebar()" aria-label="Toggle sidebar">
                    <i data-lucide="menu" style="width:18px;height:18px"></i>
                </button>
                <span class="pp-breadcrumb" id="pp-breadcrumb">${tabName}</span>
                <span class="pp-live-pill" id="pp-live-pill" style="display:none">
                    <span class="pp-live-dot"></span>Studying now
                </span>
                <div style="flex:1"></div>
                <div class="pp-seg" id="pp-seg" style="${_ppTab !== 'home' ? 'display:none' : ''}">
                    <button class="pp-seg-btn${range === "daily"   ? " active" : ""}" onclick="_ppSetRange('daily')">Daily</button>
                    <button class="pp-seg-btn${range === "weekly"  ? " active" : ""}" onclick="_ppSetRange('weekly')">Weekly</button>
                    <button class="pp-seg-btn${range === "monthly" ? " active" : ""}" onclick="_ppSetRange('monthly')">Monthly</button>
                </div>
            </header>
            <div class="pp-content" id="pp-body">
                <p class="pp-loading-center">Loading…</p>
            </div>
        </div>`;

    if (typeof lucide !== "undefined") lucide.createIcons();
    _ppApplySidebarWidth();
    _ppUpdateHabitsBadge();
    _ppStartLivePoll();
}

// ─── Sidebar toggle ───────────────────────────────────────────

/**
 * Apply sidebar width inline. CSS-cascade edits to the rail rule kept
 * appearing to fail because service-worker.js uses cacheFirst for /static/*
 * — when CSS was edited without re-running build.sh, the ?v= hash didn't
 * bump and the SW kept serving the old parent.css forever. Inline style
 * bypasses the SW cache entirely. Also forces narrow viewports to rail
 * (matches the @media (max-width: 1100px) intent).
 * @tag PARENT
 */
function _ppApplySidebarWidth() {
    const sb = document.getElementById("pp-sidebar");
    if (!sb) return;
    const isRail = sb.classList.contains("pp-rail")
                || window.matchMedia("(max-width: 1100px)").matches;
    const w = isRail ? "60px" : "232px";
    // Flexbox quirk: flex-basis defaults to `auto` which uses content max-width
    // (~232px from "Parent Dashboard" + Gia card). Setting flex shorthand
    // forces the flex item to honour the rail width.
    sb.style.setProperty("flex", `0 0 ${w}`, "important");
    sb.style.setProperty("width", w, "important");
    sb.style.setProperty("min-width", "0", "important");
}

/** @tag PARENT */
function _ppToggleSidebar() {
    const sb = document.getElementById("pp-sidebar");
    if (!sb) return;
    const nowRail = sb.classList.toggle("pp-rail");
    localStorage.setItem("pp.sidebar", nowRail ? "rail" : "expand");
    _ppApplySidebarWidth();
}

if (typeof window !== "undefined" && !window._ppSidebarResizeBound) {
    window.addEventListener("resize", _ppApplySidebarWidth);
    window._ppSidebarResizeBound = true;
}

// ─── Range segment ────────────────────────────────────────────

/** @tag PARENT */
function _ppSetRange(range) {
    localStorage.setItem("pp.range", range);
    document.querySelectorAll(".pp-seg-btn").forEach(b => {
        b.classList.toggle("active", b.textContent.toLowerCase() === range);
    });
    // Reload current tab with new range
    const body = document.getElementById("pp-body");
    if (body) _ppLoadTab(_ppTab);
}

/** Returns current range string ("daily" | "weekly" | "monthly"). @tag PARENT */
function _ppGetRange() {
    return localStorage.getItem("pp.range") || "weekly";
}
window._ppGetRange = _ppGetRange;

// ─── Live poll (studying-now indicator) ───────────────────────

/** @tag PARENT */
function _ppStartLivePoll() {
    _ppCheckLive();
    _ppLiveInterval = setInterval(_ppCheckLive, 30000);
}

/** @tag PARENT */
function _ppStopLivePoll() {
    if (_ppLiveInterval) { clearInterval(_ppLiveInterval); _ppLiveInterval = null; }
}

/** @tag PARENT */
async function _ppCheckLive() {
    try {
        const d = await apiFetchJSON("/api/xp/summary");
        const pill = document.getElementById("pp-live-pill");
        if (!pill) { _ppStopLivePoll(); return; }
        // Consider "studying now" if XP was earned in the last 10 minutes.
        // xp/summary returns {today_xp, last_activity_at (ISO)}
        let active = false;
        if (d && d.last_activity_at) {
            const diff = Date.now() - new Date(d.last_activity_at).getTime();
            active = diff < 10 * 60 * 1000;
        }
        pill.style.display = active ? "flex" : "none";
    } catch (_) {}
}

// ─── Habits badge (pending day-off count) ────────────────────

/** @tag PARENT DAY_OFF */
async function _ppUpdateHabitsBadge() {
    try {
        const d = await apiFetchJSON("/api/parent/day-off-requests");
        const pending = (d.requests || []).filter(r => r.status === "pending").length;
        const badge = document.getElementById("pp-habits-badge");
        if (!badge) return;
        badge.textContent = pending;
        badge.style.display = pending > 0 ? "flex" : "none";
    } catch (_) {}
}

// ─── Tab routing ──────────────────────────────────────────────

/** @tag PARENT */
async function _ppLoadTab(tab) {
    _ppTab = tab;
    document.querySelectorAll(".pp-nav-item[data-tab-key]").forEach(b =>
        b.classList.toggle("active", b.dataset.tabKey === tab)
    );
    const tabName = (PP_TABS.find(([k]) => k === tab) || ["", tab])[1];
    const bc = document.getElementById("pp-breadcrumb");
    if (bc) bc.textContent = tabName;
    const seg = document.getElementById("pp-seg");
    if (seg) seg.style.display = tab === "home" ? "" : "none";

    const body = document.getElementById("pp-body");
    if (!body) return;
    body.innerHTML = `<p class="pp-loading-center">Loading…</p>`;

    const missing = `<p style="color:var(--bad);padding:20px">Module not loaded.</p>`;
    switch (tab) {
        case "home":     if (typeof _ppHome        === "function") await _ppHome(body);        else body.innerHTML = missing; break;
        case "reading":  if (typeof _ppReading     === "function") await _ppReading(body);     else body.innerHTML = missing; break;
        case "math":     if (typeof _ppMathSummary === "function") await _ppMathSummary(body); else body.innerHTML = missing; break;
        case "habits":   if (typeof _ppHabits      === "function") await _ppHabits(body);      else body.innerHTML = missing; break;
        case "island":   if (typeof _ppIsland      === "function") await _ppIsland(body);      else body.innerHTML = missing; break;
        case "settings": if (typeof _ppSettings    === "function") await _ppSettings(body);    else body.innerHTML = missing; break;
        default: body.innerHTML = "<p>Coming soon.</p>";
    }
}

// SVG/HTML chart helpers (_ppSparkline, _ppRing, _ppStackBar, _ppBarChart, _ppTrend, _ppKpi)
// are in parent-panel-charts.js (loaded before this file in bundle-a).
