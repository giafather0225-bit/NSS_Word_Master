/* ================================================================
   parent-overview.js — Parent Dashboard Overview tab renderer
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/summary, /api/parent/activity,
                  /api/parent/stage-stats, /api/parent/math-summary
   ================================================================ */

/** Render enhanced overview: summary cards + activity chart + stage stats + math snapshot. @tag PARENT */
async function _ppOverview(body) {
    try {
        const [sum, act, stg, math] = await Promise.all([
            apiFetchJSON("/api/parent/summary"),
            apiFetchJSON("/api/parent/activity?days=7"),
            apiFetchJSON("/api/parent/stage-stats"),
            apiFetchJSON("/api/parent/math-summary").catch(() => null),
        ]);

        body.innerHTML =
            _ppOverviewCards(sum) +
            _ppOverviewChart(act.daily || []) +
            _ppOverviewStages(stg.stages || {}) +
            _ppOverviewMathSnap(math);
    } catch (err) {
        console.error("[parent-overview] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`;
    }
}

/** Top 2×2 summary cards. @tag PARENT */
function _ppOverviewCards(sum) {
    return `
        <div class="pp-stats">
            <div class="pp-stat"><div class="pp-stat-num">${sum.total_xp||0} XP</div><div class="pp-stat-label">Total · Lv.${sum.current_level||1}</div></div>
            <div class="pp-stat"><div class="pp-stat-num">${sum.current_streak||0}d</div><div class="pp-stat-label">Streak (best ${sum.longest_streak||0}d)</div></div>
            <div class="pp-stat"><div class="pp-stat-num">${sum.total_words_learned||0}</div><div class="pp-stat-label">Words Learned</div></div>
            <div class="pp-stat"><div class="pp-stat-num">${sum.total_study_minutes||0}m</div><div class="pp-stat-label">${sum.total_study_sessions||0} sessions</div></div>
        </div>`;
}

/** 7-day XP activity bar chart. @tag PARENT */
function _ppOverviewChart(daily) {
    if (!daily.length) return "";
    const maxXP = Math.max(1, ...daily.map(d => d.xp));
    const bars = daily.map(d => {
        const pct = Math.round((d.xp / maxXP) * 100);
        return `<div class="pp-bar-col">
            <div class="pp-bar-value">${d.xp}</div>
            <div class="pp-bar-track"><div class="pp-bar-fill" style="height:${pct}%"></div></div>
            <div class="pp-bar-label">${(d.date || "").slice(5)}</div>
        </div>`;
    }).join("");
    return `
        <div class="pp-section-title">7-Day XP Activity</div>
        <div class="pp-bar-chart">${bars}</div>`;
}

/** Stage performance grid. @tag PARENT */
function _ppOverviewStages(stages) {
    const STAGE_NAMES = {preview:"Preview", word_match:"Word Match", fill_blank:"Fill Blank", spelling:"Spelling", sentence:"Sentence", final_test:"Final Test"};
    const cards = Object.entries(stages).map(([key, s]) => {
        const name = STAGE_NAMES[key] || key;
        return `<div class="pp-stage-card">
            <div class="pp-stage-name">${name}</div>
            <div class="pp-stage-row"><span>Avg Accuracy</span><strong>${s.avg_accuracy}%</strong></div>
            <div class="pp-stage-row"><span>Avg Time</span><strong>${Math.round(s.avg_time_sec/60)}m</strong></div>
            <div class="pp-stage-row"><span>Completed</span><strong>${s.completions}x</strong></div>
        </div>`;
    }).join("");
    return cards ? `<div class="pp-section-title">Stage Performance</div><div class="pp-stage-grid">${cards}</div>` : "";
}

/** Math snapshot strip with "Details ›" button to Math tab. @tag PARENT MATH */
function _ppOverviewMathSnap(math) {
    if (!math) return "";
    const a = math.academy || {};
    const r = math.recent_7d || {};
    const w = math.wrong_review || {};
    const doneLabel = `${a.completed || 0}/${a.total_lessons || 0}`;
    return `
        <div class="pp-section-title" style="display:flex;justify-content:space-between;align-items:center">
            <span>Math Snapshot</span>
            <button class="pp-btn secondary" style="padding:4px 12px;font-size:12px" onclick="_ppLoadTab('math')">Details ›</button>
        </div>
        <div class="pp-stats" style="grid-template-columns:repeat(3,1fr)">
            <div class="pp-stat pp-math-stat"><div class="pp-stat-num">${doneLabel}</div><div class="pp-stat-label">Lessons Done</div></div>
            <div class="pp-stat pp-math-stat"><div class="pp-stat-num">${r.accuracy_pct || 0}%</div><div class="pp-stat-label">7d Accuracy</div></div>
            <div class="pp-stat pp-math-stat"><div class="pp-stat-num">${w.pending || 0}</div><div class="pp-stat-label">Review Due</div></div>
        </div>`;
}

window._ppOverview = _ppOverview;
