/* ================================================================
   parent-panel-settings.js — Parent Dashboard: Settings tab (Variant C)
   Section: Parent
   Dependencies: core.js, parent-panel.js, parent-panel-settings-forms.js
   API endpoints: /api/parent/test-mode, /api/parent/streak,
                  /api/parent/config/{key}, /api/island/config
   ================================================================ */

/** Settings tab entry. @tag PARENT SETTINGS */
async function _ppSettings(body) {
    try {
        const _safe = (p, fb) => p.catch(() => fb);
        const [testMode, streak, xpRules, reportSched, islandCfg, sysStatus] = await Promise.all([
            _safe(apiFetchJSON("/api/parent/test-mode"),       { test_mode: false }),
            _safe(apiFetchJSON("/api/parent/streak"),          { rule: {} }),
            _safe(apiFetchJSON("/api/parent/xp-rules"),        { rules: {} }),
            _safe(window._ppFetch("/api/parent/report/schedule").then(r => r.json()), {}),
            _safe(apiFetchJSON("/api/island/config"),          {}),
            _safe(apiFetchJSON("/api/system/status"),          {}),
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
            ${_ppSetSystemCard(sysStatus)}`;

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
                ${row("lock",           "Parent PIN",       "Set",                `<button class="pp-btn ghost pp-btn--sm" onclick="_ppTogglePinForm()">Change</button>`)}
                ${row("flask-conical",  "Test Mode",        tm ? "ON" : "OFF",    toggle("pp-tm-chk",       tm,       "_ppSaveTestMode(this.checked)"))}
                ${row("palmtree",       "Island enabled",   islandOn ? "ON" : "OFF", toggle("pp-island-chk", islandOn, "_ppSaveIslandToggle(this.checked)"))}
            </div>
            <div id="pp-pin-form" class="pp-form-row" style="display:none;margin-top:12px;padding:12px;background:var(--bg-surface);border-radius:var(--radius-md);">
                <div class="pp-form-row">
                    <label class="pp-form-label">Current PIN</label>
                    <div class="pp-pin-input-wrap" style="display:flex;align-items:center;gap:6px;">
                        <input id="pp-current-pin" class="pp-input" type="password" maxlength="4"
                               inputmode="numeric" pattern="[0-9]*" autocomplete="current-password"
                               placeholder="Enter current PIN" style="flex:1;" />
                        <button type="button" class="pp-btn ghost pp-btn--sm"
                                onclick="_ppTogglePinVisibility('pp-current-pin', this)"
                                aria-label="Show or hide PIN">
                            <i data-lucide="eye"></i>
                        </button>
                    </div>
                </div>
                <div class="pp-form-row" style="margin-top:8px;">
                    <label class="pp-form-label">New PIN (4 digits)</label>
                    <div class="pp-pin-input-wrap" style="display:flex;align-items:center;gap:6px;">
                        <input id="pp-new-pin" class="pp-input" type="password" maxlength="4"
                               inputmode="numeric" pattern="[0-9]*" autocomplete="new-password"
                               placeholder="Enter new PIN" style="flex:1;" />
                        <button type="button" class="pp-btn ghost pp-btn--sm"
                                onclick="_ppTogglePinVisibility('pp-new-pin', this)"
                                aria-label="Show or hide PIN">
                            <i data-lucide="eye"></i>
                        </button>
                    </div>
                </div>
                <div class="pp-form-row" style="margin-top:8px;">
                    <label class="pp-form-label">Confirm New PIN</label>
                    <div class="pp-pin-input-wrap" style="display:flex;align-items:center;gap:6px;">
                        <input id="pp-confirm-pin" class="pp-input" type="password" maxlength="4"
                               inputmode="numeric" pattern="[0-9]*" autocomplete="new-password"
                               placeholder="Re-enter new PIN" style="flex:1;" />
                        <button type="button" class="pp-btn ghost pp-btn--sm"
                                onclick="_ppTogglePinVisibility('pp-confirm-pin', this)"
                                aria-label="Show or hide PIN">
                            <i data-lucide="eye"></i>
                        </button>
                    </div>
                </div>
                <div style="display:flex;gap:8px;margin-top:12px;align-items:center;">
                    <button class="pp-btn primary" onclick="_ppSavePin()">Save</button>
                    <button class="pp-btn ghost" onclick="_ppTogglePinForm()">Cancel</button>
                    <div id="pp-pin-msg" class="pp-set-status" style="margin:0;"></div>
                </div>
                <div class="pp-form-hint" style="margin-top:8px;color:var(--text-hint);font-size:var(--font-size-xs);">
                    Avoid repeats (1111) and sequences (1234). The child should not be able to guess this.
                </div>
            </div>
            <div id="pp-tm-status" class="pp-set-status">${tm ? "Test mode active — locks bypassed." : "Real mode active."}</div>
        </div>`;
}

/** Toggle the inline Change-PIN form. @tag PARENT PIN */
function _ppTogglePinForm() {
    const f = document.getElementById("pp-pin-form");
    if (!f) return;
    const show = f.style.display === "none";
    f.style.display = show ? "block" : "none";
    if (show) {
        const i = document.getElementById("pp-current-pin");
        if (i) i.focus();
        if (window.lucide && lucide.createIcons) lucide.createIcons();
    } else {
        ["pp-current-pin", "pp-new-pin", "pp-confirm-pin"].forEach(id => {
            const el = document.getElementById(id);
            if (el) { el.value = ""; el.type = "password"; }
        });
        const msg = document.getElementById("pp-pin-msg");
        if (msg) { msg.textContent = ""; msg.classList.remove("error", "success"); }
    }
}

/** Toggle password/text visibility for a single PIN input. @tag PARENT PIN */
function _ppTogglePinVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    if (btn) {
        const icon = btn.querySelector("i[data-lucide]");
        if (icon) {
            icon.setAttribute("data-lucide", showing ? "eye" : "eye-off");
            if (window.lucide && lucide.createIcons) lucide.createIcons();
        }
    }
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
            <input type="checkbox" data-section-key="${s.key}" ${s.on ? "checked" : ""}
                   onchange="_ppSaveSectionToggle('${s.key}', this.checked)">
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
            <p class="pp-form-msg" id="pp-sections-msg"></p>
            <div class="pp-divider"></div>
            <div class="pp-mini-kick">Daily Words count</div>
            <div class="pp-dwc-row">
                <span class="mono pp-dwc-num">10</span>
                <span class="pp-dwc-unit">words / day</span>
            </div>
        </div>`;
}

/** Persist a single home section visibility toggle. @tag PARENT SETTINGS */
async function _ppSaveSectionToggle(key, checked) {
    const msg = document.getElementById("pp-sections-msg");
    try {
        const res = await window._ppFetch(`/api/parent/config/section_${key}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ value: checked ? "true" : "false" }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (msg) { msg.textContent = `${key} section ${checked ? "enabled" : "disabled"}.`; msg.className = "pp-form-msg success"; }
    } catch (err) {
        console.error("[section toggle] failed:", err);
        if (msg) { msg.textContent = "Failed to save."; msg.className = "pp-form-msg error"; }
        // Revert checkbox on failure
        const chk = document.querySelector(`[data-section-key="${key}"]`);
        if (chk) chk.checked = !checked;
    }
}

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
        const res = await window._ppFetch("/api/island/config/update", {
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

window._ppSettings            = _ppSettings;
window._ppTogglePinForm       = _ppTogglePinForm;
window._ppTogglePinVisibility = _ppTogglePinVisibility;
window._ppSaveTestMode        = _ppSaveTestMode;
window._ppSaveIslandToggle    = _ppSaveIslandToggle;
window._ppSaveSectionToggle   = _ppSaveSectionToggle;
