/* ================================================================
   DailyScreen.jsx — Attendance / Missions / Weekly Goals tabs
   Section: Shop (Island)
   Dependencies: IslandMain.jsx (apiFetchJSON, escapeHtml)
   API endpoints: GET /api/island/daily, POST /api/island/daily/claim
   ================================================================ */

// ─── State ──────────────────────────────────────────────────────
/** @tag SHOP */
let _idlData   = null;
let _idlTab    = 'attendance'; // 'attendance' | 'missions' | 'weekly'

// ─── Entry ──────────────────────────────────────────────────────

/** @tag SHOP */
async function openDailyScreen() {
    _idlTab  = 'attendance';
    _idlData = null;
    _idlRenderLoading();
    try {
        _idlData = await apiFetchJSON('/api/island/daily');
    } catch (e) {
        _idlData = { error: e.message || 'Failed to load.' };
    }
    _idlRender();
}

// ─── Loading skeleton ────────────────────────────────────────────

/** @tag SHOP */
function _idlRenderLoading() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (!wrap) return;
    wrap.innerHTML = `
        <div class="idl-screen idl-screen--loading" id="idl-screen">
            <div class="idl-skeleton idl-skeleton--banner"></div>
            <div class="idl-skeleton idl-skeleton--tabs"></div>
            <div class="idl-skeleton idl-skeleton--body"></div>
        </div>`;
}

// ─── Main render ─────────────────────────────────────────────────

