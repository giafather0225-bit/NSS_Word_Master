/* ================================================================
   diary-entry.js — GIA's Diary · Entry (read-only detail)
   Section: Diary
   Dependencies: diary.js (escapeHtml, openDiarySection, _DH_MOODS),
                 diary-write.js (resolvers _dwResolve*)
   API endpoints: GET /api/diary/entries (list), DELETE /api/diary/entries/{id}
   Spec: handoff/02b-diary-spec.md (Screen 3)
   ================================================================ */

const _deState = {
    entryId: null,
    entry: null,        // backend row { id, entry_date, content, ... }
    snap: null,         // localStorage snapshot { mode, mood, title, prompt, style, photos, ... }
    neighbors: { prev: null, next: null },
    deleteOpen: false,
};

/** Build a snapshot for an entry. Prefer backend metadata (after migration 013);
 *  fall back to localStorage so older entries stay viewable. */
function _deLoadSnap(entry) {
    if (!entry) return null;
    // Backend-driven snapshot — populated after migration 013.
    const fromBackend = {};
    let any = false;
    if (entry.title  != null) { fromBackend.title  = entry.title;  any = true; }
    if (entry.mode   != null) { fromBackend.mode   = entry.mode;   any = true; }
    if (entry.mood   != null) { fromBackend.mood   = entry.mood;   any = true; }
    if (entry.prompt != null) { fromBackend.prompt = entry.prompt; any = true; }
    if (entry.style  != null) { fromBackend.style  = entry.style;  any = true; }
    if (entry.photos != null) { fromBackend.photos = entry.photos; any = true; }

    // localStorage fallback (legacy entries / cached)
    let local = null;
    try {
        const byId = localStorage.getItem("nss.diary.entry." + entry.id);
        if (byId) local = JSON.parse(byId);
        else {
            const byDate = localStorage.getItem("nss.diary.last." + entry.entry_date);
            if (byDate) local = JSON.parse(byDate);
        }
    } catch (_) {}

    // Merge: backend overrides localStorage where present.
    if (!any) return local;
    return Object.assign({}, local || {}, fromBackend);
}

/** Strip leading "# Title\n\n" from content if present (Save merges title into content). */
function _deSplitTitleBody(content, snapTitle) {
    const c = String(content || "");
    const m = c.match(/^#\s+([^\n]+)\n\n([\s\S]*)$/);
    if (m) return { title: snapTitle || m[1].trim(), body: m[2] };
    return { title: snapTitle || "", body: c };
}

/* ── Entry point ───────────────────────────────────────────────── */

/**
 * Render the Diary Entry screen for a given entry id.
 * @tag DIARY ENTRY
 * @param {number|string} entryId
 */
async function _renderDiaryEntry(entryId) {
    const view = document.getElementById("diary-view");
    if (!view) return;

    document.body.classList.add("dh-fullscreen");
    view.classList.add("de-active");
    view.style.display = "flex";
    view.innerHTML = `<div class="de-root"><p class="diary-state-msg" style="padding:60px;">Loading…</p></div>`;

    _deState.entryId = entryId;

    // Fetch all entries once and pick the target + neighbors. Cheap for the
    // expected dataset size (one user, hundreds of entries max).
    let all = [];
    try {
        const res = await fetch("/api/diary/entries?limit=500");
        if (res.ok) {
            const d = await res.json();
            all = Array.isArray(d.entries) ? d.entries : [];
        }
    } catch (_) {}

    all.sort((a, b) => (a.entry_date || "").localeCompare(b.entry_date || ""));
    const idx = all.findIndex(e => String(e.id) === String(entryId));
    if (idx < 0) {
        view.innerHTML = `
            <div class="de-root">
                <p class="diary-state-msg" style="padding:60px;">Entry not found.</p>
                <div style="text-align:center;">
                    <button class="dw-save" type="button" onclick="openDiarySection('today')">Back to Diary</button>
                </div>
            </div>`;
        return;
    }

    _deState.entry = all[idx];
    _deState.neighbors = {
        prev: idx > 0 ? all[idx - 1] : null,
        next: idx < all.length - 1 ? all[idx + 1] : null,
    };
    _deState.snap = _deLoadSnap(_deState.entry) || {};
    _deState.deleteOpen = false;

    view.innerHTML = `
        <div class="de-root" id="de-root">
            ${_deChromeHTML()}
            <div class="de-body">
                ${_dePaperHTML()}
                ${_deNavHTML()}
            </div>
        </div>`;

    _deApplyStyle();
    _deRefreshIcons();
    document.addEventListener("keydown", _deKeyHandler);
}

function _deRefreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
        window.lucide.createIcons();
    }
}

