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
                <div class="theme-placeholder" style="text-align:center;padding:12px;cursor:pointer" onclick="gtOpenSelector()">
                    <div style="font-size:32px;margin-bottom:6px">🌱</div>
                    <div style="font-size:13px;font-weight:600;color:var(--text-primary)">Choose a Theme</div>
                    <div style="font-size:12px;color:var(--text-secondary);margin-top:2px">Tap to start growing!</div>
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
            <div onclick="gtOpenSelector()" style="cursor:pointer;text-align:center">
                <img src="${t.img_url}" alt="${t.theme} step ${t.current_step}"
                     style="width:100%;max-width:160px;height:auto;border-radius:var(--radius-md);"
                     onerror="this.style.display='none'">
            </div>`;

        // Update sidebar theme info
        _gtUpdateSidebarInfo(t, pct, nextXp, totalXp);

    } catch (_) {
        const display2 = document.getElementById("growth-theme-display");
        if (display2) display2.innerHTML = `<div class="theme-placeholder" style="padding:12px;text-align:center;color:var(--text-secondary)">🌱</div>`;
    }
}

/** Update the growth theme info in the home dashboard widget. @tag GROWTH_THEME */
function _gtUpdateSidebarInfo(t, pct, nextXp, totalXp) {
    const stepEl  = document.querySelector(".growth-theme-step");
    const barEl   = document.querySelector(".growth-theme-bar");
    const titleEl = document.querySelector(".growth-theme-title");
    const hintEl  = document.querySelector(".growth-theme-hint");

    if (titleEl) titleEl.textContent = GT_LABELS[t.theme] || t.theme;
    if (stepEl)  stepEl.textContent  = `Step ${t.current_step} / 5`;
    if (barEl)   barEl.style.width   = `${pct}%`;
    if (hintEl) {
        if (t.is_completed) {
            hintEl.textContent = "✓ Theme complete! Choose next in My Worlds.";
        } else if (nextXp) {
            hintEl.textContent = `${nextXp - totalXp} XP until Step ${t.current_step + 1}`;
        }
    }
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
        const done = info.is_completed ? "✅" : "";
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
    s.textContent = `.gt-sel-card{display:flex;flex-direction:column;align-items:center;cursor:pointer;padding:8px;border-radius:var(--radius-md);transition:background .15s}.gt-sel-card:hover{background:var(--color-primary-light)}`;
    document.head.appendChild(s);
})();
