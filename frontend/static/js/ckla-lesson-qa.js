/* ================================================================
   ckla-lesson-qa.js — CKLA Q&A tab, Word Work tab, difficulty prompt,
                       domain test banner
   Section: Academy
   Dependencies: ckla-lesson.js (state vars + shared utils)
   API endpoints: /api/academy/ckla/questions/{id}/answer,
                  /api/academy/ckla/lessons/{id}/difficulty,
                  /api/academy/ckla/domains,
                  /api/academy/ckla/badges/check
   ================================================================ */


/* ── Tab: Questions ────────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA */
function _renderQuestions() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const qs = _cklaLesson.questions;
  if (!qs.length) { el.innerHTML = '<div class="ckla-empty">No questions for this lesson.</div>'; return; }

  const allAnswered = qs.every(q => _cklaResponses[q.id]);
  const qaDone = _cklaLesson.progress?.qa_done;

  const q    = qs[_cklaQIdx];
  const resp = _cklaResponses[q.id];
  const kindCls = { Literal: 'kind-lit', Inferential: 'kind-inf', Evaluative: 'kind-eva' };
  const scoreIcon = ['<i data-lucide="x-circle" style="width:14px;height:14px;vertical-align:-2px;stroke-width:1.5"></i>', '△', '<i data-lucide="check-circle" style="width:14px;height:14px;vertical-align:-2px;stroke-width:1.5"></i>'];

  el.innerHTML = `
    ${(allAnswered || qaDone) ? '<div class="ckla-done-badge" style="margin-bottom:12px">Q&amp;A complete</div>' : ''}
    <div class="ckla-q-nav">
      <span class="ckla-q-counter">Question ${_cklaQIdx + 1} of ${qs.length}</span>
      <span class="ckla-kind-badge ${kindCls[q.kind] || ''}">${q.kind}</span>
    </div>
    <div class="ckla-question-card">
      <div class="ckla-question-text">${_esc(q.question)}</div>
      ${resp ? `
        <div class="ckla-feedback ckla-score-${resp.ai_score}">
          <span class="ckla-score-pill">${scoreIcon[resp.ai_score]}</span>
          <span class="ckla-feedback-text">${_esc(resp.ai_feedback)}</span>
        </div>` : `
        <textarea class="ckla-answer-input" id="ckla-ans" rows="4"
                  placeholder="Write your answer here…"></textarea>`}
      <div class="ckla-q-arrows">
        <button class="ckla-arrow-btn" onclick="_cklaQNav(-1)" ${_cklaQIdx === 0 ? 'disabled' : ''}>◀ Prev</button>
        ${resp
          ? (() => {
              const attempts = _cklaAttempts[q.id] || 0;
              const canRetry  = resp.ai_score < 2 && attempts < 2 && !qaDone;
              return canRetry
                ? `<button class="ckla-retry-btn" onclick="_retryQuestion(${q.id})">Try Again</button>`
                : `<button class="ckla-arrow-btn" onclick="_cklaQNav(1)" ${_cklaQIdx === qs.length - 1 ? 'disabled' : ''}>Next ▶</button>`;
            })()
          : `<button class="ckla-submit-btn" id="ckla-sub-btn" onclick="_submitAnswer(${q.id})">Submit →</button>`}
      </div>
    </div>`;
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag ACADEMY CKLA */
function _cklaQNav(dir) {
  _cklaQIdx = Math.max(0, Math.min(_cklaLesson.questions.length - 1, _cklaQIdx + dir));
  _renderQuestions();
}

/**
 * Clear the last response for a question so the student can try again.
 * Only available when score < 2 and attempts < 2.
 * @param {number} questionId
 * @tag ACADEMY CKLA
 */
function _retryQuestion(questionId) {
  delete _cklaResponses[questionId];
  _renderQuestions();
}

