/* ================================================================
   diary-write.js — GIA's Diary · Write screen (Decorated)
   Section: Diary
   Dependencies: diary.js (escapeHtml, openDiarySection, _DH_MOODS, _dhRefreshIcons)
   API endpoints: POST /api/diary/entries
   Spec: handoff/02b-diary-spec.md (Screen 2)
   ================================================================ */

/* ── Static config ─────────────────────────────────────────────── */

/** @tag DIARY */
const _DW_FONTS = [
    { id: "caveat",  label: "Caveat",  css: "'Caveat', cursive" },
    { id: "nunito",  label: "Nunito",  css: "'Nunito', sans-serif" },
    { id: "patrick", label: "Patrick", css: "'Patrick Hand', cursive" },
    { id: "shadows", label: "Shadows", css: "'Shadows Into Light', cursive" },
    { id: "indie",   label: "Indie",   css: "'Indie Flower', cursive" },
    { id: "kalam",   label: "Kalam",   css: "'Kalam', cursive" },
];
const _DW_SCRIPTY = new Set(["caveat", "shadows", "indie"]);

const _DW_TEXT_COLORS = [
    { id: "default", label: "Ink",    value: "var(--text-primary)" },
    { id: "diary",   label: "Pink",   value: "var(--diary-ink)" },
    { id: "english", label: "Blue",   value: "var(--english-ink)" },
    { id: "math",    label: "Green",  value: "var(--math-ink)" },
    { id: "arcade",  label: "Amber",  value: "var(--arcade-ink)" },
    { id: "rewards", label: "Purple", value: "var(--rewards-ink)" },
    { id: "review",  label: "Peach",  value: "var(--review-ink)" },
];

const _DW_BG_MOODS = [
    { id: "default",  label: "Paper",    fill: "#FFFFFF",              lined: "var(--diary-light)" },
    { id: "pink",     label: "Blossom",  fill: "var(--diary-light)",   lined: "var(--diary-soft)" },
    { id: "mint",     label: "Mint",     fill: "var(--math-light)",    lined: "var(--math-soft)" },
    { id: "sky",      label: "Sky",      fill: "var(--english-light)", lined: "var(--english-soft)" },
    { id: "butter",   label: "Butter",   fill: "var(--arcade-light)",  lined: "var(--arcade-soft)" },
    { id: "lavender", label: "Lavender", fill: "var(--rewards-light)", lined: "var(--rewards-soft)" },
    { id: "peach",    label: "Peach",    fill: "var(--review-light)",  lined: "var(--review-soft)" },
];

const _DW_STICKERS = [
    { id: "nature",  label: "Nature",  items: ["🌸","🌿","🌈","🌻","🍃","🌺","🌷","🌼"] },
    { id: "sky",     label: "Sky",     items: ["⭐","🌙","☀️","☁️","✨","🌤","🌟","☔"] },
    { id: "hearts",  label: "Hearts",  items: ["💕","❤️","💗","💖","💛","💚","💙","💜"] },
    { id: "faces",   label: "Faces",   items: ["😊","🥰","😌","🤗","🥺","😴","🤔","😍"] },
    { id: "things",  label: "Things",  items: ["📚","✏️","☕","🎀","🧸","🎈","🎁","📷"] },
    { id: "food",    label: "Food",    items: ["🍎","🍓","🍰","🍪","🍭","🍩","🥞","🍦"] },
    { id: "animals", label: "Animals", items: ["🐰","🐱","🐶","🐻","🐼","🦊","🐨","🐸"] },
];

const _DW_PROMPTS = [
    "What made you smile today?",
    "A small thing that surprised you.",
    "Something you felt proud of.",
    "A word you learned today.",
    "A question you asked in your head.",
];

const _DW_TIPS = [
    { k: "Start anywhere",   t: "You don't need to know the ending. Start with what you see or feel right now." },
    { k: "Show, don't tell", t: "Instead of 'I was sad,' try 'My feet dragged like wet shoes.'" },
    { k: "One small thing",  t: "Pick ONE moment from today. Don't try to cover the whole day." },
    { k: "Use your senses",  t: "What did you hear, smell, or touch? Your story comes alive." },
];

const _DW_MIN_WORDS = 15;

/* ── Module state ──────────────────────────────────────────────── */

