/* ================================================================
   FeedScreen.jsx — Character feeding using owned inventory food items
   Section: Shop (Island)
   Dependencies: IslandMain.jsx (apiFetchJSON, escapeHtml, _CHAR_EMOJI)
   API endpoints: GET /api/island/inventory?category=food,
                  GET /api/island/care/{character_progress_id},
                  POST /api/island/care/feed
   ================================================================ */

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _ifdProgId   = null;  // character_progress_id
let _ifdState    = 'select'; // 'loading' | 'select' | 'feeding' | 'result' | 'empty'
let _ifdFoods    = [];    // inventory food items
let _ifdSelected = null;  // selected inventory item
let _ifdCareData = null;  // current gauges
let _ifdResult   = null;

// ─── Entry ──────────────────────────────────────────────────────

/** @tag SHOP */
async function openFeedScreen(charProgressId) {
    _ifdProgId   = charProgressId;
    _ifdState    = 'loading';
    _ifdSelected = null;
    _ifdResult   = null;
    _ifdRenderLoading();

    try {
        const [invData, careData] = await Promise.all([
            apiFetchJSON('/api/island/inventory?category=food'),
            apiFetchJSON(`/api/island/care/${charProgressId}`),
        ]);
        _ifdFoods    = (invData.items || []).filter(i => i.quantity > 0);
        _ifdCareData = careData;
        _ifdState    = _ifdFoods.length ? 'select' : 'empty';
    } catch (e) {
        _ifdFoods    = [];
        _ifdCareData = null;
        _ifdState    = 'empty';
    }

    _ifdRender();
}

// ─── Render ─────────────────────────────────────────────────────

