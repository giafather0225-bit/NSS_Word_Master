/* ================================================================
   parent-panel.js — In-app Parent Dashboard overlay shell
   Section: Parent
   Dependencies: core.js
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
                <button class="pp-btn secondary" style="margin-top:14px;width:100%" onclick="closeParentPanel()">Cancel</button>
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
    ["english",  "English"],
    ["ckla",     "CKLA"],
    ["math",     "Math"],
    ["habits",   "Habits"],
    ["goals",    "Goals"],
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
        <div id="pp-body"><p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p></div>`;
    if (typeof lucide !== "undefined") lucide.createIcons();
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
        case "ckla":     if (typeof _ppCKLA        === "function") await _ppCKLA(body);        else body.innerHTML = missing; break;
        case "math":     if (typeof _ppMathSummary === "function") await _ppMathSummary(body); else body.innerHTML = missing; break;
        case "habits":   await _ppHabits(body);   break;
        case "goals":    if (typeof _ppGoals       === "function") await _ppGoals(body);       else body.innerHTML = missing; break;
        case "island":   if (typeof _ppIsland      === "function") await _ppIsland(body);      else body.innerHTML = missing; break;
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
            <div class="pp-stats pp-english-stats" style="margin-bottom:20px">
                <div class="pp-stat"><div class="pp-stat-num">${words.length}</div><div class="pp-stat-label">Tracked Words</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${overallAcc}%</div><div class="pp-stat-label">Overall Accuracy</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${totalStageDone}</div><div class="pp-stat-label">Stage Completions</div></div>
            </div>`;

        const wordRows = words.length
            ? words.map(w =>
                `<tr><td><strong>${escapeHtml(w.word)}</strong></td><td>${escapeHtml(w.lesson)}</td><td style="color:var(--color-error);text-align:right">${w.wrong_count}</td><td style="text-align:right">${Math.round(w.accuracy*100)}%</td></tr>`
              ).join("")
            : `<tr><td colspan="4">${_ppEmpty("file-search-2", "No missed words tracked yet.", "Words start showing up after the child fails them in Word Match or Spelling.")}</td></tr>`;

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
                    <div class="pp-stage-list">${stageList || _ppEmpty("layers", "No stages completed yet.", "Each finished stage feeds these accuracy + time stats.")}</div>
                </div>
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (_) { body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`; }
}

// ─── Tab: Habits ──────────────────────────────────────────────

/** Streak + day-off approvals. @tag PARENT STREAK DAY_OFF */
async function _ppHabits(body) {
    body.innerHTML = `<p style="color:var(--text-secondary);font-size:14px;padding:20px 0">Loading…</p>`;

    let sd = null;
    try { sd = await apiFetchJSON("/api/parent/streak"); } catch (_) {}

    let streakHtml = "";
    if (sd && typeof _ppStreakCards === "function") {
        streakHtml =
            _ppStreakCards(sd) +
            `<div class="pp-grid-2" style="margin-top:4px;align-items:start">
                <div>${_ppStreakRule(sd.rule)}</div>
                <div>${_ppStreakMilestones(sd)}</div>
            </div>` +
            _ppStreakCalendar(sd.last_30d || []);
    } else {
        streakHtml = `<p style="color:var(--color-error);padding:12px 0">Failed to load streak data.</p>`;
    }

    body.innerHTML = streakHtml + `
        <div class="pp-section-divider" style="margin:24px 0 16px"></div>
        <div class="pp-section-title">Day Off Requests</div>
        <div id="pp-habits-dayoff"></div>`;

    const dayoffEl = document.getElementById("pp-habits-dayoff");
    if (dayoffEl) await _ppDayOff(dayoffEl);
    if (typeof lucide !== "undefined") lucide.createIcons();
}

// ─── Tab: Settings (Accordion) ────────────────────────────────

const _PP_SETTINGS_SECTIONS = [
    { id: "tasks",    icon: "check-square", label: "Task Settings",         open: true  },
    { id: "schedacc", icon: "calendar",     label: "Schedule & Account",    open: false },
    { id: "report",   icon: "mail",         label: "Weekly Report",         open: false },
    { id: "textbooks",icon: "book-open",    label: "Textbooks",             open: false },
    { id: "xp",       icon: "zap",          label: "XP Rules",              open: false },
    { id: "island",   icon: "palmtree",     label: "Island System",         open: false },
    { id: "ckla",     icon: "layers",       label: "CKLA Settings",         open: false },
    { id: "devtools", icon: "terminal",     label: "Developer / Test Mode", open: false },
];

