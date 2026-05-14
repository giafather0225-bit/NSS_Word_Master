/* ================================================================
   SettingsScreen.jsx — 2-pane island settings (6 sections)
   Section: Shop (Island)
   Dependencies: IslandMain.jsx (apiFetchJSON, escapeHtml)
   API endpoints: GET /api/island/config (app_version only; prefs stored in localStorage)
   ================================================================ */

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _issSection  = 'account'; // account|sound|notify|lang|support|about
let _issSettings = {};

const _ISS_SECTIONS = [
    { id: 'account', icon: 'user',        label: 'Account'      },
    { id: 'sound',   icon: 'volume-2',    label: 'Sound'        },
    { id: 'notify',  icon: 'bell',        label: 'Notifications'},
    { id: 'lang',    icon: 'globe',       label: 'Language'     },
    { id: 'support', icon: 'help-circle', label: 'Support'      },
    { id: 'about',   icon: 'info',        label: 'About'        },
    { id: 'dev',     icon: 'wrench',      label: 'Dev Tools'    },
];

// ─── Entry ──────────────────────────────────────────────────────

/** @tag SHOP */
async function openSettingsScreen() {
    _issSection  = 'account';
    _issSettings = _issLoadLocal();
    _issRender();
    try {
        const cfg = await apiFetchJSON('/api/island/config');
        if (cfg?.app_version) {
            _issSettings.app_version = cfg.app_version;
            _issRender();
        }
    } catch (_) { /* version stays blank */ }
}

function _issLoadLocal() {
    try { return JSON.parse(localStorage.getItem('island_settings') || '{}'); } catch (_) { return {}; }
}

function _issSaveLocal(patch) {
    const cur = _issLoadLocal();
    const next = Object.assign({}, cur, patch);
    localStorage.setItem('island_settings', JSON.stringify(next));
    return next;
}

// ─── Render ─────────────────────────────────────────────────────

/** @tag SHOP */
function _issRender() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (!wrap) return;

    const navItems = _ISS_SECTIONS.map(s => `
        <button class="iss-nav-item ${_issSection === s.id ? 'iss-nav-item--active' : ''}"
                onclick="_issSwitchSection('${s.id}')">
            <i data-lucide="${s.icon}"></i>
            <span>${s.label}</span>
        </button>`).join('');

    wrap.innerHTML = `
        <div class="iss-screen" id="iss-screen">
            <button class="iss-back-btn" onclick="_issClose()" aria-label="Back">
                <i data-lucide="arrow-left"></i>
            </button>
            <div class="iss-layout">
                <nav class="iss-sidenav" role="navigation" aria-label="Settings sections">
                    ${navItems}
                </nav>
                <div class="iss-panel" id="iss-panel">
                    ${_issPanelHTML()}
                </div>
            </div>
        </div>`;

    if (typeof lucide !== 'undefined') lucide.createIcons();
    _issAttachEsc();
}

/** @tag SHOP */
function _issPanelHTML() {
    switch (_issSection) {
        case 'account':  return _issAccountPanel();
        case 'sound':    return _issSoundPanel();
        case 'notify':   return _issNotifyPanel();
        case 'lang':     return _issLangPanel();
        case 'support':  return _issSupportPanel();
        case 'about':    return _issAboutPanel();
        case 'dev':      return _issDevPanel();
        default:         return '';
    }
}

// ─── Section panels ──────────────────────────────────────────────

/** @tag SHOP */
function _issAccountPanel() {
    const name = escapeHtml(_issSettings.display_name || 'Gia');
    return `
        <h2 class="iss-panel-title">Account</h2>
        <div class="iss-profile-card">
            <div class="iss-avatar-ring"><i data-lucide="user-circle"></i></div>
            <div class="iss-profile-info">
                <span class="iss-profile-name">${name}</span>
                <span class="iss-profile-sub">Island Explorer</span>
            </div>
        </div>
        ${_issRow('Edit display name', 'pen-line', '', 'chevron-right', null, '')}`;
}

