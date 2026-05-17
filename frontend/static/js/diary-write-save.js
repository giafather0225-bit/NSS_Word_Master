/* ================================================================
   diary-write-save.js — Diary Write screen · Overflow menu + Save + AI feedback
   Section: Diary
   Dependencies: diary-write.js (_dwState, _dwToast, _dwUpdateProgress, _dwBack, _dwCleanupAndLeave, _dwIcon, _dwRefreshIcons)
                 diary-write-media.js (_dwReRenderPhotos)
   API endpoints: POST /api/diary/entries · POST /api/diary/suggest-title · POST /api/diary/feedback
   ================================================================ */

/* ── Overflow menu ──────────────────────────────────────────────── */

/** @tag DIARY */
function _dwToggleOverflow(evt) {
    if (evt) evt.stopPropagation();
    const m = document.getElementById("dw-overflow-menu");
    if (!m) return;
    const willOpen = m.classList.contains("is-hidden");
    m.classList.toggle("is-hidden", !willOpen);
    if (willOpen) {
        document.addEventListener("click", _dwCloseOverflowOnDocClick, { once: true });
    }
}

/** @tag DIARY */
function _dwCloseOverflowOnDocClick() {
    const m = document.getElementById("dw-overflow-menu");
    if (m) m.classList.add("is-hidden");
}

/** Save current Write state to localStorage so it survives a refresh. */
function _dwSaveDraft() {
    _dwCloseOverflowOnDocClick();
    try {
        const draft = {
            mode:   _dwState.mode,
            mood:   _dwState.mood,
            title:  _dwState.title,
            body:   _dwState.body,
            prompt: _dwState.prompt || "",
            style:  _dwState.style,
            photos: _dwState.photos.map(p => ({ id: p.id, name: p.name, url: p.url })),
            ts:     Date.now(),
        };
        localStorage.setItem("nss.diary.draft", JSON.stringify(draft));
        _dwToast("Draft saved", false);
    } catch (_) {
        _dwToast("Couldn't save draft.", true);
    }
}

/** Wipe title/body/photos/prompt back to defaults after a confirmation. */
function _dwClearAll() {
    _dwCloseOverflowOnDocClick();
    if (!confirm("Clear everything on this page?")) return;
    _dwState.title = "";
    _dwState.body  = "";
    _dwState.photos = [];
    const titleEl = document.getElementById("dw-title");
    const bodyEl  = document.getElementById("dw-body");
    if (titleEl) titleEl.value = "";
    if (bodyEl)  bodyEl.value  = "";
    _dwReRenderPhotos();
    _dwUpdateProgress();
}

/** Stub — full PDF export needs a server-side renderer. Browser print() is fine for now. */
function _dwExportPDF() {
    _dwCloseOverflowOnDocClick();
    _dwToast("Use Print → Save as PDF for now.", false);
    setTimeout(() => window.print(), 600);
}

/* ── Suggest title (AI) ─────────────────────────────────────────── */

/** @tag DIARY AI */
async function _dwSuggestTitle() {
    const body = (_dwState.body || "").trim();
    if (body.split(/\s+/).filter(Boolean).length < 20) return;
    const pill = document.getElementById("dw-suggest-pill");
    if (pill) {
        pill.disabled = true;
        pill.setAttribute("aria-disabled", "true");
        pill.textContent = "Thinking…";
    }
    try {
        const res = await fetch("/api/diary/suggest-title", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: body }),
        });
        if (!res.ok) throw new Error("suggest failed: " + res.status);
        const data = await res.json();
        const title = (data && data.title || "").trim();
        if (title) {
            _dwState.title = title;
            const titleEl = document.getElementById("dw-title");
            if (titleEl) titleEl.value = title;
            _dwUpdateProgress();
        }
    } catch (_) {
        _dwToast("Couldn't suggest a title.", true);
    } finally {
        if (pill) {
            pill.disabled = false;
            pill.removeAttribute("aria-disabled");
            pill.textContent = "Suggest";
        }
    }
}

/* ── Save ───────────────────────────────────────────────────────── */

