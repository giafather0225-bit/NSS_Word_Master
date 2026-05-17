/* ================================================================
   parent-settings.js — Parent Dashboard: Tasks, Schedule, PIN change
   Section: Parent
   Dependencies: parent-panel.js (ppRenderTasks, ppRenderSchedule, ppRenderPin)
   API endpoints: /api/parent/task-settings, /api/parent/academy-schedule,
                  /api/parent/config
   ================================================================ */

// ─── Task Settings ────────────────────────────────────────────

/**
 * Render task settings toggle list.
 * Called by parent-panel.js _ppLoadTab('tasks').
 * @tag PARENT SETTINGS
 */
async function ppRenderTasks(body) {
    try {
        const data = await apiFetchJSON("/api/parent/task-settings");
        const rows = (data.tasks || []).map(t => {
            const label = t.task_key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
            return `<div class="pp-task-row">
                <span class="pp-task-key">${label}</span>
                <span class="pp-task-xp">+${t.xp_value} XP</span>
                <label class="pp-toggle">
                    <input type="checkbox" ${t.is_active ? "checked" : ""}
                           data-task-key="${t.task_key}">
                    <span class="pp-toggle-track"></span>
                </label>
                ${t.is_required
                    ? `<span class="pp-required-label">Required</span>`
                    : `<button class="pp-btn secondary pp-btn--sm"
                               data-task-key="${t.task_key}">Make Required</button>`}
            </div>`;
        }).join("");
        body.innerHTML = `
            <div class="pp-section-title">Today's Tasks</div>
            <div class="pp-task-list">${rows || "<p class='pp-text-secondary'>No tasks configured.</p>"}</div>
            <p class="pp-form-hint pp-form-hint--mt12">Toggle to show/hide tasks on the Home screen.</p>`;
        body.querySelectorAll('input[data-task-key]').forEach(cb => {
            cb.addEventListener('change', function() {
                _ppToggleTask(this.dataset.taskKey, this.checked);
            });
        });
        body.querySelectorAll('button[data-task-key]').forEach(btn => {
            btn.addEventListener('click', function() {
                _ppToggleRequired(this.dataset.taskKey, true);
            });
        });
    } catch (_) { body.innerHTML = `<p class="pp-error-pad">Failed to load.</p>`; }
}

/** Toggle task is_active. PIN-protected. @tag PARENT SETTINGS */
async function _ppToggleTask(key, isActive) {
    try {
        await window._ppFetch(`/api/parent/task-settings/${key}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: isActive }),
        });
    } catch (_) {}
}

/** Toggle task is_required star. PIN-protected. @tag PARENT SETTINGS */
async function _ppToggleRequired(key, isRequired) {
    try {
        await window._ppFetch(`/api/parent/task-settings/${key}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_required: isRequired }),
        });
        // Re-render tasks tab
        const body = document.getElementById("pp-body");
        if (body) await ppRenderTasks(body);
    } catch (_) {}
}

// ─── Academy Schedule ─────────────────────────────────────────

const _DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/**
 * Render academy test schedule day-picker.
 * Called by parent-panel.js _ppLoadTab('schedule').
 * @tag PARENT SCHEDULE
 */
async function ppRenderSchedule(body) {
    let activeDays = new Set();
    try {
        const data = await apiFetchJSON("/api/parent/academy-schedule");
        (data.days || []).forEach(d => activeDays.add(d.day_of_week));
    } catch (_) {}

    window._ppScheduleDays = new Set(activeDays);

    const pills = _DAY_NAMES.map((name, i) =>
        `<div class="pp-day-pill${activeDays.has(i) ? " selected" : ""}"
              onclick="_ppToggleDay(${i}, this)">${name}</div>`
    ).join("");

    body.innerHTML = `
        <div class="pp-section-title">Test / Academy Days</div>
        <p class="pp-form-hint-sm pp-form-hint--mb12">Select days when academy tests are scheduled.</p>
        <div class="pp-week-picker">${pills}</div>
        <button class="pp-btn primary" onclick="_ppSaveSchedule()">Save Schedule</button>
        <p id="pp-sched-msg" class="pp-form-msg pp-form-msg--mt8"></p>`;
}

/** Toggle a day pill on/off. @tag PARENT SCHEDULE */
function _ppToggleDay(dayIndex, el) {
    const days = window._ppScheduleDays || new Set();
    if (days.has(dayIndex)) { days.delete(dayIndex); el.classList.remove("selected"); }
    else                    { days.add(dayIndex);    el.classList.add("selected"); }
    window._ppScheduleDays = days;
}

