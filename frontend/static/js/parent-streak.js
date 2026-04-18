/* ================================================================
   parent-streak.js — Parent Dashboard Streak tab renderer
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: GET /api/parent/streak, POST /api/parent/streak-rule,
                  POST /api/parent/streak-recalc
   ================================================================ */

const _PP_STREAK_SUBJECTS = [
    ["english", "English", "📕"],
    ["math",    "Math",    "📐"],
    ["game",    "Game",    "🎮"],
];

/** Render Streak tab: stats cards + rule config + 30-day calendar + milestones. @tag PARENT STREAK */
async function _ppStreak(body) {
    try {
        const res = await fetch("/api/parent/streak");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        window._ppStreakData = data;

        body.innerHTML =
            _ppStreakCards(data) +
            _ppStreakRule(data.rule) +
            _ppStreakCalendar(data.last_30d || []) +
            _ppStreakMilestones(data);
    } catch (err) {
        console.error("[parent-streak] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load streak.</p>`;
    }
}

/** Top 3 stat cards: current / longest / freeze this month. @tag PARENT STREAK */
function _ppStreakCards(data) {
    return `
        <div class="pp-stats" style="grid-template-columns:repeat(3,1fr)">
            <div class="pp-stat"><div class="pp-stat-num">🔥 ${data.current || 0}d</div><div class="pp-stat-label">Current Streak</div></div>
            <div class="pp-stat"><div class="pp-stat-num">🏆 ${data.longest || 0}d</div><div class="pp-stat-label">Longest Ever</div></div>
            <div class="pp-stat"><div class="pp-stat-num">🏖️ ${data.freeze_this_month || 0}</div><div class="pp-stat-label">Freezes This Month</div></div>
        </div>`;
}

/** Rule configurator: subject checkboxes + mode radio + save. @tag PARENT STREAK */
function _ppStreakRule(rule) {
    const active = new Set((rule && rule.subjects) || []);
    const mode = (rule && rule.mode) || "all";
    const checks = _PP_STREAK_SUBJECTS.map(([key, label, icon]) => `
        <label class="pp-streak-check">
            <input type="checkbox" value="${key}" ${active.has(key) ? "checked" : ""}>
            <span>${icon} ${label}</span>
        </label>`).join("");
    return `
        <div class="pp-section-title">Streak Rule</div>
        <div class="pp-streak-rule">
            <div class="pp-streak-subtitle">Subjects that count</div>
            <div class="pp-streak-checks">${checks}</div>

            <div class="pp-streak-subtitle" style="margin-top:12px">When does a day count?</div>
            <div class="pp-streak-modes">
                <label class="pp-streak-radio">
                    <input type="radio" name="pp-streak-mode" value="all" ${mode === "all" ? "checked" : ""}>
                    <span>All selected subjects required</span>
                </label>
                <label class="pp-streak-radio">
                    <input type="radio" name="pp-streak-mode" value="any" ${mode === "any" ? "checked" : ""}>
                    <span>Any one selected subject is enough</span>
                </label>
            </div>

            <div class="pp-streak-actions">
                <button class="pp-btn primary" onclick="_ppSaveStreakRule()">Save Rule</button>
                <button class="pp-btn secondary" onclick="_ppRecalcStreak()">Recalc Last 7d</button>
                <span id="pp-streak-msg" class="pp-streak-msg"></span>
            </div>
        </div>`;
}

/** 30-day calendar strip with per-subject dot trails. @tag PARENT STREAK */
function _ppStreakCalendar(days) {
    if (!days.length) return "";
    const cells = days.map(d => {
        let icon = "❌";
        let cls = "broken";
        if (d.day_off) { icon = "🏖️"; cls = "freeze"; }
        else if (d.maintained) { icon = "🔥"; cls = "maintained"; }
        const mm_dd = (d.date || "").slice(5);
        const dots = [
            d.english ? '<span class="pp-streak-dot e" title="English"></span>' : '<span class="pp-streak-dot off"></span>',
            d.math    ? '<span class="pp-streak-dot m" title="Math"></span>'    : '<span class="pp-streak-dot off"></span>',
            d.game    ? '<span class="pp-streak-dot g" title="Game"></span>'    : '<span class="pp-streak-dot off"></span>',
        ].join("");
        return `
            <div class="pp-streak-cell ${cls}" title="${d.date} — E:${d.english?'✓':'·'} M:${d.math?'✓':'·'} G:${d.game?'✓':'·'}">
                <div class="pp-streak-cell-icon">${icon}</div>
                <div class="pp-streak-cell-dots">${dots}</div>
                <div class="pp-streak-cell-date">${mm_dd}</div>
            </div>`;
    }).join("");
    return `
        <div class="pp-section-title">Last 30 Days</div>
        <div class="pp-streak-legend">
            <span><span class="pp-streak-dot e"></span> English</span>
            <span><span class="pp-streak-dot m"></span> Math</span>
            <span><span class="pp-streak-dot g"></span> Game</span>
        </div>
        <div class="pp-streak-grid">${cells}</div>`;
}

/** Milestone progress bars for 7d/30d bonus. @tag PARENT STREAK */
function _ppStreakMilestones(data) {
    const cur = data.current || 0;
    const m = data.milestones || {};
    const next7 = m.days_to_next_7 || (7 - (cur % 7 || 7));
    const next30 = m.days_to_next_30 || (30 - (cur % 30 || 30));
    const pct7  = Math.round(((7 - next7) / 7) * 100);
    const pct30 = Math.round(((30 - next30) / 30) * 100);
    return `
        <div class="pp-section-title">Milestones</div>
        <div class="pp-streak-milestone">
            <div class="pp-streak-ms-row"><span>7-day bonus (+30 XP)</span><strong>${next7}d left</strong></div>
            <div class="pp-bar-track" style="height:8px;max-width:none"><div class="pp-bar-fill" style="width:${pct7}%;height:100%"></div></div>
        </div>
        <div class="pp-streak-milestone">
            <div class="pp-streak-ms-row"><span>30-day bonus (+200 XP)</span><strong>${next30}d left</strong></div>
            <div class="pp-bar-track" style="height:8px;max-width:none"><div class="pp-bar-fill" style="width:${pct30}%;height:100%"></div></div>
        </div>`;
}

/** Collect form values and POST streak rule. @tag PARENT STREAK */
async function _ppSaveStreakRule() {
    const subjects = Array.from(
        document.querySelectorAll(".pp-streak-checks input[type=checkbox]:checked")
    ).map(i => i.value);
    const modeEl = document.querySelector("input[name=pp-streak-mode]:checked");
    const mode = modeEl ? modeEl.value : "all";
    const msg = document.getElementById("pp-streak-msg");
    if (!subjects.length) {
        if (msg) { msg.textContent = "Select at least one subject."; msg.style.color = "var(--color-error)"; }
        return;
    }
    try {
        const res = await window._ppFetch("/api/parent/streak-rule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subjects, mode }),
        });
        if (msg) {
            msg.textContent = res.ok ? "✓ Saved." : "Failed to save.";
            msg.style.color = res.ok ? "var(--color-success)" : "var(--color-error)";
        }
    } catch (err) {
        console.error("[parent-streak] save failed:", err);
        if (msg) { msg.textContent = "Network error."; msg.style.color = "var(--color-error)"; }
    }
}

/** POST recalc last 7d, then reload the tab. @tag PARENT STREAK */
async function _ppRecalcStreak() {
    const msg = document.getElementById("pp-streak-msg");
    try {
        const res = await window._ppFetch("/api/parent/streak-recalc?days=7", { method: "POST" });
        if (msg) {
            msg.textContent = res.ok ? "✓ Recalculated." : "Failed.";
            msg.style.color = res.ok ? "var(--color-success)" : "var(--color-error)";
        }
        if (res.ok && typeof _ppLoadTab === "function") setTimeout(() => _ppLoadTab("streak"), 400);
    } catch (err) {
        console.error("[parent-streak] recalc failed:", err);
    }
}

window._ppStreak          = _ppStreak;
window._ppSaveStreakRule  = _ppSaveStreakRule;
window._ppRecalcStreak    = _ppRecalcStreak;
