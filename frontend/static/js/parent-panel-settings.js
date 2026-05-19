/* ================================================================
   parent-panel-settings.js — Parent Dashboard: Settings tab (Variant C)
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/test-mode, /api/parent/streak,
                  /api/parent/xp-rules, /api/parent/report/schedule,
                  /api/parent/config/{key}, /api/system/*, /api/island/config
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

/** Settings tab entry. @tag PARENT SETTINGS */
async function _ppSettings(body) {
    try {
        const _safe = (p, fb) => p.catch(() => fb);
        const [testMode, streak, xpRules, reportSched, islandCfg] = await Promise.all([
            _safe(apiFetchJSON("/api/parent/test-mode"),       { test_mode: false }),
            _safe(apiFetchJSON("/api/parent/streak"),          { rule: {} }),
            _safe(apiFetchJSON("/api/parent/xp-rules"),        { rules: {} }),
            _safe(window._ppFetch("/api/parent/report/schedule").then(r => r.json()), {}),
            _safe(apiFetchJSON("/api/island/config"),          {}),
        ]);

        body.innerHTML = `
            <div class="pp-set-grid pp-set-grid--top">
                ${_ppSetAccessCard(testMode, islandCfg)}
                ${_ppSetHomeSectionsCard()}
            </div>
            <div class="pp-set-grid pp-set-grid--mid">
                ${_ppSetStreakRuleCard(streak.rule || {})}
                ${_ppSetXpRulesCard(xpRules.rules || {})}
            </div>
            ${_ppSetReportCard(reportSched)}
            ${_ppSetSystemCard()}`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-settings] load failed:", err);
        body.innerHTML = `<p class="pp-error-pad">Failed to load Settings.</p>`;
    }
}

/** Access & Mode card with toggles. @tag PARENT SETTINGS */
function _ppSetAccessCard(testMode, islandCfg) {
    const tm = !!testMode.test_mode;
    const islandOn = (islandCfg.config?.island_on !== "false") && (islandCfg.island_on !== false);

    const row = (icon, label, valueLabel, control) => `
        <div class="pp-set-row">
            <i data-lucide="${icon}" class="pp-set-row-icon"></i>
            <div class="pp-set-row-text">
                <div class="pp-set-row-label">${escapeHtml(label)}</div>
                <div class="pp-set-row-val">${valueLabel}</div>
            </div>
            ${control}
        </div>`;

    const toggle = (id, checked, onChange) => `
        <label class="pp-toggle">
            <input type="checkbox" id="${id}" ${checked ? "checked" : ""} onchange="${onChange}">
            <span class="pp-toggle-track"></span>
        </label>`;

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Access &amp; Mode</div>
            </div>
            <div class="pp-set-list">
                ${row("lock",           "Parent PIN",       "Set",                `<button class="pp-btn ghost pp-btn--sm" onclick="alert('Change PIN via legacy flow.')">Change</button>`)}
                ${row("flask-conical",  "Test Mode",        tm ? "ON" : "OFF",    toggle("pp-tm-chk",       tm,       "_ppSaveTestMode(this.checked)"))}
                ${row("palmtree",       "Island enabled",   islandOn ? "ON" : "OFF", toggle("pp-island-chk", islandOn, "_ppSaveIslandToggle(this.checked)"))}
            </div>
            <div id="pp-tm-status" class="pp-set-status">${tm ? "Test mode active — locks bypassed." : "Real mode active."}</div>
        </div>`;
}

/** Home sections toggle grid (6 sections). @tag PARENT SETTINGS */
function _ppSetHomeSectionsCard() {
    const sections = [
        { key: "english", label: "English", on: true },
        { key: "math",    label: "Math",    on: true },
        { key: "diary",   label: "Diary",   on: true },
        { key: "arcade",  label: "Arcade",  on: true },
        { key: "shop",    label: "Shop",    on: true },
        { key: "review",  label: "Review",  on: true },
    ];
    const cells = sections.map(s => `
        <label class="pp-home-section ${s.on ? "is-on" : ""}">
            <input type="checkbox" ${s.on ? "checked" : ""} disabled>
            <span class="pp-home-section-pill"></span>
            <span class="pp-home-section-label">${escapeHtml(s.label)}</span>
        </label>`).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Home sections
                    <span class="pp-panel-sub">Visible on child's home</span>
                </div>
            </div>
            <div class="pp-home-sec-grid">${cells}</div>
            <div class="pp-divider"></div>
            <div class="pp-mini-kick">Daily Words count</div>
            <div class="pp-dwc-row">
                <span class="mono pp-dwc-num">10</span>
                <span class="pp-dwc-unit">words / day</span>
            </div>
        </div>`;
}

