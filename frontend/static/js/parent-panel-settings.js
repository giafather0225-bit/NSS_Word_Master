/* ================================================================
   parent-panel-settings.js — Settings tab accordion + Test Mode + Island toggle
   Section: Parent
   Dependencies: core.js, parent-panel.js (_ppFetch, _ppEmpty)
   API endpoints: /api/parent/test-mode, /api/island/config,
                  /api/island/status, /api/island/config/update
   ================================================================ */

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
            <div class="pp-grid-2 pp-grid-2--gap20">
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
        <p id="pp-testmode-status" class="pp-testmode-status">
            ${active ? '<span class="pp-testmode-on-badge">TEST MODE is ON</span> — progression locks are disabled.' : 'Real mode active.'}
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
            if (typeof _loadTestMode === "function") await _loadTestMode();
            window.toast && window.toast(`Test mode ${checked ? "enabled" : "disabled"}.`, "success");
            if (status) status.innerHTML = checked
                ? '<span class="pp-testmode-on-badge">TEST MODE is ON</span> — progression locks are disabled.'
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
            : `<div class="pp-island-summary pp-island-summary--empty">No active characters yet.</div>`;

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
        el.innerHTML = `<p class="pp-island-error">Island config unavailable.</p>`;
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