/** POST updated schedule. PIN-protected. @tag PARENT SCHEDULE */
async function _ppSaveSchedule() {
    const days = Array.from(window._ppScheduleDays || []);
    try {
        const res = await window._ppFetch("/api/parent/academy-schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ days }),
        });
        const msg = document.getElementById("pp-sched-msg");
        if (msg) msg.textContent = res.ok ? "Saved!" : "Failed to save.";
        if (msg) msg.style.color = res.ok ? "var(--color-success)" : "var(--color-error)";
    } catch (_) {}
}

// ─── Change PIN ───────────────────────────────────────────────

/**
 * Render the Change PIN form.
 * Called by parent-panel.js _ppLoadTab('pin').
 * @tag PARENT PIN
 */
function ppRenderPin(body) {
    const themeIsDark = localStorage.getItem("gia-theme") === "dark";
    body.innerHTML = `
        <div class="pp-grid-2 pp-grid-2--top pp-grid-2--mb0">
            <div>
                <div class="pp-section-title pp-section-title--no-top">Appearance</div>
                <label class="pp-toggle-row">
                    <input id="pp-theme-toggle" type="checkbox" ${themeIsDark ? "checked" : ""} onchange="_ppToggleTheme(this.checked)">
                    <span><i data-lucide="moon" class="pp-icon-14v"></i> Dark mode</span>
                </label>
            </div>
            <div>
                <div class="pp-section-title pp-section-title--no-top">Parent Email</div>
                <div class="pp-form-stack">
                    <div>
                        <label class="pp-form-label">Notification email</label>
                        <input id="pp-parent-email" class="pp-input" type="email"
                               placeholder="parent@example.com" autocomplete="email" />
                        <p class="pp-form-hint">GIA's Day Off requests will be sent here.</p>
                    </div>
                    <button class="pp-btn primary" onclick="_ppSaveParentEmail()">Save Email</button>
                    <p id="pp-email-msg" class="pp-form-msg"></p>
                </div>
            </div>
        </div>

        <div class="pp-section-divider"></div>

        <div class="pp-section-title">Change PIN</div>
        <div class="pp-form-stack">
            <div>
                <label class="pp-form-label">New PIN (4 digits)</label>
                <input id="pp-new-pin" class="pp-input" type="password" maxlength="4"
                       inputmode="numeric" placeholder="Enter new PIN" autocomplete="new-password" />
            </div>
            <div>
                <label class="pp-form-label">Confirm PIN</label>
                <input id="pp-confirm-pin" class="pp-input" type="password" maxlength="4"
                       inputmode="numeric" placeholder="Confirm new PIN" autocomplete="new-password" />
            </div>
            <button class="pp-btn primary" onclick="_ppSavePin()">Change PIN</button>
            <p id="pp-pin-msg" class="pp-form-msg"></p>
        </div>`;

    _ppLoadParentEmail();
    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** Apply or clear the dark theme + persist via localStorage. @tag PARENT SETTINGS THEME */
function _ppToggleTheme(enabled) {
    if (enabled) {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("gia-theme", "dark");
    } else {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem("gia-theme", "light");
    }
}
window._ppToggleTheme = _ppToggleTheme;

/** Load existing parent email into the input. @tag PARENT SETTINGS */
async function _ppLoadParentEmail() {
    const input = document.getElementById("pp-parent-email");
    if (!input) return;
    try {
        const res = await fetch("/api/parent/config/parent_email");
        if (!res.ok) return;
        const data = await res.json();
        input.value = data.value || "";
    } catch (_) {}
}

/** Save parent email via /api/parent/config. @tag PARENT SETTINGS */
async function _ppSaveParentEmail() {
    const input = document.getElementById("pp-parent-email");
    const msg   = document.getElementById("pp-email-msg");
    const value = (input?.value || "").trim();
    if (msg) { msg.textContent = ""; msg.classList.remove("error", "success"); }
    try {
        const res = await window._ppFetch("/api/parent/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: "parent_email", value }),
        });
        if (msg) {
            if (res.ok) {
                msg.textContent = value ? "Email saved." : "Email cleared.";
                msg.classList.add("success");
            } else {
                const err = await res.json().catch(() => ({}));
                msg.textContent = err.detail || "Failed to save.";
                msg.classList.add("error");
            }
        }
    } catch (_) {
        if (msg) { msg.textContent = "Network error."; msg.classList.add("error"); }
    }
}

