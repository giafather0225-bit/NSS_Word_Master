/* ================================================================
   ckla-lesson-reading.js — CKLA Reading tab: TTS, passage render, font size,
                            per-paragraph highlight
   Section: Academy
   Dependencies: ckla-lesson.js (state vars + shared utils)
   API endpoints: /api/tts
   ================================================================ */


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
