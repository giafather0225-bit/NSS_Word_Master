/* ================================================================
   Inventory.jsx — Island inventory: owned items by category.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/inventory
   ================================================================ */

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _invTab   = 'all';
let _invItems = [];

// ─── Open / Close ───────────────────────────────────────────────

/** Open inventory screen. @tag SHOP */
async function openInventory() {
    _invTab = 'all'; _invItems = [];
    const el = document.getElementById('isl-detail-overlay');
    if (!el) return;
    el.classList.remove('hidden');
    el.dataset.screen = 'inventory';
    el.innerHTML = `<div class="iiv-screen"><div class="isl-state-screen">
        <div class="isl-loading-ship">⛵</div>
        <div class="isl-state-text">Loading inventory...</div>
    </div></div>`;
    try {
        const data = await apiFetchJSON('/api/island/inventory');
        _invItems = data.items || data || [];
        _invRender(el);
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _invAttachEsc();
    } catch (_) {
        el.innerHTML = `<div class="iiv-screen"><div class="isl-state-screen">
            <div class="isl-state-icon"><i data-lucide="wifi-off"></i></div>
            <div class="isl-state-text">Could not load inventory.</div>
            <button class="isl-retry-btn" onclick="openInventory()">Retry</button>
            <button class="isl-back-btn"  onclick="_closeInventory()">Back</button>
        </div></div>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

/** @tag SHOP */
function _closeInventory() {
    const el = document.getElementById('isl-detail-overlay');
    if (el) { el.classList.add('hidden'); el.innerHTML = ''; }
}

// ─── Render ──────────────────────────────────────────────────────

/** @tag SHOP */
function _invRender(el) {
    const tabs = [
        { key: 'all',       icon: 'layers',   label: 'All'       },
        { key: 'evolution', icon: 'sparkles', label: 'Evolution' },
        { key: 'food',      icon: 'apple',    label: 'Food'      },
        { key: 'decor',     icon: 'image',    label: 'Decor'     },
    ];
    const tabHTML = tabs.map(t => `
        <button class="iiv-tab${_invTab === t.key ? ' iiv-tab--active' : ''}"
                onclick="_invSetTab('${t.key}')">
            <i data-lucide="${t.icon}"></i> ${t.label}
        </button>`).join('');

    el.innerHTML = `
        <div class="iiv-screen">
            <div class="iiv-topbar">
                <button class="iiv-back-btn" onclick="_closeInventory()">
                    <i data-lucide="arrow-left"></i>
                </button>
                <div class="iiv-title">My Inventory</div>
            </div>
            <div class="iiv-tabs">${tabHTML}</div>
            <div class="iiv-body">${_invGridHTML()}</div>
        </div>`;
}

// ─── Tab ─────────────────────────────────────────────────────────

/** @tag SHOP */
function _invSetTab(tab) {
    _invTab = tab;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _invRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

// ─── Grid ────────────────────────────────────────────────────────

/** @tag SHOP */
function _invGridHTML() {
    const filtered = _invTab === 'all'
        ? _invItems
        : _invItems.filter(i => {
            const cat = (i.category || i.item_category || '').toLowerCase();
            return _invTab === 'evolution' ? cat === 'evolution'
                 : _invTab === 'food'      ? cat === 'food'
                 : cat === 'decoration' || cat === 'decor';
        });

    if (!filtered.length) {
        return `<div class="iiv-empty">
            <i data-lucide="backpack"></i>
            <p>No items yet. Visit the shop!</p>
            <button class="iiv-shop-btn" onclick="_invGoShop()">
                <i data-lucide="shopping-bag"></i> Open Shop
            </button>
        </div>`;
    }

    return `<div class="iiv-grid">${filtered.map(item => {
        const qty  = item.quantity ?? 1;
        const name = escapeHtml(item.name || item.item_name || '?');
        const cat  = (item.category || item.item_category || '').toLowerCase();
        const icon = cat === 'evolution' ? 'sparkles' : cat === 'food' ? 'apple' : 'image';
        return `
            <div class="iiv-item">
                <div class="iiv-item-icon"><i data-lucide="${icon}"></i></div>
                <div class="iiv-item-name">${name}</div>
                ${qty > 1 ? `<div class="iiv-item-qty">x${qty}</div>` : ''}
            </div>`;
    }).join('')}</div>`;
}

/** @tag SHOP */
function _invGoShop() {
    _closeInventory();
    if (typeof openIslandShop === 'function') openIslandShop();
}

// ─── ESC ─────────────────────────────────────────────────────────

/** @tag SHOP */
function _invAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        const ov = document.getElementById('isl-detail-overlay');
        if (ov && ov.dataset.screen === 'inventory') {
            document.removeEventListener('keydown', fn);
            _closeInventory();
        }
    };
    document.addEventListener('keydown', fn);
}
