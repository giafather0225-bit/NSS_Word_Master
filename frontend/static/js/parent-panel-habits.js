/* ================================================================
   parent-panel-habits.js — Habits tab: Streak + Goals + Day-Off
   Section: Parent
   Dependencies: core.js, parent-panel.js, parent-streak.js, parent-goals.js
   API endpoints: GET /api/parent/streak, GET /api/goals/weekly,
                  GET /api/parent/day-off-requests,
                  PUT /api/parent/day-off-requests/{id}
   ================================================================ */

/** Render the full Habits tab: streak, goals, day-off approvals. @tag PARENT STREAK GOALS DAY_OFF */
async function _ppHabits(body) {
    body.innerHTML = `<p class="pp-loading-center">Loading…</p>`;
    try {
        const [streakData, goalsData, dayOffData] = await Promise.all([
            apiFetchJSON("/api/parent/streak"),
            apiFetchJSON("/api/goals/weekly"),
            apiFetchJSON("/api/parent/day-off-requests"),
        ]);

        body.innerHTML =
            _ppHabitsStreakSection(streakData) +
            _ppHabitsGoalsSection(goalsData) +
            _ppHabitsDayOffSection(dayOffData);

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-habits] load failed:", err);
        body.innerHTML = `<p style="color:var(--bad);padding:20px">Failed to load Habits.</p>`;
    }
}
window._ppHabits = _ppHabits;

// ─── Streak Section ───────────────────────────────────────────

function _ppHabitsStreakSection(data) {
    window._ppStreakData = data;
    return `
        <div class="pp-section-title">Streak</div>
        ${_ppStreakCards(data)}
        ${_ppStreakRule(data.rule)}
        ${_ppStreakCalendar(data.last_30d || [])}
        ${_ppStreakMilestones(data)}`;
}

// ─── Goals Section ────────────────────────────────────────────

function _ppHabitsGoalsSection(data) {
    const goals = (data.goals || []).filter(g => g.is_active);
    const achieved = goals.filter(g => g.achieved).length;

    const banner = goals.length
        ? `<div class="pp-goals-summary">${achieved} / ${goals.length} goals achieved this week</div>`
        : "";

    const cards = goals.length
        ? `<div class="pp-goals-grid">${goals.map(g => _ppGoalCard(g)).join("")}</div>`
        : _ppEmpty("target", "No active goals set.", "Click Edit Targets to configure weekly goals.");

    return `
        <div class="pp-section-title" style="margin-top:24px">Weekly Goals</div>
        ${banner}
        ${cards}
        <button class="pp-btn secondary pp-btn--mt8" onclick="_ppGoalsEditMode()">Edit Targets</button>
        <div id="pp-goals-edit-area"></div>`;
}

// ─── Day-Off Approvals Section ────────────────────────────────

function _ppHabitsDayOffSection(data) {
    const requests = data.requests || [];
    const pending  = requests.filter(r => r.status === "pending");
    const past     = requests.filter(r => r.status !== "pending").slice(0, 5);

    const pendingRows = pending.length
        ? pending.map(r => _ppDayOffRow(r, true)).join("")
        : `<p class="pp-form-hint" style="margin:0">No pending requests.</p>`;

    const pastRows = past.length
        ? `<div style="margin-top:12px">
            <div style="font-size:11px;font-weight:700;color:var(--ink-3);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px">Recent</div>
            ${past.map(r => _ppDayOffRow(r, false)).join("")}
           </div>`
        : "";

    return `
        <div class="pp-section-title" style="margin-top:24px">Day-Off Requests</div>
        <div class="pp-panel" style="padding:16px">
            ${pendingRows}${pastRows}
        </div>`;
}

/** Single day-off request row. @tag PARENT DAY_OFF */
function _ppDayOffRow(r, showActions) {
    const status = r.status || "pending";
    const statusColor = status === "approved" ? "var(--ok)" : status === "denied" ? "var(--bad)" : "var(--warn)";
    const dateStr = (r.date || "").slice(0, 10);
    const reason  = escapeHtml(r.reason || "—");

    const actions = showActions ? `
        <div style="display:flex;gap:6px;margin-top:8px">
            <button class="pp-btn primary" style="padding:5px 12px;font-size:12px"
                    onclick="_ppDecideDayOff(${r.id}, 'approved')">Approve</button>
            <button class="pp-btn secondary" style="padding:5px 12px;font-size:12px"
                    onclick="_ppDecideDayOff(${r.id}, 'denied')">Deny</button>
        </div>` : "";

    return `
        <div class="pp-dayoff-row" id="pp-dayoff-${r.id}">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
                <div>
                    <div style="font-size:13px;font-weight:700;color:var(--ink-1)">${dateStr}</div>
                    <div style="font-size:12px;color:var(--ink-3);margin-top:2px">${reason}</div>
                </div>
                <span style="font-size:11px;font-weight:700;color:${statusColor};text-transform:uppercase;letter-spacing:0.06em;flex-shrink:0">${status}</span>
            </div>
            ${actions}
        </div>`;
}
window._ppDayOffRow = _ppDayOffRow;

/** Approve or deny a day-off request. @tag PARENT DAY_OFF */
async function _ppDecideDayOff(id, decision) {
    const row = document.getElementById(`pp-dayoff-${id}`);
    try {
        const res = await window._ppFetch(`/api/parent/day-off-requests/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: decision }),
        });
        if (res.ok) {
            if (row) {
                const statusColor = decision === "approved" ? "var(--ok)" : "var(--bad)";
                const actionsEl = row.querySelector("[style*='gap:6px']");
                if (actionsEl) actionsEl.remove();
                const statusEl = row.querySelector("[style*='text-transform:uppercase']");
                if (statusEl) { statusEl.textContent = decision; statusEl.style.color = statusColor; }
            }
            _ppUpdateHabitsBadge();
        } else {
            window.toast && window.toast("Failed to update request.", "error");
        }
    } catch (err) {
        console.error("[parent-habits] decide day-off failed:", err);
        window.toast && window.toast("Network error.", "error");
    }
}
window._ppDecideDayOff = _ppDecideDayOff;