const _dwState = {
    mode: "journal",      // 'journal' | 'free'
    mood: "happy",
    title: "",
    body: "",
    photos: [],           // [{ id, url, name }]
    prompt: "",
    style: { font: "caveat", textSize: "m", textColor: "default", bgMood: "default" },
    stkCat: 0,
    tipIdx: 0,
    moodOpen: false,
};

/* ── Resolvers ─────────────────────────────────────────────────── */

function _dwResolveFontFamily(font) {
    return (_DW_FONTS.find(f => f.id === font) || _DW_FONTS[0]).css;
}
function _dwResolveFontSize(font, size) {
    const base = _DW_SCRIPTY.has(font) ? 22 : 16;
    const bump = size === "s" ? -3 : size === "l" ? 4 : 0;
    return base + bump;
}
function _dwResolveLineHeight(font, size) {
    return Math.round(_dwResolveFontSize(font, size) * 1.55) + "px";
}
function _dwResolveTextColor(key) {
    return (_DW_TEXT_COLORS.find(c => c.id === key) || _DW_TEXT_COLORS[0]).value;
}
function _dwResolvePaperBg(bgKey) {
    const bg = _DW_BG_MOODS.find(b => b.id === bgKey) || _DW_BG_MOODS[0];
    // Decorated mode: ruled-paper repeating gradient, 32px line height.
    return `repeating-linear-gradient(180deg, ${bg.fill} 0 31px, ${bg.lined} 31px 32px)`;
}

/* ── Entry point ───────────────────────────────────────────────── */

/**
 * Render the Diary Write screen.
 * @tag DIARY WRITE
 * @param {'journal'|'free'} mode
 */
function _renderDiaryWrite(mode) {
    const view = document.getElementById("diary-view");
    if (!view) return;

    // Initialize state, honor any seed left by Home → "Start in Journal".
    _dwState.mode = mode === "free" ? "free" : "journal";
    try {
        const seedMode = localStorage.getItem("nss.diary.seed.mode");
        const seedPrompt = localStorage.getItem("nss.diary.seed.prompt");
        if (seedMode === "free" || seedMode === "journal") _dwState.mode = seedMode;
        if (seedPrompt) _dwState.prompt = seedPrompt;
        localStorage.removeItem("nss.diary.seed.mode");
        localStorage.removeItem("nss.diary.seed.prompt");
    } catch (_) {}

    if (!_dwState.prompt && _dwState.mode === "journal") _dwState.prompt = _DW_PROMPTS[0];

    // Hub-level: keep sidebar hidden, allow scroll.
    document.body.classList.add("dh-fullscreen");
    view.classList.add("dw-active");
    view.style.display = "flex";

    view.innerHTML = `
        <div class="dw-root" id="dw-root">
            ${_dwChromeHTML()}
            <div class="dw-body">
                <div class="dw-paper" id="dw-paper">
                    ${_dwPhotosHTML()}
                    <div class="dw-title-row">
                        <input class="dw-title-input" id="dw-title"
                               placeholder="Give this page a title…"
                               maxlength="80" autocomplete="off"/>
                        <button class="dw-suggest-pill is-hidden" id="dw-suggest-pill"
                                type="button" onclick="_dwSuggestTitle()">
                            ✨ Suggest
                        </button>
                    </div>
                    <div class="dw-prompt-quote" id="dw-prompt-quote"></div>
                    <textarea class="dw-body-input" id="dw-body"
                              placeholder="Start writing here…"></textarea>
                    ${_dwFooterHTML()}
                </div>
                <aside class="dw-aside">
                    <div id="dw-aside-top">${_dwAsideTopHTML()}</div>
                    ${_dwStyleToolsHTML()}
                    ${_dwDecorToolsHTML()}
                </aside>
            </div>
            <div class="dw-toast" id="dw-toast" role="status"></div>
        </div>`;

    _dwBindEvents();
    _dwApplyStyle();
    _dwApplyPrompt();
    _dwUpdateProgress();
    _dwRefreshIcons();
}

/* ── HTML builders ─────────────────────────────────────────────── */

function _dwIcon(name, size) {
    const px = size || 14;
    return `<i data-lucide="${name}" width="${px}" height="${px}"></i>`;
}
function _dwRefreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
        window.lucide.createIcons();
    }
}

