/* ================================================================
   diary-calendar.js — GIA's Diary · Calendar (monthly)
   Section: Diary
   Dependencies: diary.js (escapeHtml, openDiarySection, _DH_MOODS),
                 diary-entry.js (_renderDiaryEntry)
   API endpoints: GET /api/diary/entries, GET /api/day-off/requests
   Spec: handoff/02b-diary-spec.md (Screen 4)
   ================================================================ */

const _DC_MOOD_ORDER = ["great", "happy", "calm", "curious", "tired", "sad"];

const _dcState = {
    year: 0,
    month: 0,        // 0..11
    today: null,     // Date
    entries: [],     // raw rows from /api/diary/entries
    dayOffs: [],     // raw rows from /api/day-off/requests
};

/* ── Entry point ───────────────────────────────────────────────── */

/**
 * Render the Diary Calendar (monthly grid + legend + summary).
 * @tag DIARY CALENDAR
 */
async function _renderDiaryCalendar() {
    const view = document.getElementById("diary-view");
    if (!view) return;

    document.body.classList.add("dh-fullscreen");
    view.classList.add("dc-active");
    view.style.display = "flex";

    if (!_dcState.today) {
        const t = new Date();
        _dcState.today = t;
        _dcState.year  = t.getFullYear();
        _dcState.month = t.getMonth();
    }

    view.innerHTML = `<div class="dc-root"><p class="diary-state-msg" style="padding:60px;">Loading…</p></div>`;

    await _dcLoadData();
    _dcPaint();
}

async function _dcLoadData() {
    let entries = [];
    let dayOffs = [];
    try {
        const [eRes, dRes] = await Promise.allSettled([
            fetch("/api/diary/entries?limit=500"),
            fetch("/api/day-off/requests"),
        ]);
        if (eRes.status === "fulfilled" && eRes.value.ok) {
            const d = await eRes.value.json();
            entries = Array.isArray(d.entries) ? d.entries : [];
        }
        if (dRes.status === "fulfilled" && dRes.value.ok) {
            const d = await dRes.value.json();
            dayOffs = Array.isArray(d.requests) ? d.requests : [];
        }
    } catch (_) {}
    _dcState.entries = entries;
    _dcState.dayOffs = dayOffs;
}

/* ── Paint ─────────────────────────────────────────────────────── */

