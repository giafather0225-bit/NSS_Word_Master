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

    // All Diary screens are hub-level now (no sidebar). Sub-sections render
    // inside #diary-view and get class markers so per-screen scroll rules fire.
    document.body.classList.add("dh-fullscreen");

    // Reset every per-screen marker so we don't double-apply CSS.
    if (section !== "journal" && section !== "freewriting") {
        view.classList.remove("dw-active");
    }
    if (section !== "entry") {
        view.classList.remove("de-active");
    }
    if (section !== "calendar") {
        view.classList.remove("dc-active");
    }
    if (!["sentences", "worlds", "timeline", "dayoff"].includes(section)) {
        view.classList.remove("ds-active");
    }

    switch (section) {
        case "today":       _renderDiaryHome();    break;
        case "journal":     (typeof _renderDiaryWrite === "function") ? _renderDiaryWrite("journal") : _renderJournal();      break;
        case "freewriting": _renderDiaryWrite("free"); break;
        case "timeline":    _renderTimeline();     break;
        case "dayoff":      _renderDayOff();       break;
        case "sentences":   _renderSentences();    break;
        case "calendar":    (typeof _renderDiaryCalendar === "function") ? _renderDiaryCalendar() : renderCalendar(); break;
        case "worlds":      _renderWorlds();       break;
        default:            _renderDiaryHome();
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
        <button type="button" class="journal-photo-remove"
                data-filename="${escapeHtml(filename)}">Remove photo</button>`;
    // data-filename 방식으로 XSS 방지 — onclick 인라인 핸들러 제거
    el.querySelector(".journal-photo-remove").addEventListener("click", function() {
        _removeJournalPhoto(this.dataset.filename);
    });
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

// ─── Free Writing ───────────────────────────────────────────
// Removed: legacy _renderFreeWriting / _loadFreeWrites / _submitFreeWrite / _deleteFreeWrite
// Free Write UI is fully handled by diary-write.js (_renderDiaryWrite('free')).
// Entries are saved via POST /api/diary/entries (mode='free').


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
                                    onclick="_diaryPlayTTS('${safe.replace(/'/g, "\\'")}')"><i data-lucide="volume-2" style="width:14px;height:14px;stroke-width:1.5"></i></button>
                        </div>`;
                    }).join("")}
                </div>
            </div>`;
        });
        body.innerHTML = html;
        if (typeof lucide !== "undefined") lucide.createIcons();
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
