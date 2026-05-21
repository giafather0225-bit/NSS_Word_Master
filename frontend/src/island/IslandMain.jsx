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
    forest:  { cx: 345,  cy: 215, r: 78 },   // 좌상단 분홍꽃 숲
    space:   { cx: 1075, cy: 195, r: 80 },   // 우상단 라벤더 + 행성
    legend:  { cx: 660,  cy: 385, r: 70 },   // 중앙 분홍 수정/돌기둥
    ocean:   { cx: 345,  cy: 475, r: 80 },   // 좌하단 청록 만
    savanna: { cx: 1030, cy: 465, r: 80 },   // 우하단 노란 풌밭
};


// Char bubble anchor positions near artwork features
const _CHAR_BUBBLES = [
    { zone: 'forest',  left: '16%', top: '42%', delay: '0s'   },
    { zone: 'space',   left: '86%', top: '40%', delay: '.5s'  },
    { zone: 'ocean',   left: '16%', top: '78%', delay: '.8s'  },
    { zone: 'savanna', left: '83%', top: '60%', delay: '1.2s' },
    { zone: 'legend',  left: '48%', top: '50%', delay: '1.6s' },
];

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _islandStatus  = null;
let _islandStreak  = 0;
let _islandDaily   = null;
let _nightSwitchTimer = null;
let _wanderIntervals  = [];

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

    // Reset zone detail overlay so stale detail screen doesn't bleed through
    const detailEl = document.getElementById('isl-detail-overlay');
    if (detailEl) { detailEl.classList.add('hidden'); detailEl.innerHTML = ''; }

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
        _startCharWandering();
        if (typeof lucide !== 'undefined') lucide.createIcons();
        if (typeof checkIslandNotifications === 'function') checkIslandNotifications();
        _scheduleNightSwitch();
    }).catch(() => _renderIslandError());
}

