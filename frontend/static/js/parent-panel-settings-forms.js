/* ================================================================
   parent-panel-settings-forms.js — Parent Dashboard: Settings form panels
   Section: Parent
   Dependencies: core.js, parent-panel.js, parent-panel-settings.js
   API endpoints: /api/parent/streak, /api/parent/xp-rules,
                  /api/parent/report/schedule, /api/parent/report/{preview,send},
                  /api/parent/streak-recalc, /api/system/*
   ================================================================ */

const _PP_XP_RULE_META = {
    word_correct:               { label: "Word correct",                cat: "english" },
    stage_complete:             { label: "Stage complete",              cat: "english" },
    final_test_pass:            { label: "Final test pass",             cat: "english" },
    unit_test_pass:             { label: "Unit test pass",              cat: "english" },
    daily_words_complete:       { label: "Daily Words complete",        cat: "english" },
    weekly_test_pass:           { label: "Weekly test pass",            cat: "english" },
    mywords_weekly_test_pass:   { label: "My Words weekly test",        cat: "english" },
    review_complete:            { label: "Review complete",             cat: "review"  },
    journal_complete:           { label: "Journal complete",            cat: "diary"   },
    must_do_bonus:              { label: "Must-do bonus",               cat: "english" },
    all_complete_bonus:         { label: "All complete bonus",          cat: "english" },
    streak_7_bonus:             { label: "7-day streak bonus",          cat: "diary"   },
    streak_30_bonus:            { label: "30-day streak bonus",         cat: "diary"   },
    math_lesson_complete:       { label: "Math lesson complete",        cat: "math"    },
    math_unit_test_pass:        { label: "Math unit test pass",         cat: "math"    },
    math_daily_complete:        { label: "Math Daily complete",         cat: "math"    },
    math_kangaroo_complete:     { label: "Kangaroo set complete",       cat: "math"    },
    math_kangaroo_80:           { label: "Kangaroo ≥80%",               cat: "math"    },
    math_kangaroo_perfect:      { label: "Kangaroo perfect",            cat: "math"    },
    ckla_lesson_complete:       { label: "CKLA lesson complete",        cat: "english" },
    ckla_domain_test_pass:      { label: "CKLA Domain Test pass",       cat: "english" },
    ckla_grade_final_pass:      { label: "CKLA Grade Final pass",       cat: "english" },
};