/** @tag SHOP */
function _idlRender() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (!wrap) return;

    const d = _idlData || {};
    if (d.error) {
        wrap.innerHTML = `
            <div class="idl-screen" id="idl-screen">
                <button class="idl-back-btn" onclick="_idlClose()"><i data-lucide="arrow-left"></i></button>
                <p class="idl-err">${escapeHtml(d.error)}</p>
            </div>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
        return;
    }

    const streak = d.streak ?? 0;
    const tabs = ['attendance', 'missions', 'weekly'];
    const tabHTML = tabs.map(t => `
        <button class="idl-tab ${_idlTab === t ? 'idl-tab--active' : ''}" onclick="_idlSwitchTab('${t}')">
            ${t.charAt(0).toUpperCase() + t.slice(1)}
        </button>`).join('');

    let bodyHTML = '';
    if (_idlTab === 'attendance') bodyHTML = _idlAttendanceHTML(d);
    else if (_idlTab === 'missions') bodyHTML = _idlMissionsHTML(d);
    else bodyHTML = _idlWeeklyHTML(d);

    wrap.innerHTML = `
        <div class="idl-screen" id="idl-screen">
            <button class="idl-back-btn" onclick="_idlClose()" aria-label="Back">
                <i data-lucide="arrow-left"></i>
            </button>
            <div class="idl-streak-banner">
                <i data-lucide="flame"></i>
                <span>${streak}-day streak</span>
            </div>
            <div class="idl-tabs" role="tablist">
                ${tabHTML}
            </div>
            <div class="idl-body" role="tabpanel">
                ${bodyHTML}
            </div>
        </div>`;

    if (typeof lucide !== 'undefined') lucide.createIcons();
    _idlAttachEsc();
}

// ─── Tab bodies ──────────────────────────────────────────────────

/** @tag SHOP */
function _idlAttendanceHTML(d) {
    const days    = d.attendance_week || [];
    const labels  = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    const cells   = labels.map((lbl, i) => {
        const item  = days[i] || {};
        const cls   = item.claimed ? 'idl-day-cell--claimed' : (item.today ? 'idl-day-cell--today' : '');
        const icon  = item.claimed ? '<i data-lucide="check"></i>' : '';
        return `
            <div class="idl-day-cell ${cls}" title="${item.date || ''}">
                <span class="idl-day-lbl">${lbl}</span>
                ${icon}
            </div>`;
    }).join('');

    const canClaim  = d.can_claim_today && !d.today_claimed;
    const claimBtn  = canClaim
        ? `<button class="idl-claim-btn" onclick="_idlClaimAttendance()">
               <i data-lucide="gift"></i> Claim Today
           </button>`
        : `<button class="idl-claim-btn idl-claim-btn--done" disabled>
               <i data-lucide="check-circle"></i> ${d.today_claimed ? 'Claimed' : 'Come back tomorrow'}
           </button>`;

    return `
        <div class="idl-week-grid">${cells}</div>
        <div class="idl-claim-row">${claimBtn}</div>
        ${d.attendance_reward ? `<p class="idl-reward-hint">
            <i data-lucide="gem"></i> +${d.attendance_reward} Lumi for showing up today
        </p>` : ''}`;
}

/** @tag SHOP */
function _idlMissionsHTML(d) {
    const missions = d.missions || [];
    if (!missions.length) return `<p class="idl-empty-msg">No missions today.</p>`;

    return missions.map(m => {
        const done   = m.completed;
        const locked = m.locked;
        const cls    = done ? 'idl-mission-card--done' : (locked ? 'idl-mission-card--locked' : '');
        const pct    = Math.min(100, Math.round((m.progress / (m.total || 1)) * 100));
        const gaugeCls = done ? 'idl-mission-gauge-fill--done' : 'idl-mission-gauge-fill--active';
        const statusIcon = done ? 'check-circle' : (locked ? 'lock' : 'circle');

        return `
            <div class="idl-mission-card ${cls}">
                <div class="idl-mission-header">
                    <i data-lucide="${statusIcon}" class="idl-mission-status"></i>
                    <span class="idl-mission-title">${escapeHtml(m.title)}</span>
                    <span class="idl-mission-reward"><i data-lucide="gem"></i> +${m.reward_lumi ?? 0}</span>
                </div>
                <p class="idl-mission-desc">${escapeHtml(m.description || '')}</p>
                <div class="idl-mission-gauge-track">
                    <div class="idl-mission-gauge-fill ${gaugeCls}" style="width:${pct}%"></div>
                </div>
                <span class="idl-mission-progress">${m.progress ?? 0} / ${m.total ?? 1}</span>
            </div>`;
    }).join('');
}

/** @tag SHOP */
function _idlWeeklyHTML(d) {
    const goals = d.weekly_goals || [];
    if (!goals.length) return `<p class="idl-empty-msg">No weekly goals set.</p>`;

    return `
        <div class="idl-weekly-list">
            ${goals.map(g => {
                const pct  = Math.min(100, Math.round(((g.current ?? 0) / (g.target || 1)) * 100));
                const done = pct >= 100;
                return `
                    <div class="idl-weekly-row">
                        <div class="idl-weekly-info">
                            <span class="idl-weekly-label">${escapeHtml(g.label)}</span>
                            <span class="idl-weekly-val">${g.current ?? 0} / ${g.target ?? 0}</span>
                        </div>
                        <div class="idl-mission-gauge-track">
                            <div class="idl-mission-gauge-fill ${done ? 'idl-mission-gauge-fill--done' : 'idl-mission-gauge-fill--active'}" style="width:${pct}%"></div>
                        </div>
                    </div>`;
            }).join('')}
        </div>`;
}

// ─── Actions ─────────────────────────────────────────────────────

/** @tag SHOP */
function _idlSwitchTab(tab) {
    if (_idlTab === tab) return;
    const body = document.querySelector('.idl-body');
    if (body) {
        body.classList.add('idl-body--fade');
        setTimeout(() => {
            _idlTab = tab;
            _idlRender();
        }, 150);
    } else {
        _idlTab = tab;
        _idlRender();
    }
}

/** @tag SHOP */
async function _idlClaimAttendance() {
    try {
        const res = await apiFetchJSON('/api/island/daily/claim', { method: 'POST' });
        if (_idlData) {
            _idlData.today_claimed = true;
            _idlData.can_claim_today = false;
            if (res.lumi_earned) {
                // Coin particle celebration (reuses _claimCelebrate from IslandMain.jsx)
                if (typeof _claimCelebrate === 'function') {
                    _claimCelebrate(res.lumi_earned);
                } else if (typeof _showShopToast === 'function') {
                    _showShopToast(`+${res.lumi_earned} Lumi`);
                }
            }
        }
    } catch (_) { /* silent */ }
    _idlRender();
}

// ─── Close / ESC ─────────────────────────────────────────────────

/** @tag SHOP */
function _idlClose() {
    const wrap = document.getElementById('isl-detail-overlay');
    if (wrap) wrap.innerHTML = '';
    _idlData = null;
}

/** @tag SHOP */
function _idlAttachEsc() {
    const fn = e => {
        if (e.key !== 'Escape') return;
        if (document.getElementById('idl-screen')) {
            document.removeEventListener('keydown', fn);
            _idlClose();
        }
    };
    document.addEventListener('keydown', fn);
}
