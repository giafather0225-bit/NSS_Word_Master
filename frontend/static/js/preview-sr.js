/* ================================================================
   preview-sr.js — Step 1 Phase 9 add-on: Sentence Reading (×2)
   Section: English / Preview
   Dependencies: core.js, preview.js
   API endpoints: /api/tts/example_full (via playTTS callback)
   ================================================================ */

/**
 * Word-overlap similarity 0–100 for long sentence matching.
 * Ignores short filler words (≤2 chars) and punctuation.
 * @tag SENTENCE_READ
 */
function _srSimilarity(spoken, ref) {
    const sp = spoken.toLowerCase().split(/\s+/).filter(w => w.length > 2);
    const rf = ref.toLowerCase().replace(/[^a-z\s]/g, '').split(/\s+/).filter(w => w.length > 2);
    if (!rf.length) return 100;
    return Math.round(rf.filter(w => sp.includes(w)).length / rf.length * 100);
}

/**
 * Start the Sentence Reading (×2) flow inside an already-open Preview modal.
 * Called by preview.js after all 3 Spell rows pass (when item.hint exists).
 *
 * ctx:
 *   hint       — example sentence to read aloud
 *   playTTS    — async (url, body) => plays TTS blob
 *   SpeechRec  — window.SpeechRecognition constructor (or falsy)
 *   setRec     — (recObj) => registers current recognizer for stopAudio()
 *   onDone     — callback invoked once both rows pass (shows verdict)
 *
 * @tag PREVIEW SENTENCE_READ TTS
 */
window.pmStartSR = function(ctx) {
    const {hint, playTTS, SpeechRec, setRec, onDone} = ctx;
    const state = [null, null];

    const labelEl = document.getElementById('pm-sr-label');
    if (labelEl) labelEl.classList.remove('locked');

    function buildRows() {
        const rowsEl = document.getElementById('pm-sr-rows');
        if (!rowsEl) return;
        rowsEl.innerHTML = '';
        state.forEach((score, i) => {
            const passed = score !== null && score >= 90;
            const row = document.createElement('div');
            row.className = 'pm-sr-row';

            const mic = document.createElement('button');
            mic.type = 'button';
            mic.className = 'pm-mic-btn' + (passed ? ' done' : '');
            mic.innerHTML = passed ? '✓' : '🎤 Listen &amp; Repeat';
            mic.disabled = passed;
            if (!passed) mic.addEventListener('click', () => startRec(i));

            const icon = document.createElement('span');
            icon.className = 'pm-row-icon';
            icon.textContent = passed ? '✓' : '○';
            icon.style.color = passed ? '#34C759' : '#B0B0B5';

            const scoreEl = document.createElement('span');
            scoreEl.className = 'pm-score-text';
            scoreEl.textContent = score !== null ? score + '%' : '';

            row.append(mic, icon, scoreEl);
            rowsEl.appendChild(row);
        });
    }

    const isOffline = () => typeof navigator !== 'undefined' && navigator.onLine === false;

    async function startRec(i) {
        const mic = document.querySelectorAll('#pm-sr-rows .pm-mic-btn')[i];
        if (mic) { mic.disabled = true; mic.innerHTML = '🎵 Playing…'; }
        try { await playTTS('/api/tts/example_full', {sentence: hint}); } catch (_) {}

        // Offline or no Web Speech API → route to local Whisper via backend
        if (isOffline() || !SpeechRec) {
            await _recordAndRecognizeLocal(i, mic);
            return;
        }

        if (mic) { mic.classList.add('recording'); mic.innerHTML = '&#9209; Say it now'; }
        const rec = new SpeechRec();
        rec.lang = 'en-US';
        rec.interimResults = false;
        rec.maxAlternatives = 3;

        rec.onresult = e => {
            const alts = Array.from(e.results[0]);
            const score = Math.max(...alts.map(a => _srSimilarity(a.transcript, hint)));
            state[i] = score;
            buildRows();
            if (score >= 90) checkDone();
            else setTimeout(() => { state[i] = null; buildRows(); }, 1500);
        };
        rec.onerror = (ev) => {
            // 'network' error on flaky/blocked connection → fall back to local Whisper
            if (ev && ev.error === 'network') {
                _recordAndRecognizeLocal(i, mic);
                return;
            }
            buildRows();
        };
        rec.onend   = () => { if (state[i] === null) buildRows(); };

        if (typeof setRec === 'function') setRec(rec);
        try { rec.start(); } catch (_) {}
    }

    /**
     * Record 4s of mic audio and send to /api/speech/recognize (local Whisper).
     * Used as offline fallback for the Shadow stage.
     * @tag SENTENCE_READ SPEECH OFFLINE
     */
    async function _recordAndRecognizeLocal(i, mic) {
        if (!navigator.mediaDevices || !window.MediaRecorder) {
            state[i] = 100;  // hardware unavailable → auto-pass
            buildRows();
            checkDone();
            return;
        }
        if (mic) { mic.classList.add('recording'); mic.innerHTML = '&#9209; Say it now'; }
        let stream;
        try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (_) {
            state[i] = 100;
            buildRows();
            checkDone();
            return;
        }
        const rec = new MediaRecorder(stream);
        const chunks = [];
        rec.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
        rec.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());
            const blob = new Blob(chunks, { type: 'audio/webm' });
            try {
                const fd = new FormData();
                fd.append('audio', blob, 'clip.webm');
                fd.append('lang', 'en');
                const res = await fetch('/api/speech/recognize', { method: 'POST', body: fd });
                if (!res.ok) throw new Error('recognize ' + res.status);
                const data = await res.json();
                const score = _srSimilarity(data.transcript || '', hint);
                state[i] = score;
                buildRows();
                if (score >= 90) checkDone();
                else setTimeout(() => { state[i] = null; buildRows(); }, 1500);
            } catch (err) {
                console.warn('[SR] local recognize failed, auto-pass:', err.message || err);
                state[i] = 100;
                buildRows();
                checkDone();
            }
        };
        rec.start();
        setTimeout(() => { try { rec.stop(); } catch (_) {} }, 4000);
    }

    function checkDone() {
        if (state.every(s => s !== null && s >= 90)) {
            if (typeof onDone === 'function') onDone();
        }
    }

    buildRows();
};