function _dwChromeHTML() {
    const m = _dwState.mode;
    const eyebrow = m === "free" ? "Diary · Free Write" : "Diary · Journal";
    const title   = m === "free" ? "Free write what you feel" : "Write today's page";
    const sub     = m === "free" ? "Anything goes. AI gives gentle feedback." : "Pick a prompt, set a mood, write a few lines.";
    return `
        <header class="dw-chrome">
            <div class="dw-chrome-left">
                <button class="dw-back" type="button" onclick="_dwBack()">${_dwIcon("chevron-left", 14)} Diary</button>
                <span class="dw-eyebrow">${escapeHtml(eyebrow)}</span>
                <div class="dw-title">${escapeHtml(title)}</div>
                <div class="dw-sub">${escapeHtml(sub)}</div>
            </div>
            <div class="dw-chrome-right">
                <div class="dw-segmented" role="tablist" aria-label="Mode">
                    <button class="dw-seg ${m === 'journal' ? 'is-active' : ''}" role="tab"
                            type="button" onclick="_dwSetMode('journal')">Journal</button>
                    <button class="dw-seg ${m === 'free' ? 'is-active' : ''}" role="tab"
                            type="button" onclick="_dwSetMode('free')">Free Write</button>
                </div>
                <span class="dw-overflow-wrap">
                    <button class="dw-overflow" type="button" aria-label="More options"
                            aria-haspopup="menu" onclick="_dwToggleOverflow(event)">
                        ${_dwIcon("more-horizontal", 16)}
                    </button>
                    <div class="dw-overflow-menu is-hidden" id="dw-overflow-menu" role="menu">
                        <button class="dw-overflow-item" type="button" role="menuitem" onclick="_dwSaveDraft()">
                            ${_dwIcon("file-text", 13)} Save draft
                        </button>
                        <button class="dw-overflow-item danger" type="button" role="menuitem" onclick="_dwClearAll()">
                            ${_dwIcon("trash-2", 13)} Clear all
                        </button>
                        <button class="dw-overflow-item" type="button" role="menuitem" onclick="_dwExportPDF()">
                            ${_dwIcon("download", 13)} Export as PDF
                        </button>
                    </div>
                </span>
                <button class="dw-save" id="dw-save" type="button" disabled
                        onclick="_dwSave()">${_dwIcon("check", 13)} Save · +15 XP</button>
            </div>
        </header>`;
}

function _dwPhotosHTML() {
    const photos = _dwState.photos;
    const tiles = photos.map(p => `
        <div class="dw-photo" style="background-image:url('${p.url}');" data-pid="${escapeHtml(p.id)}">
            <button class="dw-photo-x" type="button" aria-label="Remove photo"
                    onclick="_dwRemovePhoto('${escapeHtml(p.id)}')">×</button>
        </div>`).join("");
    const addBtn = photos.length < 3
        ? `<label class="dw-photo-add" tabindex="0">
              + Add
              <input class="dw-photo-input" type="file" accept="image/*" multiple
                     onchange="_dwOnPhotoPick(event)"/>
           </label>`
        : "";
    return `
        <div class="dw-photos" id="dw-photos">
            ${tiles}${addBtn}
            <span class="dw-photos-count">Photos ${photos.length}/3</span>
        </div>`;
}

