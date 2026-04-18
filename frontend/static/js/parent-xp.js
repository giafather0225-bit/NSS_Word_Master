/* ================================================================
   parent-xp.js — Parent Dashboard XP Settings & Report tab
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: GET/POST /api/parent/xp-rules,
                  POST /api/parent/xp-rules/reset,
                  GET /api/parent/xp-report
   ================================================================ */

const _PP_XP_ACTIONS = [
    ["word_correct",            "Word Correct"],
    ["stage_complete",          "Stage Complete"],
    ["final_test_pass",         "Final Test Pass"],
    ["unit_test_pass",          "Unit Test Pass"],
    ["daily_words_complete",    "Daily Words Complete"],
    ["weekly_test_pass",        "Weekly Test Pass"],
    ["mywords_weekly_test_pass","My Words Weekly Test"],
    ["review_complete",         "Review Complete"],
    ["journal_complete",        "Diary Journal"],
    ["must_do_bonus",           "Must-Do Bonus"],
    ["all_complete_bonus",      "All-Complete Bonus"],
    ["streak_7_bonus",          "7-Day Streak Bonus"],
    ["streak_30_bonus",         "30-Day Streak Bonus"],
];

/** Render XP tab: rule editor + arcade cap + 7-day report. @tag PARENT XP */
async function _ppXP(body) {
    try {
        const [rulesRes, reportRes] = await Promise.all([
            fetch("/api/parent/xp-rules"),
            fetch("/api/parent/xp-report?days=7"),
        ]);
        if (!rulesRes.ok || !reportRes.ok) throw new Error("fetch failed");
        const rules  = await rulesRes.json();
        const report = await reportRes.json();
        window._ppXPData = { rules, report };

        body.innerHTML =
            _ppXPReport(report) +
            _ppXPRulesEditor(rules) +
            _ppXPArcadeEditor(rules);
    } catch (err) {
        console.error("[parent-xp] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load XP settings.</p>`;
    }
}

/** 7-day XP report: total + daily bars + top actions. @tag PARENT XP REPORT */
function _ppXPReport(r) {
    const daily = r.daily || [];
    const max   = Math.max(1, ...daily.map(d => d.xp || 0));
    const bars  = daily.map(d => {
        const pct = Math.round(((d.xp || 0) / max) * 100);
        const mm_dd = (d.date || "").slice(5);
        return `<div class="pp-bar-col">
            <div class="pp-bar-value">${d.xp || 0}</div>
            <div class="pp-bar-track"><div class="pp-bar-fill" style="height:${pct}%"></div></div>
            <div class="pp-bar-label">${mm_dd}</div>
        </div>`;
    }).join("");

    const byAction = (r.by_action || []).slice(0, 8).map(a =>
        `<tr>
            <td><strong>${escapeHtml(a.action)}</strong></td>
            <td style="text-align:right">${a.count}×</td>
            <td style="text-align:right"><strong>${a.xp}</strong> XP</td>
        </tr>`
    ).join("");

    return `
        <div class="pp-section-title" style="margin-top:0">XP · Last 7 Days</div>
        <div class="pp-stats" style="grid-template-columns:1fr">
            <div class="pp-stat">
                <div class="pp-stat-num">⭐ ${r.total_xp || 0}</div>
                <div class="pp-stat-label">Total XP · 7 days</div>
            </div>
        </div>
        <div class="pp-bar-chart">${bars}</div>
        ${byAction ? `
            <div class="pp-section-title">Top Actions</div>
            <table class="pp-log-table">
                <thead><tr><th>Action</th><th style="text-align:right">Count</th><th style="text-align:right">XP</th></tr></thead>
                <tbody>${byAction}</tbody>
            </table>` : ""}
    `;
}

/** Rule editor: number inputs for each XP action. @tag PARENT XP */
function _ppXPRulesEditor(data) {
    const rules = data.rules || {};
    const defs  = data.defaults || {};
    const rows = _PP_XP_ACTIONS.map(([key, label]) => {
        const val  = rules[key] ?? defs[key] ?? 0;
        const def  = defs[key] ?? 0;
        const diff = val !== def;
        return `
            <tr>
                <td><strong>${label}</strong><div class="pp-xp-key">${key}</div></td>
                <td class="pp-xp-default">${def}</td>
                <td>
                    <input type="number" min="0" max="10000" step="1"
                           class="pp-xp-input${diff ? " changed" : ""}"
                           data-action="${key}" value="${val}">
                </td>
            </tr>`;
    }).join("");
    return `
        <div class="pp-section-title">XP Rules</div>
        <p class="pp-xp-hint">Per-action XP values. Changes take effect immediately for new awards; past XP is unchanged.</p>
        <table class="pp-log-table pp-xp-table">
            <thead><tr><th>Action</th><th style="width:80px">Default</th><th style="width:120px">Current</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
        <div class="pp-streak-actions">
            <button class="pp-btn primary" onclick="_ppSaveXPRules()">Save XP Rules</button>
            <button class="pp-btn secondary" onclick="_ppResetXPRules()">Reset to Defaults</button>
            <span id="pp-xp-msg" class="pp-streak-msg"></span>
        </div>`;
}

/** Arcade daily-cap editor. @tag PARENT XP ARCADE */
function _ppXPArcadeEditor(data) {
    const cur = data.arcade_daily_cap ?? 10;
    const def = data.arcade_cap_default ?? 10;
    return `
        <div class="pp-section-title">Arcade Daily XP Cap</div>
        <p class="pp-xp-hint">Max XP the child can earn from arcade games per day (default: ${def}).</p>
        <div class="pp-xp-arcade">
            <input type="number" id="pp-xp-arcade-cap" min="0" max="1000" step="1" value="${cur}">
            <button class="pp-btn primary" onclick="_ppSaveArcadeCap()">Save Cap</button>
            <span id="pp-xp-arcade-msg" class="pp-streak-msg"></span>
        </div>`;
}

/** Collect rule inputs and POST. @tag PARENT XP */
async function _ppSaveXPRules() {
    const rules = {};
    document.querySelectorAll(".pp-xp-input").forEach(i => {
        const v = parseInt(i.value, 10);
        if (!Number.isNaN(v) && v >= 0) rules[i.dataset.action] = v;
    });
    const msg = document.getElementById("pp-xp-msg");
    try {
        const res = await window._ppFetch("/api/parent/xp-rules", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rules }),
        });
        if (msg) {
            msg.textContent = res.ok ? "✓ Saved." : "Failed to save.";
            msg.style.color = res.ok ? "var(--color-success)" : "var(--color-error)";
        }
        if (res.ok) setTimeout(() => _ppLoadTab("xp"), 400);
    } catch (err) {
        console.error("[parent-xp] save failed:", err);
        if (msg) { msg.textContent = "Network error."; msg.style.color = "var(--color-error)"; }
    }
}

