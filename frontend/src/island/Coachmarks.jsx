/* ================================================================
   Coachmarks.jsx — 4-step onboarding tour (one-time, spotlight trick)
   Section: System (Island)
   Dependencies: IslandMain.jsx (escapeHtml)
   API endpoints: none (localStorage.tutorialSeen flag)
   ================================================================ */

// ─── Config ─────────────────────────────────────────────────────

/** @tag SHOP */
const _ITC_STEPS = [
    {
        targetQuery: '.isl-zone-btn[data-zone="forest"]',
        title:       'Tap a zone',
        body:        'Each zone has its own friend waiting for you.',
        position:    'bottom',
    },
    {
        targetQuery: '#isl-lumi-chip',
        title:       'Your Lumi balance',
        body:        'Earn Lumi by studying, then spend it on food and evolutions.',
        position:    'bottom',
    },
    {
        targetQuery: '#isl-streak-panel',
        title:       'Daily streak',
        body:        'Keep showing up every day — a 7-day streak unlocks a special reward!',
        position:    'top',
    },
    {
        targetQuery: null, // final step: centered card
        title:       "You're all set!",
        body:        'Tap anywhere to start exploring the island.',
        position:    'center',
        final:       true,
    },
];

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _itcStep     = 0;
let _itcActive   = false;
let _itcOverlay  = null;

// ─── Entry ──────────────────────────────────────────────────────

/**
 * Launch the coachmark tour if not already seen.
 * Pass `force=true` to re-show even if previously completed.
 * @tag SHOP
 */
function startCoachmarks(force) {
    if (!force && localStorage.getItem('tutorialSeen') === 'true') return;
    _itcStep   = 0;
    _itcActive = true;
    _itcRender();
}

// ─── Render ─────────────────────────────────────────────────────

/** @tag SHOP */
function _itcRender() {
    _itcRemove();
    if (!_itcActive) return;

    const step = _ITC_STEPS[_itcStep];
    if (!step) { _itcFinish(); return; }

    const overlay = document.createElement('div');
    overlay.id        = 'itc-overlay';
    overlay.className = 'itc-overlay';
    _itcOverlay       = overlay;

    const islandEl = document.getElementById('island-overlay') || document.body;
    islandEl.appendChild(overlay);

    if (step.final) {
        _itcRenderFinal(overlay, step);
    } else {
        _itcRenderSpotlight(overlay, step);
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag SHOP */
function _itcRenderSpotlight(overlay, step) {
    const target = step.targetQuery ? document.querySelector(step.targetQuery) : null;
    const rect   = target ? target.getBoundingClientRect() : null;

    const pad   = 8;
    const top   = rect ? rect.top    - pad : 0;
    const left  = rect ? rect.left   - pad : 0;
    const width = rect ? rect.width  + pad * 2 : 0;
    const height= rect ? rect.height + pad * 2 : 0;

    // Spotlight element uses box-shadow cutout trick
    const spotlight = document.createElement('div');
    spotlight.className = 'itc-spotlight';
    spotlight.style.cssText = rect
        ? `top:${top}px;left:${left}px;width:${width}px;height:${height}px`
        : 'display:none';
    overlay.appendChild(spotlight);

    // Tooltip position
    const isBottom = step.position === 'bottom';
    const tooltipTop = rect
        ? (isBottom ? top + height + 12 : top - 12)
        : '50%';
    const tooltipLeft = rect ? Math.max(8, left) : '50%';

    const skipBtn = `<button class="itc-skip-btn" onclick="_itcSkip()">Skip tour</button>`;
    const stepNum = `${_itcStep + 1} / ${_ITC_STEPS.length}`;

    const tooltip = document.createElement('div');
    tooltip.className = 'itc-tooltip';
    tooltip.style.cssText = rect
        ? `top:${tooltipTop}px;left:${tooltipLeft}px;transform:none`
        : 'top:50%;left:50%;transform:translate(-50%,-50%)';
    tooltip.innerHTML = `
        <p class="itc-tooltip-step">${escapeHtml(stepNum)}</p>
        <p class="itc-tooltip-title">${escapeHtml(step.title)}</p>
        <p class="itc-tooltip-body">${escapeHtml(step.body)}</p>
        <div class="itc-tooltip-actions">
            ${skipBtn}
            <button class="itc-next-btn" onclick="_itcNext()">
                ${_itcStep < _ITC_STEPS.length - 2 ? 'Next <i data-lucide="arrow-right"></i>' : 'Finish'}
            </button>
        </div>`;
    overlay.appendChild(tooltip);

    // Clicking outside spotlight advances to next step
    overlay.addEventListener('click', e => {
        if (e.target === overlay) _itcNext();
    });
}

/** @tag SHOP */
function _itcRenderFinal(overlay, step) {
    const card = document.createElement('div');
    card.className = 'itc-final-card';
    card.innerHTML = `
        <i data-lucide="star" class="itc-final-icon"></i>
        <p class="itc-final-title">${escapeHtml(step.title)}</p>
        <p class="itc-final-body">${escapeHtml(step.body)}</p>
        <button class="itc-next-btn itc-next-btn--cta" onclick="_itcFinish()">
            <i data-lucide="play-circle"></i> Start exploring
        </button>`;
    overlay.appendChild(card);
    overlay.addEventListener('click', e => {
        if (e.target === overlay) _itcFinish();
    });
}

// ─── Progress dots ───────────────────────────────────────────────

/** @tag SHOP */
function _itcDots() {
    return _ITC_STEPS.map((_, i) =>
        `<span class="itc-dot ${i === _itcStep ? 'itc-dot--active' : ''}"></span>`
    ).join('');
}

// ─── Actions ─────────────────────────────────────────────────────

/** @tag SHOP */
function _itcNext() {
    _itcStep++;
    if (_itcStep >= _ITC_STEPS.length) { _itcFinish(); return; }
    _itcRender();
}

/** @tag SHOP */
function _itcSkip() {
    _itcActive = false;
    localStorage.setItem('tutorialSeen', 'true');
    _itcRemove();
}

/** @tag SHOP */
function _itcFinish() {
    _itcActive = false;
    localStorage.setItem('tutorialSeen', 'true');
    _itcRemove();
}

/** @tag SHOP */
function _itcRemove() {
    const el = document.getElementById('itc-overlay');
    if (el) el.remove();
    _itcOverlay = null;
}