function _dwFooterHTML() {
    const moodMeta = (window._DH_MOODS && window._DH_MOODS[_dwState.mood]) || null;
    const dot = moodMeta ? moodMeta.dot : "var(--border-subtle)";
    const opts = ["great", "happy", "calm", "curious", "tired", "sad"].map(id => {
        const m = window._DH_MOODS && window._DH_MOODS[id];
        const c = m ? m.dot : "var(--border-subtle)";
        const active = id === _dwState.mood ? "is-active" : "";
        return `
            <button class="dw-mood-opt ${active}" type="button" onclick="_dwSetMood('${id}')">
                <span class="dw-mood-opt-dot" style="background:${c};"></span>
                <span class="dw-mood-opt-label">${id}</span>
            </button>`;
    }).join("");

    return `
        <div class="dw-footer">
            <div data-mood-picker style="position:relative;">
                <button class="dw-mood-pill" type="button" onclick="_dwToggleMood()" aria-haspopup="dialog" aria-expanded="false">
                    <span class="dw-mood-dot" id="dw-mood-dot" style="background:${dot};"></span>
                    <span id="dw-mood-label">${escapeHtml(_dwState.mood)}</span>
                </button>
                <div class="dw-mood-popover is-hidden" id="dw-mood-popover" role="dialog" aria-label="Pick a mood">
                    ${opts}
                </div>
            </div>
            <div class="dw-progress" id="dw-progress">
                <div class="dw-progress-bar"><div class="dw-progress-fill" id="dw-progress-fill" style="width:0%;"></div></div>
                <span><b id="dw-wc">0</b> / ${_DW_MIN_WORDS}</span>
            </div>
            <button class="dw-voice-btn" id="dw-speak-btn" type="button"
                    title="Speak — dictate into the page" aria-label="Speak"
                    onclick="_dwToggleSpeak()">🎤</button>
            <button class="dw-voice-btn" id="dw-listen-btn" type="button"
                    title="Listen — read this page aloud" aria-label="Listen"
                    onclick="_dwToggleListen()">🔊</button>
        </div>`;
}

function _dwAsideTopHTML() {
    return _dwState.mode === "free" ? _dwTipsHTML() : _dwPromptBankHTML();
}

function _dwPromptBankHTML() {
    const items = _DW_PROMPTS.map(p => {
        const active = p === _dwState.prompt ? "is-active" : "";
        return `<button class="dw-prompt-item ${active}" type="button"
                        onclick="_dwPickPrompt(this.dataset.p)" data-p="${escapeHtml(p)}">${escapeHtml(p)}</button>`;
    }).join("");
    return `
        <div class="dw-card">
            <div class="dw-card-label">More prompts</div>
            <div class="dw-prompts">${items}</div>
        </div>`;
}

function _dwTipsHTML() {
    const tip = _DW_TIPS[_dwState.tipIdx];
    const dots = _DW_TIPS.map((_, i) =>
        `<div class="${i === _dwState.tipIdx ? 'is-active' : ''}"></div>`).join("");
    return `
        <div class="dw-card dw-tips">
            <div class="dw-tips-head">
                <div class="dw-tips-icon"><span>${_dwIcon("sparkles", 12)}</span><b>Writing tip</b></div>
                <button class="dw-tips-next" type="button" onclick="_dwNextTip()">Next →</button>
            </div>
            <div class="dw-tips-key">${escapeHtml(tip.k)}</div>
            <div class="dw-tips-text">${escapeHtml(tip.t)}</div>
            <div class="dw-tips-dots">${dots}</div>
        </div>`;
}

function _dwStyleToolsHTML() {
    const fonts = _DW_FONTS.map(f => {
        const active = f.id === _dwState.style.font ? "is-active" : "";
        return `
            <button class="dw-font-btn ${active}" type="button" onclick="_dwSetFont('${f.id}')">
                <span class="dw-font-sample" style="font-family:${f.css};">Aa</span>
                <span class="dw-font-name">${escapeHtml(f.label)}</span>
            </button>`;
    }).join("");
    const sizes = ["s", "m", "l"].map(s => {
        const active = s === _dwState.style.textSize ? "is-active" : "";
        return `<button class="dw-size-btn ${active}" type="button"
                        data-size="${s}" onclick="_dwSetSize('${s}')">Aa</button>`;
    }).join("");
    const colors = _DW_TEXT_COLORS.map(c => {
        const active = c.id === _dwState.style.textColor ? "is-active" : "";
        return `<button class="dw-color-btn ${active}" type="button" title="${escapeHtml(c.label)}"
                        aria-label="Text color ${escapeHtml(c.label)}"
                        style="background:${c.value};"
                        onclick="_dwSetColor('${c.id}')"></button>`;
    }).join("");
    return `
        <div class="dw-card">
            <div class="dw-card-label">Style</div>
            <div>
                <div class="dw-row-label">Font</div>
                <div class="dw-row-grid3">${fonts}</div>
            </div>
            <div>
                <div class="dw-row-label">Size</div>
                <div class="dw-size-row">${sizes}</div>
            </div>
            <div>
                <div class="dw-row-label">Text color</div>
                <div class="dw-color-row">${colors}</div>
            </div>
        </div>`;
}

