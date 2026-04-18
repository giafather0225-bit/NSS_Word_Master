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
        const res  = await fetch("/api/parent/task-settings");
        const data = await res.json();
        const rows = (data.tasks || []).map(t => {
            const label = t.task_key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
            return `<div class="pp-task-row">
                <span class="pp-task-key">${label}</span>
                <span class="pp-task-xp">+${t.xp_value} XP</span>
                <label class="pp-toggle">
                    <input type="checkbox" ${t.is_active ? "checked" : ""}
                           onchange="_ppToggleTask('${t.task_key}', this.checked)">
                    <span class="pp-toggle-track"></span>
                </label>
                ${t.is_required
                    ? `<span style="font-size:11px;font-weight:700;color:var(--color-primary)">Required</span>`
                    : `<button class="pp-btn secondary" style="padding:5px 10px;font-size:12px"
                               onclick="_ppToggleRequired('${t.task_key}', ${!t.is_required})">Make Required</button>`}
            </div>`;
        }).join("");
        body.innerHTML = `
            <div class="pp-section-title">Today's Tasks</div>
            <div class="pp-task-list">${rows || "<p style='color:var(--text-secondary)'>No tasks configured.</p>"}</div>
            <p style="font-size:12px;color:var(--text-secondary);margin-top:12px">Toggle to show/hide tasks on the Home screen.</p>`;
    } catch (_) { body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`; }
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
        const res  = await fetch("/api/parent/academy-schedule");
        const data = await res.json();
        (data.days || []).forEach(d => activeDays.add(d.day_of_week));
    } catch (_) {}

    window._ppScheduleDays = new Set(activeDays);

    const pills = _DAY_NAMES.map((name, i) =>
        `<div class="pp-day-pill${activeDays.has(i) ? " selected" : ""}"
              onclick="_ppToggleDay(${i}, this)">${name}</div>`
    ).join("");

    body.innerHTML = `
        <div class="pp-section-title">Test / Academy Days</div>
        <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">Select days when academy tests are scheduled.</p>
        <div class="pp-week-picker">${pills}</div>
        <button class="pp-btn primary" onclick="_ppSaveSchedule()">Save Schedule</button>
        <p id="pp-sched-msg" style="font-size:13px;margin-top:8px"></p>`;
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
        if (msg) msg.textContent = res.ok ? "✓ Saved!" : "Failed to save.";
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
    body.innerHTML = `
        <div class="pp-section-title">Parent Email</div>
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
}

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
                msg.textContent = value ? "✓ Email saved." : "✓ Email cleared.";
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
        if (res.ok) window._ppVerifiedPin = newPin;
        setMsg(res.ok ? "✓ PIN changed successfully!" : "Failed to save.", res.ok ? "success" : "error");
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
