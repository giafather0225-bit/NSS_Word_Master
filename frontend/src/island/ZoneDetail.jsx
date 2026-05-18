/* ================================================================
   ZoneDetail.jsx — Island zone detail screen: active character,
                    care gauges, completed/locked strip, actions.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/character/active?zone=,
                  GET /api/island/character/silhouette?zone=,
                  GET /api/island/care/{id},
                  POST /api/island/care/feed
   ================================================================ */

// ─── Image helper ───────────────────────────────────────────────

/**
 * Return an <img> for the given stage, falling back to a Lucide icon.
 * imagesJson: raw JSON string from island_characters.images column.
 * fallbackIcon: Lucide icon name (e.g. 'tree-pine').
 * @tag SHOP
 */
function _charImg(name, stage, imagesJson, fallbackIcon) {
    let imgs = {};
    try { imgs = JSON.parse(imagesJson || '{}'); } catch (_) {}
    const rel = imgs[stage] || imgs['baby'];
    if (!rel) return `<span class="izd-char-emoji-fb"><i data-lucide="${fallbackIcon || 'heart'}"></i></span>`;
    const src = `/static/img/island/${rel}`;
    return `<img class="izd-char-img" src="${src}" alt="${escapeHtml(name)}"
                 onerror="this.outerHTML='<span class=\\'izd-char-emoji-fb\\'><i data-lucide=\\'${fallbackIcon || 'heart'}\\'></i></span>';if(typeof lucide!='undefined')lucide.createIcons()">`;
}

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _zdZone       = null;
let _zdProg       = null;   // active character progress object
let _zdCareData   = null;   // /care/{id} response
let _zdCatalog    = {};     // character_id → catalog entry
let _zdCompleted  = [];
let _zdLocked     = [];
let _zdPlaced     = [];     // /placed?zone= response items
let _zdDecorating = false;  // true while in Decorate mode
let _zdDecorInv   = [];     // decoration inventory snapshot
let _zdSelectedInv = null;  // currently-selected inv id for placement
let _zdGhostEl    = null;   // floating ghost preview during placement

// ─── Open / Close ───────────────────────────────────────────────

/** Show zone detail for the given zone key. @tag SHOP */
function openZoneDetail(zone) {
    _zdZone = zone;
    const el = document.getElementById('isl-detail-overlay');
    if (!el) return;
    el.classList.remove('hidden');
    el.dataset.screen = 'zone';
    _zdRenderLoading(el);
    _zdLoad(zone, el);
}

/** Return to island map. @tag SHOP */
function _closeZoneDetail() {
    const el = document.getElementById('isl-detail-overlay');
    if (el) { el.classList.add('hidden'); el.innerHTML = ''; }
    _zdZone = _zdProg = _zdCareData = null;
}

// ─── Data loading ────────────────────────────────────────────────

/** @tag SHOP */
async function _zdLoad(zone, el) {
    try {
        const [activeData, completedData, silData, placedData] = await Promise.all([
            apiFetchJSON(`/api/island/character/active?zone=${zone}`),
            apiFetchJSON('/api/island/character/completed'),
            apiFetchJSON('/api/island/character/silhouette'),
            apiFetchJSON(`/api/island/placed?zone=${zone}`).catch(() => ({ items: [] })),
        ]);
        _zdPlaced = placedData.items || [];
        _zdProg      = activeData.characters?.[0] || null;
        _zdCompleted = (completedData.characters || []).filter(c => c.zone === zone);

        // Build catalog from silhouette (character_id → {name, zone, adoptable, …})
        _zdCatalog = {};
        (silData.characters || []).forEach(c => { _zdCatalog[c.character_id] = c; });

        // Locked = in this zone, not adoptable, not currently active or completed
        const activeIds = new Set((activeData.characters || []).map(c => c.character_id));
        const doneIds   = new Set(_zdCompleted.map(c => c.character_id));
        _zdLocked = (silData.characters || []).filter(c =>
            c.zone === zone && !c.adoptable && !activeIds.has(c.character_id) && !doneIds.has(c.character_id)
        );

        _zdCareData = null;
        if (_zdProg) {
            _zdCareData = await apiFetchJSON(`/api/island/care/${_zdProg.id}`);
        }
        _zdRender(el);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    } catch (_) {
        _zdRenderError(el);
    }
}

// ─── Loading / Error states ──────────────────────────────────────

