/* ================================================================
   ckla-review.js — CKLA SM-2 vocabulary review UI
   Section: Academy
   Dependencies: ckla.js, tts-client.js
   API endpoints: /api/academy/ckla/review/due,
                  /api/academy/ckla/review/result
   ================================================================ */

/** @type {object[]} Words due for review */
let _cklaRevWords = [];
/** @type {number} Current review index */
let _cklaRevIdx = 0;
/** @type {number} Correct count */
let _cklaRevCorrect = 0;
/** @type {number} Total attempted */
let _cklaRevTotal = 0;
/** @type {string} Current review phase: 'prompt' | 'result' | 'summary' */
let _cklaRevPhase = 'prompt';
/** @type {number} Attempts on current word */
let _cklaRevAttempts = 0;


/* ── Entry ─────────────────────────────────────────────────────────────────── */

/** Show CKLA review screen. @tag ACADEMY CKLA SM2 */
async function showCKLAReview() {
  // Hide other views
  ['idle-wrapper', 'stage-card', 'daily-words-view'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  const view = document.getElementById('ckla-view');
  if (view) view.style.display = 'flex';

  // Reset state
  _cklaRevWords   = [];
  _cklaRevIdx     = 0;
  _cklaRevCorrect = 0;
  _cklaRevTotal   = 0;
  _cklaRevPhase   = 'prompt';
  _cklaRevAttempts = 0;

  const content = document.getElementById('ckla-view');
  if (!content) return;
  content.innerHTML = '<div class="ckla-loading">Loading review…</div>';

  try {
    const res = await fetch('/api/academy/ckla/review/due');
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    _cklaRevWords = data.words || [];

    if (_cklaRevWords.length === 0) {
      _renderReviewEmpty(content);
    } else {
      _renderReviewShell(content);
      _renderReviewCard();
    }
  } catch (e) {
    content.innerHTML = `<div class="ckla-empty">Could not load review. ${e.message}</div>`;
  }
}


/* ── Render shell ──────────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA SM2 */
function _renderReviewEmpty(container) {
  container.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="hideCKLAView()">← Back</button>
      <h2 class="ckla-title">CKLA Review</h2>
    </div>
    <div class="ckla-review-empty">
      <div class="ckla-review-empty-icon">🎉</div>
      <div class="ckla-review-empty-text">No words to review today!</div>
      <div class="ckla-review-empty-sub">Keep studying lessons — new review words will appear tomorrow.</div>
    </div>`;
}

/** @tag ACADEMY CKLA SM2 */
function _renderReviewShell(container) {
  container.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="hideCKLAView()">← Back</button>
      <h2 class="ckla-title">CKLA Review</h2>
    </div>
    <div id="ckla-review-body" style="flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:12px;"></div>`;
}


/* ── Review card ───────────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA SM2 */
function _renderReviewCard() {
  const body = document.getElementById('ckla-review-body');
  if (!body) return;

  // Summary screen
  if (_cklaRevIdx >= _cklaRevWords.length) {
    _renderReviewSummary(body);
    return;
  }

  const w = _cklaRevWords[_cklaRevIdx];
  const pct = Math.round((_cklaRevIdx / _cklaRevWords.length) * 100);

  if (_cklaRevPhase === 'prompt') {
    _cklaRevAttempts = 0;
    body.innerHTML = `
      <div class="ckla-review-container">
        <div class="ckla-review-progress">
          <span>${_cklaRevIdx + 1} / ${_cklaRevWords.length}</span>
          <div class="ckla-review-bar">
            <div class="ckla-review-bar-fill" style="width:${pct}%"></div>
          </div>
          <span>${_cklaRevCorrect} ✓</span>
        </div>
        <div class="ckla-review-card">
          <div class="ckla-review-word">${_escRev(w.word)}</div>
          ${w.part_of_speech ? `<div class="ckla-review-pos">${_escRev(w.part_of_speech)}</div>` : ''}
          ${w.audio_url ? `<button class="ckla-review-audio-btn" onclick="_cklaRevAudio('${w.audio_url}')">🔊</button>` : ''}
          <div class="ckla-review-input-wrap">
            <div class="ckla-review-hint">Type the meaning of this word</div>
            <input type="text" class="ckla-review-input" id="ckla-rev-input"
                   placeholder="Enter definition…"
                   onkeydown="if(event.key==='Enter')_cklaRevCheck()" autofocus>
          </div>
          <div class="ckla-review-actions">
            <button class="ckla-review-show-btn" onclick="_cklaRevShowAnswer()">Show Answer</button>
            <button class="ckla-review-check-btn" onclick="_cklaRevCheck()">Check</button>
          </div>
        </div>
      </div>`;

    // Autofocus
    setTimeout(() => {
      const inp = document.getElementById('ckla-rev-input');
      if (inp) inp.focus();
    }, 100);

  } else if (_cklaRevPhase === 'result') {
    const isCorrect = body.dataset.lastCorrect === 'true';
    body.innerHTML = `
      <div class="ckla-review-container">
        <div class="ckla-review-progress">
          <span>${_cklaRevIdx + 1} / ${_cklaRevWords.length}</span>
          <div class="ckla-review-bar">
            <div class="ckla-review-bar-fill" style="width:${pct}%"></div>
          </div>
          <span>${_cklaRevCorrect} ✓</span>
        </div>
        <div class="ckla-review-card">
          <div class="ckla-review-word">${_escRev(w.word)}</div>
          ${w.part_of_speech ? `<div class="ckla-review-pos">${_escRev(w.part_of_speech)}</div>` : ''}
          <div class="ckla-review-result ${isCorrect ? 'ckla-review-correct' : 'ckla-review-wrong'}">
            <div class="ckla-review-result-word">${isCorrect ? '✓ Correct!' : '✗ Not quite'}</div>
            <div class="ckla-review-result-def">${_escRev(w.definition)}</div>
          </div>
          ${w.example_1 ? `<div class="ckla-vocab-ex" style="text-align:center">"${_escRev(w.example_1)}"</div>` : ''}
          <button class="ckla-review-next-btn" onclick="_cklaRevNext()">
            ${_cklaRevIdx + 1 >= _cklaRevWords.length ? 'See Results' : 'Next Word →'}
          </button>
        </div>
      </div>`;
  }
}


/* ── Check answer ──────────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA SM2 */
async function _cklaRevCheck() {
  const input = document.getElementById('ckla-rev-input');
  const userAnswer = input ? input.value.trim() : '';
  if (!userAnswer) {
    if (input) { input.style.borderColor = 'var(--color-error)'; input.focus(); }
    return;
  }

  const w = _cklaRevWords[_cklaRevIdx];
  _cklaRevAttempts++;

  // Simple match: check if user answer contains key words from definition
  const isCorrect = _cklaRevMatchAnswer(userAnswer, w.definition, w.word);

  _cklaRevTotal++;
  if (isCorrect) _cklaRevCorrect++;

  // Save to server
  try {
    await fetch('/api/academy/ckla/review/result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        word_id: w.id,
        is_correct: isCorrect,
        attempts: _cklaRevAttempts,
      }),
    });
  } catch (e) {
    console.error('CKLA review save failed:', e);
  }

  _cklaRevPhase = 'result';
  const body = document.getElementById('ckla-review-body');
  if (body) body.dataset.lastCorrect = isCorrect ? 'true' : 'false';
  _renderReviewCard();
}


