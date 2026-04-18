/* ================================================================
   parent-panel.js — In-app Parent Dashboard overlay
   Section: Parent
   Dependencies: core.js
   API endpoints: /api/parent/verify-pin, /api/parent/overview,
                  /api/parent/word-stats, /api/parent/day-off-requests,
                  /api/parent/config (PIN change)
   ================================================================ */

// ─── State ────────────────────────────────────────────────────
let _ppTab = "overview";

// ─── Open / Close ─────────────────────────────────────────────

/**
 * Show PIN modal then open Parent Dashboard.
 * Replaces the old redirect-to-/parent behavior.
 * @tag PARENT PIN
 */
function openParentPanel() {
    _ppShowPinModal();
}

/** Close Parent Dashboard overlay. @tag PARENT */
function closeParentPanel() {
    const el = document.getElementById("parent-overlay");
    if (el) el.classList.add("hidden");
    _ppRemovePin();
    // Clear the verified PIN — re-entering the panel must re-prompt
    window._ppVerifiedPin = null;
    window._ppDigits = "";
}

// ─── PIN Modal ────────────────────────────────────────────────

/** Render PIN entry modal over the overlay. @tag PARENT PIN */
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
                    <button class="pin-key" onclick="_ppPinKey('clear')">✕</button>
                    <button class="pin-key" onclick="_ppPinKey('0')">0</button>
                    <button class="pin-key pin-key delete" onclick="_ppPinKey('del')">⌫</button>
                </div>
                <button class="pp-btn secondary" style="margin-top:14px;width:100%" onclick="closeParentPanel()">Cancel</button>
            </div>
        </div>`;
    window._ppDigits = "";
}

/** Handle PIN pad key. @tag PARENT PIN */
function _ppPinKey(key) {
    const digits = window._ppDigits || "";
    if (key === "del")   window._ppDigits = digits.slice(0, -1);
    else if (key === "clear") { window._ppDigits = ""; document.getElementById("pp-pin-err").textContent = ""; }
    else if (digits.length < 4) window._ppDigits = digits + key;
    _ppUpdateDots();
    if ((window._ppDigits || "").length === 4) setTimeout(_ppVerifyPin, 200);
}

/** Update PIN dot fill. @tag PARENT PIN */
function _ppUpdateDots() {
    const d = window._ppDigits || "";
    document.querySelectorAll(".pin-dot").forEach((el, i) => el.classList.toggle("filled", i < d.length));
}

/** POST /api/parent/verify-pin and proceed or show error. @tag PARENT PIN */
async function _ppVerifyPin() {
    const enteredPin = window._ppDigits || "";
    try {
        const res = await fetch("/api/parent/verify-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pin: enteredPin }),
        });
        if (res.ok) {
            // Stash the verified PIN so subsequent mutation calls can send it
            // in the X-Parent-Pin header (require_parent_pin dependency).
            window._ppVerifiedPin = enteredPin;
            _ppRemovePin();
            _ppRenderShell();
            _ppLoadTab("overview");
        } else {
            window._ppDigits = "";
            _ppUpdateDots();
            const err = document.getElementById("pp-pin-err");
            if (err) err.textContent = "Wrong PIN. Try again.";
        }
    } catch (_) { window._ppDigits = ""; _ppUpdateDots(); }
}

/**
 * Fetch helper that automatically attaches the verified parent PIN as
 * X-Parent-Pin header. Use for all PUT/POST calls under /api/parent/*.
 * Falls back to a plain fetch if the panel hasn't been unlocked yet
 * (the backend will reject with 403 in that case, which is correct).
 * @tag PARENT PIN
 */
window._ppFetch = function(url, opts = {}) {
    const headers = Object.assign({}, opts.headers || {});
    if (window._ppVerifiedPin) headers["X-Parent-Pin"] = window._ppVerifiedPin;
    return fetch(url, Object.assign({}, opts, { headers }));
};

/** Remove the PIN modal backdrop. @tag PARENT */
function _ppRemovePin() {
    const bg = document.getElementById("pp-pin-bg");
    if (bg) bg.remove();
}

// ─── Shell ────────────────────────────────────────────────────

const PP_TABS = [
    ["overview",   "Overview"],
    ["streak",     "Streak"],
    ["dayoff",     "Day Off"],
    ["tasks",      "Tasks"],
    ["schedule",   "Schedule"],
    ["wordstats",  "Word Stats"],
    ["math",       "Math"],
    ["xp",         "XP"],
    ["textbooks",  "Textbooks"],
    ["pin",        "Change PIN"],
];

/** Render the dashboard shell (header + nav + body). @tag PARENT */
function _ppRenderShell() {
    const el = document.getElementById("parent-overlay");
    if (!el) return;
    const tabs = PP_TABS.map(([key, label]) =>
        `<button class="pp-nav-btn${key === _ppTab ? " active" : ""}" data-tab-key="${key}" onclick="_ppLoadTab('${key}')">${label}</button>`
    ).join("");
    el.innerHTML = `
        <div class="pp-header">
            <button class="pp-close" onclick="closeParentPanel()">←</button>
            <span class="pp-title">Parent Dashboard</span>
        </div>
        <div class="pp-nav">${tabs}</div>
        <div id="pp-body"><p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p></div>`;
}

/** Switch tab and render content. @tag PARENT */
async function _ppLoadTab(tab) {
    _ppTab = tab;
    document.querySelectorAll(".pp-nav-btn").forEach(b => b.classList.toggle("active", b.dataset.tabKey === tab));
    const body = document.getElementById("pp-body");
    if (!body) return;
    body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p>`;
    const missing = `<p style="color:var(--color-error);padding:20px">Module not loaded.</p>`;
    switch (tab) {
        case "overview":  if (typeof _ppOverview     === "function") await _ppOverview(body);     else body.innerHTML = missing; break;
        case "streak":    if (typeof _ppStreak       === "function") await _ppStreak(body);       else body.innerHTML = missing; break;
        case "dayoff":    await _ppDayOff(body);    break;
        case "wordstats": await _ppWordStats(body); break;
        case "math":      if (typeof _ppMathSummary  === "function") await _ppMathSummary(body);  else body.innerHTML = missing; break;
        case "xp":        if (typeof _ppXP           === "function") await _ppXP(body);           else body.innerHTML = missing; break;
        case "textbooks": if (typeof _ppTextbooks    === "function") await _ppTextbooks(body);    else body.innerHTML = missing; break;
        case "tasks":     if (typeof ppRenderTasks   === "function") await ppRenderTasks(body);   else body.innerHTML = missing; break;
        case "schedule":  if (typeof ppRenderSchedule=== "function") await ppRenderSchedule(body);else body.innerHTML = missing; break;
        case "pin":       if (typeof ppRenderPin     === "function") ppRenderPin(body);           else body.innerHTML = missing; break;
        default: body.innerHTML = "<p>Coming soon.</p>";
    }
}

