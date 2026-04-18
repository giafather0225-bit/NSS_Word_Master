/* ================================================================
   parent-math.js — Parent Dashboard Math tab renderer
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/math-summary
   ================================================================ */

/** Render Math tab: academy progress, weak areas, fluency, daily challenge. @tag PARENT MATH */
async function _ppMathSummary(body) {
    try {
        const res = await fetch("/api/parent/math-summary");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        body.innerHTML =
            _ppMathHeader(data) +
            _ppMathCards(data) +
            _ppMathStreakCond(data.streak_condition || "both") +
            _ppMathWeakAreas(data.weak_areas || []) +
            _ppMathFluency(data.fluency || []) +
            _ppMathDailyChart(data.daily_recent || []) +
            _ppMathKangaroo(data.kangaroo || []);
    } catch (err) {
        console.error("[parent-math] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load math summary.</p>`;
    }
}

/** Section heading. @tag PARENT MATH */
function _ppMathHeader(_data) {
    return `<div class="pp-section-title" style="margin-top:0">Math Overview</div>`;
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
    if (!weak.length) return "";
    const rows = weak.map(w => `
        <tr>
            <td><strong>${escapeHtml(w.lesson || "")}</strong></td>
            <td style="color:var(--color-error);text-align:right">${w.wrong_count}×</td>
        </tr>`).join("");
    return `
        <div class="pp-section-title">Weak Concepts</div>
        <table class="pp-log-table">
            <thead><tr><th>Lesson</th><th style="text-align:right">❌ Wrong</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
}

/** Fact fluency grid: one card per fact set. @tag PARENT MATH */
function _ppMathFluency(fluency) {
    if (!fluency.length) return "";
    const cards = fluency.map(f => {
        const acc = Math.round(f.accuracy_pct || 0);
        const phase = (f.phase || "A").toUpperCase();
        return `
            <div class="pp-stage-card pp-math-fluency-card">
                <div class="pp-stage-name">${escapeHtml(f.fact_set || "")}</div>
                <div class="pp-stage-row"><span>Phase</span><strong>${phase}</strong></div>
                <div class="pp-stage-row"><span>Accuracy</span><strong>${acc}%</strong></div>
                <div class="pp-stage-row"><span>Best</span><strong>${f.best_score || 0}</strong></div>
                <div class="pp-stage-row"><span>Rounds</span><strong>${f.total_rounds || 0}</strong></div>
            </div>`;
    }).join("");
    return `
        <div class="pp-section-title">Fact Fluency</div>
        <div class="pp-stage-grid">${cards}</div>`;
}

/** Daily challenge bar chart (last 7 days, newest right). @tag PARENT MATH */
function _ppMathDailyChart(daily) {
    if (!daily.length) return "";
    const sorted = [...daily].sort((a, b) => (a.date || "").localeCompare(b.date || ""));
    const maxScore = Math.max(1, ...sorted.map(d => d.total || 0));
    const bars = sorted.map(d => {
        const score = d.score || 0;
        const total = d.total || 0;
        const pct = Math.round((score / maxScore) * 100);
        const dayLabel = (d.date || "").slice(5);
        const done = d.completed ? "pp-bar-fill pp-math-bar-done" : "pp-bar-fill pp-math-bar-partial";
        return `<div class="pp-bar-col">
            <div class="pp-bar-value">${score}/${total}</div>
            <div class="pp-bar-track"><div class="${done}" style="height:${pct}%"></div></div>
            <div class="pp-bar-label">${dayLabel}</div>
        </div>`;
    }).join("");
    return `
        <div class="pp-section-title">Daily Challenge · 7 Days</div>
        <div class="pp-bar-chart pp-math-chart">${bars}</div>`;
}

/** Kangaroo sets completed list. @tag PARENT MATH */
function _ppMathKangaroo(kang) {
    if (!kang.length) return "";
    const rows = kang.map(k => {
        const acc = k.total ? Math.round((k.score / k.total) * 100) : 0;
        return `
            <tr>
                <td><strong>${escapeHtml(k.set_id || "")}</strong></td>
                <td>${k.score}/${k.total}</td>
                <td>${acc}%</td>
                <td style="color:var(--text-secondary)">${escapeHtml(k.completed_at || "")}</td>
            </tr>`;
    }).join("");
    return `
        <div class="pp-section-title">Kangaroo Sets</div>
        <table class="pp-log-table">
            <thead><tr><th>Set</th><th>Score</th><th>Acc</th><th>Date</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
}

/** Streak condition picker: both / either / english_only / math_only. @tag PARENT MATH STREAK */
function _ppMathStreakCond(current) {
    const OPTS = [
        ["both",         "Both subjects required"],
        ["either",       "Either subject counts"],
        ["english_only", "English only"],
        ["math_only",    "Math only"],
    ];
    const options = OPTS.map(([v, label]) =>
        `<option value="${v}"${v === current ? " selected" : ""}>${label}</option>`
    ).join("");
    return `
        <div class="pp-section-title">Streak Rule</div>
        <div class="pp-task-row" style="gap:10px">
            <span class="pp-task-key">Counts toward streak</span>
            <select id="pp-streak-cond" class="pp-input" style="max-width:220px;padding:6px 10px;font-size:13px"
                    onchange="_ppSaveStreakCond(this.value)">
                ${options}
            </select>
        </div>
        <p id="pp-streak-msg" style="font-size:12px;min-height:16px;color:var(--text-secondary);margin-top:6px"></p>`;
}

/** POST new streak_condition value via shared /api/parent/config. @tag PARENT MATH STREAK */
async function _ppSaveStreakCond(value) {
    const msg = document.getElementById("pp-streak-msg");
    try {
        const res = await window._ppFetch("/api/parent/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: "streak_condition", value }),
        });
        if (msg) {
            msg.textContent = res.ok ? "✓ Saved." : "Failed to save.";
            msg.style.color = res.ok ? "var(--color-success)" : "var(--color-error)";
        }
    } catch (err) {
        console.error("[parent-math] streak save failed:", err);
        if (msg) { msg.textContent = "Network error."; msg.style.color = "var(--color-error)"; }
    }
}

// Expose for parent-panel.js
window._ppMathSummary    = _ppMathSummary;
window._ppSaveStreakCond = _ppSaveStreakCond;
