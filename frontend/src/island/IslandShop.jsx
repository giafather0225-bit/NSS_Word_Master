/* ================================================================
   IslandShop.jsx — Island shop: Evolution / Food / Decor / Exchange
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/shop, GET /api/island/currency,
                  POST /api/island/shop/buy,
                  POST /api/island/lumi/exchange
   ================================================================ */

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _ishTab      = 'evolution';
let _ishItems    = [];
let _ishCurrency = { lumi: 0, legend_lumi: 0 };
let _ishSelected = null;
let _ishExchAmt  = 0;

// ─── Open / Close ───────────────────────────────────────────────

/** Open island shop screen. @tag SHOP */
async function openIslandShop() {
    _ishTab = 'evolution'; _ishSelected = null; _ishExchAmt = 0;
    const el = document.getElementById('isl-detail-overlay');
    if (!el) return;
    el.classList.remove('hidden');
    el.dataset.screen = 'shop';
    el.innerHTML = `<div class="ish-screen"><div class="isl-state-screen">
        <div class="isl-loading-ship">⛵</div>
        <div class="isl-state-text">Loading shop...</div>
    </div></div>`;
    try {
        const [shopData, curData] = await Promise.all([
            apiFetchJSON('/api/island/shop'),
            apiFetchJSON('/api/island/currency'),
        ]);
        _ishItems    = shopData.items    || shopData || [];
        _ishCurrency = curData.currency  || curData  || { lumi: 0, legend_lumi: 0 };
        _ishRender(el);
        if (typeof lucide !== 'undefined') lucide.createIcons();
        _ishAttachEsc();
    } catch (_) {
        el.innerHTML = `<div class="ish-screen"><div class="isl-state-screen">
            <div class="isl-state-icon"><i data-lucide="wifi-off"></i></div>
            <div class="isl-state-text">Could not load shop.</div>
            <button class="isl-retry-btn" onclick="openIslandShop()">Retry</button>
            <button class="isl-back-btn"  onclick="_closeIslandShop()">Back</button>
        </div></div>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

/** @tag SHOP */
function _closeIslandShop() {
    const el = document.getElementById('isl-detail-overlay');
    if (el) { el.classList.add('hidden'); el.innerHTML = ''; }
    _ishSelected = null;
}

// ─── Render ──────────────────────────────────────────────────────

/** @tag SHOP */
function _ishRender(el) {
    const tabs = [
        { key: 'evolution', icon: 'sparkles',    label: 'Evolution' },
        { key: 'food',      icon: 'apple',        label: 'Food'      },
        { key: 'decor',     icon: 'image',        label: 'Decor'     },
        { key: 'exchange',  icon: 'arrow-left-right', label: 'Exchange' },
    ];
    const tabHTML = tabs.map(t => `
        <button class="ish-tab${_ishTab === t.key ? ' ish-tab--active' : ''}"
                onclick="_ishSetTab('${t.key}')">
            <i data-lucide="${t.icon}"></i> ${t.label}
        </button>`).join('');

    const lumi = (_ishCurrency.lumi ?? 0).toLocaleString();
    const ll   = (_ishCurrency.legend_lumi ?? 0).toLocaleString();

    el.innerHTML = `
        <div class="ish-screen">
            <div class="ish-topbar">
                <button class="ish-back-btn" onclick="_closeIslandShop()">
                    <i data-lucide="arrow-left"></i>
                </button>
                <div class="ish-title">Island Shop</div>
                <div class="ish-wallet">
                    <span class="ish-cur"><span class="ish-cur-ic">💎</span>${lumi}</span>
                    <span class="ish-cur"><span class="ish-cur-ic">✨</span>${ll}</span>
                </div>
            </div>
            <div class="ish-tabs">${tabHTML}</div>
            <div class="ish-body" id="ish-body">
                ${_ishTab === 'exchange' ? _ishExchangeHTML() : _ishGridHTML()}
            </div>
            ${_ishSelected ? _ishDetailModal() : ''}
        </div>`;
}

// ─── Tabs ────────────────────────────────────────────────────────

/** @tag SHOP */
function _ishSetTab(tab) {
    _ishTab = tab; _ishSelected = null;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _ishRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

// ─── Item grid ───────────────────────────────────────────────────

/** @tag SHOP */
function _ishGridHTML() {
    const cat = _ishTab === 'evolution' ? 'evolution'
              : _ishTab === 'food'      ? 'food'
              : 'decoration';
    const filtered = _ishItems.filter(i => i.category === cat);
    if (!filtered.length) return `<div class="ish-empty">No items available.</div>`;

    return `<div class="ish-grid">${filtered.map(item => {
        const price  = item.price || 0;
        const isLl   = item.is_legend_currency;
        const wallet = isLl ? (_ishCurrency.legend_lumi ?? 0) : (_ishCurrency.lumi ?? 0);
        const afford = wallet >= price;
        return `
            <div class="ish-item${afford ? '' : ' ish-item--locked'}"
                 onclick="_ishSelectItem(${item.id})">
                <div class="ish-item-icon"><i data-lucide="${_ishItemIcon(item.category)}"></i></div>
                <div class="ish-item-name">${escapeHtml(item.name)}</div>
                <div class="ish-item-price${afford ? '' : ' ish-item-price--low'}">
                    ${isLl ? '✨' : '💎'} ${price.toLocaleString()}
                </div>
            </div>`;
    }).join('')}</div>`;
}

/** @tag SHOP */
function _ishItemIcon(cat) {
    return cat === 'evolution' ? 'sparkles' : cat === 'food' ? 'apple' : 'image';
}

// ─── Item detail modal ────────────────────────────────────────────

/** @tag SHOP */
function _ishSelectItem(id) {
    _ishSelected = _ishItems.find(i => i.id === id) || null;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _ishRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

/** @tag SHOP */
function _ishDetailModal() {
    const item   = _ishSelected;
    const isLl   = item.is_legend_currency;
    const price  = item.price || 0;
    const wallet = isLl ? (_ishCurrency.legend_lumi ?? 0) : (_ishCurrency.lumi ?? 0);
    const afford = wallet >= price;
    return `
        <div class="ish-modal-backdrop" onclick="_ishCloseModal()">
            <div class="ish-modal" onclick="event.stopPropagation()">
                <button class="ish-modal-close" onclick="_ishCloseModal()">
                    <i data-lucide="x"></i>
                </button>
                <div class="ish-modal-icon"><i data-lucide="${_ishItemIcon(item.category)}"></i></div>
                <div class="ish-modal-name">${escapeHtml(item.name)}</div>
                <div class="ish-modal-desc">${escapeHtml(item.description || '')}</div>
                <div class="ish-modal-price">${isLl ? '✨' : '💎'} ${price.toLocaleString()}</div>
                ${!afford ? `<div class="ish-modal-warn">Not enough ${isLl ? 'Legend Lumi' : 'Lumi'}.</div>` : ''}
                <button class="ish-buy-btn${afford ? '' : ' disabled'}"
                        ${afford ? `onclick="_ishBuy(${item.id})"` : 'disabled'}>
                    <i data-lucide="shopping-cart"></i> Buy
                </button>
            </div>
        </div>`;
}

/** @tag SHOP */
function _ishCloseModal() {
    _ishSelected = null;
    const el = document.getElementById('isl-detail-overlay');
    if (el) { _ishRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

// ─── Buy ─────────────────────────────────────────────────────────

/** @tag SHOP */
async function _ishBuy(itemId) {
    const btn = document.querySelector('.ish-buy-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader"></i> Buying…'; }
    if (typeof lucide !== 'undefined') lucide.createIcons();
    try {
        const res = await fetch('/api/island/shop/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId }),
        });
        if (res.ok) {
            const d = await res.json();
            _ishCurrency = d.currency || _ishCurrency;
            _ishSelected = null;
            if (typeof _showShopToast === 'function') _showShopToast('Purchased!');
            const el = document.getElementById('isl-detail-overlay');
            if (el) { _ishRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
        } else {
            const err = await res.json().catch(() => ({}));
            if (typeof _showShopToast === 'function') _showShopToast(err.detail || 'Purchase failed.', true);
            if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="shopping-cart"></i> Buy'; }
        }
    } catch (_) {
        if (typeof _showShopToast === 'function') _showShopToast('Purchase failed.', true);
        if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="shopping-cart"></i> Buy'; }
    }
}

// ─── Exchange tab ─────────────────────────────────────────────────

/** @tag SHOP */
function _ishExchangeHTML() {
    const lumi   = _ishCurrency.lumi ?? 0;
    const maxAmt = Math.floor(lumi / 100);
    const amt    = Math.min(_ishExchAmt, maxAmt);
    const ll     = amt;
    return `
        <div class="ish-exchange">
            <div class="ish-exch-title">Convert Lumi to Legend Lumi</div>
            <div class="ish-exch-rate">100 💎 = 1 ✨</div>
            <div class="ish-exch-balance">Balance: 💎 ${lumi.toLocaleString()}</div>
            <div class="ish-exch-row">
                <label class="ish-exch-label">Amount</label>
                <input type="range" class="ish-exch-slider" id="ish-exch-slider"
                       min="0" max="${maxAmt}" value="${amt}"
                       oninput="_ishExchInput(this.value)" />
                <span class="ish-exch-val" id="ish-exch-val">${amt}</span>
            </div>
            <div class="ish-exch-preview">
                You will receive: <strong>✨ ${ll}</strong>
                (costs 💎 ${(amt * 100).toLocaleString()})
            </div>
            <button class="ish-exch-btn${amt > 0 ? '' : ' disabled'}"
                    ${amt > 0 ? 'onclick="_ishExchange()"' : 'disabled'}>
                <i data-lucide="arrow-left-right"></i> Exchange
            </button>
        </div>`;
}

/** @tag SHOP */
function _ishExchInput(val) {
    _ishExchAmt = parseInt(val, 10) || 0;
    const valEl = document.getElementById('ish-exch-val');
    if (valEl) valEl.textContent = _ishExchAmt;
    const body = document.getElementById('ish-body');
    if (body) { body.innerHTML = _ishExchangeHTML(); if (typeof lucide !== 'undefined') lucide.createIcons(); }
}

/** @tag SHOP */
async function _ishExchange() {
    if (_ishExchAmt <= 0) return;
    const btn = document.querySelector('.ish-exch-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader"></i> Converting…'; }
    if (typeof lucide !== 'undefined') lucide.createIcons();
    try {
        const res = await fetch('/api/island/lumi/exchange', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: _ishExchAmt }),
        });
        if (res.ok) {
            const d = await res.json();
            _ishCurrency = d.currency || _ishCurrency;
            _ishExchAmt  = 0;
            if (typeof _showShopToast === 'function') _showShopToast(`Converted! ✨ +${_ishExchAmt}`);
            const el = document.getElementById('isl-detail-overlay');
            if (el) { _ishRender(el); if (typeof lucide !== 'undefined') lucide.createIcons(); }
        } else {
            const err = await res.json().catch(() => ({}));
            if (typeof _showShopToast === 'function') _showShopToast(err.detail || 'Exchange failed.', true);
            if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="arrow-left-right"></i> Exchange'; }
        }
    } catch (_) {
        if (typeof _showShopToast === 'function') _showShopToast('Exchange failed.', true);
        if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="arrow-left-right"></i> Exchange'; }
    }
}

// ─── ESC ─────────────────────────────────────────────────────────

/** @tag SHOP */
function _ishAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        const ov = document.getElementById('isl-detail-overlay');
        if (ov && ov.dataset.screen === 'shop') {
            document.removeEventListener('keydown', fn);
            if (_ishSelected) { _ishCloseModal(); } else { _closeIslandShop(); }
        }
    };
    document.addEventListener('keydown', fn);
}
