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
        const [activeData, silData] = await Promise.all([
            apiFetchJSON(`/api/island/character/active?zone=${zone}`),
            apiFetchJSON(`/api/island/character/silhouette?zone=${zone}`),
        ]);
        _zdProg      = activeData.active      || null;
        _zdCompleted = activeData.completed   || [];
        _zdLocked    = silData.locked         || [];
        (activeData.catalog || []).forEach(c => { _zdCatalog[c.id] = c; });

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
        <div class="isl-loading-ship">⛵</div>
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

// ─── Main render ─────────────────────────────────────────────────

/** @tag SHOP */
function _zdRender(el) {
    const meta     = _ZONE_META[_zdZone] || {};
    const isLegend = _zdZone === 'legend';
    const prog     = _zdProg;

    el.innerHTML = `
        <div class="izd-screen izd-zone--${_zdZone}" id="izd-screen">
            <button class="izd-back-btn" onclick="_closeZoneDetail()" aria-label="Back to map">
                <i data-lucide="arrow-left"></i>
            </button>
            <div class="izd-zone-label">${meta.icon || ''} ${meta.label || _zdZone}</div>
            <div class="izd-body">
                <div class="izd-left">
                    ${_zdCharVisual(prog)}
                    ${_zdDoneStrip()}
                    ${_zdLockedStrip()}
                </div>
                <div class="izd-right">
                    ${prog ? _zdRightPanel(prog, isLegend) : _zdEmptyRight()}
                </div>
            </div>
        </div>`;
    _zdAttachEsc();
}

// ─── Left panel ──────────────────────────────────────────────────

/** @tag SHOP */
function _zdCharVisual(prog) {
    if (!prog) return `
        <div class="izd-char-visual izd-char-visual--empty">
            <i data-lucide="plus-circle"></i>
            <span>No active character</span>
        </div>`;

    const cat   = _zdCatalog[prog.character_id] || {};
    const name  = escapeHtml((prog.nickname || cat.name || 'Character').substring(0, 12));
    const h = prog.hunger ?? 100, p = prog.happiness ?? 100;
    const animCls = (h < 20 || p < 20) ? 'izd-char-visual--sad'
                  : (h >= 60 && p >= 60) ? 'izd-char-visual--happy' : '';
    const status  = h < 20 ? 'Hungry — needs food!'
                  : p < 20 ? 'Feeling lonely...'
                  : h >= 80 && p >= 80 ? 'Feeling great!' : 'Doing okay.';
    return `
        <div class="izd-char-visual ${animCls}" onclick="_zdOpenCharDetail(${prog.id})"
             role="button" tabindex="0" title="View details">
            <div class="izd-char-avatar">
                <div class="izd-char-emoji">${_ZONE_META[_zdZone]?.icon || '🌟'}</div>
                <span class="izd-char-stage">${prog.stage || 'baby'}</span>
            </div>
            <div class="izd-char-name">${name}</div>
            <div class="izd-char-status">${status}</div>
        </div>`;
}

/** @tag SHOP */
function _zdDoneStrip() {
    if (!_zdCompleted.length) return '';
    const dots = _zdCompleted.map(c => {
        const n = escapeHtml((c.nickname || c.name || '?').substring(0, 6));
        return `<div class="izd-done-char" title="${n}">
            <div class="izd-done-dot"></div><span>${n}</span></div>`;
    }).join('');
    return `<div class="izd-done-strip"><span class="izd-strip-label">Completed</span>${dots}</div>`;
}

/** @tag SHOP */
function _zdLockedStrip() {
    if (!_zdLocked.length) return '';
    const dots = _zdLocked.map(() =>
        `<div class="izd-locked-char"><i data-lucide="lock"></i><span>???</span></div>`
    ).join('');
    return `<div class="izd-locked-strip">${dots}</div>`;
}

// ─── Right panel ─────────────────────────────────────────────────

/** @tag SHOP */
function _zdRightPanel(prog, isLegend) {
    const cat    = _zdCatalog[prog.character_id] || {};
    const name   = escapeHtml((prog.nickname || cat.name || 'Character').substring(0, 12));
    const xp     = _zdCareData?.current_xp        ?? prog.current_xp   ?? 0;
    const maxXp  = _zdCareData?.xp_to_next_level  ?? 100;
    const xpPct  = Math.min(100, Math.round(xp / maxXp * 100));
    const stone  = _zdCareData?.evolution_stone   ?? 'None';
    const canEvo = _zdCareData?.can_evolve        ?? false;
    const lumiPd = cat.lumi_production            ?? 0;
    const h = prog.hunger ?? 0, p = prog.happiness ?? 0;

    return `
        <div class="izd-info">
            <div class="izd-info-name">${name}</div>
            <div class="izd-info-lv">Lv. ${prog.level || 1} &middot; ${escapeHtml(prog.stage || 'baby')}</div>
            ${isLegend ? _zdLegendDays(prog) : ''}
            <div class="izd-gauges">
                ${_zdGauge('Hunger', h, 'izd-g--hunger')}
                ${_zdGauge('Happiness', p, 'izd-g--happy')}
            </div>
            <div class="izd-xp-row">
                <span>XP to evolve</span><span>${xp} / ${maxXp}</span>
            </div>
            <div class="izd-bar-wrap"><div class="izd-bar-fill" style="width:${xpPct}%"></div></div>
            <div class="izd-meta-row"><span>Stone</span>
                <span class="izd-meta-val">${escapeHtml(stone)}</span></div>
            ${lumiPd ? `<div class="izd-meta-row"><span>Lumi</span>
                <span class="izd-meta-val">+${lumiPd}/day</span></div>` : ''}
            <div class="izd-actions">
                <button class="izd-btn izd-btn--feed" onclick="_zdFeed(${prog.id})">
                    <i data-lucide="apple"></i> Feed
                </button>
                <button class="izd-btn izd-btn--evo${canEvo ? '' : ' disabled'}"
                        onclick="${canEvo ? `_zdOpenEvolution(${prog.id})` : ''}"
                        ${canEvo ? '' : 'disabled title="Not ready yet"'}>
                    <i data-lucide="sparkles"></i> Evolve
                </button>
                <button class="izd-btn izd-btn--shop" onclick="openRewardShop()">
                    <i data-lucide="shopping-bag"></i> Shop
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _zdEmptyRight() {
    return `<div class="izd-info izd-info--empty">
        <div class="izd-info-name">No character here yet</div>
        <p class="izd-info-hint">Complete the previous character to unlock the next one.</p>
    </div>`;
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
        const res = await fetch('/api/island/care/feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character_progress_id: progId }),
        });
        if (res.ok) {
            _showShopToast('Fed! Hunger restored.');
            openZoneDetail(_zdZone);
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || 'No food in inventory.', true);
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
