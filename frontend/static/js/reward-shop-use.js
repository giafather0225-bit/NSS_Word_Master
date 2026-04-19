/* ================================================================
   reward-shop-use.js — Post-purchase UX: My Rewards list, PIN modal,
                        equip/unequip. Split from reward-shop.js to
                        stay under the 300-line CLAUDE.md ceiling.
   Section: Shop
   Dependencies: core.js, reward-shop.js (shares _loadShopTab,
                 _closePopup, _showShopToast via window globals)
   API endpoints: /api/shop/use-reward/{id}, /api/shop/equip/{id}
   ================================================================ */

// Module-local PIN entry state. Kept here instead of on window so a stray
// parent-panel call can't read the in-flight digits.
let _pinTarget = null; // purchase_id pending use
let _pinDigits = "";   // current PIN entry (up to 4 digits)

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
                <div class="my-reward-meta">${r.xp_spent} XP · ${usedLabel}</div>
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
                <button class="pin-key pin-key--clear" onclick="_pinPress('clear')">C</button>
                <button class="pin-key" onclick="_pinPress('0')">0</button>
                <button class="pin-key pin-key--del" onclick="_pinPress('del')">Del</button>
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
 * Backend rate-limits (5 wrong → 5 min lockout, HTTP 429); surface that so
 * the user isn't confused by silent rejections.
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
            _showShopToast("Reward unlocked!");
            _loadShopTab("my-rewards");
            return;
        }
        _pinDigits = "";
        _updatePinDots();
        const errEl = document.getElementById("pin-error");
        if (!errEl) return;
        if (res.status === 429) {
            let detail = "Too many wrong attempts. Try again later.";
            try { detail = (await res.json()).detail || detail; } catch (_) {}
            errEl.textContent = detail;
        } else {
            errEl.textContent = "Wrong PIN. Try again.";
        }
    } catch (_) {
        _pinDigits = "";
        _updatePinDots();
    }
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