/** Streak rule editor — checkboxes + mode radios wired to _ppSaveStreakRule. @tag PARENT STREAK */
function _ppSetStreakRuleCard(rule) {
    const subjects = rule.subjects || [];
    const mode     = rule.mode || "all";

    const SUBJECTS = [
        { key: "ckla", label: "CKLA", icon: "layers" },
        { key: "math", label: "Math", icon: "calculator" },
        { key: "game", label: "Game", icon: "gamepad-2" },
    ];

    const checks = SUBJECTS.map(s => `
        <label class="pp-streak-check-label">
            <input type="checkbox" class="pp-streak-check-input" value="${s.key}"
                   ${subjects.includes(s.key) ? "checked" : ""}>
            <i data-lucide="${s.icon}" class="pp-streak-check-icon"></i>
            <span>${escapeHtml(s.label)}</span>
        </label>`).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Streak rule
                    <span class="pp-panel-sub">What counts as one streak day</span>
                </div>
            </div>
            <div class="pp-mini-kick">Subjects</div>
            <div class="pp-streak-checks">${checks}</div>
            <div class="pp-mini-kick pp-mini-kick--mt8">Mode</div>
            <div class="pp-streak-mode-row">
                <label class="pp-streak-mode-label">
                    <input type="radio" name="pp-streak-mode" value="all" ${mode === "all" ? "checked" : ""}>
                    <span>All selected — every subject must be completed</span>
                </label>
                <label class="pp-streak-mode-label">
                    <input type="radio" name="pp-streak-mode" value="any" ${mode === "any" ? "checked" : ""}>
                    <span>Any one — at least one subject is enough</span>
                </label>
            </div>
            <p class="pp-form-msg" id="pp-streak-msg"></p>
            <div class="pp-panel-foot">
                <button class="pp-btn primary pp-btn--sm" onclick="_ppSaveStreakRule()">Save rule</button>
                <button class="pp-btn ghost  pp-btn--sm" onclick="_ppRecalcStreak()">Recalculate</button>
            </div>
        </div>`;
}

/** XP rules editor — 2-col grid with category dot + label + value. @tag PARENT XP */
function _ppSetXpRulesCard(rules) {
    const catColor = {
        math:    "var(--math-primary)",
        english: "var(--english-primary)",
        diary:   "var(--diary-primary)",
        review:  "var(--review-primary)",
    };

    const cells = Object.entries(rules).slice(0, 16).map(([key, value]) => {
        const meta = _PP_XP_RULE_META[key] || { label: key, cat: "english" };
        const color = catColor[meta.cat] || "var(--ink-3)";
        return `
            <div class="pp-xprule-row">
                <span class="pp-xprule-dot" style="background:${color}"></span>
                <span class="pp-xprule-label">${escapeHtml(meta.label)}</span>
                <span class="mono pp-xprule-val">+${value} XP</span>
            </div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">XP rules
                    <span class="pp-panel-sub">How much XP each action awards</span>
                </div>
                <button class="pp-btn ghost pp-btn--sm" onclick="_ppResetXPRules()">Reset to defaults</button>
            </div>
            <div class="pp-xprule-grid">${cells || `<p class="pp-text-hint">No XP rules loaded.</p>`}</div>
        </div>`;
}

/** Weekly email report card — save form wired to _ppSaveReportSchedule. @tag PARENT REPORT */
function _ppSetReportCard(sched) {
    const dow       = sched.day_of_week != null ? sched.day_of_week : 0;
    const childName = sched.child_name   || "";
    const email     = sched.parent_email || "(not set)";

    const DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
    const dayOpts = DAYS.map((d, i) =>
        `<option value="${i}" ${dow === i ? "selected" : ""}>${d}</option>`).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Weekly report · email
                    <span class="pp-panel-sub">Sends to ${escapeHtml(email)}</span>
                </div>
                <div class="pp-rep-actions">
                    <button class="pp-btn ghost pp-btn--sm" onclick="_ppPreviewReport()">Preview</button>
                    <button class="pp-btn primary pp-btn--sm" onclick="_ppSendReportNow()">Send now</button>
                </div>
            </div>
            <div class="pp-rep-form">
                <div class="pp-toggle-row" style="margin-bottom:10px;">
                    <label class="pp-toggle">
                        <input type="checkbox" id="pp-rep-enabled">
                        <span class="pp-toggle-track"></span>
                    </label>
                    <span class="pp-form-label">Enable weekly email</span>
                </div>
                <div class="pp-form-row">
                    <label class="pp-form-label" for="pp-rep-name">Child name in email</label>
                    <input id="pp-rep-name" class="pp-input" type="text" maxlength="80"
                           value="${escapeHtml(childName)}" placeholder="e.g. Gia">
                </div>
                <div class="pp-form-row" style="margin-top:8px;">
                    <label class="pp-form-label" for="pp-rep-day">Send day</label>
                    <select id="pp-rep-day" class="pp-input">${dayOpts}</select>
                </div>
                <div style="display:flex;gap:8px;margin-top:12px;">
                    <button class="pp-btn primary pp-btn--sm" onclick="_ppSaveReportSchedule()">Save schedule</button>
                </div>
                <p class="pp-form-msg" id="pp-rep-msg"></p>
            </div>
        </div>`;
}

