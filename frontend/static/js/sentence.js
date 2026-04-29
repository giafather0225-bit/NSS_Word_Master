/* ================================================================
   sentence.js — Step 5: Make a Sentence (AI-graded free writing).
   Section: English / Sentence
   Dependencies: core.js, tts-client.js, analytics.js
   API endpoints: /api/evaluate-sentence, /api/practice/sentence,
                  /api/practice/sentences/:subject/:textbook/:lesson
   ================================================================ */

/**
 * Evaluate a student sentence using the backend AI endpoint.
 * Returns { structured: true, data: result } or { structured: false, data: feedbackString }.
 * @tag SENTENCE AI OLLAMA GEMINI
 */
async function evaluateSentence(word, sentence) {
    try {
        const res = await fetch('/api/evaluate-sentence', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word, sentence }),
        });
        if (!res.ok) throw new Error(`evaluate ${res.status}`);
        const result = await res.json();
        return { structured: true, data: result };
    } catch {
        const feedback = await apiTutorReply(word, sentence);
        return { structured: false, data: feedback };
    }
}

/**
 * Format a structured AI evaluation result into a human-readable multi-line string.
 * @tag SENTENCE AI
 */
function formatStructuredFeedback(result) {
    const grammarIcon = result.grammar.correct ? "[OK]" : "[!]";
    const wordIcon    = result.wordUsage.correct ? "[OK]" : "[!]";
    const score       = Math.min(5, Math.max(1, result.creativity.score || 1));
    const stars       = `[${score}/5]`;
    return grammarIcon + " Grammar: " + result.grammar.feedback + "\n"
         + wordIcon    + " Word Use: " + result.wordUsage.feedback + "\n"
         + stars       + " Creativity: " + result.creativity.feedback + "\n"
         + result.overall;
}

/**
 * POST a student's practice sentence to the backend for persistence.
 * @tag SENTENCE DIARY JOURNAL
 */
async function savePracticeSentence(itemId, sentence, lesson) {
    try {
        await fetch("/api/practice/sentence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: currentSubject, textbook: currentTextbook, lesson, item_id: itemId, sentence }),
        });
    } catch (err) {
        console.warn('[save] Practice sentence not saved:', err.message || err);
    }
}

/**
 * Load the student's previously-written sentences for the current lesson,
 * keyed by item_id.
 * @tag SENTENCE DIARY JOURNAL
 */
async function loadOwnSentences(lesson) {
    try {
        const res = await fetch(`/api/practice/sentences/${encodeURIComponent(currentSubject)}/${encodeURIComponent(currentTextbook)}/${encodeURIComponent(lesson)}`);
        if (!res.ok) return {};
        const data = await res.json();
        return data.by_item_id || {};
    } catch (err) {
        console.warn('[load] Own sentences fetch failed:', err.message || err);
        return {};
    }
}

/**
 * Entry point for the Make-a-Sentence stage.
 * Per-item flow: Phase 1 (word-scramble drag/drop) → Phase 2 (AI-graded free writing).
 * Items without an example sentence (item.hint) skip Phase 1.
 * @tag SENTENCE ENGLISH
 */
function renderSentenceMaker(el) {
    if (!smState.initialized) {
        smState.initialized = true;
        smState.attempt = {};
        smState.phase   = {};
        stageIndex = 0;
        const shuffled = shuffle(items);
        items.splice(0, items.length, ...shuffled);
    }

    const item = items[stageIndex];
    if (!item) {
        smState.initialized = false;
        advanceToNextStage();
        return;
    }

    const hasExample = !!(item.hint && String(item.hint).trim());
    const phase = smState.phase[item.id] || (hasExample ? 'scramble' : 'write');
    smState.phase[item.id] = phase;

    if (phase === 'scramble') {
        renderSentenceScramble(el, item);
    } else {
        renderSentenceItem(el, item);
    }
}

/**
 * Phase 1 — Tap-to-order word scramble. User rebuilds item.hint from shuffled chips.
 * On success: advance to free-writing phase for same word.
 * @tag SENTENCE ENGLISH
 */
