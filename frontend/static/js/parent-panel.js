/* ================================================================
   parent-panel.js — In-app Parent Dashboard overlay shell
   Section: Parent
   Dependencies: core.js
   API endpoints: /api/parent/verify-pin, /api/parent/day-off-requests,
                  /api/xp/summary
   ================================================================ */

// ─── PIN closure ──────────────────────────────────────────────
// Keeps the verified PIN off window so it isn't trivially readable from
// the browser console. Exposes only a setter + clearer + the fetch wrapper.
// parent-panel-settings.js also calls window._ppSetPin() after a successful
// PIN change to keep the in-memory value in sync.
(function () {
    let _pin = null;

    /** Store the verified parent PIN (called once after successful verify). @tag PARENT PIN */
    window._ppSetPin   = p  => { _pin = p; };
    /** Erase the verified PIN on panel close. @tag PARENT PIN */
    window._ppClearPin = () => { _pin = null; };

    /**
     * Authenticated fetch wrapper — injects X-Parent-Pin header automatically.
     * All parent mutation endpoints require this header for server-side auth.
     * @tag PARENT PIN
     */
    window._ppFetch = function (url, opts = {}) {
        const headers = Object.assign({}, opts.headers || {});
        if (_pin) headers["X-Parent-Pin"] = _pin;
        return fetch(url, Object.assign({}, opts, { headers }));
    };
}());

// ─── State ────────────────────────────────────────────────────
let _ppTab          = "home";
let _ppLiveInterval = null;

// ─── Tab registry ─────────────────────────────────────────────
const PP_TABS = [
    ["home",     "Home",     "home"],
    ["reading",  "Reading",  "book-open"],
    ["math",     "Math",     "calculator"],
    ["habits",   "Habits",   "flame"],
    ["island",   "Island",   "leaf"],
    ["settings", "Settings", "settings"],
];

// ─── Open / Close ─────────────────────────────────────────────

/** @tag PARENT PIN */
function openParentPanel() {
    _ppShowPinModal();
}

/** @tag PARENT */
function closeParentPanel() {
    const el = document.getElementById("parent-overlay");
    if (el) el.classList.add("hidden");
    _ppRemovePin();
    window._ppClearPin();
    window._ppDigits = "";
    _ppStopLivePoll();
}

// ─── PIN Modal ────────────────────────────────────────────────

/** @tag PARENT PIN */
function _ppShowPinModal() {
    const el = document.getElementById("parent-overlay");
    if (!el) return;
    el.classList.remove("hidden");
    el.innerHTML = `
        <div class="pp-pin-bg" id="pp-pin-bg">
            <div class="pp-pin-box">
                <div class="pp-pin-title">Parent Mode</div>
                <div class="pp-pin-sub">Enter your 4-digit PIN</div>
                <div class="pin-dots" id="pp-dots">
                    ${[0,1,2,3].map(() => `<div class="pin-dot"></div>`).join("")}
                </div>
                <div class="pin-error" id="pp-pin-err"></div>
                <div class="pin-pad">
                    ${[1,2,3,4,5,6,7,8,9].map(n =>
                        `<button class="pin-key" onclick="_ppPinKey('${n}')">${n}</button>`
                    ).join("")}
                    <button class="pin-key" aria-label="Clear" onclick="_ppPinKey('clear')"><i data-lucide="eraser" style="width:18px;height:18px"></i></button>
                    <button class="pin-key" onclick="_ppPinKey('0')">0</button>
                    <button class="pin-key delete" aria-label="Backspace" onclick="_ppPinKey('del')"><i data-lucide="delete" style="width:18px;height:18px"></i></button>
                </div>
                <button class="pp-btn secondary pp-pin-cancel" onclick="closeParentPanel()">Cancel</button>
            </div>
        </div>`;
    window._ppDigits = "";
    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** @tag PARENT PIN */
function _ppPinKey(key) {
    const digits = window._ppDigits || "";
    if (key === "del")        window._ppDigits = digits.slice(0, -1);
    else if (key === "clear") { window._ppDigits = ""; document.getElementById("pp-pin-err").textContent = ""; }
    else if (digits.length < 4) window._ppDigits = digits + key;
    _ppUpdateDots();
    if ((window._ppDigits || "").length === 4) setTimeout(_ppVerifyPin, 200);
}

/** @tag PARENT PIN */
function _ppUpdateDots() {
    const d = window._ppDigits || "";
    document.querySelectorAll(".pin-dot").forEach((el, i) => el.classList.toggle("filled", i < d.length));
}

/** @tag PARENT PIN */
async function _ppVerifyPin() {
    const enteredPin = window._ppDigits || "";
    try {
        const res = await fetch("/api/parent/verify-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pin: enteredPin }),
        });
        if (res.ok) {
            window._ppSetPin(enteredPin);
            _ppRemovePin();
            _ppRenderShell();
            _ppLoadTab("home");
        } else {
            window._ppDigits = "";
            _ppUpdateDots();
            const err = document.getElementById("pp-pin-err");
            if (err) err.textContent = "Wrong PIN. Try again.";
        }
    } catch (_) { window._ppDigits = ""; _ppUpdateDots(); }
}

