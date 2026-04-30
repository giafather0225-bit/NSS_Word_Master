/* ================================================================
   math-kangaroo-result.js — Kangaroo exam result screen
   Section: Math
   Dependencies: core.js, math-kangaroo.js
   API endpoints: none (renders submit response)
   ================================================================ */

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
            <td>${_mathEsc(s.name)}</td>
            <td>${s.correct}/${s.total}</td>
            <td>${s.points_earned}</td>
            <td>${s.max_points}</td>
        </tr>
    `).join('');
    const topicRows = (data.topic_breakdown || []).map(t => `
        <tr>
            <td>${_mathEsc(t.topic)}</td>
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
                    <div class="kang-grade-label">${_mathEsc(data.grade_label || '')}</div>
                </div>
                <div class="kang-result-meta">
                    <div class="kang-result-time"><i data-lucide="clock"></i> ${_mathEsc(data.time_spent_formatted || '00:00')}</div>
                    <div class="kang-result-xp"><i data-lucide="zap"></i> +${xp} XP</div>
                    ${data.perfect ? `<div class="kang-result-perfect"><i data-lucide="trophy"></i> Perfect!</div>` : ''}
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
    if (window.lucide) lucide.createIcons();
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
    document.getElementById('kang-back-math').addEventListener('click', () => startMathKangaroo());
}

/** @tag MATH @tag KANGAROO */
function _resReviewCard(q) {
    const icon = q.is_correct
        ? '<span class="kang-rv-ok"><i data-lucide="check"></i></span>'
        : '<span class="kang-rv-no"><i data-lucide="x"></i></span>';
    const imageOnly = !!(q.image_only && q.image);
    const opts = imageOnly
        ? ['A','B','C','D','E'].map(k => {
            const isStudent = q.student_answer === k;
            const isCorrect = q.correct_answer === k;
            let cls = '';
            if (isCorrect) cls = 'is-correct';
            else if (isStudent) cls = 'is-wrong';
            return `<li class="kang-rv-opt kang-rv-opt-compact ${cls}"><strong>${k}</strong></li>`;
        }).join('')
        : Object.entries(q.options || {}).map(([k, v]) => {
            const isStudent = q.student_answer === k;
            const isCorrect = q.correct_answer === k;
            let cls = '';
            if (isCorrect) cls = 'is-correct';
            else if (isStudent) cls = 'is-wrong';
            return `<li class="kang-rv-opt ${cls}"><strong>(${k})</strong> ${_mathEsc(v)}</li>`;
        }).join('');
    const imgHtml = imageOnly
        ? `<div class="kang-img kang-img-full"><img src="${q.image}" alt="${_mathEsc(q.image_description || q.question_text || '')}" loading="lazy"></div>`
        : q.image
            ? `<div class="kang-img"><img src="${q.image}" alt="${_mathEsc(q.image_description || '')}" loading="lazy"></div>`
            : q.image_description
                ? `<div class="kang-img kang-img-desc">${_mathEsc(q.image_description)}</div>`
                : '';
    const qTextHtml = imageOnly ? '' : `<div class="kang-rv-q">${_mathEsc(q.question_text)}</div>`;
    const studentLine = q.student_answer
        ? `<p>Your answer: <strong>(${_mathEsc(q.student_answer)})</strong></p>`
        : `<p><em>Unanswered</em></p>`;
    return `
        <article class="kang-review-card">
            <header class="kang-review-card-head">
                <div>${icon} <strong>Q${q.number}</strong> · ${q.points} pts · ${_mathEsc(q.topic)}</div>
                <span class="kang-review-toggle">▾</span>
            </header>
            <div class="kang-review-card-body">
                ${qTextHtml}
                ${imgHtml}
                <ul class="kang-rv-opts ${imageOnly ? 'kang-rv-opts-compact' : ''}">${opts}</ul>
                ${studentLine}
                <p>Correct answer: <strong>(${_mathEsc(q.correct_answer)})</strong></p>
                ${q.solution ? `<div class="kang-rv-sol"><strong>Solution:</strong> ${_mathEsc(q.solution)}</div>` : ''}
            </div>
        </article>
    `;
}

window.showKangarooResult = showKangarooResult;

// ── Past-paper result ──────────────────────────────────────

