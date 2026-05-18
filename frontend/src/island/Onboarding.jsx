/* ================================================================
   Onboarding.jsx — Island first-run onboarding:
     slides → 4-round zone+character sequential pick → name → adopt all.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/characters,
                  POST /api/island/character/adopt  (called ×4),
                  POST /api/island/onboarding/complete
   ================================================================ */

// ─── Zone metadata ─────────────────────────────────────────────
const _OB_ZONES = {
    forest:  { label: 'Forest',  desc: 'English — grow a forest friend',     lucideIcon: 'tree-pine' },
    ocean:   { label: 'Ocean',   desc: 'Math — raise an ocean creature',      lucideIcon: 'waves'     },
    savanna: { label: 'Savanna', desc: 'Diary — raise a savanna companion',   lucideIcon: 'paw-print' },
    space:   { label: 'Space',   desc: 'Review — raise a space explorer',     lucideIcon: 'rocket'    },
};

const _OB_ZONE_ORDER = ['forest', 'ocean', 'savanna', 'space'];

const _OB_SLIDES = [
    { lucideIcon: 'star',      text: "Hi! I'm Lumi! This is Gia's Island!" },
    { lucideIcon: 'gem',       text: 'Study to earn Lumi and raise your characters!' },
    { lucideIcon: 'handshake', text: 'Ready to meet your island friends? Pick one from each zone!' },
];

const _OB_ROUND_LABELS = [
    'Choose your first companion',
    'A new zone has opened!',
    'Another zone appeared!',
    'Last one — complete your team!',
];

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _obSlide       = 0;           // 0-2 during slide phase
let _obPhase       = 'slides';    // 'slides' | 'rounds' | 'name' | 'saving'
let _obRound       = 0;           // 0-3: which zone-pick round
let _obSubStep     = 'zone';      // 'zone' | 'char'
let _obSelections  = [];          // [{zone, charId}] accumulated
let _obPickZone    = null;        // zone chosen in current round
let _obPickCharId  = null;        // char chosen in current round
let _obChars       = [];
let _obSaving      = false;

// ─── Open ──────────────────────────────────────────────────────

/** Start onboarding flow. @tag SHOP */
async function openIslandOnboarding() {
    _obSlide = 0; _obPhase = 'slides';
    _obRound = 0; _obSubStep = 'zone';
    _obSelections = []; _obPickZone = null; _obPickCharId = null;
    _obSaving = false;

    const el = document.getElementById('isl-onboarding');
    if (!el) return;
    el.classList.remove('hidden');
    _obRender(el);

    try {
        const data = await apiFetchJSON('/api/island/characters');
        _obChars = data.characters || data || [];
    } catch (_) {}
}

// ─── Master render ─────────────────────────────────────────────

