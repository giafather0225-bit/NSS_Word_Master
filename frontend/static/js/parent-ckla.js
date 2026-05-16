/* ================================================================
   parent-ckla.js — Parent Dashboard: CKLA progress tab
   Section: Parent
   Dependencies: parent-panel.js (_ppFetch, _ppEmpty)
   API endpoints: /api/parent/ckla-summary, /api/parent/ckla-chart
   ================================================================ */

/** @type {string} Active chart range: week | month | full */
let _ppCKLAChartRange = "week";

/** Render the CKLA parent summary tab. @tag PARENT CKLA */
async function _ppCKLA(body) {
    _ppCKLAChartRange = "week";      // reset on tab open
    try {
        const d = await window._ppFetch("/api/parent/ckla-summary?grade=3").then(r => r.json());

        const pct = d.total_lessons
            ? Math.round(d.completed_lessons / d.total_lessons * 100)
            : 0;

        let estLine = "Not enough data yet";
        if (d.estimated_completion_days != null) {
            const estDate = new Date(Date.now() + d.estimated_completion_days * 86400000);
            const opts = { month: 'short', day: 'numeric', year: 'numeric' };
            estLine = `Est. completion: ${estDate.toLocaleDateString('en-US', opts)} (~${d.estimated_completion_days}d)`;
        }

        const statusDot = d.today_studied
            ? `<span class="pp-ckla-status--ok">Studied today</span>`
            : `<span class="pp-ckla-status--miss">No activity today</span>`;

        // ── Hero stats ─────────────────────────────────────────
        const hero = `
            <div class="pp-stats pp-ckla-stats pp-stats--mb20">
                <div class="pp-stat">
                    <div class="pp-stat-num">${d.completed_lessons}<span class="pp-stat-frac">/${d.total_lessons}</span></div>
                    <div class="pp-stat-label">Lessons Done</div>
                </div>
                <div class="pp-stat">
                    <div class="pp-stat-num">${pct}%</div>
                    <div class="pp-stat-label">G3 Progress</div>
                </div>
                <div class="pp-stat">
                    <div class="pp-stat-num">${d.qa_accuracy}%</div>
                    <div class="pp-stat-label">Q&amp;A Accuracy</div>
                </div>
                <div class="pp-stat">
                    <div class="pp-stat-num">${d.today_lessons}</div>
                    <div class="pp-stat-label">Today</div>
                </div>
            </div>
            <div class="pp-ckla-meta">
                ${statusDot}
                <span class="pp-ckla-meta-sep">·</span>
                <span class="pp-ckla-meta-est">${estLine}</span>
            </div>`;

        // ── Overall progress bar ───────────────────────────────
        const progressBar = `
            <div class="pp-ckla-progress-wrap">
                <div class="pp-ckla-progress-head">
                    <span>Grade 3 Overall</span><span>${pct}%</span>
                </div>
                <div class="pp-ckla-track">
                    <div class="pp-ckla-fill" style="width:${pct}%"></div>
                </div>
            </div>`;

        // ── Domain breakdown ───────────────────────────────────
        const domainRows = (d.domains || []).map(dom => {
            const dpct = dom.lesson_count
                ? Math.round(dom.completed_count / dom.lesson_count * 100)
                : 0;
            const testBadge = dom.domain_test_passed
                ? `<span class="pp-ckla-badge--pass">Test passed</span>`
                : (dom.all_complete
                    ? `<span class="pp-ckla-badge--ready">Test ready</span>`
                    : '');
            const histHtml = _ppTestHistory(dom.domain_test_history || []);
            return `
                <div class="pp-ckla-domain-row">
                    <div class="pp-ckla-domain-inner">
                        <div class="pp-ckla-domain-num">${dom.domain_num}</div>
                        <div class="pp-ckla-domain-info">
                            <div class="pp-ckla-domain-title">${_ppEsc(dom.title)}</div>
                            <div class="pp-ckla-domain-bar-row">
                                <div class="pp-ckla-domain-track">
                                    <div class="pp-ckla-domain-fill" style="width:${dpct}%"></div>
                                </div>
                                <span class="pp-ckla-domain-count">${dom.completed_count}/${dom.lesson_count}</span>
                            </div>
                        </div>
                        ${testBadge}
                    </div>
                    ${histHtml}
                </div>`;
        }).join('');

        // ── Activity chart (range toggle: week / month / full) ─
        const chart = _ppCKLAChartShell();

        // ── Difficulty breakdown ───────────────────────────────
        const diff = d.difficulty_breakdown || {};
        const diffTotal = (diff.easy || 0) + (diff.neutral || 0) + (diff.hard || 0);
        const diffSection = diffTotal > 0 ? `
            <div class="pp-section-title pp-section-title--icon pp-section-title--mt24-mb10">
                <i data-lucide="bar-chart-2" style="width:15px;height:15px"></i> Difficulty Ratings
            </div>
            <div class="pp-ckla-diff-list">
                ${_ppDiffChip('Easy',      diff.easy    || 0, 'var(--math-soft)',    'var(--math-ink)')}
                ${_ppDiffChip('Just right', diff.neutral || 0, 'var(--bg-surface)',  'var(--text-secondary)')}
                ${_ppDiffChip('Hard',       diff.hard    || 0, 'var(--review-soft)', 'var(--review-ink)')}
            </div>` : '';

        // ── Domain test 3-fail alerts ──────────────────────────
        const failAlerts = (d.domain_test_alerts || []).map(a => `
            <div class="pp-ckla-alert-row">
                <i data-lucide="alert-triangle" style="width:14px;height:14px;flex-shrink:0"></i>
                <span class="pp-ckla-alert-domain">Domain ${a.domain_num}</span>
                <span class="pp-ckla-alert-title">${_ppEsc(a.title)}</span>
                <span class="pp-ckla-alert-count">${a.consec_fails} failed attempts</span>
            </div>`).join('');
        const alertSection = failAlerts ? `
            <div class="pp-section-title pp-section-title--icon pp-section-title--mt24-mb10 pp-section-title--alert">
                <i data-lucide="alert-triangle" style="width:15px;height:15px"></i> Domain Test Alerts
            </div>
            <div class="pp-ckla-alert-list">${failAlerts}</div>` : '';

        // ── Grade Final Test cooldown banner ──────────────────
        const finalTestBanner = d.final_test_locked ? `
            <div class="pp-ckla-final-banner">
                <i data-lucide="lock" style="width:14px;height:14px;flex-shrink:0"></i>
                <span class="pp-ckla-final-banner-label">Grade Final Test locked</span>
                <span class="pp-ckla-final-banner-sub">Retry after ${d.final_test_retry_after?.replace('T', ' ') || ''}</span>
            </div>` : '';

        // ── Learning start time pattern ────────────────────────
        const timePattern = (d.start_time_pattern || []);
        const timeSection = timePattern.length ? `
            <div class="pp-section-title pp-section-title--icon pp-section-title--mt24-mb10">
                <i data-lucide="clock" style="width:15px;height:15px"></i> Study Time Pattern
            </div>
            <div class="pp-ckla-time-list">
                ${timePattern.map(t => `
                    <div class="pp-ckla-time-chip">
                        <div class="pp-ckla-time-label">${_ppEsc(t.label)}</div>
                        <div class="pp-ckla-time-sub">${t.count} sessions · ${t.pct}%</div>
                    </div>`).join('')}
            </div>` : '';

        // ── Needs review ───────────────────────────────────────
        const reviewSection = d.needs_review?.length ? `
            <div class="pp-section-title pp-section-title--icon pp-section-title--mt24-mb10 pp-section-title--alert">
                <i data-lucide="alert-triangle" style="width:15px;height:15px"></i> Needs Review (${d.needs_review.length})
            </div>
            <div class="pp-ckla-review-list">
                ${d.needs_review.slice(0, 5).map(r => `
                    <div class="pp-ckla-review-item">
                        <div class="pp-ckla-review-answer">"${_ppEsc(r.answer)}"</div>
                        <div class="pp-ckla-review-feedback">${_ppEsc(r.feedback)}</div>
                    </div>`).join('')}
            </div>` : '';

        body.innerHTML = `
            <div class="pp-ckla-outer">
                <div class="pp-section-title pp-section-title--icon pp-section-title--mb16">
                    <i data-lucide="book-open" style="width:15px;height:15px"></i> CKLA Grade 3
                </div>
                ${hero}
                ${progressBar}
                <div class="pp-grid-2 pp-grid-2--top">
                    <div>
                        <div class="pp-section-title pp-section-title--icon pp-section-title--mb10">
                            <i data-lucide="layers" style="width:15px;height:15px"></i> Domains
                        </div>
                        <div>${domainRows || '<div class="pp-ckla-domain-empty">No domain data yet.</div>'}</div>
                    </div>
                    <div>
                        <div class="pp-ckla-chart-head">
                            <span class="pp-ckla-chart-icon-wrap">
                                <i data-lucide="calendar-days" style="width:15px;height:15px"></i> Activity Chart
                            </span>
                            <span id="pp-ckla-chart-toggle" class="pp-ckla-range-toggle">
                                ${['week','month','full'].map(r => `
                                    <button onclick="_ppCKLASetRange('${r}')"
                                            id="pp-ckla-range-${r}"
                                            class="pp-ckla-range-btn"
                                            style="background:${r === 'week' ? 'var(--english-primary)' : 'var(--bg-card)'};color:${r === 'week' ? 'var(--text-on-primary)' : 'var(--text-secondary)'}">
                                        ${r === 'week' ? '7d' : r === 'month' ? '30d' : 'All'}
                                    </button>`).join('')}
                            </span>
                        </div>
                        ${chart}
                        ${diffSection}
                        ${timeSection}
                        ${alertSection}
                        ${finalTestBanner}
                        ${reviewSection}
                    </div>
                </div>
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
        // Load initial chart after DOM is ready
        _ppCKLALoadChart("week");
    } catch (e) {
        console.error("_ppCKLA failed:", e);
        body.innerHTML = _ppEmpty("alert-triangle", "Could not load CKLA data", "Check the server logs.");
        if (typeof lucide !== "undefined") lucide.createIcons();
    }
}

/** Return the placeholder container for the interactive chart. @tag PARENT CKLA */
function _ppCKLAChartShell() {
    return `<div id="pp-ckla-chart-wrap" class="pp-ckla-chart-wrap">
        <span class="pp-ckla-chart-hint">Loading chart…</span>
    </div>`;
}

/** Fetch chart data and re-render for the given range. @tag PARENT CKLA */
async function _ppCKLALoadChart(range) {
    _ppCKLAChartRange = range;
    const wrap = document.getElementById("pp-ckla-chart-wrap");
    if (!wrap) return;
    wrap.innerHTML = `<span class="pp-ckla-chart-hint">Loading…</span>`;

    // Update toggle button styles
    ["week", "month", "full"].forEach(r => {
        const btn = document.getElementById(`pp-ckla-range-${r}`);
        if (!btn) return;
        const active = r === range;
        btn.style.background = active ? "var(--english-primary)" : "var(--bg-card)";
        btn.style.color      = active ? "var(--text-on-primary)" : "var(--text-secondary)";
    });

    try {
        const res = await window._ppFetch(`/api/parent/ckla-chart?range=${range}&grade=3`);
        if (!res.ok) throw new Error(res.status);
        const data = await res.json();
        wrap.innerHTML = _ppCKLAChart(data.chart || [], data.grouped_by || "day");
    } catch (e) {
        wrap.innerHTML = `<span class="pp-ckla-chart-err">Could not load chart.</span>`;
    }
}

/** Called by range toggle buttons. @tag PARENT CKLA */
function _ppCKLASetRange(range) {
    if (range !== _ppCKLAChartRange) _ppCKLALoadChart(range);
}

/** Render a simple bar chart for the lesson activity chart. @tag PARENT CKLA */
function _ppCKLAChart(days, groupedBy) {
    if (!days.length) return '<div class="pp-ckla-chart-empty">No data yet.</div>';
    const max = Math.max(...days.map(d => d.count), 1);
    const todayStr = new Date().toISOString().slice(0, 10);
    // For many bars (month=30, full=many weeks), shrink bar gap
    const gap = days.length > 20 ? 2 : 3;
    const bars = days.map(d => {
        const h       = Math.round((d.count / max) * 56);
        const label   = d.label || d.date.slice(5);   // use pre-computed label if available
        const isToday = d.date === todayStr;
        const barColor = d.count > 0
            ? (isToday ? 'var(--english-primary)' : 'var(--english-soft)')
            : 'var(--bg-surface)';
        return `
            <div style="display:flex;flex-direction:column;align-items:center;gap:2px;flex:1;min-width:0">
                <span style="font-size:.62rem;color:var(--text-hint);height:14px;line-height:14px">${d.count > 0 ? d.count : ''}</span>
                <div style="width:100%;display:flex;align-items:flex-end;height:56px">
                    <div style="width:100%;height:${Math.max(h, d.count > 0 ? 4 : 1)}px;background:${barColor};border-radius:3px 3px 0 0"></div>
                </div>
                <span style="font-size:.6rem;color:${isToday ? 'var(--english-ink)' : 'var(--text-hint)'};font-weight:${isToday ? 700 : 400};white-space:nowrap;overflow:hidden;max-width:100%;text-overflow:ellipsis">${label}</span>
            </div>`;
    }).join('');
    const typeLabel = groupedBy === "week" ? "Weekly totals" : "Daily lessons";
    return `
        <div style="display:flex;gap:${gap}px;align-items:flex-end;padding:8px 0">${bars}</div>
        <div class="pp-ckla-chart-type">${typeLabel}</div>`;
}

/** Difficulty chip helper. @tag PARENT CKLA */
function _ppDiffChip(label, count, bg, color) {
    return `<div style="background:${bg};color:${color};border-radius:var(--radius-full);padding:5px 14px;font-size:.8rem;font-weight:700">${label} <span style="opacity:.7">${count}</span></div>`;
}

/** Render domain test attempt history dots. @tag PARENT CKLA */
function _ppTestHistory(history) {
    if (!history || history.length === 0) return '';
    const dots = history.slice(0, 10).map(h => {
        const color = h.passed ? 'var(--math-primary)' : 'var(--review-primary)';
        const title = `${h.date}: ${h.correct}/${h.total} (${h.score_pct}%) ${h.passed ? 'Pass' : 'Fail'}`;
        return `<div title="${_ppEsc(title)}" class="pp-ckla-hist-dot" style="background:${color}"></div>`;
    }).join('');
    const last = history[0];
    return `
        <div class="pp-ckla-hist-row">
            <span class="pp-ckla-hist-label">Test history:</span>
            <div class="pp-ckla-hist-dots">${dots}</div>
            <span class="pp-ckla-hist-latest">Latest: ${last.score_pct}% ${last.passed ? '(Pass)' : '(Fail)'}</span>
        </div>`;
}

/** HTML-escape helper (scoped to this module). @tag SYSTEM */
function _ppEsc(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