function renderSentenceScramble(el, item) {
    const total   = items.length;
    const current = stageIndex + 1;
    const tokens  = String(item.hint).trim().split(/\s+/);
    if (tokens.length < 2) {
        smState.phase[item.id] = 'write';
        renderSentenceItem(el, item);
        return;
    }
    const order = tokens.map((_, i) => i);
    const bank  = shuffle(order.slice());
    if (bank.every((v, i) => v === order[i])) {
        [bank[0], bank[1]] = [bank[1], bank[0]];
    }

    el.innerHTML = `
        <p class="st-h1">Step 5 — Make a Sentence</p>
        <p class="st-sub">First, put the words in order:</p>
        <div class="sm-word-chip">${escapeHtml(item.answer)}</div>
        <div class="sm-scramble-answer" id="sm-scr-answer" aria-label="Answer row"></div>
        <div class="sm-scramble-bank" id="sm-scr-bank" aria-label="Word bank"></div>
        <div class="st-input-row">
            <button type="button" class="st-btn ghost" id="sm-scr-reset">Reset</button>
            <button type="button" class="st-btn" id="sm-scr-check" disabled>Check</button>
        </div>
        <p id="sm-scr-feedback" class="sm-scr-feedback"></p>
        <p class="st-prog">${current} / ${total} &nbsp;·&nbsp; Phase 1 / 2</p>
    `;

    const bankEl   = el.querySelector('#sm-scr-bank');
    const answerEl = el.querySelector('#sm-scr-answer');
    const checkBtn = el.querySelector('#sm-scr-check');
    const resetBtn = el.querySelector('#sm-scr-reset');
    const fbEl     = el.querySelector('#sm-scr-feedback');

    const placed = [];

    function makeChip(tokenIdx, label) {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'sm-scr-chip';
        chip.textContent = label;
        chip.dataset.idx = String(tokenIdx);
        return chip;
    }

    function refreshCheck() {
        checkBtn.disabled = placed.length !== tokens.length;
        fbEl.textContent = '';
        fbEl.className = 'sm-scr-feedback';
    }

    function render() {
        bankEl.innerHTML = '';
        answerEl.innerHTML = '';
        bank.forEach(idx => {
            if (placed.includes(idx)) return;
            const chip = makeChip(idx, tokens[idx]);
            chip.addEventListener('click', () => {
                placed.push(idx);
                render();
            });
            bankEl.appendChild(chip);
        });
        placed.forEach((idx, pos) => {
            const chip = makeChip(idx, tokens[idx]);
            chip.classList.add('placed');
            chip.addEventListener('click', () => {
                placed.splice(pos, 1);
                render();
            });
            answerEl.appendChild(chip);
        });
        refreshCheck();
    }

    resetBtn.addEventListener('click', () => { placed.length = 0; render(); });

    checkBtn.addEventListener('click', () => {
        const correct = placed.every((idx, i) => idx === order[i]);
        if (correct) {
            stageFxCorrect();
            fbEl.textContent = 'Great! Now write your own sentence.';
            fbEl.classList.add('correct');
            checkBtn.disabled = true;
            setTimeout(() => {
                smState.phase[item.id] = 'write';
                renderSentenceMaker(el);
            }, 900);
        } else {
            stageFxWrong();
            fbEl.textContent = 'Not quite — try again!';
            fbEl.classList.add('wrong');
            _trackWordAttempt && _trackWordAttempt(item, false, 'scramble:wrong');
        }
    });

    render();
}

/**
 * Render a single Make-a-Sentence item, wiring submit and retry logic.
 * @tag SENTENCE ENGLISH AI
 */
