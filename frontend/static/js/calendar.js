/* ================================================================
   calendar.js — Monthly calendar view for GIA's Diary
   Section: Diary / Calendar
   Dependencies: core.js, diary.js (openDiarySection)
   API endpoints: /api/calendar/{year}/{month}
   ================================================================ */

// ─── State ────────────────────────────────────────────────────
let _calYear  = new Date().getFullYear();
let _calMonth = new Date().getMonth() + 1; // 1–12

// ─── Entry Point ──────────────────────────────────────────────

/**
 * Render the calendar view for the current month into #diary-view.
 * Called by diary.js when user selects "Calendar".
 * @tag CALENDAR DIARY
 */
async function renderCalendar() {
    const view = document.getElementById("diary-view");
    if (!view) return;

    _calYear  = new Date().getFullYear();
    _calMonth = new Date().getMonth() + 1;

    view.innerHTML = `
        <div class="diary-header">
            <button class="back-btn" onclick="_renderDiaryHome()">←</button>
            <div class="diary-header-text">
                <span class="diary-header-title">📅 Calendar</span>
            </div>
        </div>
        <div id="cal-container" style="width:100%;max-width:480px;margin:0 auto"></div>`;

    await _drawCalendar();
}

// ─── Draw Calendar ────────────────────────────────────────────

/**
 * Fetch data and render the calendar grid for _calYear / _calMonth.
 * @tag CALENDAR
 */
async function _drawCalendar() {
    const container = document.getElementById("cal-container");
    if (!container) return;

    const today  = new Date().toISOString().slice(0, 10);
    const m2     = String(_calMonth).padStart(2, "0");
    const label  = new Date(_calYear, _calMonth - 1, 1)
        .toLocaleDateString("en-US", { month: "long", year: "numeric" });

    // Fetch calendar data — backend returns a flat array of day objects
    let dayMap = {}; // "YYYY-MM-DD" → {marker, streak, journal, day_off}
    try {
        const res = await fetch(`/api/calendar/${_calYear}/${m2}`);
        if (res.ok) {
            const data = await res.json();
            const days = Array.isArray(data) ? data : (data.days || []);
            days.forEach(d => { dayMap[d.date] = d; });
        }
    } catch (_) {}

    // Build grid
    const firstDay  = new Date(_calYear, _calMonth - 1, 1).getDay(); // 0=Sun
    const daysInMon = new Date(_calYear, _calMonth, 0).getDate();
    const DAY_NAMES = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

    const headerCells = DAY_NAMES.map(d =>
        `<div class="cal-day-label">${d}</div>`).join("");

    const emptyCells = Array(firstDay).fill(`<div class="cal-day empty"></div>`).join("");

    const dayCells = Array.from({ length: daysInMon }, (_, i) => {
        const d = i + 1;
        const dateStr  = `${_calYear}-${m2}-${String(d).padStart(2, "0")}`;
        const info     = dayMap[dateStr] || {};
        const marker   = info.marker || "";
        const isToday  = dateStr === today;
        const isFuture = dateStr > today;
        const cls      = `cal-day${isToday ? " today" : ""}${isFuture ? " future" : " clickable"}`;
        const handler  = isFuture ? "" : ` onclick="_openCalendarDay('${dateStr}')"`;
        return `<div class="${cls}"${handler}>
            <span class="cal-day-num">${d}</span>
            ${marker ? `<span class="cal-day-marker">${marker}</span>` : ""}
        </div>`;
    }).join("");

    container.innerHTML = `
        <div class="cal-nav">
            <button class="cal-nav-btn" onclick="_calPrev()">‹</button>
            <span class="cal-month-label">${label}</span>
            <button class="cal-nav-btn" onclick="_calNext()">›</button>
        </div>
        <div class="cal-grid">
            ${headerCells}
            ${emptyCells}
            ${dayCells}
        </div>
        <div class="cal-legend">
            <span class="cal-legend-item">✅ All done</span>
            <span class="cal-legend-item">🔥 Streak</span>
            <span class="cal-legend-item">📝 Journal</span>
            <span class="cal-legend-item">🏖️ Day off</span>
            <span class="cal-legend-item">⬜ Missed</span>
        </div>`;
}