function _deIcon(name, size) {
    const px = size || 14;
    return `<i data-lucide="${name}" width="${px}" height="${px}"></i>`;
}

/* ── Chrome ─────────────────────────────────────────────────────── */

function _deChromeHTML() {
    const { entry, snap } = _deState;
    const dateLong = _deFmtDateLong(entry.entry_date);
    const { title } = _deSplitTitleBody(entry.content, snap.title);
    const heading = title || "Untitled";
    return `
        <header class="de-chrome">
            <div>
                <button class="de-back" type="button" onclick="_deBack()">${_deIcon("chevron-left", 14)} Diary</button>
                <span class="de-eyebrow">Diary · Entry</span>
                <div class="de-title">${escapeHtml(heading)}</div>
                <div class="de-sub">${escapeHtml(dateLong)}</div>
            </div>
            <div class="de-chrome-right">
                <button class="de-delete" type="button" onclick="_deToggleDelete()">
                    ${_deIcon("trash-2", 13)} Delete
                </button>
                <div class="de-delete-pop is-hidden" id="de-delete-pop" role="alertdialog" aria-label="Delete this page?">
                    <div class="de-delete-pop-title">Delete this page?</div>
                    <div class="de-delete-pop-msg">This page will be gone forever. You can't get it back.</div>
                    <div class="de-delete-pop-actions">
                        <button class="de-keep"    type="button" onclick="_deToggleDelete()">Keep it</button>
                        <button class="de-confirm" type="button" onclick="_deDelete()">Delete</button>
                    </div>
                </div>
            </div>
        </header>`;
}

/* ── Paper ──────────────────────────────────────────────────────── */

function _dePaperHTML() {
    const { entry, snap } = _deState;
    const { title, body } = _deSplitTitleBody(entry.content, snap.title);
    const mode = snap.mode || "journal";
    const moodId = snap.mood || "happy";
    const moodMeta = (window._DH_MOODS && window._DH_MOODS[moodId]) || { dot: "#E09AAE" };
    const photos = Array.isArray(snap.photos) ? snap.photos.slice(0, 3) : [];
    const hasPhotos = mode === "journal" && photos.length > 0;

    const photosHTML = hasPhotos ? `
        <div class="de-photos">
            ${photos.map(p => {
                // 72×72 read-only strip — same thumb-first rule as Write.
                const u = p.thumb_url || p.url;
                return u
                    ? `<div class="de-photo" style="background-image:url('${u}');"></div>`
                    : `<div class="de-photo"></div>`;
            }).join("")}
            <span class="de-photos-count">${photos.length} photo${photos.length === 1 ? "" : "s"}</span>
        </div>` : "";

    const promptHTML = (mode === "journal" && snap.prompt)
        ? `<div class="de-prompt">${escapeHtml(snap.prompt)}</div>`
        : "";

    const titleHTML = title
        ? `<div class="de-title-line">${escapeHtml(title)}</div>`
        : "";

    const wordsHTML = `
        <div class="de-foot">
            <div class="de-words-label">Words</div>
            <div class="de-words-list" id="de-words"></div>
            <button class="de-share" type="button" onclick="_deShare()">${_deIcon("heart", 12)} Share with parent</button>
        </div>`;

    return `
        <div class="de-paper" id="de-paper">
            ${photosHTML}
            <div class="de-meta">
                <div class="de-mood-square" style="background:${moodMeta.dot};"></div>
                <div class="de-meta-text">
                    <div class="de-mode-label">${mode === "free" ? "Free write" : "Journal"}</div>
                    <div class="de-mood-word">${escapeHtml(moodId)}</div>
                </div>
                <span class="de-xp-pill">+15 XP</span>
            </div>
            ${promptHTML}
            ${titleHTML}
            <div class="de-body-text" id="de-body-text">${escapeHtml(body)}</div>
            ${wordsHTML}
        </div>`;
}

