/* ================================================================
   reward-shop-island.js — Island Shop tabs: Evolution / Food / Decor / Exchange
   Section: Shop
   Dependencies: reward-shop.js (_closePopup, _showShopToast, _shopConfetti,
                 _shopTab, escapeHtml), core.js
   API endpoints: /api/island/shop, /api/island/shop/buy,
                  /api/island/currency, /api/island/lumi/exchange
   ================================================================ */

// ─── State ────────────────────────────────────────────────────
/** @tag SHOP */
let _islandLumi = 0;
let _islandLegendLumi = 0;
let _islandDecorZone = "all";
let _islandBuyInFlight = false;
let _exchAmount = 1;

const _DECOR_ZONES = ["all", "forest", "ocean", "savanna", "space", "legend"];

// ─── Currency ─────────────────────────────────────────────────

/** @tag SHOP */
async function _loadIslandCurrency() {
    try {
        const res = await fetch("/api/island/currency");
        if (!res.ok) return;
        const d = await res.json();
        _islandLumi       = d.lumi        ?? 0;
        _islandLegendLumi = d.legend_lumi ?? 0;
        _updateIslandCurrencyDisplay();
    } catch (_) {}
}

/** @tag SHOP */
function _updateIslandCurrencyDisplay() {
    const el = document.getElementById("shop-xp-display");
    if (el) el.textContent = `💎 ${_islandLumi}  ✨ ${_islandLegendLumi}`;
}

// ─── Tab Entry Point ──────────────────────────────────────────

