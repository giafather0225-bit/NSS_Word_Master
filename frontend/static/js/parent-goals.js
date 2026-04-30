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
            <div class="pp-goals-grid">${cards}</div>
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

/** Show inline edit form for goal targets — including active toggle. @tag PARENT GOALS */
async function _ppGoalsEditMode() {
    try {
        const data  = await apiFetchJSON("/api/goals/weekly");
        const goals = data.goals || [];

        const editArea = document.getElementById("pp-goals-edit-area");
        if (!editArea) return;

        const rows = goals.map(g => `
            <div class="pp-goal-edit-row" data-row-key="${g.key}">
                <label class="pp-toggle-row" style="flex:1;cursor:pointer">
                    <input type="checkbox" data-goal-active="${g.key}" ${g.is_active ? "checked" : ""}>
                    <span>${escapeHtml(g.label)}</span>
                </label>
                <input class="pp-xp-input" type="number" min="0" max="10000"
                       data-goal-key="${g.key}" value="${g.target}"
                       style="width:100px;text-align:right">
            </div>`).join("");

        editArea.innerHTML = `
            <div class="pp-goal-edit-box">
                <div class="pp-section-title" style="margin-top:16px">Edit Weekly Targets</div>
                <p class="pp-form-hint" style="margin:0 0 8px">Uncheck a row to deactivate the goal — it stays in the DB but stops counting toward the weekly summary.</p>
                ${rows}
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

/** Save all goal target edits — highlight failed rows, report counts. @tag PARENT GOALS */
async function _ppGoalsSave() {
    const msg = document.getElementById("pp-goals-msg");
    const inputs = document.querySelectorAll("[data-goal-key]");
    if (!inputs.length) return;

    // Reset prior row states
    document.querySelectorAll(".pp-goal-edit-row").forEach(r => r.classList.remove("error", "saved"));

    let saved = 0, failed = 0, skipped = 0;
    for (const inp of inputs) {
        const key    = inp.dataset.goalKey;
        const target = parseInt(inp.value, 10);
        const row    = document.querySelector(`[data-row-key="${key}"]`);
        const active = !!document.querySelector(`[data-goal-active="${key}"]`)?.checked;

        if (isNaN(target) || target < 0 || target > 10000) {
            row?.classList.add("error");
            skipped++;
            continue;
        }
        const res = await window._ppFetch(`/api/goals/weekly/${key}`, {
            method:  "PUT",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ target, is_active: active }),
        });
        if (res.ok) { saved++;  row?.classList.add("saved"); }
        else        { failed++; row?.classList.add("error"); }
    }

    if (msg) {
        const parts = [];
        if (saved)   parts.push(`${saved} saved`);
        if (failed)  parts.push(`${failed} failed`);
        if (skipped) parts.push(`${skipped} skipped (out of range 0–10000)`);
        msg.textContent = parts.join(" · ") || "No changes.";
        msg.className   = `pp-form-msg ${failed || skipped ? "error" : "success"}`;
    }

    // Reload only when everything went through cleanly
    if (saved && !failed && !skipped) setTimeout(() => _ppLoadTab("goals"), 800);
}

window._ppGoals = _ppGoals;
