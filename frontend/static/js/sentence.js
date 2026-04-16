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
    const grammarIcon = result.grammar.correct ? "✅" : "⚠️";
    const wordIcon    = result.wordUsage.correct ? "✅" : "⚠️";
    const stars       = "⭐".repeat(Math.min(5, Math.max(1, result.creativity.score || 1)));
    return grammarIcon + " Grammar: " + result.grammar.feedback + "\n"
         + wordIcon    + " Word Use: " + result.wordUsage.feedback + "\n"
         + stars       + " Creativity: " + result.creativity.feedback + "\n"
         + "🎉 " + result.overall;
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
 * @tag SENTENCE ENGLISH
 */
function renderSentenceMaker(el) {
    if (!smState.initialized) {
        smState.initialized = true;
        smState.attempt = {};
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

    renderSentenceItem(el, item);
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
        <div id="sm-ai-loading" class="sm-ai-loading" style="display:none;">🤖 AI가 문장을 읽고 있어요...</div>
        <div class="st-input-row" id="sm-input-row">
            <textarea class="sm-textarea" id="sentence-input" rows="3"
                      autocomplete="off" spellcheck="false" placeholder="Your sentence…"></textarea>
            <button type="button" class="st-btn" id="sent-submit">Submit ✓</button>
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
        si.textContent = "AI checking… 🤔";
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
                         && !/perfect sentence|correct ✅|great!/i.test(feedbackText.slice(0, 80));
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
                        + "<button type='button' class='sm-next-btn' id='sm-next'>Next Word ▶</button>";
                    const nextBtn = feedbackEl.querySelector("#sm-next");
                    if (nextBtn) nextBtn.addEventListener("click", () => {
                        stageIndex++;
                        renderSentenceMaker(el);
                    });
                }
                const inputRow = el.querySelector("#sm-input-row");
                if (inputRow) inputRow.remove();
                setStatus(attempt >= 2 ? "Nice effort! Moving on. ✨" : "Great sentence! ⭐");
            } else {
                // Error on 1st attempt → show feedback, allow retry
                smState.attempt[item.id] = 2;
                const feedbackEl = el.querySelector("#sm-feedback-area");
                if (feedbackEl) {
                    feedbackEl.innerHTML = "<div class='sm-feedback sm-hint'>" + escapeHtml(feedbackText).replace(/\n/g, "<br>") + "</div>";
                }
                if (inp) { inp.disabled = false; inp.value = ""; inp.focus(); }
                si.disabled = false;
                si.textContent = "Submit ✓ (2nd try)";
                setStatus("Here's a hint — give it another try! 💡");
            }
        } catch(e) {
            if (loadingEl) loadingEl.style.display = "none";
            if (inp) inp.disabled = false;
            si.disabled = false;
            si.textContent = "Submit ✓";
            setStatus("Tutor is sleeping — try again!");
        }
    });
}
