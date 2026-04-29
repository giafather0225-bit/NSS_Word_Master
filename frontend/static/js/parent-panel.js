/* ================================================================
   parent-panel.js — In-app Parent Dashboard overlay shell
   Section: Parent
   Dependencies: core.js
   API endpoints: /api/parent/verify-pin, /api/parent/day-off-requests,
                  /api/parent/word-stats, /api/parent/stage-stats
   ================================================================ */

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
    window._ppVerifiedPin = null;
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
                    <button class="pin-key" onclick="_ppPinKey('clear')">✕</button>
                    <button class="pin-key" onclick="_ppPinKey('0')">0</button>
                    <button class="pin-key pin-key delete" onclick="_ppPinKey('del')">⌫</button>
                </div>
                <button class="pp-btn secondary" style="margin-top:14px;width:100%" onclick="closeParentPanel()">Cancel</button>
            </div>
        </div>`;
    window._ppDigits = "";
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
            window._ppVerifiedPin = enteredPin;
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

/**
 * PIN-authenticated fetch for all parent mutation calls.
 * @tag PARENT PIN
 */
window._ppFetch = function(url, opts = {}) {
    const headers = Object.assign({}, opts.headers || {});
    if (window._ppVerifiedPin) headers["X-Parent-Pin"] = window._ppVerifiedPin;
    return fetch(url, Object.assign({}, opts, { headers }));
};

/** @tag PARENT */
function _ppRemovePin() {
    const bg = document.getElementById("pp-pin-bg");
    if (bg) bg.remove();
}

// ─── Shell ────────────────────────────────────────────────────

const PP_TABS = [
    ["home",     "Home"],
    ["english",  "English"],
    ["math",     "Math"],
    ["habits",   "Habits"],
    ["goals",    "Goals"],
    ["settings", "Settings"],
];

/** @tag PARENT */
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

/** @tag PARENT */
async function _ppLoadTab(tab) {
    _ppTab = tab;
    document.querySelectorAll(".pp-nav-btn").forEach(b => b.classList.toggle("active", b.dataset.tabKey === tab));
    const body = document.getElementById("pp-body");
    if (!body) return;
    body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p>`;
    const missing = `<p style="color:var(--color-error);padding:20px">Module not loaded.</p>`;
    switch (tab) {
        case "home":     if (typeof _ppHome        === "function") await _ppHome(body);        else body.innerHTML = missing; break;
        case "english":  await _ppEnglish(body);  break;
        case "math":     if (typeof _ppMathSummary === "function") await _ppMathSummary(body); else body.innerHTML = missing; break;
        case "habits":   await _ppHabits(body);   break;
        case "goals":    if (typeof _ppGoals       === "function") await _ppGoals(body);       else body.innerHTML = missing; break;
        case "settings": await _ppSettings(body); break;
        default: body.innerHTML = "<p>Coming soon.</p>";
    }
}

// ─── Tab: English ─────────────────────────────────────────────

/** Word stats + stage performance — 2-col layout. @tag PARENT WORD_STATS */
async function _ppEnglish(body) {
    try {
        const [ws, stg] = await Promise.all([
            apiFetchJSON("/api/parent/word-stats"),
            apiFetchJSON("/api/parent/stage-stats"),
        ]);

        const words = ws.top_wrong || [];
        const totalAttempts = words.reduce((a, w) => a + (w.attempts || 0), 0);
        const totalWrong    = words.reduce((a, w) => a + (w.wrong_count || 0), 0);
        const overallAcc    = totalAttempts ? Math.round((1 - totalWrong / totalAttempts) * 100) : 0;
        const stages        = stg.stages || {};
        const totalStageDone = Object.values(stages).reduce((a, s) => a + (s.completions || 0), 0);

        const summary = `
            <div class="pp-stats" style="grid-template-columns:repeat(3,1fr);margin-bottom:20px">
                <div class="pp-stat"><div class="pp-stat-num">${words.length}</div><div class="pp-stat-label">Tracked Words</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${overallAcc}%</div><div class="pp-stat-label">Overall Accuracy</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${totalStageDone}</div><div class="pp-stat-label">Stage Completions</div></div>
            </div>`;

        const wordRows = words.length
            ? words.map(w =>
                `<tr><td><strong>${escapeHtml(w.word)}</strong></td><td>${escapeHtml(w.lesson)}</td><td style="color:var(--color-error);text-align:right">${w.wrong_count}</td><td style="text-align:right">${Math.round(w.accuracy*100)}%</td></tr>`
              ).join("")
            : `<tr><td colspan="4" style="text-align:center;color:var(--text-secondary);padding:20px">No data yet.</td></tr>`;

        const STAGE_META = {
            preview:    { name: "Preview",    icon: "eye"           },
            word_match: { name: "Word Match", icon: "shuffle"       },
            fill_blank: { name: "Fill Blank", icon: "type"          },
            spelling:   { name: "Spelling",   icon: "spell-check"   },
            sentence:   { name: "Sentence",   icon: "pen-line"      },
            final_test: { name: "Final Test", icon: "graduation-cap"},
        };
        const STAGE_ORDER = ["preview", "word_match", "fill_blank", "spelling", "sentence", "final_test"];
        const stageList = STAGE_ORDER
            .filter(k => stages[k])
            .map(k => {
                const s = stages[k];
                const meta = STAGE_META[k] || { name: k, icon: "circle" };
                const acc = Math.round(s.avg_accuracy || 0);
                const accClass = acc >= 90 ? "good" : acc >= 70 ? "ok" : "low";
                return `
                    <div class="pp-stage-card">
                        <div class="pp-stage-head">
                            <i data-lucide="${meta.icon}" style="width:16px;height:16px"></i>
                            <span class="pp-stage-name">${meta.name}</span>
                            <span class="pp-stage-acc pp-stage-acc--${accClass}">${acc}%</span>
                        </div>
                        <div class="pp-stage-row"><span>Avg Time</span><strong>${Math.round(s.avg_time_sec/60)}m</strong></div>
                        <div class="pp-stage-row"><span>Completions</span><strong>${s.completions}x</strong></div>
                    </div>`;
            }).join("");

        body.innerHTML = `
            ${summary}
            <div class="pp-grid-2">
                <div>
                    <div class="pp-section-title" style="margin-top:0">Most Missed Words</div>
                    <div class="pp-table-wrap">
                        <table class="pp-log-table">
                            <thead><tr>
                                <th>Word</th><th>Lesson</th>
                                <th style="text-align:right">Wrong</th>
                                <th style="text-align:right">Accuracy</th>
                            </tr></thead>
                            <tbody>${wordRows}</tbody>
                        </table>
                    </div>
                </div>
                <div>
                    <div class="pp-section-title" style="margin-top:0">Stage Performance</div>
                    <div class="pp-stage-list">${stageList || `<p style="color:var(--text-secondary);font-size:13px">No stages completed yet.</p>`}</div>
                </div>
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (_) { body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`; }
}

