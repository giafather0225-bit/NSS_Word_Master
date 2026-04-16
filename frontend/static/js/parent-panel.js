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
                <div class="pp-pin-title">🔒 Parent Mode</div>
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
    ["dayoff",     "Day Off"],
    ["tasks",      "Tasks"],
    ["schedule",   "Schedule"],
    ["wordstats",  "Word Stats"],
    ["textbooks",  "Textbooks"],
    ["pin",        "Change PIN"],
    ["textbook",   "Add Textbook"],
];

/** Render the dashboard shell (header + nav + body). @tag PARENT */
function _ppRenderShell() {
    const el = document.getElementById("parent-overlay");
    if (!el) return;
    const tabs = PP_TABS.map(([key, label]) =>
        `<button class="pp-nav-btn${key === _ppTab ? " active" : ""}" onclick="_ppLoadTab('${key}')">${label}</button>`
    ).join("");
    el.innerHTML = `
        <div class="pp-header">
            <button class="pp-close" onclick="closeParentPanel()">←</button>
            <span class="pp-title">⚙️ Parent Dashboard</span>
        </div>
        <div class="pp-nav">${tabs}</div>
        <div id="pp-body"><p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p></div>`;
}

/** Switch tab and render content. @tag PARENT */
async function _ppLoadTab(tab) {
    _ppTab = tab;
    document.querySelectorAll(".pp-nav-btn").forEach(b => b.classList.toggle("active", b.textContent === PP_TABS.find(t => t[0] === tab)?.[1]));
    const body = document.getElementById("pp-body");
    if (!body) return;
    body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p>`;
    switch (tab) {
        case "overview":  await _ppOverview(body);  break;
        case "dayoff":    await _ppDayOff(body);    break;
        case "wordstats":  await _ppWordStats(body);  break;
        case "textbooks":  await _ppTextbooks(body); break;
        case "tasks":      if (typeof ppRenderTasks    === "function") await ppRenderTasks(body);     break;
        case "schedule":   if (typeof ppRenderSchedule === "function") await ppRenderSchedule(body);  break;
        case "pin":        if (typeof ppRenderPin      === "function") ppRenderPin(body);             break;
        case "textbook":   window.open("/ingest", "_blank"); body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary)">Opened in a new tab.</p>`; break;
        default: body.innerHTML = "<p>Coming soon.</p>";
    }
}

// ─── Overview ─────────────────────────────────────────────────