// ─── Day Off Requests ─────────────────────────────────────────

/** Render day-off requests with approve/deny buttons. @tag PARENT DAY_OFF */
async function _ppDayOff(body) {
    try {
        const res  = await fetch("/api/parent/day-off-requests");
        const data = await res.json();
        if (!data.requests.length) {
            body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:40px">No requests yet.</p>`; return;
        }
        body.innerHTML = `<div class="pp-dayoff-list">${data.requests.map(r => {
            const btns = r.status === "pending"
                ? `<button class="pp-btn success" onclick="_ppDecideDayOff(${r.id},'approved')">✓ Approve</button>
                   <button class="pp-btn danger"  onclick="_ppDecideDayOff(${r.id},'denied')">✕ Deny</button>`
                : `<span class="status-badge ${r.status}">${r.status}</span>`;
            return `<div class="pp-dayoff-row" id="dor-${r.id}">
                <div class="pp-dayoff-meta">${r.request_date} · <span class="status-badge ${r.status}">${r.status}</span></div>
                <div class="pp-dayoff-reason">${escapeHtml(r.reason)}</div>
                <div class="pp-dayoff-btns" id="dor-btns-${r.id}">${btns}</div>
            </div>`;
        }).join("")}</div>`;
    } catch (_) { body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`; }
}

/** POST approve/deny decision. PIN-protected. @tag PARENT DAY_OFF */
async function _ppDecideDayOff(id, status) {
    try {
        const res = await window._ppFetch(`/api/parent/day-off-requests/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status }),
        });
        if (res.ok) _ppLoadTab("dayoff");
    } catch (_) {}
}

// ─── Word Stats ───────────────────────────────────────────────

/** Render top wrong words table. @tag PARENT WORD_STATS */
async function _ppWordStats(body) {
    try {
        const res  = await fetch("/api/parent/word-stats");
        const data = await res.json();
        if (!data.top_wrong.length) {
            body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:40px">No word attempt data yet.</p>`; return;
        }
        const rows = data.top_wrong.map(w =>
            `<tr><td><strong>${escapeHtml(w.word)}</strong></td><td>${escapeHtml(w.lesson)}</td><td style="color:var(--color-error)">${w.wrong_count}</td><td>${Math.round(w.accuracy*100)}%</td></tr>`
        ).join("");
        body.innerHTML = `
            <div class="pp-section-title">Most Missed Words</div>
            <table class="pp-log-table"><thead><tr><th>Word</th><th>Lesson</th><th>❌ Wrong</th><th>Accuracy</th></tr></thead><tbody>${rows}</tbody></table>`;
    } catch (_) { body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`; }
}
