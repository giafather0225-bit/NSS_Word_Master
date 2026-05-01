/* ================================================================
   parent-ckla.js — Parent Dashboard: CKLA progress tab
   Section: Parent
   Dependencies: parent-panel.js (_ppFetch, _ppEmpty)
   API endpoints: /api/parent/ckla-summary
   ================================================================ */

/** Render the CKLA parent summary tab. @tag PARENT CKLA */
async function _ppCKLA(body) {
    try {
        const d = await window._ppFetch("/api/parent/ckla-summary?grade=3");

        const pct = d.total_lessons
            ? Math.round(d.completed_lessons / d.total_lessons * 100)
            : 0;

        const estLine = d.estimated_completion_days != null
            ? `~${d.estimated_completion_days} days at current pace`
            : "Not enough data yet";

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
            return `
                <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-subtle)">
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
                </div>`;
        }).join('');

        // ── Weekly chart (last 14 days) ────────────────────────
        const chart = _ppCKLAChart(d.weekly_chart || []);

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
                <div class="pp-section-title" style="margin:24px 0 10px">
                    <i data-lucide="calendar-days" style="width:15px;height:15px"></i> Last 14 Days
                </div>
                ${chart}
                ${diffSection}
                ${reviewSection}
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (e) {
        console.error("_ppCKLA failed:", e);
        body.innerHTML = _ppEmpty("alert-triangle", "Could not load CKLA data", "Check the server logs.");
        if (typeof lucide !== "undefined") lucide.createIcons();
    }
}

/** Render a simple bar chart for the weekly lesson chart. @tag PARENT CKLA */
function _ppCKLAChart(days) {
    if (!days.length) return '<div style="color:var(--text-hint);font-size:.85rem">No data.</div>';
    const max = Math.max(...days.map(d => d.count), 1);
    const bars = days.map(d => {
        const h = Math.round((d.count / max) * 48);
        const label = d.date.slice(5); // MM-DD
        const isToday = d.date === new Date().toISOString().slice(0, 10);
        return `
            <div style="display:flex;flex-direction:column;align-items:center;gap:4px;flex:1">
                <span style="font-size:.68rem;color:var(--text-hint)">${d.count || ''}</span>
                <div style="width:100%;display:flex;align-items:flex-end;height:48px">
                    <div style="width:100%;height:${h || 2}px;background:${isToday ? 'var(--english-primary)' : 'var(--english-soft)'};border-radius:3px 3px 0 0"></div>
                </div>
                <span style="font-size:.65rem;color:${isToday ? 'var(--english-ink)' : 'var(--text-hint)'};font-weight:${isToday ? 700 : 400}">${label}</span>
            </div>`;
    }).join('');
    return `<div style="display:flex;gap:3px;align-items:flex-end;padding:8px 0">${bars}</div>`;
}

/** Difficulty chip helper. @tag PARENT CKLA */
function _ppDiffChip(label, count, bg, color) {
    return `<div style="background:${bg};color:${color};border-radius:var(--radius-full);padding:5px 14px;font-size:.8rem;font-weight:700">${label} <span style="opacity:.7">${count}</span></div>`;
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
