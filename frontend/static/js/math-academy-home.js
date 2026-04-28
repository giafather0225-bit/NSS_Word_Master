/* ================================================================
   math-academy-home.js — Math Academy "Learning Path" overview view
   Section: Math
   Dependencies: math-navigation.js, math-academy.js
   API endpoints:
     GET /api/math/academy/{grade}/learning-path
   ================================================================ */

/* global startMathLesson, startMathFluency, startMathKangaroo */

const _mathAcademyHome = (() => {
    let _currentGrade = '';

    // ── Stage label map ──────────────────────────────────────
    const STAGE_LABELS = {
        pretest:    'Pretest',
        learn:      'Learn',
        try:        'Try',
        practice_r1: 'R1 Basic',
        practice_r2: 'R2 Mixed',
        practice_r3: 'R3 Adv',
        wrong_review: 'Review',
        complete:   'Done',
    };

    const STAGE_ORDER = ['pretest','learn','try','practice_r1','practice_r2','practice_r3'];

    // ── Public API ───────────────────────────────────────────

    /** Render the learning-path view for a given grade. */
    async function show(grade) {
        _currentGrade = grade || 'G3';
        // Hide the "three wins" math home when showing the learning path
        const mathHome = document.getElementById('math-home');
        if (mathHome) mathHome.style.display = 'none';

        let el = document.getElementById('math-academy-home');
        if (!el) {
            el = document.createElement('div');
            el.id = 'math-academy-home';
            const area = document.getElementById('stage-area');
            if (area) area.appendChild(el);
        }
        el.style.display = '';
        el.innerHTML = `<div class="mah-loading">Loading...</div>`;

        try {
            const data = await _fetchJSON(`/api/math/academy/${encodeURIComponent(_currentGrade)}/learning-path`);
            _render(el, data);
        } catch (err) {
            el.innerHTML = `<div class="mah-error">Could not load learning path.</div>`;
            console.warn('[math-academy-home] fetch failed', err);
        }
    }

    function hide() {
        const el = document.getElementById('math-academy-home');
        if (el) el.style.display = 'none';
    }

    function refresh() {
        if (_currentGrade) show(_currentGrade);
    }

    // ── Render ───────────────────────────────────────────────

    function _render(el, data) {
        const { units = [], stats = {}, current = null } = data;
        const totalUnits = units.length;
        const masteredUnits = units.filter(u => u.is_mastered).length;

        el.innerHTML = `
            <div class="mah-wrap">
                <div class="mah-breadcrumb">
                    <span class="mah-bc-section">Math</span>
                    <span class="mah-bc-sep">·</span>
                    <span class="mah-bc-page">Academy</span>
                    <span class="mah-bc-sep">·</span>
                    <span class="mah-bc-grade">${_esc(_currentGrade)}</span>
                </div>

                ${current ? _heroCard(current, units) : _startHint()}

                ${_statsRow(stats)}

                <section class="mah-unit-section">
                    <div class="mah-unit-section-header">
                        <span class="mah-unit-section-label">ALL UNITS · ${_esc(_currentGrade)} (GO MATH ALIGNED)</span>
                        <span class="mah-unit-count">${masteredUnits} / ${totalUnits} mastered</span>
                    </div>
                    <div class="mah-unit-list">
                        ${units.map((u, i) => _unitCard(u, i + 1)).join('')}
                    </div>
                </section>
            </div>
        `;

        _bindEvents(el, data);
    }

    // ── Hero card ─────────────────────────────────────────────

    function _heroCard(current, units) {
        const unit = units.find(u => u.name === current.unit) || {};
        const lessonDisplay = current.lesson.replace(/_/g, ' ');
        const unitDisplay = unit.display || current.unit.replace(/_/g, ' ');
        const eyebrow = `CONTINUE · ${_unitNum(current.unit)} · ${_lessonNum(current.lesson)}`;

        return `
            <div class="mah-hero" id="mah-hero">
                <div class="mah-hero-body">
                    <div class="mah-hero-eyebrow">${_esc(eyebrow)}</div>
                    <h1 class="mah-hero-title">${_esc(lessonDisplay)}</h1>
                    <p class="mah-hero-sub">${_esc(unitDisplay)}</p>
                    ${_stepStrip(current.stage)}
                </div>
                <button class="mah-hero-btn" id="mah-continue-btn"
                    data-unit="${_esc(current.unit)}"
                    data-lesson="${_esc(current.lesson)}"
                    data-stage="${_esc(current.stage || 'pretest')}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    Continue
                </button>
            </div>
        `;
    }

    function _stepStrip(currentStage) {
        const items = STAGE_ORDER.map((key, i) => {
            const idx = STAGE_ORDER.indexOf(currentStage);
            const done    = idx >= 0 && i < idx;
            const current = key === currentStage;
            let cls = 'mah-step';
            if (done) cls += ' done';
            else if (current) cls += ' current';
            else cls += ' locked';

            const inner = done
                ? `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`
                : String(i + 1);
            return `
                <div class="${cls}">
                    <div class="mah-step-dot">${inner}</div>
                    <div class="mah-step-label">${_esc(STAGE_LABELS[key] || key)}</div>
                </div>
                ${i < STAGE_ORDER.length - 1 ? '<div class="mah-step-line"></div>' : ''}
            `;
        }).join('');
        return `<div class="mah-step-strip">${items}</div>`;
    }

    function _startHint() {
        return `
            <div class="mah-start-hint">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                Choose a lesson below to start your learning path.
            </div>
        `;
    }

    // ── Stats row ─────────────────────────────────────────────

    function _statsRow(stats) {
        const chips = [
            { val: `${stats.lessons_mastered || 0}`, sub: `of ${stats.total_lessons || 0}`, label: 'LESSONS MASTERED', icon: 'check-circle' },
            { val: String(stats.streak_days || 0), sub: 'days', label: 'STREAK', icon: 'flame' },
            { val: (stats.total_xp || 0).toLocaleString(), sub: 'all-time', label: 'TOTAL XP', icon: 'star' },
            { val: stats.accuracy_pct ? `${stats.accuracy_pct}%` : '—', sub: 'last 7d', label: 'ACCURACY', icon: 'target' },
        ];
        return `
            <div class="mah-stats-row">
                ${chips.map(c => `
                    <div class="mah-stat-chip">
                        <span class="mah-stat-label">${_esc(c.label)}</span>
                        <span class="mah-stat-val">${_esc(c.val)}</span>
                        <span class="mah-stat-sub">${_esc(c.sub)}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // ── Unit cards ────────────────────────────────────────────

    function _unitCard(unit, num) {
        const pct = unit.total_lessons > 0
            ? Math.round((unit.completed_lessons / unit.total_lessons) * 100) : 0;
        const statusCls = unit.is_mastered ? 'mastered' : (unit.completed_lessons > 0 ? 'in-progress' : '');
        const statusLabel = unit.is_mastered ? 'MASTERED'
            : (unit.completed_lessons > 0 ? 'IN PROGRESS' : '');

        return `
            <div class="mah-unit-card ${statusCls}" data-unit="${_esc(unit.name)}">
                <div class="mah-unit-num">U${num}</div>
                <div class="mah-unit-info">
                    <div class="mah-unit-name">${_esc(unit.display)}</div>
                    <div class="mah-unit-lessons">${unit.completed_lessons} / ${unit.total_lessons} lessons</div>
                    <div class="mah-unit-bar">
                        <div class="mah-unit-bar-fill" style="width:${pct}%"></div>
                    </div>
                </div>
                ${statusLabel ? `<div class="mah-unit-badge ${statusCls}">${statusLabel}</div>` : '<div class="mah-unit-chevron"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg></div>'}
            </div>
        `;
    }

    // ── Events ───────────────────────────────────────────────

    function _bindEvents(el, data) {
        // Continue button
        const continueBtn = el.querySelector('#mah-continue-btn');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                const { unit, lesson } = continueBtn.dataset;
                _launchLesson(unit, lesson);
            });
        }

        // Unit card click → pick first incomplete lesson and launch
        el.querySelectorAll('.mah-unit-card').forEach(card => {
            card.addEventListener('click', () => {
                const unitName = card.dataset.unit;
                const unitData = data.units.find(u => u.name === unitName);
                if (!unitData) return;
                if (unitData.current_lesson) {
                    _launchLesson(unitName, unitData.current_lesson);
                } else if (!unitData.is_mastered) {
                    // No progress yet — show unit lessons via sidebar (fallback)
                    _populateSidebarForUnit(unitName);
                }
            });
        });
    }

    function _launchLesson(unit, lesson) {
        hide();
        if (typeof hideMathHome === 'function') hideMathHome();
        if (typeof startMathLesson === 'function') {
            startMathLesson(_currentGrade, unit, lesson);
        }
    }

    function _populateSidebarForUnit(unitName) {
        const gradeSel = document.getElementById('math-grade-select');
        const unitSel  = document.getElementById('math-unit-select');
        if (gradeSel) gradeSel.value = _currentGrade;
        if (typeof loadMathUnits === 'function') {
            loadMathUnits(_currentGrade).then(() => {
                if (unitSel) {
                    unitSel.value = unitName;
                    if (typeof loadMathLessons === 'function') {
                        loadMathLessons(_currentGrade, unitName);
                    }
                }
            });
        }
    }

    // ── Helpers ───────────────────────────────────────────────

    function _unitNum(unitName) {
        const m = unitName.match(/^U(\d+)/);
        return m ? `U${m[1]}` : unitName;
    }

    function _lessonNum(lessonName) {
        const m = lessonName.match(/L(\d+)/i);
        return m ? `L${m[1]}` : lessonName;
    }

    async function _fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) throw new Error(r.status);
        return r.json();
    }

    function _esc(s) {
        const d = document.createElement('div');
        d.textContent = s == null ? '' : String(s);
        return d.innerHTML;
    }

    return { show, hide, refresh };
})();

// ── Public API ───────────────────────────────────────────────

/** @tag MATH @tag ACADEMY */
function showMathAcademyHome(grade) { _mathAcademyHome.show(grade); }

/** @tag MATH @tag ACADEMY */
function hideMathAcademyHome() { _mathAcademyHome.hide(); }

/** @tag MATH @tag ACADEMY */
function refreshMathAcademyHome() { _mathAcademyHome.refresh(); }
