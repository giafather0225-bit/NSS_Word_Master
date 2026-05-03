/* ================================================================
   PurchaseModal.jsx — 3-state island shop purchase confirmation
   Section: Shop (Island)
   Dependencies: IslandMain.jsx (apiFetchJSON, escapeHtml, _showShopToast)
   API endpoints: POST /api/island/shop/buy
   ================================================================ */

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _ipcItem     = null; // { id, name, icon, price_lumi, price_type }
let _ipcBalance  = 0;
let _ipcState    = 'confirm'; // 'confirm' | 'success' | 'insufficient'
let _ipcResult   = null;
let _ipcOnDone   = null; // callback after successful purchase

// ─── Entry ──────────────────────────────────────────────────────

/**
 * Show purchase confirmation modal.
 * @param {{ id:string, name:string, icon:string, price_lumi:number, price_type:string }} item
 * @param {number} currentBalance   Caller supplies current Lumi balance.
 * @param {function|null} onDone    Called with result after successful buy.
 * @tag SHOP
 */
function openPurchaseModal(item, currentBalance, onDone) {
    _ipcItem    = item;
    _ipcBalance = currentBalance ?? 0;
    _ipcResult  = null;
    _ipcOnDone  = onDone || null;
    _ipcState   = (item?.price_lumi ?? 0) > _ipcBalance ? 'insufficient' : 'confirm';
    _ipcRender();
}

// ─── Render ─────────────────────────────────────────────────────

/** @tag SHOP */
function _ipcRender() {
    const existing = document.getElementById('ipc-scrim');
    if (existing) existing.remove();

    const scrim = document.createElement('div');
    scrim.id        = 'ipc-scrim';
    scrim.className = 'ipc-scrim';
    scrim.setAttribute('role', 'presentation');
    scrim.addEventListener('click', e => { if (e.target === scrim) _ipcClose(); });

    scrim.innerHTML = `
        <div class="ipc-modal" role="dialog" aria-modal="true" aria-label="Purchase confirmation">
            ${_ipcModalInner()}
        </div>`;

    const islandEl = document.getElementById('island-overlay') || document.body;
    islandEl.appendChild(scrim);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    _ipcAttachEsc();
}

/** @tag SHOP */
function _ipcModalInner() {
    switch (_ipcState) {
        case 'confirm':      return _ipcConfirmHTML();
        case 'success':      return _ipcSuccessHTML();
        case 'insufficient': return _ipcInsufficientHTML();
        default:             return '';
    }
}

/** @tag SHOP */
function _ipcConfirmHTML() {
    const item  = _ipcItem || {};
    const price = item.price_lumi ?? 0;
    const after = _ipcBalance - price;
    return `
        <div class="ipc-item-preview">
            <div class="ipc-item-ico ipc-item-ico--gem">
                <i data-lucide="${item.icon || 'package'}"></i>
            </div>
            <span class="ipc-item-name">${escapeHtml(item.name || 'Item')}</span>
        </div>
        <div class="ipc-price-box">
            <div class="ipc-price-row">
                <span class="ipc-price-label">Cost</span>
                <span class="ipc-price-val"><i data-lucide="gem"></i> ${price.toLocaleString()} Lumi</span>
            </div>
            <div class="ipc-price-row ipc-price-row--after">
                <span class="ipc-price-label">Balance after</span>
                <span class="ipc-price-val">${after.toLocaleString()} Lumi</span>
            </div>
        </div>
        <div class="ipc-actions">
            <button class="ipc-btn ipc-btn--ghost" onclick="_ipcClose()">
                Cancel
            </button>
            <button class="ipc-btn ipc-btn--primary" onclick="_ipcConfirmBuy()">
                <i data-lucide="gem"></i> Buy
            </button>
        </div>`;
}

/** @tag SHOP */
function _ipcSuccessHTML() {
    const r    = _ipcResult || {};
    const item = _ipcItem   || {};
    return `
        <div class="ipc-item-preview">
            <div class="ipc-item-ico ipc-item-ico--done">
                <i data-lucide="check-circle"></i>
            </div>
            <span class="ipc-item-name">Purchased!</span>
        </div>
        <p class="ipc-success-msg">${escapeHtml(item.name || 'Item')} added to your inventory.</p>
        ${r.currency?.lumi != null
            ? `<p class="ipc-balance-after"><i data-lucide="gem"></i> ${r.currency.lumi.toLocaleString()} Lumi remaining</p>`
            : ''}
        <div class="ipc-actions">
            <button class="ipc-btn ipc-btn--primary" onclick="_ipcClose()">
                <i data-lucide="check"></i> Done
            </button>
        </div>`;
}

/** @tag SHOP */
function _ipcInsufficientHTML() {
    const item  = _ipcItem || {};
    const price = item.price_lumi ?? 0;
    const need  = price - _ipcBalance;
    return `
        <div class="ipc-item-preview">
            <div class="ipc-item-ico ipc-item-ico--err">
                <i data-lucide="gem"></i>
            </div>
            <span class="ipc-item-name">Not enough Lumi</span>
        </div>
        <p class="ipc-insuff-msg">
            You need <strong>${need.toLocaleString()} more Lumi</strong> for ${escapeHtml(item.name || 'this item')}.
        </p>
        <div class="ipc-earn-list">
            <div class="ipc-earn-row ipc-earn-row--mission">
                <i data-lucide="target"></i>
                <span>Complete today's missions</span>
            </div>
            <div class="ipc-earn-row ipc-earn-row--exchange">
                <i data-lucide="arrow-left-right"></i>
                <span>Exchange Legend Lumi</span>
            </div>
        </div>
        <div class="ipc-actions">
            <button class="ipc-btn ipc-btn--ghost" onclick="_ipcClose()">
                Close
            </button>
        </div>`;
}

// ─── Buy ────────────────────────────────────────────────────────

/** @tag SHOP */
async function _ipcConfirmBuy() {
    const btn = document.querySelector('.ipc-btn--primary');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader-2"></i> Buying…'; }
    if (typeof lucide !== 'undefined') lucide.createIcons();

    try {
        const data = await apiFetchJSON('/api/island/shop/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shop_item_id: _ipcItem?.shop_item_id || _ipcItem?.id, quantity: 1 }),
        });
        _ipcResult  = data;
        _ipcBalance = data.currency?.lumi ?? (_ipcBalance - (_ipcItem?.price_lumi ?? 0));
        _ipcState   = 'success';
        if (_ipcOnDone) _ipcOnDone(data);
        if (typeof _showShopToast === 'function') _showShopToast(`Purchased ${_ipcItem?.name || 'item'}!`);
    } catch (e) {
        _ipcState = 'insufficient';
        _ipcResult = { error: e.message || 'Purchase failed.' };
    }

    _ipcRender();
}

// ─── Close / ESC ─────────────────────────────────────────────────

/** @tag SHOP */
function _ipcClose() {
    const scrim = document.getElementById('ipc-scrim');
    if (scrim) scrim.remove();
    _ipcItem    = null;
    _ipcResult  = null;
    _ipcOnDone  = null;
}

/** @tag SHOP */
function _ipcAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        if (document.getElementById('ipc-scrim')) {
            document.removeEventListener('keydown', fn);
            _ipcClose();
        }
    };
    document.addEventListener('keydown', fn);
}
