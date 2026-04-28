/* ================================================================
   math-placement-results.js — Placement results + sidebar status
   Section: Math
   Dependencies: math-placement.js (shares _escPl helper on window)
   API endpoints: /api/math/placement/results
   ================================================================ */

/* global _escPl, switchView */

// ── Results ────────────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
function _renderPlacementResults(data) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const suggested = data.suggested_grade || 'G3';
    const rows = (data.results || []).map(r => {
        const pct = r.total_questions ? Math.round((r.raw_score / r.total_questions) * 100) : 0;
        const barColor = pct >= 70 ? 'pass' : pct >= 40 ? 'mid' : 'fail';
        return `
            <div class="math-placement-result-row">
                <div class="math-placement-result-top">
                    <span class="math-placement-result-label">${_escPl(r.label)}</span>
                    <span class="math-placement-result-grade">${_escPl(r.estimated_grade)}</span>
                </div>
                <div class="math-placement-result-bar-wrap">
                    <div class="math-placement-result-bar ${barColor}" style="width:${pct}%"></div>
                </div>
                <div class="math-placement-result-meta">${r.raw_score}/${r.total_questions} · ${pct}%</div>
            </div>
        `;
    }).join('');

    stage.innerHTML = `
        <div class="math-placement-results-wrap">
            <div class="math-placement-results-icon">
                <i data-lucide="check-circle-2" style="width:36px;height:36px;stroke-width:1.5;color:var(--math-primary)"></i>
            </div>
            <h2 class="math-placement-results-title">Placement Complete</h2>
            <div class="math-placement-suggested-grade">${_escPl(suggested)}</div>
            <div class="math-placement-suggested-label">Suggested starting grade</div>
            <div class="math-placement-domain-results">${rows}</div>
            <div class="math-placement-result-actions">
                <button class="math-btn-ghost" id="math-placement-back">Back</button>
                <button class="math-btn-primary" id="math-placement-go">
                    Start ${_escPl(suggested)} Academy
                    <i data-lucide="arrow-right" style="width:14px;height:14px;vertical-align:-2px;stroke-width:2"></i>
                </button>
            </div>
        </div>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();

    document.getElementById('math-placement-back').addEventListener('click', () => {
        if (typeof hideLessonStage === 'function') hideLessonStage();
        if (typeof switchView === 'function') switchView('math');
    });
    document.getElementById('math-placement-go').addEventListener('click', () => {
        if (typeof hideLessonStage === 'function') hideLessonStage();
        if (typeof switchView === 'function') switchView('math');
        const sel = document.getElementById('math-grade-select');
        if (sel) {
            setTimeout(() => {
                const opt = Array.from(sel.options).find(o => o.value === suggested);
                if (opt) {
                    sel.value = suggested;
                    sel.dispatchEvent(new Event('change'));
                }
            }, 300);
        }
    });
}

// ── Sidebar status ─────────────────────────────────────────

/** @tag MATH @tag PLACEMENT */
async function loadMathPlacementStatus() {
    try {
        const res = await fetch('/api/math/placement/results');
        if (!res.ok) {
            const s = document.getElementById('math-placement-status');
            const g = document.getElementById('math-placement-suggested');
            if (s) s.textContent = 'Not taken';
            if (g) g.textContent = '—';
            return;
        }
        const data = await res.json();
        const results = data.results || [];
        const grades = ['G2', 'G3', 'G4', 'G5', 'G6'];
        const lowest = results.length
            ? results.reduce((a, b) => grades.indexOf(a.estimated_grade) < grades.indexOf(b.estimated_grade) ? a : b).estimated_grade
            : '—';
        const s = document.getElementById('math-placement-status');
        const g = document.getElementById('math-placement-suggested');
        if (s) s.textContent = results.length ? `${results.length} domains` : 'Not taken';
        if (g) g.textContent = lowest;
        const btn = document.getElementById('math-btn-placement');
        if (btn && results.length) btn.textContent = 'Retake';
    } catch (_) { /* silent */ }
}

// Hook into existing loadMathSidebarStatus if available
if (typeof window !== 'undefined') {
    const prev = window.loadMathSidebarStatus;
    window.loadMathSidebarStatus = function () {
        if (typeof prev === 'function') try { prev(); } catch (_) {}
        loadMathPlacementStatus();
    };
}