/** @tag MATH @tag KANGAROO @tag PP */
function showKangarooPdfResult(data, setInfo) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const pct = data.percentage || 0;
    const xp = data.xp_earned || 0;
    const title = data.title || (setInfo && setInfo.title) || 'Past Paper';
    const pdfFile = data.pdf_file || (setInfo && setInfo.pdf_file) || '';

    const secRows = (data.section_breakdown || []).map(s => `
        <tr>
            <td>${_mathEsc(s.name)}</td>
            <td>${s.correct}/${s.total}</td>
            <td>${s.score}/${s.max} pts</td>
        </tr>
    `).join('');

    const detailRows = (data.details || []).map(d => {
        let icon = '<i data-lucide="minus"></i>', cls = 'unanswered';
        if (d.is_correct) { icon = '<i data-lucide="check"></i>'; cls = 'correct'; }
        else if (d.student) { icon = '<i data-lucide="x"></i>'; cls = 'wrong'; }
        const you = d.student || '—';
        return `
            <tr class="kang-detail-${cls}">
                <td>${/^[A-Za-z]/.test(String(d.question)) ? _mathEsc(d.question) : 'Q' + _mathEsc(d.question)}</td>
                <td>${_mathEsc(you)}</td>
                <td>${_mathEsc(d.correct)}</td>
                <td>${icon}</td>
                <td>${d.points} pts</td>
            </tr>`;
    }).join('');

    const pctClass = _resPctClass(pct);
    const timeStr = data.time_spent_formatted ||
        ((data.time_spent_seconds != null)
            ? `${Math.floor(data.time_spent_seconds/60)}m ${data.time_spent_seconds%60}s`
            : '');

    stage.innerHTML = `
        <div class="kang-wrap kang-result kang-pp-result">
            <header class="kang-result-head">
                <h1>${_mathEsc(title)} — Results</h1>
                <div class="kang-result-score ${pctClass}">
                    <div class="kang-score-big">${data.score} / ${data.max_score}</div>
                    <div class="kang-score-pct">${pct}%</div>
                </div>
                <div class="kang-result-meta">
                    ${timeStr ? `<span>Time: ${_mathEsc(timeStr)}</span>` : ''}
                    ${xp > 0 ? `<span class="kang-xp-badge">XP earned: +${xp}</span>` : ''}
                    ${data.is_new_best ? `<span class="kang-newbest">New Best!</span>` : ''}
                </div>
                <div class="kang-result-counts">
                    <span><i data-lucide="check"></i> ${data.correct_count || 0} correct</span>
                    <span><i data-lucide="x"></i> ${data.wrong_count || 0} wrong</span>
                    <span><i data-lucide="minus"></i> ${data.unanswered_count || 0} unanswered</span>
                </div>
            </header>

            <section class="kang-section-breakdown">
                <h2>Section Breakdown</h2>
                <table class="kang-result-table">
                    <thead><tr><th>Section</th><th>Correct</th><th>Score</th></tr></thead>
                    <tbody>${secRows}</tbody>
                </table>
            </section>

            <section class="kang-detail-review">
                <h2>Answer Review</h2>
                <table class="kang-result-table kang-detail-table">
                    <thead><tr><th>#</th><th>You</th><th>Correct</th><th></th><th>Pts</th></tr></thead>
                    <tbody>${detailRows}</tbody>
                </table>
            </section>

            <div class="kang-result-actions">
                ${pdfFile ? `<a class="kang-btn kang-btn-secondary" href="${_mathEsc(pdfFile)}" target="_blank" rel="noopener">View PDF</a>` : ''}
                <button class="kang-btn kang-btn-primary" id="kang-pp-retry">Try Again</button>
                <button class="kang-btn kang-btn-secondary" id="kang-pp-back">Back to List</button>
            </div>
        </div>
    `;
    if (window.lucide) lucide.createIcons();

    const setId = (setInfo && setInfo.set_id) || data.set_id;
    document.getElementById('kang-pp-retry').addEventListener('click', () => {
        if (typeof startKangarooPdfExam === 'function' && setId) {
            startKangarooPdfExam(setId, 'test');
        }
    });
    document.getElementById('kang-pp-back').addEventListener('click', () => {
        if (typeof startMathKangaroo === 'function') startMathKangaroo();
    });
}

window.showKangarooPdfResult = showKangarooPdfResult;
