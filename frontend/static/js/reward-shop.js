/* ================================================================
   reward-shop.js — Reward Shop overlay: browsing + buy flow.
                    My Rewards / PIN / Equip split into reward-shop-use.js
                    to honor the 300-line CLAUDE.md ceiling.
   Section: Shop
   Dependencies: core.js
   API endpoints: /api/shop/items, /api/shop/buy, /api/shop/my-rewards
   ================================================================ */

// ─── State ────────────────────────────────────────────────────
/**
 * @tag SHOP
 */
let _shopTab = "shop"; // "shop" | "my-rewards"
let _shopCategory = "all"; // "all" | "badge" | "theme" | "power" | "real"
// Guard against double-click / rapid-tap buy spam. The backend now uses
// BEGIN IMMEDIATE to prevent double-spend at the DB layer, but we also
// short-circuit at the UI so the user doesn't see 2× "Purchase failed"
// toasts when the second request loses the race.
let _buyInFlight = false;

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
            <span class="shop-title">Reward Shop</span>
            <span class="shop-xp-badge" id="shop-xp-display">… XP</span>
        </div>
        <div class="shop-tabs">
            <button class="shop-tab active" id="tab-shop"       onclick="_shopSwitchTab('shop')">Rewards</button>
            <button class="shop-tab"        id="tab-my-rewards" onclick="_shopSwitchTab('my-rewards')">My Rewards</button>
            <button class="shop-tab"        id="tab-evolution"  onclick="_shopSwitchTab('evolution')">Evolution</button>
            <button class="shop-tab"        id="tab-food"       onclick="_shopSwitchTab('food')">Food</button>
            <button class="shop-tab"        id="tab-decor"      onclick="_shopSwitchTab('decor')">Decor</button>
            <button class="shop-tab"        id="tab-exchange"   onclick="_shopSwitchTab('exchange')">Exchange</button>
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
    const active = document.getElementById("tab-" + tab);
    if (active) active.classList.add("active");
    const catBar = document.getElementById("shop-cat-bar");
    if (catBar) catBar.style.display = tab === "shop" ? "flex" : "none";
    // Restore XP display when leaving island tabs
    if (tab === "shop" || tab === "my-rewards") {
        const xpEl = document.getElementById("shop-xp-display");
        if (xpEl) xpEl.textContent = "… XP";
    }
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
        } else if (tab === "my-rewards") {
            const res = await fetch("/api/shop/my-rewards");
            const data = await res.json();
            _updateXPDisplay(data.total_xp || 0);
            _renderMyRewards(data.rewards || []);
        } else if (["evolution", "food", "decor", "exchange"].includes(tab)) {
            if (typeof _loadIslandTab === "function") _loadIslandTab(tab);
            else body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:40px;">Island system not available.</p>`;
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
    if (el) el.textContent = `${xp} XP`;
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
            ? `<span class="shop-item-original">${item.price} XP</span><span class="shop-item-price">${item.final_price} XP</span>`
            : `<span class="shop-item-price">${item.final_price} XP</span>`;
        const desc = item.description ? `<div class="shop-item-desc">${escapeHtml(item.description)}</div>` : "";
        const catBadge = `<span class="shop-item-cat">${item.category || "badge"}</span>`;
        return `<div class="shop-item-card${affordable ? "" : " unaffordable"}"
                     onclick="${affordable ? `_shopConfirmBuy(${item.id},'${escapeHtml(item.name)}','${escapeHtml(item.icon)}',${item.final_price})` : ""}">
            ${discBadge}
            <span class="shop-item-icon">${item.icon}</span>
            <div class="shop-item-name">${escapeHtml(item.name)}</div>
            ${desc}
            <div class="shop-item-price-row">${priceHTML}</div>
            ${catBadge}
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
            <div class="shop-popup-sub">${price} XP will be deducted.</div>
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
    if (_buyInFlight) return;           // defuse double-click
    _buyInFlight = true;
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
            _showShopToast("Added to My Rewards");
            _loadShopTab("shop"); // refresh affordability
        } else {
            const err = await res.json().catch(() => ({}));
            _showShopToast(err.detail || "Purchase failed.", true);
        }
    } catch (_) {
        _showShopToast("Network error.", true);
    } finally {
        _buyInFlight = false;
    }
}

// ─── Utilities ────────────────────────────────────────────────
// My Rewards / PIN modal / Equip handlers live in reward-shop-use.js.
// They reach back into _closePopup / _showShopToast / _loadShopTab through
// the shared window scope (CLAUDE.md: "All modules share global window
// scope — no ES module import/export").

/** Close any open popup. @tag SHOP */
function _closePopup() {
    const bg = document.getElementById("shop-popup-bg");
    if (bg) bg.remove();
}

/**
 * Read a CSS custom property from :root, falling back to the given default.
 * Lets confetti reuse theme.css tokens instead of hardcoded hex — the
 * CLAUDE.md "no hard-coded hex colors" rule covers JS-generated color too,
 * otherwise a theme swap leaves confetti stuck on the old palette.
 * @tag SHOP @tag THEME
 */
function _cssVar(name, fallback) {
    try {
        const v = getComputedStyle(document.documentElement).getPropertyValue(name);
        return (v && v.trim()) || fallback;
    } catch (_) {
        return fallback;
    }
}

/** Spawn confetti particles on purchase success. @tag SHOP */
function _shopConfetti() {
    // Pull from theme.css; fallbacks match the Phase-5 pink-first palette so
    // a browser without CSS custom property support still gets festive colors.
    const colors = [
        _cssVar('--color-primary',   '#D4619E'),
        _cssVar('--color-secondary', '#4A8E8E'),
        _cssVar('--color-success',   '#34C759'),
        _cssVar('--color-warning',   '#FF9500'),
        _cssVar('--color-error',     '#FF3B30'),
        // Two accent confetti colors kept as literals — deliberately outside
        // the theme token set so confetti stays visually varied even when a
        // future theme collapses primary/secondary into a single hue.
        _cssVar('--color-confetti-a', '#a29bfe'),
        _cssVar('--color-confetti-b', '#fd79a8'),
    ];
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