/** @tag SHOP */
function _zdRenderLoading(el) {
    el.innerHTML = `<div class="izd-screen"><div class="isl-state-screen">
        <div class="isl-loading-ship"><i data-lucide="anchor"></i></div>
        <div class="isl-state-text">Loading zone...</div>
    </div></div>`;
}

/** @tag SHOP */
function _zdRenderError(el) {
    el.innerHTML = `<div class="izd-screen"><div class="isl-state-screen">
        <div class="isl-state-icon"><i data-lucide="wifi-off"></i></div>
        <div class="isl-state-text">Could not load zone data.</div>
        <button class="isl-retry-btn" onclick="openZoneDetail('${_zdZone}')">Retry</button>
        <button class="isl-back-btn"  onclick="_closeZoneDetail()">← Back</button>
    </div></div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Main render — Scene-Stage layout ────────────────────────────
//
// Layout:
//   ┌──────────────────────────────────────┐
//   │  STAGE  (≈62% height)                │
//   │  ── full-bleed zone bg image         │
//   │  ── back btn + zone label (overlay)  │
//   │  ── decoration layer (placed items)  │
//   │  ── character (large, centered)      │
//   ├──────────────────────────────────────┤
//   │  HUD    (≈38% height)                │
//   │  ── name + level                     │
//   │  ── gauges + XP + stone              │
//   │  ── actions (Feed/Evolve/Shop/Decor) │
//   │  ── completed/locked strips          │
//   └──────────────────────────────────────┘

/** @tag SHOP */
function _zdRender(el) {
    const meta     = _ZONE_META[_zdZone] || {};
    const isLegend = _zdZone === 'legend';
    const prog     = _zdProg;

    el.innerHTML = `
        <div class="izd-screen izd-zone--${_zdZone}" id="izd-screen">
            <div class="izd-stage" id="izd-stage"
                 style="background-image:url('/static/img/island/bg_${_zdZone}.png')">
                <button class="izd-back-btn" onclick="_closeZoneDetail()" aria-label="Back to map">
                    <i data-lucide="arrow-left"></i>
                </button>
                <div class="izd-zone-label"><i data-lucide="${meta.lucideIcon || 'map-pin'}"></i> ${meta.label || _zdZone}</div>
                <div class="izd-stage-decor" id="izd-stage-decor">
                    ${_zdRenderPlacedItems()}
                </div>
                ${prog ? _zdStageChar(prog) : _zdStageEmpty()}
            </div>
            <div class="izd-hud" id="izd-hud">
                ${prog ? _zdHudPanel(prog, isLegend) : _zdEmptyHud()}
                ${_zdStripsRow()}
            </div>
        </div>`;
    _zdAttachEsc();
}

// ─── Stage layer: character + decorations ────────────────────────

/** Big character standing in the scene. Click → character detail page. @tag SHOP */
function _zdStageChar(prog) {
    const cat   = _zdCatalog[prog.character_id] || {};
    const h     = prog.hunger ?? 100, p = prog.happiness ?? 100;
    const animCls = (h < 20 || p < 20) ? 'izd-stage-char--sad'
                  : (h >= 60 && p >= 60) ? 'izd-stage-char--happy' : '';
    const fallbackIcon = (_ZONE_META?.[cat.zone] || {}).lucideIcon || 'heart';
    const charVisual = _charImg(cat.name || '', prog.stage || 'baby', prog.images || '{}', fallbackIcon);
    return `
        <div class="izd-stage-char ${animCls}"
             onclick="_zdOpenCharDetail(${prog.id})"
             role="button" tabindex="0" title="View details">
            ${charVisual}
        </div>`;
}

/** Empty stage when no character — big adopt invite. @tag SHOP */
function _zdStageEmpty() {
    return `
        <div class="izd-stage-empty"
             onclick="_zdAdopt()" role="button" tabindex="0">
            <div class="izd-stage-empty-circle">
                <i data-lucide="plus-circle"></i>
            </div>
            <div class="izd-stage-empty-text">Adopt a companion</div>
        </div>`;
}

/** Render all placed decorations for this zone (uses _zdPlaced). @tag SHOP */
function _zdRenderPlacedItems() {
    if (!_zdPlaced.length) return '';
    return _zdPlaced.map(p => {
        const x = (p.pos_x ?? 50);
        const y = (p.pos_y ?? 50);
        const visual = _zdDecorVisual(p.image, p.name, p.sub_category);
        const handler = `onmousedown="_zdDecorMouseDown(event,${p.id},this)"`;
        return `<div class="izd-decor" data-placed-id="${p.id}"
                     style="left:${x}%;top:${y}%" ${handler}>${visual}</div>`;
    }).join('');
}

/** Build visual for a decoration: <img> with placeholder fallback. @tag SHOP */
function _zdDecorVisual(image, name, subCat) {
    const lucide = _zdDecorIcon(subCat);
    const safe   = escapeHtml(name || '');
    const phCls  = `izd-decor-ph izd-decor-ph--${escapeHtml(subCat || 'common')}`;
    const phHtml = `<div class="${phCls}">
        <i data-lucide="${lucide}"></i>
        <span class="izd-decor-ph-label">${safe}</span>
    </div>`;
    if (!image) return phHtml;
    const src = `/static/img/island/${image}`;
    // Inline onerror swaps to placeholder if PNG missing
    return `<img src="${src}" alt="${safe}" draggable="false"
                 onerror="this.outerHTML=${JSON.stringify(phHtml).replace(/"/g, '&quot;')};
                          if(typeof lucide!='undefined')lucide.createIcons()">`;
}

