/* ================================================================
   parent-goals.js — Parent Dashboard: Goals tab renderer
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: GET /api/goals/weekly, PUT /api/goals/weekly/{key}
   ================================================================ */

/** @tag PARENT GOALS */
async function _ppGoals(body) {
    try {
        const data  = await apiFetchJSON("/api/goals/weekly");
        const goals = (data.goals || []).filter(g => g.is_active);

        const achieved = goals.filter(g => g.achieved).length;
        const banner   = goals.length
            ? `<div class="pp-goals-summary">${achieved} / ${goals.length} goals achieved this week</div>`
            : "";

        const cards = goals.length
            ? goals.map(g => _ppGoalCard(g)).join("")
            : `<p style="text-align:center;color:var(--text-secondary);padding:24px">No active goals set yet.</p>`;

        body.innerHTML = `
            ${banner}
            <div class="pp-goals-list">${cards}</div>
            <button class="pp-btn secondary" style="margin-top:8px" onclick="_ppGoalsEditMode()">Edit Targets</button>
            <div id="pp-goals-edit-area"></div>`;
    } catch (err) {
        console.error("[parent-goals] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load goals.</p>`;
    }
}

/** Single goal progress card. @tag PARENT GOALS */
function _ppGoalCard(g) {
    const pct  = Math.min(100, g.pct || 0);
    const done = g.achieved;
    return `
        <div class="pp-goal-card${done ? " pp-goal-card--done" : ""}">
            <div class="pp-goal-header">
                <span class="pp-goal-label">${escapeHtml(g.label)}</span>
                <span class="pp-goal-val">${g.current} / ${g.target}</span>
            </div>
            <div class="pp-goal-track">
                <div class="pp-goal-fill${done ? " pp-goal-fill--done" : ""}" style="width:${pct}%"></div>
            </div>
            <div class="pp-goal-footer">
                ${done
                    ? `<span class="pp-goal-achieved">Goal achieved!</span>`
                    : `<span class="pp-goal-pct">${pct}% complete</span>`}
            </div>
        </div>`;
}

/** Show inline edit form for goal targets. @tag PARENT GOALS */
async function _ppGoalsEditMode() {
    try {
        const data  = await apiFetchJSON("/api/goals/weekly");
        const goals = data.goals || [];

        const editArea = document.getElementById("pp-goals-edit-area");
        if (!editArea) return;

        const inputs = goals.map(g => `
            <div class="pp-goal-edit-row">
                <label class="pp-form-label" style="flex:1">${escapeHtml(g.label)}</label>
                <input class="pp-xp-input" type="number" min="0" max="10000"
                       data-goal-key="${g.key}" value="${g.target}"
                       style="width:100px;text-align:right">
            </div>`).join("");

        editArea.innerHTML = `
            <div class="pp-goal-edit-box">
                <div class="pp-section-title" style="margin-top:16px">Edit Weekly Targets</div>
                ${inputs}
                <div style="display:flex;gap:8px;margin-top:12px">
                    <button class="pp-btn primary" onclick="_ppGoalsSave()">Save</button>
                    <button class="pp-btn secondary" onclick="document.getElementById('pp-goals-edit-area').innerHTML=''">Cancel</button>
                </div>
                <p class="pp-form-msg" id="pp-goals-msg"></p>
            </div>`;
    } catch (_) {
        window.toast && window.toast("Could not load goals for editing.", "error");
    }
}

/** Save all goal target edits. @tag PARENT GOALS */
async function _ppGoalsSave() {
    const msg = document.getElementById("pp-goals-msg");
    const inputs = document.querySelectorAll("[data-goal-key]");
    if (!inputs.length) return;

    let allOk = true;
    for (const inp of inputs) {
        const key    = inp.dataset.goalKey;
        const target = parseInt(inp.value, 10);
        if (isNaN(target) || target < 0 || target > 10000) continue;

        const res = await window._ppFetch(`/api/goals/weekly/${key}`, {
            method:  "PUT",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ target, is_active: true }),
        });
        if (!res.ok) { allOk = false; }
    }

    if (msg) {
        msg.textContent  = allOk ? "Saved!" : "Some updates failed.";
        msg.className    = `pp-form-msg ${allOk ? "success" : "error"}`;
    }

    if (allOk) setTimeout(() => _ppLoadTab("goals"), 800);
}

window._ppGoals = _ppGoals;
