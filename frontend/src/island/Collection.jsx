/* ================================================================
   Collection.jsx — Island character collection / Pokédex view.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/characters,
                  GET /api/island/character/completed
   ================================================================ */

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _colFilter    = 'all';
let _colSort      = 'default';
let _colCatalog   = [];
let _colCompleted = {};  // character_id → completed entry
let _colSelected  = null;

// ─── Open / Close ───────────────────────────────────────────────

/** Open collection screen. @tag SHOP */
async function openCollection() {
    _colFilter = 'all'; _colSort = 'default';
    _colCatalog = []; _colCompleted = {}; _colSelected = null;
    const el = document.getElementById('isl-detail-overlay');
    if (!el) return;
    el.classList.remove('hidden');
    el.dataset.screen = 'collection';
    el.innerHTML = `<div class="ico-screen"><div class="isl-state-screen">
        <div class="isl-loading-ship">⛵</div>
        <div class="isl-state-text">Loading collection...</div>
    </div></div>`;
    try {
        const [catData, doneData] = await Promise.all([
            apiFetchJSON('/api/island/characters'),
            apiFetchJSON('/api/island/character/completed'),
        ]);
        _colCatalog = catData.characters || catData || [];
        (doneData.completed || doneData || []).forEach(c => {
            _colCompleted[c.character_id] = c;
        });
        _colRender(el);
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _colAttachEsc();
    } catch (_) {
        el.innerHTML = `<div class="ico-screen"><div class="isl-state-screen">
            <div class="isl-state-icon"><i data-lucide="wifi-off"></i></div>
            <div class="isl-state-text">Could not load collection.</div>
            <button class="isl-retry-btn" onclick="openCollection()">Retry</button>
            <button class="isl-back-btn"  onclick="_closeCollection()">Back</button>
        </div></div>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

/** @tag SHOP */
function _closeCollection() {
    const el = document.getElementById('isl-detail-overlay');
    if (el) { el.classList.add('hidden'); el.innerHTML = ''; }
    _colSelected = null;
}

// ─── Render ──────────────────────────────────────────────────────

/** @tag SHOP */
function _colRender(el) {
    const total = _colCatalog.length;
    const done  = Object.keys(_colCompleted).length;
    el.innerHTML = `
        <div class="ico-screen">
            <div class="ico-topbar">
                <button class="ico-back-btn" onclick="_closeCollection()">
                    <i data-lucide="arrow-left"></i>
                </button>
                <div class="ico-title">Collection</div>
                <div class="ico-progress">${done} / ${total}</div>
            </div>
            <div class="ico-controls">
                <div class="ico-filters">
                    ${_colFilterBtn('all',        'All'       )}
                    ${_colFilterBtn('forest',     'Forest'    )}
                    ${_colFilterBtn('ocean',      'Ocean'     )}
                    ${_colFilterBtn('savanna',    'Savanna'   )}
                    ${_colFilterBtn('space',      'Space'     )}
                    ${_colFilterBtn('completed',  'Completed' )}
                    ${_colFilterBtn('progress',   'In Progress')}
                </div>
                <select class="ico-sort" onchange="_colSetSort(this.value)">
                    <option value="default"  ${_colSort==='default'  ? 'selected':''}>Default</option>
                    <option value="date"     ${_colSort==='date'     ? 'selected':''}>Completion Date</option>
                    <option value="zone"     ${_colSort==='zone'     ? 'selected':''}>By Zone</option>
                </select>
            </div>
            <div class="ico-body">${_colBodyHTML()}</div>
            ${_colSelected ? _colDetailModal() : ''}
        </div>`;
}

/** @tag SHOP */
function _colFilterBtn(key, label) {
    return `<button class="ico-filter-btn${_colFilter===key?' ico-filter-btn--active':''}"
             onclick="_colSetFilter('${key}')">${label}</button>`;
}

// ─── Filter / Sort ────────────────────────────────────────────────

/** @tag SHOP */
function _colSetFilter(f) {
    _colFilter = f;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _colRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

/** @tag SHOP */
function _colSetSort(s) {
    _colSort = s;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _colRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

// ─── Body ────────────────────────────────────────────────────────

/** @tag SHOP */
function _colBodyHTML() {
    let items = _colCatalog.filter(c => {
        if (_colFilter === 'all')       return true;
        if (_colFilter === 'completed') return !!_colCompleted[c.id];
        if (_colFilter === 'progress')  return !_colCompleted[c.id];
        return c.zone === _colFilter;
    });

    if (_colSort === 'zone') {
        const order = ['forest','ocean','savanna','space','legend'];
        items = items.slice().sort((a,b) => order.indexOf(a.zone) - order.indexOf(b.zone));
    } else if (_colSort === 'date') {
        items = items.slice().sort((a,b) => {
            const da = _colCompleted[a.id]?.completed_at || '';
            const db = _colCompleted[b.id]?.completed_at || '';
            if (!da && !db) return 0;
            if (!da) return 1;
            if (!db) return -1;
            return db.localeCompare(da);
        });
    }

    const regular = items.filter(c => c.zone !== 'legend');
    const legend  = items.filter(c => c.zone === 'legend');

    let html = '';
    if (regular.length) html += `<div class="ico-grid">${regular.map(_colCardHTML).join('')}</div>`;
    if (legend.length)  html += `
        <div class="ico-legend-section">
            <div class="ico-legend-title"><i data-lucide="star"></i> Legend Characters</div>
            <div class="ico-grid">${legend.map(_colCardHTML).join('')}</div>
        </div>`;
    if (!regular.length && !legend.length) {
        html = `<div class="ico-empty"><i data-lucide="book-open"></i><p>No characters match this filter.</p></div>`;
    }
    return html;
}

/** @tag SHOP */
function _colCardHTML(char) {
    const done = _colCompleted[char.id];
    const meta = _ZONE_META ? (_ZONE_META[char.zone] || {}) : {};
    const name = escapeHtml(done ? (char.name || '?') : '???');
    const dateStr = done?.completed_at ? done.completed_at.substring(0, 10) : '';
    return `
        <div class="ico-card${done ? ' ico-card--done' : ' ico-card--locked'}"
             onclick="_colOpenDetail(${char.id})">
            <div class="ico-card-avatar${done ? '' : ' ico-card-avatar--sil'}">
                ${meta.icon || '?'}
            </div>
            <div class="ico-card-name">${name}</div>
            <div class="ico-card-zone">${done ? (meta.label || char.zone) : char.zone}</div>
            ${done && dateStr ? `<div class="ico-card-date">${dateStr}</div>` : ''}
            ${done ? '<div class="ico-card-badge"><i data-lucide="check-circle"></i></div>' : ''}
        </div>`;
}

// ─── Detail modal ─────────────────────────────────────────────────

/** @tag SHOP */
function _colOpenDetail(charId) {
    _colSelected = _colCatalog.find(c => c.id === charId) || null;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _colRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

/** @tag SHOP */
function _colDetailModal() {
    const char = _colSelected;
    const done = _colCompleted[char.id];
    const meta = _ZONE_META ? (_ZONE_META[char.zone] || {}) : {};
    const name = done ? escapeHtml(char.name || '?') : '???';
    const dateStr = done?.completed_at ? done.completed_at.substring(0, 10) : null;
    return `
        <div class="ico-modal-backdrop" onclick="_colCloseDetail()">
            <div class="ico-modal" onclick="event.stopPropagation()">
                <button class="ico-modal-close" onclick="_colCloseDetail()">
                    <i data-lucide="x"></i>
                </button>
                <div class="ico-modal-avatar${done ? '' : ' ico-card-avatar--sil'}">
                    ${meta.icon || '?'}
                </div>
                <div class="ico-modal-name">${name}</div>
                <div class="ico-modal-zone">${meta.label || char.zone}</div>
                ${done
                    ? `<div class="ico-modal-status ico-modal-status--done">
                        <i data-lucide="check-circle"></i> Completed
                        ${dateStr ? `<span>${dateStr}</span>` : ''}
                       </div>`
                    : `<div class="ico-modal-status ico-modal-status--locked">
                        <i data-lucide="lock"></i> Not yet discovered
                       </div>`
                }
                ${char.description && done
                    ? `<div class="ico-modal-desc">${escapeHtml(char.description)}</div>` : ''}
            </div>
        </div>`;
}

/** @tag SHOP */
function _colCloseDetail() {
    _colSelected = null;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _colRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

// ─── ESC ─────────────────────────────────────────────────────────

/** @tag SHOP */
function _colAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        const ov = document.getElementById('isl-detail-overlay');
        if (ov && ov.dataset.screen === 'collection') {
            document.removeEventListener('keydown', fn);
            if (_colSelected) { _colCloseDetail(); } else { _closeCollection(); }
        }
    };
    document.addEventListener('keydown', fn);
}
