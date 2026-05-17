/* ================================================================
   ckla-lesson-vocab.js — CKLA Vocab tab: card browser, audio, quiz
   Section: Academy
   Dependencies: ckla-lesson.js (state vars + shared utils)
   API endpoints: /api/tts
   ================================================================ */


/* ── Tab: Vocabulary ───────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA */
function _renderVocab() {
  if (_cklaVocabQuizMode) { _renderVocabQuiz(); return; }

  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const words = _cklaLesson.vocab;
  if (!words.length) { el.innerHTML = '<div class="ckla-empty">No vocabulary for this lesson.</div>'; return; }

  const w    = words[_cklaVocabIdx];
  const prog = _cklaLesson.progress;
  const atEnd = _cklaVocabIdx === words.length - 1;

  el.innerHTML = `
    <div class="ckla-vocab-nav">${_cklaVocabIdx + 1} / ${words.length}</div>
    <div class="ckla-vocab-card">
      <div class="ckla-vocab-top">
        <span class="ckla-vocab-word">${_esc(w.word)}</span>
        ${w.part_of_speech ? `<span class="ckla-pos-pill">${_esc(w.part_of_speech)}</span>` : ''}
        <button class="ckla-audio-btn" data-audio-url="${_esc(w.audio_url || '')}" data-word="${_esc(w.word)}" title="Listen"><i data-lucide="volume-2" style="width:14px;height:14px"></i></button>
      </div>
      <div class="ckla-vocab-def">${_esc(w.definition) || '<em>No definition available</em>'}</div>
      ${w.example_1 ? `<div class="ckla-vocab-ex">"${_esc(w.example_1)}"</div>` : ''}
    </div>
    <div class="ckla-vocab-arrows">
      <button class="ckla-arrow-btn" onclick="_cklaVocabNav(-1)" ${_cklaVocabIdx === 0 ? 'disabled' : ''}>◀</button>
      <button class="ckla-arrow-btn" onclick="_cklaVocabNav(1)"  ${atEnd ? 'disabled' : ''}>▶</button>
    </div>
    <div class="ckla-action-bar">
      ${prog.vocab_done
        ? '<span class="ckla-done-badge">Words complete</span>'
        : (atEnd
            ? `<button class="ckla-primary-btn" onclick="_startVocabQuiz()">Take Quiz (3 questions)</button>`
            : `<button class="ckla-primary-btn" style="opacity:.5" title="Swipe through all words first" disabled>Take Quiz</button>`
          )}
    </div>`;
  el.querySelectorAll('.ckla-audio-btn').forEach(btn => {
    btn.addEventListener('click', () => _cklaAudio(btn.dataset.audioUrl, btn.dataset.word));
  });
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/** @tag ACADEMY CKLA */
function _cklaVocabNav(dir) {
  _cklaVocabIdx = Math.max(0, Math.min(_cklaLesson.vocab.length - 1, _cklaVocabIdx + dir));
  _renderVocab();
}

/**
 * Play audio for a CKLA word. Static MP3 first, edge-tts fallback when url is absent.
 * @param {string} url  - /static/audio/ckla/{id}.mp3 (may be empty string)
 * @param {string} word - raw word text for TTS fallback
 * @tag ACADEMY CKLA
 */
async function _cklaAudio(url, word) {
  if (url) {
    try { new Audio(url).play(); return; } catch (e) { /* fall through to TTS */ }
  }
  try {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: word }),
    });
    if (!res.ok) return;
    const blob = await res.blob();
    new Audio(URL.createObjectURL(blob)).play();
  } catch (e) { console.warn('CKLA audio fallback failed:', e); }
}

/** @tag ACADEMY CKLA */
async function _markVocabDone() {
  const prog = await _postProgress({ vocab_done: true });
  if (prog) { _cklaLesson.progress = prog; _renderVocab(); _maybeShowDifficultyPrompt(prog); }
}


/* ── Vocab quiz (3 MC questions, pass = 2/3) ───────────────────────────────── */

/** Build 3 quiz questions and enter quiz mode. @tag ACADEMY CKLA */
function _startVocabQuiz() {
  const words = _cklaLesson.vocab.filter(w => w.definition);
  if (words.length < 2) { _markVocabDone(); return; }

  const shuffled = [...words].sort(() => Math.random() - 0.5);
  const targets = shuffled.slice(0, Math.min(3, shuffled.length));

  _cklaVocabQuizQuestions = targets.map(target => {
    const others = words.filter(w => w.id !== target.id);
    const wrong  = others.sort(() => Math.random() - 0.5).slice(0, 3);
    const choices = [...wrong, target].sort(() => Math.random() - 0.5);
    return { word: target.word, correctId: target.id, choices };
  });
  _cklaVocabQuizMode  = true;
  _cklaVocabQuizIdx   = 0;
  _cklaVocabQuizScore = 0;
  _renderVocabQuiz();
}

/** Render current quiz question. @tag ACADEMY CKLA */
function _renderVocabQuiz() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;

  const total = _cklaVocabQuizQuestions.length;
  if (_cklaVocabQuizIdx >= total) {
    const pass = _cklaVocabQuizScore >= Math.ceil(total * 2 / 3);
    el.innerHTML = `
      <div class="ckla-quiz-result">
        <div class="ckla-quiz-score">${_cklaVocabQuizScore} / ${total}</div>
        <div class="ckla-quiz-verdict">${pass ? 'Well done!' : 'Keep practicing!'}</div>
        ${pass
          ? `<button class="ckla-primary-btn" style="margin-top:16px" onclick="_markVocabDone()">Words complete</button>`
          : `<button class="ckla-primary-btn" style="margin-top:16px" onclick="_startVocabQuiz()">Try again</button>`}
      </div>`;
    return;
  }

  const q = _cklaVocabQuizQuestions[_cklaVocabQuizIdx];
  const choiceHtml = q.choices.map(c =>
    `<button class="ckla-quiz-choice" onclick="_submitVocabQuiz(${c.id})">${_esc(c.definition || c.word)}</button>`
  ).join('');

  el.innerHTML = `
    <div class="ckla-q-nav">
      <span class="ckla-q-counter">Question ${_cklaVocabQuizIdx + 1} of ${total}</span>
      <span style="font-size:.8rem;color:var(--text-hint)">${_cklaVocabQuizScore} correct so far</span>
    </div>
    <div class="ckla-quiz-card">
      <div class="ckla-quiz-prompt">Which definition matches <strong>${_esc(q.word)}</strong>?</div>
      <div class="ckla-quiz-choices">${choiceHtml}</div>
    </div>`;
}

/** Handle choice selection for vocab quiz. @tag ACADEMY CKLA */
function _submitVocabQuiz(selectedId) {
  const q = _cklaVocabQuizQuestions[_cklaVocabQuizIdx];
  const correct = selectedId === q.correctId;
  if (correct) _cklaVocabQuizScore++;

  const btns = document.querySelectorAll('.ckla-quiz-choice');
  btns.forEach(btn => {
    btn.disabled = true;
    const c = q.choices.find(c => btn.textContent === (c.definition || c.word));
    if (c) {
      if (c.id === q.correctId) btn.classList.add('ckla-quiz-correct');
      else if (c.id === selectedId) btn.classList.add('ckla-quiz-wrong');
    }
  });

  setTimeout(() => {
    _cklaVocabQuizIdx++;
    _renderVocabQuiz();
  }, 900);
}
