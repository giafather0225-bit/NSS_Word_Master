/* ================================================================
   diary.js — GIA's Diary section: journal, timeline, day-off, sentences
   Section: Diary
   Dependencies: core.js
   API endpoints: /api/diary/entries, /api/growth/timeline,
                  /api/day-off/request, /api/practice/sentences
   ================================================================ */

// ─── Navigation ───────────────────────────────────────────────

/**
 * Open a diary sub-section and render its content.
 * @tag DIARY NAVIGATION
 * @param {'journal'|'timeline'|'dayoff'|'sentences'|'worlds'} section
 */
function openDiarySection(section) {
    const view = document.getElementById("diary-view");
    if (!view) return;
    view.style.display = "flex";
    switch (section) {
        case "journal":   _renderJournal();   break;
        case "freewriting": _renderFreeWriting(); break;
        case "timeline":  _renderTimeline();  break;
        case "dayoff":    _renderDayOff();    break;
        case "sentences": _renderSentences(); break;
        case "calendar":  renderCalendar();   break;
        case "worlds":    _renderWorlds();    break;
        default:          _renderJournal();
    }
}

/** Shared diary header HTML with back button to diary home. @tag DIARY */
function _diaryHeader(title, sub) {
    return `<div class="diary-header">
        <button class="back-btn" onclick="_renderDiaryHome()">←</button>
        <div class="diary-header-text">
            <span class="diary-header-title">${escapeHtml(title)}</span>
            ${sub ? `<span class="diary-header-sub">${escapeHtml(sub)}</span>` : ""}
        </div>
    </div>`;
}

/** Render the diary section home (section list). @tag DIARY */
function _renderDiaryHome() {
    const view = document.getElementById("diary-view");
    if (!view) return;
    view.innerHTML = `
        <div class="diary-header">
            <button class="back-btn" onclick="switchView('home')">←</button>
            <div class="diary-header-text">
                <span class="diary-header-title">📖 GIA's Diary</span>
            </div>
        </div>
        <div class="diary-home-list">
            ${[
                ["✏️","Daily Journal","journal"],
                ["📝","Free Writing","freewriting"],
                ["💬","My Sentences","sentences"],
                ["📈","Growth Timeline","timeline"],
                ["📅","Calendar","calendar"],
                ["🏖️","Day Off Request","dayoff"],
                ["🌍","My Worlds","worlds"],
            ].map(([icon, label, key]) =>
                `<button type="button" class="diary-home-card" onclick="openDiarySection('${key}')">
                    <span class="diary-home-card-icon">${icon}</span>
                    <span class="diary-home-card-label">${label}</span>
                    <span class="diary-home-card-chevron">›</span>
                </button>`
            ).join("")}
        </div>`;
}

// ─── Daily Journal ────────────────────────────────────────────

/**
 * Render the Daily Journal write area (today's date).
 * @tag DIARY JOURNAL
 */
async function _renderJournal() {
    const view = document.getElementById("diary-view");
    const today = new Date().toISOString().slice(0, 10);
    const label = new Date().toLocaleDateString("en-US", { weekday:"long", month:"long", day:"numeric", year:"numeric" });
    view.innerHTML = `
        ${_diaryHeader("Daily Journal", label)}
        <div class="journal-area">
            <div class="journal-date-label">${label}</div>
            <textarea id="journal-text" class="journal-textarea"
                      placeholder="Write about your day in English…"
                      oninput="_journalCharCount(this)"></textarea>
            <div class="journal-char-count" id="journal-cc">0 characters</div>
            <div class="journal-photo-row">
                <input type="file" id="journal-photo-input" accept="image/*"
                       data-date="${today}" onchange="_uploadJournalPhoto(this)" hidden />
                <button type="button" class="journal-photo-btn"
                        onclick="document.getElementById('journal-photo-input').click()">📷 Add Photo</button>
                <span class="journal-photo-status" id="journal-photo-status"></span>
            </div>
            <div id="journal-photo-preview" class="journal-photo-preview"></div>
            <button class="journal-submit-btn" onclick="_submitJournal('${today}')">Save & Get Feedback ✨</button>
            <div id="journal-feedback"></div>
        </div>`;

    // Load existing entry for today
    try {
        const res = await fetch(`/api/diary/entries?date=${today}`);
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

/** Render the journal photo preview with a remove button. @tag DIARY JOURNAL */
function _showJournalPhoto(filename) {
    const el = document.getElementById("journal-photo-preview");
    if (!el) return;
    const safe = encodeURIComponent(filename);
    el.innerHTML = `
        <img class="journal-photo-img" src="/api/diary/photo/${safe}" alt="Journal photo" />
        <button type="button" class="journal-photo-remove" onclick="_removeJournalPhoto('${filename}')">Remove photo</button>`;
}

/** Upload a photo for today's journal entry. @tag DIARY JOURNAL */
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
    } finally {
        input.value = "";
    }
}