/** Tasks + schedule + PIN/email + weekly report + textbooks. @tag PARENT SETTINGS */
async function _ppSettings(body) {
    body.innerHTML = `<div class="pp-accordion">${_PP_SETTINGS_SECTIONS.map(s => `
        <div class="pp-accordion-item${s.open ? " open" : ""}" data-section="${s.id}">
            <button class="pp-accordion-header" onclick="window._ppAccordionToggle(this)">
                <span class="pp-accordion-icon"><i data-lucide="${s.icon}"></i></span>
                <span class="pp-accordion-label">${s.label}</span>
                <i data-lucide="chevron-down" class="pp-accordion-chevron"></i>
            </button>
            <div class="pp-accordion-body">
                <div class="pp-accordion-content" id="pp-acc-${s.id}"></div>
            </div>
        </div>`).join("")}
    </div>`;

    if (typeof lucide !== "undefined") lucide.createIcons();
    // Render the default-open section immediately
    await _ppAccordionRender("tasks");
}

/** Toggle accordion item open/closed; lazy-renders content on first open. @tag PARENT SETTINGS */
async function _ppAccordionToggle(header) {
    const item = header.closest(".pp-accordion-item");
    const wasOpen = item.classList.contains("open");
    item.classList.toggle("open", !wasOpen);
    if (!wasOpen && !item.dataset.rendered) {
        await _ppAccordionRender(item.dataset.section);
    }
}
window._ppAccordionToggle = _ppAccordionToggle;

