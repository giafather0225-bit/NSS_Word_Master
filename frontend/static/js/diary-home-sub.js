/* ================================================================
   diary-home-sub.js — Diary · Decorated sub-section screens
   Section: Diary
   Dependencies: diary-home.js (_dhIcon, _dhRefreshIcons, escapeHtml, openDiarySection),
                 diary-home-dayoff.js (_dhOpenDayOffModal)
   API endpoints: GET /api/growth/timeline · GET /api/day-off/requests
                  POST /api/day-off/request · GET /api/diary/:subject/:textbook
   ================================================================ */

// ─── Shared sub-section chrome ────────────────────────────────

/** @tag DIARY GROWTH_TIMELINE */
/* Shared chrome HTML for Decorated sub-sections (My Sentences / My Worlds /
   Growth Timeline / Day Off). Always returns to Diary Home. */
function _dsubChrome(eyebrow, title, sub, rightSlot) {
    return `
        <header class="ds-chrome">
            <div>
                <button class="ds-back" type="button" onclick="openDiarySection('today')">
                    ${_dhIcon("chevron-left", 14)} Diary
                </button>
                <span class="ds-eyebrow">${escapeHtml(eyebrow)}</span>
                <div class="ds-title">${escapeHtml(title)}</div>
                ${sub ? `<div class="ds-sub">${escapeHtml(sub)}</div>` : ""}
            </div>
            ${rightSlot ? `<div>${rightSlot}</div>` : ""}
        </header>`;
}

/* Mark Diary view as a Decorated sub-section so global CSS can scroll it. */
function _dsubPrep() {
    const view = document.getElementById("diary-view");
    if (!view) return null;
    view.style.display = "flex";
    view.classList.add("ds-active");
    document.body.classList.add("dh-fullscreen");
    return view;
}

// ─── Growth Timeline ──────────────────────────────────────────

async function _renderTimeline() {
    const view = _dsubPrep();
    if (!view) return;
    view.innerHTML = `
        <div class="ds-root">
            ${_dsubChrome("Diary · Growth", "Growth Timeline", "Your learning milestones over time")}
            <div class="ds-body" id="ds-tl-body">
                <p class="ds-loading">Loading…</p>
            </div>
        </div>`;
    _dhRefreshIcons();
    try {
        const res  = await fetch("/api/growth/timeline");
        if (!res.ok) throw new Error();
        const data = await res.json();
        const body = document.getElementById("ds-tl-body");
        const events = data.events || [];
        if (!events.length) {
            body.innerHTML = `<div class="ds-empty">
                <span class="ds-empty-icon"><i data-lucide="sprout" style="width:24px;height:24px;stroke-width:1.5"></i></span>
                Keep learning to unlock milestones!
            </div>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }
        const KIND = {
            lesson_pass:   "lesson",
            unit_pass:     "lesson",
            weekly_pass:   "lesson",
            streak_7:      "streak",
            streak_30:     "streak",
            theme_complete:"theme",
            milestone_100: "word",
        };
        body.innerHTML = `<div class="ds-timeline">${events.map(e => {
            const kind = KIND[e.event_type] || "default";
            return `<div class="ds-tl-row" data-kind="${kind}">
                <div class="ds-tl-title">${escapeHtml(e.title || "")}</div>
                ${e.detail ? `<div class="ds-tl-detail">${escapeHtml(e.detail)}</div>` : ""}
                <div class="ds-tl-date">${escapeHtml(e.event_date || "")}</div>
            </div>`;
        }).join("")}</div>`;
    } catch (_) {
        const body = document.getElementById("ds-tl-body");
        if (body) body.innerHTML = `<p class="ds-error">Failed to load.</p>`;
    }
}

// ─── Day Off sub-screen ───────────────────────────────────────

/** @tag DIARY DAY_OFF */
async function _renderDayOff() {
    const view = _dsubPrep();
    if (!view) return;
    view.innerHTML = `
        <div class="ds-root">
            ${_dsubChrome("Diary · Day Off", "Day off requests", "Past requests + how to send a new one")}
            <div class="ds-body">
                <div class="ds-do-cta-row">
                    <span class="dh-washi" style="top:-9px;left:24px;width:80px;background:var(--arcade-soft);transform:rotate(-4deg);"></span>
                    <div class="ds-do-cta-text">
                        <div class="ds-do-cta-title">Need a break day?</div>
                        <div class="ds-do-cta-sub">Send a request from Diary Home (max 2 per month).</div>
                    </div>
                    <button class="ds-do-cta-btn" type="button" onclick="_dsubGoHomeAndOpenDayOff()">
                        ${_dhIcon("coffee", 13)} Open request form
                    </button>
                </div>
                <div id="ds-do-list">
                    <p class="ds-loading">Loading past requests…</p>
                </div>
            </div>
        </div>`;
    _dhRefreshIcons();
    _loadDayOffStatus();
}

/** Bounce back to Home and pop the modal. Keeps a single source of truth
 *  for new-request UX rather than duplicating the form here. */
function _dsubGoHomeAndOpenDayOff() {
    openDiarySection("today");
    setTimeout(() => {
        if (typeof _dhOpenDayOffModal === "function") _dhOpenDayOffModal();
    }, 80);
}

/** Fill reason textarea from chip selection. @tag DIARY DAY_OFF */
function _selectDayOffChip(btn, text) {
    document.querySelectorAll(".dayoff-chip").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    const ta = document.getElementById("dayoff-reason");
    if (ta) ta.value = text;
}

/** POST a new day-off request. @tag DIARY DAY_OFF */
async function _submitDayOff(e) {
    e.preventDefault();
    const date   = document.getElementById("dayoff-date")?.value;
    const reason = document.getElementById("dayoff-reason")?.value?.trim();
    if (!date || !reason) return;
    const btn = document.getElementById("dayoff-btn");
    if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
    try {
        const res = await fetch("/api/day-off/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ request_date: date, reason }),
        });
        if (res.ok) {
            const data = await res.json().catch(() => ({}));
            if (btn) btn.textContent = data.email_queued ? "Sent (parent notified)" : "Sent";
            _loadDayOffStatus();
        } else {
            const err = await res.json().catch(() => ({}));
            if (btn) { btn.disabled = false; btn.textContent = "Send request"; }
            if (window.toast) window.toast(err.detail || "Could not submit.", "error");
        }
    } catch (_) {
        if (btn) { btn.disabled = false; btn.textContent = "Send request"; }
        if (window.toast) window.toast("Network error.", "error");
    }
}

/** Load past day-off requests. @tag DIARY DAY_OFF */
async function _loadDayOffStatus() {
    const el = document.getElementById("ds-do-list");
    if (!el) return;
    try {
        const res  = await fetch("/api/day-off/requests");
        if (!res.ok) return;
        const data = await res.json();
        const rows = data.requests || [];
        if (!rows.length) {
            el.innerHTML = `<div class="ds-empty">
                <span class="ds-empty-icon"><i data-lucide="coffee" style="width:24px;height:24px;stroke-width:1.5"></i></span>
                No requests yet.
            </div>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }
        const LABEL = { pending: "Pending", approved: "Approved", denied: "Denied" };
        el.innerHTML = `<div class="ds-do-list">${rows.map(r => {
            const s = (r.status || "pending").toLowerCase();
            return `<div class="ds-do-row">
                <div class="ds-do-info">
                    <div class="ds-do-date">${escapeHtml(r.request_date)}</div>
                    <div class="ds-do-reason">${escapeHtml(r.reason || "")}</div>
                </div>
                <span class="ds-do-status ${s}">${LABEL[s] || s}</span>
            </div>`;
        }).join("")}</div>`;
    } catch (_) {}
}

