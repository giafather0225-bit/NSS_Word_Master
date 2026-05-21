/* ================================================================
   parent-panel-charts.js — SVG/HTML chart helper utilities for Parent Dashboard
   Section: Parent
   Dependencies: core.js (escapeHtml)
   API endpoints: none
   Split from: parent-panel.js (lines 352-526)
   ================================================================ */

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