/** @tag PARENT */
function _ppRemovePin() {
    const bg = document.getElementById("pp-pin-bg");
    if (bg) bg.remove();
}

// ─── Shell ────────────────────────────────────────────────────

/**
 * Standard empty-state markup used across all parent tabs.
 * @tag PARENT
 */
function _ppEmpty(icon, title, hint) {
    const t = escapeHtml(title || "Nothing here yet.");
    const h = hint ? escapeHtml(hint) : "";
    return `
        <div class="pp-empty">
            <i data-lucide="${icon || "inbox"}" class="pp-empty-icon"></i>
            <p class="pp-empty-title">${t}</p>
            ${h ? `<p class="pp-empty-hint">${h}</p>` : ""}
        </div>`;
}
window._ppEmpty = _ppEmpty;

/** @tag PARENT */
function _ppRenderShell() {
    const el = document.getElementById("parent-overlay");
    if (!el) return;

    const isRail  = localStorage.getItem("pp.sidebar") === "rail";
    const range   = localStorage.getItem("pp.range") || "weekly";
    const tabName = (PP_TABS.find(([k]) => k === _ppTab) || ["home", "Home"])[1];

    const navItems = PP_TABS.map(([key, label, icon]) => `
        <button class="pp-nav-item${key === _ppTab ? " active" : ""}"
                data-tab-key="${key}"
                onclick="_ppLoadTab('${key}')"
                title="${label}">
            <i data-lucide="${icon}" style="width:18px;height:18px;flex-shrink:0"></i>
            <span class="pp-nav-label">${label}</span>
            ${key === "habits" ? `<span class="pp-nav-badge" id="pp-habits-badge" style="display:none">0</span>` : ""}
        </button>`
    ).join("");

    el.innerHTML = `
        <aside class="pp-sidebar${isRail ? " pp-rail" : ""}" id="pp-sidebar">
            <div class="pp-brand">
                <div class="pp-brand-logo">G</div>
                <span class="pp-brand-text">Gia</span>
            </div>
            <nav class="pp-nav" style="flex:1;overflow-y:auto">
                ${navItems}
            </nav>
            <div class="pp-sidebar-foot">
                <button class="pp-nav-item" onclick="closeParentPanel()" title="Close">
                    <i data-lucide="log-out" style="width:18px;height:18px;flex-shrink:0"></i>
                    <span class="pp-nav-label">Close</span>
                </button>
            </div>
        </aside>
        <div class="pp-main">
            <header class="pp-topbar">
                <button class="pp-hamburger" onclick="_ppToggleSidebar()" aria-label="Toggle sidebar">
                    <i data-lucide="menu" style="width:18px;height:18px"></i>
                </button>
                <span class="pp-breadcrumb" id="pp-breadcrumb">${tabName}</span>
                <span class="pp-live-pill" id="pp-live-pill" style="display:none">
                    <span class="pp-live-dot"></span>Studying now
                </span>
                <div style="flex:1"></div>
                <div class="pp-seg">
                    <button class="pp-seg-btn${range === "daily"   ? " active" : ""}" onclick="_ppSetRange('daily')">Daily</button>
                    <button class="pp-seg-btn${range === "weekly"  ? " active" : ""}" onclick="_ppSetRange('weekly')">Weekly</button>
                    <button class="pp-seg-btn${range === "monthly" ? " active" : ""}" onclick="_ppSetRange('monthly')">Monthly</button>
                </div>
            </header>
            <div class="pp-content" id="pp-body">
                <p class="pp-loading-center">Loading…</p>
            </div>
        </div>`;

    if (typeof lucide !== "undefined") lucide.createIcons();
    _ppApplySidebarWidth();
    _ppUpdateHabitsBadge();
    _ppStartLivePoll();
}

