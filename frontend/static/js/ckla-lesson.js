/* ================================================================
   ckla-lesson.js — CKLA G3 lesson tabs (Reading/Words/Questions/Word Work)
   Section: Academy
   Dependencies: ckla.js (for back nav), tts-client.js
   API endpoints: /api/academy/ckla/lessons/{id}/progress,
                  /api/academy/ckla/questions/{id}/answer
   ================================================================ */

/** @type {object|null} Current lesson data from API */
let _cklaLesson = null;
/** @type {string} Active tab */
let _cklaTab = 'reading';
/** @type {number} Current vocab card index */
let _cklaVocabIdx = 0;
/** @type {number} Current question index */
let _cklaQIdx = 0;
/** @type {Object.<number, object>} Cached AI responses keyed by question_id */
let _cklaResponses = {};

/* ── ① Reading Timer state ─────────────────────────────────────────────────── */
/** @type {number|null} Timer interval ID */
let _cklaTimerId = null;
/** @type {number} Elapsed seconds */
let _cklaTimerSec = 0;
/** @type {boolean} Timer running */
let _cklaTimerRunning = false;

/* ── ② TTS state ───────────────────────────────────────────────────────────── */
/** @type {boolean} TTS currently playing */
let _cklaTTSPlaying = false;


/* ── Lesson shell ──────────────────────────────────────────────────────────── */

/** Render full lesson view (tabs + first tab content). @tag ACADEMY CKLA */
function renderCKLALesson(data) {
  _cklaLesson    = data;
  _cklaTab       = 'reading';
  _cklaVocabIdx  = 0;
  _cklaQIdx      = 0;
  _cklaResponses = {};
  _cklaStopTimer();

  const view = document.getElementById('ckla-view');
  if (!view) return;

  const backFn = `loadCKLALessons(${data.domain_num})`;
  view.innerHTML = `
    <div class="ckla-lesson-header">
      <button class="ckla-back-btn" onclick="${backFn}">← Domain ${data.domain_num}</button>
      <div class="ckla-lesson-info">
        <span class="ckla-lesson-tag">Lesson ${data.lesson_num} · ${data.domain_title}</span>
        <span class="ckla-lesson-htitle">${data.title}</span>
      </div>
    </div>
    <div class="ckla-tabs" role="tablist">
      <button class="ckla-tab active" id="tab-reading"   onclick="switchCKLATab('reading')">Read</button>
      <button class="ckla-tab"        id="tab-vocab"     onclick="switchCKLATab('vocab')">Words</button>
      <button class="ckla-tab"        id="tab-questions" onclick="switchCKLATab('questions')">Q&amp;A</button>
      <button class="ckla-tab"        id="tab-word-work" onclick="switchCKLATab('word-work')">Word Work</button>
    </div>
    <div id="ckla-tab-content" class="ckla-tab-content"></div>`;

  _renderReading();
}

/** Switch between the four lesson tabs. @tag ACADEMY CKLA */
function switchCKLATab(tab) {
  // Stop timer if leaving reading tab
  if (_cklaTab === 'reading' && tab !== 'reading') {
    _cklaPauseTimer();
  }
  // Stop TTS on tab switch
  _cklaStopTTS();

  _cklaTab = tab;
  document.querySelectorAll('.ckla-tab').forEach(btn =>
    btn.classList.toggle('active', btn.id === `tab-${tab}`)
  );
  const fns = {
    reading: _renderReading,
    vocab: _renderVocab,
    questions: _renderQuestions,
    'word-work': _renderWordWork,
  };
  (fns[tab] || _renderReading)();
}


/* ── ① Timer helpers ───────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA */
function _cklaStartTimer() {
  if (_cklaTimerRunning) return;
  _cklaTimerRunning = true;
  _cklaTimerId = setInterval(() => {
    _cklaTimerSec++;
    const el = document.getElementById('ckla-timer-display');
    if (el) el.textContent = _cklaFmtTime(_cklaTimerSec);
  }, 1000);
}

/** @tag ACADEMY CKLA */
function _cklaPauseTimer() {
  if (_cklaTimerId) {
    clearInterval(_cklaTimerId);
    _cklaTimerId = null;
  }
  _cklaTimerRunning = false;
}

/** @tag ACADEMY CKLA */
function _cklaStopTimer() {
  _cklaPauseTimer();
  _cklaTimerSec = 0;
}

