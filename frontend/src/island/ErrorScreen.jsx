/* ================================================================
   ErrorScreen.jsx — App error states: offline/server/update/maintenance
   Section: System (Island)
   Dependencies: IslandMain.jsx (escapeHtml)
   API endpoints: none
   ================================================================ */

// ─── Config ─────────────────────────────────────────────────────

/** @tag SHOP */
const _IER_CONFIG = {
    offline: {
        icon:      'wifi-off',
        title:     'No connection',
        sub:       "Check your Wi-Fi or mobile data.",
        hand:      "The island will wait for you 💕",
        cta:       { icon: 'refresh-cw',   label: 'Try again'       },
        alt:       { icon: 'play-circle',  label: 'Continue offline' },
    },
    server: {
        icon:      'server-off',
        title:     'Something went wrong',
        sub:       "Our servers had a hiccup. Not your fault, promise!",
        hand:      "We're already on it — hang tight!",
        cta:       { icon: 'refresh-cw',   label: 'Try again'       },
        alt:       { icon: 'flag',         label: 'Report a bug'    },
    },
    update: {
        icon:      'download-cloud',
        title:     'Update available',
        sub:       "A new version of the app is ready — update to keep playing!",
        hand:      "New things are waiting inside!",
        cta:       { icon: 'download',     label: 'Update now'      },
        alt:       { icon: 'clock',        label: 'Later'           },
    },
    maintenance: {
        icon:      'wrench',
        title:     'Under maintenance',
        sub:       "We're giving the island some love. Back soon!",
        hand:      "Worth the wait, we promise ✨",
        cta:       { icon: 'bell',         label: 'Notify me'       },
        alt:       null,
        chip:      true,
    },
};

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _ierVariant  = 'offline';
let _ierEta      = null; // maintenance ETA string
let _ierOnCta    = null;
let _ierOnAlt    = null;

// ─── Entry ──────────────────────────────────────────────────────

/**
 * Show error screen.
 * @param {'offline'|'server'|'update'|'maintenance'} variant
 * @param {{ eta?:string, onCta?:function, onAlt?:function }} opts
 * @tag SHOP
 */
function showErrorScreen(variant, opts) {
    _ierVariant = variant || 'offline';
    _ierEta     = opts?.eta    || null;
    _ierOnCta   = opts?.onCta  || null;
    _ierOnAlt   = opts?.onAlt  || null;
    _ierRender();
}

/** @tag SHOP */
function hideErrorScreen() {
    const el = document.getElementById('ier-screen');
    if (el) el.remove();
}

// ─── Render ─────────────────────────────────────────────────────

/** @tag SHOP */
function _ierRender() {
    let existing = document.getElementById('ier-screen');
    if (!existing) {
        existing = document.createElement('div');
        existing.id = 'ier-screen';
        document.body.appendChild(existing);
    }
    existing.className = 'ier-screen';
    existing.style.cssText = 'position:fixed;inset:0;z-index:8900;display:flex;flex-direction:column;align-items:center;justify-content:center';

    const cfg = _IER_CONFIG[_ierVariant] || _IER_CONFIG.offline;

    const chipHTML = cfg.chip && _ierEta
        ? `<div class="ier-maintenance-chip"><i data-lucide="clock"></i> Estimated ${escapeHtml(_ierEta)}</div>`
        : '';

    const altHTML = cfg.alt
        ? `<button class="ier-alt-btn" id="ier-alt-btn">
               <i data-lucide="${cfg.alt.icon}"></i> ${escapeHtml(cfg.alt.label)}
           </button>`
        : '';

    existing.innerHTML = `
        <div class="ier-icon-ring">
            <i data-lucide="${cfg.icon}" class="ier-icon"></i>
        </div>
        <h1 class="ier-title">${escapeHtml(cfg.title)}</h1>
        <p class="ier-sub">${escapeHtml(cfg.sub)}</p>
        <p class="ier-hand">${cfg.hand}</p>
        ${chipHTML}
        <button class="ier-cta-btn" id="ier-cta-btn">
            <i data-lucide="${cfg.cta.icon}"></i> ${escapeHtml(cfg.cta.label)}
        </button>
        ${altHTML}`;

    if (typeof lucide !== 'undefined') lucide.createIcons();

    const ctaEl = document.getElementById('ier-cta-btn');
    const altEl = document.getElementById('ier-alt-btn');
    if (ctaEl && _ierOnCta) ctaEl.addEventListener('click', _ierOnCta);
    if (altEl && _ierOnAlt) altEl.addEventListener('click', _ierOnAlt);
}
