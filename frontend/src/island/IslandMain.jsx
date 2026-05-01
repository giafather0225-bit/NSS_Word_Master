/* ================================================================
   IslandMain.jsx — Island main hub: full-bleed map with 5 zone
                    hotspots, day/night mode, floating char bubbles.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), reward-shop.js
                 (_showShopToast), island.config.js
   API endpoints: GET /api/island/status, GET /api/xp/summary
   ================================================================ */

// ─── Zone metadata ──────────────────────────────────────────────
const _ZONE_META = {
    forest:  { label: 'Forest',  icon: '🌳', varPfx: 'english', subject: 'English' },
    ocean:   { label: 'Ocean',   icon: '🌊', varPfx: 'math',    subject: 'Math'    },
    savanna: { label: 'Savanna', icon: '🦁', varPfx: 'diary',   subject: 'Diary'   },
    space:   { label: 'Space',   icon: '🚀', varPfx: 'rewards', subject: 'Review'  },
    legend:  { label: 'Legend',  icon: '✨', varPfx: 'diary',   subject: 'All'     },
};

// CALIBRATED — do not change without re-checking against island_map.png (1376×768)
const _HOTSPOTS = {
    forest:  { left: '17%', top: '42%', size: 150 },
    space:   { left: '47%', top: '22%', size: 110 },
    legend:  { left: '50%', top: '50%', size: 130 },
    ocean:   { left: '88%', top: '60%', size: 130 },
    savanna: { left: '48%', top: '80%', size: 170 },
};

// Character emoji map — swap img src here when art ships
const _CHAR_EMOJI = {
    sprout: '🌱', clover: '🍀', mossy: '🪨', fernlie: '🌿', blossie: '🌸',
    axie: '🐠', finn: '🐟', delphi: '🐬', bubbles: '🐡', starla: '⭐',
    mane: '🐴', ellie: '🐘', leo: '🦁', zuri: '🦒', rhino: '🦏',
    lumie: '👽', twinkle: '✨', orbee: '🪐', nova: '☄️', cosmo: '🤖',
    dragon: '🐉', unicorn: '🦄', phoenix: '🔥', gumiho: '🦊', qilin: '🐲',
};

// Char bubble anchor positions near artwork features
const _CHAR_BUBBLES = [
    { zone: 'forest',  left: '12%', top: '56%', delay: '0s'   },
    { zone: 'ocean',   left: '80%', top: '52%', delay: '.5s'  },
    { zone: 'savanna', left: '62%', top: '88%', delay: '.8s'  },
    { zone: 'space',   left: '58%', top: '24%', delay: '1.2s' },
];

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _islandStatus  = null;
let _islandStreak  = 0;
let _nightSwitchTimer = null;

// ─── Open / Close ───────────────────────────────────────────────

/** @tag SHOP */
async function openIslandMain() {
    const el = document.getElementById('island-overlay');
    if (!el) return;

    try {
        const ob = await apiFetchJSON('/api/island/onboarding/status');
        if (ob.initialized === false) {
            if (typeof openIslandOnboarding === 'function') openIslandOnboarding();
            return;
        }
    } catch (_) { /* proceed even if check fails */ }

    const obEl = document.getElementById('isl-onboarding');
    if (obEl) { obEl.classList.add('hidden'); obEl.innerHTML = ''; }
    el.classList.remove('hidden');
    _renderIslandLoading();

    Promise.all([
        fetch('/api/island/status').then(r => r.json()),
        fetch('/api/xp/summary').then(r => r.json()),
    ]).then(([statusData, xpData]) => {
        _islandStatus = statusData;
        _islandStreak = xpData.streak_days ?? 0;
        _renderIslandMap();
        if (typeof lucide !== 'undefined') lucide.createIcons();
        if (typeof checkIslandNotifications === 'function') checkIslandNotifications();
        _scheduleNightSwitch();
    }).catch(() => _renderIslandError());
}

/** @tag SHOP */
function closeIslandMain() {
    const el = document.getElementById('island-overlay');
    if (el) el.classList.add('hidden');
    if (_nightSwitchTimer) { clearTimeout(_nightSwitchTimer); _nightSwitchTimer = null; }
}

// ─── Loading / Error ─────────────────────────────────────────────

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
            <button class="isl-back-btn"  onclick="closeIslandMain()">Back</button>
        </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Main render ─────────────────────────────────────────────────

