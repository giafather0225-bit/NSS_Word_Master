/* ================================================================
   parent-math.js — Parent Dashboard Math tab renderer
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/math-summary
   ================================================================ */

/** Humanize "L1_multiply_with_2_and_4" → "Multiply with 2 and 4". */
function _ppMathLesson(raw) {
    return (raw || "")
        .replace(/^L\d+_/, "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, c => c.toUpperCase())
        .trim();
}

/** Section title with a Lucide icon. */
function _ppMathTitle(icon, label, extraStyle = "") {
    return `<div class="pp-section-title pp-section-title--icon" style="${extraStyle}">
        <i data-lucide="${icon}" style="width:16px;height:16px"></i>${label}
    </div>`;
}

/** Render Math tab: academy progress, weak areas, fluency, daily challenge. @tag PARENT MATH */
async function _ppMathSummary(body) {
    try {
        const data = await apiFetchJSON("/api/parent/math-summary");

        body.innerHTML = `
            ${_ppMathCards(data)}
            <div class="pp-grid-2">
                <div>${_ppMathWeakAreas(data.weak_areas || [])}</div>
                <div>${_ppMathFluency(data.fluency || [])}</div>
            </div>
            ${_ppMathDailyChart(data.daily_recent || [])}
            ${_ppMathKangaroo(data.kangaroo || [])}`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-math] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load math summary.</p>`;
    }
}

/** Top 4-stat grid: completed lessons, 7-day accuracy, wrong-review pending, mastered. @tag PARENT MATH */
function _ppMathCards(data) {
    const a = data.academy || {};
    const r = data.recent_7d || {};
    const w = data.wrong_review || {};
    const completion = a.total_lessons
        ? Math.round((a.completed / a.total_lessons) * 100)
        : 0;
    return `
        ${_ppMathTitle("calculator", "Math Overview", "margin-top:0")}
        <div class="pp-stats pp-math-stats">
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${a.completed || 0}/${a.total_lessons || 0}</div>
                <div class="pp-stat-label">Lessons (${completion}%)</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${r.accuracy_pct || 0}%</div>
                <div class="pp-stat-label">7d Accuracy · ${r.total_attempts || 0} tries</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${w.pending || 0}</div>
                <div class="pp-stat-label">Wrong Review Due</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${w.mastered || 0}</div>
                <div class="pp-stat-label">Mastered</div>
            </div>
        </div>`;
}

/** Weak concept list (top 5 by wrong count). @tag PARENT MATH */
function _ppMathWeakAreas(weak) {
    if (!weak.length) {
        return `${_ppMathTitle("alert-triangle", "Weak Concepts")}
            <p style="color:var(--text-secondary);font-size:13px">No weak areas yet.</p>`;
    }
    const rows = weak.map(w => `
        <tr>
            <td><strong>${escapeHtml(_ppMathLesson(w.lesson))}</strong></td>
            <td style="color:var(--color-error);text-align:right">${w.wrong_count}×</td>
        </tr>`).join("");
    return `
        ${_ppMathTitle("alert-triangle", "Weak Concepts")}
        <div class="pp-table-wrap">
            <table class="pp-log-table">
                <thead><tr><th>Lesson</th><th style="text-align:right">Wrong</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

/** Fact fluency list: one card per fact set with phase + accuracy chip. @tag PARENT MATH */
function _ppMathFluency(fluency) {
    if (!fluency.length) {
        return `${_ppMathTitle("zap", "Fact Fluency")}
            <p style="color:var(--text-secondary);font-size:13px">No fluency rounds yet.</p>`;
    }
    const cards = fluency.map(f => {
        const acc = Math.round(f.accuracy_pct || 0);
        const phase = (f.phase || "A").toUpperCase();
        const accClass = acc >= 90 ? "good" : acc >= 70 ? "ok" : "low";
        return `
            <div class="pp-stage-card">
                <div class="pp-stage-head">
                    <span class="pp-stage-name">${escapeHtml(_ppMathLesson(f.fact_set))}</span>
                    <span class="pp-phase-pill">Phase ${phase}</span>
                    <span class="pp-stage-acc pp-stage-acc--${accClass}">${acc}%</span>
                </div>
                <div class="pp-stage-row"><span>Best</span><strong>${f.best_score || 0}</strong></div>
                <div class="pp-stage-row"><span>Rounds</span><strong>${f.total_rounds || 0}</strong></div>
            </div>`;
    }).join("");
    return `
        ${_ppMathTitle("zap", "Fact Fluency")}
        <div class="pp-stage-list">${cards}</div>`;
}

/** Daily challenge bar chart (last 7 days, newest right). @tag PARENT MATH */
function _ppMathDailyChart(daily) {
    if (!daily.length) return "";
    const sorted = [...daily].sort((a, b) => (a.date || "").localeCompare(b.date || ""));
    const maxScore = Math.max(1, ...sorted.map(d => d.total || 0));
    const bars = sorted.map(d => {
        const score = d.score || 0;
        const total = d.total || 0;
        const pct = total ? Math.round((score / maxScore) * 100) : 0;
        const dayLabel = (d.date || "").slice(5);
        const done = d.completed ? "pp-bar-fill pp-math-bar-done" : "pp-bar-fill pp-math-bar-partial";
        return `<div class="pp-bar-col" style="min-width:32px">
            <div class="pp-bar-value">${score}/${total}</div>
            <div class="pp-bar-track"><div class="${done}" style="height:${pct}%"></div></div>
            <div class="pp-bar-label">${dayLabel}</div>
        </div>`;
    }).join("");
    return `
        ${_ppMathTitle("calendar-days", "Daily Challenge · 7 Days", "margin-top:24px")}
        <div class="pp-bar-chart pp-math-chart">${bars}</div>`;
}

/** Kangaroo sets completed list. @tag PARENT MATH */
function _ppMathKangaroo(kang) {
    if (!kang.length) return "";
    const rows = kang.map(k => {
        const acc = k.total ? Math.round((k.score / k.total) * 100) : 0;
        const accClass = acc >= 90 ? "good" : acc >= 70 ? "ok" : "low";
        return `
            <tr>
                <td><strong>${escapeHtml(k.set_id || "")}</strong></td>
                <td style="text-align:right">${k.score}/${k.total}</td>
                <td style="text-align:right"><span class="pp-stage-acc pp-stage-acc--${accClass}">${acc}%</span></td>
                <td style="color:var(--text-secondary)">${escapeHtml(k.completed_at || "")}</td>
            </tr>`;
    }).join("");
    return `
        ${_ppMathTitle("award", "Kangaroo Sets", "margin-top:24px")}
        <div class="pp-table-wrap">
            <table class="pp-log-table">
                <thead><tr>
                    <th>Set</th>
                    <th style="text-align:right">Score</th>
                    <th style="text-align:right">Acc</th>
                    <th>Date</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

// Expose for parent-panel.js
window._ppMathSummary = _ppMathSummary;
