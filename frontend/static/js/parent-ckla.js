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
            ? `<span style="color:var(--math-ink);font-weight:700">Studied today</span>`
            : `<span style="color:var(--review-ink);font-weight:700">No activity today</span>`;

        // ── Hero stats ─────────────────────────────────────────
        const hero = `
            <div class="pp-stats" style="grid-template-columns:repeat(4,1fr);margin-bottom:20px">
                <div class="pp-stat">
                    <div class="pp-stat-num">${d.completed_lessons}<span style="font-size:.65em;color:var(--text-hint)">/${d.total_lessons}</span></div>
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
            <div style="display:flex;gap:16px;align-items:center;margin-bottom:20px;font-size:.88rem">
                ${statusDot}
                <span style="color:var(--text-hint)">·</span>
                <span style="color:var(--text-secondary)">${estLine}</span>
            </div>`;

        // ── Overall progress bar ───────────────────────────────
        const progressBar = `
            <div style="margin-bottom:24px">
                <div style="display:flex;justify-content:space-between;font-size:.8rem;color:var(--text-secondary);margin-bottom:6px">
                    <span>Grade 3 Overall</span><span>${pct}%</span>
                </div>
                <div style="background:var(--bg-surface);border-radius:var(--radius-full);height:10px;overflow:hidden">
                    <div style="background:var(--english-primary);height:100%;width:${pct}%;border-radius:var(--radius-full);transition:width .4s"></div>
                </div>
            </div>`;

        // ── Domain breakdown ───────────────────────────────────
        const domainRows = (d.domains || []).map(dom => {
            const dpct = dom.lesson_count
                ? Math.round(dom.completed_count / dom.lesson_count * 100)
                : 0;
            const testBadge = dom.domain_test_passed
                ? `<span style="font-size:.7rem;background:var(--math-soft);color:var(--math-ink);border-radius:var(--radius-full);padding:2px 8px;font-weight:700">Test passed</span>`
                : (dom.all_complete
                    ? `<span style="font-size:.7rem;background:var(--arcade-soft);color:var(--arcade-ink);border-radius:var(--radius-full);padding:2px 8px;font-weight:700">Test ready</span>`
                    : '');
            const histHtml = _ppTestHistory(dom.domain_test_history || []);
            return `
                <div style="padding:10px 0;border-bottom:1px solid var(--border-subtle)">
                    <div style="display:flex;align-items:center;gap:12px">
                        <div style="width:26px;height:26px;border-radius:var(--radius-sm);background:var(--english-light);display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;color:var(--english-ink);flex-shrink:0">${dom.domain_num}</div>
                        <div style="flex:1;min-width:0">
                            <div style="font-size:.82rem;font-weight:600;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${_ppEsc(dom.title)}</div>
                            <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
                                <div style="flex:1;background:var(--bg-surface);border-radius:var(--radius-full);height:6px;overflow:hidden">
                                    <div style="background:var(--english-primary);height:100%;width:${dpct}%;border-radius:var(--radius-full)"></div>
                                </div>
                                <span style="font-size:.72rem;color:var(--text-hint);white-space:nowrap">${dom.completed_count}/${dom.lesson_count}</span>
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
            <div class="pp-section-title" style="margin:24px 0 10px">
                <i data-lucide="bar-chart-2" style="width:15px;height:15px"></i> Difficulty Ratings
            </div>
            <div style="display:flex;gap:10px;flex-wrap:wrap">
                ${_ppDiffChip('Easy',      diff.easy    || 0, 'var(--math-soft)',    'var(--math-ink)')}
                ${_ppDiffChip('Just right', diff.neutral || 0, 'var(--bg-surface)',  'var(--text-secondary)')}
                ${_ppDiffChip('Hard',       diff.hard    || 0, 'var(--review-soft)', 'var(--review-ink)')}
            </div>` : '';

        // ── Domain test 3-fail alerts ──────────────────────────
        const failAlerts = (d.domain_test_alerts || []).map(a => `
            <div style="background:var(--review-light);border-radius:var(--radius-md);padding:10px 14px;font-size:.82rem;display:flex;align-items:center;gap:10px">
                <i data-lucide="alert-triangle" style="width:14px;height:14px;color:var(--review-ink);flex-shrink:0"></i>
                <span style="color:var(--review-ink);font-weight:700">Domain ${a.domain_num}</span>
                <span style="color:var(--text-secondary)">${_ppEsc(a.title)}</span>
                <span style="margin-left:auto;font-size:.75rem;color:var(--review-ink)">${a.consec_fails} failed attempts</span>
            </div>`).join('');
        const alertSection = failAlerts ? `
            <div class="pp-section-title" style="margin:24px 0 10px;color:var(--review-ink)">
                <i data-lucide="alert-triangle" style="width:15px;height:15px"></i> Domain Test Alerts
            </div>
            <div style="display:flex;flex-direction:column;gap:6px">${failAlerts}</div>` : '';

        // ── Grade Final Test cooldown banner ──────────────────
        const finalTestBanner = d.final_test_locked ? `
            <div style="background:var(--arcade-soft);border-radius:var(--radius-md);padding:10px 14px;font-size:.82rem;display:flex;align-items:center;gap:10px;margin-bottom:8px">
                <i data-lucide="lock" style="width:14px;height:14px;color:var(--arcade-ink);flex-shrink:0"></i>
                <span style="color:var(--arcade-ink);font-weight:700">Grade Final Test locked</span>
                <span style="color:var(--text-secondary)">Retry after ${d.final_test_retry_after?.replace('T', ' ') || ''}</span>
            </div>` : '';

        // ── Learning start time pattern ────────────────────────
        const timePattern = (d.start_time_pattern || []);
        const timeSection = timePattern.length ? `
            <div class="pp-section-title" style="margin:24px 0 10px">
                <i data-lucide="clock" style="width:15px;height:15px"></i> Study Time Pattern
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
                ${timePattern.map(t => `
                    <div style="background:var(--english-light);border-radius:var(--radius-md);padding:8px 14px;text-align:center;min-width:72px">
                        <div style="font-size:.92rem;font-weight:700;color:var(--english-ink)">${_ppEsc(t.label)}</div>
                        <div style="font-size:.72rem;color:var(--text-hint);margin-top:2px">${t.count} sessions · ${t.pct}%</div>
                    </div>`).join('')}
            </div>` : '';

        // ── Needs review ───────────────────────────────────────
        const reviewSection = d.needs_review?.length ? `
            <div class="pp-section-title" style="margin:24px 0 10px;color:var(--review-ink)">
                <i data-lucide="alert-triangle" style="width:15px;height:15px"></i> Needs Review (${d.needs_review.length})
            </div>
            <div style="display:flex;flex-direction:column;gap:8px">
                ${d.needs_review.slice(0, 5).map(r => `
                    <div style="background:var(--review-light);border-radius:var(--radius-md);padding:10px 14px;font-size:.82rem">
                        <div style="color:var(--text-secondary);font-style:italic;margin-bottom:4px">"${_ppEsc(r.answer)}"</div>
                        <div style="color:var(--review-ink);font-size:.76rem">${_ppEsc(r.feedback)}</div>
                    </div>`).join('')}
            </div>` : '';

        body.innerHTML = `
            <div style="padding:20px 24px;max-width:720px">
                <div class="pp-section-title" style="margin-bottom:16px">
                    <i data-lucide="book-open" style="width:15px;height:15px"></i> CKLA Grade 3
                </div>
                ${hero}
                ${progressBar}
                <div class="pp-section-title" style="margin-bottom:10px">
                    <i data-lucide="layers" style="width:15px;height:15px"></i> Domains
                </div>
                <div>${domainRows || '<div style="color:var(--text-hint);font-size:.85rem">No domain data yet.</div>'}</div>
                <div class="pp-section-title" style="margin:24px 0 6px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
                    <span style="display:flex;align-items:center;gap:6px">
                        <i data-lucide="calendar-days" style="width:15px;height:15px"></i> Activity Chart
                    </span>
                    <span id="pp-ckla-chart-toggle" style="display:flex;gap:4px">
                        ${['week','month','full'].map(r => `
                            <button onclick="_ppCKLASetRange('${r}')"
                                    id="pp-ckla-range-${r}"
                                    style="font-size:.75rem;padding:3px 10px;border-radius:var(--radius-full);border:1px solid var(--border-default);cursor:pointer;background:${r === 'week' ? 'var(--english-primary)' : 'var(--bg-card)'};color:${r === 'week' ? 'var(--text-on-primary)' : 'var(--text-secondary)'};font-weight:600;transition:background .15s">
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
    return `<div id="pp-ckla-chart-wrap" style="min-height:72px;display:flex;align-items:center;justify-content:center">
        <span style="font-size:.8rem;color:var(--text-hint)">Loading chart…</span>
    </div>`;
}

/** Fetch chart data and re-render for the given range. @tag PARENT CKLA */
async function _ppCKLALoadChart(range) {
    _ppCKLAChartRange = range;
    const wrap = document.getElementById("pp-ckla-chart-wrap");
    if (!wrap) return;
    wrap.innerHTML = `<span style="font-size:.8rem;color:var(--text-hint)">Loading…</span>`;

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
        wrap.innerHTML = `<span style="font-size:.8rem;color:var(--review-ink)">Could not load chart.</span>`;
    }
}

/** Called by range toggle buttons. @tag PARENT CKLA */
function _ppCKLASetRange(range) {
    if (range !== _ppCKLAChartRange) _ppCKLALoadChart(range);
}

/** Render a simple bar chart for the lesson activity chart. @tag PARENT CKLA */
function _ppCKLAChart(days, groupedBy) {
    if (!days.length) return '<div style="color:var(--text-hint);font-size:.85rem;padding:12px 0">No data yet.</div>';
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
        <div style="font-size:.7rem;color:var(--text-hint);margin-top:2px">${typeLabel}</div>`;
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
        return `<div title="${_ppEsc(title)}" style="width:10px;height:10px;border-radius:50%;background:${color};flex-shrink:0"></div>`;
    }).join('');
    const last = history[0];
    return `
        <div style="display:flex;align-items:center;gap:6px;margin-top:6px;padding-left:38px">
            <span style="font-size:.7rem;color:var(--text-hint);white-space:nowrap">Test history:</span>
            <div style="display:flex;gap:4px;align-items:center">${dots}</div>
            <span style="font-size:.7rem;color:var(--text-secondary);margin-left:2px">Latest: ${last.score_pct}% ${last.passed ? '(Pass)' : '(Fail)'}</span>
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
