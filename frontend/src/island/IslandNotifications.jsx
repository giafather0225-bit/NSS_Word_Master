/* ================================================================
   IslandNotifications.jsx — App-open popup: hungry chars,
                              evolvable chars, daily Lumi production.
   Section: Shop (Island)
   Dependencies: core.js (apiFetchJSON), IslandMain.jsx
   API endpoints: GET /api/island/notifications,
                  POST /api/island/notifications/read
   ================================================================ */

// ─── State ─────────────────────────────────────────────────────
/** @tag SHOP */
let _inData = null;

// ─── Entry point ────────────────────────────────────────────────

/**
 * Show island notifications popup if there are unread notifications.
 * Called from openIslandMain() after status loads.
 * @tag SHOP
 */
async function checkIslandNotifications() {
    try {
        const data = await apiFetchJSON('/api/island/notifications');
        if (!data || (!data.hungry?.length && !data.evolvable?.length && !data.lumi_earned == null)) return;
        _inData = data;
        _inRender();
    } catch (_) { /* silent — notifications are optional */ }
}

// ─── Render ──────────────────────────────────────────────────────

/** @tag SHOP */
function _inRender() {
    const existing = document.getElementById('isl-notify-popup');
    if (existing) existing.remove();

    const d = _inData || {};
    const hungry    = d.hungry    || [];
    const evolvable = d.evolvable || [];
    const lumiEarned = d.lumi_earned ?? 0;

    const hasContent = hungry.length || evolvable.length || lumiEarned > 0;
    if (!hasContent) return;

    const popup = document.createElement('div');
    popup.id = 'isl-notify-popup';
    popup.className = 'inp-popup';
    popup.setAttribute('role', 'dialog');
    popup.setAttribute('aria-label', 'Island Notifications');

    popup.innerHTML = `
        <div class="inp-header">
            <div class="inp-title">
                <i data-lucide="bell"></i>
                Island Update
            </div>
            <button class="inp-close-btn" onclick="_inDismiss()" aria-label="Dismiss">
                <i data-lucide="x"></i>
            </button>
        </div>
        <div class="inp-body">
            ${lumiEarned > 0 ? _inLumiRow(lumiEarned) : ''}
            ${evolvable.length ? _inEvolvableSection(evolvable) : ''}
            ${hungry.length    ? _inHungrySection(hungry)       : ''}
        </div>
        <div class="inp-footer">
            <button class="inp-btn inp-btn--primary" onclick="_inDismiss()">
                Got it
            </button>
        </div>`;

    const islandEl = document.getElementById('island-overlay');
    if (islandEl) {
        islandEl.appendChild(popup);
    } else {
        document.body.appendChild(popup);
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();
    _inAttachEsc();
}

/** @tag SHOP */
function _inLumiRow(amount) {
    return `
        <div class="inp-lumi-row">
            <i data-lucide="gem"></i>
            <span>+${amount.toLocaleString()} Lumi earned today</span>
        </div>`;
}

/** @tag SHOP */
function _inEvolvableSection(chars) {
    const rows = chars.map(c => {
        const name = escapeHtml((c.nickname || c.name || 'Character').substring(0, 12));
        return `
            <div class="inp-char-row inp-char-row--evo">
                <div class="inp-char-dot inp-char-dot--evo"></div>
                <div class="inp-char-info">
                    <span class="inp-char-name">${name}</span>
                    <span class="inp-char-tag">Ready to evolve!</span>
                </div>
                <i data-lucide="sparkles" class="inp-char-icon--evo"></i>
            </div>`;
    }).join('');
    return `
        <div class="inp-section">
            <div class="inp-section-label">
                <i data-lucide="sparkles"></i> Evolution Ready
            </div>
            ${rows}
        </div>`;
}

/** @tag SHOP */
function _inHungrySection(chars) {
    const rows = chars.map(c => {
        const name   = escapeHtml((c.nickname || c.name || 'Character').substring(0, 12));
        const h      = c.hunger    ?? 0;
        const p      = c.happiness ?? 0;
        const reason = h < 20 ? 'Hungry' : 'Unhappy';
        const cls    = h < 20 ? 'inp-char-row--hungry' : 'inp-char-row--sad';
        return `
            <div class="inp-char-row ${cls}">
                <div class="inp-char-dot inp-char-dot--warn"></div>
                <div class="inp-char-info">
                    <span class="inp-char-name">${name}</span>
                    <span class="inp-char-tag">${reason} (H:${h}% / M:${p}%)</span>
                </div>
                <i data-lucide="alert-triangle" class="inp-char-icon--warn"></i>
            </div>`;
    }).join('');
    return `
        <div class="inp-section">
            <div class="inp-section-label">
                <i data-lucide="heart"></i> Needs Attention
            </div>
            ${rows}
        </div>`;
}

// ─── Dismiss ─────────────────────────────────────────────────────

/** @tag SHOP */
async function _inDismiss() {
    const popup = document.getElementById('isl-notify-popup');
    if (popup) popup.remove();
    try {
        await fetch('/api/island/notifications/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
    } catch (_) { /* silent */ }
    _inData = null;
}

// ─── ESC ─────────────────────────────────────────────────────────

/** @tag SHOP */
function _inAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        if (document.getElementById('isl-notify-popup')) {
            document.removeEventListener('keydown', fn);
            _inDismiss();
        }
    };
    document.addEventListener('keydown', fn);
}