/** Reset all XP overrides to defaults. @tag PARENT XP */
async function _ppResetXPRules() {
    if (!confirm("Reset all XP rules (and arcade cap) to defaults?")) return;
    const msg = document.getElementById("pp-xp-msg");
    try {
        const res = await window._ppFetch("/api/parent/xp-rules/reset", { method: "POST" });
        if (msg) {
            msg.textContent = res.ok ? "✓ Reset." : "Failed.";
            msg.style.color = res.ok ? "var(--color-success)" : "var(--color-error)";
        }
        if (res.ok) setTimeout(() => _ppLoadTab("xp"), 400);
    } catch (err) {
        console.error("[parent-xp] reset failed:", err);
    }
}

/** Save arcade daily cap. @tag PARENT XP ARCADE */
async function _ppSaveArcadeCap() {
    const el = document.getElementById("pp-xp-arcade-cap");
    const v = parseInt(el && el.value, 10);
    const msg = document.getElementById("pp-xp-arcade-msg");
    if (Number.isNaN(v) || v < 0) {
        if (msg) { msg.textContent = "Invalid value."; msg.style.color = "var(--color-error)"; }
        return;
    }
    try {
        const res = await window._ppFetch("/api/parent/xp-rules", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ arcade_daily_cap: v }),
        });
        if (msg) {
            msg.textContent = res.ok ? "✓ Saved." : "Failed to save.";
            msg.style.color = res.ok ? "var(--color-success)" : "var(--color-error)";
        }
    } catch (err) {
        console.error("[parent-xp] arcade save failed:", err);
    }
}

window._ppXP              = _ppXP;
window._ppSaveXPRules     = _ppSaveXPRules;
window._ppResetXPRules    = _ppResetXPRules;
window._ppSaveArcadeCap   = _ppSaveArcadeCap;