/* ── Page nav ───────────────────────────────────────────────────── */

function _deNavHTML() {
    const { prev, next } = _deState.neighbors;
    return `
        <div class="de-nav">
            ${_deNavCardHTML(prev, "left")}
            ${_deNavCardHTML(next, "right")}
        </div>`;
}

function _deNavCardHTML(entry, side) {
    if (!entry) {
        const label = side === "left" ? "No earlier pages" : "No later pages";
        return `<div class="de-nav-card is-disabled ${side === "right" ? "right" : ""}" aria-disabled="true">
            <div class="de-nav-eyebrow">${side === "left" ? "← Earlier" : "Later →"}</div>
            <div class="de-nav-title">${label}</div>
        </div>`;
    }
    const snap = _deLoadSnap(entry) || {};
    const { title } = _deSplitTitleBody(entry.content, snap.title);
    const heading = title || "Untitled";
    const dateShort = _deFmtDateShort(entry.entry_date);
    const eyebrow = side === "left" ? `← Earlier · ${dateShort}` : `Later · ${dateShort} →`;
    return `
        <button class="de-nav-card ${side === "right" ? "right" : ""}" type="button"
                onclick="_renderDiaryEntry(${entry.id})">
            <div class="de-nav-eyebrow">${escapeHtml(eyebrow)}</div>
            <div class="de-nav-title">${escapeHtml(heading)}</div>
        </button>`;
}

/* ── Style restoration ──────────────────────────────────────────── */

function _deApplyStyle() {
    const snap = _deState.snap || {};
    const style = snap.style || {};
    const paper = document.getElementById("de-paper");
    const bodyEl = document.getElementById("de-body-text");
    if (paper && typeof _dwResolvePaperBg === "function") {
        paper.style.background = _dwResolvePaperBg(style.bgMood || "default");
    }
    if (bodyEl && typeof _dwResolveFontFamily === "function") {
        const font = style.font || "caveat";
        const size = style.textSize || "m";
        bodyEl.style.fontFamily = _dwResolveFontFamily(font);
        bodyEl.style.fontSize   = _dwResolveFontSize(font, size) + "px";
        bodyEl.style.lineHeight = _dwResolveLineHeight(font, size);
        bodyEl.style.color      = _dwResolveTextColor(style.textColor || "default");
    }
}

/* ── Date formatters ────────────────────────────────────────────── */

function _deFmtDateLong(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}
function _deFmtDateShort(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString("en-US", { month: "short", day: "2-digit" }).toUpperCase();
}

/* ── Handlers ───────────────────────────────────────────────────── */

function _deBack() {
    document.removeEventListener("keydown", _deKeyHandler);
    const view = document.getElementById("diary-view");
    if (view) view.classList.remove("de-active");
    if (typeof openDiarySection === "function") openDiarySection("today");
}

function _deToggleDelete() {
    _deState.deleteOpen = !_deState.deleteOpen;
    const pop = document.getElementById("de-delete-pop");
    if (pop) pop.classList.toggle("is-hidden", !_deState.deleteOpen);
}

function _deKeyHandler(e) {
    if (e.key === "Escape") {
        if (_deState.deleteOpen) {
            _deState.deleteOpen = false;
            const pop = document.getElementById("de-delete-pop");
            if (pop) pop.classList.add("is-hidden");
        } else {
            _deBack();
        }
    }
}

async function _deDelete() {
    const id = _deState.entryId;
    if (!id) return;
    try {
        const res = await fetch("/api/diary/entries/" + encodeURIComponent(id), { method: "DELETE" });
        if (!res.ok && res.status !== 204) throw new Error("delete failed: " + res.status);
        try { localStorage.removeItem("nss.diary.entry." + id); } catch (_) {}
        _deBack();
    } catch (err) {
        const pop = document.getElementById("de-delete-pop");
        if (pop) {
            pop.querySelector(".de-delete-pop-msg").textContent = "Couldn't delete. Try again.";
        }
    }
}

function _deShare() {
    // Stub — backend hook for parent share is tracked separately.
    alert("Share with parent — coming next.");
}