/** @tag SHOP */
function _issSoundPanel() {
    const bgm  = _issSettings.bgm_on  !== false;
    const sfx  = _issSettings.sfx_on  !== false;
    const vol  = _issSettings.volume  ?? 80;
    return `
        <h2 class="iss-panel-title">Sound</h2>
        ${_issToggleRow('Background music', 'music',  bgm, "issToggle('bgm_on')")}
        ${_issToggleRow('Sound effects',    'zap',    sfx, "issToggle('sfx_on')")}
        <div class="iss-row">
            <i data-lucide="volume-2" class="iss-row-ico"></i>
            <div class="iss-row-body">
                <span class="iss-row-label">Volume</span>
                <div class="iss-vol-track">
                    <div class="iss-vol-fill" id="iss-vol-fill" style="width:${vol}%"></div>
                    <input type="range" class="iss-vol-range" min="0" max="100" value="${vol}"
                           oninput="_issVolChange(this.value)" aria-label="Volume">
                </div>
            </div>
        </div>`;
}

/** @tag SHOP */
function _issNotifyPanel() {
    const notifs = _issSettings.notifications_on !== false;
    const hungry = _issSettings.notify_hungry    !== false;
    const streak = _issSettings.notify_streak    !== false;
    const evo    = _issSettings.notify_evolution !== false;
    return `
        <h2 class="iss-panel-title">Notifications</h2>
        ${_issToggleRow('Allow notifications',  'bell',         notifs, "issToggle('notifications_on')")}
        ${_issToggleRow('Hungry reminders',     'utensils',     hungry, "issToggle('notify_hungry')")}
        ${_issToggleRow('Streak reminders',     'flame',        streak, "issToggle('notify_streak')")}
        ${_issToggleRow('Evolution ready',      'sparkles',     evo,    "issToggle('notify_evolution')")}
        <div class="iss-notify-info">
            <i data-lucide="info"></i>
            <span>Quiet hours: 22:00 – 08:00 KST</span>
        </div>`;
}

/** @tag SHOP */
function _issLangPanel() {
    const lang = _issSettings.language || 'en';
    const opts = [
        { val: 'en', label: 'English' },
        { val: 'ko', label: '한국어'  },
    ];
    const optHTML = opts.map(o =>
        `<option value="${o.val}" ${lang === o.val ? 'selected' : ''}>${o.label}</option>`
    ).join('');
    return `
        <h2 class="iss-panel-title">Language</h2>
        <div class="iss-row">
            <i data-lucide="globe" class="iss-row-ico"></i>
            <div class="iss-row-body">
                <span class="iss-row-label">App language</span>
                <select class="iss-select" onchange="_issLangChange(this.value)" aria-label="Language">
                    ${optHTML}
                </select>
            </div>
        </div>`;
}

/** @tag SHOP */
function _issSupportPanel() {
    return `
        <h2 class="iss-panel-title">Support</h2>
        ${_issRow('How to play',       'book-open',     '', 'chevron-right')}
        ${_issRow('Report a problem',  'alert-triangle','', 'chevron-right')}
        ${_issRow('Send feedback',     'message-square','', 'chevron-right')}`;
}

/** @tag SHOP */
function _issAboutPanel() {
    const ver = _issSettings.app_version || '1.0';
    return `
        <h2 class="iss-panel-title">About</h2>
        ${_issRow("Gia's Island", 'map', `v${ver}`, '')}
        ${_issRow('Open source licenses', 'file-text', '', 'chevron-right')}
        ${_issRow('Privacy policy',        'shield',    '', 'chevron-right')}`;
}

// ─── Dev Tools panel ─────────────────────────────────────────────

