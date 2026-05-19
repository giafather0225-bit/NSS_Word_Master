/* ================================================================
   parent-panel-home.js — Parent Dashboard: Home tab (Variant A)
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/summary, /api/parent/overview,
                  /api/parent/activity, /api/parent/day-off-requests,
                  /api/parent/weaknesses, /api/island/status,
                  /api/tasks/today, /api/xp/summary
   ================================================================ */

const _PP_DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** Helper: format date string (YYYY-MM-DD) to weekday short. @tag PARENT */
function _ppDayLabel(iso) {
    if (!iso) return "";
    const d = new Date(iso + "T00:00:00");
    return _PP_DAY_LABELS[d.getDay()] || "";
}

/** Helper: returns approximate per-subject share ratios from today's bySubject. @tag PARENT */
function _ppSubjectShares(bySubject) {
    const keys = ["english", "math", "diary", "review"];
    const map = {
        english: bySubject?.english?.xp || 0,
        math:    bySubject?.math?.xp    || 0,
        diary:   bySubject?.diary?.xp   || 0,
        review:  bySubject?.ckla?.xp    || 0, // CKLA logs as review in stacked chart
    };
    const total = keys.reduce((s, k) => s + map[k], 0);
    if (total === 0) return { english: 0.4, math: 0.35, diary: 0.15, review: 0.10 };
    return keys.reduce((acc, k) => (acc[k] = map[k] / total, acc), {});
}

/** Helper: build stacked series for one day from total minutes + share map. @tag PARENT */
function _ppMakeDailySeries(totalMin, shares) {
    return [
        { key: "english", v: totalMin * (shares.english || 0) },
        { key: "math",    v: totalMin * (shares.math    || 0) },
        { key: "diary",   v: totalMin * (shares.diary   || 0) },
        { key: "review",  v: totalMin * (shares.review  || 0) },
    ];
}

