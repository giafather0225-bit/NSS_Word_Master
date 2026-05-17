/* ================================================================
   ckla-lesson-refs.js — CKLA reference tabs: Spelling, Grammar, Morphology
   Section: Academy
   Dependencies: ckla-lesson.js (state vars + shared utils)
   API endpoints: /api/academy/ckla/spelling/{unit},
                  /api/academy/ckla/grammar/{unit},
                  /api/academy/ckla/morphology/{unit}
   ================================================================ */


/* ── Reference tabs: Spelling / Grammar / Morphology ──────────────────────── */

/** Render Spelling reference tab for the current unit. @tag ACADEMY CKLA */
async function _renderSpelling() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const unit = _cklaLesson?.domain_num;
  if (!unit) { el.innerHTML = '<div class="ckla-empty">No unit data.</div>'; return; }

  if (!_cklaSpellingCache) {
    el.innerHTML = '<div class="ckla-loading">Loading...</div>';
    try {
      const r = await fetch(`/api/academy/ckla/spelling/${unit}`);
      _cklaSpellingCache = await r.json();
    } catch {
      el.innerHTML = '<div class="ckla-empty">Could not load spelling data.</div>';
      return;
    }
  }

  const { weeks } = _cklaSpellingCache;
  if (!weeks || weeks.length === 0) {
    const msg = unit === 1
      ? 'Unit 1 is a review unit — new spelling patterns begin in Unit 2.'
      : 'No spelling data available for this unit.';
    el.innerHTML = `<div class="ckla-empty">${msg}</div>`;
    return;
  }

  const sectionsHtml = weeks.map(w => {
    if (!w.words.length && !w.challenge_words.length) {
      return `
      <div class="ckla-spell-week">
        <div class="ckla-ref-week-label">Week ${w.week}</div>
        <div class="ckla-empty">No spelling data available</div>
      </div>`;
    }
    const wordChips = w.words.map(word =>
      `<span class="ckla-word-chip">${_esc(word)}</span>`
    ).join('');
    const challengeChips = w.challenge_words.map(word =>
      `<span class="ckla-word-chip ckla-challenge-chip">${_esc(word)}</span>`
    ).join('');
    const patternHtml = w.pattern
      ? `<div class="ckla-ref-pattern">Pattern: <strong>${_esc(w.pattern)}</strong></div>`
      : '';
    const challengeSection = w.challenge_words.length
      ? `<div class="ckla-ref-sublabel">Challenge Words</div><div class="ckla-word-chips">${challengeChips}</div>`
      : '';
    const weekJson = JSON.stringify(w).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
    return `
      <div class="ckla-spell-week">
        <div class="ckla-spell-week-top">
          <div class="ckla-ref-week-label">Week ${w.week}</div>
          <button class="ckla-spell-practice-btn"
                  onclick='startSpellingPractice(${weekJson}, ${unit})'>
            <i data-lucide="pencil-line" width="13" height="13"></i> Practice
          </button>
        </div>
        ${patternHtml}
        <div class="ckla-word-chips">${wordChips}</div>
        ${challengeSection}
      </div>`;
  }).join('');

  el.innerHTML = `
    <div class="ckla-ref-header">
      <span class="ckla-ref-title">Spelling Words</span>
      <span class="ckla-ref-unit">Unit ${unit}</span>
    </div>
    ${sectionsHtml}`;
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** Render Grammar reference tab for the current unit. @tag ACADEMY CKLA */
async function _renderGrammar() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const unit = _cklaLesson?.domain_num;
  if (!unit) { el.innerHTML = '<div class="ckla-empty">No unit data.</div>'; return; }

  if (!_cklaGrammarCache) {
    el.innerHTML = '<div class="ckla-loading">Loading...</div>';
    try {
      const r = await fetch(`/api/academy/ckla/grammar/${unit}`);
      _cklaGrammarCache = await r.json();
    } catch {
      el.innerHTML = '<div class="ckla-empty">Could not load grammar data.</div>';
      return;
    }
  }

  const { topics } = _cklaGrammarCache;
  if (!topics || topics.length === 0) {
    const msg = unit === 1
      ? 'Unit 1 is a review unit — grammar topics begin in Unit 2.'
      : 'No grammar topics available for this unit.';
    el.innerHTML = `<div class="ckla-empty">${msg}</div>`;
    return;
  }

  const itemsHtml = topics.map(t =>
    `<li class="ckla-topic-item">${_esc(t)}</li>`
  ).join('');

  el.innerHTML = `
    <div class="ckla-ref-header">
      <span class="ckla-ref-title">Grammar</span>
      <span class="ckla-ref-unit">Unit ${unit}</span>
    </div>
    <div class="ckla-vocab-card">
      <ul class="ckla-topic-list">${itemsHtml}</ul>
    </div>`;
}

/** Render Morphology reference tab for the current unit. @tag ACADEMY CKLA */
async function _renderMorphology() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const unit = _cklaLesson?.domain_num;
  if (!unit) { el.innerHTML = '<div class="ckla-empty">No unit data.</div>'; return; }

  if (!_cklaMorphCache) {
    el.innerHTML = '<div class="ckla-loading">Loading...</div>';
    try {
      const r = await fetch(`/api/academy/ckla/morphology/${unit}`);
      _cklaMorphCache = await r.json();
    } catch {
      el.innerHTML = '<div class="ckla-empty">Could not load morphology data.</div>';
      return;
    }
  }

  const { topics } = _cklaMorphCache;
  if (!topics || topics.length === 0) {
    const msg = unit === 1
      ? 'Unit 1 is a review unit — morphology topics begin in Unit 2.'
      : 'No morphology topics available for this unit.';
    el.innerHTML = `<div class="ckla-empty">${msg}</div>`;
    return;
  }

  const itemsHtml = topics.map(t =>
    `<li class="ckla-topic-item">${_esc(t)}</li>`
  ).join('');

  el.innerHTML = `
    <div class="ckla-ref-header">
      <span class="ckla-ref-title">Morphology</span>
      <span class="ckla-ref-unit">Unit ${unit}</span>
    </div>
    <div class="ckla-vocab-card">
      <ul class="ckla-topic-list">${itemsHtml}</ul>
    </div>`;
}
