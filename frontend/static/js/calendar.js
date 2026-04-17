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

    // Fetch calendar data
    let dayMap = {}; // "YYYY-MM-DD" → {marker, streak, journal, day_off}
    try {
        const res = await fetch(`/api/calendar/${_calYear}/${m2}`);
        if (res.ok) {
            const data = await res.json();
            (data.days || []).forEach(d => { dayMap[d.date] = d; });
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
        const dateStr = `${_calYear}-${m2}-${String(d).padStart(2, "0")}`;
        const info    = dayMap[dateStr] || {};
        const marker  = info.marker || "";
        const isToday = dateStr === today;
        return `<div class="cal-day${isToday ? " today" : ""}">
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
            <span class="cal-legend-item">Streak</span>
            <span class="cal-legend-item">📝 Journal</span>
            <span class="cal-legend-item">🏖️ Day off</span>
            <span class="cal-legend-item">⬜ Missed</span>
        </div>`;
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
