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
let _zdZone      = null;
let _zdProg      = null;   // active character progress object
let _zdCareData  = null;   // /care/{id} response
let _zdCatalog   = {};     // character_id → catalog entry
let _zdCompleted = [];
let _zdLocked    = [];

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
        const [activeData, completedData, silData] = await Promise.all([
            apiFetchJSON(`/api/island/character/active?zone=${zone}`),
            apiFetchJSON('/api/island/character/completed'),
            apiFetchJSON('/api/island/character/silhouette'),
        ]);
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

/** Placed-decorations renderer (stub — wired up when /api/island/placed-items lands). @tag SHOP */
function _zdRenderPlacedItems() {
    // TODO: fetch from /api/island/placed-items?zone=… and render <img> per item
    // with absolute left/top from item.position_x/y. For now: empty layer.
    return '';
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
    const stoneLabels = { first_a: '1st Stone (A)', first_b: '1st Stone (B)', second_a: '2nd Stone (A)', second_b: '2nd Stone (B)' };
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
                <button class="izd-btn izd-btn--shop" onclick="openIslandShop()">
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

/** Open Decorate mode (stub — actual placement UI pending placed-items API). @tag SHOP */
function _zdOpenDecorate() {
    _showShopToast('Decoration placement coming soon!', false);
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
        _showShopToast('Complete a previous zone to unlock characters here.', true);
        return;
    }
    const meta  = _ZONE_META[_zdZone] || {};
    const cards = adoptable.map(c => {
        const fb = (meta.lucideIcon || 'heart');
        const adoptVisual = _charImg(c.name || '', 'baby', c.images || '{}', fb);
        return `
        <div class="izd-adopt-card" onclick="_zdAdoptStart(${c.character_id})"
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
            <button class="izd-back-link" onclick="openZoneDetail('${_zdZone}')">
                <i data-lucide="x"></i> Cancel
            </button>
        </div>`);
    if (typeof lucide !== 'undefined') lucide.createIcons();
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
        openZoneDetail(_zdZone);
    } catch (_) {
        if (btn) btn.disabled = false;
        _showShopToast('Could not adopt. Please try again.', true);
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