// ─── Sidebar toggle ───────────────────────────────────────────

/**
 * Apply sidebar width inline. CSS-cascade edits to the rail rule kept
 * appearing to fail because service-worker.js uses cacheFirst for /static/*
 * — when CSS was edited without re-running build.sh, the ?v= hash didn't
 * bump and the SW kept serving the old parent.css forever. Inline style
 * bypasses the SW cache entirely. Also forces narrow viewports to rail
 * (matches the @media (max-width: 1100px) intent).
 * @tag PARENT
 */
function _ppApplySidebarWidth() {
    const sb = document.getElementById("pp-sidebar");
    if (!sb) return;
    const isRail = sb.classList.contains("pp-rail")
                || window.matchMedia("(max-width: 1100px)").matches;
    const w = isRail ? "60px" : "232px";
    // Flexbox quirk: flex-basis defaults to `auto` which uses content max-width
    // (~232px from "Parent Dashboard" + Gia card). Setting flex shorthand
    // forces the flex item to honour the rail width.
    sb.style.setProperty("flex", `0 0 ${w}`, "important");
    sb.style.setProperty("width", w, "important");
    sb.style.setProperty("min-width", "0", "important");
}

/** @tag PARENT */
function _ppToggleSidebar() {
    const sb = document.getElementById("pp-sidebar");
    if (!sb) return;
    const nowRail = sb.classList.toggle("pp-rail");
    localStorage.setItem("pp.sidebar", nowRail ? "rail" : "expand");
    _ppApplySidebarWidth();
}

if (typeof window !== "undefined" && !window._ppSidebarResizeBound) {
    window.addEventListener("resize", _ppApplySidebarWidth);
    window._ppSidebarResizeBound = true;
}

// ─── Range segment ────────────────────────────────────────────

/** @tag PARENT */
function _ppSetRange(range) {
    localStorage.setItem("pp.range", range);
    document.querySelectorAll(".pp-seg-btn").forEach(b => {
        b.classList.toggle("active", b.textContent.toLowerCase() === range);
    });
    // Reload current tab with new range
    const body = document.getElementById("pp-body");
    if (body) _ppLoadTab(_ppTab);
}

/** Returns current range string ("daily" | "weekly" | "monthly"). @tag PARENT */
function _ppGetRange() {
    return localStorage.getItem("pp.range") || "weekly";
}
window._ppGetRange = _ppGetRange;

// ─── Live poll (studying-now indicator) ───────────────────────

/** @tag PARENT */
function _ppStartLivePoll() {
    _ppCheckLive();
    _ppLiveInterval = setInterval(_ppCheckLive, 30000);
}

/** @tag PARENT */
function _ppStopLivePoll() {
    if (_ppLiveInterval) { clearInterval(_ppLiveInterval); _ppLiveInterval = null; }
}

/** @tag PARENT */
async function _ppCheckLive() {
    try {
        const d = await apiFetchJSON("/api/xp/summary");
        const pill = document.getElementById("pp-live-pill");
        if (!pill) { _ppStopLivePoll(); return; }
        // Consider "studying now" if XP was earned in the last 10 minutes.
        // xp/summary returns {today_xp, last_activity_at (ISO)}
        let active = false;
        if (d && d.last_activity_at) {
            const diff = Date.now() - new Date(d.last_activity_at).getTime();
            active = diff < 10 * 60 * 1000;
        }
        pill.style.display = active ? "flex" : "none";
    } catch (_) {}
}