// ─── Day Detail Modal ────────────────────────────────────────

/**
 * Open a modal showing the diary entry + day-off info for a date.
 * @tag CALENDAR DIARY
 */
async function _openCalendarDay(dateStr) {
    const overlay = _ensureCalendarDayModal();
    const body    = overlay.querySelector(".cal-day-modal-body");
    const title   = overlay.querySelector(".cal-day-modal-title");
    const label   = new Date(dateStr + "T00:00:00")
        .toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
    title.textContent = label;
    body.innerHTML    = `<p class="diary-state-msg">Loading…</p>`;
    overlay.classList.remove("hidden");

    try {
        const [entryRes, dayOffRes] = await Promise.all([
            fetch(`/api/diary/entries?date=${dateStr}`),
            fetch(`/api/day-off/requests`),
        ]);
        const entryData  = entryRes.ok  ? await entryRes.json()  : { entries: [] };
        const dayOffData = dayOffRes.ok ? await dayOffRes.json() : { requests: [] };
        const entry  = (entryData.entries || [])[0];
        const dayOff = (dayOffData.requests || []).find(r => r.request_date === dateStr);

        const parts = [];
        if (dayOff) {
            parts.push(`<div class="cal-day-block">
                <div class="cal-day-block-label">🏖️ Day Off — <span class="status-badge ${dayOff.status}">${dayOff.status}</span></div>
                <div class="cal-day-block-text">${escapeHtml(dayOff.reason || "")}</div>
            </div>`);
        }
        if (entry) {
            if (entry.photo_path) {
                parts.push(`<img class="cal-day-photo" src="/api/diary/photo/${encodeURIComponent(entry.photo_path)}" alt="Journal photo">`);
            }
            if (entry.content) {
                parts.push(`<div class="cal-day-block">
                    <div class="cal-day-block-label">📝 Daily Journal</div>
                    <div class="cal-day-block-text">${escapeHtml(entry.content)}</div>
                </div>`);
            }
            if (entry.ai_feedback) {
                parts.push(`<div class="ai-feedback-box">
                    <div class="ai-feedback-label">✨ GIA says:</div>
                    <div class="ai-feedback-text">${escapeHtml(entry.ai_feedback)}</div>
                </div>`);
            }
        }
        if (!parts.length) {
            parts.push(`<p class="diary-state-msg">Nothing recorded for this day.</p>`);
        }
        body.innerHTML = parts.join("");
    } catch (_) {
        body.innerHTML = `<p class="diary-state-msg error">Failed to load.</p>`;
    }
}

/** Lazily create the day-detail modal element. @tag CALENDAR */
function _ensureCalendarDayModal() {
    let overlay = document.getElementById("cal-day-modal");
    if (overlay) return overlay;
    overlay = document.createElement("div");
    overlay.id        = "cal-day-modal";
    overlay.className = "cal-day-modal hidden";
    overlay.innerHTML = `
        <div class="cal-day-modal-card" role="dialog" aria-modal="true">
            <div class="cal-day-modal-header">
                <span class="cal-day-modal-title"></span>
                <button type="button" class="cal-day-modal-close" aria-label="Close">✕</button>
            </div>
            <div class="cal-day-modal-body"></div>
        </div>`;
    overlay.addEventListener("click", e => {
        if (e.target === overlay) overlay.classList.add("hidden");
    });
    overlay.querySelector(".cal-day-modal-close")
           .addEventListener("click", () => overlay.classList.add("hidden"));
    document.body.appendChild(overlay);
    return overlay;
}

// ─── Navigation ───────────────────────────────────────────────

/** Go to previous month. @tag CALENDAR */
function _calPrev() {
    _calMonth--;
    if (_calMonth < 1) { _calMonth = 12; _calYear--; }
    _drawCalendar();
}

/** Go to next month. @tag CALENDAR */
function _calNext() {
    _calMonth++;
    if (_calMonth > 12) { _calMonth = 1; _calYear++; }
    _drawCalendar();
}
