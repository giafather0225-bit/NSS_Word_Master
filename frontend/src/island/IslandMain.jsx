/* ================================================================
   IslandMain.jsx — Island main screen: map view with 5 zones,
                    top-bar currency, zoom, day/night sky.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), reward-shop.js
                 (_showShopToast), island.config.js (window globals via bundle)
   API endpoints: GET /api/island/status, GET /api/xp/summary
   ================================================================ */

// ─── Zone layout metadata (col/row for CSS grid) ───────────────
const _ZONE_META = {
    forest:  { label: 'Forest',  icon: '🌳', varPfx: 'english', col: 1, row: 2 },
    ocean:   { label: 'Ocean',   icon: '🌊', varPfx: 'math',    col: 3, row: 2 },
    savanna: { label: 'Savanna', icon: '🦁', varPfx: 'diary',   col: 2, row: 3 },
    space:   { label: 'Space',   icon: '🚀', varPfx: 'rewards', col: 2, row: 1 },
    legend:  { label: 'Legend',  icon: '✨', varPfx: 'review',  col: 2, row: 2 },
};

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _islandStatus = null;
let _islandStreak = 0;
let _islandZoom   = 1.0;
const _ZOOM_MIN   = 0.65;
const _ZOOM_MAX   = 2.0;
const _ZOOM_STEP  = 0.2;

// ─── Open / Close ───────────────────────────────────────────────

/** @tag SHOP */
function openIslandMain() {
    const el = document.getElementById('island-overlay');
    if (!el) return;
    el.classList.remove('hidden');
    _islandZoom = 1.0;
    _renderIslandLoading();
    Promise.all([
        fetch('/api/island/status').then(r => r.json()),
        fetch('/api/xp/summary').then(r => r.json()),
    ]).then(([statusData, xpData]) => {
        _islandStatus = statusData;
        _islandStreak = xpData.streak_days ?? 0;
        _renderIslandScreen();
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }).catch(() => _renderIslandError());
}

/** @tag SHOP */
function closeIslandMain() {
    const el = document.getElementById('island-overlay');
    if (el) el.classList.add('hidden');
}

// ─── Loading / Error states ─────────────────────────────────────

/** @tag SHOP */
function _renderIslandLoading() {
    const el = document.getElementById('island-overlay');
    if (!el) return;
    el.innerHTML = `
        <div class="isl-state-screen">
            <div class="isl-loading-ship">⛵</div>
            <div class="isl-state-text">Sailing to your island...</div>
        </div>`;
}

