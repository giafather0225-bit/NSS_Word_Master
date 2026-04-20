/* ================================================================
   math-kangaroo-result.js — Kangaroo exam result screen
   Section: Math
   Dependencies: core.js, math-kangaroo.js
   API endpoints: none (renders submit response)
   ================================================================ */

/** @tag MATH @tag KANGAROO */
function _resEsc(s) {
    return String(s ?? '').replace(/[&<>"']/g, ch => (
        { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]
    ));
}

/** @tag MATH @tag KANGAROO */
function _resPctClass(pct) {
    if (pct >= 90) return 'pct-out';
    if (pct >= 80) return 'pct-ex';
    if (pct >= 70) return 'pct-great';
    if (pct >= 60) return 'pct-good';
    return 'pct-low';
}

/** @tag MATH @tag KANGAROO */
function showKangarooResult(data) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const pct = data.percentage || 0;
    const xp = data.xp_earned || 0;
    const secRows = (data.sections || []).map(s => `
        <tr>
            <td>${_resEsc(s.name)}</td>
            <td>${s.correct}/${s.total}</td>
            <td>${s.points_earned}</td>
            <td>${s.max_points}</td>
        </tr>
    `).join('');
    const topicRows = (data.topic_breakdown || []).map(t => `
        <tr>
            <td>${_resEsc(t.topic)}</td>
            <td>${t.correct}</td>
            <td>${t.total}</td>
            <td>${t.rate.toFixed(1)}%</td>
        </tr>
    `).join('');
    const reviewHtml = (data.questions_review || []).map(q => _resReviewCard(q)).join('');
    stage.innerHTML = `
        <div class="kang-wrap kang-result">
            <header class="kang-result-head">
                <div class="kang-result-score">
                    <div class="kang-score-big">${data.score} / ${data.max_score}</div>
                    <div class="kang-score-bar"><div class="kang-score-fill ${_resPctClass(pct)}" style="width:${pct}%"></div></div>
                    <div class="kang-grade-label">${_resEsc(data.grade_label || '')}</div>
                </div>
                <div class="kang-result-meta">
                    <div class="kang-result-time">⏱ ${_resEsc(data.time_spent_formatted || '00:00')}</div>
                    <div class="kang-result-xp">⭐ +${xp} XP</div>
                    ${data.perfect ? `<div class="kang-result-perfect">🏆 Perfect!</div>` : ''}
                </div>
            </header>

            <section class="kang-result-block">
                <h3>Section Breakdown</h3>
                <table class="kang-table">
                    <thead><tr><th>Section</th><th>Correct</th><th>Points</th><th>Max</th></tr></thead>
                    <tbody>${secRows}</tbody>
                </table>
            </section>

            <section class="kang-result-block">
                <h3>Topic Breakdown</h3>
                <table class="kang-table">
                    <thead><tr><th>Topic</th><th>Correct</th><th>Total</th><th>Rate</th></tr></thead>
                    <tbody>${topicRows}</tbody>
                </table>
            </section>

            <section class="kang-result-block">
                <div class="kang-review-head">
                    <h3>Question Review</h3>
                    <div class="kang-review-actions">
                        <button class="kang-btn kang-btn-ghost" id="kang-expand-all">Expand All</button>
                        <button class="kang-btn kang-btn-ghost" id="kang-collapse-all">Collapse All</button>
                    </div>
                </div>
                <div class="kang-review">${reviewHtml}</div>
            </section>

            <footer class="kang-result-foot">
                <button class="kang-btn kang-btn-secondary" id="kang-try-another">Try Another Set</button>
                <button class="kang-btn kang-btn-ghost" id="kang-back-math">Back to Math</button>
            </footer>
        </div>
    `;
    stage.querySelectorAll('.kang-review-card').forEach(card => {
        const head = card.querySelector('.kang-review-card-head');
        head.addEventListener('click', () => card.classList.toggle('is-open'));
    });
    document.getElementById('kang-expand-all').addEventListener('click', () => {
        stage.querySelectorAll('.kang-review-card').forEach(c => c.classList.add('is-open'));
    });
    document.getElementById('kang-collapse-all').addEventListener('click', () => {
        stage.querySelectorAll('.kang-review-card').forEach(c => c.classList.remove('is-open'));
    });
    document.getElementById('kang-try-another').addEventListener('click', () => startMathKangaroo());
    document.getElementById('kang-back-math').addEventListener('click', () => {
        if (typeof showMathHome === 'function') showMathHome();
        else startMathKangaroo();
    });
}

/** @tag MATH @tag KANGAROO */
function _resReviewCard(q) {
    const icon = q.is_correct ? '<span class="kang-rv-ok">✓</span>' : '<span class="kang-rv-no">✗</span>';
    const opts = Object.entries(q.options || {}).map(([k, v]) => {
        const isStudent = q.student_answer === k;
        const isCorrect = q.correct_answer === k;
        let cls = '';
        if (isCorrect) cls = 'is-correct';
        else if (isStudent) cls = 'is-wrong';
        return `<li class="kang-rv-opt ${cls}"><strong>(${k})</strong> ${_resEsc(v)}</li>`;
    }).join('');
    const imgHtml = q.image_svg
        ? `<div class="kang-img" role="img" aria-label="${_resEsc(q.image_description || '')}">${q.image_svg}</div>`
        : '';
    const studentLine = q.student_answer
        ? `<p>Your answer: <strong>(${_resEsc(q.student_answer)})</strong></p>`
        : `<p><em>Unanswered</em></p>`;
    return `
        <article class="kang-review-card">
            <header class="kang-review-card-head">
                <div>${icon} <strong>Q${q.number}</strong> · ${q.points} pts · ${_resEsc(q.topic)}</div>
                <span class="kang-review-toggle">▾</span>
            </header>
            <div class="kang-review-card-body">
                <div class="kang-rv-q">${_resEsc(q.question_text)}</div>
                ${imgHtml}
                <ul class="kang-rv-opts">${opts}</ul>
                ${studentLine}
                <p>Correct answer: <strong>(${_resEsc(q.correct_answer)})</strong></p>
                ${q.solution ? `<div class="kang-rv-sol"><strong>Solution:</strong> ${_resEsc(q.solution)}</div>` : ''}
            </div>
        </article>
    `;
}

window.showKangarooResult = showKangarooResult;