/** Submit answer and await AI grading. @tag ACADEMY CKLA AI */
async function _submitAnswer(questionId) {
  const input = document.getElementById('ckla-ans');
  const answer = input ? input.value.trim() : '';
  if (!answer) {
    if (input) input.style.borderColor = 'var(--color-error)';
    return;
  }
  const btn = document.getElementById('ckla-sub-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Grading…'; }

  try {
    const res = await fetch(`/api/academy/ckla/questions/${questionId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_answer: answer }),
    });
    if (res.ok) {
      _cklaResponses[questionId] = await res.json();
      _cklaAttempts[questionId] = (_cklaAttempts[questionId] || 0) + 1;
      const allAnswered = _cklaLesson.questions.every(q => _cklaResponses[q.id]);
      if (allAnswered && !_cklaLesson.progress?.qa_done) {
        const prog = await _postProgress({ qa_done: true });
        if (prog) { _cklaLesson.progress = prog; _maybeShowDifficultyPrompt(prog); }
      }
      _renderQuestions();
    } else {
      if (btn) { btn.disabled = false; btn.textContent = 'Submit →'; }
    }
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = 'Submit →'; }
    console.error('CKLA submit failed:', e);
  }
}


/* ── Tab: Word Work ────────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA */
function _renderWordWork() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const word = _cklaLesson.word_work_word;
  if (!word) { el.innerHTML = '<div class="ckla-empty">No Word Work for this lesson.</div>'; return; }

  const prog = _cklaLesson.progress;
  const vw = _cklaLesson.vocab.find(v => v.word === word) || { word };

  const hintContent = [
    vw.definition ? `<em>${_esc(vw.definition)}</em>` : '',
    vw.example_1  ? `Example: "${_esc(vw.example_1)}"` : '',
  ].filter(Boolean).join('<br>');

  el.innerHTML = `
    <div class="ckla-ww-card">
      <div class="ckla-ww-label">Word Work Focus</div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div class="ckla-ww-word">${_esc(vw.word)}</div>
        ${vw.part_of_speech ? `<span class="ckla-pos-pill">${_esc(vw.part_of_speech)}</span>` : ''}
        <button class="ckla-audio-btn" data-audio-url="${_esc(vw.audio_url || '')}" data-word="${_esc(vw.word)}" title="Listen"><i data-lucide="volume-2" style="width:14px;height:14px"></i></button>
        ${!prog.word_work_done ? `<button class="ckla-hint-btn" id="ckla-hint-btn" onclick="_cklaToggleHint()">${_cklaHintVisible ? 'Hide Hint' : 'Hint'}</button>` : ''}
      </div>
      <div class="ckla-ww-hint${_cklaHintVisible ? ' visible' : ''}" id="ckla-ww-hint">${hintContent}</div>
      ${prog.word_work_done
        ? (vw.definition ? `<div class="ckla-ww-def">${_esc(vw.definition)}</div>` : '')
        : ''}
      <div class="ckla-ww-prompt">
        <label class="ckla-ww-prompt-label">
          Write your own sentence using <strong>${_esc(word)}</strong>:
        </label>
        ${prog.word_work_done
          ? '<div class="ckla-done-badge" style="margin-top:8px">Word Work complete</div>'
          : `<textarea class="ckla-answer-input" id="ckla-ww-ans" rows="3" placeholder="Write a sentence using this word…"></textarea>
             <div class="ckla-ww-hint-note" style="font-size:.75rem;color:var(--text-hint);margin-top:4px">Your sentence must include <strong>${_esc(word)}</strong></div>`}
      </div>
    </div>
    ${!prog.word_work_done ? `
    <div class="ckla-action-bar">
      <button class="ckla-primary-btn" id="ckla-ww-submit" onclick="_markWordWorkDone()">Submit</button>
    </div>` : ''}`;
  el.querySelectorAll('.ckla-audio-btn').forEach(btn => {
    btn.addEventListener('click', () => _cklaAudio(btn.dataset.audioUrl, btn.dataset.word));
  });
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag ACADEMY CKLA */
function _cklaToggleHint() {
  _cklaHintVisible = !_cklaHintVisible;
  const hint = document.getElementById('ckla-ww-hint');
  const btn  = document.getElementById('ckla-hint-btn');
  if (hint) hint.classList.toggle('visible', _cklaHintVisible);
  if (btn)  btn.textContent = _cklaHintVisible ? 'Hide Hint' : 'Hint';
}

/** @tag ACADEMY CKLA */
async function _markWordWorkDone() {
  const input = document.getElementById('ckla-ww-ans');
  const answer = input ? input.value.trim() : '';
  if (!answer) {
    if (input) input.style.borderColor = 'var(--review-primary)';
    return;
  }
  const btn = document.getElementById('ckla-ww-submit');
  if (btn) { btn.disabled = true; btn.textContent = 'Checking…'; }

  const prog = await _postProgress({ word_work_done: true, word_work_answer: answer });
  if (prog) {
    _cklaLesson.progress = prog;
    _renderWordWork();
    _maybeShowDifficultyPrompt(prog);
  } else {
    if (btn) { btn.disabled = false; btn.textContent = 'Submit'; }
    const ta = document.getElementById('ckla-ww-ans');
    if (ta) {
      ta.style.borderColor = 'var(--review-primary)';
      ta.addEventListener('input', () => { ta.style.borderColor = ''; }, { once: true });
    }
  }
}


/* ── Difficulty rating ─────────────────────────────────────────────────────── */

/**
 * Show celebration + difficulty prompt when lesson completes for the first time.
 * @tag ACADEMY CKLA
 */
function _maybeShowDifficultyPrompt(prog) {
  if (!prog || !prog.completed) return;
  if (typeof cklaNav !== 'undefined') {
    fetch(`/api/academy/ckla/badges/check?grade=${cklaNav.grade}`, { method: 'POST' }).catch(() => {});
  }
  if (prog.difficulty_rating) return;
  if (document.getElementById('ckla-diff-overlay')) return;

  const view = document.getElementById('ckla-view');
  if (!view) return;

  const burst = document.createElement('div');
  burst.id = 'ckla-complete-burst';
  burst.className = 'ckla-complete-burst';
  burst.innerHTML = `<div class="ckla-burst-inner"><i data-lucide="star" class="ckla-burst-star"></i><div class="ckla-burst-text">Lesson Complete!</div></div>`;
  if (typeof lucide !== 'undefined') lucide.createIcons({ el: burst });
  view.appendChild(burst);

  setTimeout(() => {
    burst.remove();
    const overlay = document.createElement('div');
    overlay.id = 'ckla-diff-overlay';
    overlay.className = 'ckla-diff-overlay';
    overlay.innerHTML = `
      <div class="ckla-diff-box">
        <div class="ckla-diff-title">How was this lesson?</div>
        <div class="ckla-diff-btns">
          <button class="ckla-diff-btn ckla-diff-btn--easy"
                  onclick="_rateDifficulty('easy')">Easy</button>
          <button class="ckla-diff-btn ckla-diff-btn--neutral"
                  onclick="_rateDifficulty('neutral')">Just right</button>
          <button class="ckla-diff-btn ckla-diff-btn--hard"
                  onclick="_rateDifficulty('hard')">Hard</button>
        </div>
      </div>`;
    if (document.getElementById('ckla-view')) {
      document.getElementById('ckla-view').appendChild(overlay);
    }
  }, 1600);
}

/** Submit difficulty rating and dismiss overlay. @tag ACADEMY CKLA */
async function _rateDifficulty(rating) {
  const overlay = document.getElementById('ckla-diff-overlay');
  if (overlay) overlay.remove();
  if (_cklaLesson?.progress) _cklaLesson.progress.difficulty_rating = rating;
  try {
    await fetch(`/api/academy/ckla/lessons/${_cklaLesson.id}/difficulty`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating }),
    });
  } catch (e) {
    console.warn('CKLA difficulty rating failed:', e);
  }
  _maybeShowDomainTestBanner();
}

/**
 * After lesson completion, check if all lessons in the domain are done.
 * If so, inject a Domain Test CTA banner into #ckla-view.
 * @tag ACADEMY CKLA
 */
async function _maybeShowDomainTestBanner() {
  const domainNum = _cklaLesson?.domain_num;
  if (!domainNum) return;
  const view = document.getElementById('ckla-view');
  if (!view) return;
  if (view.querySelector('.ckla-domain-test-banner')) return;

  try {
    const grade = (typeof cklaNav !== 'undefined' && cklaNav.grade) ? cklaNav.grade : 3;
    const res = await fetch(`/api/academy/ckla/domains?grade=${grade}`);
    if (!res.ok) return;
    const data = await res.json();
    const domain = (data.domains || []).find(d => d.domain_num === domainNum);
    if (!domain || !domain.all_complete) return;

    const banner = document.createElement('div');
    banner.className = 'ckla-domain-test-banner';
    banner.innerHTML = `
      <div class="ckla-domain-test-banner-text">
        <div class="ckla-domain-test-banner-title">Domain Test Unlocked!</div>
        <div class="ckla-domain-test-banner-sub">You finished all lessons in Domain ${domainNum}. Ready to test your knowledge?</div>
      </div>
      <button class="ckla-domain-test-banner-btn" onclick="openDomainTest(${domainNum})">Take Test</button>
    `;
    view.insertBefore(banner, view.firstChild);
  } catch (e) {
    console.warn('Domain test banner check failed:', e);
  }
}
