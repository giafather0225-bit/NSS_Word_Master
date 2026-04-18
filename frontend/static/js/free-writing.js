/* ================================================================
   free-writing.js — GIA's Diary: Free Writing section
   Section: Diary
   Dependencies: diary.js (_diaryHeader), core.js (escapeHtml)
   API endpoints: /api/free-writing/entries
   ================================================================ */

/**
 * Render the Free Writing list view with an inline composer.
 * @tag DIARY JOURNAL
 */
async function _renderFreeWriting() {
    const view = document.getElementById("diary-view");
    if (!view) return;
    view.innerHTML = `
        ${_diaryHeader("Free Writing", "Write freely about anything")}
        <div class="freewrite-area">
            <div class="freewrite-composer">
                <input id="fw-title" class="freewrite-title-input" type="text"
                       maxlength="120" placeholder="Title (e.g. My Adventure)" />
                <textarea id="fw-content" class="freewrite-textarea"
                          placeholder="Write your story, poem, or anything you like…"></textarea>
                <button class="journal-submit-btn" id="fw-submit-btn"
                        onclick="_submitFreeWriting()">Save & Get Feedback ✨</button>
                <p id="fw-msg" class="diary-state-msg compact"></p>
            </div>
            <div class="freewrite-section-title">My Entries</div>
            <div id="fw-list" class="freewrite-list">
                <p class="diary-state-msg">Loading…</p>
            </div>
        </div>`;
    _loadFreeWritingList();
}

/** Fetch and render the list of free-writing entries. @tag DIARY JOURNAL */
async function _loadFreeWritingList() {
    const list = document.getElementById("fw-list");
    if (!list) return;
    try {
        const res  = await fetch("/api/free-writing/entries");
        const data = await res.json();
        const rows = data.entries || [];
        if (rows.length === 0) {
            list.innerHTML = `<p class="diary-state-msg">No entries yet. Write your first one above! ✨</p>`;
            return;
        }
        list.innerHTML = rows.map(e => {
            const date = (e.created_at || "").slice(0, 10);
            return `<div class="freewrite-card">
                <div class="freewrite-card-head">
                    <div class="freewrite-card-title">${escapeHtml(e.title || "(untitled)")}</div>
                    <span class="freewrite-card-date">${escapeHtml(date)}</span>
                </div>
                <div class="freewrite-card-body">${escapeHtml(e.content || "")}</div>
                ${e.ai_feedback
                    ? `<div class="ai-feedback-box">
                            <div class="ai-feedback-label">✨ GIA says:</div>
                            <div class="ai-feedback-text">${escapeHtml(e.ai_feedback)}</div>
                       </div>`
                    : ""}
                <button class="freewrite-delete-btn"
                        onclick="_deleteFreeWriting(${e.id})">Delete</button>
            </div>`;
        }).join("");
    } catch (_) {
        list.innerHTML = `<p class="diary-state-msg error">Failed to load.</p>`;
    }
}

/** POST a new free-writing entry, then refresh the list. @tag DIARY JOURNAL AI */
async function _submitFreeWriting() {
    const titleEl   = document.getElementById("fw-title");
    const contentEl = document.getElementById("fw-content");
    const btn       = document.getElementById("fw-submit-btn");
    const msg       = document.getElementById("fw-msg");
    const title   = (titleEl?.value   || "").trim();
    const content = (contentEl?.value || "").trim();
    if (msg) { msg.textContent = ""; msg.classList.remove("error"); }
    if (!title || !content) {
        if (msg) { msg.textContent = "Title and content are required."; msg.classList.add("error"); }
        return;
    }
    if (btn) { btn.disabled = true; btn.textContent = "Saving…"; }
    try {
        const res = await fetch("/api/free-writing/entries", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, content }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            if (msg) { msg.textContent = err.detail || "Failed to save."; msg.classList.add("error"); }
            if (btn) { btn.disabled = false; btn.textContent = "Save & Get Feedback ✨"; }
            return;
        }
        if (titleEl)   titleEl.value   = "";
        if (contentEl) contentEl.value = "";
        if (btn) { btn.disabled = false; btn.textContent = "Save & Get Feedback ✨"; }
        _loadFreeWritingList();
    } catch (_) {
        if (msg) { msg.textContent = "Network error."; msg.classList.add("error"); }
        if (btn) { btn.disabled = false; btn.textContent = "Save & Get Feedback ✨"; }
    }
}

/** Delete a free-writing entry by id. @tag DIARY JOURNAL */
async function _deleteFreeWriting(entryId) {
    if (!confirm("Delete this entry? This cannot be undone.")) return;
    try {
        const res = await fetch(`/api/free-writing/entries/${entryId}`, { method: "DELETE" });
        if (res.ok) _loadFreeWritingList();
    } catch (_) {}
}
