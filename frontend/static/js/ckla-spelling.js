/* ================================================================
   ckla-spelling.js — CKLA Spelling Practice (TTS dictation mode)
   Section: CKLA
   Dependencies: ckla-lesson.js (cklaNav), tts-client.js
   API endpoints: /api/tts/word_only
   ================================================================ */

/**
 * Launch the spelling practice overlay for one week's word list.
 * @param {object} weekData  { week, pattern, words, challenge_words }
 * @param {number} unitNum   domain_num for the unit label
 * @tag ACADEMY CKLA SPELL
 */
function startSpellingPractice(weekData, unitNum) {
  const allWords = [...(weekData.words || []), ...(weekData.challenge_words || [])];
  if (!allWords.length) return;

  const state = {
    words:    allWords,
    index:    0,
    results:  [],   // { word, typed, correct }
    unitNum,
    week:     weekData.week,
    pattern:  weekData.pattern || '',
  };

  _spellBuildOverlay(state);
  _spellShowCurrent(state);
}

/* ── Overlay DOM ────────────────────────────────────────────────── */

function _spellBuildOverlay(state) {
  document.getElementById('ckla-spell-overlay')?.remove();

  const el = document.createElement('div');
  el.id  = 'ckla-spell-overlay';
  el.className = 'ckla-spell-overlay';
  el.innerHTML = `
    <div class="ckla-spell-box">
      <div class="ckla-spell-header">
        <div class="ckla-spell-meta">
          Unit ${state.unitNum} — Week ${state.week}
          ${state.pattern ? `<span class="ckla-spell-pattern">${_spEsc(state.pattern)}</span>` : ''}
        </div>
        <button class="ckla-spell-close" onclick="_spellClose()">
          <i data-lucide="x" width="16" height="16"></i>
        </button>
      </div>
      <div class="ckla-spell-progress-bar">
        <div class="ckla-spell-progress-fill" id="spell-prog-fill" style="width:0%"></div>
      </div>
      <div class="ckla-spell-body" id="spell-body"></div>
    </div>`;
  document.body.appendChild(el);
  if (typeof lucide !== 'undefined') lucide.createIcons();

  window._spellClose = () => {
    document.getElementById('ckla-spell-overlay')?.remove();
    delete window._spellClose;
    delete window._spellPlayCurrent;
    delete window._spellSubmit;
  };
}

/* ── Per-word screen ────────────────────────────────────────────── */

function _spellShowCurrent(state) {
  const body = document.getElementById('spell-body');
  if (!body) return;

  const pct = state.index > 0 ? Math.round((state.index / state.words.length) * 100) : 0;
  const fill = document.getElementById('spell-prog-fill');
  if (fill) fill.style.width = `${pct}%`;

  const word   = state.words[state.index];
  const isLast = state.index === state.words.length - 1;
  const isChallenge = state.index >= (state.words.length - (state._challengeCount ?? 0));

  body.innerHTML = `
    <div class="ckla-spell-counter">${state.index + 1} / ${state.words.length}${isChallenge ? ' <span class="ckla-spell-challenge-tag">Challenge</span>' : ''}</div>
    <div class="ckla-spell-listen-row">
      <button class="ckla-spell-play-btn" onclick="_spellPlayCurrent()" id="spell-play-btn">
        <i data-lucide="volume-2" width="22" height="22"></i>
        Listen
      </button>
      <div class="ckla-spell-hint" id="spell-hint"></div>
    </div>
    <div class="ckla-spell-input-row">
      <input type="text" id="spell-input" class="ckla-spell-input"
             placeholder="Type the word…"
             autocomplete="off" autocorrect="off" spellcheck="false"
             onkeydown="if(event.key==='Enter') _spellSubmit()">
    </div>
    <div class="ckla-spell-feedback" id="spell-feedback"></div>
    <button class="ckla-spell-submit-btn" onclick="_spellSubmit()">
      Check
    </button>`;

  if (typeof lucide !== 'undefined') lucide.createIcons();

  const input = document.getElementById('spell-input');
  if (input) input.focus();

  // Auto-play on load
  _spellPlayWord(word);

  window._spellPlayCurrent = () => _spellPlayWord(state.words[state.index]);
  window._spellSubmit = () => {
    const w = state.words[state.index];
    const last = state.index === state.words.length - 1;
    _spellCheck(state, w, last);
  };
}

/* ── TTS ────────────────────────────────────────────────────────── */

