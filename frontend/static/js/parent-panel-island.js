/* ================================================================
   parent-panel-island.js — Parent Dashboard: Island tab (Variant C)
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/island/status, /api/island/lumi/log,
                  /api/shop/items, /api/shop/my-rewards
   ================================================================ */

/** Island tab entry. @tag PARENT ISLAND */
async function _ppIsland(body) {
    try {
        const _safe = (p, fb) => p.catch(() => fb);
        const [status, lumiLog, shopItems, myRewards] = await Promise.all([
            _safe(window._ppFetch("/api/island/status").then(r => r.json()),       {}),
            _safe(window._ppFetch("/api/island/lumi/log?limit=12").then(r => r.json()), { log: [] }),
            _safe(apiFetchJSON("/api/shop/items"),                                  []),
            _safe(window._ppFetch("/api/shop/my-rewards").then(r => r.json()),     { rewards: [] }),
        ]);

        const items = Array.isArray(shopItems) ? shopItems : (shopItems.items || []);
        const rewards = myRewards.rewards || [];

        body.innerHTML = `
            <div class="pp-island-grid pp-island-grid--top">
                ${_ppIslandCollectionCard(status)}
                ${_ppIslandLumiCard(status, lumiLog.log || [])}
            </div>
            <div class="pp-island-grid pp-island-grid--bot">
                ${_ppIslandShopCard(items)}
                ${_ppIslandPurchasesCard(rewards)}
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-island] load failed:", err);
        body.innerHTML = `<p class="pp-error-pad">Failed to load Island.</p>`;
    }
}

/** Collection card: Ring + character count + zone stack bar. @tag PARENT ISLAND */
function _ppIslandCollectionCard(status) {
    const completed = status.completed_characters || [];
    const active = status.active_characters || [];
    const owned = (status.completed_count != null) ? status.completed_count : completed.length;
    const total = 24;
    const pct = Math.round((owned / total) * 100);

    const all = completed.concat(active);
    const byZone = { forest: 0, ocean: 0, savanna: 0, space: 0, legend: 0 };
    all.forEach(c => {
        const z = (c.zone || "forest").toLowerCase();
        if (byZone[z] != null) byZone[z] += 1;
    });
    const legendChar = completed.find(c => (c.zone || "").toLowerCase() === "legend");
    const legendName = legendChar ? (legendChar.name || legendChar.character_id) : "—";

    const segs = [
        { key: "english", v: byZone.forest,  label: "Forest"  },
        { key: "math",    v: byZone.ocean,   label: "Ocean"   },
        { key: "diary",   v: byZone.savanna, label: "Savanna" },
        { key: "rewards", v: byZone.space,   label: "Space"   },
        { key: "legend",  v: byZone.legend,  label: "Legend", color: "var(--legend-primary)" },
    ];
    const segSum = segs.reduce((a, s) => a + s.v, 0);

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Collection</div>
            </div>
            <div class="pp-island-coll-flex">
                ${_ppRing(owned, total, { size: 70, stroke: 8, color: "var(--legend-primary)", label: `${pct}%`, sub: "collected" })}
                <div class="pp-island-coll-right">
                    <div class="mono pp-island-coll-big">${owned}<span class="pp-island-coll-big-sub">/${total}</span></div>
                    <div class="pp-island-coll-meta">Legendary <b class="pp-island-coll-legend">"${escapeHtml(legendName)}"</b> ${legendChar ? "owned" : "not yet"}</div>
                    <div class="pp-island-coll-stack">
                        ${segSum > 0 ? _ppStackBar(segs, { height: 6 }) : `<div style="height:6px;background:var(--line);border-radius:999px"></div>`}
                        <div class="pp-island-coll-legend-row">
                            ${segs.map(s => `<span>${s.label.slice(0, 1) === "S" && s.label === "Space" ? "Sp" : s.label.slice(0,1)} ${s.v}</span>`).join("")}
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
}

/** Lumi + recent transactions + pending reward requests card. @tag PARENT ISLAND */
function _ppIslandLumiCard(status, lumiLog) {
    const lumi = status.currency?.lumi || 0;
    const legendLumi = status.currency?.legend_lumi || 0;
    const todayLumi = lumiLog.filter(l => (l.created_at || "").startsWith(new Date().toISOString().slice(0, 10)))
                              .filter(l => l.action === "earn")
                              .reduce((a, l) => a + (l.amount || 0), 0);

    const recent = lumiLog.slice(0, 1)[0];
    const recentHtml = recent ? `
        <div class="pp-island-recent">
            <div class="pp-mini-kick">Recent transaction</div>
            <div class="pp-island-recent-row">
                <span class="pp-island-recent-name">${escapeHtml(recent.source || "—")}</span>
                <span class="mono pp-island-recent-amt ${recent.action === "earn" ? "is-earn" : "is-spend"}">
                    ${recent.action === "earn" ? "+" : "−"}${recent.amount} Lumi
                </span>
                <span class="mono pp-island-recent-when">${escapeHtml((recent.created_at || "").slice(5, 16).replace("T", " "))}</span>
            </div>
        </div>` : "";

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Lumi &amp; Recent</div>
            </div>
            <div class="pp-island-lumi-flex">
                <div>
                    <div class="mono pp-island-lumi-big">${lumi.toLocaleString()} <span class="pp-island-lumi-big-sub">Lumi</span></div>
                    <div class="pp-island-lumi-meta">
                        Today <span class="mono pp-island-lumi-strong">+${todayLumi}</span> ·
                        Legend <span class="mono pp-island-lumi-strong">${legendLumi}</span>
                    </div>
                </div>
                ${recentHtml}
            </div>
            <div class="pp-island-log">
                <div class="pp-mini-kick">Last 8 transactions</div>
                <div class="pp-island-log-rows">
                    ${lumiLog.slice(0, 8).map(l => `
                        <div class="pp-island-log-row">
                            <span class="pp-island-log-source">${escapeHtml(l.source || "—")}</span>
                            <span class="mono pp-island-log-amt ${l.action === "earn" ? "is-earn" : "is-spend"}">
                                ${l.action === "earn" ? "+" : "−"}${l.amount}
                            </span>
                            <span class="mono pp-island-log-balance">→ ${l.balance_after}</span>
                            <span class="mono pp-island-log-when">${escapeHtml((l.created_at || "").slice(5, 10))}</span>
                        </div>`).join("") || `<p class="pp-text-hint">No transactions yet.</p>`}
                </div>
            </div>
        </div>`;
}

/** Reward Shop catalog 3-col grid. @tag PARENT SHOP */
function _ppIslandShopCard(items) {
    const KIND_COLOR = {
        real:      "var(--english-primary)",
        digital:   "var(--diary-primary)",
        privilege: "var(--rewards-primary)",
        custom:    "var(--math-primary)",
    };

    const active = items.filter(i => i.is_active !== false);
    const cards = active.slice(0, 9).map(item => {
        const cat = (item.category || "real").toLowerCase();
        const color = KIND_COLOR[cat] || "var(--ink-3)";
        return `
            <div class="pp-shop-card">
                <div class="pp-shop-cat">
                    <span class="pp-shop-cat-dot" style="background:${color}"></span>
                    <span class="pp-shop-cat-label">${escapeHtml(cat)}</span>
                </div>
                <div class="pp-shop-name">${escapeHtml(item.name || "")}</div>
                <div class="pp-shop-foot">
                    <span class="mono pp-shop-price">${item.final_price || item.price || 0} <span class="pp-shop-price-sub">XP</span></span>
                    ${item.discount_pct ? `<span class="mono pp-shop-discount">−${item.discount_pct}%</span>` : ""}
                </div>
            </div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Reward Shop · catalog
                    <span class="pp-panel-sub">${active.length} active items</span>
                </div>
                <button class="pp-btn primary pp-btn--sm" onclick="_ppLoadTab('settings')">
                    <i data-lucide="plus"></i>Manage
                </button>
            </div>
            <div class="pp-shop-grid">${cards || `<p class="pp-text-hint">No shop items.</p>`}</div>
        </div>`;
}

/** Recent purchases. @tag PARENT SHOP */
function _ppIslandPurchasesCard(rewards) {
    const sorted = rewards.slice().sort((a, b) => (b.purchased_at || "").localeCompare(a.purchased_at || ""));
    const rows = sorted.slice(0, 8).map(r => `
        <div class="pp-purchase-row ${r.is_used ? "is-used" : ""}">
            <i data-lucide="gift" class="pp-purchase-icon"></i>
            <div class="pp-purchase-body">
                <div class="pp-purchase-name">${escapeHtml(r.name || r.item_name || "—")}</div>
                <div class="mono pp-purchase-meta">${r.cost || r.price || 0} XP · ${escapeHtml((r.purchased_at || "").slice(0, 10))}</div>
            </div>
            <span class="pp-purchase-status ${r.is_used ? "is-used" : "is-unused"}">
                ${r.is_used ? "Used" : "Unused"}
            </span>
        </div>`).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Recent purchases</div>
            </div>
            <div class="pp-purchase-list">${rows || `<p class="pp-text-hint">No purchases yet.</p>`}</div>
        </div>`;
}

window._ppIsland = _ppIsland;
