/* ================================================================
   diary-home.js — Diary Home screen · core layout + painters
   Section: Diary
   Dependencies: diary.js (escapeHtml, openDiarySection),
                 diary-write.js, diary-entry.js, diary-calendar.js
   Spec: handoff/02b-diary-spec.md (Screen 1)

   Owns: mood palette, Decorated 2×2 home layout, week strip, polaroids,
         stats tiles. Day-off modal → diary-home-dayoff.js.
         Sub-section chrome + screens → diary-home-sub.js.
   ================================================================ */

// ─── Diary Home (Decorated, Pinterest stationery) ───────────────
// Spec: handoff/02b-diary-spec.md — Screen 1 (Diary Home)
// Layout: 2×2 grid · Mode CTAs · Prompt card · Week mood + Polaroids · Stats 2×2

/** Max day-off requests per calendar month. Consumed by diary-home-dayoff.js. */
const _DH_DAYOFF_MAX = 2;

/** Shared mutable state — modal open flag + loaded day-off list. */
let _dhState = { dayOffs: [], modal: { open: false } };

/** Mood palette — sync with handoff/reference/DiaryScreens.jsx MOODS. @tag DIARY */
const _DH_MOODS = {
    great:   { label: "great",   dot: "var(--diary-primary)" },
    happy:   { label: "happy",   dot: "var(--arcade-primary)" },
    calm:    { label: "calm",    dot: "var(--math-primary)" },
    curious: { label: "curious", dot: "var(--english-primary)" },
    tired:   { label: "tired",   dot: "var(--rewards-primary)" },
    sad:     { label: "sad",     dot: "var(--review-primary)" },
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
<button class="dh-more-item" type="button" role="menuitem" onclick="_dhMoreOpen('timeline')">
                            ${_dhIcon("trending-up", 14)} Growth Timeline
                        </button>
                        <button class="dh-more-item" type="button" role="menuitem" onclick="_dhMoreOpen('dayoff')">
                            ${_dhIcon("umbrella", 14)} Day off · all requests
                        </button>
                    </div>
                </div>
            </header>

            <div id="island-widget-diary"></div>

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
    if (typeof _renderIslandSubjectWidget === 'function') {
        _renderIslandSubjectWidget('island-widget-diary', 'savanna');
    }
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
    const todayIso = today.toISOString().slice(0, 10);
    let html = "";
    for (let i = 0; i < 7; i++) {
        const d = new Date(monday);
        d.setDate(monday.getDate() + i);
        const iso = d.toISOString().slice(0, 10);
        const isToday = iso === todayIso;
        const entry = byDate[iso];
        const mood = entry?.mood || null;
        const moodMeta = mood && _DH_MOODS[mood] ? _DH_MOODS[mood] : null;
        const empty = !mood;
        html += `
            <button class="dh-week-cell ${empty ? "is-empty" : ""}${isToday ? " is-today" : ""}" type="button"
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
                // URL 검증 — /api/ 경로만 허용해 임의 외부 URL 삽입 방지
                const safeUrl = (url && /^\/api\//.test(url)) ? encodeURI(url) : "";
                const bg = safeUrl
                    ? `background-image:url('${safeUrl}');`
                    : `background:linear-gradient(135deg, ${tone}, var(--bg-card));`;
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

    set("entries", String(monthEntries.length), monthEntries.length > 0 ? "this month" : "write your first!");
    set("words",   totalWords.toLocaleString(),  totalWords > 0 ? "kept writing" : "start writing!");
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