/** Delete the journal photo from server and clear preview. @tag DIARY JOURNAL */
async function _removeJournalPhoto(filename) {
    try {
        await fetch(`/api/diary/photo/${encodeURIComponent(filename)}`, { method: "DELETE" });
    } catch (_) {}
    const el = document.getElementById("journal-photo-preview");
    if (el) el.innerHTML = "";
}

/** Update character count display. @tag DIARY JOURNAL */
function _journalCharCount(ta) {
    const el = document.getElementById("journal-cc");
    if (el) el.textContent = `${ta.value.length} characters`;
}

/**
 * POST journal entry and show AI feedback.
 * @tag DIARY JOURNAL AI
 */
async function _submitJournal(date) {
    const ta = document.getElementById("journal-text");
    if (!ta || !ta.value.trim()) return;
    const btn = document.querySelector(".journal-submit-btn");
    const resetBtn = () => {
        if (btn) { btn.disabled = false; btn.textContent = "Save & Get Feedback ✨"; }
    };
    if (btn) { btn.disabled = true; btn.textContent = "Saving…"; }
    // Previously, any non-OK response (422 on Str5000 overflow, 500, 400)
    // left the button frozen on "Saving…" forever — the success and catch
    // branches both reset it, but the "not ok, didn't throw" path didn't.
    // Route every exit through resetBtn() so the UI never gets stuck.
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
        // Non-OK: toast.js global 422 interceptor handles validation errors;
        // for other statuses surface the detail so the parent can debug.
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

/** Render the AI feedback box. @tag DIARY JOURNAL */
function _showFeedback(text) {
    const el = document.getElementById("journal-feedback");
    if (el) el.innerHTML = `<div class="ai-feedback-box">
        <div class="ai-feedback-label">✨ GIA says:</div>
        <div class="ai-feedback-text">${escapeHtml(text)}</div>
    </div>`;
}

// ─── Growth Timeline ──────────────────────────────────────────

/**
 * Render the Growth Timeline (reverse-chronological GrowthEvents).
 * @tag DIARY GROWTH_TIMELINE
 */
async function _renderTimeline() {
    const view = document.getElementById("diary-view");
    view.innerHTML = `${_diaryHeader("Growth Timeline", "Your learning milestones")}<div id="timeline-body" class="diary-body"><p class="diary-state-msg">Loading…</p></div>`;
    try {
        const res = await fetch("/api/growth/timeline");
        if (!res.ok) throw new Error(`growth/timeline ${res.status}`);
        const data = await res.json();
        const body = document.getElementById("timeline-body");
        if (!data.events || data.events.length === 0) {
            body.innerHTML = `<p class="diary-state-msg">No events yet. Keep learning! 🌱</p>`;
            return;
        }
        const ICONS = { lesson_pass:"✦", streak_7:"✦", milestone_100:"✓", theme_complete:"✦", lesson_reset:"↺", review_complete:"📖" };
        body.innerHTML = `<div class="timeline-list">${data.events.map(e =>
            `<div class="timeline-item">
                <span class="timeline-icon">${ICONS[e.event_type] || "📌"}</span>
                <div class="timeline-info">
                    <div class="timeline-title">${escapeHtml(e.title)}</div>
                    <div class="timeline-date">${e.event_date || ""}</div>
                </div>
            </div>`
        ).join("")}</div>`;
    } catch (_) {
        const body = document.getElementById("timeline-body");
        if (body) body.innerHTML = `<p class="diary-state-msg error">Failed to load.</p>`;
    }
}

// ─── Day Off ──────────────────────────────────────────────────

/**
 * Render the Day Off request form and past requests.
 * @tag DIARY DAY_OFF
 */
async function _renderDayOff() {
    const view = document.getElementById("diary-view");
    const today = new Date().toISOString().slice(0, 10);
    view.innerHTML = `
        ${_diaryHeader("Day Off Request", "Ask a parent for a study break")}
        <form class="dayoff-form" onsubmit="_submitDayOff(event)">
            <div class="dayoff-field">
                <label class="dayoff-label">Date</label>
                <input class="dayoff-input" type="date" id="dayoff-date" value="${today}" required />
            </div>
            <div class="dayoff-field">
                <label class="dayoff-label">Reason</label>
                <textarea class="dayoff-textarea" id="dayoff-reason" placeholder="Tell your parent why you need a day off…" required></textarea>
            </div>
            <button type="submit" class="journal-submit-btn" id="dayoff-btn">Send Request 🏖️</button>
        </form>
        <div id="dayoff-status" class="dayoff-status-wrap"></div>`;
    _loadDayOffStatus();
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
            if (btn) {
                btn.textContent = data.email_queued ? "Sent ✓ (parent emailed)" : "Sent ✓";
            }
            _loadDayOffStatus();
        } else {
            const err = await res.json().catch(() => ({}));
            if (btn) { btn.disabled = false; btn.textContent = "Send Request 🏖️"; }
            toast(err.detail || "Could not submit request.", "error");
        }
    } catch (_) {
        if (btn) { btn.disabled = false; btn.textContent = "Send Request 🏖️"; }
        toast("Network error — please try again.", "error");
    }
}

