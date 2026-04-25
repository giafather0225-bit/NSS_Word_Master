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
        case "freewriting": (typeof _renderDiaryWrite === "function") ? _renderDiaryWrite("free")    : _renderFreeWriting();  break;
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

// ─── Diary Home (Decorated, Pinterest stationery) ───────────────
// Spec: handoff/02b-diary-spec.md — Screen 1 (Diary Home)
// Layout: 2×2 grid · Mode CTAs · Prompt card · Week mood + Polaroids · Stats 2×2

/** Mood palette — sync with handoff/reference/DiaryScreens.jsx MOODS. @tag DIARY */
const _DH_MOODS = {
    great:   { label: "great",   dot: "#E09AAE" },
    happy:   { label: "happy",   dot: "#EEC770" },
    calm:    { label: "calm",    dot: "#8AC4A8" },
    curious: { label: "curious", dot: "#7FA8CC" },
    tired:   { label: "tired",   dot: "#B8A4DC" },
    sad:     { label: "sad",     dot: "#EBA98C" },
};
// Expose for diary-write.js (vanilla, no modules → cross-file via window).
window._DH_MOODS = _DH_MOODS;

/** Lucide icon helper. Inline SVG via data attribute, hydrated by lucide.createIcons(). */
function _dhIcon(name, size) {
    const px = size || 16;
    return `<i data-lucide="${name}" width="${px}" height="${px}"></i>`;
}

/** Hydrate Lucide icons inside the Diary Home root after innerHTML insertion. */
function _dhRefreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
        window.lucide.createIcons();
    }
}

/**
 * Render the Diary Home screen (Decorated 2×2 layout).
 * @tag DIARY HOME
 */