/** Map sub_category → Lucide icon name. @tag SHOP */
function _zdDecorIcon(subCat) {
    const map = {
        prop:      'package',
        building:  'home',
        nature:    'trees',
        landscape: 'mountain',
        special:   'sparkles',
        common:    'star',
        dragon:    'flame',
        unicorn:   'rainbow',
        phoenix:   'flame',
        gumiho:    'moon',
        qilin:     'paw-print',
    };
    return map[subCat] || 'star';
}

// ─── HUD: stats + actions ────────────────────────────────────────

/** @tag SHOP */
function _zdHudPanel(prog, isLegend) {
    const cat    = _zdCatalog[prog.character_id] || {};
    const name   = escapeHtml((prog.nickname || cat.name || 'Character').substring(0, 12));
    const stage  = escapeHtml(prog.stage || 'baby');
    const xp     = _zdCareData?.current_xp        ?? prog.current_xp   ?? 0;
    const maxXp  = _zdCareData?.xp_to_next_level  ?? 100;
    const xpPct  = Math.min(100, Math.round(xp / maxXp * 100));
    const stoneRaw = _zdCareData?.evolution_stone ?? 'None';
    const stoneLabels = {
        first_a: '1st Stone (A)', first_b: '1st Stone (B)',
        second: '2nd Stone',
        second_a: '2nd Stone (A)', second_b: '2nd Stone (B)',
        legend_first_a: 'Legend Stone (A)', legend_first_b: 'Legend Stone (B)',
        legend_second: 'Legend Stone (2nd)',
    };
    const stone = stoneLabels[stoneRaw] || (stoneRaw === 'None' ? '—' : stoneRaw);
    const canEvo = _zdCareData?.can_evolve        ?? false;
    const lumiPd = cat.lumi_production            ?? 0;
    const h = prog.hunger ?? 0, p = prog.happiness ?? 0;
    const status  = h < 20 ? 'Hungry — needs food!'
                  : p < 20 ? 'Feeling lonely...'
                  : h >= 80 && p >= 80 ? 'Feeling great!' : 'Doing okay.';

    return `
        <div class="izd-hud-head">
            <div class="izd-hud-id">
                <span class="izd-hud-stage-pill">${stage}</span>
                <div class="izd-hud-name">${name}</div>
                <div class="izd-hud-lv">Lv. ${prog.level || 1} &middot; ${status}</div>
            </div>
            <div class="izd-hud-actions">
                <button class="izd-btn izd-btn--feed" onclick="_zdFeed(${prog.id})">
                    <i data-lucide="apple"></i> Feed
                </button>
                <button class="izd-btn izd-btn--evo${canEvo ? '' : ' disabled'}"
                        onclick="${canEvo ? `_zdOpenEvolution(${prog.id})` : ''}"
                        ${canEvo ? '' : 'disabled title="Not ready yet"'}>
                    <i data-lucide="sparkles"></i> Evolve
                </button>
                <button class="izd-btn izd-btn--shop" onclick="openRewardShop('evolution')">
                    <i data-lucide="shopping-bag"></i> Shop
                </button>
                <button class="izd-btn izd-btn--decor" onclick="_zdOpenDecorate()">
                    <i data-lucide="palette"></i> Decorate
                </button>
            </div>
        </div>
        ${isLegend ? _zdLegendDays(prog) : ''}
        <div class="izd-hud-stats">
            <div class="izd-hud-stat-col">
                ${_zdGauge('Hunger', h, 'izd-g--hunger')}
                ${_zdGauge('Happy',  p, 'izd-g--happy')}
            </div>
            <div class="izd-hud-stat-col">
                <div class="izd-hud-xp-row">
                    <span class="izd-hud-stat-label">XP</span>
                    <div class="izd-bar-wrap izd-bar-wrap--inline">
                        <div class="izd-bar-fill" style="width:${xpPct}%"></div>
                    </div>
                    <span class="izd-hud-xp-val">${xp}/${maxXp}</span>
                </div>
                <div class="izd-hud-meta-row">
                    <span class="izd-hud-meta-key">Stone</span>
                    <span class="izd-hud-meta-val">${escapeHtml(stone)}</span>
                    ${lumiPd ? `<span class="izd-hud-meta-key">&nbsp;Lumi</span>
                        <span class="izd-hud-meta-val">+${lumiPd}/day</span>` : ''}
                </div>
            </div>
        </div>`;
}