function _dwDecorToolsHTML() {
    const tabs = _DW_STICKERS.map((c, i) => {
        const active = i === _dwState.stkCat ? "is-active" : "";
        return `<button class="dw-stk-tab ${active}" type="button"
                        onclick="_dwSetStkCat(${i})">${escapeHtml(c.label)}</button>`;
    }).join("");
    const grid = _DW_STICKERS[_dwState.stkCat].items.map(s =>
        `<button class="dw-stk-btn" type="button" aria-label="Insert ${s}"
                 onclick="_dwInsertSticker('${s}')">${s}</button>`).join("");
    const bgs = _DW_BG_MOODS.map(b => {
        const active = b.id === _dwState.style.bgMood ? "is-active" : "";
        const x = b.id === "default" ? `<span class="dw-bg-btn-x">×</span>` : "";
        return `<button class="dw-bg-btn ${active}" type="button" title="${escapeHtml(b.label)}"
                        aria-label="Page color ${escapeHtml(b.label)}"
                        style="background:${b.fill};"
                        onclick="_dwSetBg('${b.id}')">${x}</button>`;
    }).join("");
    return `
        <div class="dw-card">
            <div class="dw-card-label">Decor</div>
            <div>
                <div class="dw-row-label" style="display:flex;justify-content:space-between;">
                    <span>Stickers</span><span style="font-weight:500;">Tap to add</span>
                </div>
                <div class="dw-stk-tabs" id="dw-stk-tabs">${tabs}</div>
                <div class="dw-stk-grid" id="dw-stk-grid">${grid}</div>
            </div>
            <div>
                <div class="dw-row-label">Page color</div>
                <div class="dw-bg-row">${bgs}</div>
            </div>
        </div>`;
}

/* ── Event binding ─────────────────────────────────────────────── */

function _dwBindEvents() {
    const titleEl = document.getElementById("dw-title");
    const bodyEl  = document.getElementById("dw-body");
    if (titleEl) {
        titleEl.value = _dwState.title;
        titleEl.addEventListener("input", () => {
            _dwState.title = titleEl.value;
            _dwUpdateProgress();
        });
    }
    if (bodyEl) {
        bodyEl.value = _dwState.body;
        bodyEl.addEventListener("input", () => {
            _dwState.body = bodyEl.value;
            _dwUpdateProgress();
        });
    }
    document.addEventListener("keydown", _dwGlobalKeyHandler);
}

function _dwGlobalKeyHandler(e) {
    if (e.key === "Escape" && _dwState.moodOpen) {
        _dwState.moodOpen = false;
        const pop = document.getElementById("dw-mood-popover");
        if (pop) pop.classList.add("is-hidden");
    }
}

/* ── Mutators (called from inline handlers) ────────────────────── */

function _dwSetMode(mode) {
    if (mode !== "journal" && mode !== "free") return;
    _dwState.mode = mode;
    if (mode === "journal" && !_dwState.prompt) _dwState.prompt = _DW_PROMPTS[0];
    // Re-render chrome + aside top (mode-dependent), preserve paper inputs.
    const root = document.querySelector(".dw-root");
    if (!root) return;
    const chrome = root.querySelector(".dw-chrome");
    if (chrome) chrome.outerHTML = _dwChromeHTML();
    const asideTop = document.getElementById("dw-aside-top");
    if (asideTop) asideTop.innerHTML = _dwAsideTopHTML();
    _dwApplyPrompt();
    _dwUpdateProgress();
    _dwRefreshIcons();
}

function _dwSetMood(id) {
    _dwState.mood = id;
    _dwState.moodOpen = false;
    const pop = document.getElementById("dw-mood-popover");
    if (pop) pop.classList.add("is-hidden");
    const dot = document.getElementById("dw-mood-dot");
    const label = document.getElementById("dw-mood-label");
    const meta = window._DH_MOODS && window._DH_MOODS[id];
    if (dot && meta) dot.style.background = meta.dot;
    if (label) label.textContent = id;
    // Update active class in popover
    document.querySelectorAll(".dw-mood-opt").forEach(b => b.classList.remove("is-active"));
}

function _dwToggleMood() {
    _dwState.moodOpen = !_dwState.moodOpen;
    const pop = document.getElementById("dw-mood-popover");
    if (pop) pop.classList.toggle("is-hidden", !_dwState.moodOpen);
}