async function _renderDiaryHome() {
    const view = document.getElementById("diary-view");
    if (!view) return;

    view.innerHTML = `
        <div class="dh-root" id="dh-root">
            <header class="dh-chrome">
                <div class="dh-chrome-left">
                    <button class="dh-back-home" type="button"
                            onclick="switchView('home')" aria-label="Back to home">
                        ${_dhIcon("chevron-left", 14)} Home
                    </button>
                    <span class="dh-chrome-eyebrow">Diary · Today</span>
                    <div class="dh-chrome-title">A little page for today</div>
                    <div class="dh-chrome-sub">Write what you feel, or free-write for fun.</div>
                </div>
                <div class="dh-chrome-actions">
                    <button class="dh-cta-write" type="button" onclick="_dhStartWrite('journal')">
                        ${_dhIcon("pen-tool", 14)} Start writing
                    </button>
                    <button class="dh-more-btn" type="button" aria-label="More diary sections"
                            aria-haspopup="menu" onclick="_dhToggleMore(event)">
                        ${_dhIcon("more-horizontal", 18)}
                    </button>
                    <div class="dh-more-menu is-hidden" id="dh-more-menu" role="menu">
                        <button class="dh-more-item" type="button" role="menuitem" onclick="_dhMoreOpen('sentences')">
                            ${_dhIcon("message-square", 14)} My Sentences
                        </button>
                        <button class="dh-more-item" type="button" role="menuitem" onclick="_dhMoreOpen('worlds')">
                            ${_dhIcon("globe", 14)} My Worlds
                        </button>
                        <button class="dh-more-item" type="button" role="menuitem" onclick="_dhMoreOpen('timeline')">
                            ${_dhIcon("trending-up", 14)} Growth Timeline
                        </button>
                        <button class="dh-more-item" type="button" role="menuitem" onclick="_dhMoreOpen('dayoff')">
                            ${_dhIcon("umbrella", 14)} Day off · all requests
                        </button>
                    </div>
                </div>
            </header>

            <div class="dh-grid">
                <!-- Top-left: Mode CTAs -->
                <div class="dh-modes">
                    <button class="dh-mode" type="button" onclick="_dhStartWrite('journal')">
                        <span class="dh-washi" style="top:-8px;left:20px;width:70px;background:var(--diary-soft);transform:rotate(-8deg);"></span>
                        <div class="dh-mode-icon">${_dhIcon("book-open", 17)}</div>
                        <div class="dh-mode-title">Journal</div>
                        <div class="dh-mode-copy">Pick your mood, answer a prompt, add photos.</div>
                        <div class="dh-mode-cta">Begin ${_dhIcon("chevron-right", 11)}</div>
                    </button>
                    <button class="dh-mode dh-mode--free" type="button" onclick="_dhStartWrite('free')">
                        <span class="dh-washi" style="top:-8px;right:20px;width:70px;background:var(--english-soft);transform:rotate(6deg);"></span>
                        <div class="dh-mode-icon">${_dhIcon("sparkles", 17)}</div>
                        <div class="dh-mode-title">Free Write</div>
                        <div class="dh-mode-copy">Write anything. AI gives gentle feedback.</div>
                        <div class="dh-mode-cta">Begin ${_dhIcon("chevron-right", 11)}</div>
                    </button>
                </div>

                <!-- Top-right: Prompt card -->
                <div class="dh-prompt">
                    <span class="dh-washi" style="top:-8px;left:32px;width:74px;background:var(--arcade-soft);transform:rotate(-4deg);"></span>
                    <div class="dh-prompt-eyebrow">Today's prompt</div>
                    <div class="dh-prompt-q" id="dh-prompt-q">What made you smile today?</div>
                    <div class="dh-prompt-tip">Try using <i>three new words</i> from today's lesson.</div>
                    <button class="dh-prompt-btn" type="button" onclick="_dhStartPrompt()">Start in Journal</button>
                </div>

                <!-- Bottom-left: Week mood + Recent polaroids -->
                <div class="dh-bl">
                    <div class="dh-week">
                        <span class="dh-washi" style="top:-9px;left:28px;width:90px;background:var(--diary-soft);transform:rotate(-4deg);"></span>
                        <div class="dh-week-head">
                            <div>
                                <div class="dh-week-title">This week's mood</div>
                                <div class="dh-week-sub">Tap a day to open that entry.</div>
                            </div>
                            <button class="dh-week-link" type="button" onclick="openDiarySection('calendar')">
                                Month view ${_dhIcon("chevron-right", 11)}
                            </button>
                        </div>
                        <div class="dh-week-grid" id="dh-week-grid"></div>
                    </div>

                    <div class="dh-recent">
                        <div class="dh-recent-head">
                            <div class="dh-recent-title">Recent pages</div>
                            <button class="dh-recent-link" type="button" onclick="openDiarySection('calendar')">See all</button>
                        </div>
                        <div class="dh-recent-grid" id="dh-recent-grid">
                            <p class="diary-state-msg compact">Loading…</p>
                        </div>
                    </div>
                </div>

                <!-- Bottom-right: Stats 2×2 + Day off CTA -->
                <div class="dh-stats">
                    <span class="dh-washi" style="top:-9px;left:28px;width:80px;background:var(--math-soft);transform:rotate(5deg);"></span>
                    <div class="dh-stats-head">
                        <div>
                            <div class="dh-stats-title">This month</div>
                            <div class="dh-stats-sub">Your writing life so far.</div>
                        </div>
                        <div class="dh-stats-month" id="dh-stats-month">—</div>
                    </div>
                    <div class="dh-stats-grid" id="dh-stats-grid">
                        ${_dhTileSkeleton("Entries", "diary",   "notebook")}
                        ${_dhTileSkeleton("Words",   "english", "edit-3")}
                        ${_dhTileSkeleton("Streak",  "arcade",  "flame")}
                        ${_dhTileSkeleton("Day off", "rewards", "coffee")}
                    </div>
                    <button class="dh-dayoff-cta" id="dh-dayoff-cta" type="button" onclick="_dhOpenDayOffModal()">
                        ${_dhIcon("coffee", 13)} Request a day off
                    </button>
                </div>
            </div>
            ${_dhDayOffModalHTML()}
        </div>`;

    _dhRefreshIcons();
    _dhFillStaticBits();
    _dhLoadHomeData();
}

