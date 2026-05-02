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
/** @type {string} Font size class: sm / md / lg */
let _cklaFontSize = localStorage.getItem('ckla_font_size') || 'md';
/** @type {boolean} Vocab quiz mode active */
let _cklaVocabQuizMode = false;
/** @type {number} Current quiz question index */
let _cklaVocabQuizIdx = 0;
/** @type {number} Quiz correct answer count */
let _cklaVocabQuizScore = 0;
/** @type {Array} Generated quiz questions [{word, definition, choices:[]}] */
let _cklaVocabQuizQuestions = [];
/** @type {boolean} Hint visible in Word Work tab */
let _cklaHintVisible = false;
/** @type {Array} Text blocks from current passage for per-paragraph TTS */
let _cklaPassageBlocks = [];

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

/* ── ③ Reference tab cache ─────────────────────────────────────────────────── */
/** @type {object|null} Cached spelling data for current unit */
let _cklaSpellingCache = null;
/** @type {object|null} Cached grammar data for current unit */
let _cklaGrammarCache = null;
/** @type {object|null} Cached morphology data for current unit */
let _cklaMorphCache = null;


/* ── Lesson shell ──────────────────────────────────────────────────────────── */

/** Render full lesson view (tabs + first tab content). @tag ACADEMY CKLA */
function renderCKLALesson(data) {
  _cklaLesson    = data;
  _cklaTab       = 'reading';
  _cklaVocabIdx  = 0;
  _cklaQIdx      = 0;
  _cklaResponses = {};
  _cklaVocabQuizMode      = false;
  _cklaVocabQuizIdx       = 0;
  _cklaVocabQuizScore     = 0;
  _cklaVocabQuizQuestions = [];
  _cklaHintVisible        = false;
  _cklaPassageBlocks      = [];
  _cklaSpellingCache      = null;
  _cklaGrammarCache       = null;
  _cklaMorphCache         = null;
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
      <span class="ckla-tab-sep" aria-hidden="true"></span>
      <button class="ckla-tab ckla-tab-ref" id="tab-spelling"   onclick="switchCKLATab('spelling')">Spelling</button>
      <button class="ckla-tab ckla-tab-ref" id="tab-grammar"    onclick="switchCKLATab('grammar')">Grammar</button>
      <button class="ckla-tab ckla-tab-ref" id="tab-morphology" onclick="switchCKLATab('morphology')">Morphology</button>
    </div>
    <div id="ckla-tab-content" class="ckla-tab-content"></div>`;

  _renderReading();
  _cklaUpdateTabLocks();
}

/** Disable non-reading tabs until reading is done. @tag ACADEMY CKLA */
function _cklaUpdateTabLocks() {
  const readDone = !!_cklaLesson?.progress?.reading_done;
  ['vocab', 'questions', 'word-work'].forEach(id => {
    const btn = document.getElementById(`tab-${id}`);
    if (!btn) return;
    btn.disabled = !readDone;
    btn.style.opacity = readDone ? '' : '0.45';
    btn.title = readDone ? '' : 'Complete reading first';
  });
}

/** Switch between lesson tabs. Reference tabs (spelling/grammar/morphology) bypass the reading_done lock. @tag ACADEMY CKLA */
function switchCKLATab(tab) {
  const refTabs = new Set(['spelling', 'grammar', 'morphology']);
  // Block core tabs until reading is done; reference tabs are always accessible
  if (!refTabs.has(tab) && tab !== 'reading' && !_cklaLesson?.progress?.reading_done) return;
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
    spelling: _renderSpelling,
    grammar: _renderGrammar,
    morphology: _renderMorphology,
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
  btn.textContent = _cklaTTSPlaying ? 'Stop' : 'Listen All';
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

  // Store blocks so _cklaReadParagraph can access content by index
  _cklaPassageBlocks = blocks;

  let paraIdx = 0;
  const html = blocks.map(b => {
    if (b.type === 'marker') {
      return `<div class="ckla-image-marker">${_esc(b.content)}</div>`;
    }
    const idx = paraIdx++;
    return `<p id="ckla-para-${idx}" class="ckla-para" onclick="_cklaReadParagraph(${idx})" title="Tap to listen">${_esc(b.content)}</p>`;
  }).join('');

  const fontBtns = ['sm','md','lg'].map(s =>
    `<button class="ckla-font-btn${_cklaFontSize === s ? ' active' : ''}" data-size="${s}" onclick="_cklaSetFontSize('${s}')">${s === 'sm' ? 'A-' : s === 'lg' ? 'A+' : 'A'}</button>`
  ).join('');

  el.innerHTML = `
    <div class="ckla-reading-toolbar">
      <div class="ckla-timer-wrap">
        <span class="ckla-timer-display" id="ckla-timer-display">${_cklaFmtTime(_cklaTimerSec)}</span>
        ${!prog.reading_done ? `
          <button class="ckla-timer-btn" id="ckla-timer-btn" onclick="_cklaToggleTimer()">
            ${_cklaTimerRunning ? 'Pause' : 'Start'}
          </button>
        ` : ''}
      </div>
      <div class="ckla-font-size-ctrl">${fontBtns}</div>
      <div class="ckla-reading-tools">
        <button class="ckla-tts-btn" id="ckla-tts-btn" onclick="_cklaReadAloud()">Listen All</button>
        <span class="ckla-char-count">${chars.toLocaleString()} chars</span>
      </div>
    </div>
    <div class="ckla-passage-wrap">
      <div class="ckla-passage ckla-font-${_cklaFontSize}">${html}</div>
    </div>
    <div class="ckla-action-bar">
      ${prog.reading_done
        ? `<span class="ckla-done-badge">Reading complete</span>`
        : `<button class="ckla-primary-btn" onclick="_markReadingDone()">Done Reading${_cklaTimerSec > 0 ? ' (' + _cklaFmtTime(_cklaTimerSec) + ')' : ''}</button>`}
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
  if (prog) {
    _cklaLesson.progress = prog;
    _renderReading();
    _cklaUpdateTabLocks();
    _maybeShowDifficultyPrompt(prog);
  }
}


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
        ${w.audio_url ? `<button class="ckla-audio-btn" onclick="_cklaAudio('${w.audio_url}')" title="Listen"><i data-lucide="volume-2" style="width:14px;height:14px"></i></button>` : ''}
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
  if (typeof lucide !== 'undefined') lucide.createIcons();
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
        ${vw.audio_url ? `<button class="ckla-audio-btn" onclick="_cklaAudio('${vw.audio_url}')" title="Listen"><i data-lucide="volume-2" style="width:14px;height:14px"></i></button>` : ''}
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
  }
}


