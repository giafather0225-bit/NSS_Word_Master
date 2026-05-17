/* ================================================================
   diary-write.js — GIA's Diary · Write screen: config, state, icon helpers,
                    entry point, event binding, mutators, style apply,
                    sticker insert, progress, navigation, toast
   Section: Diary
   Dependencies: diary.js (escapeHtml, openDiarySection, _DH_MOODS)
   Split modules: diary-write-html.js  diary-write-media.js  diary-write-save.js
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

// 1 = "any non-empty body". Lowered from 15 (spec) → 5 → 1 because the
// 5-word threshold still tripped short journal lines (and Korean entries
// where word count is harder to predict).
const _DW_MIN_WORDS = 1;

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

/* ── Icon helpers ──────────────────────────────────────────────── */

function _dwIcon(name, size) {
    const px = size || 14;
    return `<i data-lucide="${name}" width="${px}" height="${px}"></i>`;
}
function _dwRefreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
        window.lucide.createIcons();
    }
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

    // Reset state on every entry — Journal and Free Write are separate
    // entries, and we don't want stale text from a previous session leaking
    // into a new page.
    _dwState.mode      = mode === "free" ? "free" : "journal";
    _dwState.mood      = "happy";
    _dwState.title     = "";
    _dwState.body      = "";
    _dwState.photos    = [];
    _dwState.prompt    = "";
    _dwState.style     = { font: "caveat", textSize: "m", textColor: "default", bgMood: "default" };
    _dwState.stkCat    = 0;
    _dwState.tipIdx    = 0;
    _dwState.moodOpen  = false;

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
                    ${_dwMoodTopHTML()}
                    <input class="dw-title-input" id="dw-title"
                           placeholder="Give this page a title…"
                           maxlength="80" autocomplete="off"
                           oninput="_dwOnTitleInput()"/>
                    <div class="dw-prompt-quote" id="dw-prompt-quote"></div>
                    <textarea class="dw-body-input" id="dw-body"
                              placeholder="Start writing here…"
                              oninput="_dwUpdateProgress()"></textarea>
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

/** Title input handler — wired via oninline so dynamic re-renders keep working. */
function _dwOnTitleInput() {
    const t = document.getElementById("dw-title");
    if (!t) return;
    _dwState.title = t.value;
    _dwUpdateProgress();
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

/* ── Progress + Save gating ────────────────────────────────────── */

function _dwUpdateProgress() {
    // Read directly from the live textarea so a missed `input` event
    // can't leave Save permanently disabled.
    const ta = document.getElementById("dw-body");
    if (ta) _dwState.body = ta.value;
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
        // Block Save while any photo is mid-upload — otherwise we'd persist
        // a transient blob: URL into the backend snapshot and the image
        // would 404 on next reload.
        const uploading = _dwState.photos.some(p => p.uploading);
        const enable = count >= _DW_MIN_WORDS && !uploading;
        save.disabled = !enable;
        save.setAttribute("aria-disabled", String(!enable));
        save.title = uploading ? "Uploading photos…" : "";
    }
}

/* ── Navigation ────────────────────────────────────────────────── */

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

/* ── Expose mood map for cross-file access ─────────────────────── */
// diary.js defines _DH_MOODS as a top-level const. Re-publish on window
// for cross-file access (vanilla, no modules).
if (typeof _DH_MOODS !== "undefined") { window._DH_MOODS = _DH_MOODS; }