/** Render an empty stat tile placeholder. */
function _dhTileSkeleton(label, color, icon) {
    return `
        <div class="dh-tile" data-tile="${label.toLowerCase().replace(/\s+/g,'-')}">
            <div class="dh-tile-icon dh-tile-icon--${color}">${_dhIcon(icon, 17)}</div>
            <div>
                <div class="dh-tile-value" data-role="value">—</div>
                <div class="dh-tile-label">${escapeHtml(label)}</div>
                <div class="dh-tile-sub" data-role="sub">&nbsp;</div>
            </div>
        </div>`;
}

/** Fill bits that don't need an API call (current month label). */
function _dhFillStaticBits() {
    const month = new Date().toLocaleDateString("en-US", { month: "long" });
    const el = document.getElementById("dh-stats-month");
    if (el) el.textContent = month;
}

/** "Start writing" CTAs — Step 2 (Write screen) is not yet implemented in this PR. */
function _dhStartWrite(mode) {
    try { localStorage.setItem("nss.diary.seed.mode", mode || "journal"); } catch (_) {}
    // Until /diary/write is built, fall back to existing Daily Journal section.
    openDiarySection(mode === "free" ? "freewriting" : "journal");
}

/** "Start in Journal" — seeds prompt + mode then routes to Journal sub-section. */
function _dhStartPrompt() {
    const q = document.getElementById("dh-prompt-q");
    const prompt = q ? q.textContent.trim() : "";
    try {
        localStorage.setItem("nss.diary.seed.mode", "journal");
        if (prompt) localStorage.setItem("nss.diary.seed.prompt", prompt);
    } catch (_) {}
    openDiarySection("journal");
}

/**
 * Load entries + streak in parallel, then paint week strip / polaroids / stats.
 * Falls back to placeholder content if the endpoints are unavailable.
 * @tag DIARY HOME
 */
async function _dhLoadHomeData() {
    let entries = [];
    let streakDays = 0;
    let dayOffs = [];

    try {
        const [entriesRes, streakRes, dayOffRes] = await Promise.allSettled([
            fetch(`/api/diary/entries?limit=100`),
            fetch(`/api/streak/status`),
            fetch(`/api/day-off/requests`),
        ]);

        if (entriesRes.status === "fulfilled" && entriesRes.value.ok) {
            const d = await entriesRes.value.json();
            entries = Array.isArray(d.entries) ? d.entries : [];
        }
        if (streakRes.status === "fulfilled" && streakRes.value.ok) {
            const d = await streakRes.value.json();
            streakDays = d.streak_days ?? d.current_streak ?? 0;
        }
        if (dayOffRes.status === "fulfilled" && dayOffRes.value.ok) {
            const d = await dayOffRes.value.json();
            dayOffs = Array.isArray(d.requests) ? d.requests : [];
        }
    } catch (_) { /* network error → keep placeholders */ }

    _dhState.dayOffs = dayOffs;
    _dhPaintWeek(entries);
    _dhPaintRecent(entries);
    _dhPaintStats(entries, streakDays, dayOffs);
}