/** Streak rule editor with radio cards. @tag PARENT STREAK */
function _ppSetStreakRuleCard(rule) {
    const subjects = rule.subjects || [];
    const mode = rule.mode || "all";
    const current = `${mode}|${subjects.slice().sort().join(",")}`;

    const rules = [
        { key: "any|english",              label: "English only",       desc: "Complete one English lesson today" },
        { key: "any|english,math",         label: "English or Math",    desc: "Complete English or Math today" },
        { key: "all|english,game,math",    label: "All three subjects", desc: "English, Math, and one game/arcade" },
        { key: "any|english,game,math",    label: "Any one subject",    desc: "At least one of English, Math, or game" },
    ];

    const rows = rules.map(r => {
        const isCurrent = r.key === current;
        return `
            <label class="pp-rule-card ${isCurrent ? "is-current" : ""}">
                <span class="pp-rule-radio ${isCurrent ? "is-current" : ""}"></span>
                <span class="pp-rule-body">
                    <span class="pp-rule-label">${escapeHtml(r.label)}</span>
                    <span class="pp-rule-desc">${escapeHtml(r.desc)}</span>
                </span>
            </label>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Streak rule
                    <span class="pp-panel-sub">What counts as one streak day · current: ${escapeHtml(current)}</span>
                </div>
            </div>
            <div class="pp-rule-list">${rows}</div>
            <div class="pp-panel-foot">
                <span class="pp-text-hint">After changing, optionally recalculate past streaks.</span>
                <button class="pp-btn ghost pp-btn--sm" onclick="_ppRecalcStreak()">Recalculate</button>
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
                <button class="pp-btn ghost pp-btn--sm" onclick="alert('Reset via /api/parent/xp-rules POST { action: reset }')">Reset to defaults</button>
            </div>
            <div class="pp-xprule-grid">${cells || `<p class="pp-text-hint">No XP rules loaded.</p>`}</div>
        </div>`;
}

/** Weekly email report card. @tag PARENT REPORT */
function _ppSetReportCard(sched) {
    const enabled = !!sched.enabled;
    const day = sched.send_day || "Sun";
    const time = sched.send_time || "20:00";
    const email = sched.email || "";
    const lastSent = sched.last_sent || "—";

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Weekly report · email
                    <span class="pp-panel-sub">${enabled ? `Active · sends ${escapeHtml(day)} at ${escapeHtml(time)}` : "Disabled"}</span>
                </div>
                <div class="pp-rep-actions">
                    <button class="pp-btn ghost pp-btn--sm" onclick="_ppPreviewReport()">Preview</button>
                    <button class="pp-btn primary pp-btn--sm" onclick="_ppSendReportNow()">Send now</button>
                </div>
            </div>
            <div class="pp-rep-grid">
                <div class="pp-rep-field">
                    <div class="pp-mini-kick">Email</div>
                    <div class="mono pp-rep-val">${escapeHtml(email || "(not set)")}</div>
                </div>
                <div class="pp-rep-field">
                    <div class="pp-mini-kick">Last sent</div>
                    <div class="mono pp-rep-val">${escapeHtml(lastSent.slice(0, 19))}</div>
                </div>
                <div class="pp-rep-field">
                    <div class="pp-mini-kick">Status</div>
                    <div class="pp-rep-val">
                        <span class="pp-pill ${enabled ? "pp-pill--ok" : "pp-pill--ink"}">
                            ${enabled ? "Active" : "Off"}
                        </span>
                    </div>
                </div>
            </div>
        </div>`;
}

/** System status 4-cell grid + action buttons. @tag PARENT SYSTEM */
function _ppSetSystemCard() {
    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">System status</div>
            </div>
            <div class="pp-sys-grid pp-sys-grid--4">
                <div class="pp-sys-cell">
                    <div class="pp-sys-label">App version</div>
                    <div class="mono pp-sys-val">v0.9.4</div>
                </div>
                <div class="pp-sys-cell">
                    <div class="pp-sys-label">AI engine</div>
                    <div class="pp-sys-val pp-sys-val--flex">
                        <span class="pp-sys-dot is-on"></span>
                        Running
                    </div>
                    <div class="pp-sys-meta mono">gemma2:2b</div>
                </div>
                <div class="pp-sys-cell">
                    <div class="pp-sys-label">Database backups</div>
                    <div class="pp-sys-val pp-sys-val--flex">
                        <i data-lucide="check-circle" class="pp-sys-icon-ok"></i>
                        <span class="mono">today</span>
                    </div>
                    <div class="pp-sys-meta">7-day rolling</div>
                </div>
                <div class="pp-sys-cell">
                    <div class="pp-sys-label">Asset check</div>
                    <div class="pp-sys-val">
                        <span class="mono pp-sys-asset-ok">—</span>
                        <span class="pp-sys-asset-sub">ready</span>
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

/** Save test_mode toggle (PIN-gated POST). @tag PARENT SETTINGS */
async function _ppSaveTestMode(checked) {
    try {
        const res = await window._ppFetch("/api/parent/test-mode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled: checked }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const status = document.getElementById("pp-tm-status");
        if (status) status.textContent = checked ? "Test mode active — locks bypassed." : "Real mode active.";
    } catch (err) {
        console.error("[save test-mode] failed:", err);
        alert("Failed to update test mode.");
        const chk = document.getElementById("pp-tm-chk");
        if (chk) chk.checked = !checked;
    }
}

/** Save island_on toggle (PIN-gated POST). @tag PARENT ISLAND */
async function _ppSaveIslandToggle(checked) {
    try {
        const res = await window._ppFetch("/api/island/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ island_on: checked }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
        console.error("[save island] failed:", err);
        alert("Failed to toggle island.");
        const chk = document.getElementById("pp-island-chk");
        if (chk) chk.checked = !checked;
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
        const res = await window._ppFetch("/api/system/backup", { method: "POST" });
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

/** Stub: check for updates. @tag PARENT SYSTEM */
function _ppCheckUpdates() {
    if (window.showToast) window.showToast("Update checker not implemented.", "info");
}

window._ppSettings         = _ppSettings;
window._ppSaveTestMode     = _ppSaveTestMode;
window._ppSaveIslandToggle = _ppSaveIslandToggle;
window._ppRecalcStreak     = _ppRecalcStreak;
window._ppPreviewReport    = _ppPreviewReport;
window._ppSendReportNow    = _ppSendReportNow;
window._ppRunBackup        = _ppRunBackup;
window._ppRestartOllama    = _ppRestartOllama;
window._ppCheckUpdates     = _ppCheckUpdates;
