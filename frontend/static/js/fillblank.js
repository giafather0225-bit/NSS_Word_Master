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
            setStatus("Almost there! Let's retry the ones you missed. 💪");
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
 * @tag FILL_BLANK ENGLISH
 */
function renderFillItem(el, item, isRetry) {
    const example  = item.hint && String(item.hint).trim() ? item.hint : "";
    const mistakes = fbState.mistakeCount[item.id] || 0;
    const total    = isRetry ? fbState.retryQueue.length : items.length;
    const current  = isRetry ? fbState.retryIndex + 1 : stageIndex + 1;

    // Word-chip list (shuffled, already-done ones greyed out)
    const displayOrder = items.map((it, i) => ({ it, i }));
    for (let k = displayOrder.length - 1; k > 0; k--) {
        const j = Math.floor(Math.random() * (k + 1));
        [displayOrder[k], displayOrder[j]] = [displayOrder[j], displayOrder[k]];
    }
    const wordBoxHtml = displayOrder.map(({ it, i }) => {
        const used = !isRetry && i < stageIndex;
        return `<span class="fb-word${used ? " fb-used" : ""}">${escapeHtml(it.answer)}</span>`;
    }).join(" ");

    let hintHtml = "";
    if (mistakes >= 1) {
        const len = String(item.answer).length;
        hintHtml = `<p class="hint-line">💡 ${len} letters</p>`;
    }
    if (mistakes >= 2) {
        const first = String(item.answer).charAt(0).toUpperCase();
        hintHtml = `<p class="hint-line">💡 Starts with <strong>${escapeHtml(first)}</strong> · ${String(item.answer).length} letters</p>`;
    }

    const blanked    = example ? replaceWordWithBlank(example, item.answer) : "(no example sentence)";
    const retryLabel = isRetry ? " — Retry" : "";
    const progLabel  = `${current} / ${total}${isRetry ? " retries" : ""}`;

    el.innerHTML = `
        <p class="st-h1">Step 3 — Fill the Blank${retryLabel}</p>
        <div class="fb-word-box">${wordBoxHtml}</div>
        <div class="example-box">${escapeHtml(blanked)}</div>
        ${hintHtml}
        <div class="st-input-row">
            <input class="st-input" id="answer-input" type="text"
                   autocomplete="off" spellcheck="false" placeholder="Type the missing word…"/>
            <button type="button" class="st-btn" id="ctx-submit">Check ✓</button>
        </div>
        <p class="st-prog">${progLabel}</p>
    `;

    const inp = el.querySelector("#answer-input");
    if (inp) inp.focus();

    // Word-chip click → auto-fill input
    el.querySelectorAll(".fb-word").forEach(function(span) {
        if (span.classList.contains("fb-used")) {
            span.style.cursor = "default";
            return;
        }
        span.style.cursor = "pointer";
        span.addEventListener("click", function() {
            if (span.classList.contains("fb-used")) return;
            if (inp) {
                inp.value = span.textContent.trim();
                inp.focus();
            }
        });
    });

    const submitBtn = el.querySelector("#ctx-submit");
    if (!submitBtn) return;

    const doSubmit = async () => {
        const val = (inp.value || "").trim();
        if (!val) return;

        if (val.toLowerCase() === item.answer.toLowerCase()) {
            // Correct
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
                        setStatus("Good job! Now let's retry " + fbState.retryQueue.length + " missed word(s). 💪");
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
                    setStatus("Correct! ✓");
                    await new Promise(r => setTimeout(r, 300));
                    renderContextFill(el);
                }
            }
        } else {
            // Wrong
            bumpWrong(item);
            stageFxWrong();
            fbState.mistakeCount[item.id] = (fbState.mistakeCount[item.id] || 0) + 1;
            const mc = fbState.mistakeCount[item.id];
            inp.value = "";

            if (mc >= CONF.FB_MAX_STRIKES) {
                if (!fbState.retryQueue.find(it => it.id === item.id)) {
                    fbState.retryQueue.push(item);
                }
                setStatus("Tough one — we'll come back to it! ❌");
                await new Promise(r => setTimeout(r, 600));
                if (!isRetry) {
                    stageIndex++;
                    if (stageIndex >= items.length) {
                        fbState.retryMode  = true;
                        fbState.retryIndex = 0;
                        fbState.retryQueue.forEach(it => { fbState.mistakeCount[it.id] = 0; });
                        setStatus("Let's retry the words you missed! 💪");
                    }
                } else {
                    fbState.retryIndex++;
                }
                renderContextFill(el);
            } else {
                setStatus(mc === 1 ? "Not quite! Check the hint below. 💡" : "Try again — stronger hint! 💡💡");
                renderFillItem(el, item, isRetry);
            }
        }
    };

    submitBtn.addEventListener("click", doSubmit);
    if (inp) inp.addEventListener("keydown", (e) => { if (e.key === "Enter") doSubmit(); });
}