/** @tag SHOP */
function _obRender(el) {
    if (!el) el = document.getElementById('isl-onboarding');
    if (!el) return;

    if      (_obPhase === 'slides') _obRenderSlide(el);
    else if (_obPhase === 'rounds') _obRenderRound(el);
    else if (_obPhase === 'name')   _obRenderName(el);
    else                            _obRenderSaving(el);

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Slides ────────────────────────────────────────────────────

/** @tag SHOP */
function _obRenderSlide(el) {
    const s    = _OB_SLIDES[_obSlide];
    const dots = _OB_SLIDES.map((_, i) =>
        `<div class="iob-dot${i === _obSlide ? ' iob-dot--active' : ''}"></div>`
    ).join('');
    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-slide">
                <div class="iob-slide-icon"><i data-lucide="${s.lucideIcon}"></i></div>
                <div class="iob-slide-text">${escapeHtml(s.text)}</div>
                <div class="iob-dots">${dots}</div>
                <button class="iob-next-btn" onclick="_obSlideNext()">
                    ${_obSlide < 2
                        ? 'Next <i data-lucide="arrow-right"></i>'
                        : 'Start <i data-lucide="arrow-right"></i>'}
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _obSlideNext() {
    if (_obSlide < 2) { _obSlide++; _obRender(); return; }
    _obPhase = 'rounds';
    _obRound = 0;
    _obSubStep = 'zone';
    _obPickZone = null;
    _obPickCharId = null;
    _obRender();
}

// ─── Round (zone + char pick × 4) ────────────────────────────

/** @tag SHOP */
function _obRenderRound(el) {
    if (_obSubStep === 'zone') _obRenderZonePick(el);
    else                       _obRenderCharPick(el);
}

/** Progress dots for 4 rounds. @tag SHOP */
function _obRoundProgress() {
    return `<div class="iob-round-progress">
        ${_OB_ZONE_ORDER.map((z, i) => {
            const done = i < _obRound;
            const active = i === _obRound;
            const sel = _obSelections[i];
            const cls = done ? 'done' : active ? 'active' : 'pending';
            return `<div class="iob-rp-step iob-rp-step--${cls}">
                <div class="iob-rp-dot">
                    ${done ? '<i data-lucide="check"></i>' : `<span>${i + 1}</span>`}
                </div>
                <div class="iob-rp-label">${done && sel ? _OB_ZONES[sel.zone].label : _OB_ZONES[z].label}</div>
            </div>`;
        }).join('<div class="iob-rp-line"></div>')}
    </div>`;
}

/** Zone pick sub-step. @tag SHOP */
function _obRenderZonePick(el) {
    // zones already picked
    const pickedZones = new Set(_obSelections.map(s => s.zone));
    const remaining   = _OB_ZONE_ORDER.filter(z => !pickedZones.has(z));

    const zoneCards = _OB_ZONE_ORDER.map(zone => {
        const z    = _OB_ZONES[zone];
        const done = pickedZones.has(zone);
        const sel  = _obPickZone === zone;
        const isNew = !done && _obRound > 0 && remaining.indexOf(zone) >= 0;

        if (done) {
            const whoSel = _obSelections.find(s => s.zone === zone);
            const char   = _obChars.find(c => c.id === whoSel?.charId);
            return `<div class="iob-zone-card iob-zone-card--done">
                <div class="iob-zone-check"><i data-lucide="check-circle-2"></i></div>
                <div class="iob-zone-emoji"><i data-lucide="${z.lucideIcon}"></i></div>
                <div class="iob-zone-name">${z.label}</div>
                <div class="iob-zone-desc">${escapeHtml(char?.name || '—')}</div>
            </div>`;
        }
        return `<div class="iob-zone-card${sel ? ' iob-zone-card--selected' : ''}${isNew ? ' iob-zone-card--new' : ''}"
                     onclick="_obPickZoneSelect('${zone}')">
            <div class="iob-zone-emoji"><i data-lucide="${z.lucideIcon}"></i></div>
            <div class="iob-zone-name">${z.label}</div>
            <div class="iob-zone-desc">${escapeHtml(z.desc)}</div>
        </div>`;
    }).join('');

    const banner = _obRound > 0
        ? `<div class="iob-unlock-banner">
               <i data-lucide="sparkles"></i>
               ${escapeHtml(_OB_ROUND_LABELS[_obRound])}
           </div>`
        : `<div class="iob-stage-title">${escapeHtml(_OB_ROUND_LABELS[0])}</div>`;

    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-stage">
                ${_obRoundProgress()}
                ${banner}
                <div class="iob-zone-grid">${zoneCards}</div>
                <button class="iob-next-btn${_obPickZone ? '' : ' disabled'}"
                        onclick="_obZoneConfirm()" ${_obPickZone ? '' : 'disabled'}>
                    Choose companion <i data-lucide="arrow-right"></i>
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _obPickZoneSelect(zone) {
    const pickedZones = new Set(_obSelections.map(s => s.zone));
    if (pickedZones.has(zone)) return;  // already done
    _obPickZone = zone;
    _obRender();
}

/** @tag SHOP */
function _obZoneConfirm() {
    if (!_obPickZone) return;
    _obSubStep = 'char';
    _obPickCharId = null;
    _obRender();
}

/** Character pick sub-step. @tag SHOP */
function _obRenderCharPick(el) {
    const z        = _OB_ZONES[_obPickZone] || {};
    const zoneChars = _obChars.filter(c => c.zone === _obPickZone);

    const charCards = zoneChars.length
        ? zoneChars.map(c => {
            let imgs = {};
            try { imgs = JSON.parse(c.images || '{}'); } catch (_) {}
            const rel = imgs['baby'] || imgs['mid_a'] || imgs['mid_b'] || imgs['final_a'] || imgs['final_b'];
            const visual = rel
                ? `<img class="iob-char-img" src="/static/img/island/${rel}" alt="${escapeHtml(c.name)}" onerror="this.style.display='none';this.nextElementSibling.style.display=''"><i data-lucide="${z.lucideIcon || 'smile'}" style="display:none"></i>`
                : `<i data-lucide="${z.lucideIcon || 'smile'}"></i>`;
            return `
            <div class="iob-char-card${_obPickCharId === c.id ? ' iob-char-card--selected' : ''}"
                 onclick="_obSelectChar(${c.id})">
                <div class="iob-char-sil">${visual}</div>
                <div class="iob-char-name">${escapeHtml(c.name)}</div>
            </div>`;
        }).join('')
        : `<div class="iob-empty">No characters found.</div>`;

    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-stage">
                ${_obRoundProgress()}
                <div class="iob-char-zone-label">
                    <i data-lucide="${z.lucideIcon}"></i>
                    <span>${z.label} Zone</span>
                </div>
                <div class="iob-stage-title">Pick your ${z.label.toLowerCase()} companion</div>
                <div class="iob-char-grid">${charCards}</div>
                <div class="iob-char-row">
                    <button class="iob-back-link" onclick="_obCharBack()">
                        <i data-lucide="arrow-left"></i> Back
                    </button>
                    <button class="iob-next-btn${_obPickCharId ? '' : ' disabled'}"
                            onclick="_obCharConfirm()" ${_obPickCharId ? '' : 'disabled'}>
                        ${_obRound < 3 ? 'Next zone <i data-lucide="arrow-right"></i>' : 'Almost done! <i data-lucide="arrow-right"></i>'}
                    </button>
                </div>
            </div>
        </div>`;
}

/** @tag SHOP */
function _obSelectChar(id) {
    _obPickCharId = id;
    _obRender();
}

/** @tag SHOP */
function _obCharBack() {
    _obSubStep = 'zone';
    _obPickZone = null;
    _obPickCharId = null;
    _obRender();
}

/** @tag SHOP */
function _obCharConfirm() {
    if (!_obPickCharId || !_obPickZone) return;
    _obSelections.push({ zone: _obPickZone, charId: _obPickCharId });
    _obPickZone    = null;
    _obPickCharId  = null;
    _obRound++;

    if (_obRound >= 4) {
        // All 4 zones picked → name screen for first character
        _obPhase = 'name';
    } else {
        _obSubStep = 'zone';
    }
    _obRender();
}

// ─── Name screen ───────────────────────────────────────────────

/** @tag SHOP */
function _obRenderName(el) {
    const first    = _obSelections[0];
    const char     = _obChars.find(c => c.id === first?.charId) || {};
    const defName  = escapeHtml(char.name || 'Friend');

    const summaryCards = _obSelections.map(sel => {
        const z = _OB_ZONES[sel.zone] || {};
        const c = _obChars.find(ch => ch.id === sel.charId) || {};
        return `<div class="iob-summary-card">
            <i data-lucide="${z.lucideIcon || 'smile'}"></i>
            <span>${escapeHtml(c.name || '—')}</span>
        </div>`;
    }).join('');

    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-stage iob-stage--name">
                <div class="iob-stage-title">Your island team is ready!</div>
                <div class="iob-summary-row">${summaryCards}</div>
                <div class="iob-name-section">
                    <div class="iob-name-label">Give your first companion a nickname</div>
                    <div class="iob-name-hint">Max 8 characters — cannot be changed later.</div>
                    <input id="iob-name-input" class="iob-name-input"
                           type="text" maxlength="8"
                           placeholder="${defName}"
                           oninput="_obNameInput(this.value)"
                           autocomplete="off" autocorrect="off" spellcheck="false" />
                    <div class="iob-name-count"><span id="iob-name-len">0</span> / 8</div>
                </div>
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

// ─── Saving ────────────────────────────────────────────────────

/** @tag SHOP */
function _obRenderSaving(el) {
    el.innerHTML = `
        <div class="iob-screen">
            <div class="iob-slide">
                <div class="iob-slide-icon"><i data-lucide="loader"></i></div>
                <div class="iob-slide-text">Setting up your island…</div>
            </div>
        </div>`;
}

// ─── Confirm: adopt all 4 characters ──────────────────────────

/** @tag SHOP */
async function _obConfirm() {
    if (_obSaving) return;
    _obSaving = true;

    const input       = document.getElementById('iob-name-input');
    const firstChar   = _obChars.find(c => c.id === _obSelections[0]?.charId) || {};
    const firstNick   = (input?.value?.trim() || firstChar.name || 'Friend').substring(0, 8);

    _obPhase = 'saving';
    _obRender();

    try {
        // Adopt each character in order; first gets the custom nickname.
        // Idempotent: if a character was already adopted (e.g. from a partial retry),
        // the 400 "already adopted" response is treated as success.
        for (let i = 0; i < _obSelections.length; i++) {
            const sel  = _obSelections[i];
            const char = _obChars.find(c => c.id === sel.charId) || {};
            try {
                await apiFetchJSON('/api/island/character/adopt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        character_id: sel.charId,
                        nickname: i === 0 ? firstNick : char.name || 'Friend',
                    }),
                });
            } catch (adoptErr) {
                // Skip if already adopted (idempotent retry safety).
                if (String(adoptErr.message).toLowerCase().includes('already')) continue;
                throw adoptErr; // re-raise any other error
            }
        }

        // Mark onboarding complete.
        await apiFetchJSON('/api/island/onboarding/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });

        // Hide and open island.
        const el = document.getElementById('isl-onboarding');
        if (el) el.classList.add('hidden');
        if (typeof _loadIslandCard === 'function') _loadIslandCard();
        if (typeof openIslandMain === 'function') openIslandMain();
    } catch (err) {
        _obSaving = false;
        _obPhase = 'name';
        _obRender();
        if (typeof _showShopToast === 'function')
            _showShopToast('Could not save. Please try again.', true);
    }
}
