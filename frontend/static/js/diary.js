/* ================================================================
   diary.js — GIA's Diary section (Notion+Linear editorial style)
   Section: Diary
   Dependencies: core.js
   API endpoints: /api/diary/entries, /api/growth/timeline,
                  /api/day-off/request, /api/practice/sentences
   ================================================================ */

// ─── Navigation ───────────────────────────────────────────────

/**
 * Open a diary sub-section and render its content.
 * @tag DIARY NAVIGATION
 * @param {'today'|'journal'|'freewriting'|'timeline'|'dayoff'|'sentences'|'calendar'|'worlds'} section
 */
function openDiarySection(section) {
    const view = document.getElementById("diary-view");
    if (!view) return;
    view.style.display = "flex";

    // Highlight active sidebar item
    document.querySelectorAll("#sb-diary-section .sb-sidebar-card").forEach(btn => {
        btn.classList.remove("active");
    });

    switch (section) {
        case "today":       _renderDiaryToday();   break;
        case "journal":     _renderJournal();      break;
        case "freewriting": _renderFreeWriting();  break;
        case "timeline":    _renderTimeline();     break;
        case "dayoff":      _renderDayOff();       break;
        case "sentences":   _renderSentences();    break;
        case "calendar":    renderCalendar();      break;
        case "worlds":      _renderWorlds();       break;
        default:            _renderDiaryToday();
    }
}

/** Shared section header HTML (no back button — sidebar handles nav). @tag DIARY */
function _diaryHeader(title, dateStr, sub) {
    return `
        <div class="diary-section-header">
            ${dateStr ? `<div class="diary-section-date">${escapeHtml(dateStr)}</div>` : ""}
            <div class="diary-section-title">${escapeHtml(title)}</div>
            ${sub ? `<div class="diary-section-sub">${escapeHtml(sub)}</div>` : ""}
        </div>`;
}

/** Format a date for display. */
function _fmtDate(d) {
    return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}

// ─── Today Dashboard ─────────────────────────────────────────

/**
 * Render the Diary Today dashboard (stats, week, recent sentences, milestones).
 * @tag DIARY
 */
async function _renderDiaryToday() {
    const view = document.getElementById("diary-view");
    const today = new Date();
    const todayStr = today.toISOString().slice(0, 10);
    const greeting = today.getHours() < 12 ? "Good morning" : today.getHours() < 17 ? "Good afternoon" : "Good evening";
    const dateLabel = today.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

    view.innerHTML = `
        <div class="diary-section-header">
            <div class="diary-section-date">${escapeHtml(dateLabel)}</div>
            <div class="diary-section-title">${greeting}, Gia.</div>
        </div>
        <div class="diary-today" id="diary-today-body">
            <div class="diary-stats-row" id="diary-stats-row">
                <div class="diary-stat"><div class="diary-stat-label">Entries</div><div class="diary-stat-value" id="dst-entries">—</div><div class="diary-stat-unit">total</div></div>
                <div class="diary-stat"><div class="diary-stat-label">Words</div><div class="diary-stat-value" id="dst-words">—</div><div class="diary-stat-unit">written</div></div>
                <div class="diary-stat"><div class="diary-stat-label">Streak</div><div class="diary-stat-value streak" id="dst-streak">—</div><div class="diary-stat-unit">days</div></div>
                <div class="diary-stat"><div class="diary-stat-label">Sentences</div><div class="diary-stat-value" id="dst-sentences">—</div><div class="diary-stat-unit">collected</div></div>
            </div>
            <div class="diary-week-section">
                <div class="diary-week-label">This Week</div>
                <div class="diary-week-row" id="diary-week-row"></div>
            </div>
            <div class="diary-today-section" id="diary-recent-section">
                <div class="diary-today-section-head">
                    <div class="diary-today-section-label">Recent Sentences</div>
                    <button class="diary-today-view-all" onclick="openDiarySection('sentences')">View all →</button>
                </div>
                <div id="diary-recent-sentences"><p class="diary-state-msg compact">Loading…</p></div>
            </div>
            <div class="diary-today-section" id="diary-milestones-section">
                <div class="diary-today-section-head">
                    <div class="diary-today-section-label">Growth Milestones</div>
                </div>
                <div class="diary-milestones-row" id="diary-milestones-row">
                    <p class="diary-state-msg compact">Loading…</p>
                </div>
            </div>
        </div>`;

    _loadTodayStats(todayStr);
    _loadWeekCalendar(today);
    _loadRecentSentences();
    _loadMilestones();
}