/** @tag DIARY JOURNAL */
async function _dwSave() {
    const today = new Date().toISOString().slice(0, 10);
    const title = (_dwState.title || "").trim();
    const body  = (_dwState.body  || "").trim();
    if (!body) return;

    // title은 별도 필드로 전송 — "# title\n\nbody" 합치기 제거.
    // _deSplitTitleBody 파싱 의존성 제거 + title에 # 포함 시 파싱 오류 방지.
    const content = body;

    const save = document.getElementById("dw-save");
    if (save) save.disabled = true;

    // Snapshot of all decoration state — keyed by entry_date until we get the
    // backend id back (and then re-keyed by id for Entry retrieval).
    const snap = {
        mode:   _dwState.mode,
        mood:   _dwState.mood,
        title,
        prompt: _dwState.prompt || "",
        style:  _dwState.style,
        photos: _dwState.photos.map(p => ({
            id: p.id,
            name: p.name,
            url: p.url,
            thumb_url: p.thumb_url || null,
        })),
    };

    try {
        const res = await fetch("/api/diary/entries", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                content,
                entry_date: today,
                title:  title || null,
                mode:   _dwState.mode,
                mood:   _dwState.mood,
                prompt: _dwState.prompt || null,
                style:  _dwState.style,
                photos: snap.photos,
            }),
        });
        if (!res.ok) throw new Error("save failed: " + res.status);
        const data = await res.json();
        // Persist snapshot under the canonical entry id so Entry screen can
        // restore exact font/color/bg/title/mood/photos. Also keep a date-key
        // fallback for graceful display when id is missing (older entries).
        try {
            if (data && data.id != null) {
                localStorage.setItem("nss.diary.entry." + data.id, JSON.stringify(snap));
            }
            localStorage.setItem("nss.diary.last." + today, JSON.stringify(snap));
        } catch (_) {}
        _dwToast("Saved · +15 XP", false);
        if (typeof _appendIslandUpdate === "function") {
            const islandSlot = document.getElementById("dw-island-update") || document.createElement("div");
            islandSlot.id = "dw-island-update";
            const saveBtn = document.getElementById("dw-save");
            if (saveBtn && saveBtn.parentElement) saveBtn.parentElement.appendChild(islandSlot);
            _appendIslandUpdate(islandSlot, data?.island ?? null);
        }
        _dwOnSaveSuccess(today);
    } catch (err) {
        _dwToast("Couldn't save. Try again.", true);
        if (save) save.disabled = false;
    }
}

/* ── Post-save: opt-in writing tips ────────────────────────────── */

/** Called after a successful save. Shows a Done button + opt-in tips prompt. */
function _dwOnSaveSuccess(date) {
    const save = document.getElementById("dw-save");
    if (save) {
        save.disabled = false;
        save.innerHTML = _dwIcon("arrow-left", 13) + " Done";
        save.onclick = _dwFinish;
    }
    const asideTop = document.getElementById("dw-aside-top");
    if (!asideTop) {
        // No aside visible — just navigate away normally.
        setTimeout(_dwFinish, 700);
        return;
    }
    asideTop.innerHTML = `
        <div class="dw-card">
            <div class="dw-card-label">Entry saved</div>
            <p style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin:0 0 10px;">
                Would you like a few writing tips from GIA?
            </p>
            <button class="dw-prompt-item is-active" id="dw-tips-ask-btn"
                    type="button" style="width:100%;text-align:center;"
                    data-date="${escapeHtml(date)}">
                ${_dwIcon("sparkles", 12)} Get writing tips
            </button>
        </div>`;
    _dwRefreshIcons();
    const askBtn = document.getElementById("dw-tips-ask-btn");
    if (askBtn) askBtn.addEventListener("click", function() {
        _dwRequestWritingTips(this.dataset.date, this);
    });
}

/** Navigate back to the diary home. Called from Done button or fallback. */
function _dwFinish() {
    _dwCleanupAndLeave();
    if (typeof openDiarySection === "function") openDiarySection("today");
}

/** Fetch AI writing tips for the saved entry (child-triggered, opt-in only). */
async function _dwRequestWritingTips(date, btn) {
    if (btn) { btn.disabled = true; btn.textContent = "Thinking…"; }
    try {
        const res = await fetch(`/api/diary/feedback?entry_date=${encodeURIComponent(date)}`, {
            method: "POST",
        });
        if (!res.ok) throw new Error("feedback failed");
        const data = await res.json();
        _dwShowFeedbackInAside((data && data.ai_feedback) || "Great writing! Keep it up.");
    } catch (_) {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = _dwIcon("sparkles", 12) + " Try again";
            _dwRefreshIcons();
        }
    }
}

/** Render AI feedback in the aside panel after the child requests it. */
function _dwShowFeedbackInAside(text) {
    const asideTop = document.getElementById("dw-aside-top");
    if (!asideTop) return;
    asideTop.innerHTML = `
        <div class="dw-card">
            <div class="dw-card-label">${_dwIcon("sparkles", 12)} GIA says</div>
            <p style="font-size:14px;color:var(--text-primary);line-height:1.6;margin:0 0 12px;">
                ${escapeHtml(text)}
            </p>
            <button class="dw-prompt-item" type="button"
                    style="width:100%;text-align:center;" onclick="_dwFinish()">
                ${_dwIcon("arrow-left", 12)} Done
            </button>
        </div>`;
    _dwRefreshIcons();
}