function _dwPickPrompt(text) {
    _dwState.prompt = text;
    _dwApplyPrompt();
    document.querySelectorAll(".dw-prompt-item").forEach(b =>
        b.classList.toggle("is-active", b.dataset.p === text));
}

function _dwApplyPrompt() {
    const el = document.getElementById("dw-prompt-quote");
    if (!el) return;
    if (_dwState.mode === "journal" && _dwState.prompt) {
        el.textContent = _dwState.prompt;
    } else {
        el.textContent = "";
    }
}

function _dwNextTip() {
    _dwState.tipIdx = (_dwState.tipIdx + 1) % _DW_TIPS.length;
    const top = document.getElementById("dw-aside-top");
    if (top) top.innerHTML = _dwTipsHTML();
    _dwRefreshIcons();
}

function _dwSetFont(id)   { _dwState.style.font = id;       _dwApplyStyle(); _dwReRenderStyle(); }
function _dwSetSize(s)    { _dwState.style.textSize = s;    _dwApplyStyle(); _dwReRenderStyle(); }
function _dwSetColor(id)  { _dwState.style.textColor = id;  _dwApplyStyle(); _dwReRenderStyle(); }
function _dwSetBg(id)     { _dwState.style.bgMood = id;     _dwApplyStyle(); _dwReRenderDecor(); }
function _dwSetStkCat(i)  { _dwState.stkCat = i;            _dwReRenderDecor(); }

function _dwReRenderStyle() {
    // Find the Style card (the second .dw-card under .dw-aside) and swap.
    const cards = document.querySelectorAll(".dw-aside .dw-card");
    if (cards.length >= 2) cards[1].outerHTML = _dwStyleToolsHTML();
}
function _dwReRenderDecor() {
    const cards = document.querySelectorAll(".dw-aside .dw-card");
    if (cards.length >= 3) cards[2].outerHTML = _dwDecorToolsHTML();
}

/** Apply font/size/color/lineHeight + paper bg to the live editor. */
function _dwApplyStyle() {
    const body = document.getElementById("dw-body");
    const paper = document.getElementById("dw-paper");
    const s = _dwState.style;
    if (body) {
        body.style.fontFamily = _dwResolveFontFamily(s.font);
        body.style.fontSize   = _dwResolveFontSize(s.font, s.textSize) + "px";
        body.style.lineHeight = _dwResolveLineHeight(s.font, s.textSize);
        body.style.color      = _dwResolveTextColor(s.textColor);
    }
    if (paper) paper.style.background = _dwResolvePaperBg(s.bgMood);
}

/* ── Sticker insert ────────────────────────────────────────────── */

function _dwInsertSticker(emoji) {
    const ta = document.getElementById("dw-body");
    if (!ta) return;
    const insert = emoji + " ";
    const start = ta.selectionStart || 0;
    const end   = ta.selectionEnd   || 0;
    const value = ta.value;
    ta.value = value.slice(0, start) + insert + value.slice(end);
    const caret = start + insert.length;
    ta.focus();
    ta.setSelectionRange(caret, caret);
    _dwState.body = ta.value;
    _dwUpdateProgress();
}

/* ── Photos ────────────────────────────────────────────────────── */

async function _dwOnPhotoPick(e) {
    const files = Array.from(e.target.files || []);
    e.target.value = "";
    const room = 3 - _dwState.photos.length;
    const picked = files.slice(0, room);
    if (picked.length === 0) return;

    const today = new Date().toISOString().slice(0, 10);

    // Add optimistic local previews so the UI feels instant; replace each
    // tile's URL with the server-served URL once the upload returns.
    const placeholders = picked.map(f => ({
        id: "p-" + Date.now() + "-" + Math.random().toString(36).slice(2, 7),
        url: URL.createObjectURL(f),
        name: f.name,
        filename: null,
        uploading: true,
    }));
    _dwState.photos.push(...placeholders);
    _dwReRenderPhotos();

    // Upload sequentially — small N (≤3), and avoids race on filename uniqueness.
    for (let i = 0; i < picked.length; i++) {
        const f = picked[i];
        const ph = placeholders[i];
        const fd = new FormData();
        fd.append("entry_date", today);
        fd.append("file", f);
        try {
            const res = await fetch("/api/diary/photo/multi", { method: "POST", body: fd });
            if (!res.ok) throw new Error("upload failed: " + res.status);
            const data = await res.json();
            ph.filename = data.filename || null;
            // Swap the blob URL for the server URL so it survives reload.
            try { URL.revokeObjectURL(ph.url); } catch (_) {}
            ph.url = data.photo_url || ph.url;
            ph.uploading = false;
        } catch (err) {
            // Drop the failed placeholder and notify.
            _dwState.photos = _dwState.photos.filter(p => p.id !== ph.id);
            _dwToast("Photo upload failed.", true);
        }
    }
    _dwReRenderPhotos();
}