/** Load entry count, word count, streak, sentence count. @tag DIARY */
async function _loadTodayStats(todayStr) {
    try {
        const [entriesRes, streakRes, sentencesRes] = await Promise.allSettled([
            fetch(`/api/diary/entries?limit=100`),
            fetch(`/api/streak/status`),
            fetch(`/api/diary/${encodeURIComponent(typeof currentSubject !== "undefined" ? currentSubject : "English")}/${encodeURIComponent(typeof currentTextbook !== "undefined" ? currentTextbook : "")}`),
        ]);

        if (entriesRes.status === "fulfilled" && entriesRes.value.ok) {
            const d = await entriesRes.value.json();
            const entries = d.entries || [];
            const totalWords = entries.reduce((sum, e) => sum + (e.content || "").split(/\s+/).filter(Boolean).length, 0);
            const el = document.getElementById("dst-entries");
            const wEl = document.getElementById("dst-words");
            if (el) el.textContent = entries.length;
            if (wEl) wEl.textContent = totalWords.toLocaleString();
        }

        if (streakRes.status === "fulfilled" && streakRes.value.ok) {
            const d = await streakRes.value.json();
            const el = document.getElementById("dst-streak");
            if (el) el.textContent = d.streak_days ?? d.current_streak ?? "0";
        }

        if (sentencesRes.status === "fulfilled" && sentencesRes.value.ok) {
            const d = await sentencesRes.value.json();
            const el = document.getElementById("dst-sentences");
            if (el) el.textContent = d.total_sentences ?? 0;
        }
    } catch (_) {}
}

/** Render the Mon–Sun week row with entry status. @tag DIARY */
async function _loadWeekCalendar(today) {
    const row = document.getElementById("diary-week-row");
    if (!row) return;

    const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const todayStr  = today.toISOString().slice(0, 10);

    // Build Mon–Sun for the current week
    const dayOfWeek = today.getDay(); // 0=Sun
    const monday    = new Date(today);
    monday.setDate(today.getDate() - ((dayOfWeek + 6) % 7));

    const days = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(monday);
        d.setDate(monday.getDate() + i);
        return d;
    });

    // Fetch entries for this week range
    const from = days[0].toISOString().slice(0, 10);
    const to   = days[6].toISOString().slice(0, 10);
    let entryDates = new Set();
    try {
        const res = await fetch(`/api/diary/entries?from=${from}&to=${to}`);
        if (res.ok) {
            const data = await res.json();
            (data.entries || []).forEach(e => entryDates.add((e.entry_date || "").slice(0, 10)));
        }
    } catch (_) {}

    row.innerHTML = days.map(d => {
        const ds = d.toISOString().slice(0, 10);
        const isToday    = ds === todayStr;
        const hasEntry   = entryDates.has(ds);
        const isFuture   = ds > todayStr;
        let cls = "diary-week-day-box";
        if (isToday)  cls += " today";
        else if (hasEntry) cls += " has-entry";
        return `<div class="diary-week-day">
            <div class="diary-week-day-name">${DAY_NAMES[d.getDay()]}</div>
            <div class="${cls}">${isFuture ? "" : (hasEntry || isToday ? "✓" : d.getDate())}</div>
        </div>`;
    }).join("");
}

