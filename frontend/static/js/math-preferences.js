/* ================================================================
   math-preferences.js — Math Preferences modal
   Section: Math
   Dependencies: core.js
   API endpoints: GET /api/math/preferences, POST /api/math/preferences
   ================================================================ */

// ── Open ──────────────────────────────────────────────────────

/** @tag MATH @tag SETTINGS */
async function openMathPreferences() {
    const existing = document.getElementById('math-prefs-modal');
    if (existing) { existing.remove(); }

    const overlay = document.createElement('div');
    overlay.id = 'math-prefs-modal';
    overlay.className = 'mprefs-overlay';
    overlay.innerHTML = `
        <div class="mprefs-card">
            <div class="mprefs-header">
                <h2 class="mprefs-title">Math Settings</h2>
                <button class="mprefs-close" id="mprefs-close" aria-label="Close">
                    <i data-lucide="x" style="width:18px;height:18px;stroke-width:2"></i>
                </button>
            </div>
            <div class="mprefs-body" id="mprefs-body">
                <div class="mprefs-loading">Loading…</div>
            </div>
        </div>`;
    document.body.appendChild(overlay);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
    });
    document.getElementById('mprefs-close').addEventListener('click', () => overlay.remove());

    try {
        const prefs = await fetch('/api/math/preferences').then(r => r.json());
        _renderPrefsBody(prefs);
    } catch (_) {
        document.getElementById('mprefs-body').innerHTML =
            '<p class="mprefs-err">Could not load settings.</p>';
    }
}

// ── Render body ───────────────────────────────────────────────

/** @tag MATH @tag SETTINGS */
function _renderPrefsBody(prefs) {
    const body = document.getElementById('mprefs-body');
    if (!body) return;

    const grades = ['G2', 'G3', 'G4', 'G5', 'G6'];
    const gradeOptions = grades.map(g =>
        `<option value="${g}" ${prefs.default_grade === g ? 'selected' : ''}>${g.replace('G', 'Grade ')}</option>`
    ).join('');

    const targets = [1, 2, 3, 5, 10];
    const targetOptions = targets.map(n =>
        `<option value="${n}" ${prefs.fluency_daily_target === n ? 'selected' : ''}>${n} round${n > 1 ? 's' : ''} / day</option>`
    ).join('');

    body.innerHTML = `
        <div class="mprefs-field">
            <label class="mprefs-label" for="mprefs-grade">Default grade</label>
            <p class="mprefs-hint">Sets the starting grade in the Math sidebar.</p>
            <select class="mprefs-select" id="mprefs-grade">${gradeOptions}</select>
        </div>

        <div class="mprefs-field">
            <label class="mprefs-label" for="mprefs-fluency-target">Daily fluency target</label>
            <p class="mprefs-hint">How many fact fluency rounds to aim for each day.</p>
            <select class="mprefs-select" id="mprefs-fluency-target">${targetOptions}</select>
        </div>

        <div class="mprefs-field">
            <div class="mprefs-toggle-row">
                <div>
                    <div class="mprefs-label">Daily challenge</div>
                    <p class="mprefs-hint">Show the daily challenge card on the home screen.</p>
                </div>
                <button class="mprefs-toggle ${prefs.daily_challenge_enabled ? 'on' : ''}"
                        id="mprefs-daily-toggle"
                        aria-pressed="${prefs.daily_challenge_enabled}"
                        aria-label="Toggle daily challenge">
                    <span class="mprefs-toggle-thumb"></span>
                </button>
            </div>
        </div>

        <div class="mprefs-actions">
            <button class="mprefs-cancel" id="mprefs-cancel">Cancel</button>
            <button class="mprefs-save" id="mprefs-save">Save</button>
        </div>
    `;

    // Toggle
    const toggleBtn = document.getElementById('mprefs-daily-toggle');
    toggleBtn.addEventListener('click', () => {
        const on = toggleBtn.classList.toggle('on');
        toggleBtn.setAttribute('aria-pressed', String(on));
    });

    document.getElementById('mprefs-cancel').addEventListener('click', () => {
        document.getElementById('math-prefs-modal')?.remove();
    });
    document.getElementById('mprefs-save').addEventListener('click', _savePrefs);
}

// ── Save ──────────────────────────────────────────────────────

/** @tag MATH @tag SETTINGS */
async function _savePrefs() {
    const saveBtn = document.getElementById('mprefs-save');
    if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Saving…'; }

    const grade = document.getElementById('mprefs-grade')?.value;
    const target = parseInt(document.getElementById('mprefs-fluency-target')?.value, 10);
    const dailyOn = document.getElementById('mprefs-daily-toggle')?.classList.contains('on');

    try {
        const res = await fetch('/api/math/preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                default_grade: grade,
                fluency_daily_target: target,
                daily_challenge_enabled: dailyOn,
            }),
        });
        if (!res.ok) throw new Error('bad response');

        // Apply grade to sidebar immediately
        const gradeSel = document.getElementById('math-grade-select');
        if (gradeSel && grade) {
            gradeSel.value = grade;
            gradeSel.dispatchEvent(new Event('change'));
        }

        document.getElementById('math-prefs-modal')?.remove();

        // Refresh math home if visible
        if (typeof showMathHome === 'function') showMathHome();
    } catch (_) {
        if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Save'; }
        const body = document.getElementById('mprefs-body');
        if (body) {
            const err = body.querySelector('.mprefs-err') || document.createElement('p');
            err.className = 'mprefs-err';
            err.textContent = 'Save failed. Please try again.';
            body.appendChild(err);
        }
    }
}