// ─── Habits badge (pending day-off count) ────────────────────

/** @tag PARENT DAY_OFF */
async function _ppUpdateHabitsBadge() {
    try {
        const d = await apiFetchJSON("/api/parent/day-off-requests");
        const pending = (d.requests || []).filter(r => r.status === "pending").length;
        const badge = document.getElementById("pp-habits-badge");
        if (!badge) return;
        badge.textContent = pending;
        badge.style.display = pending > 0 ? "flex" : "none";
    } catch (_) {}
}

// ─── Tab routing ──────────────────────────────────────────────

/** @tag PARENT */
async function _ppLoadTab(tab) {
    _ppTab = tab;
    document.querySelectorAll(".pp-nav-item[data-tab-key]").forEach(b =>
        b.classList.toggle("active", b.dataset.tabKey === tab)
    );
    const tabName = (PP_TABS.find(([k]) => k === tab) || ["", tab])[1];
    const bc = document.getElementById("pp-breadcrumb");
    if (bc) bc.textContent = tabName;

    const body = document.getElementById("pp-body");
    if (!body) return;
    body.innerHTML = `<p class="pp-loading-center">Loading…</p>`;

    const missing = `<p style="color:var(--bad);padding:20px">Module not loaded.</p>`;
    switch (tab) {
        case "home":     if (typeof _ppHome        === "function") await _ppHome(body);        else body.innerHTML = missing; break;
        case "reading":  if (typeof _ppReading     === "function") await _ppReading(body);     else body.innerHTML = missing; break;
        case "math":     if (typeof _ppMathSummary === "function") await _ppMathSummary(body); else body.innerHTML = missing; break;
        case "habits":   if (typeof _ppHabits      === "function") await _ppHabits(body);      else body.innerHTML = missing; break;
        case "island":   if (typeof _ppIsland      === "function") await _ppIsland(body);      else body.innerHTML = missing; break;
        case "settings": if (typeof _ppSettings    === "function") await _ppSettings(body);    else body.innerHTML = missing; break;
        default: body.innerHTML = "<p>Coming soon.</p>";
    }
}

// ─── SVG chart helpers ────────────────────────────────────────

/**
 * Returns an inline SVG sparkline string.
 * @tag PARENT
 */
function _ppSparkline(data, opts) {
    if (!data || data.length === 0) return "";
    const { color = "var(--ink-2)", width = 120, height = 32, strokeWidth = 1.5, fill = false } = opts || {};
    const max = Math.max(...data, 1);
    const min = Math.min(...data, 0);
    const range = max - min || 1;
    const step = width / (Math.max(data.length - 1, 1));
    const pts = data.map((v, i) => [i * step, height - ((v - min) / range) * (height - 4) - 2]);
    const path = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
    const last = pts[pts.length - 1];
    const fillPath = `${path} L ${width} ${height} L 0 ${height} Z`;
    return `<svg width="${width}" height="${height}" style="display:block;overflow:visible">
        ${fill ? `<path d="${fillPath}" fill="${color}" opacity="0.12"/>` : ""}
        <path d="${path}" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linejoin="round" stroke-linecap="round"/>
        <circle cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="2.5" fill="${color}"/>
    </svg>`;
}
window._ppSparkline = _ppSparkline;

/**
 * Returns an inline SVG ring (progress arc) string.
 * @tag PARENT
 */
