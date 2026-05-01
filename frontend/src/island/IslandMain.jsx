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

// CALIBRATED — polygon points in 1376×768 coordinate space (SVG viewBox matches map)
// lx/ly = label pill center (CSS transform: translate(-50%,-50%) is applied)
// Zones are non-overlapping; shared edges touch but do not cross.
const _ZONE_POLYS = {
    // Forest: upper-left woodland — right edge stops at x=435 before Legend starts (y≥302)
    forest:  {
        pts: '12,88 190,62 392,70 492,108 530,192 435,290 258,468 78,448 12,368',
        lx: '17%', ly: '38%',
    },
    // Space: top-center observatory — bottom edge y≈262, above Legend top (y=275)
    space:   {
        pts: '532,20 686,10 762,22 818,62 832,155 810,228 768,254 704,262 640,248 582,212 548,155',
        lx: '49%', ly: '18%',
    },
    // Legend: center ruins — upper-left at (462,302), clear of Forest (ends y≈262 at x=462)
    legend:  {
        pts: '462,302 554,282 700,275 806,294 868,348 884,464 848,550 734,580 606,584 484,556 434,494 420,388',
        lx: '50%', ly: '50%',
    },
    // Ocean: right coast — lighthouse + beach + dock; left edge x≈860 clear of Legend (right≈868)
    ocean:   {
        pts: '878,190 1008,146 1204,86 1376,166 1376,608 1224,664 1070,650 962,556 940,430 870,330 860,246',
        lx: '85%', ly: '48%',
    },
    // Savanna: bottom grassland — top edge y≈506-540, below Legend bottom (y=584)
    savanna: {
        pts: '358,556 448,516 604,506 800,508 962,540 1064,596 1070,684 984,760 784,768 496,768 358,726 346,626',
        lx: '49%', ly: '76%',
    },
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
let _islandDaily   = null;
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
        fetch('/api/island/daily').then(r => r.json()).catch(() => null),
    ]).then(([statusData, xpData, dailyData]) => {
        _islandStatus = statusData;
        _islandStreak = xpData.streak_days ?? 0;
        _islandDaily  = dailyData;
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

            <!-- Map stage — SVG zone polygons + floating labels -->
            <div class="gim-map-stage" id="gim-map-stage">

                <!-- Zone polygons (SVG) + HTML label pills -->
                ${_svgZonesHTML(charsByZone, completedZones, legendLocked)}

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

// ─── SVG zone polygons ────────────────────────────────────────────

/** Render one SVG <polygon> per zone + HTML label pills positioned at zone centers. @tag SHOP */
function _svgZonesHTML(charsByZone, completedZones, legendLocked) {
    const polygons = Object.entries(_ZONE_POLYS).map(([zone, cfg]) => {
        const meta   = _ZONE_META[zone];
        const locked = zone === 'legend' && legendLocked;
        const cls    = locked ? 'gim-poly gim-poly--locked' : `gim-poly gim-poly--${meta.varPfx}`;
        const click  = locked
            ? `onclick="_islandLockedClick('${zone}')" aria-label="Enter ${meta.label} zone (locked)"`
            : `onclick="_islandZoneClick('${zone}')"  aria-label="Enter ${meta.label} zone"`;
        return `<polygon class="${cls}" points="${cfg.pts}" ${click} />`;
    }).join('');

    const labels = Object.entries(_ZONE_POLYS).map(([zone, cfg]) => {
        const meta   = _ZONE_META[zone];
        const locked = zone === 'legend' && legendLocked;
        const chars  = charsByZone[zone] || [];
        const hasWarn  = chars.some(c => (c.hunger  ?? 100) < 30 || (c.happiness ?? 100) < 30);
        const hasReady = chars.some(c => c.ready_to_evolve);

        const warnBadge = (!locked && hasWarn)
            ? `<div class="gim-badge gim-badge--warn" aria-label="Needs care">!</div>` : '';
        const evoBadge  = (!locked && hasReady)
            ? `<div class="gim-badge gim-badge--evo" aria-label="Ready to evolve">✨</div>` : '';
        const lockTag   = locked
            ? `<i data-lucide="lock" style="width:10px;height:10px;vertical-align:-1px"></i> ` : '';
        const lockOverlay = locked ? `
            <div class="gim-lock-overlay">
                <i data-lucide="lock" style="width:24px;height:24px;color:rgba(255,255,255,.9)"></i>
                <span>${completedZones} / 4</span>
            </div>` : '';

        const click = locked
            ? `onclick="_islandLockedClick('${zone}')"`
            : `onclick="_islandZoneClick('${zone}')"`;

        return `
            <div class="gim-zone-label-wrap" style="left:${cfg.lx};top:${cfg.ly}" ${click}>
                ${lockOverlay}
                <div class="gim-label gim-label--${meta.varPfx}">${lockTag}${meta.label}</div>
                ${warnBadge}${evoBadge}
            </div>`;
    }).join('');

    return `
        <svg class="gim-zones-svg" viewBox="0 0 1376 768"
             xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            ${polygons}
        </svg>
        ${labels}`;
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
    // Character rows (top 3)
    const top3 = chars.slice(0, 3);
    const charRows = top3.length
        ? top3.map(c => {
            const emoji  = _charEmoji(c);
            const name   = escapeHtml((c.nickname || c.name || '').substring(0, 10));
            const status = _charStatus(c);
            return `<div class="gim-today-row">${emoji} <b class="gim-today-name">${name}</b> · ${escapeHtml(status)}</div>`;
        }).join('')
        : `<div class="gim-today-row"><span>Your island awaits</span></div>`;

    // Daily section — skip if data unavailable
    const d = _islandDaily;
    if (!d) return charRows;

    const streak   = typeof d.streak === 'number' ? d.streak : (d.streak?.current_streak ?? _islandStreak);
    const attended = d.attendance_week?.find(w => w.today)?.attended ?? false;
    const claimed  = d.today_claimed;
    const canClaim = d.can_claim_today;

    let claimHTML;
    if (claimed) {
        claimHTML = `<div class="gim-today-claimed"><i data-lucide="check-circle"></i> Claimed</div>`;
    } else if (canClaim) {
        claimHTML = `<button class="gim-today-claim-btn" id="gim-claim-btn" onclick="_claimDailyAttendance()">
            <i data-lucide="gem"></i> Claim 30 Lumi
        </button>`;
    } else {
        claimHTML = `<button class="gim-today-claim-btn gim-today-claim-btn--locked" disabled>
            Study first to claim
        </button>`;
    }

    // Weekly goal (first active XP goal, if any)
    const goal = (d.weekly_goals || [])[0];
    const goalHTML = goal ? (() => {
        const pct = goal.target > 0 ? Math.min(100, Math.round((goal.current / goal.target) * 100)) : 0;
        return `
            <div class="gim-today-goal">
                <div class="gim-today-goal-header">
                    <span class="gim-today-goal-label">${escapeHtml(goal.label || 'Weekly XP')}</span>
                    <span class="gim-today-goal-pct">${goal.current} / ${goal.target}</span>
                </div>
                <div class="gim-today-goal-bar">
                    <div class="gim-today-goal-fill" style="width:${pct}%"></div>
                </div>
            </div>`;
    })() : '';

    return `
        ${charRows}
        <div class="gim-today-divider"></div>
        <div class="gim-today-attend">
            <span>${attended ? '✅' : '⬜'} Today</span>
            <span>🔥 ${streak} day${streak === 1 ? '' : 's'}</span>
        </div>
        ${claimHTML}
        ${goalHTML}`;
}

/** @tag SHOP */
function _charStatus(c) {
    if (c.ready_to_evolve) return 'ready to evolve ✨';
    if ((c.hunger ?? 100) < 30)    return 'feeling hungry';
    if ((c.happiness ?? 100) < 30) return 'feeling sad';
    return 'happy & full';
}

/** Claim today's attendance Lumi reward. @tag SHOP */
async function _claimDailyAttendance() {
    const btn = document.getElementById('gim-claim-btn');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2"></i> Claiming…';
    if (typeof lucide !== 'undefined') lucide.createIcons();

    try {
        const result = await apiFetchJSON('/api/island/daily/claim', { method: 'POST' });

        // Update topbar lumi balance
        const newLumi = result.currency?.lumi;
        if (newLumi != null) {
            const lumiSpan = document.querySelector('.gim-stat--lumi span');
            if (lumiSpan) lumiSpan.textContent = newLumi.toLocaleString();
        }

        // Swap button → claimed badge in place
        btn.outerHTML = `<div class="gim-today-claimed"><i data-lucide="check-circle"></i> Claimed</div>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Keep state in sync so re-renders stay consistent
        if (_islandDaily) {
            _islandDaily.today_claimed  = true;
            _islandDaily.can_claim_today = false;
        }

        showIslandLumiToast(result.lumi_earned ?? 30);
    } catch (e) {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="gem"></i> Claim 30 Lumi';
        if (typeof lucide !== 'undefined') lucide.createIcons();
        if (typeof _showShopToast === 'function') _showShopToast(e.message || 'Claim failed');
    }
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
        if (d.island_on === false) {
            if (cardEl) cardEl.style.display = 'none';
            return;
        }
        const cnt  = (d.active_characters || []).length + (d.completed_count || 0);
        const lumi = d.currency?.lumi ?? 0;
        if (charEl) charEl.textContent = `${cnt} character${cnt === 1 ? '' : 's'}`;
        if (lumiEl) lumiEl.textContent = `💎 ${lumi.toLocaleString()}`;
    } catch (_) {
        if (charEl) charEl.textContent = 'Your island awaits';
        if (lumiEl) lumiEl.textContent = '';
    }
}
