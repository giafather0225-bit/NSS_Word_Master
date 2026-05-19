/* ================================================================
   parent-panel-habits.js — Parent Dashboard: Habits tab (Variant C)
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/streak, /api/parent/day-off-requests,
                  /api/goals/weekly, PUT /api/parent/day-off-requests/{id}
   ================================================================ */

const _PP_HABIT_MILESTONES = [
    { d: 7,   label: "1 week" },
    { d: 14,  label: "2 weeks" },
    { d: 30,  label: "1 month" },
    { d: 60,  label: "2 months" },
    { d: 100, label: "100 days" },
];

/** Habits tab entry. @tag PARENT HABITS */
async function _ppHabits(body) {
    try {
        const _safe = (p, fb) => p.catch(() => fb);
        const [streak, dayoffs, goalsResp] = await Promise.all([
            _safe(apiFetchJSON("/api/parent/streak"),             {}),
            _safe(apiFetchJSON("/api/parent/day-off-requests"),   { requests: [] }),
            _safe(apiFetchJSON("/api/goals/weekly"),              { goals: [] }),
        ]);

        body.innerHTML = `
            <div class="pp-habits-grid">
                ${_ppHabitsStreakCard(streak)}
                ${_ppHabitsDayOffsCard(dayoffs.requests || [], goalsResp.goals || [])}
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-habits] load failed:", err);
        body.innerHTML = `<p class="pp-error-pad">Failed to load Habits.</p>`;
    }
}

/** Streak panel: big number + milestones + 30-day grid. @tag PARENT STREAK */
function _ppHabitsStreakCard(streak) {
    const current = streak.current || 0;
    const best = streak.longest || 0;
    const subjects = streak.rule?.subjects || [];
    const mode = streak.rule?.mode || "all";
    const ruleLabel = `${mode === "all" ? "All of" : "Any of"}: ${subjects.join(" · ") || "—"}`;
    const last30 = streak.last_30d || [];

    const msList = _PP_HABIT_MILESTONES.map(m => {
        const reached = current >= m.d;
        const dDays = m.d - current;
        return `
            <div class="pp-ms-row ${reached ? "is-reached" : ""}">
                <span class="pp-ms-dot ${reached ? "is-reached" : ""}">${reached ? "✓" : ""}</span>
                <span class="mono pp-ms-d">${m.d}d</span>
                <span class="pp-ms-label">${escapeHtml(m.label)}</span>
                ${!reached ? `<span class="mono pp-ms-eta">D-${dDays}</span>` : ""}
            </div>`;
    }).join("");

    const cells = last30.map(d => {
        const cls = d.day_off ? "is-dayoff" : d.maintained ? "is-on" : "is-off";
        return `<div class="pp-30cell ${cls}" title="${escapeHtml(d.date || "")}"></div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Streak
                    <span class="pp-panel-sub">${escapeHtml(ruleLabel)}</span>
                </div>
            </div>
            <div class="pp-streak-flex">
                <div>
                    <div class="pp-streak-big">
                        <span class="mono">${current}</span>
                        <span class="pp-streak-big-sub">days</span>
                    </div>
                    <div class="pp-streak-best">Best ${best}d</div>
                </div>
                <div class="pp-ms-list">${msList}</div>
            </div>
            <div class="pp-30grid-kick">Last 30 days</div>
            <div class="pp-30grid">${cells || `<p class="pp-text-hint">No data yet.</p>`}</div>
            <div class="pp-30legend">
                <span><span class="pp-30legend-dot is-on"></span>Maintained</span>
                <span><span class="pp-30legend-dot is-dayoff"></span>Day off</span>
                <span><span class="pp-30legend-dot is-off"></span>Missed</span>
            </div>
        </div>`;
}

/** Day-off list + Weekly goals progress combined panel. @tag PARENT DAY_OFF GOALS */
function _ppHabitsDayOffsCard(requests, goals) {
    const sorted = requests.slice().sort((a, b) => {
        if (a.status === "pending" && b.status !== "pending") return -1;
        if (b.status === "pending" && a.status !== "pending") return 1;
        return (b.request_date || "").localeCompare(a.request_date || "");
    });
    const pending = sorted.filter(r => r.status === "pending").length;

    const rows = sorted.slice(0, 6).map(r => `
        <div class="pp-dayoff-card ${r.status === "pending" ? "is-pending" : ""}">
            <div class="pp-dayoff-card-head">
                <span class="mono pp-dayoff-date">${escapeHtml(r.request_date || "")}</span>
                <span class="pp-dayoff-status pp-dayoff-status--${r.status}">${escapeHtml(r.status || "")}</span>
            </div>
            <div class="pp-dayoff-reason">"${escapeHtml(r.reason || "")}"</div>
            ${r.status === "pending" ? `
                <div class="pp-dayoff-btns">
                    <button class="pp-btn primary pp-btn--sm" onclick="_ppDecideDayOff(${r.id}, 'approved')">Approve</button>
                    <button class="pp-btn secondary pp-btn--sm" onclick="_ppDecideDayOff(${r.id}, 'denied')">Deny</button>
                </div>` : ""}
        </div>`).join("");

    const goalRows = (goals || []).filter(g => g.is_active).slice(0, 4).map(g => {
        const pct = Math.min(100, g.pct || 0);
        return `
            <div class="pp-goalbar-row">
                <span class="pp-goalbar-label">${escapeHtml(g.label || g.key)}</span>
                <span class="mono pp-goalbar-val"><b>${g.current || 0}</b> / ${g.target || 0}</span>
                <div class="pp-goalbar-track"><div class="pp-goalbar-fill" style="width:${pct}%"></div></div>
            </div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Day Off Requests</div>
                <span class="mono ${pending ? "pp-rail-count--bad" : "pp-rail-count"}">${pending} pending</span>
            </div>
            <div class="pp-dayoff-list">${rows || `<p class="pp-text-hint">No day-off requests yet.</p>`}</div>

            <div class="pp-divider"></div>
            <div class="pp-panel-title pp-panel-title--inline">
                <div class="pp-panel-title-left">Weekly Goals</div>
                <button class="pp-btn ghost pp-btn--sm" onclick="_ppGoalsEdit()">Edit</button>
            </div>
            <div class="pp-goalbar-list">${goalRows || `<p class="pp-text-hint">No active goals.</p>`}</div>
        </div>`;
}

/** Approve/Deny a day-off request and reload habits tab. @tag PARENT DAY_OFF */
async function _ppDecideDayOff(reqId, decision) {
    try {
        const res = await window._ppFetch(`/api/parent/day-off-requests/${reqId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: decision, parent_response: "" }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const body = document.getElementById("pp-body");
        if (body) await _ppHabits(body);
        if (typeof _ppUpdateHabitsBadge === "function") _ppUpdateHabitsBadge();
    } catch (err) {
        console.error("[decide day-off] failed:", err);
        alert("Failed to update request.");
    }
}

/** Placeholder — open settings tab where goals can be edited. @tag PARENT GOALS */
function _ppGoalsEdit() {
    if (typeof _ppLoadTab === "function") _ppLoadTab("settings");
}

window._ppHabits         = _ppHabits;
window._ppDecideDayOff   = _ppDecideDayOff;
window._ppGoalsEdit      = _ppGoalsEdit;