function renderSentenceItem(el, item) {
    const attempt      = smState.attempt[item.id] || 1;
    const total        = items.length;
    const current      = stageIndex + 1;
    const attemptLabel = attempt === 2 ? " (2nd try)" : "";

    const hintHtml = item.question
        ? `<div class="sm-hint-block"><div class="sm-hint-meaning">${escapeHtml(item.question)}</div></div>`
        : `<div class="sm-hint-block"></div>`;

    el.innerHTML = `
        <p class="st-h1">Step 5 — Make a Sentence</p>
        <p class="st-sub">Use this word in a sentence${attemptLabel}:</p>
        <div class="sm-word-chip">${escapeHtml(item.answer)}</div>
        ${hintHtml}
        <div id="sm-feedback-area"></div>
        <div id="sm-ai-loading" class="sm-ai-loading" style="display:none;">AI is reading your sentence…</div>
        <div class="st-input-row" id="sm-input-row">
            <textarea class="sm-textarea" id="sentence-input" rows="3"
                      autocomplete="off" spellcheck="false" placeholder="Your sentence…"></textarea>
            <button type="button" class="st-btn" id="sent-submit">Submit</button>
        </div>
        <p class="st-prog">${current} / ${total}</p>
    `;

    const inp = el.querySelector("#sentence-input");
    if (inp) inp.focus();

    // Shift+Enter = newline; Enter = submit
    if (inp) {
        inp.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const si = el.querySelector("#sent-submit");
                if (si && !si.disabled) si.click();
            }
        });
    }

    const si = el.querySelector("#sent-submit");
    if (!si) return;

    si.addEventListener("click", async () => {
        const sentence = (inp ? inp.value || "" : "").trim();
        if (!sentence || sentence.split(/\s+/).length < 2) {
            setStatus("Write a full sentence (at least 2 words)!");
            return;
        }
        if (!sentenceHasWord(sentence, item.answer)) {
            stageFxWrong();
            setStatus("Your sentence must include \"" + item.answer + "\"!");
            return;
        }

        if (inp) inp.disabled = true;
        si.disabled = true;
        si.textContent = "AI checking…";
        setStatus("Asking AI tutor…");

        const loadingEl = el.querySelector("#sm-ai-loading");
        if (loadingEl) loadingEl.style.display = "block";

        try {
            const evalResult = await evaluateSentence(item.answer, sentence);
            await savePracticeSentence(item.id, sentence, lessonSelected());
            lastTypedSentence = sentence;

            if (loadingEl) loadingEl.style.display = "none";

            let feedbackText;
            let hasError;
            if (evalResult.structured) {
                feedbackText = formatStructuredFeedback(evalResult.data);
                hasError = !(evalResult.data.grammar.correct && evalResult.data.wordUsage.correct);
            } else {
                feedbackText = evalResult.data;
                hasError = /correct(ed|ion)|grammar|mistake|should be|try:/i.test(feedbackText)
                         && !/perfect sentence|correct|great!/i.test(feedbackText.slice(0, 80));
            }

            if (!hasError || attempt >= 2) {
                // OK or 2nd attempt → advance
                stageFxCorrect();
                starCount++;
                updateStars();
                addWordVault(item.answer);

                const feedbackEl = el.querySelector("#sm-feedback-area");
                if (feedbackEl) {
                    feedbackEl.innerHTML = "<div class='sm-feedback'>" + escapeHtml(feedbackText).replace(/\n/g, "<br>") + "</div>"
                        + "<button type='button' class='sm-next-btn' id='sm-next'>Next Word <i data-lucide=\"chevron-right\"></i></button>";
                    if (window.lucide) lucide.createIcons();
                    const nextBtn = feedbackEl.querySelector("#sm-next");
                    if (nextBtn) nextBtn.addEventListener("click", () => {
                        stageIndex++;
                        renderSentenceMaker(el);
                    });
                }
                const inputRow = el.querySelector("#sm-input-row");
                if (inputRow) inputRow.remove();
                setStatus(attempt >= 2 ? "Nice effort! Moving on." : "Great sentence!");
            } else {
                // Error on 1st attempt → show feedback, allow retry
                smState.attempt[item.id] = 2;
                const feedbackEl = el.querySelector("#sm-feedback-area");
                if (feedbackEl) {
                    feedbackEl.innerHTML = "<div class='sm-feedback sm-hint'>" + escapeHtml(feedbackText).replace(/\n/g, "<br>") + "</div>";
                }
                if (inp) { inp.disabled = false; inp.value = ""; inp.focus(); }
                si.disabled = false;
                si.textContent = "Submit (2nd try)";
                setStatus("Here's a hint — give it another try!");
            }
        } catch(e) {
            if (loadingEl) loadingEl.style.display = "none";
            if (inp) inp.disabled = false;
            si.disabled = false;
            si.textContent = "Submit";
            setStatus("Tutor is sleeping — try again!");
        }
    });
}