/** Fuzzy match user answer against definition. @tag ACADEMY CKLA SM2 */
function _cklaRevMatchAnswer(userAnswer, definition, word) {
  if (!definition) return false;

  const normalize = s => s.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
  const ua = normalize(userAnswer);
  const def = normalize(definition);

  // Exact or near-exact match
  if (ua === def) return true;
  if (def.includes(ua) && ua.length > 3) return true;

  // Extract key content words from definition (skip common words)
  const stopWords = new Set([
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'or',
    'and', 'that', 'this', 'it', 'its', 'as', 'not', 'but', 'if', 'do',
    'does', 'did', 'has', 'have', 'had', 'will', 'would', 'can', 'could',
    'may', 'might', 'shall', 'should', 'very', 'much', 'more', 'most',
    'also', 'just', 'about', 'up', 'out', 'so', 'than', 'too', 'only',
    'into', 'over', 'after', 'before', 'between', 'through', 'during',
    'something', 'someone', 'thing', 'things', 'way', 'make', 'made',
  ]);

  const defWords = def.split(/\s+/).filter(w => w.length > 2 && !stopWords.has(w));
  const uaWords = new Set(ua.split(/\s+/));

  if (defWords.length === 0) return false;

  let matchCount = 0;
  for (const dw of defWords) {
    for (const uw of uaWords) {
      if (uw === dw || (uw.length > 4 && dw.startsWith(uw)) || (dw.length > 4 && uw.startsWith(dw))) {
        matchCount++;
        break;
      }
    }
  }

  const ratio = matchCount / defWords.length;
  return ratio >= 0.4;
}


/** Show answer without checking (counts as wrong). @tag ACADEMY CKLA SM2 */
async function _cklaRevShowAnswer() {
  const w = _cklaRevWords[_cklaRevIdx];
  _cklaRevAttempts++;
  _cklaRevTotal++;

  // Save as wrong
  try {
    await fetch('/api/academy/ckla/review/result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        word_id: w.id,
        is_correct: false,
        attempts: _cklaRevAttempts,
      }),
    });
  } catch (e) {
    console.error('CKLA review save failed:', e);
  }

  _cklaRevPhase = 'result';
  const body = document.getElementById('ckla-review-body');
  if (body) body.dataset.lastCorrect = 'false';
  _renderReviewCard();
}


/** Move to next word. @tag ACADEMY CKLA SM2 */
function _cklaRevNext() {
  _cklaRevIdx++;
  _cklaRevPhase = 'prompt';
  _renderReviewCard();
}


/** Audio playback. @tag ACADEMY CKLA SM2 */
function _cklaRevAudio(url) {
  try { new Audio(url).play(); } catch (e) { console.warn('CKLA review audio failed:', e); }
}


/* ── Summary ───────────────────────────────────────────────────────────────── */

/** @tag ACADEMY CKLA SM2 */
function _renderReviewSummary(body) {
  const pct = _cklaRevTotal > 0 ? Math.round((_cklaRevCorrect / _cklaRevTotal) * 100) : 0;
  const emoji = pct >= 80 ? '🌟' : pct >= 50 ? '👍' : '💪';
  const msg = pct >= 80 ? 'Excellent work!' : pct >= 50 ? 'Good effort!' : 'Keep practicing!';

  body.innerHTML = `
    <div class="ckla-review-container">
      <div class="ckla-review-summary">
        <div class="ckla-review-emoji">${emoji}</div>
        <div class="ckla-review-score">${_cklaRevCorrect} / ${_cklaRevTotal}</div>
        <div class="ckla-review-detail">
          ${msg}<br>
          ${pct}% correct · ${_cklaRevTotal} words reviewed
        </div>
        <button class="ckla-review-done-btn" onclick="hideCKLAView()">Done</button>
      </div>
    </div>`;
}


/** Escape HTML. @tag SYSTEM */
function _escRev(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
