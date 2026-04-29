/* ================================================================
   fillblank.js — Step 3: Fill the Blank (sentence cloze with retry queue).
   Section: English / Fill Blank
   Dependencies: core.js, tts-client.js, analytics.js
   API endpoints: none
   ================================================================ */

/**
 * Entry point for the Fill-the-Blank stage.
 * Dispatches to retry mode or main-pass rendering based on fbState.
 * @tag FILL_BLANK ENGLISH
 */
function renderContextFill(el) {
    if (!fbState.initialized) {
        fbState.mistakeCount = {};
        fbState.retryQueue   = [];
        fbState.retryMode    = false;
        fbState.retryIndex   = 0;
        fbState.initialized  = true;
        stageIndex = 0;
    }

    if (fbState.retryMode) {
        if (fbState.retryIndex >= fbState.retryQueue.length) {
            fbState.initialized = false;
            advanceToNextStage();
            return;
        }
        const retryItem = fbState.retryQueue[fbState.retryIndex];
        renderFillItem(el, retryItem, true);
        return;
    }

    const item = items[stageIndex];
    if (!item) {
        if (fbState.retryQueue.length > 0) {
            fbState.retryMode  = true;
            fbState.retryIndex = 0;
            fbState.retryQueue.forEach(it => { fbState.mistakeCount[it.id] = 0; });
            setStatus("Almost there! Let's retry the ones you missed.");
            renderContextFill(el);
        } else {
            fbState.initialized = false;
            advanceToNextStage();
        }
        return;
    }
    renderFillItem(el, item, false);
}

/**
 * Render a single fill-the-blank item (main pass or retry).
 * v3 redesign: inline <input> inside the sentence (the blank IS the input).
 * @tag FILL_BLANK ENGLISH
 */
