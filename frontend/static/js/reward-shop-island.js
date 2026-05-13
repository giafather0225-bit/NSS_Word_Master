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
let _islandExchRate = 100;   // overwritten by /api/island/currency response
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
        _islandLumi       = d.lumi          ?? 0;
        _islandLegendLumi = d.legend_lumi   ?? 0;
        _islandExchRate   = d.exchange_rate ?? 100;
        _updateIslandCurrencyDisplay();
    } catch (_) {}
}

/** @tag SHOP */
function _updateIslandCurrencyDisplay() {
    const el = document.getElementById("shop-xp-display");
    if (el) el.textContent = `Lumi: ${_islandLumi}  Legend: ${_islandLegendLumi}`;
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

// ─── Icon render helper ───────────────────────────────────────

/**
 * Render a shop item's image. Server returns `image` (PNG path) not `icon`.
 * Falls back to the provided emoji default when image is absent or blank.
 * @tag SHOP
 * @param {string} imagePath  — value of item.image from the server
 * @param {string} fallback   — emoji/text fallback (e.g. "gem" icon char)
 */
function _islandItemIcon(imagePath, fallback) {
    if (imagePath && imagePath.trim()) {
        return `<img src="${escapeHtml(imagePath)}" class="shop-item-img" alt="" loading="lazy">`;
    }
    return `<span class="shop-item-icon">${fallback}</span>`;
}

// ─── Card listener helper ────────────────────────────────────

/** Attach click listeners to island shop cards that carry data-item-id. @tag SHOP */
function _attachIslandCardListeners(container) {
    container.querySelectorAll(".shop-item-card[data-item-id]").forEach(card => {
        card.addEventListener("click", () => {
            _islandConfirmBuy(
                Number(card.dataset.itemId),
                card.dataset.itemName,
                card.dataset.itemImage,
                Number(card.dataset.itemPrice),
                card.dataset.currency
            );
        });
    });
}

// ─── Evolution Tab ────────────────────────────────────────────

/** @tag SHOP */
async function _renderEvolutionTab(body) {
    const res = await fetch("/api/island/shop?category=evolution");
    const data = await res.json();
    const items = data.items || [];
    if (!items.length) {
        body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No evolution stones available.</p>`;
        return;
    }
    const cards = items.map(item => {
        const isLegend    = item.is_legend_currency;
        const balance     = isLegend ? _islandLegendLumi : _islandLumi;
        const symbol      = isLegend ? "LL" : "Lumi";
        const affordable  = balance >= item.price;
        const currencyStr = isLegend ? "legend_lumi" : "lumi";
        const dataAttrs   = affordable
            ? `data-item-id="${item.id}" data-item-name="${escapeHtml(item.name)}" data-item-image="${escapeHtml(item.image || "")}" data-item-price="${item.price}" data-currency="${currencyStr}"`
            : "";
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}" ${dataAttrs}>
            ${_islandItemIcon(item.image, "+")}
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            <div class="shop-item-price-row"><span class="shop-item-price">${item.price} ${symbol}</span></div>
        </div>`;
    }).join("");
    body.innerHTML = `<div class="shop-grid">${cards}</div>`;
    _attachIslandCardListeners(body);
}

// ─── Food Tab ────────────────────────────────────────────────

/** @tag SHOP */
async function _renderFoodTab(body) {
    const res = await fetch("/api/island/shop?category=food");
    const data = await res.json();
    const items = data.items || [];
    if (!items.length) {
        body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No food items available.</p>`;
        return;
    }
    const cards = items.map(item => {
        const affordable = _islandLumi >= item.price;
        const desc       = item.description ? `<div class="shop-item-desc">${escapeHtml(item.description)}</div>` : "";
        const dataAttrs  = affordable
            ? `data-item-id="${item.id}" data-item-name="${escapeHtml(item.name)}" data-item-image="${escapeHtml(item.image || "")}" data-item-price="${item.price}" data-currency="lumi"`
            : "";
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}" ${dataAttrs}>
            ${_islandItemIcon(item.image, "+")}
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            ${desc}
            <div class="shop-item-price-row"><span class="shop-item-price">${item.price} Lumi</span></div>
        </div>`;
    }).join("");
    body.innerHTML = `<div class="shop-grid">${cards}</div>`;
    _attachIslandCardListeners(body);
}

// ─── Decor Tab ────────────────────────────────────────────────

