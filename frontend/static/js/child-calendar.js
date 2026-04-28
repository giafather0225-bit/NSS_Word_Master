/* ================================================================
   child-calendar.js — Sidebar Mini Calendar widget
   Section: System
   Dependencies: none (pure DOM + fetch)
   API endpoints: /api/dashboard/analytics
   ================================================================ */

// NOTE: distinct from the Phase 6 full Calendar in calendar.js — this one
// powers the small #sb-cal-grid widget in the sidebar. Renamed to _sbCal*
// to avoid colliding with calendar.js's _calYear/_calMonth (1-indexed).

/** @tag SYSTEM */
let _sbCalYear, _sbCalMonth;

/**
 * Alias kept for compatibility — delegates to initMonthlyCalendar().
 * @tag SYSTEM
 */
function initWeeklyCalendar() { initMonthlyCalendar(); }

/**
 * Initialise the monthly sidebar calendar and wire prev/next buttons.
 * @tag SYSTEM
 */
function initMonthlyCalendar() {
    const now = new Date();
    _sbCalYear  = now.getFullYear();
    _sbCalMonth = now.getMonth();
    renderMonthlyCalendar();
    const prev = document.getElementById("sb-cal-prev");
    const next = document.getElementById("sb-cal-next");
    if (prev) prev.onclick = function() { _sbCalMonth--; if (_sbCalMonth < 0)  { _sbCalMonth = 11; _sbCalYear--; } renderMonthlyCalendar(); };
    if (next) next.onclick = function() { _sbCalMonth++; if (_sbCalMonth > 11) { _sbCalMonth = 0;  _sbCalYear++; } renderMonthlyCalendar(); };
}

/**
 * Render the month grid into #sb-cal-grid and trigger study-data fetch.
 * @tag SYSTEM
 */
function renderMonthlyCalendar() {
    const grid  = document.getElementById("sb-cal-grid");
    const title = document.getElementById("sb-cal-title");
    if (!grid) return;
    const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    if (title) title.textContent = months[_sbCalMonth] + " " + _sbCalYear;
    grid.innerHTML = "";
    const headers = ["Mo","Tu","We","Th","Fr","Sa","Su"];
    headers.forEach(function(h) {
        const el = document.createElement("div");
        el.className = "sb-cal-day-header";
        el.textContent = h;
        grid.appendChild(el);
    });
    const firstDay    = new Date(_sbCalYear, _sbCalMonth, 1).getDay();
    const startOffset = firstDay === 0 ? 6 : firstDay - 1;
    const daysInMonth = new Date(_sbCalYear, _sbCalMonth + 1, 0).getDate();
    const now         = new Date();
    const todayDate   = now.getDate();
    const todayMonth  = now.getMonth();
    const todayYear   = now.getFullYear();
    for (let i = 0; i < startOffset; i++) {
        const empty = document.createElement("div");
        empty.className = "sb-cal-day empty";
        grid.appendChild(empty);
    }
    for (let d = 1; d <= daysInMonth; d++) {
        const cell = document.createElement("div");
        cell.className = "sb-cal-day";
        cell.textContent = d;
        cell.dataset.date = _sbCalYear + "-" + String(_sbCalMonth+1).padStart(2,"0") + "-" + String(d).padStart(2,"0");
        if (d === todayDate && _sbCalMonth === todayMonth && _sbCalYear === todayYear) {
            cell.classList.add("today");
        }
        grid.appendChild(cell);
    }
    loadMonthlyStudyData();
}

/**
 * Fetch analytics and highlight studied days on the calendar grid.
 * @tag SYSTEM
 */
function loadMonthlyStudyData() {
    fetch("/api/dashboard/analytics")
        .then(function(res) { return res.json(); })
        .then(function(data) {
            const sessions = data.daily_sessions || data.sessions || [];
            const studiedDates = new Set();
            sessions.forEach(function(s) {
                const dateStr = s.date || (s.started_at ? s.started_at.substring(0,10) : "");
                if (dateStr) studiedDates.add(dateStr);
            });
            const grid = document.getElementById("sb-cal-grid");
            if (!grid) return;
            grid.querySelectorAll(".sb-cal-day[data-date]").forEach(function(cell) {
                if (studiedDates.has(cell.dataset.date)) {
                    cell.classList.add("studied");
                }
            });
        })
        .catch(function() {});
}