/** @tag SHOP */
function _ifdRenderLoading() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (!wrap) return;
    wrap.innerHTML = `
        <div class="ifd-screen" id="ifd-screen">
            <button class="ifd-back-btn" onclick="_ifdClose()" aria-label="Back">
                <i data-lucide="arrow-left"></i>
            </button>
            <div class="ifd-loading">
                <div class="ils-dots">
                    <span class="ils-dot" style="--d:0s"></span>
                    <span class="ils-dot" style="--d:0.2s"></span>
                    <span class="ils-dot" style="--d:0.4s"></span>
                </div>
            </div>
        </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag SHOP */
function _ifdRender() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (!wrap) return;

    let inner = '';
    if (_ifdState === 'empty')   inner = _ifdEmptyHTML();
    else if (_ifdState === 'result') inner = _ifdResultHTML();
    else inner = _ifdSelectHTML();

    wrap.innerHTML = `
        <div class="ifd-screen" id="ifd-screen">
            <button class="ifd-back-btn" onclick="_ifdClose()" aria-label="Back">
                <i data-lucide="arrow-left"></i>
            </button>
            ${inner}
        </div>`;

    if (typeof lucide !== 'undefined') lucide.createIcons();
    _ifdAttachEsc();
}

/** @tag SHOP */
function _ifdSelectHTML() {
    const c     = _ifdCareData || {};
    const prog  = c.progress   || {};
    const emoji = (_CHAR_EMOJI && prog.character_id && _CHAR_EMOJI[prog.character_id]) || '🐾';
    const name  = escapeHtml(prog.nickname || prog.character_name || 'Character');
    const hunger = c.hunger    ?? prog.hunger    ?? 0;
    const happy  = c.happiness ?? prog.happiness ?? 0;

    const foodCards = _ifdFoods.map(item => {
        const sel   = _ifdSelected?.id === item.id ? 'ifd-food-card--selected' : '';
        const icon  = item.item_type === 'food' ? 'utensils' : 'package';
        return `
            <button class="ifd-food-card ${sel}" onclick="_ifdPickFood(${item.id})" aria-pressed="${_ifdSelected?.id === item.id}">
                <i data-lucide="${icon}" class="ifd-food-icon"></i>
                <span class="ifd-food-name">${escapeHtml(item.name)}</span>
                <span class="ifd-food-stats">×${item.quantity}</span>
            </button>`;
    }).join('');

    const feeding = _ifdState === 'feeding';
    const feedDisabled = !_ifdSelected || feeding ? 'disabled' : '';

    return `
        <div class="ifd-char-preview">
            <span class="ifd-char-emoji">${emoji}</span>
            <span class="ifd-char-name">${name}</span>
        </div>
        <div class="ifd-hud">
            <div class="ifd-gauge-row">
                <span class="ifd-gauge-label"><i data-lucide="utensils"></i> Hunger</span>
                <div class="ifd-gauge-track">
                    <div class="ifd-gauge-fill ifd-gauge-fill--hunger" style="width:${Math.min(hunger,100)}%"></div>
                </div>
                <span class="ifd-gauge-pct">${hunger}%</span>
            </div>
            <div class="ifd-gauge-row">
                <span class="ifd-gauge-label"><i data-lucide="heart"></i> Mood</span>
                <div class="ifd-gauge-track">
                    <div class="ifd-gauge-fill ifd-gauge-fill--happiness" style="width:${Math.min(happy,100)}%"></div>
                </div>
                <span class="ifd-gauge-pct">${happy}%</span>
            </div>
        </div>
        <div class="ifd-tray">
            <p class="ifd-tray-label">Choose a food</p>
            <div class="ifd-food-grid">${foodCards}</div>
        </div>
        <button class="ifd-feed-btn ${feedDisabled ? 'ifd-feed-btn--disabled' : ''}" ${feedDisabled}
                onclick="_ifdStartFeed()">
            <i data-lucide="${feeding ? 'loader-2' : 'gift'}"></i>
            ${feeding ? 'Feeding…' : 'Feed'}
        </button>`;
}

/** @tag SHOP */
function _ifdEmptyHTML() {
    return `
        <div class="ifd-empty">
            <i data-lucide="package-open" class="ifd-empty-icon"></i>
            <p class="ifd-empty-title">No food in inventory</p>
            <p class="ifd-empty-sub">Buy food from the shop to feed your character.</p>
            <button class="ifd-feed-btn" onclick="_ifdClose()">
                <i data-lucide="arrow-left"></i> Back
            </button>
        </div>`;
}

/** @tag SHOP */
function _ifdResultHTML() {
    const r     = _ifdResult || {};
    const ok    = r.ok !== false;
    const emoji = (() => {
        const c = _ifdCareData?.progress || {};
        return (_CHAR_EMOJI && c.character_id && _CHAR_EMOJI[c.character_id]) || '🐾';
    })();

    return `
        <div class="ifd-result ${ok ? 'ifd-result--ok' : 'ifd-result--err'}">
            <span class="ifd-result-emoji">${emoji}</span>
            <i data-lucide="${ok ? 'check-circle' : 'alert-circle'}" class="ifd-result-icon"></i>
            <p class="ifd-result-msg">${ok ? `Loved the ${escapeHtml(r.item_name || 'food')}!` : escapeHtml(r.detail || 'Something went wrong.')}</p>
            ${ok ? `<div class="ifd-result-xp">+${r.xp_gained ?? 0} XP</div>` : ''}
            <button class="ifd-feed-btn" onclick="_ifdClose()">
                <i data-lucide="arrow-left"></i> Back to island
            </button>
        </div>`;
}

// ─── Interactions ────────────────────────────────────────────────

/** @tag SHOP */
function _ifdPickFood(inventoryId) {
    _ifdSelected = _ifdFoods.find(f => f.id === inventoryId) || null;
    _ifdRender();
}

/** @tag SHOP */
async function _ifdStartFeed() {
    if (!_ifdSelected || !_ifdProgId || _ifdState === 'feeding') return;
    _ifdState = 'feeding';
    _ifdRender();

    try {
        const data = await apiFetchJSON('/api/island/care/feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character_progress_id: _ifdProgId,
                inventory_id: _ifdSelected.id,
            }),
        });
        _ifdResult = data;
    } catch (e) {
        _ifdResult = { ok: false, detail: e.message || 'Feed failed.' };
    }

    _ifdState = 'result';
    _ifdRender();
}

// ─── Close / ESC ─────────────────────────────────────────────────

/** @tag SHOP */
function _ifdClose() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (wrap) wrap.innerHTML = '';
    _ifdProgId   = null;
    _ifdState    = 'select';
    _ifdSelected = null;
    _ifdResult   = null;
    _ifdFoods    = [];
    _ifdCareData = null;
}

/** @tag SHOP */
function _ifdAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        if (document.getElementById('ifd-screen')) {
            document.removeEventListener('keydown', fn);
            _ifdClose();
        }
    };
    document.addEventListener('keydown', fn);
}
