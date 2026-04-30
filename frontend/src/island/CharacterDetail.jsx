/* ================================================================
   CharacterDetail.jsx — Island character detail screen: large avatar,
                         gauges, XP, evolution path tree, actions.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), ZoneDetail.jsx
                 (openZoneDetail, _showShopToast, _zdZone)
   API endpoints: GET /api/island/care/{id},
                  POST /api/island/care/feed
   ================================================================ */

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _cdProgId = null;
let _cdZone   = null;
let _cdData   = null;   // /care/{id} response

// ─── Open / Close ───────────────────────────────────────────────

/** Show character detail for a progress id. @tag SHOP */
function openCharacterDetail(progId, zone) {
    _cdProgId = progId;
    _cdZone   = zone;
    const el = document.getElementById('isl-detail-overlay');
    if (!el) return;
    el.classList.remove('hidden');
    el.dataset.screen = 'character';
    _cdRenderLoading(el);
    _cdLoad(progId, el);
}

/** Return to zone detail. @tag SHOP */
function _closeCharDetail() {
    const el = document.getElementById('isl-detail-overlay');
    if (el) { el.classList.add('hidden'); el.innerHTML = ''; }
    _cdProgId = _cdZone = _cdData = null;
    if (_zdZone) openZoneDetail(_zdZone);
}

// ─── Data loading ─────────────────────────────────────────────

/** @tag SHOP */
async function _cdLoad(progId, el) {
    try {
        _cdData = await apiFetchJSON(`/api/island/care/${progId}`);
        _cdRender(el);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    } catch (_) {
        _cdRenderError(el);
    }
}

// ─── Loading / Error states ───────────────────────────────────

/** @tag SHOP */
function _cdRenderLoading(el) {
    el.innerHTML = `<div class="icd-screen"><div class="isl-state-screen">
        <div class="isl-loading-ship">⛵</div>
        <div class="isl-state-text">Loading character...</div>
    </div></div>`;
}

