/* ================================================================
   ckla-lesson.js — CKLA lesson shell: state, tab routing, timer, shared utils
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
/** @type {Object.<number, number>} Attempt count per question_id (max 2) */
let _cklaAttempts = {};
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
  _cklaAttempts  = {};
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

  view.innerHTML = `
    <div class="ckla-lesson-header">
      <button class="ckla-back-btn" id="ckla-lesson-back-btn">← Domain ${data.domain_num}</button>
      <div class="ckla-lesson-info">
        <span class="ckla-lesson-tag">Lesson ${data.lesson_num} · ${escapeHtml(data.domain_title)}</span>
        <span class="ckla-lesson-htitle">${escapeHtml(data.title)}</span>
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

  const backBtn = document.getElementById('ckla-lesson-back-btn');
  if (backBtn) backBtn.addEventListener('click', () => loadCKLALessons(data.domain_num));

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