/** @tag SHOP */
function closeIslandMain() {
    const el = document.getElementById('island-overlay');
    if (el) el.classList.add('hidden');
    const detailEl = document.getElementById('isl-detail-overlay');
    if (detailEl) { detailEl.classList.add('hidden'); detailEl.innerHTML = ''; }
    const evoEl = document.getElementById('isl-evo-modal');
    if (evoEl) { evoEl.classList.add('hidden'); evoEl.innerHTML = ''; }
    if (_nightSwitchTimer) { clearTimeout(_nightSwitchTimer); _nightSwitchTimer = null; }
    _wanderIntervals.forEach(clearInterval);
    _wanderIntervals = [];
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
                 src="/static/img/island/bg_island_v5.png"
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
                ${_svgZonesHTML(charsByZone, completedZones, zoneUnlock)}

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
function _svgZonesHTML(charsByZone, completedZones, zoneUnlock) {
    const W = 1376, H = 768;

    const circles = Object.entries(_ZONE_CIRCLES).map(([zone, cfg]) => {
        const meta   = _ZONE_META[zone];
        const locked = !zoneUnlock[zone];
        const cls    = locked ? 'gim-circle gim-circle--locked' : `gim-circle gim-circle--${meta.varPfx}`;
        const click  = locked
            ? `onclick="_islandLockedClick('${zone}')" aria-label="Enter ${meta.label} zone (locked)"`
            : `onclick="_islandZoneClick('${zone}')"  aria-label="Enter ${meta.label} zone"`;
        return `<circle class="${cls}" cx="${cfg.cx}" cy="${cfg.cy}" r="${cfg.r}" ${click} />`;
    }).join('');

    // Lock overlay centered on each locked circle
    const lockOverlays = Object.entries(_ZONE_CIRCLES).map(([zone, cfg]) => {
        if (zoneUnlock[zone]) return '';
        const lx = `${(cfg.cx / W * 100).toFixed(2)}%`;
        const ly = `${(cfg.cy / H * 100).toFixed(2)}%`;
        const sub = zone === 'legend'
            ? `<span>${completedZones} / 4</span>`
            : '';
        return `
            <div class="gim-lock-center" style="left:${lx};top:${ly}" onclick="_islandLockedClick('${zone}')">
                <i data-lucide="lock" style="width:24px;height:24px;color:rgba(255,255,255,.9)"></i>
                ${sub}
            </div>`;
    }).join('');

    // Label pills — always below the circle
    const labels = Object.entries(_ZONE_CIRCLES).map(([zone, cfg]) => {
        const meta   = _ZONE_META[zone];
        const locked = !zoneUnlock[zone];
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

        // Label sits BELOW the circle.
        // Anchor = circle's bottom edge (cy + r) + small gap.
        // CSS uses translateX(-50%) so the wrap top aligns to anchor → label flows down.
        const lx = `${(cfg.cx / W * 100).toFixed(2)}%`;
        const ly = `${((cfg.cy + cfg.r + 6) / H * 100).toFixed(2)}%`;

        // Order: badges first (appear above label, just below circle) → label last.
        return `
            <div class="gim-zone-label-wrap" style="left:${lx};top:${ly}" ${click}>
                ${warnBadge}${evoBadge}
                <div class="gim-label gim-label--${meta.varPfx}">${lockTag}${meta.label}</div>
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

// ─── Character wandering ─────────────────────────────────────────

/**
 * Move each character bubble to a random point within its zone circle.
 * Uses CSS transition (already set on the bubble) for smooth gliding.
 * @tag SHOP
 */
function _startCharWandering() {
    _wanderIntervals.forEach(clearInterval);
    _wanderIntervals = [];

    const SVG_W = 1376, SVG_H = 768;

    _CHAR_BUBBLES.forEach(b => {
        const circle = _ZONE_CIRCLES[b.zone];
        if (!circle) return;

        let prevSvgX = circle.cx; // track last x to determine facing direction

        function pickWaypoint() {
            // P2: skip while Zone Detail overlay is visible
            const detail = document.getElementById('isl-detail-overlay');
            if (detail && !detail.classList.contains('hidden')) return;

            const bubble = document.querySelector(`.gim-bubble[data-zone="${b.zone}"]`);
            if (!bubble) return;

            // sqrt(random) gives uniform distribution inside a circle
            const angle = Math.random() * 2 * Math.PI;
            const dist  = Math.sqrt(Math.random()) * circle.r * 0.68;
            const svgX  = circle.cx + Math.cos(angle) * dist;
            const svgY  = circle.cy + Math.sin(angle) * dist;

            bubble.style.left = (svgX / SVG_W * 100).toFixed(2) + '%';
            bubble.style.top  = (svgY / SVG_H * 100).toFixed(2) + '%';

            // P3: flip character image based on horizontal movement direction
            const dot = bubble.querySelector('.gim-bubble-dot');
            if (dot) {
                const movingLeft = svgX < prevSvgX - 2; // 2px dead-zone avoids flicker on tiny moves
                dot.style.transform = movingLeft ? 'scaleX(-1)' : 'scaleX(1)';
            }
            prevSvgX = svgX;
        }

        // First wander after 1.5-2.5s so the map fully renders
        setTimeout(pickWaypoint, 1500 + Math.random() * 1000);
        // Then wander every 6-10s, each bubble on its own cadence
        _wanderIntervals.push(setInterval(pickWaypoint, 6000 + Math.random() * 4000));
    });
}

// ─── Character bubbles ───────────────────────────────────────────

/** @tag SHOP */
function _bubblesHTML(charsByZone) {
    // zone -> 폴더명 매핑 (Forest, Ocean, Savanna, Space, Legend)
    const ZONE_FOLDER = {
        forest: 'Forest', ocean: 'Ocean', savanna: 'Savanna',
        space: 'Space',   legend: 'Legend'
    };

    return _CHAR_BUBBLES.map((b, i) => {
        const chars = charsByZone[b.zone] || [];
        const char  = chars[0];
        if (!char) return '';
        const meta  = _ZONE_META[b.zone] || {};
        const name   = escapeHtml((char.nickname || char.name || '').substring(0, 10));
        const stage  = char.stage || 'baby';
        const hunger = char.hunger  ?? 100;
        const happy  = char.happiness ?? 100;

        // 1) DB의 character.images JSON에서 stage별 경로 시도
        let imgRel = '';
        try {
            const imgs = JSON.parse(char.images || '{}');
            imgRel = imgs[stage] || imgs['baby'] || '';
        } catch (_) {}

        // 2) JSON에 없으면 표준 경로 추정
        const baseName = (char.name || '').trim();
        const folder = ZONE_FOLDER[b.zone] || '';
        const guessSrc = folder && baseName
            ? `/static/img/island/${folder}/${baseName}_${stage}.png`
            : '';
        const guessLower = folder && baseName
            ? `/static/img/island/${folder}/${baseName.toLowerCase()}_${stage}.png`
            : '';
        const finalSrc = imgRel ? `/static/img/island/${imgRel}` : guessSrc;

        // 폴백 체인: imgRel → guessLower → Lucide
        const lucideName = meta.lucideIcon || 'smile';
        const onErr = guessLower && guessLower !== finalSrc
            ? `this.onerror=function(){this.outerHTML='<i data-lucide=\\'${lucideName}\\' style=\\'width:36px;height:36px;color:#7a5a9e\\'></i>';if(typeof lucide!=='undefined')lucide.createIcons();};this.src='${guessLower}'`
            : `this.outerHTML='<i data-lucide=\\'${lucideName}\\' style=\\'width:36px;height:36px;color:#7a5a9e\\'></i>';if(typeof lucide!=='undefined')lucide.createIcons();`;

        const imgHTML = finalSrc
            ? `<img src="${finalSrc}" alt="${name}" draggable="false"
                  style="width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 4px 8px rgba(80,40,120,.25))"
                  onerror="${onErr}">`
            : `<i data-lucide="${lucideName}" style="width:36px;height:36px;color:#7a5a9e"></i>`;

        const hungerWarn = hunger < 30 ? ' gim-gauge--warn' : '';
        const happyWarn  = happy  < 30 ? ' gim-gauge--warn' : '';
        const evoCls     = char.ready_to_evolve ? ' gim-bubble-dot--evo' : '';

        // Start at zone circle center (converted to %) so initial position is inside the zone
        const zc       = _ZONE_CIRCLES[b.zone];
        const initLeft = zc ? (zc.cx / 1376 * 100).toFixed(2) + '%' : b.left;
        const initTop  = zc ? (zc.cy / 768  * 100).toFixed(2) + '%' : b.top;

        return `
            <button class="gim-bubble gim-float"
                    data-zone="${b.zone}"
                    style="left:${initLeft};top:${initTop};width:96px;height:auto;animation-delay:${b.delay};display:flex;flex-direction:column;align-items:center;gap:4px;background:transparent;border:none;padding:0 0 4px;cursor:pointer;pointer-events:auto;transition:left 3.5s ease-in-out,top 3.5s ease-in-out"
                    onclick="_bubbleClick(this, '${escapeHtml(name)}', '${b.zone}', ${char.id || 0}, '${char.stage || 'baby'}', ${!!char.ready_to_evolve})"
                    aria-label="${name}" title="${name}">
                <span class="gim-bubble-dot${evoCls}"
                      style="width:84px;height:84px;background:rgba(255,255,255,.92);border:3px solid #fff;border-radius:50%;display:flex;align-items:center;justify-content:center;padding:8px;box-shadow:0 6px 18px rgba(40,20,80,.30);overflow:hidden">
                    ${imgHTML}
                </span>
                <span style="background:rgba(255,255,255,.95);border-radius:999px;padding:2px 10px;font-size:11px;font-weight:800;color:#2a1f3d;white-space:nowrap;box-shadow:0 2px 6px rgba(40,20,80,.18);letter-spacing:.01em">${name}</span>
                <div class="gim-bubble-gauges">
                    <div class="gim-bubble-gauge gim-bubble-gauge--hunger${hungerWarn}" style="--g-pct:${Math.round(hunger)}%"></div>
                    <div class="gim-bubble-gauge gim-bubble-gauge--happy${happyWarn}"   style="--g-pct:${Math.round(happy)}%"></div>
                </div>
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
    // Character rows — show all active characters
    const charRows = chars.length
        ? chars.map(c => {
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

        _claimCelebrate(result.lumi_earned ?? 30);
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
    // Shake the zone button for tactile feedback
    const btn = document.querySelector(`.gim-zone-btn[data-zone="${zone}"]`);
    if (btn) {
        btn.classList.remove('gim-zone-btn--shake');
        // Force reflow to restart animation if clicked again quickly
        void btn.offsetWidth;
        btn.classList.add('gim-zone-btn--shake');
        setTimeout(() => btn.classList.remove('gim-zone-btn--shake'), 320);
    }
    if (typeof _showShopToast !== 'function') return;
    const msg = zone === 'legend'
        ? 'Evolve 1 character in each zone to unlock Legend'
        : `Complete a character in the previous zone to unlock ${_ZONE_META[zone]?.label || 'this zone'}`;
    _showShopToast(msg);
}

/** Bubble click → small care popup with Feed / Evolve / Zone buttons. @tag SHOP */
function _bubbleClick(el, name, zone, progId, stage, canEvolve) {
    // Remove any existing popup
    const existing = document.getElementById('gim-care-popup');
    if (existing) { existing.remove(); return; }

    el.classList.add('gim-bubble--pulse');
    setTimeout(() => el.classList.remove('gim-bubble--pulse'), 300);

    const evolveBtn = canEvolve
        ? `<button class="gim-care-btn gim-care-btn--evo" onclick="_careBubbleEvolve(${progId},'${stage}','${escapeHtml(name)}')">
               <i data-lucide="sparkles"></i> Evolve
           </button>`
        : '';

    const popup = document.createElement('div');
    popup.id = 'gim-care-popup';
    popup.className = 'gim-care-popup';
    popup.innerHTML = `
        <div class="gim-care-popup-name">${escapeHtml(name)}</div>
        <div class="gim-care-popup-btns">
            <button class="gim-care-btn gim-care-btn--feed" onclick="_careBubbleFeed(${progId})">
                <i data-lucide="utensils"></i> Feed
            </button>
            ${evolveBtn}
            <button class="gim-care-btn gim-care-btn--zone" onclick="_careBubbleZone('${zone}')">
                <i data-lucide="map"></i> Zone
            </button>
        </div>`;

    // Position near the bubble
    const rect = el.getBoundingClientRect();
    const screen = document.getElementById('gim-screen');
    const sRect = screen ? screen.getBoundingClientRect() : { left: 0, top: 0 };
    popup.style.left = `${rect.left - sRect.left + rect.width / 2}px`;
    popup.style.top  = `${rect.top  - sRect.top  - 8}px`;

    (screen || document.body).appendChild(popup);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Close on outside click
    setTimeout(() => {
        document.addEventListener('click', function _closePopup(e) {
            if (!popup.contains(e.target) && e.target !== el) {
                popup.remove();
                document.removeEventListener('click', _closePopup);
            }
        });
    }, 0);
}

function _careBubbleFeed(progId) {
    const p = document.getElementById('gim-care-popup');
    if (p) p.remove();
    if (progId && typeof openFeedScreen === 'function') openFeedScreen(progId);
}

function _careBubbleEvolve(progId, stage, name) {
    const p = document.getElementById('gim-care-popup');
    if (p) p.remove();
    if (progId && typeof openEvolutionModal === 'function') openEvolutionModal(progId, stage, name);
}

function _careBubbleZone(zone) {
    const p = document.getElementById('gim-care-popup');
    if (p) p.remove();
    if (zone && typeof openZoneDetail === 'function') openZoneDetail(zone);
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
        _startCharWandering();
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _scheduleNightSwitch();
    }, corrected);
}

/** True between 06:00–18:00 local time. @tag SHOP */
function _isDay() { const h = new Date().getHours(); return h >= 6 && h < 18; }

// ─── Lumi toast ───────────────────────────────────────────────────

/** Full-screen celebration when daily Lumi is claimed. @tag SHOP */
function _claimCelebrate(amount) {
    const screen = document.getElementById('gim-screen');
    if (!screen) { showIslandLumiToast(amount); return; }

    const coins = Array.from({ length: 10 }).map(() => {
        const x   = 20 + Math.random() * 60;
        const del = (Math.random() * 0.45).toFixed(2);
        const dur = (0.65 + Math.random() * 0.55).toFixed(2);
        return `<div class="gim-claim-coin" style="left:${x}%;animation-delay:${del}s;animation-duration:${dur}s"><i data-lucide="gem"></i></div>`;
    }).join('');

    const div = document.createElement('div');
    div.className = 'gim-claim-splash';
    div.innerHTML = `
        ${coins}
        <div class="gim-claim-splash-inner">
            <div class="gim-claim-amount">+${amount}</div>
            <div class="gim-claim-label"><i data-lucide="gem"></i> Lumi earned!</div>
        </div>`;
    screen.appendChild(div);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    setTimeout(() => {
        div.classList.add('gim-claim-splash--out');
        setTimeout(() => div.remove(), 400);
    }, 1800);
}

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

const _IH_SLOT_ORDER  = ['forest', 'ocean', 'legend', 'savanna', 'space'];
const _IH_ZONE_FOLDER = { forest: 'Forest', ocean: 'Ocean', savanna: 'Savanna', space: 'Space', legend: 'Legend' };
const _IH_ZONE_ICON   = { forest: 'tree-pine', ocean: 'waves', savanna: 'sun', space: 'sparkles', legend: 'crown' };

/**
 * Resolve PNG src for home-card slot.
 * Priority: images JSON[stage] → images JSON[baby] → lowercase guess → original-case guess.
 * Returns { primary, fallback } where primary is the first URL to try and fallback is the
 * onerror URL (original case, for Sprout-style uppercase filenames).
 */
function _ihImgSrc(c, zone, stage) {
    const folder = _IH_ZONE_FOLDER[zone];
    const name   = (c.name || '').trim();
    // 1. DB images JSON (most reliable — set during character seeding)
    try {
        const imgs = JSON.parse(c.images || '{}');
        const rel  = imgs[stage] || imgs['baby'];
        if (rel) return { primary: `/static/img/island/${rel}`, fallback: '' };
    } catch (_) {}
    // 2. Lowercase first (majority of files: blossie_baby.png etc.)
    //    onerror fallback tries original case (Sprout_baby.png etc.)
    const lower    = folder && name ? `/static/img/island/${folder}/${name.toLowerCase()}_${stage}.png` : '';
    const original = folder && name ? `/static/img/island/${folder}/${name}_${stage}.png` : '';
    return { primary: lower, fallback: original !== lower ? original : '' };
}

/** Render empty-state placeholder (no characters yet) into #island-home-pets. @tag HOME_DASHBOARD */
function _renderHomePetsEmpty() {
    const host = document.getElementById('island-home-pets');
    if (!host) return;
    const icons = [
        { icon: 'tree-pine',  zone: 'forest' },
        { icon: 'sparkles',   zone: 'legend' },
        { icon: 'waves',      zone: 'ocean'  },
    ];
    host.innerHTML = `
        <div class="ih-empty">
            ${icons.map(({ icon, zone }) =>
                `<span class="ih-empty-icon" data-zone="${zone}"><i data-lucide="${icon}"></i></span>`
            ).join('')}
            <span class="ih-empty-hint">Adopt your first character</span>
        </div>`;
    if (window.lucide) lucide.createIcons();
}

/** Render character PNG slots into #island-home-pets. @tag HOME_DASHBOARD */
function _renderHomePets(chars) {
    const host = document.getElementById('island-home-pets');
    if (!host) return;
    const byZone = {};
    (chars || []).forEach(c => { byZone[c.zone] = c; });
    const html = _IH_SLOT_ORDER.map(zone => {
        const c = byZone[zone];
        if (!c) return '';
        const isLegend         = zone === 'legend';
        const stage            = c.stage || 'baby';
        const name             = (c.name || '').trim();
        const { primary, fallback } = _ihImgSrc(c, zone, stage);
        const icon             = _IH_ZONE_ICON[zone];
        const onerr = fallback
            ? `if(this.src!=='${fallback}'){this.src='${fallback}';}else{this.outerHTML='<i data-lucide=\\'${icon}\\'></i>';if(window.lucide)lucide.createIcons();}`
            : `this.outerHTML='<i data-lucide=\\'${icon}\\'></i>';if(window.lucide)lucide.createIcons();`;
        const crown = isLegend ? `<svg class="ih-crown" viewBox="0 0 32 22" fill="none">
            <path d="M3 19 L5 7 L11 13 L16 4 L21 13 L27 7 L29 19 Z" fill="#f5d97c" stroke="#a88860" stroke-width="1.4" stroke-linejoin="round"/>
            <circle cx="16" cy="14" r="1.3" fill="#ea4f6e"/>
        </svg>` : '';
        const lvText = c.level ? `Lv.${c.level}` : '';
        const zoneDot = `<span class="ih-lv">${lvText}</span>`;
        return `<div class="ih-pet ih-pet--${isLegend ? 'legend' : 'normal'}" data-zone="${zone}">
            ${crown}
            <div class="ih-img">
                <img src="${primary}" alt="${escapeHtml(name)}" onerror="${onerr}">
            </div>
            ${zoneDot}
        </div>`;
    }).join('');
    host.innerHTML = html;
    const filledCount = _IH_SLOT_ORDER.filter(z => byZone[z]).length;
    host.classList.toggle('ih-pets--full', filledCount >= 5);
    if (html && window.lucide) lucide.createIcons();
}

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
        // Merge active + completed so graduated characters stay visible in slots.
        // Zone collision: active takes priority (active char may be in same zone as a
        // completed one if the player started a second character in the same zone).
        const active    = d.active_characters    || [];
        const completed = d.completed_characters || [];
        const allChars  = [...active, ...completed];
        const lumi = d.currency?.lumi ?? 0;
        if (allChars.length > 0) {
            _renderHomePets(allChars);
            // Count unique zones actually rendered (zone-dedup, same as _renderHomePets logic)
            const byZone = {};
            allChars.forEach(c => { byZone[c.zone] = c; });
            const cnt = Object.keys(byZone).length;
            if (charEl) charEl.textContent = `${cnt} / 5 characters`;
        } else {
            _renderHomePetsEmpty();
            if (charEl) charEl.textContent = '0 / 5 characters';
        }
        if (lumiEl) lumiEl.textContent = lumi.toLocaleString();

        // Evo badge — show if any active character can evolve
        const anyReady = active.some(c => c.ready_to_evolve);
        let evoBadge = document.getElementById('island-home-evo-badge');
        if (anyReady) {
            if (!evoBadge && cardEl) {
                evoBadge = document.createElement('div');
                evoBadge.id = 'island-home-evo-badge';
                evoBadge.className = 'island-home-evo-badge';
                evoBadge.textContent = 'Ready to Evolve!';
                cardEl.insertBefore(evoBadge, cardEl.firstChild);
            } else if (evoBadge) {
                evoBadge.style.display = '';
            }
        } else if (evoBadge) {
            evoBadge.style.display = 'none';
        }

        // P3: warn badge — red dot if any active character has hunger or happiness < 30
        const anyWarn = active.some(c => (c.hunger ?? 100) < 30 || (c.happiness ?? 100) < 30);
        let warnBadge = document.getElementById('island-home-warn-badge');
        if (anyWarn) {
            if (!warnBadge && cardEl) {
                warnBadge = document.createElement('div');
                warnBadge.id = 'island-home-warn-badge';
                warnBadge.className = 'island-home-warn-badge';
                warnBadge.title = 'A character needs care!';
                cardEl.insertBefore(warnBadge, cardEl.firstChild);
            } else if (warnBadge) {
                warnBadge.style.display = '';
            }
        } else if (warnBadge) {
            warnBadge.style.display = 'none';
        }
    } catch (_) {
        if (charEl) charEl.textContent = 'Your island awaits';
        if (lumiEl) lumiEl.textContent = '';
    }
}