function _dcPaint() {
    const view = document.getElementById("diary-view");
    if (!view) return;

    const monthLabel = new Date(_dcState.year, _dcState.month, 1)
        .toLocaleDateString("en-US", { month: "long" });

    // Build month index maps
    const ymPrefix = `${_dcState.year}-${String(_dcState.month + 1).padStart(2, "0")}`;
    const monthEntries = _dcState.entries.filter(e =>
        (e.entry_date || "").startsWith(ymPrefix));
    const monthDayOffs = _dcState.dayOffs.filter(r =>
        (r.request_date || "").startsWith(ymPrefix));

    const entryByDay  = {};   // day -> { id, mood }
    const dayOffByDay = {};   // day -> 'approved' | 'pending'

    for (const e of monthEntries) {
        const day = parseInt((e.entry_date || "").slice(8, 10), 10);
        if (!day) continue;
        let mood = e.mood || null;
        if (!mood) {
            try {
                const snap = JSON.parse(localStorage.getItem("nss.diary.entry." + e.id) || "null");
                if (snap && snap.mood) mood = snap.mood;
            } catch (_) {}
        }
        entryByDay[day] = { id: e.id, mood };
    }
    for (const r of monthDayOffs) {
        const day = parseInt((r.request_date || "").slice(8, 10), 10);
        if (!day) continue;
        const status = (r.status || "").toLowerCase();
        if (status === "approved" || status === "pending") {
            dayOffByDay[day] = status;
        }
    }

    // Mood counts for legend
    const moodCounts = _DC_MOOD_ORDER.reduce((a, k) => { a[k] = 0; return a; }, {});
    Object.values(entryByDay).forEach(({ mood }) => {
        if (mood && moodCounts[mood] != null) moodCounts[mood] += 1;
    });
    const dayOffCount = { approved: 0, pending: 0 };
    Object.values(dayOffByDay).forEach(s => { dayOffCount[s] = (dayOffCount[s] || 0) + 1; });

    // Build cells
    const firstDay = new Date(_dcState.year, _dcState.month, 1).getDay(); // 0=Sun
    const daysInMonth = new Date(_dcState.year, _dcState.month + 1, 0).getDate();
    const today = _dcState.today;
    const isCurrentMonth = today.getFullYear() === _dcState.year && today.getMonth() === _dcState.month;
    const todayDay = isCurrentMonth ? today.getDate() : -1;

    const cells = [];
    for (let i = 0; i < firstDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    while (cells.length % 7 !== 0) cells.push(null);

    const cellsHTML = cells.map((d, i) => {
        if (d === null) return `<div class="dc-cell is-empty"></div>`;
        const entry = entryByDay[d];
        const dayOff = dayOffByDay[d];
        const isToday = d === todayDay;
        const isFuture = (() => {
            if (_dcState.year > today.getFullYear()) return true;
            if (_dcState.year < today.getFullYear()) return false;
            if (_dcState.month > today.getMonth()) return true;
            if (_dcState.month < today.getMonth()) return false;
            return d > todayDay;
        })();
        const isMissed = !entry && !dayOff && !isFuture && !isToday;

        let cls = "dc-cell";
        if (isToday) cls += " is-today";
        else if (dayOff === "approved") cls += " is-dayoff-approved";
        else if (dayOff === "pending")  cls += " is-dayoff-pending";
        else if (isMissed) cls += " is-missed";
        else if (isFuture) cls += " is-future";
        if (entry) cls += " is-clickable";

        const onClick = entry
            ? `onclick="_dcOpenEntry(${entry.id})"`
            : "";

        let title = "";
        if (dayOff === "approved") title = "Day off · approved";
        else if (dayOff === "pending") title = "Day off · waiting for parent";
        else if (isMissed) title = "No entry this day";
        else if (entry) title = `Entry · ${entry.mood || "no mood"}`;

        const moodMeta = entry && entry.mood ? (window._DH_MOODS && window._DH_MOODS[entry.mood]) : null;
        const moodDot = moodMeta
            ? `<div class="dc-cell-mood" style="background:${moodMeta.dot};"></div>`
            : "";
        const coffee = dayOff
            ? `<div class="dc-cell-coffee"><i data-lucide="coffee"></i></div>`
            : "";
        const missedDot = isMissed ? `<div class="dc-cell-missed-dot"></div>` : "";

        return `
            <button class="${cls}" type="button" ${onClick}
                    ${isFuture || (!entry && !dayOff && !isMissed && !isToday) ? "disabled" : ""}
                    title="${escapeHtml(title)}">
                <div class="dc-cell-num">${d}</div>
                ${moodDot}${coffee}${missedDot}
            </button>`;
    }).join("");

    // Legend rows
    const legendRows = _DC_MOOD_ORDER.map(id => {
        const meta = window._DH_MOODS && window._DH_MOODS[id];
        const dot = meta ? meta.dot : "var(--border-subtle)";
        return `
            <div class="dc-legend-row">
                <div class="dc-legend-dot" style="background:${dot};"></div>
                <div class="dc-legend-label">${id}</div>
                <div class="dc-legend-count">${moodCounts[id] || 0}</div>
            </div>`;
    }).join("");

    // Summary text — small heuristic on dominant mood
    const top = _DC_MOOD_ORDER
        .map(k => [k, moodCounts[k]])
        .sort((a, b) => b[1] - a[1])[0];
    const dominant = top && top[1] > 0 ? top[0] : "happy";
    const quoteMap = {
        great:   "A bright month.",
        happy:   "Mostly happy.",
        calm:    "Quiet and steady.",
        curious: "A wondering month.",
        tired:   "A resting month.",
        sad:     "Some heavy days.",
    };
    const totalEntries = monthEntries.length;
    const totalWords = monthEntries.reduce(
        (sum, e) => sum + ((e.content || "").split(/\s+/).filter(Boolean).length), 0);

    const root = `
        <div class="dc-root" id="dc-root">
            <header class="dc-chrome">
                <div>
                    <button class="dc-back" type="button" onclick="openDiarySection('today')">
                        <i data-lucide="chevron-left"></i> Diary
                    </button>
                    <span class="dc-eyebrow">Diary · Month</span>
                    <div class="dc-title">${escapeHtml(monthLabel)} ${_dcState.year}</div>
                    <div class="dc-sub">${totalEntries} ${totalEntries === 1 ? "entry" : "entries"}</div>
                </div>
                <div class="dc-monthnav" role="group" aria-label="Change month">
                    <button type="button" aria-label="Previous month" onclick="_dcShiftMonth(-1)">
                        <i data-lucide="chevron-left"></i>
                    </button>
                    <div class="dc-monthnav-label">${escapeHtml(monthLabel.slice(0, 3))}</div>
                    <button type="button" aria-label="Next month" onclick="_dcShiftMonth(1)">
                        <i data-lucide="chevron-right"></i>
                    </button>
                </div>
            </header>

            <div class="dc-body">
                <div class="dc-card">
                    <span class="dh-washi" style="top:-9px;left:30px;width:100px;background:var(--diary-soft);transform:rotate(-3deg);"></span>
                    <div class="dc-weekdays">
                        ${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
                            .map(d => `<div class="dc-weekday">${d}</div>`).join("")}
                    </div>
                    <div class="dc-grid">${cellsHTML}</div>
                </div>

                <aside class="dc-aside">
                    <div class="dc-legend">
                        <div class="dc-legend-title">Mood legend</div>
                        <div class="dc-legend-grid">${legendRows}</div>
                        <div class="dc-legend-dayoff">
                            <div class="dc-legend-row">
                                <div class="dc-legend-tile approved"><i data-lucide="coffee"></i></div>
                                <div class="dc-legend-label">Day off</div>
                                <div class="dc-legend-count">${dayOffCount.approved || 0}</div>
                            </div>
                            <div class="dc-legend-row">
                                <div class="dc-legend-tile pending"><i data-lucide="coffee"></i></div>
                                <div class="dc-legend-label">Waiting</div>
                                <div class="dc-legend-count">${dayOffCount.pending || 0}</div>
                            </div>
                        </div>
                    </div>

                    <div class="dc-summary">
                        <span class="dh-washi" style="top:-9px;left:18px;width:70px;background:var(--arcade-soft);transform:rotate(-5deg);"></span>
                        <div class="dc-summary-eyebrow">${escapeHtml(monthLabel)} summary</div>
                        <div class="dc-summary-quote">${escapeHtml(quoteMap[dominant])}</div>
                        <div class="dc-summary-stats">
                            <div class="dc-mini">
                                <div class="dc-mini-value">${totalEntries}</div>
                                <div class="dc-mini-label">Entries</div>
                            </div>
                            <div class="dc-mini">
                                <div class="dc-mini-value">${_dcStreakInMonth(monthEntries)}</div>
                                <div class="dc-mini-label">Streak</div>
                            </div>
                            <div class="dc-mini">
                                <div class="dc-mini-value">${totalWords.toLocaleString()}</div>
                                <div class="dc-mini-label">Words</div>
                            </div>
                        </div>
                    </div>
                </aside>
            </div>
        </div>`;

    view.innerHTML = root;
    if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();
}

/** Longest consecutive-day streak observed within the month entries. */
function _dcStreakInMonth(entries) {
    const days = entries
        .map(e => parseInt((e.entry_date || "").slice(8, 10), 10))
        .filter(n => !Number.isNaN(n))
        .sort((a, b) => a - b);
    let best = 0, run = 0, prev = -1;
    for (const d of days) {
        run = (d === prev + 1) ? (run + 1) : 1;
        if (run > best) best = run;
        prev = d;
    }
    return best;
}

/* ── Handlers ──────────────────────────────────────────────────── */

function _dcShiftMonth(delta) {
    let m = _dcState.month + delta;
    let y = _dcState.year;
    while (m < 0)  { m += 12; y -= 1; }
    while (m > 11) { m -= 12; y += 1; }
    _dcState.month = m;
    _dcState.year  = y;
    _dcPaint();
}

function _dcOpenEntry(id) {
    if (typeof _renderDiaryEntry === "function") {
        const view = document.getElementById("diary-view");
        if (view) view.classList.remove("dc-active");
        if (view) view.classList.add("de-active");
        _renderDiaryEntry(id);
    }
}