/* ── Difficulty rating ─────────────────────────────────────────────────────── */

/**
 * Show celebration + difficulty prompt when lesson completes for the first time.
 * @tag ACADEMY CKLA
 */
function _maybeShowDifficultyPrompt(prog) {
  if (!prog || !prog.completed) return;
  if (prog.difficulty_rating) return;
  if (document.getElementById('ckla-diff-overlay')) return;

  const view = document.getElementById('ckla-view');
  if (!view) return;

  // Brief celebration flash (auto-dismisses after 1.5s then shows rating)
  const burst = document.createElement('div');
  burst.id = 'ckla-complete-burst';
  burst.className = 'ckla-complete-burst';
  burst.innerHTML = `<div class="ckla-burst-inner"><span class="ckla-burst-star">★</span><div class="ckla-burst-text">Lesson Complete!</div></div>`;
  view.appendChild(burst);

  setTimeout(() => {
    burst.remove();
    // Now show difficulty rating overlay
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
    if (res.ok) return await res.json();
    if (res.status === 400) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail || 'Could not save. Please try again.';
      _cklaShowError(msg);
    }
    return null;
  } catch (e) {
    console.error('CKLA progress update failed:', e);
    return null;
  }
}

/** Show a non-blocking inline error near the active action bar. @tag ACADEMY CKLA */
function _cklaShowError(msg) {
  const bar = document.querySelector('.ckla-action-bar');
  if (!bar) return;
  let errEl = bar.querySelector('.ckla-inline-error');
  if (!errEl) {
    errEl = document.createElement('div');
    errEl.className = 'ckla-inline-error';
    bar.appendChild(errEl);
  }
  errEl.textContent = msg;
  errEl.style.display = 'block';
  setTimeout(() => { if (errEl) errEl.style.display = 'none'; }, 4000);
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


/* ── Font size control ─────────────────────────────────────────────────────── */

/** Set reading font size and persist to localStorage. @tag ACADEMY CKLA */
function _cklaSetFontSize(size) {
  _cklaFontSize = size;
  localStorage.setItem('ckla_font_size', size);
  const pass = document.querySelector('.ckla-passage');
  if (pass) {
    pass.classList.remove('ckla-font-sm', 'ckla-font-md', 'ckla-font-lg');
    pass.classList.add(`ckla-font-${size}`);
  }
  document.querySelectorAll('.ckla-font-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.size === size);
  });
}


