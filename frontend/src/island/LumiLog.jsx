/* ================================================================
   LumiLog.jsx — Lumi transaction history: earned / spent / balance.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/lumi/log
   ================================================================ */

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _llFilter = 'all';
let _llItems  = [];

// ─── Open / Close ───────────────────────────────────────────────

/** Open Lumi log. Called from topbar currency click. @tag SHOP */
async function openLumiLog() {
    _llFilter = 'all'; _llItems = [];
    const el = document.getElementById('isl-detail-overlay');
    if (!el) return;
    el.classList.remove('hidden');
    el.dataset.screen = 'lumi-log';
    el.innerHTML = `<div class="ill-screen"><div class="isl-state-screen">
        <div class="isl-loading-ship">⛵</div>
        <div class="isl-state-text">Loading history...</div>
    </div></div>`;
    try {
        const data = await apiFetchJSON('/api/island/lumi/log');
        _llItems = data.log || data || [];
        _llRender(el);
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _llAttachEsc();
    } catch (_) {
        el.innerHTML = `<div class="ill-screen"><div class="isl-state-screen">
            <div class="isl-state-icon"><i data-lucide="wifi-off"></i></div>
            <div class="isl-state-text">Could not load Lumi history.</div>
            <button class="isl-retry-btn" onclick="openLumiLog()">Retry</button>
            <button class="isl-back-btn"  onclick="_closeLumiLog()">Back</button>
        </div></div>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

/** @tag SHOP */
function _closeLumiLog() {
    const el = document.getElementById('isl-detail-overlay');
    if (el) { el.classList.add('hidden'); el.innerHTML = ''; }
}

// ─── Render ──────────────────────────────────────────────────────

/** @tag SHOP */
function _llRender(el) {
    const filtered = _llFilter === 'earned' ? _llItems.filter(i => (i.amount || 0) > 0)
                   : _llFilter === 'spent'  ? _llItems.filter(i => (i.amount || 0) < 0)
                   : _llItems;

    const balance = _llItems.length
        ? (_llItems[0].balance_after ?? 0)
        : 0;

    const tabs = [
        { key: 'all',    label: 'All'    },
        { key: 'earned', label: 'Earned' },
        { key: 'spent',  label: 'Spent'  },
    ];
    const tabHTML = tabs.map(t => `
        <button class="ill-tab${_llFilter === t.key ? ' ill-tab--active' : ''}"
                onclick="_llSetFilter('${t.key}')">${t.label}</button>`
    ).join('');

    const rowsHTML = filtered.length ? filtered.map(row => {
        const amount  = row.amount ?? 0;
        const sign    = amount >= 0 ? '+' : '';
        const cls     = amount >= 0 ? 'ill-row--earned' : 'ill-row--spent';
        const dateStr = (row.created_at || '').substring(0, 10);
        const bal     = row.balance_after ?? '—';
        return `
            <div class="ill-row ${cls}">
                <div class="ill-row-left">
                    <div class="ill-row-reason">${escapeHtml(row.reason || row.action || '—')}</div>
                    <div class="ill-row-date">${dateStr}</div>
                </div>
                <div class="ill-row-right">
                    <div class="ill-row-amount">${sign}${amount} 💎</div>
                    <div class="ill-row-bal">${bal.toLocaleString()}</div>
                </div>
            </div>`;
    }).join('') : `<div class="ill-empty">No transactions found.</div>`;

    el.innerHTML = `
        <div class="ill-screen">
            <div class="ill-topbar">
                <button class="ill-back-btn" onclick="_closeLumiLog()">
                    <i data-lucide="arrow-left"></i>
                </button>
                <div class="ill-title">Lumi History</div>
                <div class="ill-balance">💎 ${balance.toLocaleString()}</div>
            </div>
            <div class="ill-tabs">${tabHTML}</div>
            <div class="ill-body">${rowsHTML}</div>
        </div>`;
}

// ─── Tab ─────────────────────────────────────────────────────────

/** @tag SHOP */
function _llSetFilter(f) {
    _llFilter = f;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _llRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

// ─── ESC ─────────────────────────────────────────────────────────

/** @tag SHOP */
function _llAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        const ov = document.getElementById('isl-detail-overlay');
        if (ov && ov.dataset.screen === 'lumi-log') {
            document.removeEventListener('keydown', fn);
            _closeLumiLog();
        }
    };
    document.addEventListener('keydown', fn);
}