/** @tag ACADEMY CKLA */
function _cklaFmtTime(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}


/* ── ② TTS helpers ─────────────────────────────────────────────────────────── */

/** Play passage text via edge-tts or browser fallback. @tag ACADEMY CKLA TTS */
async function _cklaReadAloud() {
  if (_cklaTTSPlaying) {
    _cklaStopTTS();
    return;
  }
  const passage = _cklaLesson?.passage;
  if (!passage) return;

  // Extract clean text (skip title line, remove § markers)
  const lines = passage.split('\n');
  const cleanLines = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    if (line.startsWith('§')) continue;
    cleanLines.push(line);
  }
  const text = cleanLines.join(' ').replace(/\s+/g, ' ').trim();
  if (!text) return;

  _cklaTTSPlaying = true;
  _cklaUpdateTTSBtn();

  // Pause timer during TTS (listening, not reading)
  const wasTimerRunning = _cklaTimerRunning;
  _cklaPauseTimer();

  try {
    // Try server TTS first (edge-tts)
    if (!_isOffline()) {
      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text, voice: 'en-US-AriaNeural' }),
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          _globalCurrentAudio = audio;
          await new Promise((resolve) => {
            audio.onended = resolve;
            audio.onerror = resolve;
            audio.play().catch(resolve);
          });
          URL.revokeObjectURL(url);
          _globalCurrentAudio = null;
          _cklaTTSPlaying = false;
          _cklaUpdateTTSBtn();
          if (wasTimerRunning) _cklaStartTimer();
          return;
        }
      } catch (e) {
        console.warn('CKLA TTS server failed, using browser fallback:', e);
      }
    }

    // Browser fallback
    if (typeof _speakLocal === 'function') {
      await _speakLocal(text, { rate: 0.85 });
    } else if ('speechSynthesis' in window) {
      await new Promise((resolve) => {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = 'en-US';
        u.rate = 0.85;
        u.onend = resolve;
        u.onerror = resolve;
        window.speechSynthesis.speak(u);
      });
    }
  } catch (e) {
    console.error('CKLA TTS error:', e);
  }

  _cklaTTSPlaying = false;
  _cklaUpdateTTSBtn();
  if (wasTimerRunning) _cklaStartTimer();
}

/** @tag ACADEMY CKLA TTS */
function _cklaStopTTS() {
  _cklaTTSPlaying = false;
  if (_globalCurrentAudio) {
    _globalCurrentAudio.pause();
    _globalCurrentAudio.currentTime = 0;
    _globalCurrentAudio = null;
  }
  if (window.speechSynthesis?.speaking) {
    window.speechSynthesis.cancel();
  }
  _cklaUpdateTTSBtn();
}

/** @tag ACADEMY CKLA TTS */
function _cklaUpdateTTSBtn() {
  const btn = document.getElementById('ckla-tts-btn');
  if (!btn) return;
  btn.textContent = _cklaTTSPlaying ? '⏹ Stop' : '🔊 Listen';
  btn.classList.toggle('ckla-tts-playing', _cklaTTSPlaying);
}


/* ── Tab: Reading (① timer + ② TTS integrated) ────────────────────────────── */

