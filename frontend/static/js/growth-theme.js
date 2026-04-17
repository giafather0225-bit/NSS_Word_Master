/* ================================================================
   growth-theme.js — Growth Theme display, selection, XP advancement
   Section: Growth Theme
   Dependencies: core.js, home.js (renderSummaryBar)
   API endpoints: /api/growth/theme, /api/growth/theme/select,
                  /api/growth/theme/advance, /api/growth/theme/all
   ================================================================ */

// ─── Constants ────────────────────────────────────────────────
const GT_THEMES = ["space", "tree", "city", "animal", "ocean"];
const GT_LABELS = {
    space:  "Space Explorer",
    tree:   "Growing Tree",
    city:   "My City",
    animal: "Animal Kingdom",
    ocean:  "Ocean World",
};
const GT_XP = [0, 100, 300, 600, 1000, 1500]; // XP to reach each step

// ─── Home Dashboard Widget ────────────────────────────────────

/**
 * Fetch active theme and render the home dashboard growth widget.
 * Replaces the Phase 8 stub in home.js.
 * @tag GROWTH_THEME HOME_DASHBOARD
 */
async function gtRenderTheme() {
    const display = document.getElementById("growth-theme-display");
    if (!display) return;

    try {
        const res  = await fetch("/api/growth/theme");
        const data = await res.json();

        if (!data.active) {
            display.innerHTML = `
                <div class="theme-placeholder gt-empty" onclick="event.stopPropagation(); gtOpenSelector()">
                    <div>🌱</div>
                    <div class="gt-empty-title">Choose a Theme</div>
                    <div class="gt-empty-sub">Tap to start growing!</div>
                </div>`;
            return;
        }

        const t = data.active;
        const totalXp = data.total_xp || 0;
        const nextXp  = GT_XP[t.current_step + 1] ?? null;
        const pct     = nextXp ? Math.min(100, Math.round(((totalXp - GT_XP[t.current_step]) / (nextXp - GT_XP[t.current_step])) * 100)) : 100;

        // Check for auto-advance
        if (t.current_step < 5) {
            const targetStep = GT_XP.reduce((acc, xp, i) => totalXp >= xp ? i : acc, 0);
            if (targetStep > t.current_step) await gtAdvance();
        }

        display.innerHTML = `
            <img src="${t.img_url}" alt="${t.theme} step ${t.current_step}"
                 onerror="this.style.display='none'">`;

        // Cache for detail modal
        window._gtState = { t, pct, nextXp, totalXp };

    } catch (_) {
        const display2 = document.getElementById("growth-theme-display");
        if (display2) display2.innerHTML = `<div class="theme-placeholder" style="padding:12px;text-align:center;color:var(--text-secondary)">🌱</div>`;
    }
}

/**
 * Open the current theme detail modal.
 * @tag GROWTH_THEME
 */
async function gtOpenThemeDetail() {
    document.getElementById("gt-detail-modal-bg")?.remove();

    let state = window._gtState;
    if (!state) {
        try {
            const res  = await fetch("/api/growth/theme");
            const data = await res.json();
            if (!data.active) { gtOpenSelector(); return; }
            const t = data.active;
            const totalXp = data.total_xp || 0;
            const nextXp  = GT_XP[t.current_step + 1] ?? null;
            const pct     = nextXp ? Math.min(100, Math.round(((totalXp - GT_XP[t.current_step]) / (nextXp - GT_XP[t.current_step])) * 100)) : 100;
            state = { t, pct, nextXp, totalXp };
        } catch (_) { gtOpenSelector(); return; }
    }

    const { t, pct, nextXp, totalXp } = state;
    const label = GT_LABELS[t.theme] || t.theme;
    const stepXpNeed = nextXp ? (nextXp - totalXp) : 0;
    const hintText = t.is_completed
        ? "✓ Theme complete!"
        : (nextXp ? `${stepXpNeed} XP until Step ${t.current_step + 1}` : "Max step reached");

    const bg = document.createElement("div");
    bg.id = "gt-detail-modal-bg";
    bg.className = "gt-detail-bg";
    bg.onclick = (e) => { if (e.target === bg) bg.remove(); };
    bg.innerHTML = `
        <div class="gt-detail-modal">
            <button class="gt-detail-close" onclick="document.getElementById('gt-detail-modal-bg').remove()">✕</button>
            <img src="${t.img_url}" alt="${label}" class="gt-detail-img" onerror="this.style.display='none'">
            <div class="gt-detail-title">${label}</div>
            <div class="gt-detail-sub">Growth Theme · Step ${t.current_step} / 5</div>
            <div class="gt-detail-progress"><div class="gt-detail-progress-fill" style="width:${pct}%"></div></div>
            <div class="gt-detail-hint">${hintText}</div>
            <div class="gt-detail-grid">
                <div class="gt-detail-stat">
                    <div class="gt-detail-stat-label">Current Step</div>
                    <div class="gt-detail-stat-value">${t.current_step} / 5</div>
                </div>
                <div class="gt-detail-stat">
                    <div class="gt-detail-stat-label">XP Needed</div>
                    <div class="gt-detail-stat-value">${stepXpNeed}</div>
                </div>
                <div class="gt-detail-stat">
                    <div class="gt-detail-stat-label">Total XP</div>
                    <div class="gt-detail-stat-value">${totalXp}</div>
                </div>
                <div class="gt-detail-stat">
                    <div class="gt-detail-stat-label">Next Theme</div>
                    <div class="gt-detail-stat-value">Soon</div>
                </div>
            </div>
        </div>`;
    document.body.appendChild(bg);
}

