/* ================================================================
   math-3read.js — 3-Read Strategy modal for word problems
   Section: Math
   Dependencies: core.js (optional playTTS)
   API endpoints: /api/tts/speak (fallback)
   ================================================================ */

// ── Heuristic: is this a word problem? ─────────────────────

const _3R_KEYWORDS = [
    'how many', 'how much', 'altogether', 'in all', 'total',
    'left over', 'leftover', 'remaining', 'share', 'each',
    'more than', 'fewer than', 'times as', 'equally',
    'together', 'per ', 'split', 'spent', 'bought',
];

/** @tag MATH @tag THREE_READ */
function isWordProblem(text) {
    if (!text || typeof text !== 'string') return false;
    const words = text.trim().split(/\s+/);
    if (words.length < 10) return false;
    const lower = text.toLowerCase();
    return _3R_KEYWORDS.some(k => lower.includes(k));
}

// ── Modal ──────────────────────────────────────────────────

/** @tag MATH @tag THREE_READ */
function show3ReadModal(questionText, onDone) {
    const steps = [
        {
            icon: '📖',
            label: 'Read 1',
            prompt: 'What is happening in this problem?',
            hint: 'Read slowly. Picture it in your mind. Who or what is in the story?',
        },
        {
            icon: '❓',
            label: 'Read 2',
            prompt: 'What is the question asking?',
            hint: 'Find the sentence that asks something. What do you need to find?',
        },
        {
            icon: '🔢',
            label: 'Read 3',
            prompt: 'What numbers and information are important?',
            hint: 'Look for the numbers and what they mean. Which ones will you use?',
        },
    ];

    let stepIdx = 0;

    const overlay = document.createElement('div');
    overlay.className = 'math-3read-modal';
    overlay.innerHTML = `
        <div class="math-3read-card">
            <button class="math-3read-close" aria-label="Close">×</button>
            <div class="math-3read-head">
                <h2 class="math-3read-title">3-Read Strategy</h2>
                <div class="math-3read-dots" id="math-3read-dots"></div>
            </div>
            <blockquote class="math-3read-question" id="math-3read-question"></blockquote>
            <div class="math-3read-step" id="math-3read-step"></div>
            <div class="math-3read-actions">
                <button class="math-btn-ghost" id="math-3read-tts">🔊 Listen</button>
                <button class="math-btn-primary" id="math-3read-next">Next read →</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    const cleanup = () => {
        overlay.remove();
        document.removeEventListener('keydown', onKey);
    };
    const onKey = (e) => {
        if (e.key === 'Escape') cleanup();
        else if (e.key === 'Enter') advance();
    };
    document.addEventListener('keydown', onKey);

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay || e.target.classList.contains('math-3read-close')) cleanup();
    });

    const qEl = overlay.querySelector('#math-3read-question');
    qEl.textContent = questionText || '';

    const render = () => {
        const s = steps[stepIdx];
        const stepEl = overlay.querySelector('#math-3read-step');
        stepEl.innerHTML = `
            <div class="math-3read-label"><span class="math-3read-icon">${s.icon}</span> ${s.label}</div>
            <div class="math-3read-prompt">${s.prompt}</div>
            <div class="math-3read-hint">${s.hint}</div>`;

        const dots = overlay.querySelector('#math-3read-dots');
        dots.innerHTML = steps.map((_, i) =>
            `<span class="math-3read-dot ${i === stepIdx ? 'active' : i < stepIdx ? 'done' : ''}"></span>`
        ).join('');

        const nextBtn = overlay.querySelector('#math-3read-next');
        nextBtn.textContent = stepIdx === steps.length - 1 ? 'Solve! ✓' : 'Next read →';

        // Autoplay TTS for the question + prompt on each step
        _play3ReadTTS(questionText, s.prompt);
    };

    const advance = () => {
        if (stepIdx < steps.length - 1) {
            stepIdx += 1;
            render();
        } else {
            cleanup();
            if (typeof onDone === 'function') onDone();
        }
    };

    overlay.querySelector('#math-3read-next').addEventListener('click', advance);
    overlay.querySelector('#math-3read-tts').addEventListener('click', () => {
        const s = steps[stepIdx];
        _play3ReadTTS(questionText, s.prompt);
    });

    render();
}

// ── TTS ────────────────────────────────────────────────────

async function _play3ReadTTS(question, prompt) {
    const text = `${question}. ${prompt}`;
    if (!text) return;
    try {
        if (typeof playTTS === 'function') {
            await playTTS(text);
            return;
        }
        const res = await fetch('/api/tts/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, voice: 'en-US-AriaNeural' }),
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audio.play();
            audio.onended = () => URL.revokeObjectURL(url);
        }
    } catch (err) {
        console.warn('[math] 3-read TTS failed', err);
    }
}

// Expose globally
window.isWordProblem = isWordProblem;
window.show3ReadModal = show3ReadModal;
