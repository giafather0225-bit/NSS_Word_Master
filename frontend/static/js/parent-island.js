/* ================================================================
   parent-island.js — Parent Dashboard: Island monitoring tab
   Section: Parent
   Dependencies: parent-panel.js (_ppFetch, _ppEmpty, escapeHtml)
   API endpoints:
     GET /api/island/status
     GET /api/island/lumi/log?limit=12
   ================================================================ */

/**
 * Render the Island monitoring tab.
 * Shows: Lumi balance, zone unlock status, per-character gauges + level,
 * and the last 12 Lumi transactions.
 * @tag PARENT ISLAND
 */
async function _ppIsland(body) {
    try {
        const [status, logData] = await Promise.all([
            window._ppFetch("/api/island/status").then(r => r.json()),
            window._ppFetch("/api/island/lumi/log?limit=12").then(r => r.json()),
        ]);

        const currency = status.currency || {};
        const lumi     = currency.lumi      ?? 0;
        const legend   = currency.legend_lumi ?? 0;
        const earned   = currency.total_earned ?? 0;
        const chars    = status.active_characters || [];
        const zones    = status.zones || [];
        const log      = logData.log || [];

        const islandOn = status.island_on;

        if (!islandOn) {
            body.innerHTML = _ppEmpty("island", "Island is Disabled",
                "Enable Island in Settings to start raising characters.");
            if (typeof lucide !== "undefined") lucide.createIcons();
            return;
        }

        // ── Currency bar ──────────────────────────────────────────
        const currencyHtml = `
            <div class="pp-island-currency-bar">
                <div class="pp-island-currency-item">
                    <i data-lucide="gem"></i>
                    <span class="pp-island-currency-label">Lumi</span>
                    <span class="pp-island-currency-val">${lumi.toLocaleString()}</span>
                </div>
                <div class="pp-island-currency-item">
                    <i data-lucide="sparkles"></i>
                    <span class="pp-island-currency-label">Legend Lumi</span>
                    <span class="pp-island-currency-val">${legend.toLocaleString()}</span>
                </div>
                <div class="pp-island-currency-item pp-island-currency-item--muted">
                    <i data-lucide="trending-up"></i>
                    <span class="pp-island-currency-label">Total Earned</span>
                    <span class="pp-island-currency-val">${earned.toLocaleString()}</span>
                </div>
            </div>`;

        // ── Zone status pills ─────────────────────────────────────
        const ZONE_ICONS = { forest:"trees", ocean:"waves", savanna:"sun", space:"rocket", legend:"star" };
        const zonePills = zones.map(z => {
            const icon   = ZONE_ICONS[z.zone] || "map-pin";
            const locked = !z.is_unlocked;
            return `<div class="pp-island-zone-pill${locked ? " pp-island-zone-pill--locked" : ""}">
                <i data-lucide="${icon}"></i>
                <span>${z.zone.charAt(0).toUpperCase() + z.zone.slice(1)}</span>
                ${locked ? `<i data-lucide="lock" class="pp-island-zone-lock"></i>` : ""}
            </div>`;
        }).join("");

        const zonesHtml = `
            <div class="pp-section-title">
                <i data-lucide="map" class="pp-section-title--icon"></i> Zones
            </div>
            <div class="pp-island-zones">${zonePills}</div>`;

        // ── Character cards ───────────────────────────────────────
        const STAGE_ORDER = ["baby", "mid_a", "mid_b", "final_a", "final_b"];
        const SUBJECT_COLOR = {
            english: "var(--english-primary)",
            math:    "var(--math-primary)",
            diary:   "var(--diary-primary)",
            review:  "var(--review-primary)",
        };

        const charCards = chars.map(c => {
            const hunger    = c.hunger    ?? 0;
            const happiness = c.happiness ?? 0;
            const level     = c.level     ?? 1;
            const stage     = c.stage     || "baby";
            const isDone    = c.is_completed;
            const evolveRdy = c.ready_to_evolve;

            const hColor  = hunger    < 20 ? "var(--color-error)"   : hunger    < 60 ? "var(--arcade-primary)" : "var(--math-primary)";
            const hpColor = happiness < 20 ? "var(--color-error)"   : happiness < 60 ? "var(--arcade-primary)" : "var(--math-primary)";
            const subjectColor = SUBJECT_COLOR[c.subject] || "var(--text-hint)";

            // Parse image URL for current stage
            let imgSrc = "";
            try {
                const imgs = JSON.parse(c.images || "{}");
                imgSrc = imgs[stage] ? `/static/img/island/${imgs[stage]}` : "";
            } catch (_) {}

            const imgHtml = imgSrc
                ? `<img class="pp-island-char-portrait" src="${imgSrc}" alt="${escapeHtml(c.name)}" loading="lazy">`
                : `<div class="pp-island-char-portrait pp-island-char-portrait--placeholder"><i data-lucide="image-off"></i></div>`;

            const stagePct  = (STAGE_ORDER.indexOf(stage) / (STAGE_ORDER.length - 1)) * 100;

            const badges = [];
            if (isDone)    badges.push(`<span class="pp-island-badge pp-island-badge--done">Completed</span>`);
            if (evolveRdy) badges.push(`<span class="pp-island-badge pp-island-badge--evolve">Ready to Evolve</span>`);
            if (c.boost_active) badges.push(`<span class="pp-island-badge pp-island-badge--boost">Boost Active</span>`);

            return `
            <div class="pp-island-char-card${isDone ? " pp-island-char-card--done" : ""}">
                <div class="pp-island-char-portrait-wrap">
                    ${imgHtml}
                    <div class="pp-island-char-level" style="background:${subjectColor}">Lv.${level}</div>
                </div>
                <div class="pp-island-char-info">
                    <div class="pp-island-char-header">
                        <span class="pp-island-char-name">${escapeHtml(c.nickname || c.name)}</span>
                        <span class="pp-island-char-zone-tag" style="color:${subjectColor}">${escapeHtml(c.zone)}</span>
                    </div>
                    <div class="pp-island-char-stage">${stage}</div>
                    ${badges.length ? `<div class="pp-island-char-badges">${badges.join("")}</div>` : ""}
                    ${isDone ? "" : `
                    <div class="pp-island-gauges">
                        <div class="pp-island-gauge-row">
                            <i data-lucide="utensils"></i>
                            <div class="pp-island-gauge-track">
                                <div class="pp-island-gauge-fill" style="width:${hunger}%;background:${hColor}"></div>
                            </div>
                            <span class="pp-island-gauge-num">${hunger}</span>
                        </div>
                        <div class="pp-island-gauge-row">
                            <i data-lucide="smile"></i>
                            <div class="pp-island-gauge-track">
                                <div class="pp-island-gauge-fill" style="width:${happiness}%;background:${hpColor}"></div>
                            </div>
                            <span class="pp-island-gauge-num">${happiness}</span>
                        </div>
                    </div>`}
                </div>
            </div>`;
        }).join("");

        const charsHtml = chars.length
            ? `<div class="pp-island-char-grid">${charCards}</div>`
            : _ppEmpty("users", "No Active Characters", "Adopt a character from the Island shop to start raising.");

        // ── Lumi log ──────────────────────────────────────────────
        const logRows = log.map(entry => {
            const amount  = entry.amount ?? 0;
            const sign    = amount >= 0 ? "+" : "";
            const color   = amount >= 0 ? "var(--math-ink)" : "var(--review-ink)";
            const when    = entry.created_at
                ? new Date(entry.created_at).toLocaleDateString("en-US", { month:"short", day:"numeric", hour:"2-digit", minute:"2-digit" })
                : "";
            return `<div class="pp-island-log-row">
                <span class="pp-island-log-source">${escapeHtml(entry.source || entry.action || "")}</span>
                <span class="pp-island-log-amount" style="color:${color}">${sign}${amount}</span>
                <span class="pp-island-log-when">${when}</span>
            </div>`;
        }).join("");

        const logHtml = log.length
            ? `<div class="pp-island-log">${logRows}</div>`
            : `<p style="color:var(--text-hint);font-size:13px;padding:8px 0">No Lumi transactions yet.</p>`;

        // ── Assemble ──────────────────────────────────────────────
        body.innerHTML = `
            <div class="pp-island-tab">
                ${currencyHtml}
                ${zonesHtml}
                <div class="pp-grid-2" style="margin-top:24px;gap:24px">
                    <div>
                        <div class="pp-section-title">
                            <i data-lucide="users" class="pp-section-title--icon"></i> Characters
                            <span class="pp-island-completed-badge">${status.completed_count ?? 0} completed</span>
                        </div>
                        ${charsHtml}
                    </div>
                    <div>
                        <div class="pp-section-title">
                            <i data-lucide="activity" class="pp-section-title--icon"></i> Recent Lumi Activity
                        </div>
                        <div class="pp-island-log-header">
                            <span>Source</span><span>Amount</span><span>When</span>
                        </div>
                        ${logHtml}
                    </div>
                </div>
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (e) {
        console.error("[ppIsland]", e);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Could not load Island data.</p>`;
    }
}
