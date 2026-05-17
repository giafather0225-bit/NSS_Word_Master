/* ================================================================
   diary-write-html.js — Diary Write screen · HTML builders + style resolvers
   Section: Diary
   Dependencies: diary-write.js (_dwState, _DW_*, _dwIcon, _dwRefreshIcons)
   API endpoints: none
   ================================================================ */

/* ── Style resolvers ───────────────────────────────────────────── */

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
    return `repeating-linear-gradient(180deg, ${bg.fill} 0 31px, ${bg.lined} 31px 32px)`;
}

/* ── HTML builders ─────────────────────────────────────────────── */

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
    const tiles = photos.map(p => {
        const rawUrl  = p.thumb_url || p.url || "";
        const tileUrl = (rawUrl && /^\/api\//.test(rawUrl)) ? encodeURI(rawUrl) : "";
        const bg = tileUrl ? `background-image:url('${tileUrl}');` : "";
        return `
        <div class="dw-photo" style="${bg}" data-pid="${escapeHtml(p.id)}">
            <button class="dw-photo-x" type="button" aria-label="Remove photo"
                    data-remove-pid="${escapeHtml(p.id)}">×</button>
        </div>`;
    }).join("");
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

/** Mood pill row — top of paper (above title). Tapping opens picker. */
function _dwMoodTopHTML() {
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
        <div class="dw-mood-top" data-mood-picker>
            <span class="dw-mood-top-label">Mood</span>
            <button class="dw-mood-pill" type="button" onclick="_dwToggleMood()"
                    aria-haspopup="dialog" aria-expanded="false">
                <span class="dw-mood-dot" id="dw-mood-dot" style="background:${dot};"></span>
                <span id="dw-mood-label">${escapeHtml(_dwState.mood)}</span>
            </button>
            <div class="dw-mood-popover is-top is-hidden" id="dw-mood-popover"
                 role="dialog" aria-label="Pick a mood">
                ${opts}
            </div>
        </div>`;
}

function _dwFooterHTML() {
    return `
        <div class="dw-footer">
            <div class="dw-progress" id="dw-progress">
                <div class="dw-progress-bar"><div class="dw-progress-fill" id="dw-progress-fill" style="width:0%;"></div></div>
                <span><b id="dw-wc">0</b> / ${_DW_MIN_WORDS}</span>
            </div>
            <button class="dw-voice-btn" id="dw-speak-btn" type="button"
                    title="Speak — dictate into the page" aria-label="Speak"
                    onclick="_dwToggleSpeak()"><i data-lucide="mic" style="width:16px;height:16px;stroke-width:1.5"></i></button>
            <button class="dw-voice-btn" id="dw-listen-btn" type="button"
                    title="Listen — read this page aloud" aria-label="Listen"
                    onclick="_dwToggleListen()"><i data-lucide="volume-2" style="width:16px;height:16px;stroke-width:1.5"></i></button>
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
