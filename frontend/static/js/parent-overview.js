/* ================================================================
   parent-overview.js — Parent Dashboard: Home tab renderer
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/summary, /api/parent/overview,
                  /api/parent/activity, /api/parent/day-off-requests,
                  /api/goals/weekly
   ================================================================ */

/** Full Home tab: Hero + Today Progress + Week Calendar + vs Last Week + Alerts. @tag PARENT */
async function _ppHome(body) {
    try {
        const [sum, ov, act14, dayoffs, goals] = await Promise.all([
            apiFetchJSON("/api/parent/summary"),
            apiFetchJSON("/api/parent/overview"),
            apiFetchJSON("/api/parent/activity?days=14"),
            apiFetchJSON("/api/parent/day-off-requests").catch(() => ({ requests: [] })),
            apiFetchJSON("/api/goals/weekly").catch(() => ({ goals: [] })),
        ]);

        const bySubject = ov.today_by_subject || {
            english: { xp: 0, count: 0 },
            math:    { xp: 0, count: 0 },
            diary:   { xp: 0, count: 0 },
        };
        const todayXP    = ov.today_xp || 0;
        const activeCount = ["english", "math", "diary"]
            .filter(k => (bySubject[k]?.count || 0) > 0).length;

        const daily    = act14.daily || [];
        const thisWeek = daily.slice(-7);
        const lastWeek = daily.slice(-14, -7);

        const pendingDayoffs = (dayoffs.requests || []).filter(r => r.status === "pending");
        const weekMinutes    = thisWeek.reduce((a, d) => a + (d.minutes || 0), 0);

        body.innerHTML =
            _ppHomeHero(sum, todayXP, activeCount, weekMinutes) +
            _ppHomeWeekCalendar(thisWeek, sum) +
            `<div class="pp-grid-2">
                <div>${_ppHomeTodayProgress(bySubject)}</div>
                <div>${_ppHomeVsLastWeek(thisWeek, lastWeek)}</div>
             </div>` +
            _ppHomeAlerts(pendingDayoffs, todayXP, activeCount, sum, goals);

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-home] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`;
    }
}

/** Hero status banner with status icon + 3 quick-stat pills. @tag PARENT */
function _ppHomeHero(sum, todayXP, activeCount, weekMinutes) {
    let statusClass, statusMsg, statusIcon;
    if (activeCount >= 2 || todayXP >= 20) {
        statusClass = "pp-hero--green";
        statusMsg   = "Gia had a great day!";
        statusIcon  = "sun";
    } else if (activeCount >= 1 || todayXP > 0) {
        statusClass = "pp-hero--amber";
        statusMsg   = "Gia is making progress today.";
        statusIcon  = "trending-up";
    } else {
        statusClass = "pp-hero--red";
        statusMsg   = "Gia hasn’t studied yet today.";
        statusIcon  = "moon";
    }

    const streak = sum.current_streak || 0;

    return `
        <div class="pp-hero ${statusClass}">
            <div class="pp-hero-head">
                <i data-lucide="${statusIcon}" class="pp-hero-icon"></i>
                <div class="pp-hero-msg">${statusMsg}</div>
            </div>
            <div class="pp-hero-stats">
                <div class="pp-hero-stat">
                    <span class="pp-hero-num">${streak}</span>
                    <span class="pp-hero-label">Day Streak</span>
                </div>
                <div class="pp-hero-stat">
                    <span class="pp-hero-num">+${todayXP}</span>
                    <span class="pp-hero-label">XP Today</span>
                </div>
                <div class="pp-hero-stat">
                    <span class="pp-hero-num">${weekMinutes}m</span>
                    <span class="pp-hero-label">This Week</span>
                </div>
            </div>
        </div>`;
}

/** Per-subject completion rows for today, with XP earned. @tag PARENT */
function _ppHomeTodayProgress(bySubject) {
    const subjects = [
        { key: "english", label: "English", icon: "book-open" },
        { key: "math",    label: "Math",    icon: "calculator" },
        { key: "diary",   label: "Diary",   icon: "pen-line"   },
    ];

    const rows = subjects.map(s => {
        const data   = bySubject[s.key] || { xp: 0, count: 0 };
        const active = (data.count || 0) > 0;
        const badge  = active
            ? `+${data.xp || 0} XP <span class="pp-today-sub">· ${data.count}×</span>`
            : "Not started";
        return `
            <div class="pp-today-row${active ? " pp-today-row--active" : ""}">
                <div class="pp-today-subject">
                    <i data-lucide="${s.icon}" style="width:16px;height:16px"></i>
                    ${s.label}
                </div>
                <span class="pp-today-badge${active ? " pp-today-badge--done" : " pp-today-badge--none"}">
                    ${badge}
                </span>
            </div>`;
    }).join("");

    return `
        <div class="pp-section-title">Today’s Progress</div>
        <div class="pp-today-list">${rows}</div>`;
}

/** 7-day calendar strip with XP label. @tag PARENT */
function _ppHomeWeekCalendar(thisWeek, sum) {
    const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

    const cells = thisWeek.map((d, i) => {
        const active = (d.sessions || 0) > 0 || (d.xp || 0) > 0;
        return `
            <div class="pp-week-cell${active ? " pp-week-cell--active" : ""}">
                <div class="pp-week-day">${DAY_LABELS[i] || ""}</div>
                <div class="pp-week-dot${active ? " pp-week-dot--active" : ""}"></div>
                <div class="pp-week-xp">${active ? (d.xp || 0) : "–"}</div>
            </div>`;
    }).join("");

    return `
        <div class="pp-section-title" style="display:flex;justify-content:space-between;align-items:center">
            <span>This Week</span>
            <span style="font-size:12px;color:var(--text-secondary);font-weight:400">
                Streak <strong style="color:var(--text-primary)">${sum.current_streak || 0}d</strong>
                &nbsp;&middot;&nbsp; Best <strong style="color:var(--text-primary)">${sum.longest_streak || 0}d</strong>
            </span>
        </div>
        <div class="pp-week-grid">${cells}</div>`;
}

/** Three-row comparison vs previous week. @tag PARENT */
function _ppHomeVsLastWeek(thisWeek, lastWeek) {
    const sum7 = (arr, key) => arr.reduce((a, d) => a + (d[key] || 0), 0);

    const thisWords = sum7(thisWeek, "words_correct");
    const lastWords = sum7(lastWeek, "words_correct");
    const thisXP    = sum7(thisWeek, "xp");
    const lastXP    = sum7(lastWeek, "xp");
    const thisDays  = thisWeek.filter(d => (d.sessions || 0) > 0).length;
    const lastDays  = lastWeek.filter(d => (d.sessions || 0) > 0).length;

    const trend = (a, b, unit = "") => {
        const d = a - b;
        if (d > 0) return `<span class="pp-trend pp-trend--up">+${d}${unit} ↑</span>`;
        if (d < 0) return `<span class="pp-trend pp-trend--down">${d}${unit} ↓</span>`;
        return `<span class="pp-trend pp-trend--same">same →</span>`;
    };

    const row = (label, val, tr) => `
        <div class="pp-compare-row">
            <span class="pp-compare-label">${label}</span>
            <span class="pp-compare-val">${val}</span>
            ${tr}
        </div>`;

    return `
        <div class="pp-section-title">vs Last Week</div>
        <div class="pp-compare-grid">
            ${row("Words learned", thisWords, trend(thisWords, lastWords))}
            ${row("XP earned",     thisXP,    trend(thisXP,    lastXP))}
            ${row("Study days",    `${thisDays}/7`, trend(thisDays, lastDays, "d"))}
        </div>`;
}

/** Alert banners: pending day-offs, streak risk, goals at risk. @tag PARENT */
function _ppHomeAlerts(pendingDayoffs, todayXP, activeCount, sum, goalsResp) {
    const alerts = [];

    if (pendingDayoffs.length > 0) {
        const n = pendingDayoffs.length;
        alerts.push(`
            <div class="pp-alert pp-alert--warn" onclick="_ppLoadTab('habits')" style="cursor:pointer">
                <i data-lucide="calendar-off" style="width:16px;height:16px;flex-shrink:0"></i>
                <span>${n} day-off request${n > 1 ? "s" : ""} pending your approval</span>
                <i data-lucide="chevron-right" style="width:14px;height:14px;margin-left:auto;opacity:0.5"></i>
            </div>`);
    }

    if ((sum.current_streak || 0) >= 3 && todayXP === 0 && activeCount === 0) {
        alerts.push(`
            <div class="pp-alert pp-alert--info">
                <i data-lucide="flame" style="width:16px;height:16px;flex-shrink:0"></i>
                <span>Streak at risk — ${sum.current_streak}d streak, no activity yet today</span>
            </div>`);
    }

    // Goals at risk: active goals < 50% complete in the back half of the week (Thu-Sat)
    const dow = new Date().getDay(); // 0=Sun .. 6=Sat
    const inBackHalf = dow >= 4 || dow === 0; // Thu/Fri/Sat/Sun
    const lagging = (goalsResp?.goals || []).filter(g => g.is_active && (g.pct || 0) < 50 && !g.achieved);
    if (inBackHalf && lagging.length > 0) {
        alerts.push(`
            <div class="pp-alert pp-alert--warn" onclick="_ppLoadTab('goals')" style="cursor:pointer">
                <i data-lucide="target" style="width:16px;height:16px;flex-shrink:0"></i>
                <span>${lagging.length} goal${lagging.length > 1 ? "s" : ""} lagging this week — under 50% with the weekend ahead</span>
                <i data-lucide="chevron-right" style="width:14px;height:14px;margin-left:auto;opacity:0.5"></i>
            </div>`);
    }

    if (!alerts.length) return "";

    return `
        <div class="pp-section-title">Alerts</div>
        <div class="pp-alert-list">${alerts.join("")}</div>`;
}

window._ppHome = _ppHome;
