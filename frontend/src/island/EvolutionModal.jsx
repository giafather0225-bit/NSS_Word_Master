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
            <div class="isl-loading-ship">⛵</div>
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

/** @tag SHOP */
function _emRenderModal(el, d) {
    const nameHtml = escapeHtml(_emCharName || 'Character');
    const stoneA   = escapeHtml(d.branch_a?.stone || 'Stone A');
    const stoneB   = escapeHtml(d.branch_b?.stone || 'Stone B');
    const descA    = escapeHtml(d.branch_a?.description || 'Path A — takes a new form.');
    const descB    = escapeHtml(d.branch_b?.description || 'Path B — takes a new form.');
    const targetA  = escapeHtml(d.branch_a?.target_stage || 'mid_a');
    const targetB  = escapeHtml(d.branch_b?.target_stage || 'mid_b');

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

    try {
        await apiFetchJSON('/api/island/character/evolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character_progress_id: _emProgId,
                branch: _emSelection,
            }),
        });
        _showShopToast('Evolution complete!');
        _closeEvoModal();
        // Refresh whichever screen called us
        if (_cdProgId) {
            openCharacterDetail(_cdProgId, _cdZone);
        } else if (_zdZone) {
            openZoneDetail(_zdZone);
        }
    } catch (err) {
        if (btn) { btn.disabled = false; btn.textContent = 'Confirm Evolution'; }
        _showShopToast(err?.detail || 'Evolution failed.', true);
    }
}
