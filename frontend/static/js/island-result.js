/* ================================================================
   island-result.js — Island update card appended to study result screens.
   Section: Shop (Island)
   Dependencies: core.js (apiFetchJSON, escapeHtml)
   API endpoints: GET /api/island/notifications
   ================================================================ */

// ─── Shared helper ───────────────────────────────────────────────

/**
 * Fetch pending island update and append a compact card to containerEl.
 * Called after study stage / review / math / diary completion.
 * No-op if island is off, no char is active, or fetch fails.
 * @tag SHOP
 * @param {HTMLElement} containerEl  — element to append card into
 */
async function _appendIslandUpdate(containerEl) {
    if (!containerEl) return;
    try {
        const d = await apiFetchJSON('/api/island/notifications');
        if (!d) return;

        const lumiEarned = d.lumi_earned  ?? 0;
        const xpGained   = d.xp_gained   ?? 0;
        const charName   = d.char_name   ?? '';
        const levelUp    = d.level_up    ?? false;
        const evolved    = d.evolved     ?? false;
        const hunger     = d.hunger      ?? null;
        const happiness  = d.happiness   ?? null;

        const hasUpdate  = lumiEarned > 0 || xpGained > 0 || levelUp || evolved;
        if (!hasUpdate && !charName) return;

        const card = document.createElement('div');
        card.className = 'ir-card';
        card.innerHTML = `
            <div class="ir-header">
                <i data-lucide="gem" class="ir-gem-icon"></i>
                <span class="ir-title">Island Update</span>
                ${charName ? `<span class="ir-char">${escapeHtml(charName)}</span>` : ''}
            </div>
            <div class="ir-rows">
                ${xpGained   > 0    ? `<div class="ir-row"><i data-lucide="zap"></i><span>+${xpGained} XP earned</span></div>` : ''}
                ${lumiEarned > 0    ? `<div class="ir-row"><i data-lucide="gem"></i><span>+${lumiEarned} Lumi earned</span></div>` : ''}
                ${hunger !== null   ? `<div class="ir-row ir-row--gauge"><i data-lucide="apple"></i><span>Hunger ${hunger}%</span>${_irGaugeBar(hunger)}</div>` : ''}
                ${happiness !== null? `<div class="ir-row ir-row--gauge"><i data-lucide="heart"></i><span>Mood ${happiness}%</span>${_irGaugeBar(happiness)}</div>` : ''}
                ${levelUp           ? `<div class="ir-row ir-row--event"><i data-lucide="trending-up"></i><span>Level Up!</span></div>` : ''}
                ${evolved           ? `<div class="ir-row ir-row--event"><i data-lucide="sparkles"></i><span>Evolved!</span></div>` : ''}
            </div>`;
        containerEl.appendChild(card);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    } catch (_) { /* silent — island update is non-critical */ }
}

/** @tag SHOP */
function _irGaugeBar(pct) {
    const cls = pct < 20 ? 'ir-bar-fill--low' : pct < 60 ? 'ir-bar-fill--mid' : 'ir-bar-fill--ok';
    return `<div class="ir-bar"><div class="ir-bar-fill ${cls}" style="width:${Math.max(0,Math.min(100,pct))}%"></div></div>`;
}
