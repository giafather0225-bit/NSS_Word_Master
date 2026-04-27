/* ================================================================
   math-navigation.js — Math sidebar navigation, grade/unit/lesson
                        dropdowns, and accordion logic.
   Section: Math / Navigation
   Dependencies: core.js, navigation.js
   API endpoints: /api/math/academy/grades, /api/math/academy/{grade}/units,
                  /api/math/academy/{grade}/{unit}/lessons,
                  /api/math/fluency/summary, /api/math/my-problems/summary
   ================================================================ */

/* global $, currentSubject */

// ── Math state ──────────────────────────────────────────────
let mathGrade = '';
let mathUnit = '';
let mathLesson = '';

// ── Accordion logic (one open at a time) ────────────────────

/** @tag MATH @tag NAVIGATION */
(function initMathAccordions() {
    document.addEventListener('click', (e) => {
        const header = e.target.closest('#sb-math-section .sb-accordion-header');
        if (!header) return;
        const target = header.dataset.target;
        const body = document.getElementById(target);
        if (!body) return;

        const isOpen = header.classList.contains('math-acc-open');

        // Close all in same group
        const group = header.closest('.sb-section');
        if (group) {
            group.querySelectorAll('.sb-accordion-header').forEach(h => {
                h.classList.remove('math-acc-open');
                const b = document.getElementById(h.dataset.target);
                if (b) b.style.display = 'none';
            });
        }

        // Toggle clicked
        if (!isOpen) {
            header.classList.add('math-acc-open');
            body.style.display = '';
        }
    });
})();

// ── switchView integration ──────────────────────────────────

/** @tag MATH @tag NAVIGATION */
const _origSwitchView = window.switchView;
window.switchView = function (view) {
    if (view === 'math') {
        currentView = 'math';
        document.body.dataset.view = 'math';

        // Hide main content areas (same pattern as home.js)
        const homeDash  = document.getElementById('home-dashboard');
        const idleWrap  = document.getElementById('idle-wrapper');
        const stageCard = document.getElementById('stage-card');
        const dailyView = document.getElementById('daily-words-view');
        const diaryView = document.getElementById('diary-view');
        const topBar    = document.querySelector('.top-bar');
        const sidebar   = document.getElementById('sidebar');

        if (homeDash)  homeDash.style.display = 'none';
        if (idleWrap)  idleWrap.style.display = 'none';
        if (stageCard) stageCard.style.display = 'none';
        if (dailyView) dailyView.style.display = 'none';
        if (diaryView) diaryView.style.display = 'none';
        if (topBar)    topBar.style.display = 'none';
        if (sidebar)   sidebar.dataset.mode = 'math';

        updateSidebarMode('math');
        loadMathGrades();
        loadMathSidebarStatus();

        // Show math home screen
        if (typeof showMathHome === 'function') showMathHome();
        return;
    }

    // For non-math views, delegate to original
    if (typeof _origSwitchView === 'function') {
        _origSwitchView(view);
    }
};

// ── Load grades ─────────────────────────────────────────────

