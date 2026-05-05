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
            ${_ppMathSpacedReview(data.spaced_review || {})}
            ${_ppMathExitQuizHistory(data.exit_quiz_history || [])}
            ${_ppMathUnitTestHistory(data.unit_test_history || [])}
            ${_ppMathDailyChart(data.daily_recent || [])}
            ${_ppMathKangaroo(data.kangaroo || [])}`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-math] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load math summary.</p>`;
    }
}

/** Top 5-stat grid: completed lessons, exit quiz rate, 7-day accuracy, unit tests passed, spaced review due. @tag PARENT MATH */
function _ppMathCards(data) {
    const a = data.academy || {};
    const r = data.recent_7d || {};
    const sr = data.spaced_review || {};
    const completion = a.total_lessons
        ? Math.round((a.completed / a.total_lessons) * 100)
        : 0;
    const srDue = sr.due_today || 0;
    const srDueStyle = srDue > 0 ? "color:var(--color-error)" : "";
    const eqRate = a.eq_pass_rate || 0;
    const eqStyle = eqRate >= 80 ? "color:var(--math-ink)" : eqRate > 0 ? "color:var(--color-warning)" : "";
    return `
        ${_ppMathTitle("calculator", "Math Overview", "margin-top:0")}
        <div class="pp-stats pp-math-stats">
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${a.completed || 0}/${a.total_lessons || 0}</div>
                <div class="pp-stat-label">Lessons (${completion}%)</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num" style="${eqStyle}">${eqRate}%</div>
                <div class="pp-stat-label">Exit Quiz Rate · ${a.exit_quiz_passed || 0} passed</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${r.accuracy_pct || 0}%</div>
                <div class="pp-stat-label">7d Accuracy · ${r.total_attempts || 0} tries</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${a.unit_tests_passed || 0}</div>
                <div class="pp-stat-label">Unit Tests Passed</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num" style="${srDueStyle}">${srDue}</div>
                <div class="pp-stat-label">Spaced Review Due</div>
            </div>
        </div>`;
}

/** Weak concept list (top 5 by wrong count). @tag PARENT MATH */
function _ppMathWeakAreas(weak) {
    if (!weak.length) {
        return _ppMathTitle("alert-triangle", "Weak Concepts")
            + _ppEmpty("check-circle", "No weak areas yet.", "Keep practicing to surface lessons that need review.");
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
        return _ppMathTitle("zap", "Fact Fluency")
            + _ppEmpty("zap-off", "No fluency rounds yet.", "Run a Math Fact Fluency round to populate this section.");
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

/** Spaced review stats strip. @tag PARENT MATH */
function _ppMathSpacedReview(sr) {
    if (!sr || !sr.total) return "";
    const dueClass = sr.due_today > 0 ? "color:var(--color-error)" : "color:var(--color-success)";
    return `
        ${_ppMathTitle("repeat", "Spaced Review", "margin-top:24px")}
        <div class="pp-stats pp-math-stats">
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num" style="${dueClass}">${sr.due_today}</div>
                <div class="pp-stat-label">Due Today</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${sr.overdue}</div>
                <div class="pp-stat-label">Overdue</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${sr.upcoming_7d}</div>
                <div class="pp-stat-label">Next 7 Days</div>
            </div>
            <div class="pp-stat pp-math-stat">
                <div class="pp-stat-num">${sr.avg_score_pct}%</div>
                <div class="pp-stat-label">Avg Exit Score · ${sr.total} scheduled</div>
            </div>
        </div>`;
}

/** Exit quiz history table (last 10 passed lessons). @tag PARENT MATH */
function _ppMathExitQuizHistory(history) {
    if (!history.length) return "";
    const rows = history.map(r => {
        const score = r.score != null ? r.score : "—";
        const pct = r.score != null ? Math.round((r.score / 5) * 100) : 0;
        const accClass = pct >= 90 ? "good" : pct >= 80 ? "ok" : "low";
        const attempts = r.attempts || 1;
        const attLabel = attempts === 1
            ? `<span style="color:var(--text-hint);font-size:11px">1st try</span>`
            : `<span style="color:var(--color-warning);font-size:11px;font-weight:600">${attempts} tries</span>`;
        return `
            <tr>
                <td style="color:var(--text-hint);font-size:12px">${escapeHtml(r.grade || "")}</td>
                <td><strong>${escapeHtml(_ppMathLesson(r.lesson || ""))}</strong></td>
                <td style="text-align:right">${score}/5</td>
                <td style="text-align:right"><span class="pp-stage-acc pp-stage-acc--${accClass}">${pct}%</span></td>
                <td style="text-align:center">${attLabel}</td>
                <td style="color:var(--text-secondary)">${escapeHtml(r.completed_at || "")}</td>
            </tr>`;
    }).join("");
    return `
        ${_ppMathTitle("check-circle", "Exit Quiz History", "margin-top:24px")}
        <div class="pp-table-wrap">
            <table class="pp-log-table">
                <thead><tr>
                    <th>Grade</th>
                    <th>Lesson</th>
                    <th style="text-align:right">Score</th>
                    <th style="text-align:right">Acc</th>
                    <th style="text-align:center">Attempts</th>
                    <th>Date</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

/** Unit test history table (last 10). @tag PARENT MATH */
function _ppMathUnitTestHistory(history) {
    if (!history.length) return "";
    const rows = history.map(r => {
        const accClass = r.pct >= 90 ? "good" : r.pct >= 80 ? "ok" : "low";
        const passed = r.passed
            ? `<span style="color:var(--color-success);font-weight:700">Pass</span>`
            : `<span style="color:var(--color-error)">Fail</span>`;
        const attempt = r.attempt_number === 1
            ? `<span style="color:var(--text-hint);font-size:11px">1st</span>`
            : `<span style="color:var(--color-warning);font-size:11px;font-weight:600">Retry</span>`;
        return `
            <tr>
                <td><strong>${escapeHtml(r.unit_id || "")}</strong></td>
                <td style="text-align:center">${attempt}</td>
                <td style="text-align:right">${r.score}/${r.total}</td>
                <td style="text-align:right"><span class="pp-stage-acc pp-stage-acc--${accClass}">${r.pct}%</span></td>
                <td style="text-align:center">${passed}</td>
                <td style="color:var(--text-secondary)">${escapeHtml(r.taken_at || "")}</td>
            </tr>`;
    }).join("");
    return `
        ${_ppMathTitle("clipboard-list", "Unit Test History", "margin-top:24px")}
        <div class="pp-table-wrap">
            <table class="pp-log-table">
                <thead><tr>
                    <th>Unit</th>
                    <th style="text-align:center">Attempt</th>
                    <th style="text-align:right">Score</th>
                    <th style="text-align:right">Acc</th>
                    <th style="text-align:center">Result</th>
                    <th>Date</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

// Expose for parent-panel.js
window._ppMathSummary = _ppMathSummary;
