/* ================================================================
   reward-shop.js — Reward Shop overlay (buy + use + PIN modal)
   Section: Shop
   Dependencies: core.js
   API endpoints: /api/shop/items, /api/shop/buy,
                  /api/shop/my-rewards, /api/shop/use-reward/{id}
   ================================================================ */

// ─── State ────────────────────────────────────────────────────
/**
 * @tag SHOP
 */
let _shopTab = "shop"; // "shop" | "my-rewards"
let _shopCategory = "all"; // "all" | "badge" | "theme" | "power" | "real"
let _pinTarget = null; // purchase_id pending use
let _pinDigits = "";   // current PIN entry (up to 4 digits)

// ─── Open / Close ─────────────────────────────────────────────

/** Open the Reward Shop overlay and load items. @tag SHOP */
function openRewardShop() {
    const el = document.getElementById("shop-overlay");
    if (!el) return;
    el.classList.remove("hidden");
    _shopTab = "shop";
    _renderShopFrame();
    _loadShopTab("shop");
}

/** Close the Reward Shop overlay. @tag SHOP */
function closeRewardShop() {
    const el = document.getElementById("shop-overlay");
    if (el) el.classList.add("hidden");
    _closePopup();
}

// ─── Frame / Tabs ─────────────────────────────────────────────

/** Render the static shop shell (header + tabs). @tag SHOP */
function _renderShopFrame() {
    const el = document.getElementById("shop-overlay");
    if (!el) return;
    el.innerHTML = `
        <div class="shop-header">
            <button class="shop-close-btn" onclick="closeRewardShop()">←</button>
            <span class="shop-title">💎 Reward Shop</span>
            <span class="shop-xp-badge" id="shop-xp-display">⭐ …</span>
        </div>
        <div class="shop-tabs">
            <button class="shop-tab active" id="tab-shop"       onclick="_shopSwitchTab('shop')">Shop</button>
            <button class="shop-tab"        id="tab-my-rewards" onclick="_shopSwitchTab('my-rewards')">My Rewards</button>
        </div>
        <div class="shop-cat-bar" id="shop-cat-bar">
            <button class="shop-cat active" data-cat="all" onclick="_shopFilterCat('all')">All</button>
            <button class="shop-cat" data-cat="badge" onclick="_shopFilterCat('badge')">Badges</button>
            <button class="shop-cat" data-cat="theme" onclick="_shopFilterCat('theme')">Themes</button>
            <button class="shop-cat" data-cat="power" onclick="_shopFilterCat('power')">Powers</button>
            <button class="shop-cat" data-cat="real" onclick="_shopFilterCat('real')">Real</button>
        </div>
        <div id="shop-body"><p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p></div>`;
}

/** Filter shop items by category. @tag SHOP */
function _shopFilterCat(cat) {
    _shopCategory = cat;
    document.querySelectorAll(".shop-cat").forEach(b => b.classList.toggle("active", b.dataset.cat === cat));
    _loadShopTab("shop");
}

/** Switch between Shop and My Rewards tabs. @tag SHOP */
function _shopSwitchTab(tab) {
    _shopTab = tab;
    document.querySelectorAll(".shop-tab").forEach(b => b.classList.remove("active"));
    const active = document.getElementById(tab === "shop" ? "tab-shop" : "tab-my-rewards");
    if (active) active.classList.add("active");
    const catBar = document.getElementById("shop-cat-bar");
    if (catBar) catBar.style.display = tab === "shop" ? "flex" : "none";
    _loadShopTab(tab);
}

// ─── Shop Tab ─────────────────────────────────────────────────

