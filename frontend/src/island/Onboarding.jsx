/* ================================================================
   Onboarding.jsx — Island first-run onboarding: slides → zone
                    select → character select → naming → adopt.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/characters,
                  POST /api/island/character/adopt,
                  POST /api/island/onboarding/complete
   ================================================================ */

// ─── Zone metadata ─────────────────────────────────────────────
const _OB_ZONES = {
    forest:  { desc: 'English vocabulary — grow a forest friend',  emoji: '🌳' },
    ocean:   { desc: 'Math problems — raise an ocean creature',    emoji: '🌊' },
    savanna: { desc: 'Diary journaling — raise a savanna companion',emoji: '🦁' },
    space:   { desc: 'Spaced review — raise a space explorer',     emoji: '🚀' },
};

const _OB_SLIDES = [
    { icon: '🌟', text: "Hi! I'm Lumi! This is Gia's Island!" },
    { icon: '💎', text: 'Study to earn XP, convert to Lumi, and raise your characters!' },
    { icon: '🤝', text: 'Ready to meet your first friend?' },
];

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _obStep    = 0;
let _obZone    = null;
let _obCharId  = null;
let _obChars   = [];

// ─── Open ──────────────────────────────────────────────────────

/** Start onboarding flow. @tag SHOP */
async function openIslandOnboarding() {
    _obStep = 0; _obZone = null; _obCharId = null;
    const el = document.getElementById('isl-onboarding');
    if (!el) return;
    el.classList.remove('hidden');
    _obRender(el);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    try {
        const data = await apiFetchJSON('/api/island/characters');
        _obChars = data.characters || data || [];
    } catch (_) {}
}

// ─── Step router ───────────────────────────────────────────────