// ─── My Sentences ─────────────────────────────────────────────

/** @tag DIARY MY_SENTENCES */
function _sentenceAgeDays(iso, now) {
    if (!iso) return null;
    const t = Date.parse(iso);
    return isNaN(t) ? null : Math.floor((now - t) / 86400000);
}

/** @tag DIARY MY_SENTENCES */
async function _renderSentences() {
    const view = _dsubPrep();
    if (!view) return;
    view.innerHTML = `
        <div class="ds-root">
            ${_dsubChrome("Diary · Sentences", "My Sentences", "Sentences I created in Step 5 — older than 2 weeks ask for a rewrite")}
            <div class="ds-body" id="ds-sent-body">
                <p class="ds-loading">Loading…</p>
            </div>
        </div>`;
    _dhRefreshIcons();

    const subject  = (typeof currentSubject  !== "undefined" && currentSubject)  ? currentSubject  : "English";
    // "all" sentinel — empty path segment 404s on FastAPI.
    const textbook = (typeof currentTextbook !== "undefined" && currentTextbook) ? currentTextbook : "all";
    try {
        const res = await fetch(`/api/diary/${encodeURIComponent(subject)}/${encodeURIComponent(textbook)}`);
        if (!res.ok) throw new Error();
        const data    = await res.json();
        const body    = document.getElementById("ds-sent-body");
        const lessons = data.lessons || [];
        if (!lessons.length || data.total_sentences === 0) {
            body.innerHTML = `<div class="ds-empty">
                <span class="ds-empty-icon"><i data-lucide="file-text" style="width:24px;height:24px;stroke-width:1.5"></i></span>
                No sentences yet. Finish Step 5 of a lesson to start collecting them.
            </div>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }
        const now   = Date.now();
        const STALE = 14;
        const cards = lessons.flatMap(lesson =>
            (lesson.sentences || []).map(s => {
                const age   = _sentenceAgeDays(s.created_at, now);
                const stale = age !== null && age >= STALE;
                return `<div class="ds-sent-card ${stale ? "is-stale" : ""}">
                    <div class="ds-sent-head">
                        <div class="ds-sent-word">${escapeHtml(s.word || lesson.lesson || "")}</div>
                        ${stale ? `<span class="ds-sent-stale" title="${age} days ago">Rewrite</span>` : ""}
                    </div>
                    <div class="ds-sent-text">${escapeHtml(s.sentence || "")}</div>
                </div>`;
            })
        ).join("");
        body.innerHTML = `<div class="ds-sent-grid">${cards}</div>`;
    } catch (_) {
        const body = document.getElementById("ds-sent-body");
        if (body) body.innerHTML = `<p class="ds-error">Failed to load.</p>`;
    }
}