/** Parse raw passage string into renderable blocks. @tag ACADEMY CKLA */
function _parsePassage(raw) {
  const lines = raw.split('\n');
  const blocks = [];
  let buf = [];

  const flush = () => {
    if (!buf.length) return;
    let text = '';
    for (let i = 0; i < buf.length; i++) {
      const line = buf[i];
      if (i === 0) { text = line; continue; }
      text = text.endsWith('-') ? text + line : text + ' ' + line;
    }
    text = text.trim();
    if (text) blocks.push({ type: 'text', content: text });
    buf = [];
  };

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    if (line.startsWith('§')) {
      flush();
      blocks.push({ type: 'marker', content: line.replace(/^§\s*/, '') });
      continue;
    }

    buf.push(line);

    const endsWithPunct = /[.!?'"""]\s*$/.test(line);
    const nextLine = (lines[i + 1] || '').trim();
    const nextIsNewSentence = /^[A-Z"']/.test(nextLine) && !nextLine.startsWith('§');
    if (endsWithPunct && nextIsNewSentence && buf.join(' ').length > 80) {
      flush();
    }
  }
  flush();
  return blocks;
}

/** @tag ACADEMY CKLA */
function _renderReading() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const prog   = _cklaLesson.progress;
  const blocks = _parsePassage(_cklaLesson.passage);
  const chars  = _cklaLesson.passage_chars || 0;

  const html = blocks.map(b => {
    if (b.type === 'marker') {
      return `<div class="ckla-image-marker">${_esc(b.content)}</div>`;
    }
    return `<p>${_esc(b.content)}</p>`;
  }).join('');

  el.innerHTML = `
    <div class="ckla-reading-toolbar">
      <div class="ckla-timer-wrap">
        <span class="ckla-timer-icon">⏱</span>
        <span class="ckla-timer-display" id="ckla-timer-display">${_cklaFmtTime(_cklaTimerSec)}</span>
        ${!prog.reading_done ? `
          <button class="ckla-timer-btn" id="ckla-timer-btn" onclick="_cklaToggleTimer()">
            ${_cklaTimerRunning ? 'Pause' : 'Start'}
          </button>
        ` : ''}
      </div>
      <div class="ckla-reading-tools">
        <button class="ckla-tts-btn" id="ckla-tts-btn" onclick="_cklaReadAloud()">🔊 Listen</button>
        <span class="ckla-char-count">${chars.toLocaleString()} chars</span>
      </div>
    </div>
    <div class="ckla-passage-wrap">
      <div class="ckla-passage">${html}</div>
    </div>
    <div class="ckla-action-bar">
      ${prog.reading_done
        ? `<span class="ckla-done-badge">✓ Reading complete${prog.reading_done_at ? ' · ' + _cklaFmtTime(_cklaTimerSec) : ''}</span>`
        : `<button class="ckla-primary-btn" onclick="_markReadingDone()">✓ Done Reading${_cklaTimerSec > 0 ? ' (' + _cklaFmtTime(_cklaTimerSec) + ')' : ''}</button>`}
    </div>`;

  // Auto-start timer if not done
  if (!prog.reading_done && !_cklaTimerRunning) {
    _cklaStartTimer();
  }
}

/** @tag ACADEMY CKLA */
function _cklaToggleTimer() {
  if (_cklaTimerRunning) {
    _cklaPauseTimer();
  } else {
    _cklaStartTimer();
  }
  const btn = document.getElementById('ckla-timer-btn');
  if (btn) btn.textContent = _cklaTimerRunning ? 'Pause' : 'Start';
}

/** @tag ACADEMY CKLA */
async function _markReadingDone() {
  _cklaPauseTimer();
  _cklaStopTTS();
  const prog = await _postProgress({ reading_done: true });
  if (prog) { _cklaLesson.progress = prog; _renderReading(); _maybeShowDifficultyPrompt(prog); }
}


