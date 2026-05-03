/* ================================================================
   LoadingScreen.jsx — App loading states: splash / sync / reconnect
   Section: System (Island)
   Dependencies: core.js (apiFetchJSON), IslandMain.jsx
   API endpoints: none (controls app entry point)
   ================================================================ */

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _ilsVariant   = 'splash'; // 'splash' | 'sync' | 'reconnect'
let _ilsProgress  = 0;        // 0-100 for sync variant
let _ilsTimer     = null;
let _ilsStartTime = 0;
let _ilsOnDone    = null;

// ─── Entry ──────────────────────────────────────────────────────

/**
 * Show loading screen.
 * @param {'splash'|'sync'|'reconnect'} variant
 * @param {function|null} onDone  Called when loading completes.
 * @tag SHOP
 */
function showLoadingScreen(variant, onDone) {
    _ilsVariant   = variant || 'splash';
    _ilsProgress  = 0;
    _ilsOnDone    = onDone || null;
    _ilsStartTime = Date.now();
    _ilsRender();
    _ilsStart();
}

/** @tag SHOP */
function hideLoadingScreen() {
    _ilsClear();
    const el = document.getElementById('ils-screen');
    if (el) el.remove();
}

// ─── Render ─────────────────────────────────────────────────────

/** @tag SHOP */
function _ilsRender() {
    let existing = document.getElementById('ils-screen');
    if (!existing) {
        existing = document.createElement('div');
        existing.id = 'ils-screen';
        document.body.appendChild(existing);
    }
    existing.className = `ils-screen ils-screen--${_ilsVariant}`;
    existing.innerHTML = _ilsInner();
    existing.style.cssText = 'position:fixed;inset:0;z-index:9000;display:flex;flex-direction:column;align-items:center;justify-content:center';
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag SHOP */
function _ilsInner() {
    if (_ilsVariant === 'splash') return _ilsSplashHTML();
    if (_ilsVariant === 'sync')   return _ilsSyncHTML();
    return _ilsReconnectHTML();
}

/** @tag SHOP */
function _ilsSplashHTML() {
    return `
        <div class="ils-logo-wrap">
            <i data-lucide="island" class="ils-logo-icon"></i>
            <span class="ils-logo-name">Gia's Island</span>
        </div>
        <div class="ils-dots" aria-label="Loading" role="status">
            <span class="ils-dot" style="--d:0s"></span>
            <span class="ils-dot" style="--d:0.2s"></span>
            <span class="ils-dot" style="--d:0.4s"></span>
        </div>`;
}

/** @tag SHOP */
function _ilsSyncHTML() {
    const pct = Math.round(_ilsProgress);
    return `
        <i data-lucide="refresh-cw" class="ils-sync-icon"></i>
        <p class="ils-sync-label">Restoring your island…</p>
        <div class="ils-progress-track" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100">
            <div class="ils-progress-fill" id="ils-progress-fill" style="width:${pct}%"></div>
        </div>
        <span class="ils-progress-pct" id="ils-pct">${pct}%</span>`;
}

/** @tag SHOP */
function _ilsReconnectHTML() {
    return `
        <div class="ils-spinner" role="status" aria-label="Reconnecting">
            <i data-lucide="wifi" class="ils-spinner-icon"></i>
        </div>
        <p class="ils-reconnect-label">Reconnecting…</p>`;
}

// ─── Animation drivers ───────────────────────────────────────────

/** @tag SHOP */
function _ilsStart() {
    _ilsClear();
    if (_ilsVariant === 'splash') {
        // Minimum 800ms brand display
        _ilsTimer = setTimeout(() => {
            if (_ilsOnDone) _ilsOnDone();
        }, 800);
    } else if (_ilsVariant === 'sync') {
        _ilsFakeProgress();
    } else {
        // reconnect: show 3s then fallback to error
        _ilsTimer = setTimeout(() => {
            if (_ilsOnDone) _ilsOnDone('timeout');
        }, 3000);
    }
}

/** @tag SHOP */
function _ilsFakeProgress() {
    // Fake progress: fast to 80%, pause, complete on done() call
    _ilsTimer = setInterval(() => {
        if (_ilsProgress < 80) {
            _ilsProgress = Math.min(80, _ilsProgress + (Math.random() * 4 + 1));
        } else if (_ilsProgress < 90) {
            _ilsProgress = Math.min(90, _ilsProgress + 0.3);
        }
        _ilsUpdateProgressBar();
    }, 150);
}

/** @tag SHOP */
function _ilsUpdateProgressBar() {
    const fill = document.getElementById('ils-progress-fill');
    const pctEl = document.getElementById('ils-pct');
    const pct   = Math.round(_ilsProgress);
    if (fill)  fill.style.width   = `${pct}%`;
    if (pctEl) pctEl.textContent  = `${pct}%`;
    const track = fill?.parentElement;
    if (track) track.setAttribute('aria-valuenow', String(pct));
}

/**
 * Complete sync progress to 100% and fire onDone.
 * @tag SHOP
 */
function completeSyncProgress() {
    _ilsClear();
    _ilsProgress = 100;
    _ilsUpdateProgressBar();
    setTimeout(() => {
        if (_ilsOnDone) _ilsOnDone();
    }, 300);
}

/** @tag SHOP */
function _ilsClear() {
    if (_ilsTimer) {
        clearTimeout(_ilsTimer);
        clearInterval(_ilsTimer);
        _ilsTimer = null;
    }
}