/** @tag SHOP */
function _zdEmptyHud() {
    return `<div class="izd-hud-empty">
        <div class="izd-hud-empty-title">No character here yet</div>
        <p class="izd-hud-empty-hint">Complete the previous character to unlock the next one, or tap the circle above to adopt.</p>
    </div>`;
}

/** Compact completed/locked strips at the bottom of HUD. @tag SHOP */
function _zdStripsRow() {
    const done = _zdCompleted.length ? _zdCompleted.map(c => {
        const n = escapeHtml((c.nickname || c.name || '?').substring(0, 6));
        return `<div class="izd-done-char" title="${n}">
            <div class="izd-done-dot"></div><span>${n}</span></div>`;
    }).join('') : '';
    const locked = _zdLocked.length ? _zdLocked.map(() =>
        `<div class="izd-locked-char"><i data-lucide="lock"></i></div>`
    ).join('') : '';
    if (!done && !locked) return '';
    return `
        <div class="izd-strips-row">
            ${done   ? `<div class="izd-done-strip"><span class="izd-strip-label">Completed</span>${done}</div>`     : ''}
            ${locked ? `<div class="izd-locked-strip"><span class="izd-strip-label">Locked</span>${locked}</div>` : ''}
        </div>`;
}

// ─── Decorate mode ───────────────────────────────────────────────

/** Enter Decorate mode: load decoration inventory + swap HUD with toolbar. @tag SHOP */
async function _zdOpenDecorate() {
    if (_zdDecorating) return;
    try {
        const inv = await apiFetchJSON('/api/island/inventory?category=decoration');
        // Filter to items applicable to this zone (zone === current OR 'all')
        _zdDecorInv = (inv.items || []).filter(i =>
            i.quantity > 0 && (
                _zdAcceptZone(i.shop_item_id, _zdZone)
            )
        );
    } catch (_) {
        _showShopToast('Could not load decorations.', true);
        return;
    }
    _zdDecorating  = true;
    _zdSelectedInv = null;
    const stage = document.getElementById('izd-stage');
    if (stage) stage.classList.add('izd-stage--decorating');
    _zdRenderDecorHud();
    _zdAttachStagePlacementListener();
}

