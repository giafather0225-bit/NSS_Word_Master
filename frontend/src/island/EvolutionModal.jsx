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
let _iccZone     = null;   // zone for completion overlay (needed by _closeCharCompletion)

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
    const nameHtml   = escapeHtml(_emCharName || 'Character');
    const ba         = d.branch_a || {};
    const bb         = d.branch_b || {};
    const rawStoneA  = ba.stone || '';
    const rawStoneB  = bb.stone || '';
    const rawTargetA = ba.target_stage || 'mid_a';
    const rawTargetB = bb.target_stage || 'mid_b';
    const stoneA     = escapeHtml(_EM_STONE_LABELS[rawStoneA] || rawStoneA || 'Stone A');
    const stoneB     = escapeHtml(_EM_STONE_LABELS[rawStoneB] || rawStoneB || 'Stone B');
    const abilityA   = escapeHtml(ba.ability || (_EM_STAGE_LABELS[rawTargetA] || rawTargetA));
    const abilityB   = escapeHtml(bb.ability || (_EM_STAGE_LABELS[rawTargetB] || rawTargetB));
    const descA      = escapeHtml(ba.description || `Evolve into ${rawTargetA} form.`);
    const descB      = escapeHtml(bb.description || `Evolve into ${rawTargetB} form.`);
    const boostA     = escapeHtml(ba.boost_preview || '');
    const boostB     = escapeHtml(bb.boost_preview || '');
    const iconA      = ba.boost_icon || 'zap';
    const iconB      = bb.boost_icon || 'gem';

    // Build target-stage image preview from images JSON.
    let imgA = '', imgB = '';
    try {
        const imgs = JSON.parse(d.images || '{}');
        if (imgs[rawTargetA]) imgA = `/static/img/island/${imgs[rawTargetA]}`;
        if (imgs[rawTargetB]) imgB = `/static/img/island/${imgs[rawTargetB]}`;
    } catch (_) {}

    const _branchImg = (src, alt) => src
        ? `<img src="${src}" class="iem-branch-img" alt="${alt}" />`
        : `<div class="iem-branch-img-placeholder"><i data-lucide="sparkles"></i></div>`;

    el.innerHTML = `
        <div class="iem-backdrop" onclick="_closeEvoModal()">
            <div class="iem-box" onclick="event.stopPropagation()">
                <div class="iem-header">
                    <div class="iem-title">
                        <i data-lucide="sparkles"></i>
                        ${nameHtml} — Choose a Path
                    </div>
                    <button class="iem-close" onclick="_closeEvoModal()" aria-label="Close">
                        <i data-lucide="x"></i>
                    </button>
                </div>
                <div class="iem-stone-row">
                    <i data-lucide="gem"></i>
                    <span>This choice is <strong>permanent</strong> — pick the ability that fits your style.</span>
                </div>
                <div class="iem-branches">
                    <div class="iem-branch" id="iem-branch-a" onclick="_emSelectBranch('a')">
                        <div class="iem-branch-check" id="iem-check-a">
                            <i data-lucide="circle"></i>
                        </div>
                        <div class="iem-branch-preview">
                            ${_branchImg(imgA, abilityA)}
                        </div>
                        <div class="iem-branch-ability">
                            <i data-lucide="${iconA}"></i>
                            ${abilityA}
                        </div>
                        <div class="iem-branch-boost">${boostA}</div>
                        <div class="iem-branch-desc">${descA}</div>
                        <div class="iem-branch-stone">${stoneA}</div>
                    </div>
                    <div class="iem-vs">OR</div>
                    <div class="iem-branch" id="iem-branch-b" onclick="_emSelectBranch('b')">
                        <div class="iem-branch-check" id="iem-check-b">
                            <i data-lucide="circle"></i>
                        </div>
                        <div class="iem-branch-preview">
                            ${_branchImg(imgB, abilityB)}
                        </div>
                        <div class="iem-branch-ability">
                            <i data-lucide="${iconB}"></i>
                            ${abilityB}
                        </div>
                        <div class="iem-branch-boost">${boostB}</div>
                        <div class="iem-branch-desc">${descB}</div>
                        <div class="iem-branch-stone">${stoneB}</div>
                    </div>
                </div>
                <div class="iem-warning">
                    <i data-lucide="alert-triangle"></i>
                    The other path will be locked forever once you choose.
                </div>
                <button class="iem-confirm-btn" id="iem-confirm-btn"
                        onclick="_emConfirm()" disabled>
                    <i data-lucide="sparkles"></i>
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

    // Capture before-state while _emValidData is still populated.
    const beforeStage = _emEvoStage || 'baby';
    const chosenBranch = _emSelection === 'a' ? (_emValidData?.branch_a || {}) : (_emValidData?.branch_b || {});
    const afterStage   = chosenBranch.target_stage || '';
    const chosenAbility = chosenBranch.ability || '';
    const chosenBoost   = chosenBranch.boost_preview || '';
    let beforeImgSrc = '', afterImgSrc = '';
    try {
        const imgs = JSON.parse(_emValidData?.images || '{}');
        if (imgs[beforeStage]) beforeImgSrc = `/static/img/island/${imgs[beforeStage]}`;
        if (imgs[afterStage])  afterImgSrc  = `/static/img/island/${imgs[afterStage]}`;
    } catch (_) {}

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
        // Capture zone/name/progId before _closeEvoModal wipes _em* vars.
        const zone     = _cdZone || _zdZone || 'forest';
        const charName = _emCharName || 'Character';
        const progId   = _emProgId;
        _closeEvoModal();

        // P4: 3-step evolution sequence instead of jumping straight to celebration.
        _runEvoSequence({
            beforeImgSrc, afterImgSrc,
            beforeStage, afterStage,
            chosenAbility, chosenBoost,
            result, zone, charName, progId,
        });

        // Check if legend zone just unlocked via this evolution.
        if (!legendWasUnlocked) {
            try {
                const ls = await apiFetchJSON('/api/island/legend/unlock/status');
                if (ls.legend_unlocked) _showLegendUnlock();
            } catch (_) {}
        }
    } catch (err) {
        if (btn) { btn.disabled = false; btn.textContent = 'Confirm Evolution'; }
        _showShopToast(err?.message || err?.detail || 'Evolution failed.', true);
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

// ─── P4: 3-step Evolution Sequence ────────────────────────────

/**
 * Orchestrate 3-step evolution: flash → before/after → celebration.
 * @tag SHOP
 */
function _runEvoSequence({ beforeImgSrc, afterImgSrc, beforeStage, afterStage,
                            chosenAbility, chosenBoost, result, zone, charName, progId }) {
    // Step 1: white flash (auto-advance after 700ms)
    const flash = document.createElement('div');
    flash.id = 'iem-flash-overlay';
    flash.className = 'iem-flash-overlay';
    document.body.appendChild(flash);

    // Trigger paint then add --in to animate opacity.
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            flash.classList.add('iem-flash-overlay--in');
        });
    });

    setTimeout(() => {
        // Fade flash out.
        flash.classList.remove('iem-flash-overlay--in');
        flash.classList.add('iem-flash-overlay--out');

        // Step 2: show before/after panel while flash is fading.
        _showEvoBeforeAfter({
            beforeImgSrc, afterImgSrc, beforeStage, afterStage,
            chosenAbility, chosenBoost, result, zone, charName, progId,
        });

        setTimeout(() => flash.remove(), 400);
    }, 700);
}

/** Build an img or placeholder div for before/after panel. @tag SHOP */
function _baImg(src, className = '') {
    const wrap = document.createElement('div');
    wrap.className = `iem-ba-img-wrap ${className}`;
    if (src) {
        const img = document.createElement('img');
        img.src = src;
        img.alt = '';
        wrap.appendChild(img);
    } else {
        const ph = document.createElement('div');
        ph.className = 'iem-ba-img-placeholder';
        ph.innerHTML = '<i data-lucide="sparkles"></i>';
        wrap.appendChild(ph);
    }
    return wrap;
}

/** Step 2: full-screen before/after comparison panel. @tag SHOP */
function _showEvoBeforeAfter({ beforeImgSrc, afterImgSrc, beforeStage, afterStage,
                                chosenAbility, chosenBoost, result, zone, charName, progId }) {
    const stageLabel = s => ({ baby:'Baby', mid_a:'Mid A', mid_b:'Mid B',
                                final_a:'Final A', final_b:'Final B' }[s] || s);

    const overlay = document.createElement('div');
    overlay.id = 'iem-ba-overlay';
    overlay.className = 'iem-ba-overlay';

    const box = document.createElement('div');
    box.className = 'iem-ba-box';

    // Title
    const title = document.createElement('div');
    title.className = 'iem-ba-title';
    title.textContent = 'Look at the change!';
    box.appendChild(title);

    // Cards row
    const cards = document.createElement('div');
    cards.className = 'iem-ba-cards';

    // Before card
    const cBefore = document.createElement('div');
    cBefore.className = 'iem-ba-card iem-ba-card--before';
    cBefore.appendChild(_baImg(beforeImgSrc, 'iem-ba-img-wrap--before'));
    const stBefore = document.createElement('div');
    stBefore.className = 'iem-ba-stage';
    stBefore.textContent = stageLabel(beforeStage);
    cBefore.appendChild(stBefore);
    cards.appendChild(cBefore);

    // Arrow
    const arrow = document.createElement('div');
    arrow.className = 'iem-ba-arrow';
    arrow.innerHTML = '<i data-lucide="arrow-right"></i>';
    cards.appendChild(arrow);

    // After card
    const cAfter = document.createElement('div');
    cAfter.className = 'iem-ba-card iem-ba-card--after';
    cAfter.appendChild(_baImg(afterImgSrc));
    const stAfter = document.createElement('div');
    stAfter.className = 'iem-ba-stage';
    stAfter.textContent = stageLabel(afterStage);
    cAfter.appendChild(stAfter);
    if (chosenAbility) {
        const ab = document.createElement('div');
        ab.className = 'iem-ba-ability';
        ab.textContent = chosenAbility;
        cAfter.appendChild(ab);
    }
    cards.appendChild(cAfter);

    box.appendChild(cards);

    // Boost line (if available)
    if (chosenBoost) {
        const bl = document.createElement('div');
        bl.className = 'iem-ba-tap-hint';
        bl.style.fontWeight = '700';
        bl.style.color = 'var(--rewards-ink)';
        bl.textContent = chosenBoost;
        box.appendChild(bl);
    }

    // Continue button
    const continueBtn = document.createElement('button');
    continueBtn.className = 'iem-ba-continue-btn';
    continueBtn.innerHTML = '<i data-lucide="sparkles"></i> See the celebration!';
    continueBtn.onclick = () => {
        overlay.remove();
        // Step 3: existing celebration
        if (result.is_completed) {
            _showCharCompletion(result, zone, charName);
        } else {
            _showMidEvoReveal(result, zone, charName, progId);
        }
    };
    box.appendChild(continueBtn);

    overlay.appendChild(box);
    document.body.appendChild(overlay);

    if (typeof lucide !== 'undefined') lucide.createIcons();
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
    _refreshIslandHomeUI(zone);
    // Set _zdZone so that CharacterDetail's Back button returns to ZoneDetail
    // instead of dropping the user at the island map root.
    _zdZone = zone;
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
    _iccZone = zone;
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
    _refreshIslandHomeUI(_iccZone);
    _iccZone = null;
    // Reload island map so boost/lumi production is reflected.
    if (typeof openIslandMain === 'function') openIslandMain();
}

// ─── Home UI Refresh After Evolution ─────────────────────────

/**
 * Refresh the home board island card and the subject-view mini widget
 * for the evolved zone so they reflect the new character stage immediately.
 * @tag SHOP
 */
function _refreshIslandHomeUI(zone) {
    // Refresh home board island card.
    if (typeof _loadIslandCard === 'function') _loadIslandCard();

    // Refresh the subject-view mini widget for the evolved zone.
    const zoneWidgetMap = {
        forest:  { id: 'island-widget-english', zone: 'forest'  },
        ocean:   { id: 'island-widget-math',    zone: 'ocean'   },
        savanna: { id: 'island-widget-diary',   zone: 'savanna' },
        space:   null, // no subject widget for space/review zone yet — skip silently
    };
    const entry = zone ? zoneWidgetMap[zone] : null;
    if (entry && typeof _renderIslandSubjectWidget === 'function') {
        _renderIslandSubjectWidget(entry.id, entry.zone);
    }
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