function _ppRing(value, max, opts) {
    if (max == null) max = 100;
    const { size = 56, stroke = 6, color = "var(--ink-1)", track = "var(--line)", label = "", sub = "" } = opts || {};
    const r = (size - stroke) / 2;
    const c = 2 * Math.PI * r;
    const pct = Math.min(1, Math.max(0, value / max));
    const inner = (label || sub) ? `
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1">
            ${label ? `<span class="mono" style="font-weight:700;font-size:${Math.round(size * 0.26)}px">${label}</span>` : ""}
            ${sub   ? `<span style="font-size:9px;color:var(--ink-3);margin-top:2px">${sub}</span>` : ""}
        </div>` : "";
    return `<div style="position:relative;width:${size}px;height:${size}px;flex-shrink:0">
        <svg width="${size}" height="${size}">
            <circle cx="${size/2}" cy="${size/2}" r="${r}" stroke="${track}" stroke-width="${stroke}" fill="none"/>
            <circle cx="${size/2}" cy="${size/2}" r="${r}" stroke="${color}" stroke-width="${stroke}" fill="none"
                stroke-dasharray="${c.toFixed(2)}" stroke-dashoffset="${(c*(1-pct)).toFixed(2)}"
                stroke-linecap="round" transform="rotate(-90 ${size/2} ${size/2})"/>
        </svg>${inner}
    </div>`;
}
window._ppRing = _ppRing;

/**
 * Returns an inline stacked horizontal bar HTML string.
 * segments: [{key, label, v, color}]
 * @tag PARENT
 */
function _ppStackBar(segments, opts) {
    const { height = 8, total } = opts || {};
    const sum = total || segments.reduce((s, x) => s + x.v, 0) || 1;
    const SUBJ = { english: "var(--english-primary)", math: "var(--math-primary)", diary: "var(--diary-primary)", rewards: "var(--rewards-primary)", review: "var(--review-primary)" };
    const bars = segments.map(s => {
        const bg = s.color || SUBJ[s.key] || "var(--ink-2)";
        return `<div title="${escapeHtml(s.label || s.key)}: ${s.v}" style="width:${((s.v/sum)*100).toFixed(1)}%;background:${bg}"></div>`;
    }).join("");
    return `<div style="display:flex;height:${height}px;width:100%;border-radius:999px;overflow:hidden;background:var(--line)">${bars}</div>`;
}
window._ppStackBar = _ppStackBar;

/**
 * Returns an inline vertical bar chart HTML string.
 * data: [{label, v, today?, color?, dim?, series?}]
 * series: [{key, v}] for stacked bars.
 * @tag PARENT
 */