function renderFillItem(el, item, isRetry) {
    const example  = item.hint && String(item.hint).trim() ? item.hint : "";
    const mistakes = fbState.mistakeCount[item.id] || 0;
    const total    = isRetry ? fbState.retryQueue.length : items.length;
    const current  = isRetry ? fbState.retryIndex + 1 : stageIndex + 1;

    // Word-chip list (shuffled; already-used ones get fb-used)
    const displayOrder = items.map((it, i) => ({ it, i }));
    for (let k = displayOrder.length - 1; k > 0; k--) {
        const j = Math.floor(Math.random() * (k + 1));
        [displayOrder[k], displayOrder[j]] = [displayOrder[j], displayOrder[k]];
    }
    const usedCount = isRetry ? 0 : stageIndex;
    const leftCount = isRetry
        ? (fbState.retryQueue.length - fbState.retryIndex)
        : (items.length - stageIndex);
    const bankHtml = displayOrder.map(({ it, i }) => {
        const used = !isRetry && i < stageIndex;
        return `<span class="fb-chip${used ? " fb-used" : ""}">${escapeHtml(it.answer)}</span>`;
    }).join("");

    // Hint (inside sentence card, appears from 1 mistake)
    let hintHtml = "";
    if (mistakes >= 1) {
        const len = String(item.answer).length;
        hintHtml = `<div class="fb-hint"><span>${len} letters</span></div>`;
    }
    if (mistakes >= 2) {
        const first = String(item.answer).charAt(0).toUpperCase();
        const len = String(item.answer).length;
        hintHtml = `<div class="fb-hint"><span>Starts with <strong>${escapeHtml(first)}</strong> · ${len} letters</span></div>`;
    }

    // Sentence with inline blank input
    const blanked = example ? replaceWordWithBlank(example, item.answer) : "(no example sentence)";
    const parts = blanked.split("________");
    const minW = Math.max(110, item.answer.length * 13 + 40);
    const placeholder = "_".repeat(item.answer.length);
    const sentenceHtml =
        escapeHtml(parts[0] || "") +
        `<input class="fb-blank-input" id="answer-input" type="text" ` +
        `autocomplete="off" spellcheck="false" ` +
        `placeholder="${escapeHtml(placeholder)}" ` +
        `style="min-width:${minW}px;width:${minW}px" ` +
        `maxlength="${item.answer.length + 4}"/>` +
        escapeHtml(parts[1] || "");

    // Retry banner
    const retryBanner = isRetry
        ? `<div class="fb-retry-banner">
             <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
             Retry mode — ${fbState.retryQueue.length} word${fbState.retryQueue.length === 1 ? "" : "s"} to conquer
           </div>`
        : "";

    const progLabel = `${current} / ${total}${isRetry ? " retries" : ""}`;

    el.innerHTML = `
        <div class="fb-wrap">
          <div class="fb-sentence-card">
            <div class="fb-context-label">Context sentence</div>
            <button type="button" class="fb-speaker" id="fb-speaker" title="Listen">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
            </button>
            <p class="fb-sentence">${sentenceHtml}</p>
            ${hintHtml}
          </div>
          ${retryBanner}
          <div class="fb-input-row">
            <button type="button" class="fb-clear-btn" id="fb-clear">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              Clear
            </button>
            <span class="fb-kbd-hint">Press <kbd>Enter</kbd> to check</span>
            <button type="button" class="fb-check-btn" id="ctx-submit" disabled>
              Check
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </button>
          </div>
          <div class="fb-bank">
            <div class="fb-bank-header">
              <div class="fb-bank-title">Word bank</div>
              <div class="fb-bank-count">${isRetry ? leftCount + ' words to go' : usedCount + ' used · ' + leftCount + ' left'}</div>
            </div>
            <div class="fb-bank-grid">${bankHtml}</div>
          </div>
          <p class="st-prog" style="text-align:center;margin-top:4px;">${progLabel}</p>
        </div>
    `;

    const inp = el.querySelector("#answer-input");
    const submitBtn = el.querySelector("#ctx-submit");
    const clearBtn  = el.querySelector("#fb-clear");

    // Auto-focus the blank (prevent page jump)
    if (inp) {
        requestAnimationFrame(() => {
            inp.focus({ preventScroll: true });
            try { inp.setSelectionRange(inp.value.length, inp.value.length); } catch (_) {}
        });
    }

    // Toggle Check button + filled skin based on input value
    const refreshCheckState = () => {
        const hasVal = inp && inp.value && inp.value.trim().length > 0;
        if (submitBtn) submitBtn.disabled = !hasVal;
        if (inp) {
            inp.classList.remove("wrong", "correct");
            if (hasVal) inp.classList.add("filled");
            else        inp.classList.remove("filled");
        }
    };

    if (inp) {
        inp.addEventListener("input", refreshCheckState);
    }

    // Word-chip click → fill the inline blank
    el.querySelectorAll(".fb-chip").forEach(function(span) {
        if (span.classList.contains("fb-used")) {
            span.style.cursor = "default";
            return;
        }
        span.style.cursor = "pointer";
        span.addEventListener("click", function() {
            if (span.classList.contains("fb-used")) return;
            if (inp) {
                inp.value = span.textContent.trim();
                refreshCheckState();
                inp.focus({ preventScroll: true });
                try { inp.setSelectionRange(inp.value.length, inp.value.length); } catch (_) {}
            }
        });
    });

    // Clear button
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            if (!inp) return;
            inp.value = "";
            refreshCheckState();
            inp.focus({ preventScroll: true });
        });
    }

    if (!submitBtn) return;

    const doSubmit = async () => {
        const val = (inp.value || "").trim();
        if (!val) return;

        if (val.toLowerCase() === item.answer.toLowerCase()) {
            // Correct
            if (inp) inp.classList.add("correct");
            stageFxCorrect();
            starCount++;
            updateStars();
            addWordVault(item.answer);

            if (isRetry) {
                fbState.retryIndex++;
                const moreRetries = fbState.retryIndex < fbState.retryQueue.length;
                setStatus(moreRetries ? "Correct! Next retry..." : "All done!");
                await new Promise(r => setTimeout(r, 400));
                renderContextFill(el);
            } else {
                stageIndex++;
                const moreItems = stageIndex < items.length;
                if (!moreItems) {
                    if (fbState.retryQueue.length > 0) {
                        fbState.retryMode  = true;
                        fbState.retryIndex = 0;
                        setStatus("Good job! Now let's retry " + fbState.retryQueue.length + " missed word(s).");
                        await new Promise(r => setTimeout(r, 400));
                        renderContextFill(el);
                    } else {
                        fbState.initialized = false;
                        items.forEach(it => { if (!wrongMap[it.id]) _trackWordAttempt(it, true, it.answer); });
                        setStatus("Fill the Blank complete!");
                        await new Promise(r => setTimeout(r, 400));
                        advanceToNextStage();
                    }
                } else {
                    setStatus("Correct!");
                    await new Promise(r => setTimeout(r, 300));
                    renderContextFill(el);
                }
            }
        } else {
            // Wrong
            if (inp) {
                inp.classList.remove("filled", "correct");
                inp.classList.add("wrong");
            }
            bumpWrong(item);
            stageFxWrong();
            fbState.mistakeCount[item.id] = (fbState.mistakeCount[item.id] || 0) + 1;
            const mc = fbState.mistakeCount[item.id];

            if (mc >= CONF.FB_MAX_STRIKES) {
                if (!fbState.retryQueue.find(it => it.id === item.id)) {
                    fbState.retryQueue.push(item);
                }
                setStatus("Tough one — we'll come back to it!");
                await new Promise(r => setTimeout(r, 700));
                if (!isRetry) {
                    stageIndex++;
                    if (stageIndex >= items.length) {
                        fbState.retryMode  = true;
                        fbState.retryIndex = 0;
                        fbState.retryQueue.forEach(it => { fbState.mistakeCount[it.id] = 0; });
                        setStatus("Let's retry the words you missed!");
                    }
                } else {
                    fbState.retryIndex++;
                }
                renderContextFill(el);
            } else {
                setStatus(mc === 1 ? "Not quite! Check the hint below." : "Try again — stronger hint!");
                await new Promise(r => setTimeout(r, 500));
                renderFillItem(el, item, isRetry);
            }
        }
    };

    submitBtn.addEventListener("click", doSubmit);
    if (inp) inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); doSubmit(); } });
}
