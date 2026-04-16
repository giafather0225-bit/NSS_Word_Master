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
        <div style="display:flex;flex-direction:column;gap:10px;max-width:480px;margin:0 auto;width:100%">
            ${[
                ["✏️","Daily Journal","journal"],
                ["💬","My Sentences","sentences"],
                ["📈","Growth Timeline","timeline"],
                ["📅","Calendar","calendar"],
                ["🏖️","Day Off Request","dayoff"],
                ["🌍","My Worlds","worlds"],
            ].map(([icon, label, key]) =>
                `<button class="sb-sidebar-card" style="background:var(--bg-card);border:none;border-radius:var(--radius-md);padding:14px 16px;display:flex;align-items:center;gap:12px;cursor:pointer;box-shadow:var(--shadow-card);"
                         onclick="openDiarySection('${key}')">
                    <span style="font-size:22px">${icon}</span>
                    <span style="font-size:15px;font-weight:600;color:var(--text-primary)">${label}</span>
                    <span style="margin-left:auto;color:var(--text-secondary)">›</span>
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
            }
        }
    } catch (_) {}
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
        }
    } catch (_) {
        if (btn) { btn.disabled = false; btn.textContent = "Save & Get Feedback ✨"; }
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
    view.innerHTML = `${_diaryHeader("Growth Timeline", "Your learning milestones")}<div id="timeline-body" style="width:100%"><p style="text-align:center;color:var(--text-secondary);padding:40px;">Loading…</p></div>`;
    try {
        const res = await fetch("/api/growth/timeline");
        const data = await res.json();
        const body = document.getElementById("timeline-body");
        if (!data.events || data.events.length === 0) {
            body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:40px;">No events yet. Keep learning! 🌱</p>`;
            return;
        }
        const ICONS = { lesson_pass:"🏆", streak_7:"🔥", milestone_100:"💯", theme_complete:"🌟", lesson_reset:"🔄", review_complete:"📖" };
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
        if (body) body.innerHTML = `<p style="text-align:center;color:var(--color-error);padding:40px;">Failed to load.</p>`;
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
        <div id="dayoff-status" style="margin-top:24px;width:100%;max-width:480px;margin-left:auto;margin-right:auto"></div>`;
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
            if (btn) { btn.textContent = "Sent ✓"; }
            _loadDayOffStatus();
        } else {
            const err = await res.json().catch(() => ({}));
            if (btn) { btn.disabled = false; btn.textContent = "Send Request 🏖️"; }
            alert(err.detail || "Could not submit request.");
        }
    } catch (_) {
        if (btn) { btn.disabled = false; btn.textContent = "Send Request 🏖️"; }
    }
}

/** Load and render past day-off requests. @tag DIARY DAY_OFF */
async function _loadDayOffStatus() {
    // We get all entries and filter client-side (no dedicated list endpoint yet)
    const el = document.getElementById("dayoff-status");
    if (!el) return;
    try {
        const res = await fetch("/api/diary/entries"); // reuse entries endpoint for now
        // Actually use day-off from timeline
    } catch (_) {}
}

// ─── My Sentences ─────────────────────────────────────────────

/**
 * Render the My Sentences list (Step 5 practice sentences).
 * @tag DIARY MY_SENTENCES
 */
async function _renderSentences() {
    const view = document.getElementById("diary-view");
    view.innerHTML = `${_diaryHeader("My Sentences", "Sentences I created in Step 5")}<div id="sentences-body" style="width:100%"><p style="text-align:center;color:var(--text-secondary);padding:40px;">Loading…</p></div>`;
    try {
        const res = await fetch("/api/practice/sentences/English//");
        const data = await res.json();
        const body = document.getElementById("sentences-body");
        if (!data.sentences || data.sentences.length === 0) {
            body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:40px;">No sentences yet. Complete Step 5 in a lesson!</p>`;
            return;
        }
        body.innerHTML = `<div class="sentences-list">${data.sentences.map(s =>
            `<div class="sentence-card">
                <div class="sentence-word">${escapeHtml(s.lesson || "")}</div>
                <div class="sentence-text">${escapeHtml(s.sentence)}</div>
            </div>`
        ).join("")}</div>`;
    } catch (_) {
        const body = document.getElementById("sentences-body");
        if (body) body.innerHTML = `<p style="text-align:center;color:var(--color-error);padding:40px;">Failed to load.</p>`;
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
    body.innerHTML = '<p style="text-align:center;color:var(--text-secondary);padding:40px;">Loading...</p>';

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
        body.innerHTML = '<div class="diary-empty" style="color:var(--color-error)">Failed to load sentences.</div>';
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
    view.innerHTML = `${_diaryHeader("My Worlds", "Completed growth themes")}<div id="worlds-body" style="width:100%"><p style="text-align:center;color:var(--text-secondary);padding:40px;">Loading…</p></div>`;
    try {
        const res  = await fetch("/api/growth/theme/all");
        const data = await res.json();
        const done = (data.themes || []).filter(t => t.is_completed);
        const body = document.getElementById("worlds-body");
        if (!done.length) {
            body.innerHTML = `<div style="text-align:center;padding:40px"><div style="font-size:48px">🌍</div><p style="color:var(--text-secondary);margin-top:8px">Complete a Growth Theme to add your first world!</p></div>`;
            return;
        }
        const cards = done.map(t => `
            <div style="background:var(--bg-card);border-radius:var(--radius-lg);padding:16px;text-align:center;box-shadow:var(--shadow-card)">
                <img src="${t.img_url}" style="width:100px;height:100px;border-radius:var(--radius-md)" onerror="this.style.opacity='0.3'">
                <div style="font-size:14px;font-weight:700;color:var(--text-primary);margin-top:8px">${escapeHtml(t.label||t.theme)}</div>
                <div style="font-size:11px;color:var(--color-success)">✅ Completed</div>
            </div>`).join("");
        body.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;max-width:480px;margin:0 auto">${cards}</div>`;
    } catch (_) {
        const body = document.getElementById("worlds-body");
        if (body) body.innerHTML = `<p style="color:var(--color-error);padding:20px;text-align:center">Failed to load.</p>`;
    }
}