/** Load 3 most recent sentences. @tag DIARY */
async function _loadRecentSentences() {
    const el = document.getElementById("diary-recent-sentences");
    if (!el) return;
    try {
        const subject  = typeof currentSubject  !== "undefined" ? currentSubject  : "English";
        const textbook = typeof currentTextbook !== "undefined" ? currentTextbook : "";
        const res = await fetch(`/api/diary/${encodeURIComponent(subject)}/${encodeURIComponent(textbook)}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        const all = (data.lessons || []).flatMap(l => l.sentences || []).slice(0, 3);
        if (!all.length) {
            el.innerHTML = `<p class="diary-state-msg compact">No sentences yet. Complete Step 5!</p>`;
            return;
        }
        el.innerHTML = all.map(s => `
            <div class="diary-recent-sentence">
                <div class="diary-recent-sentence-word">${escapeHtml(s.word || "")}</div>
                <div class="diary-recent-sentence-text">${escapeHtml(s.sentence || "")}</div>
            </div>`).join("");
    } catch (_) {
        el.innerHTML = `<p class="diary-state-msg compact">—</p>`;
    }
}

/** Load recent growth milestones. @tag DIARY */
async function _loadMilestones() {
    const row = document.getElementById("diary-milestones-row");
    if (!row) return;
    try {
        const res = await fetch("/api/growth/timeline");
        if (!res.ok) throw new Error();
        const data = await res.json();
        const events = (data.events || []).slice(0, 4);
        if (!events.length) {
            row.innerHTML = `<p class="diary-state-msg compact">Keep learning to unlock milestones!</p>`;
            return;
        }
        const DOT_CLASS = { streak_7: "streak", lesson_pass: "", milestone_100: "success", theme_complete: "lilac" };
        row.innerHTML = events.map(e => `
            <div class="diary-milestone">
                <div class="diary-milestone-dot ${DOT_CLASS[e.event_type] || ""}"></div>
                <div>
                    <div class="diary-milestone-text">${escapeHtml(e.title)}</div>
                    <div class="diary-milestone-date">${escapeHtml(e.event_date || "")}</div>
                </div>
            </div>`).join("");
    } catch (_) {
        if (row) row.innerHTML = "";
    }
}

// ─── Daily Journal ────────────────────────────────────────────

/**
 * Render the Daily Journal — 2-column: editor + AI panel.
 * @tag DIARY JOURNAL
 */
async function _renderJournal() {
    const view = document.getElementById("diary-view");
    const today    = new Date();
    const todayStr = today.toISOString().slice(0, 10);
    const dateLabel = today.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });

    view.innerHTML = `
        ${_diaryHeader("Today's journal", dateLabel.toUpperCase())}
        <div class="diary-journal-layout">
            <div class="diary-journal-editor">
                <textarea id="journal-text" class="journal-textarea"
                    placeholder="Write about your day in English…"
                    oninput="_journalCharCount(this)"></textarea>
                <div class="diary-journal-meta">
                    <div class="journal-char-count" id="journal-cc">0 characters · <span id="journal-word-count">0</span> words</div>
                    <button class="journal-submit-btn" onclick="_submitJournal('${todayStr}')">Save &amp; Get Feedback</button>
                </div>
                <div class="journal-photo-row">
                    <input type="file" id="journal-photo-input" accept="image/*"
                           data-date="${todayStr}" onchange="_uploadJournalPhoto(this)" hidden />
                    <button type="button" class="journal-photo-btn"
                            onclick="document.getElementById('journal-photo-input').click()">
                        <i data-lucide="camera" width="14" height="14"></i> Add Photo
                    </button>
                    <span class="journal-photo-status" id="journal-photo-status"></span>
                </div>
                <div id="journal-photo-preview" class="journal-photo-preview"></div>
            </div>
            <div class="diary-ai-panel">
                <div class="diary-ai-panel-label">GIA says</div>
                <div id="journal-feedback">
                    <div class="diary-ai-empty">Feedback updates as you write.</div>
                </div>
            </div>
        </div>`;

    if (typeof lucide !== "undefined") lucide.createIcons();

    // Load existing entry
    try {
        const res = await fetch(`/api/diary/entries?date=${todayStr}`);
        if (res.ok) {
            const data = await res.json();
            if (data.entries && data.entries.length > 0) {
                const entry = data.entries[0];
                const ta = document.getElementById("journal-text");
                if (ta) { ta.value = entry.content || ""; _journalCharCount(ta); }
                if (entry.ai_feedback) _showFeedback(entry.ai_feedback);
                if (entry.photo_path)  _showJournalPhoto(entry.photo_path);
            }
        }
    } catch (_) {}
}

/** Render the journal photo preview. @tag DIARY JOURNAL */
function _showJournalPhoto(filename) {
    const el = document.getElementById("journal-photo-preview");
    if (!el) return;
    const safe = encodeURIComponent(filename);
    el.innerHTML = `
        <img class="journal-photo-img" src="/api/diary/photo/${safe}" alt="Journal photo" />
        <button type="button" class="journal-photo-remove" onclick="_removeJournalPhoto('${escapeHtml(filename)}')">Remove photo</button>`;
}

/** Upload a journal photo. @tag DIARY JOURNAL */
async function _uploadJournalPhoto(input) {
    const file = input.files && input.files[0];
    if (!file) return;
    const date   = input.dataset.date;
    const status = document.getElementById("journal-photo-status");
    if (status) status.textContent = "Uploading…";
    const fd = new FormData();
    fd.append("entry_date", date);
    fd.append("file", file);
    try {
        const res = await fetch("/api/diary/photo", { method: "POST", body: fd });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            if (status) status.textContent = err.detail || "Upload failed.";
            return;
        }
        const data = await res.json();
        if (status) status.textContent = "";
        if (data.photo_path) _showJournalPhoto(data.photo_path);
    } catch (_) {
        if (status) status.textContent = "Upload failed.";
    } finally { input.value = ""; }
}

/** Delete the journal photo. @tag DIARY JOURNAL */
async function _removeJournalPhoto(filename) {
    try { await fetch(`/api/diary/photo/${encodeURIComponent(filename)}`, { method: "DELETE" }); } catch (_) {}
    const el = document.getElementById("journal-photo-preview");
    if (el) el.innerHTML = "";
}

/** Update character + word count. @tag DIARY JOURNAL */
function _journalCharCount(ta) {
    const el   = document.getElementById("journal-cc");
    const wEl  = document.getElementById("journal-word-count");
    const words = ta.value.trim().split(/\s+/).filter(Boolean).length;
    if (el)  el.innerHTML = `${ta.value.length} characters · <span id="journal-word-count">${words}</span> words`;
}

/** POST journal entry and show AI feedback. @tag DIARY JOURNAL AI */
async function _submitJournal(date) {
    const ta = document.getElementById("journal-text");
    if (!ta || !ta.value.trim()) return;
    const btn = document.querySelector(".journal-submit-btn");
    const resetBtn = () => { if (btn) { btn.disabled = false; btn.textContent = "Save & Get Feedback"; } };
    if (btn) { btn.disabled = true; btn.textContent = "Saving…"; }
    try {
        const res = await fetch("/api/diary/entries", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: ta.value, entry_date: date }),
        });
        if (res.ok) {
            const data = await res.json();
            if (btn) { btn.disabled = false; btn.textContent = "Saved ✓"; }
            if (data.ai_feedback) _showFeedback(data.ai_feedback);
            return;
        }
        if (res.status !== 422) {
            let detail = "";
            try { detail = (await res.json()).detail || ""; } catch (_) {}
            if (window.toast) window.toast(detail || "Could not save entry.", "error");
        }
        resetBtn();
    } catch (_) {
        if (window.toast) window.toast("Network error — try again.", "error");
        resetBtn();
    }
}

/** Render AI feedback in the right panel. @tag DIARY JOURNAL */
function _showFeedback(text) {
    const el = document.getElementById("journal-feedback");
    if (!el) return;
    el.innerHTML = `
        <div class="ai-feedback-box">
            <div class="ai-feedback-label">
                <i data-lucide="sparkles" width="12" height="12"></i> Feedback
            </div>
            <div class="ai-feedback-text">${escapeHtml(text)}</div>
        </div>`;
    if (typeof lucide !== "undefined") lucide.createIcons();
}

// ─── Free Writing ─────────────────────────────────────────────

/** Render the Free Writing section. @tag DIARY */
async function _renderFreeWriting() {
    const view = document.getElementById("diary-view");
    view.innerHTML = `
        ${_diaryHeader("Free Writing", "", "Write anything on your mind.")}
        <div class="diary-body" style="max-width:640px">
            <div class="freewrite-area">
                <div class="freewrite-composer">
                    <input class="freewrite-title-input" id="fw-title" type="text" placeholder="Title (optional)" />
                    <textarea class="freewrite-textarea" id="fw-body" placeholder="Write freely…"></textarea>
                    <button class="journal-submit-btn" style="align-self:flex-end" onclick="_submitFreeWrite()">Save</button>
                </div>
                <div class="freewrite-section-title">Previous</div>
                <div class="freewrite-list" id="fw-list"><p class="diary-state-msg compact">Loading…</p></div>
            </div>
        </div>`;
    _loadFreeWrites();
}

/** Load saved free writes. @tag DIARY */
async function _loadFreeWrites() {
    const el = document.getElementById("fw-list");
    if (!el) return;
    try {
        const res = await fetch("/api/diary/freewrites");
        if (!res.ok) { el.innerHTML = `<p class="diary-state-msg">—</p>`; return; }
        const data = await res.json();
        const items = data.entries || [];
        if (!items.length) { el.innerHTML = `<p class="diary-state-msg compact">Nothing yet.</p>`; return; }
        el.innerHTML = items.map(fw => `
            <div class="freewrite-card">
                <div class="freewrite-card-head">
                    <div class="freewrite-card-title">${escapeHtml(fw.title || "Untitled")}</div>
                    <div class="freewrite-card-date">${escapeHtml(fw.entry_date || "")}</div>
                </div>
                <div class="freewrite-card-body">${escapeHtml(fw.content || "")}</div>
                <button class="freewrite-delete-btn" onclick="_deleteFreeWrite(${fw.id})">Delete</button>
            </div>`).join("");
    } catch (_) { el.innerHTML = `<p class="diary-state-msg compact">—</p>`; }
}

/** POST a new free write entry. @tag DIARY */
async function _submitFreeWrite() {
    const title   = document.getElementById("fw-title")?.value?.trim();
    const content = document.getElementById("fw-body")?.value?.trim();
    if (!content) return;
    try {
        const res = await fetch("/api/diary/freewrites", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: title || "Untitled", content, entry_date: new Date().toISOString().slice(0, 10) }),
        });
        if (res.ok) {
            const inp = document.getElementById("fw-title");
            const ta  = document.getElementById("fw-body");
            if (inp) inp.value = "";
            if (ta)  ta.value  = "";
            _loadFreeWrites();
        }
    } catch (_) {}
}

/** DELETE a free write entry. @tag DIARY */
async function _deleteFreeWrite(id) {
    try {
        await fetch(`/api/diary/freewrites/${id}`, { method: "DELETE" });
        _loadFreeWrites();
    } catch (_) {}
}

// ─── Growth Timeline ──────────────────────────────────────────

/** @tag DIARY GROWTH_TIMELINE */
async function _renderTimeline() {
    const view = document.getElementById("diary-view");
    view.innerHTML = `
        ${_diaryHeader("Growth Timeline", "", "Your learning milestones")}
        <div class="diary-body" id="timeline-body"><p class="diary-state-msg">Loading…</p></div>`;
    try {
        const res  = await fetch("/api/growth/timeline");
        if (!res.ok) throw new Error();
        const data = await res.json();
        const body = document.getElementById("timeline-body");
        if (!data.events || data.events.length === 0) {
            body.innerHTML = `<p class="diary-state-msg">No events yet. Keep learning!</p>`;
            return;
        }
        body.innerHTML = `<div class="timeline-list">${data.events.map(e => `
            <div class="timeline-item">
                <div class="timeline-info">
                    <div class="timeline-title">${escapeHtml(e.title)}</div>
                    <div class="timeline-date">${escapeHtml(e.event_date || "")}</div>
                </div>
            </div>`).join("")}</div>`;
    } catch (_) {
        const body = document.getElementById("timeline-body");
        if (body) body.innerHTML = `<p class="diary-state-msg error">Failed to load.</p>`;
    }
}

// ─── Day Off ──────────────────────────────────────────────────

/** @tag DIARY DAY_OFF */
async function _renderDayOff() {
    const view = document.getElementById("diary-view");
    const today = new Date().toISOString().slice(0, 10);
    const REASON_CHIPS = ["Feeling sick", "Family event", "School trip", "Too tired"];

    view.innerHTML = `
        ${_diaryHeader("Need a break day?", "", "Send a request to your parent.")}
        <div class="diary-dayoff-layout">
            <form class="dayoff-form" onsubmit="_submitDayOff(event)">
                <div class="dayoff-field">
                    <label class="dayoff-label">Date</label>
                    <input class="dayoff-input" type="date" id="dayoff-date" value="${today}" required />
                </div>
                <div class="dayoff-field">
                    <label class="dayoff-label">Reason</label>
                    <div class="dayoff-chips">
                        ${REASON_CHIPS.map(r =>
                            `<button type="button" class="dayoff-chip" onclick="_selectDayOffChip(this, '${escapeHtml(r)}')">${escapeHtml(r)}</button>`
                        ).join("")}
                    </div>
                    <textarea class="dayoff-textarea" id="dayoff-reason" placeholder="Tell your parent why…" required></textarea>
                </div>
                <button type="submit" class="journal-submit-btn" id="dayoff-btn">Send request</button>
            </form>
            <div class="dayoff-history">
                <div class="dayoff-history-label">Past requests</div>
                <div id="dayoff-status"></div>
            </div>
        </div>`;
    _loadDayOffStatus();
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
            if (btn) btn.textContent = data.email_queued ? "Sent ✓ (parent notified)" : "Sent ✓";
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
    const el = document.getElementById("dayoff-status");
    if (!el) return;
    try {
        const res  = await fetch("/api/day-off/requests");
        if (!res.ok) return;
        const data = await res.json();
        const rows = data.requests || [];
        if (!rows.length) { el.innerHTML = `<p class="diary-state-msg compact">No previous requests.</p>`; return; }
        const LABEL = { pending: "Pending", approved: "Approved", denied: "Denied" };
        el.innerHTML = `<div class="dayoff-status-list">${rows.map(r => {
            const s = (r.status || "pending").toLowerCase();
            return `<div class="dayoff-status-row">
                <div class="dayoff-status-info">
                    <div class="dayoff-status-date">${escapeHtml(r.request_date)}</div>
                    <div class="dayoff-status-reason">${escapeHtml(r.reason || "")}</div>
                </div>
                <span class="status-badge ${s}">${LABEL[s] || s}</span>
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
    const view = document.getElementById("diary-view");
    view.innerHTML = `
        ${_diaryHeader("My Sentences", "", "Sentences I created in Step 5")}
        <div class="diary-body" id="sentences-body"><p class="diary-state-msg">Loading…</p></div>`;

    const subject  = (typeof currentSubject  !== "undefined" && currentSubject)  ? currentSubject  : "English";
    const textbook = (typeof currentTextbook !== "undefined" && currentTextbook) ? currentTextbook : "";
    try {
        const res = await fetch(`/api/diary/${encodeURIComponent(subject)}/${encodeURIComponent(textbook)}`);
        if (!res.ok) throw new Error();
        const data    = await res.json();
        const body    = document.getElementById("sentences-body");
        const lessons = data.lessons || [];
        if (!lessons.length || data.total_sentences === 0) {
            body.innerHTML = `<p class="diary-state-msg">No sentences yet. Complete Step 5!</p>`;
            return;
        }
        const now   = Date.now();
        const STALE = 14;
        const cards = lessons.flatMap(lesson =>
            lesson.sentences.map(s => {
                const age   = _sentenceAgeDays(s.created_at, now);
                const stale = age !== null && age >= STALE;
                return `<div class="sentence-card${stale ? " stale" : ""}">
                    <div class="sentence-card-head">
                        <div class="sentence-word">${escapeHtml(s.word || lesson.lesson || "")}</div>
                        ${stale ? `<span class="sentence-rewrite-badge" title="${age} days ago">Rewrite</span>` : ""}
                    </div>
                    <div class="sentence-text">${escapeHtml(s.sentence || "")}</div>
                </div>`;
            })
        ).join("");
        body.innerHTML = `<div class="sentences-list">${cards}</div>`;
    } catch (_) {
        const body = document.getElementById("sentences-body");
        if (body) body.innerHTML = `<p class="diary-state-msg error">Failed to load.</p>`;
    }
}

// ─── My Worlds ────────────────────────────────────────────────

/** @tag DIARY MY_WORLDS GROWTH_THEME */
async function _renderWorlds() {
    const view = document.getElementById("diary-view");
    view.innerHTML = `
        ${_diaryHeader("My Worlds", "", "Completed growth themes")}
        <div class="diary-body" id="worlds-body"><p class="diary-state-msg">Loading…</p></div>`;
    try {
        const res  = await fetch("/api/growth/theme/all");
        if (!res.ok) throw new Error();
        const data = await res.json();
        const done = (data.themes || []).filter(t => t.is_completed);
        const body = document.getElementById("worlds-body");
        if (!done.length) {
            body.innerHTML = `<div class="worlds-empty">
                <div class="worlds-empty-icon">🌱</div>
                <p class="worlds-empty-text">Complete a Growth Theme to add your first world!</p>
            </div>`;
            return;
        }
        body.innerHTML = `<div class="worlds-grid">${done.map(t => `
            <div class="worlds-card">
                <img class="worlds-card-img" src="${t.img_url}" alt="${escapeHtml(t.label || t.theme)}" onerror="this.classList.add('broken')">
                <div class="worlds-card-title">${escapeHtml(t.label || t.theme)}</div>
                <div class="worlds-card-status"><span class="check-dot"></span> Completed</div>
            </div>`).join("")}</div>`;
    } catch (_) {
        const body = document.getElementById("worlds-body");
        if (body) body.innerHTML = `<p class="diary-state-msg error">Failed to load.</p>`;
    }
}

// ─── Diary Overlay (top-bar button — compat) ──────────────────

/** @tag DIARY MY_SENTENCES */
async function openDiaryOverlay() {
    const overlay = document.getElementById("diary-overlay");
    const body    = document.getElementById("diary-overlay-body");
    if (!overlay || !body) return;
    overlay.classList.remove("hidden");
    body.innerHTML = `<p class="diary-state-msg">Loading…</p>`;

    const subject  = typeof currentSubject  !== "undefined" ? currentSubject  : "English";
    const textbook = typeof currentTextbook !== "undefined" ? currentTextbook : "";
    try {
        const res  = await fetch(`/api/diary/${encodeURIComponent(subject)}/${encodeURIComponent(textbook)}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!data.lessons || !data.total_sentences) {
            body.innerHTML = `<div class="diary-empty">Start writing sentences in Step 5!</div>`;
            return;
        }
        let html = `<div class="diary-summary">You've written ${data.total_sentences} sentence${data.total_sentences !== 1 ? "s" : ""} across ${data.lessons.length} lesson${data.lessons.length !== 1 ? "s" : ""}.</div>`;
        data.lessons.forEach(lesson => {
            html += `<div class="diary-lesson-group">
                <div class="diary-lesson-title" onclick="this.classList.toggle('collapsed');this.nextElementSibling.classList.toggle('collapsed')">
                    <span class="chevron">▾</span> ${escapeHtml(lesson.lesson)} (${lesson.sentences.length})
                </div>
                <div class="diary-lesson-cards">
                    ${lesson.sentences.map(s => {
                        const safe = escapeHtml(s.sentence || "");
                        return `<div class="diary-sentence-card">
                            <span class="diary-sentence-word">${escapeHtml(s.word || "")}</span>
                            <span class="diary-sentence-text">${safe}</span>
                            <button class="diary-tts-btn" type="button" title="Listen"
                                    onclick="_diaryPlayTTS('${safe.replace(/'/g, "\\'")}')">🔊</button>
                        </div>`;
                    }).join("")}
                </div>
            </div>`;
        });
        body.innerHTML = html;
    } catch (_) {
        body.innerHTML = `<div class="diary-empty error">Failed to load sentences.</div>`;
    }
}

/** @tag DIARY */
function closeDiaryOverlay() {
    const overlay = document.getElementById("diary-overlay");
    if (overlay) overlay.classList.add("hidden");
}

/** @tag DIARY TTS */
async function _diaryPlayTTS(sentence) {
    try {
        const res = await fetch("/api/tts/example_full", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sentence }),
        });
        if (!res.ok) return;
        const blob  = await res.blob();
        const url   = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        audio.play().catch(() => {});
    } catch (_) {}
}

// Wire top-bar diary button
document.addEventListener("DOMContentLoaded", () => {
    const diaryBtn  = document.querySelector(".top-diary-btn");
    if (diaryBtn)   diaryBtn.addEventListener("click", openDiaryOverlay);
    const closeBtn  = document.getElementById("diary-close");
    if (closeBtn)   closeBtn.addEventListener("click", closeDiaryOverlay);
});