async function _dwRemovePhoto(id) {
    const target = _dwState.photos.find(p => p.id === id);
    _dwState.photos = _dwState.photos.filter(p => p.id !== id);
    _dwReRenderPhotos();
    // Best-effort backend cleanup so orphan files don't accumulate.
    if (target && target.filename) {
        try {
            await fetch("/api/diary/photo/" + encodeURIComponent(target.filename), { method: "DELETE" });
        } catch (_) {}
    }
}

function _dwReRenderPhotos() {
    const wrap = document.getElementById("dw-photos");
    if (!wrap) return;
    const tmp = document.createElement("div");
    tmp.innerHTML = _dwPhotosHTML();
    wrap.replaceWith(tmp.firstElementChild);
}

/* ── Word count + Save activation ──────────────────────────────── */

function _dwUpdateProgress() {
    const text = (_dwState.body || "").trim();
    const count = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const wcEl = document.getElementById("dw-wc");
    const fillEl = document.getElementById("dw-progress-fill");
    const progress = document.getElementById("dw-progress");
    if (wcEl) wcEl.textContent = String(count);
    if (fillEl) {
        const pct = Math.min(100, Math.round((count / _DW_MIN_WORDS) * 100));
        fillEl.style.width = pct + "%";
    }
    if (progress) progress.classList.toggle("is-met", count >= _DW_MIN_WORDS);

    const save = document.getElementById("dw-save");
    if (save) {
        const enable = count >= _DW_MIN_WORDS;
        save.disabled = !enable;
        save.setAttribute("aria-disabled", String(!enable));
    }

    // Suggest pill: visible only when body has 20+ words AND title is empty.
    const pill = document.getElementById("dw-suggest-pill");
    if (pill) {
        const titleEmpty = !((_dwState.title || "").trim());
        const showPill = count >= 20 && titleEmpty;
        pill.classList.toggle("is-hidden", !showPill);
    }
}

/* ── Overflow / Back / Save ────────────────────────────────────── */

/* ── Overflow menu ─────────────────────────────────────────────── */

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

/* ── Suggest title (AI) ────────────────────────────────────────── */

async function _dwSuggestTitle() {
    const body = (_dwState.body || "").trim();
    if (body.split(/\s+/).filter(Boolean).length < 20) return;
    const pill = document.getElementById("dw-suggest-pill");
    if (pill) {
        pill.disabled = true;
        pill.setAttribute("aria-disabled", "true");
        pill.textContent = "✨ Thinking…";
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
            pill.textContent = "✨ Suggest";
        }
    }
}

function _dwBack() {
    _dwCleanupAndLeave();
    if (typeof openDiarySection === "function") openDiarySection("today");
}

function _dwCleanupAndLeave() {
    document.removeEventListener("keydown", _dwGlobalKeyHandler);
    // Stop any in-flight speech I/O so audio doesn't leak across screens.
    try { if (_dwRec && _dwListening) _dwRec.stop(); } catch (_) {}
    _dwListening = false;
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    _dwSpeaking = false;
    const view = document.getElementById("diary-view");
    if (view) view.classList.remove("dw-active");
}

async function _dwSave() {
    const today = new Date().toISOString().slice(0, 10);
    const title = (_dwState.title || "").trim();
    const body  = (_dwState.body  || "").trim();
    if (!body) return;

    // Combine title + body for the existing schema (content + entry_date).
    const content = title ? `# ${title}\n\n${body}` : body;

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
        photos: _dwState.photos.map(p => ({ id: p.id, name: p.name, url: p.url })),
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
        setTimeout(() => {
            _dwCleanupAndLeave();
            if (typeof openDiarySection === "function") openDiarySection("today");
        }, 700);
    } catch (err) {
        _dwToast("Couldn't save. Try again.", true);
        if (save) save.disabled = false;
    }
}