/** Load the correct island tab. Called from reward-shop.js _loadShopTab. @tag SHOP */
async function _loadIslandTab(tab) {
    const body = document.getElementById("shop-body");
    if (!body) return;
    body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p>`;
    await _loadIslandCurrency();
    try {
        if      (tab === "evolution") await _renderEvolutionTab(body);
        else if (tab === "food")      await _renderFoodTab(body);
        else if (tab === "decor")     await _renderDecorTab(body);
        else if (tab === "exchange")  _renderExchangeTab(body);
    } catch (_) {
        body.innerHTML = `<p style="text-align:center;color:var(--color-error);padding:40px;">Failed to load.</p>`;
    }
}

// ─── Evolution Tab ────────────────────────────────────────────

/** @tag SHOP */
async function _renderEvolutionTab(body) {
    const res = await fetch("/api/island/shop?type=evolution");
    const data = await res.json();
    const items = data.items || [];
    if (!items.length) {
        body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No evolution stones available.</p>`;
        return;
    }
    const cards = items.map(item => {
        const isLegend   = item.currency === "legend_lumi";
        const balance    = isLegend ? _islandLegendLumi : _islandLumi;
        const symbol     = isLegend ? "✨" : "💎";
        const affordable = balance >= item.price;
        const onclick    = affordable
            ? `_islandConfirmBuy(${item.id},'${escapeHtml(item.name)}','${escapeHtml(item.icon || "🧬")}',${item.price},'${item.currency}')`
            : "";
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}" onclick="${onclick}">
            <span class="shop-item-icon">${item.icon || "🧬"}</span>
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            <div class="shop-item-price-row"><span class="shop-item-price">${item.price} ${symbol}</span></div>
        </div>`;
    }).join("");
    body.innerHTML = `<div class="shop-grid">${cards}</div>`;
}

// ─── Food Tab ────────────────────────────────────────────────

/** @tag SHOP */
async function _renderFoodTab(body) {
    const res = await fetch("/api/island/shop?type=food");
    const data = await res.json();
    const items = data.items || [];
    if (!items.length) {
        body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No food items available.</p>`;
        return;
    }
    const cards = items.map(item => {
        const affordable = _islandLumi >= item.price;
        const desc       = item.description ? `<div class="shop-item-desc">${escapeHtml(item.description)}</div>` : "";
        const onclick    = affordable
            ? `_islandConfirmBuy(${item.id},'${escapeHtml(item.name)}','${escapeHtml(item.icon || "🍖")}',${item.price},'lumi')`
            : "";
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}" onclick="${onclick}">
            <span class="shop-item-icon">${item.icon || "🍖"}</span>
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            ${desc}
            <div class="shop-item-price-row"><span class="shop-item-price">${item.price} 💎</span></div>
        </div>`;
    }).join("");
    body.innerHTML = `<div class="shop-grid">${cards}</div>`;
}

// ─── Decor Tab ────────────────────────────────────────────────

/** @tag SHOP */
async function _renderDecorTab(body) {
    const zoneParam = _islandDecorZone !== "all" ? `&zone=${_islandDecorZone}` : "";
    const res  = await fetch(`/api/island/shop?type=decor${zoneParam}`);
    const data = await res.json();
    const items    = data.items    || [];
    const ownedIds = new Set(data.owned_ids || []);

    const zoneBar = `<div class="shop-cat-bar" style="margin-bottom:8px">
        ${_DECOR_ZONES.map(z => {
            const label = z === "all" ? "All" : z.charAt(0).toUpperCase() + z.slice(1);
            return `<button class="shop-cat${_islandDecorZone === z ? " active" : ""}"
                onclick="_islandSetDecorZone('${z}')">${label}</button>`;
        }).join("")}
    </div>`;

    if (!items.length) {
        body.innerHTML = zoneBar + `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No items available.</p>`;
        return;
    }

    const cards = items.map(item => {
        const owned      = ownedIds.has(item.id);
        const isLegend   = item.zone === "legend";
        const symbol     = isLegend ? "✨" : "💎";
        const balance    = isLegend ? _islandLegendLumi : _islandLumi;
        const affordable = !owned && balance >= item.price;
        const currency   = isLegend ? "legend_lumi" : "lumi";
        const ownedBadge = owned
            ? `<span class="shop-item-cat" style="background:var(--math-soft);color:var(--math-ink)">Owned</span>`
            : "";
        const onclick    = (affordable && !owned)
            ? `_islandConfirmBuy(${item.id},'${escapeHtml(item.name)}','${escapeHtml(item.icon || "🌿")}',${item.price},'${currency}')`
            : "";
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}" onclick="${onclick}">
            <span class="shop-item-icon">${item.icon || "🌿"}</span>
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            <div class="shop-item-price-row"><span class="shop-item-price">${owned ? "—" : `${item.price} ${symbol}`}</span></div>
            ${ownedBadge}
        </div>`;
    }).join("");
    body.innerHTML = zoneBar + `<div class="shop-grid">${cards}</div>`;
}

/** @tag SHOP */
function _islandSetDecorZone(zone) {
    _islandDecorZone = zone;
    const body = document.getElementById("shop-body");
    if (body) _renderDecorTab(body);
}

// ─── Exchange Tab ─────────────────────────────────────────────

/** @tag SHOP */
function _renderExchangeTab(body) {
    const maxExch = Math.floor(_islandLumi / 100);
    body.innerHTML = `
        <div style="max-width:360px;margin:32px auto;text-align:center">
            <div style="font-size:48px;margin-bottom:16px">💱</div>
            <div style="font-size:var(--font-size-lg);font-weight:700;margin-bottom:8px">Lumi Exchange</div>
            <div style="color:var(--text-secondary);margin-bottom:24px">100 💎 = 1 ✨ Legend Lumi</div>
            <div style="background:var(--bg-surface);border-radius:var(--radius-md);padding:16px;margin-bottom:20px">
                <div>Your Lumi: <strong id="exch-lumi">${_islandLumi} 💎</strong></div>
                <div>Legend Lumi: <strong id="exch-legend">${_islandLegendLumi} ✨</strong></div>
                <div style="margin-top:8px;color:var(--text-hint)">You can exchange up to <strong>${maxExch}</strong> Legend Lumi</div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;justify-content:center;margin-bottom:20px">
                <button class="shop-popup-btn secondary" onclick="_islandExchangeAdj(-1)" style="padding:8px 16px">−</button>
                <span id="exch-amount" style="font-size:var(--font-size-xl);font-weight:700;min-width:40px">1</span>
                <button class="shop-popup-btn secondary" onclick="_islandExchangeAdj(1)" style="padding:8px 16px">+</button>
            </div>
            <div style="color:var(--text-secondary);margin-bottom:20px">Cost: <span id="exch-cost">100</span> 💎</div>
            <button class="shop-popup-btn primary" id="exch-btn" onclick="_doExchange()"
                ${maxExch < 1 ? "disabled" : ""}>Exchange</button>
        </div>`;
    _exchAmount = 1;
}

