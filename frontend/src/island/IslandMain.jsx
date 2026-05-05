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
    forest:  { label: 'Forest',  lucideIcon: 'tree-pine', varPfx: 'english', subject: 'English' },
    ocean:   { label: 'Ocean',   lucideIcon: 'waves',     varPfx: 'math',    subject: 'Math'    },
    savanna: { label: 'Savanna', lucideIcon: 'paw-print', varPfx: 'diary',   subject: 'Diary'   },
    space:   { label: 'Space',   lucideIcon: 'rocket',    varPfx: 'rewards', subject: 'Review'  },
    legend:  { label: 'Legend',  lucideIcon: 'sparkles',  varPfx: 'legend',  subject: 'All'     },
};

// ZONE CIRCLES — cx/cy/r in 1376×768 coordinate space (SVG viewBox matches map)
// cx/cy = circle center, r = radius. Label pill is always rendered BELOW the circle.
// Update cx/cy to reposition; update r to resize the clickable/visual area.
const _ZONE_CIRCLES = {
    forest:  { cx: 255, cy: 305, r: 85 },
    space:   { cx: 685, cy: 155, r: 85 },
    legend:  { cx: 690, cy: 375, r: 85 },
    ocean:   { cx: 1195, cy: 400, r: 85 },
    savanna: { cx: 685, cy: 615, r: 85 },
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
            <div class="isl-loading-ship"><i data-lucide="anchor"></i></div>
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
                 src="/static/img/island/bg_island.png"
                 alt="Gia's Island" draggable="false">

            ${isNight ? `
            <div class="gim-night-scrim"></div>
            <div class="gim-stars" id="gim-stars"></div>
            <div class="gim-sunmoon gim-night-moon"><i data-lucide="moon"></i></div>
            ` : `
            <div class="gim-sunmoon"><i data-lucide="sun"></i></div>
            `}

            <!-- Top bar -->
            <div class="gim-topbar${isNight ? ' gim-topbar--night' : ''}">
                <div class="gim-topbar-left">
                    <button class="gim-stat gim-stat--lumi" onclick="_openLumiLog()" title="Lumi history">
                        <i data-lucide="gem"></i> <span>${lumi.toLocaleString()}</span>
                    </button>
                    <span class="gim-stat gim-stat--legend">
                        <i data-lucide="sparkles"></i> <span>${legendLumi.toLocaleString()}</span>
                    </span>
                    <span class="gim-stat gim-stat--streak">
                        <i data-lucide="flame"></i> <span>${_islandStreak} day${_islandStreak === 1 ? '' : 's'}</span>
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

// ─── SVG zone circles ─────────────────────────────────────────────

/** Render one SVG <circle> per zone + HTML label pills below each circle. @tag SHOP */
function _svgZonesHTML(charsByZone, completedZones, legendLocked) {
    const W = 1376, H = 768;

    const circles = Object.entries(_ZONE_CIRCLES).map(([zone, cfg]) => {
        const meta   = _ZONE_META[zone];
        const locked = zone === 'legend' && legendLocked;
        const cls    = locked ? 'gim-circle gim-circle--locked' : `gim-circle gim-circle--${meta.varPfx}`;
        const click  = locked
            ? `onclick="_islandLockedClick('${zone}')" aria-label="Enter ${meta.label} zone (locked)"`
            : `onclick="_islandZoneClick('${zone}')"  aria-label="Enter ${meta.label} zone"`;
        return `<circle class="${cls}" cx="${cfg.cx}" cy="${cfg.cy}" r="${cfg.r}" ${click} />`;
    }).join('');

    // Lock overlay centered on circle (only for locked Legend)
    const lockOverlays = Object.entries(_ZONE_CIRCLES).map(([zone, cfg]) => {
        if (!(zone === 'legend' && legendLocked)) return '';
        const lx = `${(cfg.cx / W * 100).toFixed(2)}%`;
        const ly = `${(cfg.cy / H * 100).toFixed(2)}%`;
        return `
            <div class="gim-lock-center" style="left:${lx};top:${ly}" onclick="_islandLockedClick('legend')">
                <i data-lucide="lock" style="width:24px;height:24px;color:rgba(255,255,255,.9)"></i>
                <span>${completedZones} / 4</span>
            </div>`;
    }).join('');

    // Label pills — always below the circle
    const labels = Object.entries(_ZONE_CIRCLES).map(([zone, cfg]) => {
        const meta   = _ZONE_META[zone];
        const locked = zone === 'legend' && legendLocked;
        const chars  = charsByZone[zone] || [];
        const hasWarn  = chars.some(c => (c.hunger  ?? 100) < 30 || (c.happiness ?? 100) < 30);
        const hasReady = chars.some(c => c.ready_to_evolve);

        const warnBadge = (!locked && hasWarn)
            ? `<div class="gim-badge gim-badge--warn" aria-label="Needs care">!</div>` : '';
        const evoBadge  = (!locked && hasReady)
            ? `<div class="gim-badge gim-badge--evo" aria-label="Ready to evolve">+</div>` : '';
        const lockTag   = locked
            ? `<i data-lucide="lock" style="width:10px;height:10px;vertical-align:-1px"></i> ` : '';

        const click = locked
            ? `onclick="_islandLockedClick('${zone}')"`
            : `onclick="_islandZoneClick('${zone}')"`;

        // Label sits BELOW the circle, with a small gap from the circle bottom edge.
        // Anchor = bottom-center of circle + 18px gap. Label-wrap uses translate(-50%, 0)
        // so the label's TOP aligns to the anchor (label hangs below).
        const lx = `${(cfg.cx / W * 100).toFixed(2)}%`;
        const ly = `${((cfg.cy + cfg.r + 18) / H * 100).toFixed(2)}%`;

        return `
            <div class="gim-zone-label-wrap" style="left:${lx};top:${ly}" ${click}>
                <div class="gim-label gim-label--${meta.varPfx}">${lockTag}${meta.label}</div>
                ${warnBadge}${evoBadge}
            </div>`;
    }).join('');

    return `
        <svg class="gim-zones-svg" viewBox="0 0 1376 768"
             xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            ${circles}
        </svg>
        ${lockOverlays}
        ${labels}`;
}

// ─── Character bubbles ───────────────────────────────────────────

/** @tag SHOP */
function _bubblesHTML(charsByZone) {
    return _CHAR_BUBBLES.map((b, i) => {
        const chars = charsByZone[b.zone] || [];
        const char  = chars[0];
        if (!char) return '';
        const meta  = _ZONE_META[b.zone] || {};
        const name  = escapeHtml((char.nickname || char.name || '').substring(0, 8));
        return `
            <button class="gim-bubble gim-float"
                    style="left:${b.left};top:${b.top};animation-delay:${b.delay}"
                    onclick="_bubbleClick(this, '${escapeHtml(name)}')"
                    aria-label="${name}" title="${name}">
                <span class="gim-bubble-dot"><i data-lucide="${meta.lucideIcon || 'smile'}"></i></span>
            </button>`;
    }).join('');
}

// ─── Streak dots ─────────────────────────────────────────────────

/** @tag SHOP */
function _streakDotsHTML(count, total = 7) {
    const clamped = Math.min(count, total);
    return Array.from({ length: total }).map((_, i) => {
        const lit = i < clamped;
        const isLast = lit && i === clamped - 1;
        return `<span class="gim-streak-dot${lit ? ' gim-streak-dot--lit' : ' gim-streak-dot--dark'}">
            ${isLast ? '<span class="gim-streak-flame"><i data-lucide="flame"></i></span>' : ''}
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
            const meta   = _ZONE_META[c.zone] || {};
            const name   = escapeHtml((c.nickname || c.name || '').substring(0, 10));
            const status = _charStatus(c);
            return `<div class="gim-today-row"><i data-lucide="${meta.lucideIcon || 'heart'}" class="gim-today-icon"></i> <b class="gim-today-name">${name}</b> · ${escapeHtml(status)}</div>`;
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
            <span>${attended ? '<i data-lucide="check-circle"></i>' : '<i data-lucide="circle"></i>'} Today</span>
            <span><i data-lucide="flame"></i> ${streak} day${streak === 1 ? '' : 's'}</span>
        </div>
        ${claimHTML}
        ${goalHTML}`;
}

/** @tag SHOP */
function _charStatus(c) {
    if (c.ready_to_evolve) return 'ready to evolve!';
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
    el.innerHTML = `<i data-lucide="gem"></i> +${amount} Lumi earned!`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
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
        if (lumiEl) lumiEl.textContent = lumi.toLocaleString();
    } catch (_) {
        if (charEl) charEl.textContent = 'Your island awaits';
        if (lumiEl) lumiEl.textContent = '';
    }
}