/* ── Toast ─────────────────────────────────────────────────────── */

function _dwToast(msg, isError) {
    const t = document.getElementById("dw-toast");
    if (!t) return;
    t.textContent = msg;
    t.classList.toggle("is-error", !!isError);
    t.classList.add("is-show");
    clearTimeout(_dwToast._h);
    _dwToast._h = setTimeout(() => t.classList.remove("is-show"), 2200);
}

/* ── Speak (STT) / Listen (TTS) — Web Speech API ───────────────── */
// Self-contained implementation using window.SpeechRecognition + SpeechSynthesis
// because the legacy ai-assistant-stt.js / -tts.js files are syntax-broken.

let _dwRec = null;       // SpeechRecognition instance
let _dwListening = false;
let _dwSpeaking = false;

function _dwGetRec() {
    if (_dwRec) return _dwRec;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.lang = "en-US";
    r.continuous = true;
    r.interimResults = false;
    r.onresult = (e) => {
        const ta = document.getElementById("dw-body");
        if (!ta) return;
        let added = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) added += e.results[i][0].transcript + " ";
        }
        if (!added) return;
        const start = ta.selectionStart || ta.value.length;
        const end   = ta.selectionEnd   || ta.value.length;
        ta.value = ta.value.slice(0, start) + added + ta.value.slice(end);
        const caret = start + added.length;
        ta.setSelectionRange(caret, caret);
        _dwState.body = ta.value;
        _dwUpdateProgress();
    };
    r.onend = () => {
        _dwListening = false;
        _dwReflectSpeakBtn();
    };
    r.onerror = (e) => {
        _dwListening = false;
        _dwReflectSpeakBtn();
        if (e && e.error === "not-allowed") _dwToast("Mic permission needed.", true);
    };
    _dwRec = r;
    return r;
}

function _dwReflectSpeakBtn() {
    const btn = document.getElementById("dw-speak-btn");
    if (!btn) return;
    btn.textContent = _dwListening ? "⏺" : "🎤";
    btn.title = _dwListening ? "Stop dictation" : "Speak — dictate into the page";
}
function _dwReflectListenBtn() {
    const btn = document.getElementById("dw-listen-btn");
    if (!btn) return;
    btn.textContent = _dwSpeaking ? "⏸" : "🔊";
    btn.title = _dwSpeaking ? "Stop reading" : "Listen — read this page aloud";
}

function _dwToggleSpeak() {
    const rec = _dwGetRec();
    if (!rec) {
        _dwToast("Speech input isn't supported in this browser.", true);
        return;
    }
    if (_dwListening) {
        try { rec.stop(); } catch (_) {}
        _dwListening = false;
        _dwReflectSpeakBtn();
        return;
    }
    try {
        rec.start();
        _dwListening = true;
        _dwReflectSpeakBtn();
    } catch (err) {
        _dwToast("Couldn't start the mic.", true);
    }
}

function _dwToggleListen() {
    const synth = window.speechSynthesis;
    if (!synth) {
        _dwToast("Speech output isn't supported in this browser.", true);
        return;
    }
    if (_dwSpeaking) {
        synth.cancel();
        _dwSpeaking = false;
        _dwReflectListenBtn();
        return;
    }
    const text = (
        (_dwState.title ? _dwState.title + ". " : "") +
        (_dwState.body || "")
    ).trim();
    if (!text) {
        _dwToast("Nothing to read yet.", false);
        return;
    }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = 0.95;
    u.onend   = () => { _dwSpeaking = false; _dwReflectListenBtn(); };
    u.onerror = () => { _dwSpeaking = false; _dwReflectListenBtn(); };
    synth.cancel();
    synth.speak(u);
    _dwSpeaking = true;
    _dwReflectListenBtn();
}

/* ── Expose mood map to diary-write (read by footer renderer) ──── */
// diary.js defines _DH_MOODS as a top-level const. Re-publish on window
// for cross-file access (vanilla, no modules).
if (typeof _DH_MOODS !== "undefined") { window._DH_MOODS = _DH_MOODS; }