/** Load and render the shop grid or my-rewards list. @tag SHOP */
async function _loadShopTab(tab) {
    const body = document.getElementById("shop-body");
    if (!body) return;
    body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p>`;
    try {
        if (tab === "shop") {
            const catParam = _shopCategory && _shopCategory !== "all" ? `?category=${_shopCategory}` : "";
            const res = await fetch(`/api/shop/items${catParam}`);
            const data = await res.json();
            _updateXPDisplay(data.total_xp || 0);
            _renderShopGrid(data.items || [], data.total_xp || 0);
        } else {
            const res = await fetch("/api/shop/my-rewards");
            const data = await res.json();
            _updateXPDisplay(data.total_xp || 0);
            _renderMyRewards(data.rewards || []);
        }
    } catch (_) {
        body.innerHTML = `<p style="text-align:center;color:var(--color-error);padding:40px;">Failed to load.</p>`;
    }
}

/**
 * Update the XP badge in the shop header.
 * @tag SHOP XP
 */
function _updateXPDisplay(xp) {
    const el = document.getElementById("shop-xp-display");
    if (el) el.textContent = `⭐ ${xp} XP`;
}

/** Render the shop item grid. @tag SHOP */
function _renderShopGrid(items, totalXp) {
    const body = document.getElementById("shop-body");
    if (!items.length) {
        body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No items available.</p>`;
        return;
    }
    const cards = items.map(item => {
        const affordable = totalXp >= item.final_price;
        const discBadge  = item.discount_pct > 0 ? `<span class="shop-discount-badge">-${item.discount_pct}%</span>` : "";
        const priceHTML  = item.discount_pct > 0
            ? `<span class="shop-item-original">⭐${item.price}</span><span class="shop-item-price">⭐${item.final_price}</span>`
            : `<span class="shop-item-price">⭐${item.final_price}</span>`;
        const desc = item.description ? `<div class="shop-item-desc">${escapeHtml(item.description)}</div>` : "";
        const catBadge = `<span class="shop-item-cat">${item.category || "badge"}</span>`;
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}"
                     onclick="${affordable ? `_shopConfirmBuy(${item.id},'${escapeHtml(item.name)}','${escapeHtml(item.icon)}',${item.final_price})` : ""}">
            ${discBadge}
            ${catBadge}
            <span class="shop-item-icon">${item.icon}</span>
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            ${desc}
            <div>${priceHTML}</div>
        </div>`;
    }).join("");
    body.innerHTML = `<div class="shop-grid">${cards}</div>`;
}

// ─── Buy Confirm Popup ────────────────────────────────────────

/**
 * Show the buy confirmation popup for an item.
 * @tag SHOP
 */
function _shopConfirmBuy(itemId, name, icon, price) {
    _closePopup();
    const bg = document.createElement("div");
    bg.className = "shop-popup-bg";
    bg.id = "shop-popup-bg";
    bg.innerHTML = `
        <div class="shop-popup">
            <div class="shop-popup-icon">${icon}</div>
            <div class="shop-popup-title">${escapeHtml(name)}</div>
            <div class="shop-popup-sub">⭐ ${price} XP will be deducted.</div>
            <div class="shop-popup-btns">
                <button class="shop-popup-btn secondary" onclick="_closePopup()">Cancel</button>
                <button class="shop-popup-btn primary"   onclick="_doBuy(${itemId})">Buy!</button>
            </div>
        </div>`;
    document.body.appendChild(bg);
}

/**
 * Execute the buy API call.
 * @tag SHOP XP
 */
async function _doBuy(itemId) {
    _closePopup();
    try {
        const res = await fetch("/api/shop/buy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: itemId }),
        });
        if (res.ok) {
            const d = await res.json();
            _updateXPDisplay(d.remaining_xp || 0);
            _shopConfetti();
            _showShopToast("✓ Added to My Rewards");
            _loadShopTab("shop"); // refresh affordability
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || "Purchase failed.", true);
        }
    } catch (_) { _showShopToast("Network error.", true); }
}

// ─── My Rewards Tab ───────────────────────────────────────────

/**
 * Render the My Rewards list.
 * @tag SHOP
 */
function _renderMyRewards(rewards) {
    const body = document.getElementById("shop-body");
    const unused = rewards.filter(r => !r.is_used);
    const used   = rewards.filter(r => r.is_used);
    if (!rewards.length) {
        body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">No rewards yet. Go buy something!</p>`;
        return;
    }
    const row = r => {
        const date = r.purchased_at ? r.purchased_at.slice(0,10) : "";
        const usedLabel = r.is_used ? `Used ${r.used_at ? r.used_at.slice(0,10) : ""}` : `Bought ${date}`;
        const desc = r.description ? `<div class="my-reward-desc">${escapeHtml(r.description)}</div>` : "";
        const canEquip = !r.is_used && (r.category === "badge" || r.category === "theme");
        const equipBtn = canEquip
            ? `<button class="my-reward-equip-btn${r.is_equipped ? " equipped" : ""}"
                       onclick="_shopToggleEquip(${r.id}, ${!r.is_equipped})">${r.is_equipped ? "Equipped" : "Equip"}</button>`
            : "";
        return `<div class="my-reward-row${r.is_used ? " used" : ""}${r.is_equipped ? " equipped" : ""}">
            <span class="my-reward-icon">${r.icon}</span>
            <div class="my-reward-info">
                <div class="my-reward-name">${escapeHtml(r.name)}</div>
                ${desc}
                <div class="my-reward-meta">⭐${r.xp_spent} · ${usedLabel}</div>
            </div>
            <div class="my-reward-actions">
                ${equipBtn}
                <button class="my-reward-use-btn" onclick="_shopOpenPin(${r.id})"
                        ${r.is_used ? "disabled" : ""}>${r.is_used ? "Used ✓" : "Use"}</button>
            </div>
        </div>`;
    };
    body.innerHTML = `<div class="my-rewards-list">
        ${[...unused, ...used].map(row).join("")}
    </div>`;
}