/** @tag SHOP */
function _renderIslandMap() {
    const el = document.getElementById('island-overlay');
    if (!el || !_islandStatus) return;

    const currency   = _islandStatus.currency || {};
    const lumi       = currency.lumi        ?? 0;
    const legendLumi = currency.legend_lumi ?? 0;

    const zoneUnlock = {};
    (_islandStatus.zones || []).forEach(z => { zoneUnlock[z.zone] = z.is_unlocked; });

    const charsByZone = {};
    (_islandStatus.active_characters || []).forEach(c => {
        if (!charsByZone[c.zone]) charsByZone[c.zone] = [];
        charsByZone[c.zone].push(c);
    });

    const isNight     = !_isDay();
    const nightClass  = isNight ? ' gim-screen--night' : '';
    const legendLocked = !zoneUnlock['legend'];

    // Count completed zones for legend progress display
    const completedZones = ['forest','ocean','savanna','space'].filter(z => zoneUnlock[z]).length;

    el.innerHTML = `
        <div class="gim-screen${nightClass}" id="gim-screen">

            <!-- Full-bleed backdrop -->
            <img class="gim-backdrop${isNight ? ' gim-backdrop--night' : ''}"
                 src="/static/img/island/island_map.png"
                 alt="Gia's Island" draggable="false">

            ${isNight ? `
            <div class="gim-night-scrim"></div>
            <div class="gim-stars" id="gim-stars"></div>
            <div class="gim-sunmoon gim-night-moon">🌙</div>
            ` : `
            <div class="gim-sunmoon">☀️</div>
            `}

            <!-- Top bar -->
            <div class="gim-topbar${isNight ? ' gim-topbar--night' : ''}">
                <div class="gim-topbar-left">
                    <button class="gim-stat gim-stat--lumi" onclick="_openLumiLog()" title="Lumi history">
                        💎 <span>${lumi.toLocaleString()}</span>
                    </button>
                    <span class="gim-stat gim-stat--legend">
                        ✨ <span>${legendLumi.toLocaleString()}</span>
                    </span>
                    <span class="gim-stat gim-stat--streak">
                        🔥 <span>${_islandStreak} day${_islandStreak === 1 ? '' : 's'}</span>
                    </span>
                </div>
                <div class="gim-topbar-right">
                    <button class="gim-iconbtn" onclick="_openIslandInventory()" aria-label="Inventory" title="Inventory">
                        <i data-lucide="backpack"></i>
                    </button>
                    <button class="gim-iconbtn" onclick="_openIslandCollection()" aria-label="Collection" title="Collection">
                        <i data-lucide="book-open"></i>
                    </button>
                    <button class="gim-iconbtn" onclick="openRewardShop()" aria-label="Shop" title="Shop">
                        <i data-lucide="shopping-bag"></i>
                    </button>
                    <button class="gim-iconbtn" onclick="closeIslandMain()" aria-label="Close island" title="Close">
                        <i data-lucide="x"></i>
                    </button>
                </div>
            </div>

            <!-- Map stage — hotspots positioned relative to this layer -->
            <div class="gim-map-stage" id="gim-map-stage">

                <!-- Zone hotspots -->
                ${Object.entries(_HOTSPOTS).map(([zone, pos]) =>
                    _hotspotHTML(zone, _ZONE_META[zone], pos,
                        zone === 'legend' && legendLocked,
                        charsByZone[zone] || [],
                        completedZones)
                ).join('')}

                <!-- Floating character bubbles -->
                ${_bubblesHTML(charsByZone)}

            </div>

            <!-- Streak panel (bottom-left) -->
            <div class="gim-streak-panel">
                <div class="gim-streak-label">STREAK</div>
                <div class="gim-streak-dots">
                    ${_streakDotsHTML(_islandStreak)}
                </div>
            </div>

            <!-- Today panel (bottom-right) -->
            <div class="gim-today-panel">
                <div class="gim-today-title">Today on the Island</div>
                <div class="gim-today-rows">
                    ${_todayRowsHTML(_islandStatus.active_characters || [])}
                </div>
            </div>

            <!-- Lumi toast (hidden by default) -->
            <div class="gim-lumi-toast" id="gim-lumi-toast"></div>

        </div>`;

    if (isNight) _spawnStars();
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Hotspot ─────────────────────────────────────────────────────

/** @tag SHOP */
function _hotspotHTML(zone, meta, pos, locked, chars, completedZones) {
    const varPfx = meta.varPfx;
    const hasWarn  = chars.some(c => (c.hunger ?? 100) < 30 || (c.happiness ?? 100) < 30);
    const hasReady = chars.some(c => c.ready_to_evolve);

    const ringStyle = locked
        ? `border:2px dashed rgba(255,255,255,.7); background:radial-gradient(circle,rgba(255,255,255,.5),rgba(243,210,220,.35)); box-shadow:inset 0 0 30px rgba(255,255,255,.6); backdrop-filter:blur(3px);`
        : `border:3px solid var(--${varPfx}-primary); background:radial-gradient(circle,rgba(255,255,255,.18),transparent 70%); box-shadow:0 6px 20px rgba(0,0,0,.18),inset 0 0 0 6px rgba(255,255,255,.25);`;

    const clickAttr = locked
        ? `onclick="_islandLockedClick('${zone}')" aria-label="Enter ${meta.label} zone (locked)"`
        : `onclick="_islandZoneClick('${zone}')" aria-label="Enter ${meta.label} zone"`;

    const warnBadge = (!locked && hasWarn)
        ? `<div class="gim-badge gim-badge--warn" aria-label="Needs care">!</div>` : '';
    const evoBadge  = (!locked && hasReady)
        ? `<div class="gim-badge gim-badge--evo" aria-label="Ready to evolve">✨</div>` : '';

    const lockContent = locked ? `
        <div class="gim-lock-content">
            <i data-lucide="lock" style="width:26px;height:26px;color:rgba(255,255,255,.9)"></i>
            <span>${completedZones} / 4</span>
        </div>` : '';

    const labelPill = `
        <div class="gim-label gim-label--${varPfx}">
            ${locked ? '<i data-lucide="lock" style="width:11px;height:11px"></i> ' : ''}${meta.label}
        </div>`;

    return `
        <button class="gim-hotspot${locked ? ' gim-hotspot--locked' : ''}"
                style="left:${pos.left};top:${pos.top};width:${pos.size}px;height:${pos.size}px"
                ${clickAttr} tabindex="0">
            <div class="gim-ring" style="${ringStyle}"></div>
            ${labelPill}
            ${warnBadge}
            ${evoBadge}
            ${lockContent}
        </button>`;
}

// ─── Character bubbles ───────────────────────────────────────────

/** @tag SHOP */
function _bubblesHTML(charsByZone) {
    return _CHAR_BUBBLES.map((b, i) => {
        const chars = charsByZone[b.zone] || [];
        const char  = chars[0];
        if (!char) return '';
        const emoji = _charEmoji(char);
        const name  = escapeHtml((char.nickname || char.name || '').substring(0, 8));
        return `
            <button class="gim-bubble gim-float"
                    style="left:${b.left};top:${b.top};animation-delay:${b.delay}"
                    onclick="_bubbleClick(this, '${escapeHtml(name)}')"
                    aria-label="${name}" title="${name}">
                <span class="gim-bubble-dot">${emoji}</span>
            </button>`;
    }).join('');
}

/** @tag SHOP */
function _charEmoji(char) {
    const key = (char.name || '').toLowerCase();
    return _CHAR_EMOJI[key] || '🐾';
}

// ─── Streak dots ─────────────────────────────────────────────────

/** @tag SHOP */
function _streakDotsHTML(count, total = 7) {
    const clamped = Math.min(count, total);
    return Array.from({ length: total }).map((_, i) => {
        const lit = i < clamped;
        const isLast = lit && i === clamped - 1;
        return `<span class="gim-streak-dot${lit ? ' gim-streak-dot--lit' : ' gim-streak-dot--dark'}">
            ${isLast ? '<span class="gim-streak-flame">🔥</span>' : ''}
        </span>`;
    }).join('');
}

// ─── Today panel ─────────────────────────────────────────────────

/** @tag SHOP */
function _todayRowsHTML(chars) {
    const top3 = chars.slice(0, 3);
    if (!top3.length) return `<div class="gim-today-row"><span>Your island awaits</span></div>`;
    return top3.map(c => {
        const emoji  = _charEmoji(c);
        const name   = escapeHtml((c.nickname || c.name || '').substring(0, 10));
        const status = _charStatus(c);
        return `<div class="gim-today-row">${emoji} <b class="gim-today-name">${name}</b> · ${escapeHtml(status)}</div>`;
    }).join('');
}

/** @tag SHOP */
function _charStatus(c) {
    if (c.ready_to_evolve) return 'ready to evolve ✨';
    if ((c.hunger ?? 100) < 30)    return 'feeling hungry';
    if ((c.happiness ?? 100) < 30) return 'feeling sad';
    return 'happy & full';
}

// ─── Zone click ──────────────────────────────────────────────────

/** @tag SHOP */
function _islandZoneClick(zone) {
    if (typeof openZoneDetail === 'function') openZoneDetail(zone);
}

/** @tag SHOP */
function _islandLockedClick(zone) {
    if (typeof _showShopToast === 'function') {
        _showShopToast('Complete all 4 zones to unlock Legend');
    }
}

/** Pulse + tooltip on bubble tap. @tag SHOP */
function _bubbleClick(el, name) {
    el.classList.add('gim-bubble--pulse');
    setTimeout(() => el.classList.remove('gim-bubble--pulse'), 600);
}

// ─── Night stars ─────────────────────────────────────────────────

/** @tag SHOP */
function _spawnStars() {
    const container = document.getElementById('gim-stars');
    if (!container) return;
    container.innerHTML = Array.from({ length: 80 }).map(() => {
        const x    = Math.random() * 100;
        const y    = Math.random() * 60;
        const size = Math.random() * 2 + 1;
        const dur  = (Math.random() * 2 + 1.5).toFixed(1);
        const del  = (Math.random() * 3).toFixed(1);
        return `<div class="gim-star" style="left:${x}%;top:${y}%;width:${size}px;height:${size}px;animation-duration:${dur}s;animation-delay:${del}s"></div>`;
    }).join('');
}

// ─── Day/Night auto-switch ────────────────────────────────────────

/** @tag SHOP */
function _scheduleNightSwitch() {
    if (_nightSwitchTimer) clearTimeout(_nightSwitchTimer);
    const now   = new Date();
    const h     = now.getHours();
    const m     = now.getMinutes();
    const s     = now.getSeconds();
    // Next switch at 06:00 or 18:00
    let targetH = (h < 6) ? 6 : (h < 18) ? 18 : 30;
    if (targetH === 30) targetH = 6; // next day
    const msUntil = ((targetH - h) * 3600 - m * 60 - s) * 1000;
    const corrected = msUntil <= 0 ? msUntil + 86400000 : msUntil;
    _nightSwitchTimer = setTimeout(() => {
        const el = document.getElementById('gim-screen');
        if (!el) return; // overlay closed
        _renderIslandMap();
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _scheduleNightSwitch();
    }, corrected);
}

/** True between 06:00–18:00 local time. @tag SHOP */
function _isDay() { const h = new Date().getHours(); return h >= 6 && h < 18; }

// ─── Lumi toast ───────────────────────────────────────────────────

/** Show +N Lumi earned toast. @tag SHOP */
function showIslandLumiToast(amount) {
    const el = document.getElementById('gim-lumi-toast');
    if (!el) return;
    el.textContent = `💎 +${amount} Lumi earned!`;
    el.classList.add('gim-lumi-toast--show');
    setTimeout(() => el.classList.remove('gim-lumi-toast--show'), 3000);
}

// ─── Helpers ─────────────────────────────────────────────────────

/** @tag SHOP */
function _openLumiLog()          { if (typeof openLumiLog    === 'function') openLumiLog();    }
function _openIslandInventory()  { if (typeof openInventory  === 'function') openInventory();  }
function _openIslandCollection() { if (typeof openCollection === 'function') openCollection(); }

// ─── Home card loader ─────────────────────────────────────────────

/** Populate island home card with live data. @tag HOME_DASHBOARD */
async function _loadIslandCard() {
    const charEl  = document.getElementById('island-home-chars');
    const lumiEl  = document.getElementById('island-home-lumi');
    const cardEl  = document.getElementById('island-home-card');
    if (cardEl) cardEl.onclick = openIslandMain;
    try {
        const d    = await apiFetchJSON('/api/island/status');
        const cnt  = (d.active_characters || []).length + (d.completed_count || 0);
        const lumi = d.currency?.lumi ?? 0;
        if (charEl) charEl.textContent = `${cnt} character${cnt === 1 ? '' : 's'}`;
        if (lumiEl) lumiEl.textContent = `💎 ${lumi.toLocaleString()}`;
    } catch (_) {
        if (charEl) charEl.textContent = 'Your island awaits';
        if (lumiEl) lumiEl.textContent = '';
    }
}