/** @tag SHOP */
async function _renderDecorTab(body) {
    const zoneParam = _islandDecorZone !== "all" ? `&zone=${_islandDecorZone}` : "";
    const res  = await fetch(`/api/island/shop?category=decoration${zoneParam}`);
    const data = await res.json();
    const items    = data.items    || [];
    const ownedIds = new Set(data.owned_ids || []);

    const zoneBar = `<div class="shop-cat-bar" style="margin-bottom:8px">
        ${_DECOR_ZONES.map(z => {
            const label = z === "all" ? "All" : z.charAt(0).toUpperCase() + z.slice(1);
            return `<button class="shop-cat${_islandDecorZone === z ? " active" : ""}"
                data-zone="${z}">${label}</button>`;
        }).join("")}
    </div>`;

    if (!items.length) {
        body.innerHTML = zoneBar + `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No items available.</p>`;
        _attachDecorZoneListeners(body);
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
        const dataAttrs  = (affordable && !owned)
            ? `data-item-id="${item.id}" data-item-name="${escapeHtml(item.name)}" data-item-image="${escapeHtml(item.image || "")}" data-item-price="${item.price}" data-currency="${currency}"`
            : "";
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}" ${dataAttrs}>
            ${_islandItemIcon(item.image, "+")}
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            <div class="shop-item-price-row"><span class="shop-item-price">${owned ? "—" : `${item.price} ${symbol}`}</span></div>
            ${ownedBadge}
        </div>`;
    }).join("");
    body.innerHTML = zoneBar + `<div class="shop-grid">${cards}</div>`;
    _attachDecorZoneListeners(body);
    _attachIslandCardListeners(body);
}

/** Attach zone filter button listeners in the Decor tab. @tag SHOP */
function _attachDecorZoneListeners(container) {
    container.querySelectorAll(".shop-cat[data-zone]").forEach(btn => {
        btn.addEventListener("click", () => _islandSetDecorZone(btn.dataset.zone));
    });
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
    const rate    = _islandExchRate;
    const maxExch = Math.floor(_islandLumi / rate);
    body.innerHTML = `
        <div style="max-width:360px;margin:32px auto;text-align:center">
            <div style="margin-bottom:16px"><i data-lucide="arrow-left-right" style="width:48px;height:48px;stroke:var(--arcade-primary)"></i></div>
            <div style="font-size:var(--font-size-lg);font-weight:700;margin-bottom:8px">Lumi Exchange</div>
            <div style="color:var(--text-secondary);margin-bottom:24px">${rate} Lumi = 1 Legend Lumi</div>
            <div style="background:var(--bg-surface);border-radius:var(--radius-md);padding:16px;margin-bottom:20px">
                <div>Your Lumi: <strong id="exch-lumi">${_islandLumi}</strong></div>
                <div>Legend Lumi: <strong id="exch-legend">${_islandLegendLumi}</strong></div>
                <div style="margin-top:8px;color:var(--text-hint)">You can exchange up to <strong>${maxExch}</strong> Legend Lumi</div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;justify-content:center;margin-bottom:20px">
                <button class="shop-popup-btn secondary" onclick="_islandExchangeAdj(-1)" style="padding:8px 16px">−</button>
                <span id="exch-amount" style="font-size:var(--font-size-xl);font-weight:700;min-width:40px">1</span>
                <button class="shop-popup-btn secondary" onclick="_islandExchangeAdj(1)" style="padding:8px 16px">+</button>
            </div>
            <div style="color:var(--text-secondary);margin-bottom:20px">Cost: <span id="exch-cost">${rate}</span> Lumi</div>
            <button class="shop-popup-btn primary" id="exch-btn" onclick="_doExchange()"
                ${maxExch < 1 ? "disabled" : ""}>Exchange</button>
        </div>`;
    _exchAmount = 1;
}

/** @tag SHOP */
function _islandExchangeAdj(delta) {
    const rate = _islandExchRate;
    const max  = Math.floor(_islandLumi / rate);
    _exchAmount = Math.max(1, Math.min(max, _exchAmount + delta));
    const amtEl  = document.getElementById("exch-amount");
    const costEl = document.getElementById("exch-cost");
    if (amtEl)  amtEl.textContent  = _exchAmount;
    if (costEl) costEl.textContent = _exchAmount * rate;
}

/** @tag SHOP */
async function _doExchange() {
    if (_islandBuyInFlight) return;
    _islandBuyInFlight = true;
    try {
        const res = await fetch("/api/island/lumi/exchange", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ lumi_amount: _exchAmount * _islandExchRate }),
        });
        if (res.ok) {
            const d = await res.json();
            const bal = d.currency ?? d;
            _islandLumi       = bal.lumi        ?? _islandLumi;
            _islandLegendLumi = bal.legend_lumi ?? _islandLegendLumi;
            _updateIslandCurrencyDisplay();
            _showShopToast(`+${_exchAmount} Legend Lumi`);
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
function _islandConfirmBuy(itemId, name, image, price, currency) {
    _closePopup();
    const symbol  = currency === "legend_lumi" ? "Legend Lumi" : "Lumi";
    const iconHtml = _islandItemIcon(image, "+");
    const bg = document.createElement("div");
    bg.className = "shop-popup-bg";
    bg.id        = "shop-popup-bg";
    bg.innerHTML = `
        <div class="shop-popup">
            <div class="shop-popup-icon">${iconHtml}</div>
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
            body:    JSON.stringify({ shop_item_id: itemId, quantity: 1 }),
        });
        if (res.ok) {
            const d = await res.json();
            const bal = d.currency ?? d;
            _islandLumi       = bal.lumi        ?? _islandLumi;
            _islandLegendLumi = bal.legend_lumi ?? _islandLegendLumi;
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