/** System status grid + action buttons — renders live data from /api/system/status. @tag PARENT SYSTEM */
function _ppSetSystemCard(sys) {
    const ollama      = sys?.ollama  || {};
    const backups     = sys?.backups || {};
    const ollamaOn    = !!ollama.running;
    const ollamaModel = ollama.model || "gemma2:2b";
    const bkCount     = backups.count  != null ? backups.count  : "—";
    const bkLatest    = backups.latest ? backups.latest.slice(0, 10) : "—";

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">System status</div>
            </div>
            <div class="pp-sys-grid pp-sys-grid--4">
                <div class="pp-sys-cell">
                    <div class="pp-sys-label">AI engine</div>
                    <div class="pp-sys-val pp-sys-val--flex">
                        <span class="pp-sys-dot ${ollamaOn ? "is-on" : "is-off"}"></span>
                        ${ollamaOn ? "Running" : "Offline"}
                    </div>
                    <div class="pp-sys-meta mono">${escapeHtml(ollamaModel)}</div>
                </div>
                <div class="pp-sys-cell">
                    <div class="pp-sys-label">Database backups</div>
                    <div class="pp-sys-val pp-sys-val--flex">
                        <i data-lucide="archive" class="pp-sys-icon-ok"></i>
                        <span class="mono">${escapeHtml(bkLatest)}</span>
                    </div>
                    <div class="pp-sys-meta">${bkCount} backup${bkCount !== 1 ? "s" : ""} kept</div>
                </div>
                <div class="pp-sys-cell">
                    <div class="pp-sys-label" id="pp-update-label">Updates</div>
                    <div class="pp-sys-val">
                        <span class="mono" id="pp-update-val">—</span>
                    </div>
                </div>
            </div>
            <div class="pp-sys-actions">
                <button class="pp-btn ghost pp-btn--sm" onclick="_ppRunBackup()">
                    <i data-lucide="archive"></i>Run backup
                </button>
                <button class="pp-btn ghost pp-btn--sm" onclick="_ppRestartOllama()">
                    <i data-lucide="rotate-ccw"></i>Restart Ollama
                </button>
                <button class="pp-btn ghost pp-btn--sm" onclick="_ppCheckUpdates()">
                    <i data-lucide="search"></i>Check updates
                </button>
            </div>
        </div>`;
}

// ─── Mutations ────────────────────────────────────────────────

/** Reset all XP rules to defaults via POST /api/parent/xp-rules/reset. @tag PARENT XP */
async function _ppResetXPRules() {
    if (!confirm("Reset all XP rules to default values?")) return;
    try {
        const res = await window._ppFetch("/api/parent/xp-rules/reset", { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (window.showToast) window.showToast("XP rules reset to defaults.", "success");
        // Reload settings tab to reflect new values
        if (typeof _ppLoadTab === "function") setTimeout(() => _ppLoadTab("settings"), 600);
    } catch (err) {
        console.error("[reset xp rules] failed:", err);
        alert("Failed to reset XP rules.");
    }
}

/** Trigger backend streak recalc. @tag PARENT STREAK */
async function _ppRecalcStreak() {
    try {
        const res = await window._ppFetch("/api/parent/streak-recalc", { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (window.showToast) window.showToast("Streak recalculated.", "success");
    } catch (err) {
        alert("Failed to recalculate streak.");
    }
}

/** Preview weekly report HTML. @tag PARENT REPORT */
async function _ppPreviewReport() {
    window.open("/api/parent/report/preview", "_blank");
}

/** Send weekly report immediately. @tag PARENT REPORT */
async function _ppSendReportNow() {
    if (!confirm("Send weekly report now to the configured email?")) return;
    try {
        const res = await window._ppFetch("/api/parent/report/send", { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (window.showToast) window.showToast("Report sent.", "success");
    } catch (err) {
        alert("Failed to send report.");
    }
}

/** Trigger backup. @tag PARENT SYSTEM BACKUP */
async function _ppRunBackup() {
    try {
        const res = await window._ppFetch("/api/system/backups", { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (window.showToast) window.showToast("Backup created.", "success");
    } catch (err) {
        alert("Failed to run backup.");
    }
}

/** Restart Ollama service. @tag PARENT SYSTEM OLLAMA */
async function _ppRestartOllama() {
    try {
        const res = await window._ppFetch("/api/system/ollama/restart", { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (window.showToast) window.showToast("Ollama restarted.", "success");
    } catch (err) {
        alert("Failed to restart Ollama.");
    }
}

/** Check for app updates via /api/system/check-update. @tag PARENT SYSTEM */
async function _ppCheckUpdates() {
    const val   = document.getElementById("pp-update-val");
    const label = document.getElementById("pp-update-label");
    if (val) val.textContent = "checking…";
    try {
        const data = await apiFetchJSON("/api/system/check-update");
        const available = !!data.update_available;
        const text = available
            ? `Update available (${(data.local_head || "").slice(0, 7)})`
            : "Up to date";
        if (val)   val.textContent   = text;
        if (label) label.textContent = available ? "Update!" : "Updates";
        if (window.showToast) window.showToast(text, available ? "info" : "success");
    } catch (err) {
        if (val) val.textContent = "check failed";
        if (window.showToast) window.showToast("Update check failed.", "error");
    }
}

window._ppResetXPRules     = _ppResetXPRules;
window._ppSetStreakRuleCard = _ppSetStreakRuleCard;
window._ppSetXpRulesCard   = _ppSetXpRulesCard;
window._ppSetReportCard    = _ppSetReportCard;
window._ppSetSystemCard    = _ppSetSystemCard;
window._ppRecalcStreak     = _ppRecalcStreak;
window._ppPreviewReport    = _ppPreviewReport;
window._ppSendReportNow    = _ppSendReportNow;
window._ppRunBackup        = _ppRunBackup;
window._ppRestartOllama    = _ppRestartOllama;
window._ppCheckUpdates     = _ppCheckUpdates;