/** @tag SHOP */
function _obRender(el) {
    if (_obStep <= 2) _obRenderSlide(el);
    else if (_obStep === 3) _obRenderZones(el);
    else if (_obStep === 4) _obRenderChars(el);
    else _obRenderName(el);
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Slides ────────────────────────────────────────────────────

/** @tag SHOP */
function _obRenderSlide(el) {
    const s = _OB_SLIDES[_obStep];
    const dots = _OB_SLIDES.map((_, i) =>
        `<div class="iob-dot${i === _obStep ? ' iob-dot--active' : ''}"></div>`
    ).join('');
    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-slide">
                <div class="iob-slide-icon">${s.icon}</div>
                <div class="iob-slide-text">${escapeHtml(s.text)}</div>
                <div class="iob-dots">${dots}</div>
                <button class="iob-next-btn" onclick="_obNext()">
                    ${_obStep < 2 ? 'Next <i data-lucide="arrow-right"></i>' : 'Start <i data-lucide="arrow-right"></i>'}
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _obNext() {
    _obStep++;
    const el = document.getElementById('isl-onboarding');
    if (el) _obRender(el);
}

// ─── Zone selection ────────────────────────────────────────────

/** @tag SHOP */
function _obRenderZones(el) {
    const cards = Object.entries(_OB_ZONES).map(([zone, z]) => `
        <div class="iob-zone-card${_obZone === zone ? ' iob-zone-card--selected' : ''}"
             onclick="_obSelectZone('${zone}')">
            <div class="iob-zone-emoji">${z.emoji}</div>
            <div class="iob-zone-name">${zone.charAt(0).toUpperCase() + zone.slice(1)}</div>
            <div class="iob-zone-desc">${escapeHtml(z.desc)}</div>
        </div>`).join('');

    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-stage">
                <div class="iob-stage-title">Choose your starting zone</div>
                <div class="iob-zone-grid">${cards}</div>
                <button class="iob-next-btn${_obZone ? '' : ' disabled'}"
                        onclick="_obZoneConfirm()" ${_obZone ? '' : 'disabled'}>
                    Continue <i data-lucide="arrow-right"></i>
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _obSelectZone(zone) {
    _obZone = zone;
    const el = document.getElementById('isl-onboarding');
    if (el) _obRenderZones(el);
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag SHOP */
function _obZoneConfirm() {
    if (!_obZone) return;
    _obStep = 4;
    const el = document.getElementById('isl-onboarding');
    if (el) _obRender(el);
}

// ─── Character selection ───────────────────────────────────────

/** @tag SHOP */
function _obRenderChars(el) {
    const zoneChars = _obChars.filter(c => c.zone === _obZone);
    const meta = _OB_ZONES[_obZone] || {};
    const cards = zoneChars.length
        ? zoneChars.map(c => `
            <div class="iob-char-card${_obCharId === c.id ? ' iob-char-card--selected' : ''}"
                 onclick="_obSelectChar(${c.id})">
                <div class="iob-char-sil">${meta.emoji || '?'}</div>
                <div class="iob-char-name">${escapeHtml(c.name)}</div>
            </div>`).join('')
        : `<div class="iob-empty">No characters found for this zone.</div>`;

    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-stage">
                <button class="iob-back-link" onclick="_obBack()">
                    <i data-lucide="arrow-left"></i> Back
                </button>
                <div class="iob-stage-title">Choose your first companion</div>
                <div class="iob-char-grid">${cards}</div>
                <button class="iob-next-btn${_obCharId ? '' : ' disabled'}"
                        onclick="_obCharConfirm()" ${_obCharId ? '' : 'disabled'}>
                    Continue <i data-lucide="arrow-right"></i>
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _obSelectChar(id) {
    _obCharId = id;
    const el = document.getElementById('isl-onboarding');
    if (el) _obRenderChars(el);
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag SHOP */
function _obCharConfirm() {
    if (!_obCharId) return;
    _obStep = 5;
    const el = document.getElementById('isl-onboarding');
    if (el) _obRender(el);
}

// ─── Naming ────────────────────────────────────────────────────

/** @tag SHOP */
function _obRenderName(el) {
    const char = _obChars.find(c => c.id === _obCharId) || {};
    const defaultName = escapeHtml(char.name || 'Friend');
    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-stage iob-stage--name">
                <button class="iob-back-link" onclick="_obBack()">
                    <i data-lucide="arrow-left"></i> Back
                </button>
                <div class="iob-stage-title">Give your friend a name</div>
                <div class="iob-name-hint">Max 8 characters — this cannot be changed later.</div>
                <input id="iob-name-input" class="iob-name-input"
                       type="text" maxlength="8"
                       placeholder="${defaultName}"
                       oninput="_obNameInput(this.value)"
                       autocomplete="off" autocorrect="off" spellcheck="false" />
                <div class="iob-name-count"><span id="iob-name-len">0</span> / 8</div>
                <button class="iob-confirm-btn" onclick="_obConfirm()">
                    <i data-lucide="check"></i> Start my island!
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _obNameInput(val) {
    const len = document.getElementById('iob-name-len');
    if (len) len.textContent = val.length;
}

/** @tag SHOP */
function _obBack() {
    if (_obStep === 4) { _obStep = 3; _obZone = null; }
    else if (_obStep === 5) { _obStep = 4; _obCharId = null; }
    const el = document.getElementById('isl-onboarding');
    if (el) _obRender(el);
}

// ─── Confirm ───────────────────────────────────────────────────

/** @tag SHOP */
async function _obConfirm() {
    const input    = document.getElementById('iob-name-input');
    const char     = _obChars.find(c => c.id === _obCharId) || {};
    const nickname = (input?.value?.trim() || char.name || 'Friend').substring(0, 8);
    const btn = document.querySelector('.iob-confirm-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader"></i> Saving…'; }
    if (typeof lucide !== 'undefined') lucide.createIcons();

    try {
        await apiFetchJSON('/api/island/character/adopt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character_id: _obCharId, nickname }),
        });
        await apiFetchJSON('/api/island/onboarding/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });
        const el = document.getElementById('isl-onboarding');
        if (el) el.classList.add('hidden');
        if (typeof openIslandMain === 'function') openIslandMain();
    } catch (err) {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="check"></i> Start my island!'; }
        if (typeof _showShopToast === 'function') _showShopToast('Could not save. Please try again.', true);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}
