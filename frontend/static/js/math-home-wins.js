/* ================================================================
   math-home-wins.js — Math home win-card + weekly-section helpers
   Section: Math
   Dependencies: math-home.js (calls these globals)
   ================================================================ */

// ── Shared escape utility ─────────────────────────────────────

function _mhEsc(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

// ── Win card data builder ─────────────────────────────────────

/** @tag MATH @tag HOME_DASHBOARD */
function mathHomeBuildWins(fluency, daily, lastLesson) {
    const wins = [];

    const fluencyDone = fluency && fluency.today_rounds >= fluency.daily_target;
    wins.push({
        type: 'fluency',
        tag: 'Fact Fluency',
        title: fluencyDone
            ? `${fluency.today_rounds} rounds complete`
            : `${fluency ? fluency.today_rounds : 0}/${fluency ? fluency.daily_target : 3} rounds done`,
        subtitle: fluencyDone ? 'Great work!' : 'Build your math speed',
        done: fluencyDone,
        cta: fluencyDone ? 'Done' : 'Go',
    });

    const hasLesson = !!lastLesson;
    wins.push({
        type: 'lesson',
        tag: 'Academy',
        title: hasLesson
            ? lastLesson.lesson.replace(/_/g, ' ')
            : 'Start a new lesson',
        subtitle: hasLesson
            ? `${lastLesson.unit.replace(/_/g, ' ')}`
            : 'Pick a lesson from the sidebar',
        done: false,
        cta: hasLesson ? 'Continue' : 'Choose',
        data: lastLesson,
    });

    const dailyDone = daily && daily.completed;
    wins.push({
        type: 'daily',
        tag: 'Daily Challenge',
        title: dailyDone
            ? `Score: ${daily.score}/${daily.total}`
            : (daily && daily.exists ? `${daily.total} problems` : 'Not available today'),
        subtitle: dailyDone ? 'Challenge complete!' : 'One problem set',
        done: dailyDone,
        cta: (daily && daily.exists && !dailyDone) ? 'Start' : (dailyDone ? 'Done' : '—'),
    });

    return wins;
}

// ── Win card HTML ─────────────────────────────────────────────

/** @tag MATH @tag HOME_DASHBOARD */
function mathHomeWinCard(win, i) {
    const doneClass = win.done ? 'done' : '';
    const disabledAttr = (win.cta === '—' || win.done) ? 'disabled' : '';
    return `
        <div class="mh-win-card ${doneClass}">
            <div class="mh-win-top">
                <span class="mh-win-tag">${_mhEsc(win.tag)}</span>
                ${win.done ? `<span class="mh-win-check"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></span>` : ''}
            </div>
            <div class="mh-win-title">${_mhEsc(win.title)}</div>
            <div class="mh-win-subtitle">${_mhEsc(win.subtitle)}</div>
            <button class="mh-win-btn" data-win="${i}" ${disabledAttr}>${_mhEsc(win.cta)}</button>
        </div>
    `;
}

// ── Continue / start section HTML ─────────────────────────────

/** @tag MATH @tag HOME_DASHBOARD */
function mathHomeContinueSection(last) {
    return `
        <section class="mh-section">
            <h2 class="mh-section-title">Continue learning</h2>
            <div class="mh-continue-card">
                <div class="mh-continue-info">
                    <div class="mh-continue-eyebrow">${_mhEsc(last.unit.replace(/_/g, ' '))}</div>
                    <div class="mh-continue-title">${_mhEsc(last.lesson.replace(/_/g, ' '))}</div>
                </div>
                <button class="mh-continue-btn" id="mh-continue-btn">
                    Continue
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                </button>
            </div>
        </section>
    `;
}

/** @tag MATH @tag HOME_DASHBOARD */
function mathHomeStartSection() {
    return `
        <section class="mh-section">
            <div class="mh-start-hint">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                Select a grade, unit, and lesson from the sidebar to start learning.
            </div>
        </section>
    `;
}

// ── Weekly analytics section HTML ─────────────────────────────

/** @tag MATH @tag HOME_DASHBOARD */
function mathHomeWeeklySection(w) {
    const days = w.days || [];
    const totals = w.totals || {};
    const maxProbs = Math.max(...days.map(d => d.total), 1);

    const bars = days.map(d => {
        const heightPct = Math.round((d.total / maxProbs) * 100);
        const accPct = d.total ? Math.round((d.correct / d.total) * 100) : 0;
        const todayLabel = new Date().toLocaleDateString('en-US', { weekday: 'short' }).slice(0, 3);
        const isToday = d.label === todayLabel;
        return `
            <div class="mh-weekly-bar-col${isToday ? ' today' : ''}">
                <div class="mh-weekly-bar-wrap">
                    <div class="mh-weekly-bar" style="height:${heightPct}%" title="${d.total} problems · ${accPct}% correct"></div>
                </div>
                <div class="mh-weekly-bar-label">${_mhEsc(d.label)}</div>
            </div>`;
    }).join('');

    const strengthPills = (w.strengths || []).map(s =>
        `<span class="mh-weekly-pill strength">${_mhEsc(s)}</span>`
    ).join('');
    const needsPills = (w.needs_work || []).map(s =>
        `<span class="mh-weekly-pill needs">${_mhEsc(s)}</span>`
    ).join('');
    const hasTags = strengthPills || needsPills;

    return `
        <section class="mh-section">
            <h2 class="mh-section-title">This week</h2>
            <div class="mh-weekly-card">
                <div class="mh-weekly-stats-row">
                    <div class="mh-weekly-stat">
                        <span class="mh-weekly-stat-val">${totals.problems || 0}</span>
                        <span class="mh-weekly-stat-label">problems</span>
                    </div>
                    <div class="mh-weekly-stat">
                        <span class="mh-weekly-stat-val">${totals.accuracy_pct || 0}%</span>
                        <span class="mh-weekly-stat-label">accuracy</span>
                    </div>
                    <div class="mh-weekly-stat">
                        <span class="mh-weekly-stat-val">${totals.fluency_rounds || 0}</span>
                        <span class="mh-weekly-stat-label">fluency rounds</span>
                    </div>
                    <div class="mh-weekly-stat">
                        <span class="mh-weekly-stat-val">${totals.daily_challenges || 0}/7</span>
                        <span class="mh-weekly-stat-label">daily challenges</span>
                    </div>
                </div>
                <div class="mh-weekly-chart">
                    ${bars}
                </div>
                ${hasTags ? `
                <div class="mh-weekly-tags">
                    ${strengthPills ? `<div class="mh-weekly-tag-row"><span class="mh-weekly-tag-label">Strengths</span>${strengthPills}</div>` : ''}
                    ${needsPills ? `<div class="mh-weekly-tag-row"><span class="mh-weekly-tag-label">Review more</span>${needsPills}</div>` : ''}
                </div>` : ''}
            </div>
        </section>
    `;
}