/** Render the enhanced overview: summary cards + activity chart + stage stats. @tag PARENT */
async function _ppOverview(body) {
    try {
        const [sumRes, actRes, stgRes] = await Promise.all([
            fetch("/api/parent/summary"),
            fetch("/api/parent/activity?days=7"),
            fetch("/api/parent/stage-stats"),
        ]);
        const sum = await sumRes.json();
        const act = await actRes.json();
        const stg = await stgRes.json();

        // Summary cards (2×2)
        const cards = `
            <div class="pp-stats">
                <div class="pp-stat"><div class="pp-stat-num">⭐ ${sum.total_xp||0}</div><div class="pp-stat-label">Total XP · Lv.${sum.current_level||1}</div></div>
                <div class="pp-stat"><div class="pp-stat-num">🔥 ${sum.current_streak||0}d</div><div class="pp-stat-label">Streak (best ${sum.longest_streak||0}d)</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${sum.total_words_learned||0}</div><div class="pp-stat-label">Words Learned</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${sum.total_study_minutes||0}m</div><div class="pp-stat-label">${sum.total_study_sessions||0} sessions</div></div>
            </div>`;

        // 7-day activity bar chart (CSS-only)
        const daily = act.daily || [];
        const maxXP = Math.max(1, ...daily.map(d => d.xp));
        const bars = daily.map(d => {
            const pct = Math.round((d.xp / maxXP) * 100);
            const dayLabel = d.date.slice(5); // MM-DD
            return `<div class="pp-bar-col">
                <div class="pp-bar-value">${d.xp}</div>
                <div class="pp-bar-track"><div class="pp-bar-fill" style="height:${pct}%"></div></div>
                <div class="pp-bar-label">${dayLabel}</div>
            </div>`;
        }).join("");
        const chart = `
            <div class="pp-section-title">7-Day XP Activity</div>
            <div class="pp-bar-chart">${bars}</div>`;

        // Stage performance
        const STAGE_NAMES = {preview:"Preview", word_match:"Word Match", fill_blank:"Fill Blank", spelling:"Spelling", sentence:"Sentence", final_test:"Final Test"};
        const stageCards = Object.entries(stg.stages || {}).map(([key, s]) => {
            const name = STAGE_NAMES[key] || key;
            return `<div class="pp-stage-card">
                <div class="pp-stage-name">${name}</div>
                <div class="pp-stage-row"><span>Avg Accuracy</span><strong>${s.avg_accuracy}%</strong></div>
                <div class="pp-stage-row"><span>Avg Time</span><strong>${Math.round(s.avg_time_sec/60)}m</strong></div>
                <div class="pp-stage-row"><span>Completed</span><strong>${s.completions}x</strong></div>
            </div>`;
        }).join("");
        const stageSection = stageCards ? `<div class="pp-section-title">Stage Performance</div><div class="pp-stage-grid">${stageCards}</div>` : "";

        body.innerHTML = cards + chart + stageSection;
    } catch (_) { body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`; }
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

// ─── Textbooks Overview ───────────────────────────────────────

/**
 * Render textbook accordion with lesson breakdown.
 * Uses /api/dashboard/stats for the list and /api/dashboard/textbook/{tb} for details.
 * @tag PARENT WORD_STATS
 */
async function _ppTextbooks(body) {
    try {
        const res  = await fetch("/api/dashboard/stats");
        const data = await res.json();
        const tbs  = data.textbooks || [];

        if (!tbs.length) {
            body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:40px">No textbooks found.</p>`;
            return;
        }

        // Summary row
        const summary = `
            <div class="pp-stats" style="grid-template-columns:repeat(3,1fr);margin-bottom:20px">
                <div class="pp-stat"><div class="pp-stat-num">${data.total_words || 0}</div><div class="pp-stat-label">Total Words</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${data.textbook_count || 0}</div><div class="pp-stat-label">Textbooks</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${data.lesson_count || 0}</div><div class="pp-stat-label">Lessons</div></div>
            </div>`;

        // Accordion rows
        const rows = tbs.map((tb, i) => `
            <div style="border-bottom:1px solid var(--color-primary-light)">
                <div style="display:flex;align-items:center;gap:12px;padding:14px 4px;cursor:pointer"
                     onclick="_ppTbToggle('ppTb${i}', '${escapeHtml(tb.name)}')">
                    <span style="font-size:20px">📚</span>
                    <div style="flex:1;min-width:0">
                        <div style="font-size:15px;font-weight:600;color:var(--text-primary)">${escapeHtml(tb.name)}</div>
                        <div style="font-size:12px;color:var(--text-secondary);margin-top:2px">${tb.lessons||0} lessons · ${tb.words||0} words</div>
                    </div>
                    <span id="ppTbArrow${i}" style="font-size:18px;color:var(--text-secondary);transition:transform 0.2s">›</span>
                </div>
                <div id="ppTb${i}" style="display:none;padding:0 0 8px 52px"></div>
            </div>`).join("");

        body.innerHTML = summary + `<div class="pp-section-title">Textbook Overview</div><div>${rows}</div>`;
    } catch (_) {
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`;
    }
}

/**
 * Toggle textbook accordion and lazy-load lessons.
 * @tag PARENT WORD_STATS
 */
async function _ppTbToggle(panelId, tbName) {
    const panel = document.getElementById(panelId);
    const idx   = panelId.replace("ppTb", "");
    const arrow = document.getElementById(`ppTbArrow${idx}`);
    if (!panel) return;

    const isOpen = panel.style.display !== "none";
    panel.style.display = isOpen ? "none" : "block";
    if (arrow) arrow.style.transform = isOpen ? "" : "rotate(90deg)";
    if (isOpen || panel.dataset.loaded) return;

    panel.dataset.loaded = "1";
    panel.innerHTML = `<p style="font-size:13px;color:var(--text-secondary);padding:4px 0">Loading…</p>`;
    try {
        const res  = await fetch("/api/dashboard/textbook/" + encodeURIComponent(tbName));
        const data = await res.json();
        const lessons = data.lessons || [];
        if (!lessons.length) { panel.innerHTML = `<p style="font-size:13px;color:var(--text-secondary);padding:4px 0">No lessons.</p>`; return; }
        panel.innerHTML = lessons.map(l => `
            <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:var(--radius-sm);transition:background 0.15s"
                 onmouseover="this.style.background='var(--color-primary-light)'" onmouseout="this.style.background=''">
                <span style="font-size:13px;font-weight:500;color:var(--text-primary);flex:1">${escapeHtml(l.lesson)}</span>
                <span style="font-size:12px;color:var(--text-secondary)">${l.words||0} words</span>
            </div>`).join("");
    } catch (_) {
        panel.innerHTML = `<p style="font-size:13px;color:var(--color-error);padding:4px 0">Failed to load.</p>`;
    }
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