/** Render the 7-day week mood strip (Mon..Sun), filling cells that have entries. */
function _dhPaintWeek(entries) {
    const grid = document.getElementById("dh-week-grid");
    if (!grid) return;

    const today = new Date();
    const dow = today.getDay(); // 0=Sun..6=Sat
    const monday = new Date(today);
    monday.setDate(today.getDate() - ((dow + 6) % 7)); // back up to Monday

    const byDate = {};
    for (const e of entries) {
        const iso = (e.entry_date || e.date || "").slice(0, 10);
        if (iso) byDate[iso] = e;
    }

    const labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    let html = "";
    for (let i = 0; i < 7; i++) {
        const d = new Date(monday);
        d.setDate(monday.getDate() + i);
        const iso = d.toISOString().slice(0, 10);
        const entry = byDate[iso];
        const mood = entry?.mood || null;
        const moodMeta = mood && _DH_MOODS[mood] ? _DH_MOODS[mood] : null;
        const empty = !mood;
        html += `
            <button class="dh-week-cell ${empty ? "is-empty" : ""}" type="button"
                ${empty ? "" : `aria-label="${escapeHtml(d.toDateString())}, ${escapeHtml(mood)} mood"`}
                ${empty ? "disabled" : ""}>
                <div class="dh-week-day">${labels[i]}</div>
                <div class="dh-week-dot" style="${moodMeta ? `background:${moodMeta.dot};` : ""}"></div>
            </button>`;
    }
    grid.innerHTML = html;
}

/** Render up to 3 polaroids of the most recent entries. */
function _dhPaintRecent(entries) {
    const grid = document.getElementById("dh-recent-grid");
    if (!grid) return;

    const sorted = [...entries].sort((a, b) => {
        const da = (a.entry_date || a.date || "");
        const db = (b.entry_date || b.date || "");
        return db.localeCompare(da);
    });
    const recent = sorted.slice(0, 3);

    if (recent.length === 0) {
        grid.innerHTML = `<div class="dh-poly-empty">No pages yet. Start your first one →</div>`;
        return;
    }

    const tiltClass = (i) => i === 0 ? "dh-poly--tilt-l" : i === 1 ? "" : "dh-poly--tilt-r";
    grid.innerHTML = recent.map((e, i) => _dhPolaroid(e, tiltClass(i))).join("");
}

/** Single polaroid card markup. */
function _dhPolaroid(entry, tiltClass) {
    const mood = entry.mood && _DH_MOODS[entry.mood] ? _DH_MOODS[entry.mood] : null;
    const photoBg = mood
        ? `background:linear-gradient(135deg, ${mood.dot}, var(--diary-light));`
        : "";
    const photos = Array.isArray(entry.photos) ? entry.photos.slice(0, 3) : [];
    const type = entry.type === "free" || entry.entry_type === "free" ? "Free Write" : "Journal";

    let mosaic = "";
    if (photos.length > 0) {
        const cls = `dh-poly-mosaic--${photos.length}`;
        mosaic = `<div class="dh-poly-mosaic ${cls}">` +
            photos.map(p => {
                // Prefer the 256-px thumbnail in the polaroid (~96-128 px tile)
                // and fall back to the full-size URL for legacy snapshots.
                const url  = p.thumb_url || p.url || p.path || "";
                const tone = p.tone || "var(--diary-soft)";
                const bg = url
                    ? `background-image:url('${url}');`
                    : `background:linear-gradient(135deg, ${tone}, #fff);`;
                return `<div class="dh-poly-tile" style="${bg}"></div>`;
            }).join("") + `</div>`;
    }

    const countBadge = photos.length > 1
        ? `<div class="dh-poly-count">${_dhIcon("grid", 10)} ${photos.length}</div>`
        : "";

    const title = entry.title || (entry.content || "").split(/[.!?]/)[0].slice(0, 40) || "Untitled";
    const text  = (entry.content || entry.body || "").trim();
    const dateLong = _dhFmtDateShort(entry.entry_date || entry.date || "");

    const onClick = entry.id != null
        ? `onclick="_dhOpenEntry(${Number(entry.id)})"`
        : "";

    return `
        <button class="dh-poly ${tiltClass}" type="button" ${onClick}>
            <div class="dh-poly-photo" style="${photoBg}">
                ${mosaic}
                <div class="dh-poly-pill">${type}</div>
                ${countBadge}
            </div>
            <div class="dh-poly-body">
                <div class="dh-poly-title">${escapeHtml(title)}</div>
                <div class="dh-poly-text">${escapeHtml(text)}</div>
                <div class="dh-poly-date">${escapeHtml(dateLong)}</div>
            </div>
        </button>`;
}