/* ── Tab: Vocabulary ───────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA */
function _renderVocab() {
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
        ${w.audio_url ? `<button class="ckla-audio-btn" onclick="_cklaAudio('${w.audio_url}')" title="Listen">🔊</button>` : ''}
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
        ? '<span class="ckla-done-badge">✓ Words complete</span>'
        : `<button class="ckla-primary-btn" onclick="_markVocabDone()"${!atEnd ? ' style="opacity:.5" title="Swipe through all words first"' : ''}>
             ✓ All Words Reviewed
           </button>`}
    </div>`;
}

/** @tag ACADEMY CKLA */
function _cklaVocabNav(dir) {
  _cklaVocabIdx = Math.max(0, Math.min(_cklaLesson.vocab.length - 1, _cklaVocabIdx + dir));
  _renderVocab();
}

/** @tag ACADEMY CKLA */
function _cklaAudio(url) {
  try { new Audio(url).play(); } catch (e) { console.warn('CKLA audio failed:', e); }
}

/** @tag ACADEMY CKLA */
async function _markVocabDone() {
  const prog = await _postProgress({ vocab_done: true });
  if (prog) { _cklaLesson.progress = prog; _renderVocab(); _maybeShowDifficultyPrompt(prog); }
}


/* ── Tab: Questions ────────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA */
function _renderQuestions() {
  const el = document.getElementById('ckla-tab-content');
  if (!el) return;
  const qs = _cklaLesson.questions;
  if (!qs.length) { el.innerHTML = '<div class="ckla-empty">No questions for this lesson.</div>'; return; }

  const q    = qs[_cklaQIdx];
  const resp = _cklaResponses[q.id];
  const kindCls = { Literal: 'kind-lit', Inferential: 'kind-inf', Evaluative: 'kind-eva' };
  const scoreIcon = ['✗', '△', '✓'];

  el.innerHTML = `
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
          ? `<button class="ckla-arrow-btn" onclick="_cklaQNav(1)" ${_cklaQIdx === qs.length - 1 ? 'disabled' : ''}>Next ▶</button>`
          : `<button class="ckla-submit-btn" id="ckla-sub-btn" onclick="_submitAnswer(${q.id})">Submit →</button>`}
      </div>
    </div>`;
}

/** @tag ACADEMY CKLA */
function _cklaQNav(dir) {
  _cklaQIdx = Math.max(0, Math.min(_cklaLesson.questions.length - 1, _cklaQIdx + dir));
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

  el.innerHTML = `
    <div class="ckla-ww-card">
      <div class="ckla-ww-label">Word Work Focus</div>
      <div class="ckla-ww-word">${_esc(vw.word)}</div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        ${vw.part_of_speech ? `<span class="ckla-pos-pill">${_esc(vw.part_of_speech)}</span>` : ''}
        ${vw.audio_url ? `<button class="ckla-audio-btn" onclick="_cklaAudio('${vw.audio_url}')">🔊 Listen</button>` : ''}
      </div>
      ${vw.definition ? `<div class="ckla-ww-def">${_esc(vw.definition)}</div>` : ''}
      ${vw.example_1  ? `<div class="ckla-vocab-ex">"${_esc(vw.example_1)}"</div>` : ''}
      <div class="ckla-ww-prompt">
        <label class="ckla-ww-prompt-label">
          Write your own sentence using <strong>${_esc(word)}</strong>:
        </label>
        <textarea class="ckla-answer-input" id="ckla-ww-ans" rows="3"
                  placeholder="Write a sentence…"></textarea>
      </div>
    </div>
    <div class="ckla-action-bar">
      ${prog.word_work_done
        ? '<span class="ckla-done-badge">✓ Word Work complete</span>'
        : '<button class="ckla-primary-btn" onclick="_markWordWorkDone()">✓ Done</button>'}
    </div>`;
}

/** @tag ACADEMY CKLA */
async function _markWordWorkDone() {
  const prog = await _postProgress({ word_work_done: true });
  if (prog) { _cklaLesson.progress = prog; _renderWordWork(); _maybeShowDifficultyPrompt(prog); }
}


/* ── Difficulty rating ─────────────────────────────────────────────────────── */

/**
 * Show difficulty prompt if lesson just became complete and hasn't been rated yet.
 * @tag ACADEMY CKLA
 */
function _maybeShowDifficultyPrompt(prog) {
  if (!prog || !prog.completed || prog.difficulty_rating) return;
  const existing = document.getElementById('ckla-diff-overlay');
  if (existing) return;

  const overlay = document.createElement('div');
  overlay.id = 'ckla-diff-overlay';
  overlay.className = 'ckla-diff-overlay';
  overlay.innerHTML = `
    <div class="ckla-diff-box">
      <div class="ckla-diff-title">Lesson complete! How was it?</div>
      <div class="ckla-diff-btns">
        <button class="ckla-diff-btn ckla-diff-btn--easy"
                onclick="_rateDifficulty('easy')">Easy</button>
        <button class="ckla-diff-btn ckla-diff-btn--neutral"
                onclick="_rateDifficulty('neutral')">Just right</button>
        <button class="ckla-diff-btn ckla-diff-btn--hard"
                onclick="_rateDifficulty('hard')">Hard</button>
      </div>
    </div>`;

  const view = document.getElementById('ckla-view');
  if (view) view.appendChild(overlay);
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
}


/* ── Shared helpers ────────────────────────────────────────────────────────── */

/** POST progress update, return updated progress dict or null on error. @tag ACADEMY CKLA */
async function _postProgress(body) {
  try {
    const res = await fetch(`/api/academy/ckla/lessons/${_cklaLesson.id}/progress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return res.ok ? await res.json() : null;
  } catch (e) {
    console.error('CKLA progress update failed:', e);
    return null;
  }
}

/** Escape HTML to prevent XSS. @tag SYSTEM */
function _esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