/** Exit Decorate mode: restore HUD, drop ghost, clear listeners. @tag SHOP */
function _zdCloseDecorate() {
    _zdDecorating  = false;
    _zdSelectedInv = null;
    const stage = document.getElementById('izd-stage');
    if (stage) stage.classList.remove('izd-stage--decorating');
    _zdRemoveGhost();
    _zdDetachStagePlacementListener();
    // Re-render full HUD with normal panel
    const hud = document.getElementById('izd-hud');
    if (hud && _zdProg) {
        const isLegend = _zdZone === 'legend';
        hud.innerHTML = _zdHudPanel(_zdProg, isLegend) + _zdStripsRow();
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

/** Quick check: is this shop item placeable in this zone? @tag SHOP */
function _zdAcceptZone(shopItemId, zone) {
    // Item zone metadata is on the inventory entry's joined name only — for
    // simplicity, accept any decoration whose backend already validates zone
    // on /decorate/place. The API will reject mismatches.
    return true;
}

/** Render the Decorate-mode toolbar + inventory drawer in place of HUD. @tag SHOP */
function _zdRenderDecorHud() {
    const hud = document.getElementById('izd-hud');
    if (!hud) return;
    const items = _zdDecorInv;
    const inv = items.length
        ? items.map(it => {
            const sel = (_zdSelectedInv === it.id) ? ' izd-decor-inv-item--selected' : '';
            const visual = _zdDecorVisual(it.image, it.name, it.sub_category || 'common');
            return `<div class="izd-decor-inv-item${sel}" onclick="_zdSelectDecor(${it.id})">
                <div class="izd-decor-inv-thumb">${visual}</div>
                <div class="izd-decor-inv-name" title="${escapeHtml(it.name)}">${escapeHtml(it.name)}</div>
                <div class="izd-decor-inv-qty">×${it.quantity}</div>
            </div>`;
        }).join('')
        : `<div class="izd-decor-inv-empty">No decorations in your inventory yet.<br>Visit the shop to buy some!</div>`;
    hud.innerHTML = `
        <div class="izd-decor-toolbar">
            <div class="izd-decor-toolbar-title">
                <i data-lucide="palette"></i> Decorate Mode
            </div>
            <div class="izd-decor-toolbar-hint">
                ${items.length ? 'Pick an item, then click on the scene to place it.' : ''}
            </div>
            <button class="izd-decor-toolbar-btn" onclick="_zdCloseDecorate()">
                Done
            </button>
        </div>
        <div class="izd-decor-inv">${inv}</div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** Select a decoration to place; tap on stage will drop it there. @tag SHOP */
function _zdSelectDecor(invId) {
    _zdSelectedInv = (_zdSelectedInv === invId) ? null : invId;
    _zdRenderDecorHud();
    _zdRemoveGhost();
    if (_zdSelectedInv) _zdAttachGhost();
}

/** Attach floating ghost preview that follows cursor while a decor is selected. @tag SHOP */
function _zdAttachGhost() {
    if (!_zdSelectedInv) return;
    const it = _zdDecorInv.find(x => x.id === _zdSelectedInv);
    if (!it) return;
    _zdGhostEl = document.createElement('div');
    _zdGhostEl.className = 'izd-decor-ghost';
    _zdGhostEl.innerHTML = _zdDecorVisual(it.image, it.name, it.sub_category || 'common');
    document.body.appendChild(_zdGhostEl);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    document.addEventListener('mousemove', _zdGhostMove);
}
function _zdRemoveGhost() {
    if (_zdGhostEl) { _zdGhostEl.remove(); _zdGhostEl = null; }
    document.removeEventListener('mousemove', _zdGhostMove);
}
function _zdGhostMove(e) {
    if (!_zdGhostEl) return;
    _zdGhostEl.style.left = `${e.clientX}px`;
    _zdGhostEl.style.top  = `${e.clientY}px`;
}

/** Stage click handler — converts click coords to %, posts /decorate/place. @tag SHOP */
function _zdStageClick(e) {
    if (!_zdDecorating || !_zdSelectedInv) return;
    if (e.target.closest('.izd-decor')) return;  // clicking existing item handled separately
    const stage = document.getElementById('izd-stage');
    if (!stage) return;
    const rect = stage.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width)  * 100;
    const y = ((e.clientY - rect.top)  / rect.height) * 100;
    _zdPlaceSelected(x, y);
}
function _zdAttachStagePlacementListener() {
    const stage = document.getElementById('izd-stage');
    if (stage) stage.addEventListener('click', _zdStageClick);
}
function _zdDetachStagePlacementListener() {
    const stage = document.getElementById('izd-stage');
    if (stage) stage.removeEventListener('click', _zdStageClick);
}

/** POST place selected decoration at (x%, y%). @tag SHOP */
async function _zdPlaceSelected(x, y) {
    const invId = _zdSelectedInv;
    const it = _zdDecorInv.find(i => i.id === invId);
    if (!it) return;
    try {
        await apiFetchJSON('/api/island/decorate/place', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                inventory_id: invId,
                zone: _zdZone,
                // Backend stores integer % (0–100). Round + clamp.
                pos_x: Math.max(0, Math.min(100, Math.round(x))),
                pos_y: Math.max(0, Math.min(100, Math.round(y))),
            }),
        });
        _showShopToast(`${it.name} placed!`);
        // Decrement local quantity, refresh both layers
        it.quantity -= 1;
        if (it.quantity <= 0) {
            _zdDecorInv = _zdDecorInv.filter(i => i.id !== invId);
            _zdSelectedInv = null;
            _zdRemoveGhost();
        }
        // Refresh placed list and re-render decor layer
        const placedData = await apiFetchJSON(`/api/island/placed?zone=${_zdZone}`);
        _zdPlaced = placedData.items || [];
        const layer = document.getElementById('izd-stage-decor');
        if (layer) layer.innerHTML = _zdRenderPlacedItems();
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _zdRenderDecorHud();
    } catch (e) {
        _showShopToast(e?.detail || 'Could not place item.', true);
    }
}

/**
 * Mousedown on a placed decoration — distinguishes click vs drag.
 * - movement ≤ 5px: treat as click → show Remove popup (legacy behavior).
 * - movement >  5px: drag → live-track cursor, POST /decorate/move on release.
 * Only active in decorate mode. @tag SHOP
 */
function _zdDecorMouseDown(e, placedId, el) {
    if (e.button !== 0) return;            // left click only
    // Outside decorate mode: click-only (no drag) to show Remove popup
    if (!_zdDecorating) {
        e.stopPropagation();
        _zdDecorClick(placedId, el);
        return;
    }
    e.stopPropagation();
    e.preventDefault();

    const stage = document.getElementById('izd-stage');
    if (!stage) return;
    const stageRect = stage.getBoundingClientRect();
    const startX = e.clientX, startY = e.clientY;
    const DRAG_THRESHOLD = 5;
    let dragging = false;

    function _toPct(clientX, clientY) {
        const x = ((clientX - stageRect.left) / stageRect.width)  * 100;
        const y = ((clientY - stageRect.top)  / stageRect.height) * 100;
        return [
            Math.max(0, Math.min(100, Math.round(x))),
            Math.max(0, Math.min(100, Math.round(y))),
        ];
    }

    function onMove(ev) {
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;
        if (!dragging && Math.hypot(dx, dy) > DRAG_THRESHOLD) {
            dragging = true;
            el.classList.add('izd-decor--dragging');
            // Hide ghost preview if any (don't double-render).
            if (_zdGhostEl) _zdGhostEl.style.display = 'none';
        }
        if (dragging) {
            const [px, py] = _toPct(ev.clientX, ev.clientY);
            el.style.left = `${px}%`;
            el.style.top  = `${py}%`;
        }
    }

    async function onUp(ev) {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup',   onUp);
        if (_zdGhostEl) _zdGhostEl.style.display = '';
        if (!dragging) {
            // Click → existing Remove popup behavior.
            _zdDecorClick(placedId, el);
            return;
        }
        el.classList.remove('izd-decor--dragging');
        const [px, py] = _toPct(ev.clientX, ev.clientY);
        // Optimistic local update — already moved visually above.
        const placed = _zdPlaced.find(p => p.id === placedId);
        if (placed) { placed.pos_x = px; placed.pos_y = py; }
        try {
            await apiFetchJSON('/api/island/decorate/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ placed_item_id: placedId, pos_x: px, pos_y: py }),
            });
        } catch (err) {
            _showShopToast(err?.detail || 'Could not move item.', true);
            // Revert by refetching authoritative state.
            try {
                const data = await apiFetchJSON(`/api/island/placed?zone=${_zdZone}`);
                _zdPlaced = data.items || [];
                const layer = document.getElementById('izd-stage-decor');
                if (layer) layer.innerHTML = _zdRenderPlacedItems();
                if (typeof lucide !== 'undefined') lucide.createIcons();
            } catch {}
        }
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup',   onUp);
}

/** Click an already-placed item → show Remove popup (works in and out of decorate mode). @tag SHOP */
function _zdDecorClick(placedId, btnEl) {
    document.querySelectorAll('.izd-decor-popup').forEach(n => n.remove());
    const popup = document.createElement('div');
    popup.className = 'izd-decor-popup';
    popup.innerHTML = `<button onclick="_zdRemovePlaced(${placedId})">
        <i data-lucide="trash-2"></i> Remove
    </button>`;
    btnEl.appendChild(popup);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    // Auto-dismiss on outside click
    setTimeout(() => {
        const close = ev => {
            if (!popup.contains(ev.target)) {
                popup.remove();
                document.removeEventListener('click', close, true);
            }
        };
        document.addEventListener('click', close, true);
    }, 0);
}

/** Remove a placed item back to inventory. @tag SHOP */
async function _zdRemovePlaced(placedId) {
    try {
        await apiFetchJSON('/api/island/decorate/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ placed_item_id: placedId }),
        });
        _showShopToast('Returned to inventory.');
        // Refresh both layers
        const [placedData, invData] = await Promise.all([
            apiFetchJSON(`/api/island/placed?zone=${_zdZone}`),
            apiFetchJSON('/api/island/inventory?category=decoration'),
        ]);
        _zdPlaced   = placedData.items || [];
        _zdDecorInv = (invData.items || []).filter(i => i.quantity > 0);
        const layer = document.getElementById('izd-stage-decor');
        if (layer) layer.innerHTML = _zdRenderPlacedItems();
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _zdRenderDecorHud();
    } catch (e) {
        _showShopToast(e?.detail || 'Could not remove item.', true);
    }
}

/** @tag SHOP */
function _zdLegendDays(prog) {
    const d  = prog.consecutive_days ?? 0;
    const p1 = Math.min(100, Math.round(d / 14 * 100));
    const p2 = Math.min(100, Math.round(d / 30 * 100));
    return `<div class="izd-legend-days">
        <div class="izd-ld-row"><span>1st Evo</span>
            <div class="izd-bar-wrap izd-bar-wrap--sm">
                <div class="izd-bar-fill" style="width:${p1}%"></div></div>
            <span>${Math.min(d,14)}/14</span></div>
        <div class="izd-ld-row"><span>2nd Evo</span>
            <div class="izd-bar-wrap izd-bar-wrap--sm">
                <div class="izd-bar-fill izd-bar-fill--legend" style="width:${p2}%"></div></div>
            <span>${Math.min(d,30)}/30</span></div>
    </div>`;
}

/** @tag SHOP */
function _zdGauge(label, val, cls) {
    const pct = Math.max(0, Math.min(100, val));
    const fc  = pct < 20 ? 'izd-gf--low' : pct < 60 ? 'izd-gf--mid' : 'izd-gf--ok';
    return `<div class="izd-gauge-row">
        <span class="izd-gauge-label">${label}</span>
        <div class="izd-gauge-bar ${cls}"><div class="izd-gauge-fill ${fc}" style="width:${pct}%"></div></div>
        <span class="izd-gauge-pct">${pct}%</span>
    </div>`;
}

// ─── Actions ─────────────────────────────────────────────────────

/** @tag SHOP */
async function _zdFeed(progId) {
    try {
        const inv = await apiFetchJSON('/api/island/inventory?category=food');
        const food = (inv.items || []).find(i => i.quantity > 0);
        if (!food) {
            _showShopToast('No food in inventory. Visit the shop!', true);
            return;
        }
        const res = await fetch('/api/island/care/feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character_progress_id: progId, inventory_id: food.id }),
        });
        if (res.ok) {
            _showShopToast('Fed! XP gained.');
            openZoneDetail(_zdZone);
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || 'Feed failed.', true);
        }
    } catch (_) { _showShopToast('Feed failed.', true); }
}

/** @tag SHOP */
function _zdOpenCharDetail(progId) { openCharacterDetail(progId, _zdZone); }

/** @tag SHOP */
function _zdOpenEvolution(progId) {
    const prog = _zdProg, cat = _zdCatalog[prog?.character_id] || {};
    openEvolutionModal(progId, prog?.stage, prog?.nickname || cat.name || 'Character');
}

// ─── Adopt flow ──────────────────────────────────────────────────

/** Show adoptable character picker for this zone. @tag SHOP */
function _zdAdopt() {
    const adoptable = Object.values(_zdCatalog).filter(c => c.zone === _zdZone && c.adoptable);
    if (!adoptable.length) {
        const hasActive = Object.values(_zdCatalog).some(c => c.zone === _zdZone && c.already_active);
        const msg = hasActive
            ? 'A character from this zone is already being raised.'
            : 'Complete a previous zone to unlock characters here.';
        _showShopToast(msg, true);
        return;
    }
    const meta  = _ZONE_META[_zdZone] || {};
    const cards = adoptable.map(c => {
        const fb = (meta.lucideIcon || 'heart');
        const adoptVisual = _charImg(c.name || '', 'baby', c.images || '{}', fb);
        return `
        <div class="izd-adopt-card" data-char-id="${c.character_id}"
             onclick="_zdAdoptSelect(${c.character_id})"
             role="button" tabindex="0">
            <div class="izd-adopt-emoji">${adoptVisual}</div>
            <div class="izd-adopt-name">${escapeHtml(c.name)}</div>
        </div>`;
    }).join('');
    const stage = document.getElementById('izd-stage');
    if (!stage) return;
    // Replace stage-empty / stage-char with adopt panel
    stage.querySelectorAll('.izd-stage-char,.izd-stage-empty,.izd-adopt-panel').forEach(n => n.remove());
    stage.insertAdjacentHTML('beforeend', `
        <div class="izd-adopt-panel">
            <div class="izd-adopt-title">Choose your companion</div>
            <div class="izd-adopt-grid">${cards}</div>
            <div class="izd-adopt-actions">
                <button id="izd-adopt-next" class="izd-btn izd-btn--feed" disabled
                        onclick="_zdAdoptStartSelected()">
                    <i data-lucide="arrow-right"></i> Next
                </button>
                <button class="izd-back-link" onclick="openZoneDetail('${_zdZone}')">
                    <i data-lucide="x"></i> Cancel
                </button>
            </div>
        </div>`);
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** Highlight selected adopt card and enable the Next button. @tag SHOP */
function _zdAdoptSelect(charId) {
    document.querySelectorAll('.izd-adopt-card').forEach(el => {
        el.classList.toggle('izd-adopt-card--selected', el.dataset.charId == charId);
    });
    const nextBtn = document.getElementById('izd-adopt-next');
    if (nextBtn) {
        nextBtn.disabled = false;
        nextBtn.onclick = () => _zdAdoptStart(charId);
    }
}

/** Proceed to name input for the currently selected character. @tag SHOP */
function _zdAdoptStartSelected() {
    const sel = document.querySelector('.izd-adopt-card--selected');
    if (!sel) return;
    _zdAdoptStart(Number(sel.dataset.charId));
}

/** Show nickname input for chosen character. @tag SHOP */
function _zdAdoptStart(charId) {
    const cat   = _zdCatalog[charId] || {};
    const stage = document.getElementById('izd-stage');
    if (!stage) return;
    stage.querySelectorAll('.izd-stage-char,.izd-stage-empty,.izd-adopt-panel').forEach(n => n.remove());
    stage.insertAdjacentHTML('beforeend', `
        <div class="izd-adopt-panel">
            <div class="izd-adopt-title">Name your companion</div>
            <div class="izd-adopt-hint">Max 8 characters</div>
            <input id="izd-adopt-input" class="iob-name-input"
                   type="text" maxlength="8"
                   placeholder="${escapeHtml(cat.name || 'Friend')}"
                   autocomplete="off" spellcheck="false" />
            <div class="izd-adopt-actions">
                <button class="izd-btn izd-btn--feed" onclick="_zdAdoptConfirm(${charId})">
                    <i data-lucide="check"></i> Adopt
                </button>
                <button class="izd-back-link" onclick="_zdAdopt()">
                    <i data-lucide="arrow-left"></i> Back
                </button>
            </div>
        </div>`);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    document.getElementById('izd-adopt-input')?.focus();
}

/** POST adopt and reload zone detail. @tag SHOP */
async function _zdAdoptConfirm(charId) {
    const input    = document.getElementById('izd-adopt-input');
    const cat      = _zdCatalog[charId] || {};
    const nickname = (input?.value?.trim() || cat.name || 'Friend').substring(0, 8);
    const btn      = document.querySelector('.izd-adopt-panel .izd-btn--feed');
    if (btn) btn.disabled = true;
    try {
        await apiFetchJSON('/api/island/character/adopt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character_id: charId, nickname }),
        });
        _showShopToast(`${escapeHtml(nickname)} joined your island!`);
        if (typeof _loadIslandCard === 'function') _loadIslandCard();
        openZoneDetail(_zdZone);
    } catch (err) {
        if (btn) btn.disabled = false;
        const msg = err?.detail || err?.message || '';
        const friendlyMsg = msg.toLowerCase().includes('already')
            ? 'This character is already being raised.'
            : 'Could not adopt. Please try again.';
        _showShopToast(friendlyMsg, true);
    }
}

/** @tag SHOP */
function _zdAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        const ov = document.getElementById('isl-detail-overlay');
        if (ov && ov.dataset.screen === 'zone') {
            document.removeEventListener('keydown', fn);
            _closeZoneDetail();
        }
    };
    document.addEventListener('keydown', fn);
}