/** Toggle Home chrome ⋯ More dropdown (sentences / worlds / timeline / dayoff). */
function _dhToggleMore(evt) {
    if (evt) evt.stopPropagation();
    const m = document.getElementById("dh-more-menu");
    if (!m) return;
    const willOpen = m.classList.contains("is-hidden");
    m.classList.toggle("is-hidden", !willOpen);
    if (willOpen) {
        document.addEventListener("click", _dhCloseMoreOnDocClick, { once: true });
    }
}
function _dhCloseMoreOnDocClick() {
    const m = document.getElementById("dh-more-menu");
    if (m) m.classList.add("is-hidden");
}
/** Route to a non-hub-level Diary sub-section (sidebar reappears there). */
function _dhMoreOpen(section) {
    _dhCloseMoreOnDocClick();
    if (typeof openDiarySection === "function") openDiarySection(section);
}

/** Open Entry screen for a given entry id. */
function _dhOpenEntry(id) {
    if (typeof _renderDiaryEntry === "function") {
        // Mark the entry view active, then call the renderer directly so
        // openDiarySection's cleanup logic doesn't fight us.
        const view = document.getElementById("diary-view");
        if (view) view.classList.add("de-active");
        document.body.classList.add("dh-fullscreen");
        _renderDiaryEntry(id);
    } else {
        openDiarySection("today");
    }
}

/** Format ISO date as e.g. "APR 23". */
function _dhFmtDateShort(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-US", { month: "short", day: "2-digit" }).toUpperCase();
}

/** Paint the 4 stat tiles (Entries / Words / Streak / Day off). */
function _dhPaintStats(entries, streakDays, dayOffs) {
    const monthIso = new Date().toISOString().slice(0, 7);
    const monthEntries = entries.filter(e => (e.entry_date || e.date || "").startsWith(monthIso));
    const totalWords = monthEntries.reduce(
        (sum, e) => sum + ((e.content || e.body || "").split(/\s+/).filter(Boolean).length),
        0
    );

    const used = (dayOffs || [])
        .filter(r => (r.request_date || "").startsWith(monthIso))
        .filter(r => {
            const s = (r.status || "").toLowerCase();
            return s === "approved" || s === "pending";
        }).length;
    const left = Math.max(_DH_DAYOFF_MAX - used, 0);

    const set = (label, value, sub) => {
        const tile = document.querySelector(`.dh-tile[data-tile="${label}"]`);
        if (!tile) return;
        const v = tile.querySelector('[data-role="value"]');
        const s = tile.querySelector('[data-role="sub"]');
        if (v) v.textContent = value;
        if (s) s.textContent = sub || "";
    };

    set("entries", String(monthEntries.length), "this month");
    set("words",   totalWords.toLocaleString(),  "kept writing");
    set("streak",  `${streakDays}d`,             streakDays > 0 ? "keep it going" : "start today");
    set("day-off", `${used}/${_DH_DAYOFF_MAX}`,  left > 0 ? `${left} left` : "all used");

    // Reflect remaining quota on the CTA button.
    const cta = document.getElementById("dh-dayoff-cta");
    if (cta) {
        if (left <= 0) {
            cta.disabled = true;
            cta.setAttribute("aria-disabled", "true");
            cta.innerHTML = `${_dhIcon("coffee", 13)} No day offs left this month`;
        } else {
            cta.disabled = false;
            cta.removeAttribute("aria-disabled");
            cta.innerHTML = `${_dhIcon("coffee", 13)} Request a day off`;
        }
    }
    _dhRefreshIcons();
}

/* ── Day Off Request modal (Home) ──────────────────────────────── */

const _DH_DAYOFF_MAX = 2;
const _dhState = { dayOffs: [], modal: { open: false } };