// ─── Tab: Habits ──────────────────────────────────────────────

/** Streak + day-off approvals. @tag PARENT STREAK DAY_OFF */
async function _ppHabits(body) {
    body.innerHTML = `
        <div class="pp-section-title">Streak</div>
        <div id="pp-habits-streak"></div>
        <div class="pp-section-divider"></div>
        <div class="pp-section-title">Day Off Requests</div>
        <div id="pp-habits-dayoff"></div>`;

    const streakEl = document.getElementById("pp-habits-streak");
    const dayoffEl = document.getElementById("pp-habits-dayoff");

    if (typeof _ppStreak === "function") await _ppStreak(streakEl);
    else streakEl.innerHTML = `<p style="color:var(--text-secondary);font-size:14px;padding:12px 0">Streak module not loaded.</p>`;

    await _ppDayOff(dayoffEl);
}

// ─── Tab: Settings ────────────────────────────────────────────

/** Tasks + schedule + PIN/email + weekly report + textbooks. @tag PARENT SETTINGS */
async function _ppSettings(body) {
    body.innerHTML = `
        <div class="pp-section-title">Task Settings</div>
        <div id="pp-settings-tasks"></div>

        <div class="pp-grid-2" style="margin-top:20px">
            <div>
                <div class="pp-section-title">Academy Schedule</div>
                <div id="pp-settings-schedule"></div>
            </div>
            <div>
                <div class="pp-section-title">Account</div>
                <div id="pp-settings-pin"></div>
            </div>
        </div>

        <div class="pp-section-title" style="margin-top:8px">Weekly Report</div>
        <div id="pp-settings-report"></div>

        <div class="pp-section-title" style="margin-top:24px">Textbooks</div>
        <div id="pp-settings-textbooks"></div>`;

    const tasksEl     = document.getElementById("pp-settings-tasks");
    const scheduleEl  = document.getElementById("pp-settings-schedule");
    const pinEl       = document.getElementById("pp-settings-pin");
    const reportEl    = document.getElementById("pp-settings-report");
    const textbooksEl = document.getElementById("pp-settings-textbooks");

    if (typeof ppRenderTasks    === "function") await ppRenderTasks(tasksEl);
    if (typeof ppRenderSchedule === "function") await ppRenderSchedule(scheduleEl);
    if (typeof ppRenderPin      === "function") ppRenderPin(pinEl);
    if (typeof ppRenderReport   === "function") await ppRenderReport(reportEl);
    if (typeof _ppTextbooks     === "function") await _ppTextbooks(textbooksEl);

    if (typeof lucide !== "undefined") lucide.createIcons();
}

// ─── Day Off Requests (shared helper) ────────────────────────

/** @tag PARENT DAY_OFF */
async function _ppDayOff(body) {
    try {
        const data = await apiFetchJSON("/api/parent/day-off-requests");
        if (!data.requests.length) {
            body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:20px">No requests yet.</p>`; return;
        }
        body.innerHTML = `<div class="pp-dayoff-list">${data.requests.map(r => {
            const btns = r.status === "pending"
                ? `<button class="pp-btn success" onclick="_ppDecideDayOff(${r.id},'approved')">Approve</button>
                   <button class="pp-btn danger"  onclick="_ppDecideDayOff(${r.id},'denied')">Deny</button>`
                : `<span class="status-badge ${r.status}">${r.status}</span>`;
            return `<div class="pp-dayoff-row" id="dor-${r.id}">
                <div class="pp-dayoff-meta">${r.request_date} · <span class="status-badge ${r.status}">${r.status}</span></div>
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