/** Home tab entry. @tag PARENT */
async function _ppHome(body) {
    try {
        const _safe = (p, fb) => p.catch(() => fb);

        const [sum, ov, act30, dayoffs, island, weak, tasks, xpSum] = await Promise.all([
            _safe(apiFetchJSON("/api/parent/summary"),               {}),
            _safe(apiFetchJSON("/api/parent/overview"),              {}),
            _safe(apiFetchJSON("/api/parent/activity?days=30"),      { daily: [] }),
            _safe(apiFetchJSON("/api/parent/day-off-requests"),      { requests: [] }),
            _safe(apiFetchJSON("/api/island/status"),                null),
            _safe(apiFetchJSON("/api/parent/weaknesses"),            { weaknesses: [] }),
            _safe(apiFetchJSON("/api/tasks/today"),                  []),
            _safe(apiFetchJSON("/api/xp/summary"),                   {}),
        ]);

        const range = window._ppGetRange ? window._ppGetRange() : "weekly";
        const daily = act30.daily || [];

        body.innerHTML = `
            ${_ppHomeHeadline(range, sum, ov, daily, xpSum)}
            <div class="pp-home-grid">
                <div class="pp-home-main">
                    ${_ppHomeKpiRow(range, sum, ov, daily, xpSum)}
                    ${_ppHomeTasksCard(tasks)}
                    ${_ppHomeChartCard(range, daily, ov)}
                    <div class="pp-2col pp-2col--top">
                        ${_ppHomeReadingCard()}
                        ${_ppHomeMathCard()}
                    </div>
                </div>
                <div class="pp-home-rail">
                    ${_ppHomeApprovalsCard(dayoffs.requests || [], island)}
                    ${_ppHomeStreakCard(sum, daily)}
                    ${_ppHomeIslandCard(island)}
                </div>
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-home] load failed:", err);
        body.innerHTML = `<p class="pp-error-pad">Failed to load Home.</p>`;
    }
}

/** Headline with range-aware copy + "Send a cheer" CTA. @tag PARENT */
function _ppHomeHeadline(range, sum, ov, daily, xpSum) {
    const streak = sum.current_streak || 0;
    const todayXP = ov.today_xp || xpSum.today_xp || 0;
    const todayRow = daily[daily.length - 1] || {};
    const todayMin = todayRow.minutes || 0;
    const todaySessions = todayRow.sessions || 0;

    const last7 = daily.slice(-7);
    const last30 = daily.slice(-30);
    const weekMin = last7.reduce((a, d) => a + (d.minutes || 0), 0);
    const weekSessions = last7.reduce((a, d) => a + (d.sessions || 0), 0);
    const monthMin = last30.reduce((a, d) => a + (d.minutes || 0), 0);
    const monthSessions = last30.reduce((a, d) => a + (d.sessions || 0), 0);

    let title, body;
    if (range === "daily") {
        title = "How is Gia doing today";
        body = `<b class="mono">${todayMin}m</b> learned · <b class="mono">${todaySessions}</b> session${todaySessions === 1 ? "" : "s"} · <b class="mono">${streak}</b>-day streak`;
    } else if (range === "monthly") {
        const now = new Date();
        const monthName = now.toLocaleDateString("en", { month: "long", year: "numeric" });
        title = monthName;
        body = `<b class="mono">${monthMin}m</b> this month · <b class="mono">${monthSessions}</b> sessions completed · ${_ppTrend(7)}`;
    } else {
        title = "This week at a glance";
        body = `<b class="mono">${weekMin}m</b> this week · <b class="mono">${weekSessions}</b> sessions · ${_ppTrend(14)}`;
    }

    return `
        <div class="pp-headline">
            <div class="pp-headline-text">
                <h1 class="pp-headline-h">${title}</h1>
                <p class="pp-headline-body">${body}</p>
            </div>
            <button class="pp-btn primary pp-headline-cta" onclick="_ppSendCheer()">
                <i data-lucide="message-square-text"></i>Send a cheer
            </button>
        </div>`;
}
window._ppSendCheer = function () {
    // Placeholder — could POST to /api/parent/cheer in future.
    if (window.toast) window.toast("Cheer sent to Gia!", "success");
};

/** 4-column KPI row, accent colors per metric. @tag PARENT */
function _ppHomeKpiRow(range, sum, ov, daily, xpSum) {
    const streak = sum.current_streak || 0;
    const best = sum.longest_streak || 0;
    const last7 = daily.slice(-7);
    const last30 = daily.slice(-30);

    let kpis;
    if (range === "daily") {
        const todayRow = daily[daily.length - 1] || {};
        const todayMin = todayRow.minutes || 0;
        const todayXP = ov.today_xp || xpSum.today_xp || 0;
        const todaySessions = todayRow.sessions || 0;
        kpis = [
            _ppKpi("Today's minutes", todayMin, { unit: "min", sub: "Goal 60m", accent: "var(--english-primary)", colorful: true }),
            _ppKpi("Sessions today",  todaySessions, { sub: "completed",        accent: "var(--math-primary)",   colorful: true }),
            _ppKpi("XP today",        todayXP, { unit: "XP", sub: `Total ${(xpSum.total_xp || 0).toLocaleString()}`, accent: "var(--legend-primary)", colorful: true }),
            _ppKpi("Streak",          streak, { unit: "days", sub: `Best ${best}d`, accent: "var(--diary-primary)", colorful: true }),
        ];
    } else if (range === "monthly") {
        const totalMin = last30.reduce((a, d) => a + (d.minutes || 0), 0);
        const totalSessions = last30.reduce((a, d) => a + (d.sessions || 0), 0);
        const totalXP = last30.reduce((a, d) => a + (d.xp || 0), 0);
        const avgPerWeek = Math.round(totalMin / 4) || 0;
        kpis = [
            _ppKpi("Month minutes", totalMin, { unit: "min", sub: `Avg ${avgPerWeek}m/week`, accent: "var(--english-primary)", colorful: true }),
            _ppKpi("Sessions",      totalSessions, { sub: "this month",                       accent: "var(--math-primary)",   colorful: true }),
            _ppKpi("XP this month", totalXP, { unit: "XP", sub: `Total ${(xpSum.total_xp || 0).toLocaleString()}`, accent: "var(--legend-primary)", colorful: true }),
            _ppKpi("Streak",        streak, { unit: "days", sub: `Best ${best}d`, accent: "var(--diary-primary)", colorful: true }),
        ];
    } else {
        const weekMin = last7.reduce((a, d) => a + (d.minutes || 0), 0);
        const weekSessions = last7.reduce((a, d) => a + (d.sessions || 0), 0);
        const weekXP = last7.reduce((a, d) => a + (d.xp || 0), 0);
        kpis = [
            _ppKpi("Week minutes", weekMin, { unit: "min", sub: "Goal 420m/week", accent: "var(--english-primary)", colorful: true }),
            _ppKpi("Sessions",     weekSessions, { sub: "this week",              accent: "var(--math-primary)",   colorful: true }),
            _ppKpi("XP this week", weekXP, { unit: "XP", sub: `Total ${(xpSum.total_xp || 0).toLocaleString()}`, accent: "var(--legend-primary)", colorful: true }),
            _ppKpi("Streak",       streak, { unit: "days", sub: `Best ${best}d`, accent: "var(--diary-primary)", colorful: true }),
        ];
    }

    return `<div class="pp-kpi-row">${kpis.join("")}</div>`;
}

/** Today's Tasks card with combined progress bar + 2-col task grid. @tag PARENT */
function _ppHomeTasksCard(tasks) {
    const list = Array.isArray(tasks) ? tasks : [];
    const total = list.length || 5;
    const done = list.filter(t => t.is_done).length;
    const xpEarned = list.filter(t => t.is_done).reduce((a, t) => a + (t.xp || 0), 0);
    const xpTotal = list.reduce((a, t) => a + (t.xp || 0), 0);

    const barSegs = list.length
        ? list.map(t => `<div class="pp-task-pill ${t.is_done ? "is-done" : "is-pending"}" title="${escapeHtml(t.label || "")}"></div>`).join("")
        : Array.from({ length: 5 }).map(() => `<div class="pp-task-pill is-empty"></div>`).join("");

    const taskRows = list.length
        ? list.map(t => `
            <div class="pp-task-card ${t.is_done ? "is-done" : ""}">
                <span class="pp-task-check ${t.is_done ? "is-done" : ""}">
                    ${t.is_done ? `<i data-lucide="check"></i>` : ""}
                </span>
                <span class="pp-task-label">${escapeHtml(t.label || "")}</span>
                <span class="pp-task-xp mono">+${t.xp || 0} XP</span>
            </div>`).join("")
        : `<div class="pp-empty" style="grid-column:1/-1"><p class="pp-empty-title">No tasks assigned today.</p></div>`;

    return `
        <div class="pp-card pp-tasks-card">
            <div class="pp-card-head pp-tasks-head">
                <div>
                    <div class="pp-kick-inline">Today's tasks · parent-assigned</div>
                    <div class="pp-tasks-summary">
                        <span class="mono pp-tasks-big">${done}<span class="pp-tasks-big-of">/${total}</span></span>
                        <span class="pp-tasks-sub">completed ·</span>
                        <span class="mono pp-tasks-xp">${xpEarned}/${xpTotal} XP</span>
                    </div>
                </div>
                <button class="pp-btn ghost pp-btn--sm" onclick="_ppLoadTab('settings')">
                    <i data-lucide="settings-2"></i>Edit tasks
                </button>
            </div>
            <div class="pp-task-bar">${barSegs}</div>
            <div class="pp-task-grid">${taskRows}</div>
        </div>`;
}

/** Range-aware bar chart card. @tag PARENT */
function _ppHomeChartCard(range, daily, ov) {
    let series, totalLabel, xLabel, goalLine, goalLabel, isDaily;
    if (range === "daily") {
        // Daily view: show last 7 sessions today — for now use last hour buckets (placeholder = today single bar)
        const today = (daily[daily.length - 1] || {});
        series = [{ label: "Now", v: today.minutes || 0, today: true, color: "var(--english-primary)" }];
        totalLabel = "today";
        xLabel = "Today's sessions";
        goalLine = 15;
        goalLabel = "avg/session";
        isDaily = true;
    } else if (range === "monthly") {
        const last4w = [];
        for (let w = 3; w >= 0; w--) {
            const slice = daily.slice(-7 * (w + 1), daily.length - 7 * w);
            const min = slice.reduce((a, d) => a + (d.minutes || 0), 0);
            last4w.push({ label: `W${4 - w}`, v: min, today: w === 0 });
        }
        series = last4w;
        totalLabel = "this month";
        xLabel = "Last 4 weeks";
        goalLine = 300;
        goalLabel = "goal 300m/week";
        isDaily = false;
    } else {
        const last7 = daily.slice(-7);
        series = last7.map((d, i) => ({
            label: _ppDayLabel(d.date) || `D${i + 1}`,
            v: d.minutes || 0,
            today: i === last7.length - 1,
        }));
        totalLabel = "this week";
        xLabel = "Last 7 days";
        goalLine = 60;
        goalLabel = "goal 60m/day";
        isDaily = false;
    }

    const shares = _ppSubjectShares(ov.today_by_subject || {});
    if (!isDaily) series = series.map(d => ({ ...d, series: _ppMakeDailySeries(d.v, shares) }));

    const total = series.reduce((a, d) => a + d.v, 0);
    const avg = Math.round(total / Math.max(series.length, 1));
    const goalHit = series.filter(d => d.v >= goalLine).length;

    const legend = isDaily
        ? `<span class="pp-chart-legend-item"><span class="pp-legend-dot" style="background:var(--english-primary)"></span>Session minutes</span>`
        : `
            <span class="pp-chart-legend-item"><span class="pp-legend-dot" style="background:var(--english-primary)"></span>Reading</span>
            <span class="pp-chart-legend-item"><span class="pp-legend-dot" style="background:var(--math-primary)"></span>Math</span>
            <span class="pp-chart-legend-item"><span class="pp-legend-dot" style="background:var(--diary-primary)"></span>Diary</span>
            <span class="pp-chart-legend-item"><span class="pp-legend-dot" style="background:var(--review-primary)"></span>Review</span>`;

    return `
        <div class="pp-card pp-chart-card">
            <div class="pp-chart-header">
                <div>
                    <div class="pp-kick-inline">${xLabel} · Learning minutes</div>
                    <div class="pp-chart-totals">
                        <span class="mono pp-chart-big">${total}</span>
                        <span class="pp-chart-sub">min · ${totalLabel} total</span>
                        ${_ppTrend(range === "monthly" ? 7 : range === "daily" ? 18 : 14)}
                    </div>
                    <div class="pp-chart-meta">
                        ${isDaily
                            ? `Per-session avg <span class="mono pp-chart-meta-strong">${avg}m</span> · ${series.length} sessions`
                            : `Daily avg <span class="mono pp-chart-meta-strong">${avg}m</span> · Goal hit <span class="mono pp-chart-meta-strong">${goalHit}/${series.length}</span>`}
                    </div>
                </div>
                <div class="pp-chart-legend">
                    ${legend}
                    <span class="pp-chart-legend-item"><span class="pp-legend-line"></span>${goalLabel}</span>
                </div>
            </div>
            <div class="pp-chart-body">
                ${_ppBarChart(series, { goalLine, height: 180, color: "var(--ink-1)", valueLabels: true })}
            </div>
        </div>`;
}

/** Reading summary mini card. @tag PARENT */
function _ppHomeReadingCard() {
    return `
        <div class="pp-card pp-mini-card">
            <div class="pp-card-head pp-mini-head">
                <span class="pp-card-head-left"><span class="pp-dot pp-dot--english"></span>Reading</span>
                <a href="#" class="pp-card-link" onclick="event.preventDefault();_ppLoadTab('reading')">Open tab →</a>
            </div>
            <div class="pp-mini-body" id="pp-home-reading-mini">
                <p class="pp-loading-center" style="padding:14px">Loading…</p>
            </div>
        </div>`;
}

/** Math summary mini card. @tag PARENT */
function _ppHomeMathCard() {
    // Lazy-load reading + math mini contents after first paint.
    setTimeout(_ppHomeLoadMiniCards, 0);
    return `
        <div class="pp-card pp-mini-card">
            <div class="pp-card-head pp-mini-head">
                <span class="pp-card-head-left"><span class="pp-dot pp-dot--math"></span>Math</span>
                <a href="#" class="pp-card-link" onclick="event.preventDefault();_ppLoadTab('math')">Open tab →</a>
            </div>
            <div class="pp-mini-body" id="pp-home-math-mini">
                <p class="pp-loading-center" style="padding:14px">Loading…</p>
            </div>
        </div>`;
}

/** Defer-load mini Reading + Math card bodies. @tag PARENT */
async function _ppHomeLoadMiniCards() {
    const [ckla, math] = await Promise.all([
        apiFetchJSON("/api/parent/ckla-summary").catch(() => null),
        apiFetchJSON("/api/parent/math-summary").catch(() => null),
    ]);

    const readingEl = document.getElementById("pp-home-reading-mini");
    if (readingEl) {
        if (ckla && Array.isArray(ckla.domains)) {
            const rows = ckla.domains.slice(0, 4).map(d => `
                <div class="pp-mini-row">
                    <span class="pp-mini-row-label">${escapeHtml(d.name || d.domain_name || "")}</span>
                    <span class="mono pp-mini-row-val">${d.lessons_done || 0}/${d.lessons_total || 0}</span>
                    <div class="pp-mini-bar"><div class="pp-mini-bar-fill" style="width:${Math.round((d.progress || 0) * 100)}%;background:var(--english-primary)"></div></div>
                </div>`).join("");
            readingEl.innerHTML = `
                <div class="pp-mini-kick">CKLA · G3</div>
                <div class="pp-mini-rows">${rows}</div>`;
        } else {
            readingEl.innerHTML = `<p class="pp-text-hint" style="padding:12px">No reading data yet.</p>`;
        }
    }

    const mathEl = document.getElementById("pp-home-math-mini");
    if (mathEl) {
        if (math) {
            const lessons = math.academy?.completed || 0;
            const totalLessons = math.academy?.total_lessons || 0;
            const accPct = math.recent_7d?.accuracy_pct;
            const accStr = accPct != null ? `${accPct}%` : "—";
            const weakCount = (math.weak_areas || []).length;
            const eqRate = math.academy?.eq_pass_rate != null ? `${math.academy.eq_pass_rate}%` : "—";
            mathEl.innerHTML = `
                <div class="pp-mini-flex">
                    <div>
                        <div class="pp-mini-kick">Academy</div>
                        <div class="mono pp-mini-big">${lessons}<span class="pp-mini-big-sub">/ ${totalLessons} lessons</span></div>
                    </div>
                </div>
                <div class="pp-mini-3">
                    <div><div class="pp-mini-kick">7d Accuracy</div><div class="mono pp-mini-val">${accStr}</div></div>
                    <div><div class="pp-mini-kick">Exit Quiz</div><div class="mono pp-mini-val">${eqRate}</div></div>
                    <div><div class="pp-mini-kick">Weak Areas</div><div class="mono pp-mini-val">${weakCount}</div></div>
                </div>`;
        } else {
            mathEl.innerHTML = `<p class="pp-text-hint" style="padding:12px">No math data yet.</p>`;
        }
    }
    if (typeof lucide !== "undefined") lucide.createIcons();
}
window._ppHomeLoadMiniCards = _ppHomeLoadMiniCards;

/** Approvals rail card. @tag PARENT DAY_OFF */
function _ppHomeApprovalsCard(allReqs, island) {
    const dayoff = allReqs.filter(r => r.status === "pending");
    const total = dayoff.length;

    const dayoffRows = dayoff.map(r => `
        <div class="pp-rail-row">
            <div class="pp-rail-row-head">
                <i data-lucide="calendar-x-2" class="pp-rail-icon-warn"></i>
                <span class="pp-rail-row-title">Day Off</span>
            </div>
            <div class="mono pp-rail-row-meta">${escapeHtml(r.request_date || "")}</div>
            <div class="pp-rail-row-body">"${escapeHtml(r.reason || "")}"</div>
            <div class="pp-rail-row-btns">
                <button class="pp-btn primary pp-btn--sm" onclick="_ppDecideDayOff(${r.id}, 'approved')">Approve</button>
                <button class="pp-btn secondary pp-btn--sm" onclick="_ppDecideDayOff(${r.id}, 'denied')">Deny</button>
            </div>
        </div>`).join("");

    return `
        <div class="pp-card pp-rail-card">
            <div class="pp-card-head pp-rail-head">
                <span class="pp-card-head-left">
                    <i data-lucide="${total ? "bell-dot" : "bell"}" class="${total ? "pp-rail-icon-bad" : ""}"></i>
                    Approvals
                </span>
                <span class="mono ${total ? "pp-rail-count--bad" : "pp-rail-count"}">${total} pending</span>
            </div>
            ${total === 0
                ? `<div class="pp-empty pp-rail-empty"><p class="pp-empty-title">No pending requests</p></div>`
                : dayoffRows}
        </div>`;
}

/** Streak rail card with 30-day grid (derived from daily activity). @tag PARENT STREAK */
function _ppHomeStreakCard(sum, daily) {
    const current = sum.current_streak || 0;
    const best = sum.longest_streak || 0;
    const rule = sum.streak_rule_label || "Any subject completed";
    const last30 = daily.slice(-30);

    // Pad with leading empties if activity history is shorter than 30 days.
    const pad = Math.max(0, 30 - last30.length);
    const cells = (Array.from({ length: pad }).map(() => null).concat(last30))
        .map(d => {
            const on = d && ((d.minutes || 0) > 0 || (d.sessions || 0) > 0 || (d.xp || 0) > 0);
            return `<div class="pp-streak-mini-cell ${on ? "is-on" : "is-off"}"></div>`;
        }).join("");

    return `
        <div class="pp-card pp-rail-card">
            <div class="pp-card-head pp-rail-head">
                <span class="pp-card-head-left"><i data-lucide="flame" class="pp-rail-icon-diary"></i>Streak</span>
                <span class="mono pp-rail-count">Best ${best}d</span>
            </div>
            <div class="pp-rail-body">
                <div class="pp-streak-mini-num">
                    <span class="mono pp-streak-mini-big">${current}</span>
                    <span class="pp-streak-mini-unit">days</span>
                </div>
                <div class="pp-streak-mini-rule">Rule: ${escapeHtml(rule)}</div>
                <div class="pp-streak-mini-grid">${cells}</div>
            </div>
        </div>`;
}

/** Island rail card. @tag PARENT ISLAND */
function _ppHomeIslandCard(island) {
    if (!island || !island.island_on) {
        return `
            <div class="pp-card pp-rail-card">
                <div class="pp-card-head pp-rail-head">
                    <span class="pp-card-head-left"><i data-lucide="palmtree" class="pp-rail-icon-rewards"></i>Island</span>
                </div>
                <div class="pp-rail-body">
                    <p class="pp-text-hint">Island disabled.</p>
                </div>
            </div>`;
    }
    const lumi = island.currency?.lumi || 0;
    const completed = island.completed_characters || [];
    const active = island.active_characters || [];
    const owned = (island.completed_count != null) ? island.completed_count : completed.length;
    const total = 24; // 5 chars × 4 zones + 4 legend = 24 (matches ISLAND_SPEC)
    const pct = total ? Math.round((owned / total) * 100) : 0;

    // Group characters by zone for the stacked bar.
    const allChars = completed.concat(active);
    const byZone = { forest: 0, ocean: 0, savanna: 0, space: 0, legend: 0 };
    allChars.forEach(c => {
        const z = (c.zone || "forest").toLowerCase();
        if (byZone[z] != null) byZone[z] += 1;
    });
    const segs = [
        { key: "english", v: byZone.forest,  label: "Forest"  },
        { key: "math",    v: byZone.ocean,   label: "Ocean"   },
        { key: "diary",   v: byZone.savanna, label: "Savanna" },
        { key: "rewards", v: byZone.space,   label: "Space"   },
        { key: "legend",  v: byZone.legend,  label: "Legend", color: "var(--legend-primary)" },
    ];
    const segSum = segs.reduce((a, s) => a + s.v, 0);

    return `
        <div class="pp-card pp-rail-card">
            <div class="pp-card-head pp-rail-head">
                <span class="pp-card-head-left"><i data-lucide="palmtree" class="pp-rail-icon-rewards"></i>Island</span>
                <span class="mono pp-rail-count">${owned}/${total}</span>
            </div>
            <div class="pp-rail-body">
                <div class="pp-island-mini-flex">
                    ${_ppRing(owned, total, { size: 52, stroke: 6, color: "var(--legend-primary)", label: `${pct}%` })}
                    <div class="pp-island-mini-right">
                        <div class="mono pp-island-mini-lumi">${lumi.toLocaleString()} <span class="pp-island-mini-lumi-sub">Lumi</span></div>
                        <div class="pp-island-mini-sub">${active.length} active · ${owned} completed</div>
                    </div>
                </div>
                <div class="pp-island-mini-stack">
                    ${segSum > 0 ? _ppStackBar(segs, { height: 6 }) : `<div style="height:6px;background:var(--line);border-radius:999px"></div>`}
                    <div class="pp-island-mini-legend">
                        ${segs.map(s => `<span>${s.label} ${s.v}</span>`).join("")}
                    </div>
                </div>
            </div>
        </div>`;
}

window._ppHome = _ppHome;