/** Modal markup — hidden by default. */
function _dhDayOffModalHTML() {
    return `
        <div class="dh-modal-backdrop is-hidden" id="dh-dayoff-modal" role="dialog"
             aria-modal="true" aria-label="Request a day off"
             onclick="_dhCloseDayOffModalIfBackdrop(event)">
            <div class="dh-modal" onclick="event.stopPropagation()" lang="en">
                <span class="dh-washi" style="top:-9px;left:32px;width:90px;background:var(--arcade-soft);transform:rotate(-4deg);"></span>
                <div class="dh-modal-head">
                    <div class="dh-modal-icon">${_dhIcon("coffee", 17)}</div>
                    <div>
                        <div class="dh-modal-title">Take a day off?</div>
                        <div class="dh-modal-sub" id="dh-dayoff-sub">— left this month</div>
                    </div>
                </div>
                <div class="dh-modal-field">
                    <label class="dh-modal-label" for="dh-dayoff-start">Single day or range?</label>
                    <div class="dh-modal-range">
                        <input class="dh-modal-input" type="date" id="dh-dayoff-start" min="" lang="en"/>
                        <span class="dh-modal-range-sep">→</span>
                        <input class="dh-modal-input" type="date" id="dh-dayoff-end" min="" lang="en"
                               placeholder="optional"/>
                    </div>
                    <div class="dh-modal-help">Leave the second date empty for a single day.</div>
                </div>
                <div class="dh-modal-field">
                    <label class="dh-modal-label" for="dh-dayoff-reason">
                        Why? <span class="dh-modal-label-hint">(optional)</span>
                    </label>
                    <input class="dh-modal-input" type="text" id="dh-dayoff-reason"
                           maxlength="60" placeholder="e.g. Family trip, feeling sick"/>
                </div>
                <div class="dh-modal-note">
                    ${_dhIcon("heart", 13)}
                    Mom or Dad will see your request and say OK.
                </div>
                <div class="dh-modal-error" id="dh-dayoff-error"></div>
                <div class="dh-modal-actions">
                    <button class="dh-modal-cancel" type="button" onclick="_dhCloseDayOffModal()">Cancel</button>
                    <button class="dh-modal-submit" id="dh-dayoff-submit" type="button"
                            onclick="_dhSubmitDayOff()" disabled aria-disabled="true">
                        ${_dhIcon("check", 12)} Send request
                    </button>
                </div>
            </div>
        </div>`;
}

function _dhOpenDayOffModal() {
    const monthIso = new Date().toISOString().slice(0, 7);
    const used = (_dhState.dayOffs || [])
        .filter(r => (r.request_date || "").startsWith(monthIso))
        .filter(r => {
            const s = (r.status || "").toLowerCase();
            return s === "approved" || s === "pending";
        }).length;
    const left = Math.max(_DH_DAYOFF_MAX - used, 0);
    if (left <= 0) return;

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const minDate = tomorrow.toISOString().slice(0, 10);

    const modal = document.getElementById("dh-dayoff-modal");
    const startEl = document.getElementById("dh-dayoff-start");
    const endEl = document.getElementById("dh-dayoff-end");
    const reasonEl = document.getElementById("dh-dayoff-reason");
    const subEl = document.getElementById("dh-dayoff-sub");
    const errEl = document.getElementById("dh-dayoff-error");
    const submitEl = document.getElementById("dh-dayoff-submit");
    if (!modal) return;

    [startEl, endEl].forEach(el => {
        if (!el) return;
        el.value = "";
        el.min = minDate;
        el.removeEventListener("input", _dhDayOffValidate);
        el.addEventListener("input", _dhDayOffValidate);
    });
    if (reasonEl) reasonEl.value = "";
    if (subEl) subEl.textContent = `${left} / ${_DH_DAYOFF_MAX} left this month`;
    if (errEl) errEl.textContent = "";
    if (submitEl) {
        submitEl.disabled = true;
        submitEl.setAttribute("aria-disabled", "true");
        submitEl.innerHTML = `${_dhIcon("check", 12)} Send request`;
    }

    modal.classList.remove("is-hidden");
    _dhState.modal.open = true;
    document.addEventListener("keydown", _dhDayOffKey);
    _dhRefreshIcons();
    setTimeout(() => startEl && startEl.focus(), 30);
}

