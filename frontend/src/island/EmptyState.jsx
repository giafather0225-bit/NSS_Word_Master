/* ================================================================
   EmptyState.jsx — 4-variant empty placeholder for island screens
   Section: Shop (Island)
   Dependencies: IslandMain.jsx (escapeHtml)
   API endpoints: none
   ================================================================ */

// ─── Config ─────────────────────────────────────────────────────

/** @tag SHOP */
const _IES_CONFIG = {
    zone: {
        icon:    'map',
        title:   'No characters yet',
        sub:     'Start raising your first island friend!',
        hand:    'Your island is waiting…',
        ctaIcon: 'plus-circle',
        ctaText: 'Adopt a character',
    },
    inv: {
        icon:    'package-open',
        title:   'Inventory is empty',
        sub:     'Earn Lumi and pick up food, stones, and decor.',
        hand:    'Time to go shopping!',
        ctaIcon: 'shopping-bag',
        ctaText: 'Visit the shop',
    },
    dex: {
        icon:    'book-heart',
        title:   'Dex is empty',
        sub:     'Graduate characters to add them here.',
        hand:    'Your first entry is just ahead…',
        ctaIcon: null,
        ctaText: null,
        ghosts:  true,
    },
    friends: {
        icon:    'users',
        title:   'No friends here',
        sub:     'Unlock more zones to meet new characters.',
        hand:    'More friends are out there!',
        ctaIcon: null,
        ctaText: null,
    },
};

// ─── Render ─────────────────────────────────────────────────────

/**
 * Inject an empty-state block into `containerId`.
 * @param {'zone'|'inv'|'dex'|'friends'} variant
 * @param {string} containerId
 * @param {function|null} onCta  Called when CTA button is clicked.
 * @tag SHOP
 */
function renderEmptyState(variant, containerId, onCta) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const cfg = _IES_CONFIG[variant] || _IES_CONFIG.zone;

    const ghosts = cfg.ghosts ? `
        <div class="ies-dex-ghosts" aria-hidden="true">
            ${Array.from({length: 6}, () => '<div class="ies-dex-ghost"></div>').join('')}
        </div>` : '';

    const ctaBtn = cfg.ctaIcon && cfg.ctaText ? `
        <button class="ies-cta-btn" id="ies-cta-${containerId}">
            <i data-lucide="${cfg.ctaIcon}"></i>
            ${escapeHtml(cfg.ctaText)}
        </button>` : '';

    container.innerHTML = `
        <div class="ies-wrap" role="status" aria-label="${escapeHtml(cfg.title)}">
            <div class="ies-icon-ring">
                <i data-lucide="${cfg.icon}" class="ies-icon"></i>
            </div>
            <p class="ies-title">${escapeHtml(cfg.title)}</p>
            <p class="ies-sub">${escapeHtml(cfg.sub)}</p>
            <p class="ies-hand">${escapeHtml(cfg.hand)}</p>
            ${ghosts}
            ${ctaBtn}
        </div>`;

    if (typeof lucide !== 'undefined') lucide.createIcons();

    if (onCta) {
        const btn = document.getElementById(`ies-cta-${containerId}`);
        if (btn) btn.addEventListener('click', onCta);
    }
}

/**
 * Returns true if the container currently shows an empty state.
 * @param {string} containerId
 * @tag SHOP
 */
function isEmptyStateVisible(containerId) {
    return !!document.querySelector(`#${containerId} .ies-wrap`);
}