// ─── Advance ──────────────────────────────────────────────────

/**
 * POST /api/growth/theme/advance and refresh widget.
 * @tag GROWTH_THEME XP
 */
async function gtAdvance() {
    try {
        const res = await fetch("/api/growth/theme/advance", { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            if (data.advanced && data.advanced.length > 0) {
                data.advanced.forEach(step => {
                    const msg = step === 5 ? "✓ Theme Complete!" : `✦ Step ${step} Unlocked!`;
                    if (typeof _showXPToast === "function") _showXPToast(msg);
                });
            }
            if (typeof renderSummaryBar === "function") renderSummaryBar();
        }
    } catch (_) {}
}

// ─── Theme Selector ───────────────────────────────────────────

/**
 * Open the theme selector modal.
 * @tag GROWTH_THEME
 */
async function gtOpenSelector() {
    // Remove existing modal
    document.getElementById("gt-modal-bg")?.remove();

    let themeData = [];
    try {
        const res  = await fetch("/api/growth/theme/all");
        const data = await res.json();
        themeData = data.themes || [];
    } catch (_) {}

    const cards = GT_THEMES.map(key => {
        const info = themeData.find(t => t.theme === key) || {};
        const step = info.current_step || 0;
        const done = info.is_completed ? "✓" : "";
        return `<div class="gt-sel-card" onclick="gtSelectTheme('${key}')">
            <img src="/static/img/themes/${key}/step_${step}_v1.svg"
                 style="width:80px;height:80px;border-radius:var(--radius-md);object-fit:cover"
                 onerror="this.style.opacity='0.3'">
            <div style="font-size:12px;font-weight:600;color:var(--text-primary);margin-top:6px;text-align:center">
                ${GT_LABELS[key]} ${done}
            </div>
            <div style="font-size:11px;color:var(--text-secondary)">Step ${step}/5</div>
        </div>`;
    }).join("");

    const bg = document.createElement("div");
    bg.id = "gt-modal-bg";
    bg.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:800;display:flex;align-items:center;justify-content:center";
    bg.innerHTML = `
        <div style="background:var(--bg-card);border-radius:var(--radius-lg);padding:24px;width:340px;box-shadow:0 8px 32px rgba(0,0,0,0.15)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
                <span style="font-size:16px;font-weight:700;color:var(--text-primary)">Choose a Theme</span>
                <button onclick="document.getElementById('gt-modal-bg').remove()"
                        style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text-secondary)">✕</button>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px">${cards}</div>
            <p style="font-size:11px;color:var(--text-secondary);margin-top:12px;text-align:center">Select a theme to grow with your XP!</p>
        </div>`;
    document.body.appendChild(bg);
}

/**
 * POST /api/growth/theme/select and refresh.
 * @tag GROWTH_THEME
 */
async function gtSelectTheme(theme) {
    document.getElementById("gt-modal-bg")?.remove();
    try {
        await fetch("/api/growth/theme/select", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme, variation: 1 }),
        });
        await gtAdvance();   // apply any pending XP steps immediately
        await gtRenderTheme();
    } catch (_) {}
}

// CSS for selector cards (injected once)
(function _gtInjectStyles() {
    if (document.getElementById("gt-styles")) return;
    const s = document.createElement("style");
    s.id = "gt-styles";
    s.textContent = `
.gt-sel-card{display:flex;flex-direction:column;align-items:center;cursor:pointer;padding:8px;border-radius:var(--radius-md);transition:background .15s}
.gt-sel-card:hover{background:var(--color-primary-light)}
.gt-empty{cursor:pointer;padding:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px}
.gt-empty-title{font-size:14px;font-weight:600;color:var(--text-primary)}
.gt-empty-sub{font-size:12px;color:var(--text-secondary)}
.gt-detail-bg{position:fixed;inset:0;background:var(--overlay-scrim);z-index:800;display:flex;align-items:center;justify-content:center}
.gt-detail-modal{background:var(--bg-card);border:0.5px solid var(--border-card);border-radius:var(--radius-lg);padding:24px;max-width:360px;width:calc(100% - 32px);position:relative}
.gt-detail-close{position:absolute;top:12px;right:12px;background:none;border:none;font-size:20px;color:var(--text-hint);cursor:pointer;line-height:1}
.gt-detail-img{width:100%;max-height:200px;object-fit:cover;border-radius:var(--radius-md);margin-bottom:12px;background:var(--color-secondary-light);display:block}
.gt-detail-title{font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:2px}
.gt-detail-sub{font-size:12px;color:var(--text-secondary);margin-bottom:12px}
.gt-detail-progress{height:var(--progress-height);background:var(--bg-surface);border-radius:var(--radius-full);overflow:hidden;margin-bottom:6px}
.gt-detail-progress-fill{height:100%;background:var(--color-accent);border-radius:var(--radius-full);transition:width 0.6s var(--ease-calm-out)}
.gt-detail-hint{font-size:12px;color:var(--color-primary);font-weight:500;margin-bottom:14px}
.gt-detail-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}
.gt-detail-stat{background:var(--color-secondary-light);border-radius:10px;padding:12px}
.gt-detail-stat-label{font-size:10px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px}
.gt-detail-stat-value{font-size:16px;font-weight:700;color:var(--text-primary)}
`;
    document.head.appendChild(s);
})();