// ─── PIN Modal ────────────────────────────────────────────────

/**
 * Open the PIN entry modal for using a reward.
 * @tag SHOP PIN
 */
function _shopOpenPin(purchaseId) {
    _pinTarget = purchaseId;
    _pinDigits = "";
    _closePopup();
    const bg = document.createElement("div");
    bg.className = "shop-popup-bg";
    bg.id = "shop-popup-bg";
    bg.innerHTML = `
        <div class="shop-popup">
            <div class="shop-popup-title">Enter PIN</div>
            <div class="shop-popup-sub" style="margin-bottom:12px;">Parent approval required</div>
            <div class="pin-dots" id="pin-dots">
                ${[0,1,2,3].map(() => `<div class="pin-dot"></div>`).join("")}
            </div>
            <div class="pin-error" id="pin-error"></div>
            <div class="pin-pad">
                ${[1,2,3,4,5,6,7,8,9].map(n => `<button class="pin-key" onclick="_pinPress('${n}')">${n}</button>`).join("")}
                <button class="pin-key" onclick="_pinPress('clear')">✕</button>
                <button class="pin-key" onclick="_pinPress('0')">0</button>
                <button class="pin-key pin-key delete" onclick="_pinPress('del')">⌫</button>
            </div>
        </div>`;
    document.body.appendChild(bg);
}

/**
 * Handle a PIN pad key press.
 * @tag SHOP PIN
 */
function _pinPress(key) {
    if (key === "del")   { _pinDigits = _pinDigits.slice(0, -1); }
    else if (key === "clear") { _pinDigits = ""; document.getElementById("pin-error").textContent = ""; }
    else if (_pinDigits.length < 4) { _pinDigits += key; }
    _updatePinDots();
    if (_pinDigits.length === 4) setTimeout(_submitPin, 200);
}

/**
 * Update PIN dot fill display.
 * @tag SHOP PIN
 */
function _updatePinDots() {
    const dots = document.querySelectorAll(".pin-dot");
    dots.forEach((d, i) => d.classList.toggle("filled", i < _pinDigits.length));
}

/**
 * Submit PIN to /api/shop/use-reward/{id}.
 * @tag SHOP PIN
 */
async function _submitPin() {
    try {
        const res = await fetch(`/api/shop/use-reward/${_pinTarget}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pin: _pinDigits }),
        });
        if (res.ok) {
            _closePopup();
            _showShopToast("✅ Enjoy your reward!");
            _loadShopTab("my-rewards");
        } else {
            _pinDigits = "";
            _updatePinDots();
            const errEl = document.getElementById("pin-error");
            if (errEl) errEl.textContent = "Wrong PIN. Try again.";
        }
    } catch (_) { _pinDigits = ""; _updatePinDots(); }
}

// ─── Equip / Unequip ──────────────────────────────────────────

/**
 * Toggle equip status for a purchased reward (badges/themes).
 * @tag SHOP
 */
async function _shopToggleEquip(purchaseId, equip) {
    try {
        const res = await fetch(`/api/shop/equip/${purchaseId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ equip }),
        });
        if (res.ok) {
            _showShopToast(equip ? "Equipped!" : "Unequipped");
            _loadShopTab("my-rewards");
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || "Failed.", true);
        }
    } catch (_) { _showShopToast("Network error.", true); }
}

// ─── Utilities ────────────────────────────────────────────────

/** Close any open popup. @tag SHOP */
function _closePopup() {
    const bg = document.getElementById("shop-popup-bg");
    if (bg) bg.remove();
}

/** Spawn confetti particles on purchase success. @tag SHOP */
function _shopConfetti() {
    const colors = ['#D4619E', '#4A8E8E', '#34C759', '#F59E0B', '#FF3B30', '#a29bfe', '#fd79a8'];
    for (let i = 0; i < 50; i++) {
        const el = document.createElement('div');
        el.className = 'shop-confetti';
        el.style.left = Math.random() * 100 + 'vw';
        el.style.background = colors[Math.floor(Math.random() * colors.length)];
        el.style.width = (5 + Math.random() * 6) + 'px';
        el.style.height = (5 + Math.random() * 6) + 'px';
        el.style.animationDuration = (2 + Math.random() * 2) + 's';
        el.style.animationDelay = (Math.random() * 0.5) + 's';
        document.body.appendChild(el);
        el.addEventListener('animationend', () => el.remove());
    }
}

/** Show a brief toast in the shop overlay. @tag SHOP */
function _showShopToast(msg, isError = false) {
    const t = document.createElement("div");
    t.className = "xp-toast";
    if (isError) t.style.background = "var(--color-error)";
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));
    setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 300); }, 2200);
}