/** @tag SHOP */
function _islandExchangeAdj(delta) {
    const max = Math.floor(_islandLumi / 100);
    _exchAmount = Math.max(1, Math.min(max, _exchAmount + delta));
    const amtEl  = document.getElementById("exch-amount");
    const costEl = document.getElementById("exch-cost");
    if (amtEl)  amtEl.textContent  = _exchAmount;
    if (costEl) costEl.textContent = _exchAmount * 100;
}

/** @tag SHOP */
async function _doExchange() {
    if (_islandBuyInFlight) return;
    _islandBuyInFlight = true;
    try {
        const res = await fetch("/api/island/lumi/exchange", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ amount: _exchAmount }),
        });
        if (res.ok) {
            const d = await res.json();
            _islandLumi       = d.lumi        ?? _islandLumi;
            _islandLegendLumi = d.legend_lumi ?? _islandLegendLumi;
            _updateIslandCurrencyDisplay();
            _showShopToast(`✨ +${_exchAmount} Legend Lumi`);
            const body = document.getElementById("shop-body");
            if (body) _renderExchangeTab(body);
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || "Exchange failed.", true);
        }
    } catch (_) {
        _showShopToast("Network error.", true);
    } finally {
        _islandBuyInFlight = false;
    }
}

// ─── Island Buy Flow ──────────────────────────────────────────

/** @tag SHOP */
function _islandConfirmBuy(itemId, name, icon, price, currency) {
    _closePopup();
    const symbol = currency === "legend_lumi" ? "✨" : "💎";
    const bg = document.createElement("div");
    bg.className = "shop-popup-bg";
    bg.id        = "shop-popup-bg";
    bg.innerHTML = `
        <div class="shop-popup">
            <div class="shop-popup-icon">${icon}</div>
            <div class="shop-popup-title">${escapeHtml(name)}</div>
            <div class="shop-popup-sub">${price} ${symbol} will be used.</div>
            <div class="shop-popup-btns">
                <button class="shop-popup-btn secondary" onclick="_closePopup()">Cancel</button>
                <button class="shop-popup-btn primary"   onclick="_doIslandBuy(${itemId})">Buy!</button>
            </div>
        </div>`;
    document.body.appendChild(bg);
}

/** @tag SHOP */
async function _doIslandBuy(itemId) {
    if (_islandBuyInFlight) return;
    _islandBuyInFlight = true;
    _closePopup();
    try {
        const res = await fetch("/api/island/shop/buy", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ item_id: itemId }),
        });
        if (res.ok) {
            const d = await res.json();
            _islandLumi       = d.lumi        ?? _islandLumi;
            _islandLegendLumi = d.legend_lumi ?? _islandLegendLumi;
            _updateIslandCurrencyDisplay();
            _shopConfetti();
            _showShopToast("Added to Inventory!");
            // Refresh current island tab
            if (typeof _shopTab !== "undefined") _loadIslandTab(_shopTab);
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || "Purchase failed.", true);
        }
    } catch (_) {
        _showShopToast("Network error.", true);
    } finally {
        _islandBuyInFlight = false;
    }
}
