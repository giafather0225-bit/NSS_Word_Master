/* ================================================================
   parent-panel-home-rail.js — Parent Dashboard: Home tab rail cards
   Section: Parent
   Dependencies: core.js, parent-panel.js, parent-panel-home.js
   API endpoints: /api/parent/ckla-summary, /api/parent/math-summary
   ================================================================ */

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
        apiFetchJSON("/api/parent/ckla-summary?grade=3").catch(() => null),
        apiFetchJSON("/api/parent/math-summary").catch(() => null),
    ]);

    const readingEl = document.getElementById("pp-home-reading-mini");
    if (readingEl) {
        if (ckla && Array.isArray(ckla.domains)) {
            const rows = ckla.domains.slice(0, 4).map(d => {
                const done  = d.completed_count || 0;
                const total = d.lesson_count    || 0;
                const pct   = total ? Math.round(done / total * 100) : 0;
                return `
                <div class="pp-mini-row">
                    <span class="pp-mini-row-label">${escapeHtml(d.title || `Domain ${d.domain_num}` || "")}</span>
                    <span class="mono pp-mini-row-val">${done}/${total}</span>
                    <div class="pp-mini-bar"><div class="pp-mini-bar-fill" style="width:${pct}%;background:var(--english-primary)"></div></div>
                </div>`;
            }).join("");
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
                    <div><div class="pp-mini-kick">Last 7 Days</div><div class="mono pp-mini-val">${accStr}</div></div>
                    <div><div class="pp-mini-kick">Exit Quiz</div><div class="mono pp-mini-val">${eqRate}</div></div>
                    <div><div class="pp-mini-kick">Weak Areas</div><div class="mono pp-mini-val">${weakCount}</div></div>
                </div>`;
        } else {
            mathEl.innerHTML = `<p class="pp-text-hint" style="padding:12px">No math data yet.</p>`;
        }
    }
    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** Alerts rail card — streak-at-risk, goals lagging, pending day-offs. @tag PARENT */
function _ppHomeAlertsCard(sum, dayoffs, goalsResp, daily) {
    const alerts = [];

    // 1. Pending day-off requests
    const pending = (dayoffs.requests || []).filter(r => r.status === "pending").length;
    if (pending > 0) {
        alerts.push({ icon: "calendar-x-2", type: "warn",
            text: `${pending} day-off request${pending > 1 ? "s" : ""} pending approval` });
    }

    // 2. Streak at risk: streak > 0 and no activity today
    const streak = sum.current_streak || 0;
    if (streak > 0) {
        const todayRow = (daily || []).slice(-1)[0] || {};
        const todayActive = (todayRow.minutes || 0) > 0 || (todayRow.sessions || 0) > 0 || (todayRow.xp || 0) > 0;
        if (!todayActive) {
            alerts.push({ icon: "flame", type: "warn",
                text: `Streak at risk — no activity yet today (${streak}d streak)` });
        }
    }

    // 3. Goals lagging: Thu-Sun and any active goal < 50% complete
    const dow = new Date().getDay(); // 0=Sun,4=Thu,5=Fri,6=Sat
    if ([0, 4, 5, 6].includes(dow)) {
        const lagging = (goalsResp.goals || []).filter(g => g.is_active && (g.pct || 0) < 50);
        if (lagging.length > 0) {
            alerts.push({ icon: "target", type: "info",
                text: `${lagging.length} weekly goal${lagging.length > 1 ? "s" : ""} behind pace (<50%)` });
        }
    }

    if (alerts.length === 0) return "";

    const rows = alerts.map(a => `
        <div class="pp-alert pp-alert--${a.type}">
            <i data-lucide="${a.icon}"></i>
            <span>${escapeHtml(a.text)}</span>
        </div>`).join("");

    return `
        <div class="pp-card pp-rail-card">
            <div class="pp-card-head pp-rail-head">
                <span class="pp-card-head-left">
                    <i data-lucide="alert-triangle" class="pp-rail-icon-bad"></i>Alerts
                </span>
                <span class="mono pp-rail-count--bad">${alerts.length}</span>
            </div>
            <div class="pp-alert-list">${rows}</div>
        </div>`;
}

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

window._ppHomeReadingCard    = _ppHomeReadingCard;
window._ppHomeMathCard       = _ppHomeMathCard;
window._ppHomeLoadMiniCards  = _ppHomeLoadMiniCards;
window._ppHomeAlertsCard     = _ppHomeAlertsCard;
window._ppHomeApprovalsCard  = _ppHomeApprovalsCard;
window._ppHomeStreakCard      = _ppHomeStreakCard;
window._ppHomeIslandCard     = _ppHomeIslandCard;