// ─── CKLA Settings ────────────────────────────────────────────

const _CKLA_CFG_KEYS = [
    "ckla_daily_goal", "ckla_vacation_end", "ckla_domain_order_fixed",
    "ckla_domain_pass_pct", "ckla_grade_pass_pct", "ckla_show_hints", "ckla_g4_unlocked",
];

/**
 * Render CKLA-specific settings (daily goal, vacation date, pass thresholds, G4 unlock).
 * @tag PARENT SETTINGS CKLA
 */
async function ppRenderCKLASettings(body) {
    if (!body) return;
    body.innerHTML = `<p class="pp-form-hint-sm">Loading…</p>`;
    try {
        const vals = {};
        await Promise.all(_CKLA_CFG_KEYS.map(async k => {
            try {
                const r = await fetch(`/api/parent/config/${k}`);
                if (r.ok) vals[k] = (await r.json()).value;
            } catch (_) {}
        }));

        const dailyGoal  = vals.ckla_daily_goal     || "1";
        const vacEnd     = vals.ckla_vacation_end    || "";
        const orderFixed = vals.ckla_domain_order_fixed === "true";
        const domainPct  = vals.ckla_domain_pass_pct || "80";
        const gradePct   = vals.ckla_grade_pass_pct  || "80";
        const showHints  = vals.ckla_show_hints !== "false";
        const g4Unlocked = vals.ckla_g4_unlocked === "true";

        body.innerHTML = `
            <div class="pp-col-12">
                <div class="pp-grid-2 pp-grid-2--gap12">
                    <div>
                        <label class="pp-form-label">Daily Lesson Goal</label>
                        <input id="ckla-daily-goal" class="pp-input" type="number"
                               min="1" max="10" value="${dailyGoal}" />
                        <p class="pp-form-hint">Lessons per day target (auto mode).</p>
                    </div>
                    <div>
                        <label class="pp-form-label">Vacation End Date</label>
                        <input id="ckla-vacation-end" class="pp-input" type="date"
                               value="${vacEnd}" />
                        <p class="pp-form-hint">Intensive pace until this date.</p>
                    </div>
                </div>
                <div class="pp-grid-2 pp-grid-2--gap12 pp-grid-2--mt4">
                    <div>
                        <label class="pp-form-label">Domain Test Pass %</label>
                        <input id="ckla-domain-pct" class="pp-input" type="number"
                               min="50" max="100" value="${domainPct}" />
                    </div>
                    <div>
                        <label class="pp-form-label">Grade Final Test Pass %</label>
                        <input id="ckla-grade-pct" class="pp-input" type="number"
                               min="50" max="100" value="${gradePct}" />
                    </div>
                </div>
                <label class="pp-toggle-row pp-toggle-row--mt4">
                    <input id="ckla-order-fixed" type="checkbox" ${orderFixed ? "checked" : ""}>
                    <span>Enforce Domain Order (sequential only)</span>
                </label>
                <label class="pp-toggle-row">
                    <input id="ckla-show-hints" type="checkbox" ${showHints ? "checked" : ""}>
                    <span>Show Hint Button in Word Work</span>
                </label>
                <button class="pp-btn primary pp-btn--mt4"
                        onclick="ppSaveCKLASettings()">Save CKLA Settings</button>
                <p id="ckla-settings-msg" class="pp-form-msg"></p>

                <div class="pp-section-divider pp-section-divider--16"></div>
                <label class="pp-form-label">Grade 4 Access</label>
                ${g4Unlocked
                    ? `<p class="pp-ckla-g4-label">Grade 4 is unlocked.</p>`
                    : `<button class="pp-btn secondary pp-btn--mt4" onclick="ppForceUnlockG4()">
                           Force Unlock Grade 4
                       </button>`}
                <p class="pp-form-hint">Override the G3 Final Test requirement and give access to Grade 4.</p>
                <p id="ckla-g4-msg" class="pp-form-msg"></p>
            </div>`;
    } catch (_) {
        body.innerHTML = `<p class="pp-error-pad--compact">Failed to load CKLA settings.</p>`;
    }
}

