/* ================================================================
   parent-panel.js — In-app Parent Dashboard overlay shell
   Section: Parent
   Dependencies: core.js, parent-panel-settings.js
   API endpoints: /api/parent/verify-pin, /api/parent/day-off-requests,
                  /api/parent/word-stats, /api/parent/stage-stats
   ================================================================ */

// ─── PIN closure ──────────────────────────────────────────────
// Keeps the verified PIN off window so it isn't trivially readable from
// the browser console. Exposes only a setter + clearer + the fetch wrapper.
// parent-settings.js also calls window._ppSetPin() after a successful
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
let _ppTab = "home";

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
    if (key === "del")   window._ppDigits = digits.slice(0, -1);
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
            const el = document.getElementById("parent-overlay");
            if (el) el.innerHTML = `<p class="pp-loading-center">Loading…</p>`;
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

// ─── Shell ────────────────────────────────────────────────────

const PP_TABS = [
    ["home",     "Home"],
    ["reading",  "Reading"],
    ["math",     "Math"],
    ["habits",   "Habits"],
    ["island",   "Island"],
    ["settings", "Settings"],
];

/**
 * Standard empty-state markup used across all parent tabs.
 * Pair the call site with lucide.createIcons() afterwards.
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
    const tabs = PP_TABS.map(([key, label]) =>
        `<button class="pp-nav-btn${key === _ppTab ? " active" : ""}" data-tab-key="${key}" onclick="_ppLoadTab('${key}')">${label}</button>`
    ).join("");
    el.innerHTML = `
        <div class="pp-header">
            <button class="pp-close" aria-label="Close" onclick="closeParentPanel()"><i data-lucide="arrow-left" style="width:20px;height:20px"></i></button>
            <span class="pp-title">Parent Dashboard</span>
        </div>
        <div class="pp-nav">${tabs}</div>
        <div id="pp-body"><p class="pp-loading-center">Loading…</p></div>`;
    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** @tag PARENT */
async function _ppLoadTab(tab) {
    _ppTab = tab;
    document.querySelectorAll(".pp-nav-btn").forEach(b => b.classList.toggle("active", b.dataset.tabKey === tab));
    const body = document.getElementById("pp-body");
    if (!body) return;
    body.innerHTML = `<p class="pp-loading-center">Loading…</p>`;
    const missing = `<p style="color:var(--color-error);padding:20px">Module not loaded.</p>`;
    switch (tab) {
        case "home":     if (typeof _ppHome        === "function") await _ppHome(body);        else body.innerHTML = missing; break;
        case "reading":  if (typeof _ppReading     === "function") await _ppReading(body);     else body.innerHTML = missing; break;
        case "math":     if (typeof _ppMathSummary === "function") await _ppMathSummary(body); else body.innerHTML = missing; break;
        case "habits":   await _ppHabits(body);   break;
        case "island":   if (typeof _ppIsland      === "function") await _ppIsland(body);      else body.innerHTML = missing; break;
        case "settings": await _ppSettings(body); break;
        default: body.innerHTML = "<p>Coming soon.</p>";
    }
}

// ─── Tab: Habits ──────────────────────────────────────────────

/** Streak + Goals + day-off approvals. @tag PARENT STREAK DAY_OFF */
async function _ppHabits(body) {
    body.innerHTML = `<p style="color:var(--text-secondary);font-size:14px;padding:20px 0">Loading…</p>`;

    let sd = null;
    try { sd = await apiFetchJSON("/api/parent/streak"); } catch (_) {}

    let streakHtml = "";
    if (sd && typeof _ppStreakCards === "function") {
        streakHtml =
            _ppStreakCards(sd) +
            `<div class="pp-grid-2 pp-habits-rule-row">
                <div>${_ppStreakRule(sd.rule)}</div>
                <div>${_ppStreakMilestones(sd)}</div>
            </div>` +
            _ppStreakCalendar(sd.last_30d || []);
    } else {
        streakHtml = `<p style="color:var(--color-error);padding:12px 0">Failed to load streak data.</p>`;
    }

    body.innerHTML = streakHtml + `
        <div class="pp-section-divider pp-section-divider--habits"></div>
        <div class="pp-section-title">Weekly Goals</div>
        <div id="pp-habits-goals"></div>
        <div class="pp-section-divider pp-section-divider--habits"></div>
        <div class="pp-section-title">Day Off Requests</div>
        <div id="pp-habits-dayoff"></div>`;

    const goalsEl  = document.getElementById("pp-habits-goals");
    const dayoffEl = document.getElementById("pp-habits-dayoff");
    if (goalsEl  && typeof _ppGoals   === "function") await _ppGoals(goalsEl);
    if (dayoffEl) await _ppDayOff(dayoffEl);
    if (typeof lucide !== "undefined") lucide.createIcons();
}

// ─── Tab: Settings ────────────────────────────────────────────
// Settings accordion + Test Mode + Island toggle live in parent-panel-settings.js.


// ─── Day Off Requests (shared helper) ────────────────────────

/** @tag PARENT DAY_OFF */
async function _ppDayOff(body) {
    try {
        const data = await apiFetchJSON("/api/parent/day-off-requests");
        if (!data.requests.length) {
            body.innerHTML = _ppEmpty("calendar-check", "No day-off requests.", "Pending requests show up here for your approval.");
            if (typeof lucide !== "undefined") lucide.createIcons();
            return;
        }
        body.innerHTML = `<div class="pp-dayoff-list">${data.requests.map(r => {
            const btns = r.status === "pending"
                ? `<button class="pp-btn success" onclick="_ppDecideDayOff(${r.id},'approved')">Approve</button>
                   <button class="pp-btn danger"  onclick="_ppDecideDayOff(${r.id},'denied')">Deny</button>`
                : `<span class="status-badge ${r.status}">${r.status}</span>`;
            return `<div class="pp-dayoff-row" id="dor-${r.id}">
                <div class="pp-dayoff-meta">${escapeHtml(r.request_date)} · <span class="status-badge ${escapeHtml(r.status)}">${escapeHtml(r.status)}</span></div>
                <div class="pp-dayoff-reason">${escapeHtml(r.reason)}</div>
                <div class="pp-dayoff-btns" id="dor-btns-${r.id}">${btns}</div>
            </div>`;
        }).join("")}</div>`;
    } catch (_) { body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`; }
}

/** @tag PARENT DAY_OFF */
async function _ppDecideDayOff(id, status) {
    try {
        const res = await window._ppFetch(`/api/parent/day-off-requests/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status }),
        });
        if (res.ok) { _ppLoadTab("habits"); return; }
        let detail = "";
        try { detail = (await res.json()).detail || ""; } catch (_) {}
        if (res.status === 403) {
            window.toast && window.toast("Parent PIN required — please re-enter.", "error");
        } else if (res.status === 404) {
            window.toast && window.toast("Request no longer exists.", "warn");
            _ppLoadTab("habits");
        } else {
            window.toast && window.toast(detail || "Could not save decision.", "error");
        }
    } catch (_) {
        window.toast && window.toast("Network error — try again.", "error");
    }
}