async function _spellPlayWord(word) {
  const btn = document.getElementById('spell-play-btn');
  if (btn) btn.disabled = true;
  try {
    const res = await fetch('/api/tts/word_only', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ word }),
    });
    if (!res.ok) throw new Error('TTS error');
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const aud  = new Audio(url);
    aud.onended = () => { URL.revokeObjectURL(url); if (btn) btn.disabled = false; };
    aud.onerror = () => { URL.revokeObjectURL(url); if (btn) btn.disabled = false; };
    await aud.play();
  } catch {
    if (btn) btn.disabled = false;
    const hint = document.getElementById('spell-hint');
    if (hint) hint.textContent = '(TTS unavailable)';
  }
}

/* ── Check answer ───────────────────────────────────────────────── */

function _spellCheck(state, correctWord, isLast) {
  const input    = document.getElementById('spell-input');
  const feedback = document.getElementById('spell-feedback');
  if (!input || !feedback) return;

  const typed   = input.value.trim().toLowerCase();
  const correct = correctWord.toLowerCase();

  if (!typed) { input.focus(); return; }

  const isCorrect = typed === correct;
  state.results.push({ word: correctWord, typed, correct: isCorrect });

  if (isCorrect) {
    feedback.className = 'ckla-spell-feedback ckla-spell-correct';
    feedback.innerHTML = '<i data-lucide="check-circle-2" width="16" height="16"></i> Correct!';
    if (typeof lucide !== 'undefined') lucide.createIcons();
    input.disabled = true;
    document.querySelector('.ckla-spell-submit-btn').disabled = true;
    setTimeout(() => {
      if (isLast) { _spellShowResults(state); }
      else        { state.index++; _spellShowCurrent(state); }
    }, 700);
  } else {
    feedback.className = 'ckla-spell-feedback ckla-spell-wrong';
    feedback.innerHTML = `<i data-lucide="x-circle" width="16" height="16"></i> The correct spelling is <strong>${_spEsc(correctWord)}</strong>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    input.disabled = true;
    document.querySelector('.ckla-spell-submit-btn').textContent = isLast ? 'Finish' : 'Next';
    document.querySelector('.ckla-spell-submit-btn').onclick = () => {
      if (isLast) { _spellShowResults(state); }
      else        { state.index++; _spellShowCurrent(state); }
    };
  }
}

/* ── Results screen ─────────────────────────────────────────────── */

function _spellShowResults(state) {
  const body  = document.getElementById('spell-body');
  const fill  = document.getElementById('spell-prog-fill');
  if (fill) fill.style.width = '100%';
  if (!body) return;

  const total   = state.results.length;
  const correct = state.results.filter(r => r.correct).length;
  const pct     = Math.round((correct / total) * 100);

  const rowsHtml = state.results.map(r => `
    <tr class="ckla-spell-res-row ${r.correct ? 'ok' : 'err'}">
      <td class="ckla-spell-res-word">${_spEsc(r.word)}</td>
      <td class="ckla-spell-res-typed">${_spEsc(r.typed)}</td>
      <td>${r.correct
        ? '<i data-lucide="check" width="14" height="14"></i>'
        : '<i data-lucide="x" width="14" height="14"></i>'}</td>
    </tr>`).join('');

  const emoji = pct === 100 ? 'award' : pct >= 80 ? 'star' : 'refresh-ccw';

  body.innerHTML = `
    <div class="ckla-spell-result-header">
      <i data-lucide="${emoji}" width="32" height="32" class="ckla-spell-result-icon"></i>
      <div class="ckla-spell-score">${correct} / ${total}</div>
      <div class="ckla-spell-score-label">${pct}% correct</div>
    </div>
    <table class="ckla-spell-res-table">
      <thead><tr>
        <th>Word</th><th>Your answer</th><th></th>
      </tr></thead>
      <tbody>${rowsHtml}</tbody>
    </table>
    <div class="ckla-spell-result-btns">
      <button class="ckla-btn ckla-spell-retry-btn" onclick="_spellRetry()">Practice Again</button>
      <button class="ckla-btn-secondary ckla-spell-close-btn" onclick="_spellClose()">Done</button>
    </div>`;

  if (typeof lucide !== 'undefined') lucide.createIcons();

  window._spellRetry = () => {
    state.index   = 0;
    state.results = [];
    _spellShowCurrent(state);
  };
}

/* ── Utilities ──────────────────────────────────────────────────── */

function _spEsc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