/** Load and render past day-off requests. @tag DIARY DAY_OFF */
async function _loadDayOffStatus() {
    const el = document.getElementById("dayoff-status");
    if (!el) return;
    try {
        const res = await fetch("/api/day-off/requests");
        if (!res.ok) return;
        const data = await res.json();
        const rows = data.requests || [];
        if (rows.length === 0) {
            el.innerHTML = `<p class="diary-state-msg compact">No previous requests.</p>`;
            return;
        }
        const STATUS_LABEL = { pending: "Pending", approved: "Approved", denied: "Denied" };
        el.innerHTML = `<div class="dayoff-status-list">${rows.map(r => {
            const status = (r.status || "pending").toLowerCase();
            const label  = STATUS_LABEL[status] || status;
            return `<div class="dayoff-status-row">
                <div class="dayoff-status-info">
                    <div class="dayoff-status-date">${escapeHtml(r.request_date)}</div>
                    <div class="dayoff-status-reason">${escapeHtml(r.reason || "")}</div>
                </div>
                <span class="status-badge ${status}">${label}</span>
            </div>`;
        }).join("")}</div>`;
    } catch (_) {}
}

// ─── My Sentences ─────────────────────────────────────────────

/**
 * Days elapsed since an ISO 8601 timestamp. Returns null if unparseable.
 * @tag DIARY MY_SENTENCES
 */
function _sentenceAgeDays(iso, now) {
    if (!iso) return null;
    const t = Date.parse(iso);
    if (isNaN(t)) return null;
    return Math.floor((now - t) / 86400000);
}


/**
 * Render the My Sentences list (Step 5 practice sentences).
 * @tag DIARY MY_SENTENCES
 */