/** Save CKLA config values. PIN-protected via window._ppFetch. @tag PARENT SETTINGS CKLA */
async function ppSaveCKLASettings() {
    const msg    = document.getElementById("ckla-settings-msg");
    const setMsg = (text, kind) => {
        if (!msg) return;
        msg.textContent = text;
        msg.classList.remove("error", "success");
        if (kind) msg.classList.add(kind);
    };

    const dailyGoalRaw = parseInt(document.getElementById("ckla-daily-goal")?.value || "1", 10);
    const domainPctRaw = parseInt(document.getElementById("ckla-domain-pct")?.value  || "80", 10);
    const gradePctRaw  = parseInt(document.getElementById("ckla-grade-pct")?.value   || "80", 10);

    if (isNaN(dailyGoalRaw) || dailyGoalRaw < 1 || dailyGoalRaw > 10) {
        setMsg("Daily goal must be 1–10.", "error"); return;
    }
    if (isNaN(domainPctRaw) || domainPctRaw < 50 || domainPctRaw > 100) {
        setMsg("Domain pass % must be 50–100.", "error"); return;
    }
    if (isNaN(gradePctRaw) || gradePctRaw < 50 || gradePctRaw > 100) {
        setMsg("Grade pass % must be 50–100.", "error"); return;
    }

    const configs = [
        { key: "ckla_daily_goal",          value: String(dailyGoalRaw) },
        { key: "ckla_vacation_end",         value: document.getElementById("ckla-vacation-end")?.value || "" },
        { key: "ckla_domain_pass_pct",      value: String(domainPctRaw) },
        { key: "ckla_grade_pass_pct",       value: String(gradePctRaw) },
        { key: "ckla_domain_order_fixed",   value: document.getElementById("ckla-order-fixed")?.checked  ? "true" : "false" },
        { key: "ckla_show_hints",           value: document.getElementById("ckla-show-hints")?.checked   ? "true" : "false" },
    ];

    try {
        const results = await Promise.all(configs.map(c =>
            window._ppFetch("/api/parent/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(c),
            })
        ));
        const allOk = results.every(r => r.ok);
        setMsg(allOk ? "CKLA settings saved." : "Some settings failed to save.", allOk ? "success" : "error");
    } catch (_) {
        setMsg("Network error.", "error");
    }
}

/** Force-unlock Grade 4 by setting ckla_g4_unlocked = "true". PIN-protected. @tag PARENT SETTINGS CKLA */
async function ppForceUnlockG4() {
    const msg    = document.getElementById("ckla-g4-msg");
    const setMsg = (text, kind) => {
        if (!msg) return;
        msg.textContent = text;
        msg.classList.remove("error", "success");
        if (kind) msg.classList.add(kind);
    };
    try {
        const res = await window._ppFetch("/api/parent/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: "ckla_g4_unlocked", value: "true" }),
        });
        if (res.ok) {
            const cklaEl = document.getElementById("pp-settings-ckla");
            if (cklaEl) await ppRenderCKLASettings(cklaEl);
        } else {
            setMsg("Failed to unlock.", "error");
        }
    } catch (_) {
        setMsg("Network error.", "error");
    }
}

/** POST new PIN to /api/parent/config. Requires current PIN to already be verified. @tag PARENT PIN */
async function _ppSavePin() {
    const newPin  = document.getElementById("pp-new-pin")?.value.trim();
    const confirm = document.getElementById("pp-confirm-pin")?.value.trim();
    const msg     = document.getElementById("pp-pin-msg");
    const setMsg  = (text, kind) => {
        if (!msg) return;
        msg.textContent = text;
        msg.classList.remove("error", "success");
        if (kind) msg.classList.add(kind);
    };
    if (!newPin || newPin.length !== 4 || !/^\d+$/.test(newPin)) {
        setMsg("PIN must be exactly 4 digits.", "error");
        return;
    }
    if (newPin !== confirm) {
        setMsg("PINs do not match.", "error");
        return;
    }
    try {
        const res = await window._ppFetch("/api/parent/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: "pin", value: newPin }),
        });
        // Update the in-memory verified PIN so subsequent calls keep working
        if (res.ok) window._ppSetPin(newPin);   // keep closure PIN in sync
        setMsg(res.ok ? "PIN changed successfully!" : "Failed to save.", res.ok ? "success" : "error");
        if (res.ok) {
            ["pp-new-pin", "pp-confirm-pin"].forEach(id => {
                const i = document.getElementById(id);
                if (i) i.value = "";
            });
        }
    } catch (_) {
        setMsg("Network error.", "error");
    }
}