/** @tag SHOP */
function _issDevPanel() {
    return `
        <h2 class="iss-panel-title">Dev Tools</h2>
        <div class="iss-dev-notice">
            <i data-lucide="triangle-alert"></i>
            <span>Testing only — bypasses game constraints</span>
        </div>
        <div class="iss-dev-btn-list">
            <button class="iss-dev-btn" onclick="_issDevAction('seed')">
                <i data-lucide="coins"></i>
                <div>
                    <span class="iss-dev-btn-label">Add Lumi + Stones + Max Gauges</span>
                    <span class="iss-dev-btn-sub">+9999 Lumi, +5 each evo stone, hunger/happiness → 100</span>
                </div>
            </button>
            <button class="iss-dev-btn" onclick="_issDevAction('level-up')">
                <i data-lucide="arrow-up-circle"></i>
                <div>
                    <span class="iss-dev-btn-label">Level Up to Evo-Ready</span>
                    <span class="iss-dev-btn-sub">Push active chars to max level of their stage</span>
                </div>
            </button>
            <button class="iss-dev-btn" onclick="_issDevAction('unlock-zones')">
                <i data-lucide="unlock"></i>
                <div>
                    <span class="iss-dev-btn-label">Unlock All Zones</span>
                    <span class="iss-dev-btn-sub">Forest, Ocean, Savanna, Space, Legend</span>
                </div>
            </button>
        </div>`;
}

/** @tag SHOP */
async function _issDevAction(action) {
    const btns = document.querySelectorAll('.iss-dev-btn');
    btns.forEach(b => { b.disabled = true; });
    try {
        const result = await apiFetchJSON('/api/island/dev/' + action, { method: 'POST' });
        if (typeof _showShopToast === 'function') _showShopToast('Done: ' + JSON.stringify(result));
    } catch (err) {
        if (typeof _showShopToast === 'function') _showShopToast(err?.detail || 'Dev action failed.', true);
    } finally {
        btns.forEach(b => { b.disabled = false; });
    }
}

// ─── Row helpers ─────────────────────────────────────────────────

/** @tag SHOP */
function _issToggleRow(label, icon, on, cb) {
    return `
        <div class="iss-row iss-toggle-row" role="group">
            <i data-lucide="${icon}" class="iss-row-ico"></i>
            <div class="iss-row-body">
                <span class="iss-row-label">${label}</span>
            </div>
            <button class="iss-toggle ${on ? 'iss-toggle--on' : ''}" onclick="${cb}" aria-checked="${on}" role="switch">
                <span class="iss-toggle-thumb"></span>
            </button>
        </div>`;
}

/** @tag SHOP */
function _issRow(label, icon, sub, rightIcon, onclick, extraCls) {
    const cls = ['iss-row', extraCls || ''].filter(Boolean).join(' ');
    const fn  = onclick ? `onclick="${onclick}"` : '';
    const btn = rightIcon ? `<i data-lucide="${rightIcon}" class="iss-row-right"></i>` : '';
    const subEl = sub ? `<span class="iss-row-sub">${escapeHtml(sub)}</span>` : '';
    return `
        <div class="${cls}" ${fn}>
            <i data-lucide="${icon}" class="iss-row-ico"></i>
            <div class="iss-row-body">
                <span class="iss-row-label">${label}</span>
                ${subEl}
            </div>
            ${btn}
        </div>`;
}

// ─── Interactions ────────────────────────────────────────────────

/** @tag SHOP */
function issToggle(key) {
    _issSettings[key] = !(_issSettings[key] !== false);
    _issSaveLocal({ [key]: _issSettings[key] });
    const panel = document.getElementById('iss-panel');
    if (panel) {
        panel.innerHTML = _issPanelHTML();
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

/** @tag SHOP */
function _issVolChange(val) {
    const n = Number(val);
    _issSettings.volume = n;
    const fill = document.getElementById('iss-vol-fill');
    if (fill) fill.style.width = `${n}%`;
    clearTimeout(_issVolChange._t);
    _issVolChange._t = setTimeout(() => _issSaveLocal({ volume: n }), 600);
}

/** @tag SHOP */
function _issLangChange(val) {
    _issSettings.language = val;
    _issSaveLocal({ language: val });
}

/** @tag SHOP */
function _issSwitchSection(sec) {
    _issSection = sec;
    _issRender();
}

// ─── Close / ESC ─────────────────────────────────────────────────

/** @tag SHOP */
function _issClose() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (wrap) wrap.innerHTML = '';
    _issSettings = {};
}

/** @tag SHOP */
function _issAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        if (document.getElementById('iss-screen')) {
            document.removeEventListener('keydown', fn);
            _issClose();
        }
    };
    document.addEventListener('keydown', fn);
}