async function _renderSentences() {
    const view = document.getElementById("diary-view");
    view.innerHTML = `${_diaryHeader("My Sentences", "Sentences I created in Step 5")}<div id="sentences-body" class="diary-body"><p class="diary-state-msg">Loading…</p></div>`;

    const subject  = (typeof currentSubject  !== "undefined" && currentSubject)  ? currentSubject  : "English";
    const textbook = (typeof currentTextbook !== "undefined" && currentTextbook) ? currentTextbook : "";

    try {
        const res = await fetch(`/api/diary/${encodeURIComponent(subject)}/${encodeURIComponent(textbook)}`);
        if (!res.ok) throw new Error("fetch failed");
        const data = await res.json();
        const body = document.getElementById("sentences-body");
        const lessons = data.lessons || [];
        if (lessons.length === 0 || data.total_sentences === 0) {
            body.innerHTML = `<p class="diary-state-msg">No sentences yet. Complete Step 5 in a lesson!</p>`;
            return;
        }
        const REWRITE_AFTER_DAYS = 14;
        const now = Date.now();
        const cards = lessons.flatMap(lesson =>
            lesson.sentences.map(s => {
                const ageDays = _sentenceAgeDays(s.created_at, now);
                const stale   = ageDays !== null && ageDays >= REWRITE_AFTER_DAYS;
                const badge   = stale
                    ? `<span class="sentence-rewrite-badge" title="Written ${ageDays} days ago">Rewrite ✏️</span>`
                    : "";
                return `<div class="sentence-card${stale ? " stale" : ""}">
                    <div class="sentence-card-head">
                        <div class="sentence-word">${escapeHtml(s.word || lesson.lesson || "")}</div>
                        ${badge}
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

// ─── Diary Overlay (top-bar 📖 button) ───────────────────────

/**
 * Open the diary overlay and load all practice sentences.
 * @tag DIARY MY_SENTENCES
 */
async function openDiaryOverlay() {
    const overlay = document.getElementById('diary-overlay');
    const body = document.getElementById('diary-overlay-body');
    if (!overlay || !body) return;
    overlay.classList.remove('hidden');
    body.innerHTML = '<p class="diary-state-msg">Loading…</p>';

    const subject = typeof currentSubject !== 'undefined' ? currentSubject : 'English';
    const textbook = typeof currentTextbook !== 'undefined' ? currentTextbook : '';

    try {
        const res = await fetch(`/api/diary/${encodeURIComponent(subject)}/${encodeURIComponent(textbook)}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();

        if (!data.lessons || data.lessons.length === 0 || data.total_sentences === 0) {
            body.innerHTML = '<div class="diary-empty">Start writing sentences in Step 5 to fill your diary! ✨</div>';
            return;
        }

        let html = `<div class="diary-summary">You've written ${data.total_sentences} sentence${data.total_sentences !== 1 ? 's' : ''} across ${data.lessons.length} lesson${data.lessons.length !== 1 ? 's' : ''}!</div>`;

        data.lessons.forEach((lesson, idx) => {
            html += `<div class="diary-lesson-group">
                <div class="diary-lesson-title" onclick="this.classList.toggle('collapsed');this.nextElementSibling.classList.toggle('collapsed')">
                    <span class="chevron">▾</span> ${escapeHtml(lesson.lesson)} (${lesson.sentences.length})
                </div>
                <div class="diary-lesson-cards">`;
            lesson.sentences.forEach(s => {
                const safeWord = escapeHtml(s.word || '');
                const safeSentence = escapeHtml(s.sentence || '');
                html += `<div class="diary-sentence-card">
                    <span class="diary-sentence-word">${safeWord}</span>
                    <span class="diary-sentence-text">${safeSentence}</span>
                    <button class="diary-tts-btn" type="button" title="Listen"
                            onclick="_diaryPlayTTS('${safeSentence.replace(/'/g, "\\'")}')">🔊</button>
                </div>`;
            });
            html += '</div></div>';
        });

        body.innerHTML = html;
    } catch (e) {
        body.innerHTML = '<div class="diary-empty error">Failed to load sentences.</div>';
    }
}

/**
 * Close the diary overlay.
 * @tag DIARY
 */
function closeDiaryOverlay() {
    const overlay = document.getElementById('diary-overlay');
    if (overlay) overlay.classList.add('hidden');
}

/**
 * Play a sentence via TTS from the diary overlay.
 * @tag DIARY TTS
 */
async function _diaryPlayTTS(sentence) {
    try {
        const res = await fetch('/api/tts/example_full', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sentence }),
        });
        if (!res.ok) return;
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        audio.play().catch(() => {});
    } catch (_) {}
}

// Wire top-bar 📖 button and close button on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    const diaryBtn = document.querySelector('.top-diary-btn');
    if (diaryBtn) diaryBtn.addEventListener('click', openDiaryOverlay);
    const closeBtn = document.getElementById('diary-close');
    if (closeBtn) closeBtn.addEventListener('click', closeDiaryOverlay);
});

// ─── My Worlds (stub) ─────────────────────────────────────────

/**
 * Render the My Worlds completed theme collection.
 * @tag DIARY MY_WORLDS GROWTH_THEME
 */
async function _renderWorlds() {
    const view = document.getElementById("diary-view");
    view.innerHTML = `${_diaryHeader("My Worlds", "Completed growth themes")}<div id="worlds-body" class="diary-body"><p class="diary-state-msg">Loading…</p></div>`;
    try {
        const res  = await fetch("/api/growth/theme/all");
        if (!res.ok) throw new Error(`growth/theme/all ${res.status}`);
        const data = await res.json();
        const done = (data.themes || []).filter(t => t.is_completed);
        const body = document.getElementById("worlds-body");
        if (!done.length) {
            body.innerHTML = `<div class="worlds-empty">
                <div class="worlds-empty-icon">🌍</div>
                <p class="worlds-empty-text">Complete a Growth Theme to add your first world!</p>
            </div>`;
            return;
        }
        const cards = done.map(t => `
            <div class="worlds-card">
                <img class="worlds-card-img" src="${t.img_url}" alt="${escapeHtml(t.label || t.theme)}" onerror="this.classList.add('broken')">
                <div class="worlds-card-title">${escapeHtml(t.label || t.theme)}</div>
                <div class="worlds-card-status"><span class="check-dot"></span> Completed</div>
            </div>`).join("");
        body.innerHTML = `<div class="worlds-grid">${cards}</div>`;
    } catch (_) {
        const body = document.getElementById("worlds-body");
        if (body) body.innerHTML = `<p class="diary-state-msg error">Failed to load.</p>`;
    }
}