/** @tag MATH @tag ACADEMY */
async function loadMathGrades() {
    const sel = document.getElementById('math-grade-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">Select grade</option>';
    try {
        const data = await apiFetchJSON('/api/math/academy/grades');
        (data.grades || []).forEach(g => {
            const opt = document.createElement('option');
            opt.value = g;
            opt.textContent = g;
            sel.appendChild(opt);
        });
        // Auto-select if only one
        if (data.grades && data.grades.length === 1) {
            sel.value = data.grades[0];
            await loadMathUnits(data.grades[0]);
        }
    } catch (err) {
        console.warn('[math] Failed to load grades:', err);
    }
}

/** @tag MATH @tag ACADEMY */
async function loadMathUnits(grade) {
    mathGrade = grade;
    const sel = document.getElementById('math-unit-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">Select unit</option>';
    document.getElementById('math-lesson-select').innerHTML = '<option value="">Select lesson</option>';
    updateMathStartBtn();
    if (!grade) return;

    try {
        const data = await apiFetchJSON(`/api/math/academy/${encodeURIComponent(grade)}/units`);
        (data.units || []).forEach(u => {
            const opt = document.createElement('option');
            opt.value = u;
            opt.textContent = u.replace(/_/g, ' ');
            sel.appendChild(opt);
        });
    } catch (err) {
        console.warn('[math] Failed to load units:', err);
    }
}

/** @tag MATH @tag ACADEMY */
async function loadMathLessons(grade, unit) {
    mathUnit = unit;
    const sel = document.getElementById('math-lesson-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">Select lesson</option>';
    updateMathStartBtn();
    if (!unit) return;

    try {
        const data = await apiFetchJSON(`/api/math/academy/${encodeURIComponent(grade)}/${encodeURIComponent(unit)}/lessons`);
        (data.lessons || []).forEach(l => {
            const opt = document.createElement('option');
            opt.value = l.name;
            const prefix = l.is_completed ? '✓ ' : '';
            opt.textContent = prefix + l.name.replace(/_/g, ' ');
            sel.appendChild(opt);
        });

        // Unit test button
        const utBtn = document.getElementById('math-btn-unit-test');
        if (utBtn) {
            const badge = utBtn.querySelector('.sb-card-badge');
            if (data.unit_test_unlocked) {
                utBtn.disabled = false;
                if (badge) badge.textContent = '→';
            } else {
                utBtn.disabled = true;
                if (badge) badge.textContent = '🔒';
            }
        }
    } catch (err) {
        console.warn('[math] Failed to load lessons:', err);
    }
}

// ── Start button ────────────────────────────────────────────

/** @tag MATH @tag NAVIGATION */
function updateMathStartBtn() {
    const btn = document.getElementById('math-btn-start');
    if (!btn) return;
    const lessonSel = document.getElementById('math-lesson-select');
    btn.disabled = !(lessonSel && lessonSel.value);
}

// ── Sidebar status ──────────────────────────────────────────

/** @tag MATH @tag NAVIGATION */
async function loadMathSidebarStatus() {
    // Fluency summary
    try {
        const data = await apiFetchJSON('/api/math/fluency/summary');
        const el = document.getElementById('math-fluency-today');
        if (el) el.textContent = `${data.today_rounds}/${data.daily_target} rounds`;
    } catch (e) { /* silent */ }

    // My Problems summary
    try {
        const data = await apiFetchJSON('/api/math/my-problems/summary');
        const el = document.getElementById('math-problems-count');
        if (el) el.textContent = `${data.due_today} items`;
    } catch (e) { /* silent */ }

    // Kangaroo sets status
    try {
        const data = await apiFetchJSON('/api/math/kangaroo/sets');
        const total = (data.sets || []).length;
        const done = (data.sets || []).filter(s => s.completed).length;
        const el = document.getElementById('math-kangaroo-week');
        if (el) el.textContent = `${done}/${total} sets`;
    } catch (e) { /* silent */ }

    // Daily Challenge status
    try {
        const data = await apiFetchJSON('/api/math/daily/today');
        const el = document.getElementById('math-daily-status');
        if (el) {
            if (!data.exists) el.textContent = 'Not available';
            else if (data.completed) el.textContent = `✓ ${data.score}/${data.total}`;
            else el.textContent = `${data.total} problems`;
        }
    } catch (e) { /* silent */ }
}

// ── Wire select handlers ────────────────────────────────────

/** @tag MATH @tag NAVIGATION */
(function wireMathSelects() {
    document.addEventListener('DOMContentLoaded', () => {
        const gradeSel = document.getElementById('math-grade-select');
        const unitSel = document.getElementById('math-unit-select');
        const lessonSel = document.getElementById('math-lesson-select');
        const startBtn = document.getElementById('math-btn-start');

        if (gradeSel) {
            gradeSel.addEventListener('change', () => loadMathUnits(gradeSel.value));
        }
        if (unitSel) {
            unitSel.addEventListener('change', () => loadMathLessons(mathGrade, unitSel.value));
        }
        if (lessonSel) {
            lessonSel.addEventListener('change', () => {
                mathLesson = lessonSel.value;
                updateMathStartBtn();
            });
        }
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                if (!mathGrade || !mathUnit || !mathLesson) return;
                console.log(`[math] Starting lesson: ${mathGrade}/${mathUnit}/${mathLesson}`);
                startMathLesson(mathGrade, mathUnit, mathLesson);
            });
        }

        const dailyBtn = document.getElementById('math-btn-daily');
        if (dailyBtn) {
            dailyBtn.addEventListener('click', () => {
                if (typeof startMathDaily === 'function') startMathDaily();
            });
        }

        const glossBtn = document.getElementById('math-btn-glossary');
        if (glossBtn) {
            glossBtn.addEventListener('click', () => {
                if (typeof startMathGlossary === 'function') {
                    const g = document.getElementById('math-glossary-grade');
                    startMathGlossary((g && g.textContent.trim()) || 'G3');
                }
            });
        }

        const kangBtn = document.getElementById('math-btn-kangaroo');
        if (kangBtn) {
            kangBtn.addEventListener('click', () => {
                if (typeof startMathKangaroo === 'function') startMathKangaroo();
            });
        }
    });
})();