/** @tag SHOP */
function _cdRenderError(el) {
    el.innerHTML = `<div class="icd-screen"><div class="isl-state-screen">
        <div class="isl-state-icon"><i data-lucide="wifi-off"></i></div>
        <div class="isl-state-text">Could not load character data.</div>
        <button class="isl-retry-btn" onclick="openCharacterDetail(${_cdProgId},'${_cdZone}')">Retry</button>
        <button class="isl-back-btn"  onclick="_closeCharDetail()">← Back</button>
    </div></div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Main render ──────────────────────────────────────────────

/** @tag SHOP */
function _cdRender(el) {
    const d    = _cdData;
    const prog = d?.progress || {};
    const meta = window._ZONE_META?.[_cdZone] || {};

    const name   = escapeHtml((prog.nickname || prog.character_name || 'Character').substring(0, 16));
    const stage  = escapeHtml(prog.stage || 'baby');
    const lv     = prog.level || 1;
    const xp     = d.current_xp ?? prog.current_xp ?? 0;
    const maxXp  = d.xp_to_next_level ?? 100;
    const xpPct  = Math.min(100, Math.round(xp / maxXp * 100));
    const h      = prog.hunger    ?? 100;
    const p      = prog.happiness ?? 100;
    const canEvo = d.can_evolve   ?? false;
    const stone  = escapeHtml(d.evolution_stone ?? 'None');

    const animCls = (h < 20 || p < 20) ? 'icd-avatar--sad'
                  : (h >= 60 && p >= 60) ? 'icd-avatar--happy' : 'icd-avatar--idle';

    el.innerHTML = `
        <div class="icd-screen icd-zone--${_cdZone}" id="icd-screen">
            <button class="icd-back-btn" onclick="_closeCharDetail()" aria-label="Back to zone">
                <i data-lucide="arrow-left"></i>
            </button>
            <div class="icd-body">
                <div class="icd-hero">
                    <div class="icd-avatar ${animCls}" id="icd-avatar"
                         onclick="_cdBounce()" role="button" tabindex="0" title="Say hi!">
                        <div class="icd-avatar-emoji">${meta.icon || '🌟'}</div>
                        <span class="icd-avatar-stage">${stage}</span>
                    </div>
                    <div class="icd-hero-info">
                        <div class="icd-char-name">${name}</div>
                        <div class="icd-char-lv">Lv. ${lv} &middot; ${stage}</div>
                        <div class="icd-stone-row">
                            <span class="icd-stone-label">Stone</span>
                            <span class="icd-stone-val">${stone}</span>
                        </div>
                    </div>
                </div>
                <div class="icd-gauges">
                    ${_cdGauge('Hunger',    h, 'icd-g--hunger')}
                    ${_cdGauge('Happiness', p, 'icd-g--happy')}
                </div>
                <div class="icd-xp-section">
                    <div class="icd-xp-row">
                        <span>XP to evolve</span><span>${xp} / ${maxXp}</span>
                    </div>
                    <div class="icd-xp-bar-wrap">
                        <div class="icd-xp-bar-fill" style="width:${xpPct}%"></div>
                    </div>
                </div>
                ${prog.is_legend_type ? _cdLegendSection(prog) : _cdEvoTree(prog)}
                <div class="icd-actions">
                    <button class="izd-btn izd-btn--feed" onclick="_cdFeed(${prog.id})">
                        <i data-lucide="apple"></i> Feed
                    </button>
                    <button class="izd-btn izd-btn--evo${canEvo ? '' : ' disabled'}"
                            onclick="${canEvo ? `_cdOpenEvolution(${prog.id})` : ''}"
                            ${canEvo ? '' : 'disabled title="Not ready yet"'}>
                        <i data-lucide="sparkles"></i> Evolve
                    </button>
                </div>
            </div>
        </div>`;
    _cdAttachEsc();
}

// ─── Gauge ─────────────────────────────────────────────────────

/** @tag SHOP */
function _cdGauge(label, val, cls) {
    const pct = Math.max(0, Math.min(100, val));
    const fc  = pct < 20 ? 'icd-gf--low' : pct < 60 ? 'icd-gf--mid' : 'icd-gf--ok';
    return `<div class="icd-gauge-row">
        <span class="icd-gauge-label">${label}</span>
        <div class="icd-gauge-bar ${cls}">
            <div class="icd-gauge-fill ${fc}" style="width:${pct}%"></div>
        </div>
        <span class="icd-gauge-pct">${pct}%</span>
    </div>`;
}

// ─── Evolution tree ───────────────────────────────────────────

/** @tag SHOP */
function _cdEvoTree(prog) {
    const stage  = prog.stage || 'baby';
    const isDone = s => ['mid_a','mid_b','final_a','final_b'].includes(stage)
                     && (s === 'baby' || (s.startsWith('mid') && stage.startsWith('final')));
    const isCur  = s => s === stage;
    const isMidA = stage === 'mid_a' || stage === 'final_a';
    const isMidB = stage === 'mid_b' || stage === 'final_b';

    const node = (s, chosen) => {
        const cls = isCur(s)  ? 'icd-evo-node--current'
                  : isDone(s) ? 'icd-evo-node--done'
                  : chosen    ? 'icd-evo-node--future'
                  :             'icd-evo-node--locked';
        const icon = isCur(s) ? 'star' : isDone(s) ? 'check-circle' : chosen ? 'circle' : 'lock';
        return `<div class="icd-evo-node ${cls}">
            <i data-lucide="${icon}"></i>
            <span>${s}</span>
        </div>`;
    };
    const midAChosen = isMidA || stage === 'baby';
    const midBChosen = isMidB || stage === 'baby';

    return `
        <div class="icd-evo-section">
            <div class="icd-evo-title">Evolution Path</div>
            <div class="icd-evo-tree">
                <div class="icd-evo-col icd-evo-col--center">${node('baby', true)}</div>
                <div class="icd-evo-connector"></div>
                <div class="icd-evo-branches">
                    <div class="icd-evo-col">${node('mid_a', midAChosen)}</div>
                    <div class="icd-evo-col">${node('mid_b', midBChosen)}</div>
                </div>
                <div class="icd-evo-connector"></div>
                <div class="icd-evo-branches">
                    <div class="icd-evo-col">${node('final_a', isMidA)}</div>
                    <div class="icd-evo-col">${node('final_b', isMidB)}</div>
                </div>
            </div>
        </div>`;
}

/** @tag SHOP */
function _cdLegendSection(prog) {
    const d  = prog.consecutive_days ?? 0;
    const p1 = Math.min(100, Math.round(d / 14 * 100));
    const p2 = Math.min(100, Math.round(d / 30 * 100));
    return `
        <div class="icd-evo-section">
            <div class="icd-evo-title">Legend Progress</div>
            <div class="icd-legend-row">
                <span>1st Evo</span>
                <div class="icd-xp-bar-wrap icd-xp-bar-wrap--sm">
                    <div class="icd-xp-bar-fill" style="width:${p1}%"></div>
                </div>
                <span>${Math.min(d,14)}/14 days</span>
            </div>
            <div class="icd-legend-row">
                <span>2nd Evo</span>
                <div class="icd-xp-bar-wrap icd-xp-bar-wrap--sm">
                    <div class="icd-xp-bar-fill icd-xp-bar-fill--legend" style="width:${p2}%"></div>
                </div>
                <span>${Math.min(d,30)}/30 days</span>
            </div>
        </div>`;
}

// ─── Actions ──────────────────────────────────────────────────

/** @tag SHOP */
async function _cdFeed(progId) {
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
            _cdBounce();
            openCharacterDetail(progId, _cdZone);
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || 'Feed failed.', true);
        }
    } catch (_) { _showShopToast('Feed failed.', true); }
}

/** @tag SHOP */
function _cdOpenEvolution(progId) {
    const prog = _cdData?.progress || {};
    openEvolutionModal(progId, prog.stage, prog.nickname || prog.character_name || 'Character');
}

// ─── Bounce animation ─────────────────────────────────────────

/** One-shot bounce on avatar click. @tag SHOP */
function _cdBounce() {
    const av = document.getElementById('icd-avatar');
    if (!av) return;
    av.classList.remove('icd-bounce');
    void av.offsetWidth; // reflow to restart animation
    av.classList.add('icd-bounce');
}

// ─── ESC key ──────────────────────────────────────────────────

/** @tag SHOP */
function _cdAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        const ov = document.getElementById('isl-detail-overlay');
        if (ov && ov.dataset.screen === 'character') {
            document.removeEventListener('keydown', fn);
            _closeCharDetail();
        }
    };
    document.addEventListener('keydown', fn);
}