/** @tag SHOP */
function _renderIslandError() {
    const el = document.getElementById('island-overlay');
    if (!el) return;
    el.innerHTML = `
        <div class="isl-state-screen">
            <div class="isl-state-icon"><i data-lucide="wifi-off"></i></div>
            <div class="isl-state-text">Could not reach your island.</div>
            <button class="isl-retry-btn" onclick="openIslandMain()">Try Again</button>
            <button class="isl-back-btn"  onclick="closeIslandMain()">← Back</button>
        </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Main render ────────────────────────────────────────────────

/** @tag SHOP */
function _renderIslandScreen() {
    const el = document.getElementById('island-overlay');
    if (!el || !_islandStatus) return;

    const currency  = _islandStatus.currency || {};
    const lumi      = currency.lumi       ?? 0;
    const legendLumi = currency.legend_lumi ?? 0;

    const zoneUnlock = {};
    (_islandStatus.zones || []).forEach(z => { zoneUnlock[z.zone] = z.is_unlocked; });

    const charsByZone = {};
    (_islandStatus.active_characters || []).forEach(c => {
        if (!charsByZone[c.zone]) charsByZone[c.zone] = [];
        charsByZone[c.zone].push(c);
    });

    const nightClass = _isDay() ? '' : ' isl-night';

    el.innerHTML = `
        <div class="isl-screen${nightClass}" id="isl-screen">
            ${_topBarHTML(lumi, legendLumi, _islandStreak)}
            <div class="isl-map-wrap" id="isl-map-wrap">
                <div class="isl-sky"></div>
                <div class="isl-map" id="isl-map" style="transform:scale(${_islandZoom})">
                    ${Object.entries(_ZONE_META).map(([z, m]) =>
                        _zoneHTML(z, m, zoneUnlock[z] ?? false, charsByZone[z] || [])
                    ).join('')}
                </div>
                <div class="isl-zoom-bar">
                    <button class="isl-zoom-btn" onclick="_islandZoomIn()"  aria-label="Zoom in">+</button>
                    <button class="isl-zoom-btn" onclick="_islandZoomOut()" aria-label="Zoom out">−</button>
                </div>
            </div>
        </div>`;

    _attachWheelPinch(document.getElementById('isl-map-wrap'));
}

// ─── Top bar ────────────────────────────────────────────────────

/** @tag SHOP */
function _topBarHTML(lumi, legendLumi, streak) {
    return `
        <div class="isl-topbar">
            <div class="isl-topbar-left">
                <span class="isl-cur" title="Lumi — tap for history" onclick="_openLumiLog()">
                    <span class="isl-cur-icon">💎</span>
                    <span class="isl-cur-val">${lumi.toLocaleString()}</span>
                </span>
                <span class="isl-cur">
                    <span class="isl-cur-icon">✨</span>
                    <span class="isl-cur-val">${legendLumi.toLocaleString()}</span>
                </span>
                <span class="isl-streak">
                    <i data-lucide="flame" class="isl-streak-ic"></i>
                    <span>${streak} day${streak === 1 ? '' : 's'}</span>
                </span>
            </div>
            <div class="isl-topbar-right">
                <button class="isl-topbar-btn" onclick="_openIslandInventory()" title="Inventory">
                    <i data-lucide="backpack"></i>
                </button>
                <button class="isl-topbar-btn" onclick="_openIslandCollection()" title="Collection">
                    <i data-lucide="book-open"></i>
                </button>
                <button class="isl-topbar-btn" onclick="openRewardShop()" title="Shop">
                    <i data-lucide="shopping-bag"></i>
                </button>
                <button class="isl-topbar-btn" onclick="closeIslandMain()" title="Back to Home">
                    <i data-lucide="x"></i>
                </button>
            </div>
        </div>`;
}

// ─── Zone cards ─────────────────────────────────────────────────

/** @tag SHOP */
function _zoneHTML(zone, meta, unlocked, chars) {
    const lockClass   = unlocked ? '' : ' isl-zone--locked';
    const clickAttr   = unlocked ? `onclick="_islandZoneClick('${zone}')"` : '';
    const roleAttr    = unlocked ? 'role="button" tabindex="0"' : 'tabindex="-1"';
    const ariaLabel   = `${meta.label} zone${unlocked ? '' : ' (locked)'}`;

    const charsHTML = (unlocked && chars.length)
        ? `<div class="isl-zone-chars">${chars.map(_charTokenHTML).join('')}</div>`
        : '';
    const lockHTML  = unlocked ? '' :
        `<div class="isl-zone-lock"><i data-lucide="lock"></i></div>`;

    return `
        <div class="isl-zone isl-zone--${zone}${lockClass}"
             style="grid-column:${meta.col};grid-row:${meta.row}"
             ${clickAttr} ${roleAttr} aria-label="${ariaLabel}">
            <div class="isl-zone-body">
                <div class="isl-zone-icon">${meta.icon}</div>
                <div class="isl-zone-label">${meta.label}</div>
                ${charsHTML}
            </div>
            ${lockHTML}
        </div>`;
}

/** @tag SHOP */
function _charTokenHTML(char) {
    const lowGauge = (char.hunger ?? 100) < 20 || (char.happiness ?? 100) < 20;
    const badge    = lowGauge
        ? '<span class="isl-char-badge isl-char-badge--warn">❗</span>'
        : '';
    const name = escapeHtml((char.nickname || char.name).substring(0, 7));
    return `
        <div class="isl-char-token" title="${name}">
            <div class="isl-char-dot"></div>
            <span class="isl-char-name">${name}</span>${badge}
        </div>`;
}

// ─── Zone click ─────────────────────────────────────────────────

/** Navigate to zone detail. @tag SHOP */
function _islandZoneClick(zone) {
    // Zone detail screen — future implementation.
    const label = _ZONE_META[zone]?.label || zone;
    if (typeof _showShopToast === 'function') {
        _showShopToast(`${label} zone — coming soon!`);
    }
}

// ─── Zoom ───────────────────────────────────────────────────────

/** @tag SHOP */
function _islandZoomIn()  { _islandZoom = Math.min(_ZOOM_MAX, _islandZoom + _ZOOM_STEP); _applyZoom(); }
/** @tag SHOP */
function _islandZoomOut() { _islandZoom = Math.max(_ZOOM_MIN, _islandZoom - _ZOOM_STEP); _applyZoom(); }

/** @tag SHOP */
function _applyZoom() {
    const map = document.getElementById('isl-map');
    if (map) map.style.transform = `scale(${_islandZoom})`;
}

/** Trackpad pinch → wheel + ctrlKey. @tag SHOP */
function _attachWheelPinch(el) {
    if (!el) return;
    el.addEventListener('wheel', e => {
        if (!e.ctrlKey) return;
        e.preventDefault();
        const delta = e.deltaY > 0 ? -_ZOOM_STEP / 2 : _ZOOM_STEP / 2;
        _islandZoom = Math.max(_ZOOM_MIN, Math.min(_ZOOM_MAX, _islandZoom + delta));
        _applyZoom();
    }, { passive: false });
}

// ─── Helpers ────────────────────────────────────────────────────

/** True between 06:00–18:00 local time. @tag SHOP */
function _isDay() { const h = new Date().getHours(); return h >= 6 && h < 18; }

/** @tag SHOP */
function _openLumiLog()          { /* Lumi log — future screen */ }
function _openIslandInventory()  { /* Inventory — future screen */ }
function _openIslandCollection() { /* Collection — future screen */ }

// ─── Home card loader ───────────────────────────────────────────

/** Populate island home card with live data. @tag HOME_DASHBOARD */
async function _loadIslandCard() {
    const footer   = document.getElementById('island-home-footer');
    const charEl   = document.getElementById('island-home-chars');
    const lumiEl   = document.getElementById('island-home-lumi');
    const cardEl   = document.getElementById('island-home-card');
    if (cardEl) cardEl.onclick = openIslandMain;
    try {
        const d = await apiFetchJSON('/api/island/status');
        const cnt  = (d.active_characters || []).length + (d.completed_count || 0);
        const lumi = d.currency?.lumi ?? 0;
        if (charEl) charEl.textContent = `${cnt} character${cnt === 1 ? '' : 's'}`;
        if (lumiEl) lumiEl.textContent = `💎 ${lumi.toLocaleString()}`;
    } catch (_) {
        if (charEl) charEl.textContent = 'Your island awaits';
        if (lumiEl) lumiEl.textContent = '';
    }
}