/** Render a single accordion section's content. @tag PARENT SETTINGS */
async function _ppAccordionRender(sectionId) {
    const el = document.getElementById(`pp-acc-${sectionId}`);
    if (!el) return;
    const item = el.closest(".pp-accordion-item");
    if (item) item.dataset.rendered = "true";

    if (sectionId === "tasks") {
        if (typeof ppRenderTasks === "function") await ppRenderTasks(el);
    } else if (sectionId === "schedacc") {
        el.innerHTML = `
            <div class="pp-grid-2" style="gap:20px">
                <div>
                    <div class="pp-section-title">Academy Schedule</div>
                    <div id="pp-acc-schedule-inner"></div>
                </div>
                <div>
                    <div class="pp-section-title">Account</div>
                    <div id="pp-acc-pin-inner"></div>
                </div>
            </div>`;
        const sEl = document.getElementById("pp-acc-schedule-inner");
        const pEl = document.getElementById("pp-acc-pin-inner");
        if (sEl && typeof ppRenderSchedule === "function") await ppRenderSchedule(sEl);
        if (pEl && typeof ppRenderPin      === "function") ppRenderPin(pEl);
    } else if (sectionId === "report") {
        if (typeof ppRenderReport === "function") await ppRenderReport(el);
    } else if (sectionId === "textbooks") {
        if (typeof _ppTextbooks === "function") await _ppTextbooks(el);
    } else if (sectionId === "xp") {
        if (typeof _ppXP === "function") await _ppXP(el);
    } else if (sectionId === "island") {
        await _ppIslandToggle(el);
    } else if (sectionId === "ckla") {
        if (typeof ppRenderCKLASettings === "function") await ppRenderCKLASettings(el);
    } else if (sectionId === "devtools") {
        await _ppTestModeSection(el);
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** Render Test Mode (God Mode) toggle. PIN-gated on save. @tag PARENT SETTINGS */
async function _ppTestModeSection(el) {
    if (!el) return;
    let active = false;
    try {
        const d = await apiFetchJSON("/api/parent/test-mode");
        active = !!d.test_mode;
    } catch (_) {}

    el.innerHTML = `
        <div class="pp-toggle-row">
            <div>
                <div class="pp-toggle-label">Test Mode (God Mode)</div>
                <div class="pp-toggle-hint">Bypasses all progression locks, enables free shop purchases and character level/evolution buttons. Disable before real sessions.</div>
            </div>
            <label class="pp-toggle-switch" title="Toggle Test Mode">
                <input type="checkbox" id="pp-testmode-chk" ${active ? "checked" : ""}
                       onchange="_ppSaveTestMode(this.checked)">
                <span class="pp-toggle-track"></span>
            </label>
        </div>
        <p id="pp-testmode-status" style="font-size:12px;color:var(--text-hint);margin:4px 0 0 0">
            ${active ? '<span style="color:var(--arcade-ink);font-weight:700">TEST MODE is ON</span> — progression locks are disabled.' : 'Real mode active.'}
        </p>`;
}

/** @tag PARENT SETTINGS */
async function _ppSaveTestMode(checked) {
    const chk = document.getElementById("pp-testmode-chk");
    const status = document.getElementById("pp-testmode-status");
    try {
        const res = await window._ppFetch("/api/parent/test-mode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled: checked }),
        });
        if (res.ok) {
            // Update global flag and badge
            if (typeof _loadTestMode === "function") await _loadTestMode();
            window.toast && window.toast(`Test mode ${checked ? "enabled" : "disabled"}.`, "success");
            if (status) status.innerHTML = checked
                ? '<span style="color:var(--arcade-ink);font-weight:700">TEST MODE is ON</span> — progression locks are disabled.'
                : 'Real mode active.';
        } else {
            window.toast && window.toast("Could not save Test Mode setting.", "error");
            if (chk) chk.checked = !checked;
        }
    } catch (_) {
        window.toast && window.toast("Network error.", "error");
        if (chk) chk.checked = !checked;
    }
}

/** Render Island ON/OFF toggle + active character summary. @tag PARENT SETTINGS SHOP */
async function _ppIslandToggle(el) {
    if (!el) return;
    try {
        const [cfg, status] = await Promise.all([
            apiFetchJSON("/api/island/config"),
            apiFetchJSON("/api/island/status"),
        ]);
        const on     = cfg.config?.island_on !== "false";
        const chars  = status.active_characters || [];
        const lumi   = status.currency?.lumi ?? 0;

        const charCards = chars.map(c => {
            const hunger    = c.hunger    ?? 0;
            const happiness = c.happiness ?? 0;
            const hColor    = hunger    < 20 ? "var(--review-primary)" : hunger    < 60 ? "var(--arcade-primary)" : "var(--math-primary)";
            const hpColor   = happiness < 20 ? "var(--review-primary)" : happiness < 60 ? "var(--arcade-primary)" : "var(--math-primary)";
            return `
                <div class="pp-island-char-card">
                    <div class="pp-island-char-name">${escapeHtml(c.name || "?")} <span class="pp-island-char-zone">${escapeHtml(c.zone || "")}</span></div>
                    <div class="pp-island-char-meta">Lv.${c.level ?? 1} · ${escapeHtml(c.stage || "baby")}</div>
                    <div class="pp-island-char-gauges">
                        <div class="pp-island-gauge">
                            <i data-lucide="utensils" style="width:12px;height:12px;color:var(--text-hint)"></i>
                            <div class="pp-island-gauge-bar">
                                <div class="pp-island-gauge-fill" style="width:${hunger}%;background:${hColor}"></div>
                            </div>
                            <span class="pp-island-gauge-val">${hunger}</span>
                        </div>
                        <div class="pp-island-gauge">
                            <i data-lucide="smile" style="width:12px;height:12px;color:var(--text-hint)"></i>
                            <div class="pp-island-gauge-bar">
                                <div class="pp-island-gauge-fill" style="width:${happiness}%;background:${hpColor}"></div>
                            </div>
                            <span class="pp-island-gauge-val">${happiness}</span>
                        </div>
                    </div>
                </div>`;
        }).join('');

        const completedCount = status.completed_count ?? 0;
        const summaryLine = chars.length
            ? `<div class="pp-island-summary">Lumi: ${lumi} &nbsp;|&nbsp; Completed: ${completedCount}</div>`
            : `<div class="pp-island-summary" style="color:var(--text-hint)">No active characters yet.</div>`;

        el.innerHTML = `
            <div class="pp-toggle-row">
                <div>
                    <div class="pp-toggle-label">Gia's Island</div>
                    <div class="pp-toggle-hint">Character raising, Lumi economy, zone exploration</div>
                </div>
                <label class="pp-toggle-switch" title="Toggle Island">
                    <input type="checkbox" id="pp-island-chk" ${on ? "checked" : ""}
                           onchange="_ppSaveIslandToggle(this.checked)">
                    <span class="pp-toggle-track"></span>
                </label>
            </div>
            ${summaryLine}
            ${charCards ? `<div class="pp-island-char-list">${charCards}</div>` : ''}`;
    } catch (_) {
        el.innerHTML = `<p style="color:var(--text-hint);font-size:13px;padding:8px 0">Island config unavailable.</p>`;
    }
}

/** @tag PARENT SETTINGS SHOP */
async function _ppSaveIslandToggle(checked) {
    try {
        const res = await window._ppFetch("/api/island/config/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: "island_on", value: checked ? "true" : "false" }),
        });
        if (res.ok) {
            window.toast && window.toast(`Island ${checked ? "enabled" : "disabled"}.`, "success");
        } else {
            window.toast && window.toast("Could not save Island setting.", "error");
            const chk = document.getElementById("pp-island-chk");
            if (chk) chk.checked = !checked;
        }
    } catch (_) {
        window.toast && window.toast("Network error.", "error");
    }
}

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