function _dhDayOffValidate() {
    const startEl = document.getElementById("dh-dayoff-start");
    const endEl   = document.getElementById("dh-dayoff-end");
    const submitEl = document.getElementById("dh-dayoff-submit");
    const errEl   = document.getElementById("dh-dayoff-error");
    if (!submitEl) return;
    const start = startEl && startEl.value;
    const end   = endEl   && endEl.value;
    let ok = !!start;
    let err = "";
    if (start && end && end < start) {
        ok = false;
        err = "End date must be on/after the start.";
    }
    // Range size limit: don't let one request blow past the monthly quota.
    if (ok && start && end) {
        const days = _dhDayCount(start, end);
        if (days > _DH_DAYOFF_MAX) {
            ok = false;
            err = `Range too long — max ${_DH_DAYOFF_MAX} days.`;
        }
    }
    if (errEl) errEl.textContent = err;
    submitEl.disabled = !ok;
    submitEl.setAttribute("aria-disabled", String(!ok));
}

/** Inclusive day count between two ISO yyyy-mm-dd strings. */
function _dhDayCount(start, end) {
    const a = new Date(start + "T00:00:00");
    const b = new Date(end   + "T00:00:00");
    const ms = b - a;
    if (Number.isNaN(ms) || ms < 0) return 0;
    return Math.round(ms / 86400000) + 1;
}

/** Build ISO yyyy-mm-dd strings from start..end inclusive. */
function _dhExpandRange(start, end) {
    const out = [];
    const a = new Date(start + "T00:00:00");
    const b = new Date((end || start) + "T00:00:00");
    if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime())) return out;
    for (let d = new Date(a); d <= b; d.setDate(d.getDate() + 1)) {
        out.push(d.toISOString().slice(0, 10));
    }
    return out;
}

/** Render a compact history list inside the modal. */
function _dhRenderDayOffHistory() {
    const wrap = document.getElementById("dh-dayoff-history");
    if (!wrap) return;
    const rows = (_dhState.dayOffs || []).slice(0, 5);
    if (!rows.length) { wrap.innerHTML = ""; return; }
    const LABEL = { pending: "Pending", approved: "Approved", denied: "Denied" };
    wrap.innerHTML = `
        <div class="dh-modal-history-label">Recent requests</div>
        <div class="dh-modal-history-list">
            ${rows.map(r => {
                const s = (r.status || "pending").toLowerCase();
                return `<div class="dh-modal-history-row">
                    <span class="dh-modal-history-date">${escapeHtml(r.request_date || "")}</span>
                    <span class="dh-modal-history-status ${s}">${LABEL[s] || s}</span>
                </div>`;
            }).join("")}
        </div>`;
}

function _dhCloseDayOffModal() {
    const modal = document.getElementById("dh-dayoff-modal");
    if (modal) modal.classList.add("is-hidden");
    _dhState.modal.open = false;
    document.removeEventListener("keydown", _dhDayOffKey);
}

function _dhCloseDayOffModalIfBackdrop(e) {
    if (e.target && e.target.id === "dh-dayoff-modal") _dhCloseDayOffModal();
}

function _dhDayOffKey(e) {
    if (e.key === "Escape" && _dhState.modal.open) _dhCloseDayOffModal();
}

