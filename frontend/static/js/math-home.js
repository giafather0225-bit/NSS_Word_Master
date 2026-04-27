/* ================================================================
   math-home.js — Math entry home screen (Three small wins + overview)
   Section: Math
   Dependencies: math-home-wins.js, math-navigation.js, math-academy.js,
                 math-fluency.js, math-daily.js, math-glossary.js
   API endpoints: /api/math/fluency/summary, /api/math/daily/today,
                  /api/math/academy/weekly-stats
   ================================================================ */

/* global mathState, startMathLesson, startMathFluency, startMathDaily,
          startMathGlossary, mathGrade, mathUnit, mathLesson,
          loadMathUnits, loadMathLessons, updateMathStartBtn */

const _mathHome = (() => {
    // ── Last lesson memory (localStorage) ────────────────────
    const LS_KEY = 'mathHome_lastLesson';

    function _saveLastLesson(grade, unit, lesson) {
        try {
            localStorage.setItem(LS_KEY, JSON.stringify({ grade, unit, lesson }));
        } catch (_) { /* ignore */ }
    }

    function _loadLastLesson() {
        try {
            const raw = localStorage.getItem(LS_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (_) { return null; }
    }

    // ── Date helpers ─────────────────────────────────────────
    function _todayLabel() {
        const d = new Date();
        return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    }

    // ── API helpers ──────────────────────────────────────────
    async function _fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) throw new Error(r.status);
        return r.json();
    }

    // ── Mount / unmount ──────────────────────────────────────

    /** Show the math home screen. */
    function show() {
        let el = document.getElementById('math-home');
        if (!el) {
            el = document.createElement('div');
            el.id = 'math-home';
            const area = document.getElementById('stage-area');
            if (area) area.appendChild(el);
        }
        el.style.display = '';
        _render(el);
    }

    /** Hide the math home screen. */
    function hide() {
        const el = document.getElementById('math-home');
        if (el) el.style.display = 'none';
    }

    // ── Render ───────────────────────────────────────────────

    async function _render(el) {
        el.innerHTML = `<div class="mh-loading">Loading...</div>`;

        // Parallel data fetch
        const [fluency, daily, lastLesson, weekly] = await Promise.all([
            _fetchJSON('/api/math/fluency/summary').catch(() => null),
            _fetchJSON('/api/math/daily/today').catch(() => null),
            Promise.resolve(_loadLastLesson()),
            _fetchJSON('/api/math/academy/weekly-stats').catch(() => null),
        ]);

        const wins = mathHomeBuildWins(fluency, daily, lastLesson);
        const doneCount = wins.filter(w => w.done).length;

        el.innerHTML = `
            <div class="mh-wrap">

                <!-- Header -->
                <div class="mh-header">
                    <div class="mh-header-left">
                        <div class="mh-section-tag">Math</div>
                        <h1 class="mh-title">Good ${_timeOfDay()}, Gia!</h1>
                        <p class="mh-date">${_todayLabel()}</p>
                    </div>
                    <div class="mh-header-right">
                        <div class="mh-header-stats" id="mh-stats-row">
                            <div class="mh-stat-chip" id="mh-stat-time">
                                <span class="mh-stat-val">—</span>
                                <span class="mh-stat-label">min today</span>
                            </div>
                            <div class="mh-stat-chip" id="mh-stat-probs">
                                <span class="mh-stat-val">—</span>
                                <span class="mh-stat-label">problems</span>
                            </div>
                            <div class="mh-stat-chip" id="mh-stat-xp">
                                <span class="mh-stat-val">—</span>
                                <span class="mh-stat-label">XP earned</span>
                            </div>
                        </div>
                        <button class="mh-settings-btn" id="mh-settings-btn" aria-label="Math settings">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                        </button>
                    </div>
                </div>

                <!-- Three small wins -->
                <section class="mh-section">
                    <div class="mh-section-header">
                        <h2 class="mh-section-title">Three small wins for today</h2>
                        <span class="mh-wins-badge ${doneCount === 3 ? 'all-done' : ''}">${doneCount}/3 done</span>
                    </div>
                    <div class="mh-wins-grid">
                        ${wins.map((w, i) => mathHomeWinCard(w, i)).join('')}
                    </div>
                </section>

                <!-- Continue / Start lesson -->
                ${lastLesson ? mathHomeContinueSection(lastLesson) : mathHomeStartSection()}

                <!-- Quick access -->
                <section class="mh-section">
                    <h2 class="mh-section-title">Quick access</h2>
                    <div class="mh-quick-grid">
                        <button class="mh-quick-btn" id="mh-q-fluency">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            <span>Fact Fluency</span>
                        </button>
                        <button class="mh-quick-btn" id="mh-q-glossary">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                            <span>Glossary</span>
                        </button>
                        <button class="mh-quick-btn" id="mh-q-daily">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                            <span>Daily Challenge</span>
                        </button>
                        <button class="mh-quick-btn" id="mh-q-placement">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                            <span>Placement</span>
                        </button>
                    </div>
                </section>

                <!-- This Week -->
                ${weekly ? mathHomeWeeklySection(weekly) : ''}

            </div>
        `;

        _bindEvents(el, wins, lastLesson);
        _loadTodayStats();
    }

    // ── Bind events ──────────────────────────────────────────

    function _bindEvents(el, wins, lastLesson) {
        // Win card buttons
        el.querySelectorAll('.mh-win-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = parseInt(btn.dataset.win, 10);
                const win = wins[i];
                if (!win || win.done || win.cta === '—') return;
                _handleWinClick(win);
            });
        });

        // Continue button
        const contBtn = el.querySelector('#mh-continue-btn');
        if (contBtn && lastLesson) {
            contBtn.addEventListener('click', () => {
                _launchLesson(lastLesson.grade, lastLesson.unit, lastLesson.lesson);
            });
        }

        // Settings
        el.querySelector('#mh-settings-btn')?.addEventListener('click', () => {
            if (typeof openMathPreferences === 'function') openMathPreferences();
        });

        // Quick access
        el.querySelector('#mh-q-fluency')?.addEventListener('click', () => {
            if (typeof startMathFluency === 'function') { hide(); startMathFluency(); }
        });
        el.querySelector('#mh-q-glossary')?.addEventListener('click', () => {
            if (typeof startMathGlossary === 'function') { hide(); startMathGlossary('G4'); }
        });
        el.querySelector('#mh-q-daily')?.addEventListener('click', () => {
            if (typeof startMathDaily === 'function') { hide(); startMathDaily(); }
        });
        el.querySelector('#mh-q-placement')?.addEventListener('click', () => {
            if (typeof startMathPlacement === 'function') { hide(); startMathPlacement(); }
        });
    }

    function _handleWinClick(win) {
        switch (win.type) {
            case 'fluency':
                if (typeof startMathFluency === 'function') { hide(); startMathFluency(); }
                break;
            case 'lesson':
                if (win.data) _launchLesson(win.data.grade, win.data.unit, win.data.lesson);
                // else: user needs to select from sidebar
                break;
            case 'daily':
                if (typeof startMathDaily === 'function') { hide(); startMathDaily(); }
                break;
        }
    }

    function _launchLesson(grade, unit, lesson) {
        hide();
        if (typeof startMathLesson === 'function') {
            startMathLesson(grade, unit, lesson);
        }
    }

    // ── Today stats (best-effort) ────────────────────────────

    async function _loadTodayStats() {
        try {
            const data = await _fetchJSON('/api/math/academy/today-stats').catch(() => null);
            if (!data) return;
            _setStatVal('mh-stat-time', data.minutes_today ?? '—');
            _setStatVal('mh-stat-probs', data.problems_today ?? '—');
            _setStatVal('mh-stat-xp', data.xp_today != null ? `+${data.xp_today}` : '—');
        } catch (_) { /* silent */ }
    }

    function _setStatVal(id, val) {
        const el = document.querySelector(`#${id} .mh-stat-val`);
        if (el) el.textContent = String(val);
    }

    // ── Tiny utils ───────────────────────────────────────────

    function _timeOfDay() {
        const h = new Date().getHours();
        if (h < 12) return 'morning';
        if (h < 17) return 'afternoon';
        return 'evening';
    }

    return { show, hide, saveLastLesson: _saveLastLesson };
})();

// ── Public API ───────────────────────────────────────────────

/** @tag MATH @tag HOME_DASHBOARD */
function showMathHome() { _mathHome.show(); }

/** @tag MATH @tag HOME_DASHBOARD */
function hideMathHome() { _mathHome.hide(); }

/** Save last lesson for "continue" card. @tag MATH @tag HOME_DASHBOARD */
function mathHomeSaveLesson(grade, unit, lesson) {
    _mathHome.saveLastLesson(grade, unit, lesson);
}