function _ppBarChart(data, opts) {
    const { color = "var(--ink-1)", goalLine, height = 130, max, labels = true, valueLabels = false } = opts || {};
    if (!data || !data.length) return "";
    const SUBJ = { english: "var(--english-primary)", math: "var(--math-primary)", diary: "var(--diary-primary)", rewards: "var(--rewards-primary)", review: "var(--review-primary)" };
    const peak = max || Math.max(...data.map(d => d.v), 1);
    const labelH = labels ? 20 : 0;
    const vlH    = valueLabels ? 14 : 0;
    const chartH = height - labelH - vlH;
    const n = data.length;

    let bars = "";
    data.forEach((d, i) => {
        const colW   = 100 / n;
        const barW   = colW * 0.62;
        const x      = i * colW + (colW - barW) / 2;
        const totalH = Math.max(2, (d.v / peak) * chartH);
        const baseY  = chartH + vlH;

        const segments = (d.series && d.series.length) ? d.series : [{ key: "__solid", v: d.v, color: d.color || color }];
        const segTotal = segments.reduce((s, x) => s + x.v, 0) || 1;
        let cum = 0;
        const lastIdx = segments.length - 1;
        const segsHtml = segments.map((seg, si) => {
            const segH = (seg.v / segTotal) * totalH;
            const segY = baseY - cum - segH;
            cum += segH;
            const fill = seg.color || SUBJ[seg.key] || color;
            return `<rect x="${x.toFixed(1)}" y="${segY.toFixed(1)}" width="${barW.toFixed(1)}" height="${Math.max(0.2, segH).toFixed(1)}"
                fill="${fill}" opacity="${d.dim ? 0.35 : 1}" rx="${si === lastIdx ? 0.6 : 0}">
                <title>${escapeHtml(d.label)} · ${seg.key !== "__solid" ? seg.key + ": " : ""}${Math.round(seg.v)}</title></rect>`;
        }).join("");

        const valHtml = valueLabels ? `<text x="${(x+barW/2).toFixed(1)}" y="${(baseY-totalH-4).toFixed(1)}"
            text-anchor="middle" font-size="3.2" font-family="JetBrains Mono,monospace" fill="var(--ink-3)">${d.v}</text>` : "";
        bars += `<g>${valHtml}${segsHtml}</g>`;
    });

    const goalHtml = (goalLine != null) ? `<line x1="0" x2="100"
        y1="${(chartH + vlH - (goalLine/peak)*chartH).toFixed(1)}"
        y2="${(chartH + vlH - (goalLine/peak)*chartH).toFixed(1)}"
        stroke="var(--ink-4)" stroke-width="0.3" stroke-dasharray="1 1" vector-effect="non-scaling-stroke"/>` : "";

    const labelRow = labels ? `<div style="display:grid;grid-template-columns:repeat(${n},1fr);gap:0;margin-top:4px">
        ${data.map(d => `<div class="mono" style="font-size:10px;color:${d.today ? "var(--ink-1)" : "var(--ink-3)"};
            font-weight:${d.today ? 700 : 500};text-align:center">${escapeHtml(d.label)}</div>`).join("")}
    </div>` : "";

    return `<div style="width:100%">
        <svg width="100%" height="${chartH+vlH}" viewBox="0 0 100 ${chartH+vlH}"
            preserveAspectRatio="none" style="display:block;overflow:visible">
            ${goalHtml}${bars}
        </svg>${labelRow}
    </div>`;
}
window._ppBarChart = _ppBarChart;

/**
 * Returns a trend indicator HTML string (▲+12% or ▼−5%).
 * @tag PARENT
 */
function _ppTrend(value, opts) {
    const { suffix = "%", size = 12 } = opts || {};
    const up    = value >= 0;
    const color = up ? "var(--ok)" : "var(--bad)";
    const arrow = up ? "▲" : "▼";
    const sign  = up ? "+" : "";
    return `<span class="mono" style="display:inline-flex;align-items:center;gap:2px;color:${color};font-size:${size}px;font-weight:600">
        <span style="font-size:${size-1}px">${arrow}</span>${sign}${value}${escapeHtml(suffix)}
    </span>`;
}
window._ppTrend = _ppTrend;

/**
 * Returns a KPI card HTML string.
 * @tag PARENT
 */
function _ppKpi(label, value, opts) {
    const { unit, sub, trend, accent, dense = false, colorful = false } = opts || {};
    const ac = accent || "var(--ink-1)";
    const pad = dense ? "14px 16px" : "18px 20px";
    const valSize = dense ? 28 : 34;
    const borderTop = (colorful && accent) ? `border-top:2px solid ${ac}` : "";
    const dotHtml = accent ? `<span style="width:6px;height:6px;border-radius:50%;background:${ac};display:inline-block;flex-shrink:0"></span>` : "";
    const footHtml = (sub || trend != null) ? `
        <div style="display:flex;align-items:center;gap:8px;margin-top:${dense ? 6 : 8}px">
            ${trend != null ? _ppTrend(trend) : ""}
            ${sub ? `<span style="font-size:12px;color:var(--ink-3)">${escapeHtml(sub)}</span>` : ""}
        </div>` : "";
    return `<div class="pp-panel" style="padding:${pad};${borderTop}">
        <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--ink-3);display:flex;align-items:center;gap:6px">
            ${dotHtml}${escapeHtml(label)}
        </div>
        <div style="display:flex;align-items:baseline;gap:4px;margin-top:${dense ? 6 : 8}px">
            <span class="mono" style="font-size:${valSize}px;font-weight:700;letter-spacing:-0.04em;line-height:1;color:${(colorful && accent) ? ac : "var(--ink-1)"}">
                ${escapeHtml(String(value))}
            </span>
            ${unit ? `<span class="mono" style="font-size:13px;color:var(--ink-3);font-weight:600">${escapeHtml(unit)}</span>` : ""}
        </div>${footHtml}
    </div>`;
}
window._ppKpi = _ppKpi;