async function _dhSubmitDayOff() {
    const startEl  = document.getElementById("dh-dayoff-start");
    const endEl    = document.getElementById("dh-dayoff-end");
    const reasonEl = document.getElementById("dh-dayoff-reason");
    const errEl    = document.getElementById("dh-dayoff-error");
    const submitEl = document.getElementById("dh-dayoff-submit");
    if (!startEl || !startEl.value) return;
    const start  = startEl.value;
    const end    = (endEl && endEl.value) || start;
    const dates  = _dhExpandRange(start, end);
    if (!dates.length) return;
    // Backend requires non-empty reason; provide a polite default if blank.
    const reason = (reasonEl && reasonEl.value.trim()) || "Personal day";

    if (errEl) errEl.textContent = "";
    if (submitEl) {
        submitEl.disabled = true;
        submitEl.innerHTML = `${_dhIcon("check", 12)} Sending…`;
        _dhRefreshIcons();
    }

    // Submit each day separately — the existing backend stores one row per
    // date and rejects duplicates with 409. We stop on the first hard
    // failure (other than 409) so the user can fix and retry.
    const failed = [];
    for (const d of dates) {
        try {
            const res = await fetch("/api/day-off/request", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ request_date: d, reason }),
            });
            if (!res.ok && res.status !== 409) {
                let msg = `Couldn't send ${d}.`;
                try {
                    const j = await res.json();
                    if (j && j.detail) msg = j.detail;
                } catch (_) {}
                failed.push({ d, msg });
                break;
            }
        } catch (_) {
            failed.push({ d, msg: `Network error on ${d}.` });
            break;
        }
    }
    if (failed.length) {
        if (errEl) errEl.textContent = failed[0].msg;
        if (submitEl) {
            submitEl.disabled = false;
            submitEl.innerHTML = `${_dhIcon("check", 12)} Send request`;
            _dhRefreshIcons();
        }
        return;
    }
    _dhCloseDayOffModal();
    _dhLoadHomeData();
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
                <span class="ds-empty-icon">🌱</span>
                Keep learning to unlock milestones!
            </div>`;
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

// ─── Day Off ──────────────────────────────────────────────────

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
    const el = document.getElementById("ds-do-list");
    if (!el) return;
    try {
        const res  = await fetch("/api/day-off/requests");
        if (!res.ok) return;
        const data = await res.json();
        const rows = data.requests || [];
        if (!rows.length) {
            el.innerHTML = `<div class="ds-empty">
                <span class="ds-empty-icon">☕</span>
                No requests yet.
            </div>`;
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
                <span class="ds-empty-icon">📝</span>
                No sentences yet. Finish Step 5 of a lesson to start collecting them.
            </div>`;
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

// ─── My Worlds ────────────────────────────────────────────────

/** @tag DIARY MY_WORLDS GROWTH_THEME */
async function _renderWorlds() {
    const view = _dsubPrep();
    if (!view) return;
    view.innerHTML = `
        <div class="ds-root">
            ${_dsubChrome("Diary · Worlds", "My Worlds", "Growth themes you've completed")}
            <div class="ds-body" id="ds-worlds-body">
                <p class="ds-loading">Loading…</p>
            </div>
        </div>`;
    _dhRefreshIcons();
    try {
        const res  = await fetch("/api/growth/theme/all");
        if (!res.ok) throw new Error();
        const data = await res.json();
        const done = (data.themes || []).filter(t => t.is_completed);
        const body = document.getElementById("ds-worlds-body");
        if (!done.length) {
            body.innerHTML = `<div class="ds-empty">
                <span class="ds-empty-icon">🌱</span>
                Finish a Growth Theme to plant your first world here.
            </div>`;
            return;
        }
        body.innerHTML = `<div class="ds-worlds-grid">${done.map(t => `
            <div class="ds-world-card">
                <img class="ds-world-img" src="${t.img_url}"
                     alt="${escapeHtml(t.label || t.theme)}"
                     onerror="this.classList.add('broken')">
                <div class="ds-world-title">${escapeHtml(t.label || t.theme)}</div>
                <div class="ds-world-status"><span class="ds-world-dot"></span> Completed</div>
            </div>`).join("")}</div>`;
    } catch (_) {
        const body = document.getElementById("ds-worlds-body");
        if (body) body.innerHTML = `<p class="ds-error">Failed to load.</p>`;
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