/* ── Per-paragraph TTS ─────────────────────────────────────────────────────── */

/** Play TTS for a single paragraph and highlight it. @tag ACADEMY CKLA TTS */
async function _cklaReadParagraph(idx) {
  if (_cklaTTSPlaying) { _cklaStopTTS(); return; }
  const block = _cklaPassageBlocks.filter(b => b.type === 'text')[idx];
  if (!block) return;

  _cklaTTSPlaying = true;
  _cklaHighlightPara(idx);
  _cklaUpdateTTSBtn();

  const text = block.content;
  try {
    if (!_isOffline()) {
      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice: 'en-US-AriaNeural' }),
        });
        if (res.ok) {
          const blob = await res.blob();
          const url  = URL.createObjectURL(blob);
          const audio = new Audio(url);
          _globalCurrentAudio = audio;
          await new Promise(r => { audio.onended = r; audio.onerror = r; audio.play().catch(r); });
          URL.revokeObjectURL(url);
          _globalCurrentAudio = null;
          _cklaTTSPlaying = false;
          _cklaClearHighlight();
          _cklaUpdateTTSBtn();
          return;
        }
      } catch (e) { console.warn('CKLA para TTS failed, using fallback:', e); }
    }
    if ('speechSynthesis' in window) {
      await new Promise(r => {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = 'en-US'; u.rate = 0.85; u.onend = r; u.onerror = r;
        window.speechSynthesis.speak(u);
      });
    }
  } catch (e) { console.error('CKLA para TTS error:', e); }

  _cklaTTSPlaying = false;
  _cklaClearHighlight();
  _cklaUpdateTTSBtn();
}

/** Highlight the paragraph at text-block index idx. @tag ACADEMY CKLA */
function _cklaHighlightPara(idx) {
  _cklaClearHighlight();
  const el = document.getElementById(`ckla-para-${idx}`);
  if (el) el.classList.add('ckla-para-active');
}

/** Remove paragraph highlight. @tag ACADEMY CKLA */
function _cklaClearHighlight() {
  document.querySelectorAll('.ckla-para-active').forEach(el => el.classList.remove('ckla-para-active'));
}


/* ── Vocab quiz (3 MC questions, pass = 2/3) ───────────────────────────────── */

/** Build 3 quiz questions and enter quiz mode. @tag ACADEMY CKLA */
function _startVocabQuiz() {
  const words = _cklaLesson.vocab.filter(w => w.definition);
  if (words.length < 2) { _markVocabDone(); return; }

  // Pick up to 3 target words
  const shuffled = [...words].sort(() => Math.random() - 0.5);
  const targets = shuffled.slice(0, Math.min(3, shuffled.length));

  _cklaVocabQuizQuestions = targets.map(target => {
    // 3 wrong choices from other words' definitions
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
    // Quiz finished
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

  // Brief flash on buttons
  document.querySelectorAll('.ckla-quiz-choice').forEach(btn => {
    btn.disabled = true;
    const choiceWord = q.choices.find(c => {
      // match by definition text shown
      return _esc(c.definition || c.word) === btn.textContent;
    });
  });

  // Show correct/wrong highlight then advance
  const btns = document.querySelectorAll('.ckla-quiz-choice');
  btns.forEach(btn => {
    // Find which choice this button represents by text
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
    el.innerHTML = '<div class="ckla-empty">No spelling data available for this unit.</div>';
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
    return `
      <div class="ckla-spell-week">
        <div class="ckla-ref-week-label">Week ${w.week}</div>
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
    el.innerHTML = '<div class="ckla-empty">No grammar topics available for this unit.</div>';
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
    el.innerHTML = '<div class="ckla-empty">No morphology topics available for this unit.</div>';
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
