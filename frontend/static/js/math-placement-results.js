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
        return `
            <div class="math-placement-row">
                <div class="math-placement-row-label">${_escPl(r.label)}</div>
                <div class="math-placement-row-meta">
                    <span class="math-summary-chip">${_escPl(r.estimated_grade)}</span>
                    <span class="math-placement-row-score">${r.raw_score}/${r.total_questions} · ${pct}%</span>
                </div>
            </div>
        `;
    }).join('');

    stage.innerHTML = `
        <div class="math-round-summary">
            <div class="math-summary-icon">🎯</div>
            <h2 class="math-summary-title">Placement Complete</h2>
            <div class="math-summary-score">${_escPl(suggested)}</div>
            <div class="math-summary-pct">Suggested starting grade</div>
            <div class="math-placement-results">${rows}</div>
            <div class="math-fluency-actions">
                <button class="math-btn-ghost" id="math-placement-back">Back</button>
                <button class="math-btn-primary" id="math-placement-go">Go to ${_escPl(suggested)} Academy</button>
            </div>
        </div>
    `;
    document.getElementById('math-placement-back').addEventListener('click', () => {
        if (typeof switchView === 'function') switchView('math');
        const stageCard = document.getElementById('stage-card');
        if (stageCard) stageCard.style.display = 'none';
        const idleWrap = document.getElementById('idle-wrapper');
        if (idleWrap) idleWrap.style.display = '';
    });
    document.getElementById('math-placement-go').addEventListener('click', () => {
        if (typeof switchView === 'function') switchView('math');
        const stageCard = document.getElementById('stage-card');
        if (stageCard) stageCard.style.display = 'none';
        const idleWrap = document.getElementById('idle-wrapper');
        if (idleWrap) idleWrap.style.display = '';
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
