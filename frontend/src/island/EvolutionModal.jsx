/* ================================================================
   EvolutionModal.jsx — Island evolution branch selection modal.
   Section: Shop (Island)
   Dependencies: core.js (escapeHtml, apiFetchJSON), CharacterDetail.jsx
                 (_showShopToast), ZoneDetail.jsx (openZoneDetail, _zdZone)
   API endpoints: POST /api/island/evolve/validate,
                  POST /api/island/character/evolve
   ================================================================ */

// ─── State ───────────────────────────────────────────────────
/** @tag SHOP */
let _emProgId    = null;
let _emEvoStage  = null;
let _emCharName  = null;
let _emSelection = null;   // 'a' | 'b' | null
let _emValidData = null;   // validate response

// ─── Open / Close ─────────────────────────────────────────────

/** Show evolution branch modal. @tag SHOP */
async function openEvolutionModal(progId, currentStage, charName) {
    _emProgId   = progId;
    _emEvoStage = currentStage;
    _emCharName = charName;
    _emSelection = null;
    _emValidData = null;

    const el = document.getElementById('isl-evo-modal');
    if (!el) return;
    el.classList.remove('hidden');
    _emRenderLoading(el);

    try {
        _emValidData = await apiFetchJSON('/api/island/evolve/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character_progress_id: progId }),
        });
        if (!_emValidData.valid) {
            _emRenderError(el, _emValidData.message || 'Cannot evolve right now.');
            return;
        }
        _emRenderModal(el, _emValidData);
    } catch (err) {
        _emRenderError(el, err?.detail || 'Evolution check failed.');
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** Close modal, return to character detail or zone detail. @tag SHOP */
function _closeEvoModal() {
    const el = document.getElementById('isl-evo-modal');
    if (el) { el.classList.add('hidden'); el.innerHTML = ''; }
    _emProgId = _emEvoStage = _emCharName = _emSelection = _emValidData = null;
}

// ─── Loading / Error states ───────────────────────────────────

/** @tag SHOP */
function _emRenderLoading(el) {
    el.innerHTML = `<div class="iem-backdrop">
        <div class="iem-box iem-box--loading">
            <div class="isl-loading-ship"><i data-lucide="anchor"></i></div>
            <div class="isl-state-text">Checking evolution...</div>
        </div>
    </div>`;
}

/** @tag SHOP */
function _emRenderError(el, msg) {
    el.innerHTML = `<div class="iem-backdrop" onclick="_closeEvoModal()">
        <div class="iem-box" onclick="event.stopPropagation()">
            <div class="iem-header">
                <div class="iem-title">Evolution</div>
                <button class="iem-close" onclick="_closeEvoModal()" aria-label="Close">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="isl-state-icon"><i data-lucide="alert-triangle"></i></div>
            <div class="isl-state-text">${escapeHtml(msg)}</div>
            <button class="isl-back-btn" onclick="_closeEvoModal()">Close</button>
        </div>
    </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Main render ─────────────────────────────────────────────

const _EM_STAGE_LABELS = { baby:'Baby', mid_a:'Mid A', mid_b:'Mid B', final_a:'Final A', final_b:'Final B' };
const _EM_STONE_LABELS = {
    first_a: '1st Stone (A)', first_b: '1st Stone (B)',
    second: '2nd Stone', second_a: '2nd Stone (A)', second_b: '2nd Stone (B)',
    legend_first_a: 'Legend Stone (A)', legend_first_b: 'Legend Stone (B)',
    legend_second: 'Legend Stone (2nd)',
};

/** @tag SHOP */
function _emRenderModal(el, d) {
    const nameHtml = escapeHtml(_emCharName || 'Character');
    const rawStoneA = d.branch_a?.stone || '';
    const rawStoneB = d.branch_b?.stone || '';
    const rawTargetA = d.branch_a?.target_stage || 'mid_a';
    const rawTargetB = d.branch_b?.target_stage || 'mid_b';
    const stoneA   = escapeHtml(_EM_STONE_LABELS[rawStoneA] || rawStoneA || 'Stone A');
    const stoneB   = escapeHtml(_EM_STONE_LABELS[rawStoneB] || rawStoneB || 'Stone B');
    const targetA  = escapeHtml(_EM_STAGE_LABELS[rawTargetA] || rawTargetA);
    const targetB  = escapeHtml(_EM_STAGE_LABELS[rawTargetB] || rawTargetB);
    const descA    = escapeHtml(`Evolve into ${_EM_STAGE_LABELS[rawTargetA] || rawTargetA} form.`);
    const descB    = escapeHtml(`Evolve into ${_EM_STAGE_LABELS[rawTargetB] || rawTargetB} form.`);

    el.innerHTML = `
        <div class="iem-backdrop" onclick="_closeEvoModal()">
            <div class="iem-box" onclick="event.stopPropagation()">
                <div class="iem-header">
                    <div class="iem-title">
                        <i data-lucide="sparkles"></i>
                        ${nameHtml} — Choose Evolution
                    </div>
                    <button class="iem-close" onclick="_closeEvoModal()" aria-label="Close">
                        <i data-lucide="x"></i>
                    </button>
                </div>
                <div class="iem-stone-row">
                    <i data-lucide="gem"></i>
                    <span>Use evolution stone to evolve. <strong>This choice cannot be undone.</strong></span>
                </div>
                <div class="iem-branches">
                    <div class="iem-branch" id="iem-branch-a" onclick="_emSelectBranch('a')">
                        <div class="iem-branch-check" id="iem-check-a">
                            <i data-lucide="circle"></i>
                        </div>
                        <div class="iem-branch-avatar iem-branch-avatar--a">A</div>
                        <div class="iem-branch-label">${targetA}</div>
                        <div class="iem-branch-stone">${stoneA}</div>
                        <div class="iem-branch-desc">${descA}</div>
                    </div>
                    <div class="iem-vs">VS</div>
                    <div class="iem-branch" id="iem-branch-b" onclick="_emSelectBranch('b')">
                        <div class="iem-branch-check" id="iem-check-b">
                            <i data-lucide="circle"></i>
                        </div>
                        <div class="iem-branch-avatar iem-branch-avatar--b">B</div>
                        <div class="iem-branch-label">${targetB}</div>
                        <div class="iem-branch-stone">${stoneB}</div>
                        <div class="iem-branch-desc">${descB}</div>
                    </div>
                </div>
                <div class="iem-warning">
                    <i data-lucide="alert-triangle"></i>
                    Once you choose a path, the other branch will be locked forever.
                </div>
                <button class="iem-confirm-btn" id="iem-confirm-btn"
                        onclick="_emConfirm()" disabled>
                    Confirm Evolution
                </button>
            </div>
        </div>`;
}

// ─── Branch selection ─────────────────────────────────────────

/** @tag SHOP */
function _emSelectBranch(branch) {
    _emSelection = branch;
    const bA = document.getElementById('iem-branch-a');
    const bB = document.getElementById('iem-branch-b');
    const cA = document.getElementById('iem-check-a');
    const cB = document.getElementById('iem-check-b');
    const btn = document.getElementById('iem-confirm-btn');
    if (!bA || !bB) return;

    bA.classList.toggle('iem-branch--selected', branch === 'a');
    bB.classList.toggle('iem-branch--selected', branch === 'b');

    if (cA) cA.innerHTML = branch === 'a'
        ? '<i data-lucide="check-circle"></i>' : '<i data-lucide="circle"></i>';
    if (cB) cB.innerHTML = branch === 'b'
        ? '<i data-lucide="check-circle"></i>' : '<i data-lucide="circle"></i>';

    if (btn) btn.disabled = false;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ─── Confirm ──────────────────────────────────────────────────

/** @tag SHOP */
async function _emConfirm() {
    if (!_emSelection || !_emProgId) return;
    const btn = document.getElementById('iem-confirm-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Evolving…'; }

    // Snapshot legend unlock state before evolution to detect a new unlock.
    const legendWasUnlocked = _islandStatus?.zones
        ? !!_islandStatus.zones.find(z => z.zone === 'legend')?.is_unlocked
        : false;

    try {
        const result = await apiFetchJSON('/api/island/character/evolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character_progress_id: _emProgId,
                branch: _emSelection,
            }),
        });
        // Capture these before _closeEvoModal clears module state.
        // Capture all needed state before _closeEvoModal wipes _em* vars.
        const zone     = _cdZone || _zdZone || 'forest';
        const charName = _emCharName || 'Character';
        const progId   = _emProgId;
        _closeEvoModal();

        if (result.is_completed) {
            _showCharCompletion(result, zone, charName);
        } else {
            _showMidEvoReveal(result, zone, charName, progId);
        }

        // Check if legend zone just unlocked via this evolution.
        if (!legendWasUnlocked) {
            try {
                const ls = await apiFetchJSON('/api/island/legend/unlock/status');
                if (ls.legend_unlocked) _showLegendUnlock();
            } catch (_) {}
        }
    } catch (err) {
        if (btn) { btn.disabled = false; btn.textContent = 'Confirm Evolution'; }
        _showShopToast(err?.detail || 'Evolution failed.', true);
    }
}

/** Navigate back to character or zone detail after evolution. @tag SHOP */
function _emRefreshBack() {
    if (_cdProgId) {
        openCharacterDetail(_cdProgId, _cdZone);
    } else if (_zdZone) {
        openZoneDetail(_zdZone);
    }
}

// ─── Mid-stage Evolution Reveal ───────────────────────────────

/** Show full-screen reveal when baby evolves to mid_a or mid_b. @tag SHOP */
function _showMidEvoReveal(result, zone, charName, progId) {
    const overlay = document.createElement('div');
    overlay.id    = 'imer-overlay';
    overlay.className = `icc-overlay icc-${zone}`;

    const icon       = (_ZONE_META?.[zone] || {}).lucideIcon || 'star';
    const newStage   = result.new_stage || '';
    const stageLabel = {
        mid_a: 'Mid Form A', mid_b: 'Mid Form B',
        final_a: 'Final Form A', final_b: 'Final Form B',
    }[newStage] || newStage;

    overlay.innerHTML = `
        <div class="icc-bloom"></div>
        <div class="icc-particles" id="imer-particles"></div>
        <div class="icc-content">
            <div class="icc-char-emoji"><i data-lucide="${icon}"></i></div>
            <div class="icc-badge">EVOLVED!</div>
            <div class="icc-name">${escapeHtml(charName)}</div>
            <div class="icc-subtitle">grew into ${escapeHtml(stageLabel)}!</div>
            <button class="icc-continue-btn" onclick="_closeMidEvoReveal(${progId},'${zone}')">
                <i data-lucide="arrow-right"></i> Continue
            </button>
        </div>`;

    document.body.appendChild(overlay);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    const colors = _ZONE_PARTICLE_COLORS[zone] || _ZONE_PARTICLE_COLORS.forest;
    const pEl = document.getElementById('imer-particles');
    if (pEl) {
        for (let i = 0; i < 14; i++) {
            const p = document.createElement('div');
            p.className = 'icc-particle';
            p.style.cssText = [
                `left:${5 + Math.random() * 90}%`,
                `bottom:${Math.random() * 40}%`,
                `background:${colors[i % colors.length]}`,
                `--dur:${1.4 + Math.random() * 1.2}s`,
                `--delay:${Math.random() * 1.2}s`,
                `width:${5 + Math.random() * 7}px`,
                `height:${5 + Math.random() * 7}px`,
            ].join(';');
            pEl.appendChild(p);
        }
    }
}

/** Dismiss mid-evolution reveal, refresh island map, open evolved character's detail. @tag SHOP */
function _closeMidEvoReveal(progId, zone) {
    const el = document.getElementById('imer-overlay');
    if (el) el.remove();
    if (typeof openIslandMain === 'function') openIslandMain();
    openCharacterDetail(progId, zone);
}

// ─── Character Completion Celebration ─────────────────────────

const _ZONE_PARTICLE_COLORS = {
    forest:  ['var(--english-primary)', 'var(--english-soft)', 'var(--math-primary)'],
    ocean:   ['var(--math-primary)', 'var(--math-soft)', 'var(--english-primary)'],
    savanna: ['var(--diary-primary)', 'var(--diary-soft)', 'var(--arcade-primary)'],
    space:   ['var(--rewards-primary)', 'var(--rewards-soft)', 'var(--arcade-primary)'],
    legend:  ['var(--arcade-primary)', 'var(--arcade-soft)', 'var(--rewards-primary)'],
};

/** Show full-screen completion celebration. @tag SHOP */
function _showCharCompletion(result, zone, charName) {
    const overlay = document.createElement('div');
    overlay.id    = 'icc-overlay';
    overlay.className = `icc-overlay icc-${zone}`;

    const icon  = (_ZONE_META?.[zone] || {}).lucideIcon || 'star';
    const boostSubject = result.boost_subject
        ? result.boost_subject.charAt(0).toUpperCase() + result.boost_subject.slice(1)
        : '';
    const stageLabel = { final_a: 'Final Form A', final_b: 'Final Form B' }[result.new_stage] || result.new_stage || '';

    const attrsHtml = [
        boostSubject ? `<span class="icc-attr"><i data-lucide="zap"></i> ${escapeHtml(boostSubject)} Boost</span>` : '',
        stageLabel   ? `<span class="icc-attr"><i data-lucide="star"></i> ${escapeHtml(stageLabel)}</span>` : '',
        `<span class="icc-attr"><i data-lucide="gem"></i> Lumi Production Active</span>`,
    ].filter(Boolean).join('');

    overlay.innerHTML = `
        <div class="icc-bloom"></div>
        <div class="icc-particles" id="icc-particles"></div>
        <div class="icc-content">
            <div class="icc-char-emoji"><i data-lucide="${icon}"></i></div>
            <div class="icc-badge">COMPLETE!</div>
            <div class="icc-name">${escapeHtml(charName)}</div>
            <div class="icc-subtitle">is fully evolved!</div>
            <div class="icc-attrs">${attrsHtml}</div>
            <button class="icc-continue-btn" onclick="_closeCharCompletion()">
                <i data-lucide="arrow-right"></i> Continue
            </button>
        </div>`;

    document.body.appendChild(overlay);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Spawn particles
    const colors = _ZONE_PARTICLE_COLORS[zone] || _ZONE_PARTICLE_COLORS.forest;
    const pEl = document.getElementById('icc-particles');
    if (pEl) {
        for (let i = 0; i < 18; i++) {
            const p = document.createElement('div');
            p.className = 'icc-particle';
            p.style.cssText = [
                `left:${5 + Math.random() * 90}%`,
                `bottom:${Math.random() * 40}%`,
                `background:${colors[i % colors.length]}`,
                `--dur:${1.6 + Math.random() * 1.4}s`,
                `--delay:${Math.random() * 1.5}s`,
                `width:${6 + Math.random() * 8}px`,
                `height:${6 + Math.random() * 8}px`,
            ].join(';');
            pEl.appendChild(p);
        }
    }
}

/** Dismiss completion overlay and refresh the island view. @tag SHOP */
function _closeCharCompletion() {
    const el = document.getElementById('icc-overlay');
    if (el) el.remove();
    _emRefreshBack();
    // Reload island map so boost/lumi production is reflected.
    if (typeof openIslandMain === 'function') openIslandMain();
}

// ─── Legend Zone Unlock Animation ─────────────────────────────

/** Show Legend Isle awakens full-screen animation. @tag SHOP */
function _showLegendUnlock() {
    const overlay = document.createElement('div');
    overlay.id        = 'ilu-overlay';
    overlay.className = 'ilu-overlay';
    overlay.onclick   = _closeLegendUnlock;

    overlay.innerHTML = `
        <div class="ilu-light"></div>
        <div class="ilu-silhouette"></div>
        <div class="ilu-icon"><i data-lucide="sparkles"></i></div>
        <div class="ilu-text">The Legend Isle awakens...</div>
        <div class="ilu-subtitle">All four zones are now connected.</div>
        <button class="ilu-tap-hint" onclick="_closeLegendUnlock()">Tap to continue</button>`;

    document.body.appendChild(overlay);
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** Dismiss legend unlock overlay and reload island map. @tag SHOP */
function _closeLegendUnlock() {
    const el = document.getElementById('ilu-overlay');
    if (el) el.remove();
    if (typeof openIslandMain === 'function') openIslandMain();
}
