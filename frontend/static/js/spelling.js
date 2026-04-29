/* ================================================================
   spelling.js — Step 4: Spelling Master (3-pass masked word + retry queue).
   Section: English / Spelling
   Dependencies: core.js, tts-client.js, analytics.js
   API endpoints: /api/tts/word_only (via apiWordOnly)
   ================================================================ */

/**
 * Build the display mask for a word at a given pass (1–3).
 * Phonics-based progression (pedagogically grounded):
 *   Pass 1: hide vowels only — reinforces consonant/vowel recognition ("wound" → "w_ _nd").
 *   Pass 2: show first + last letter only — anchors word boundaries ("wound" → "w___d").
 *   Pass 3: hide everything — full recall.
 * Fallback for words with no vowels (rare, e.g. "hmm"): hide every other alpha char.
 * @tag SPELLING ENGLISH
 */
function makeSpellMask(word, pass) {
    const chars    = [...word];
    const alphaIdx = chars.map((c, i) => /[a-zA-Z]/.test(c) ? i : -1).filter(i => i >= 0);
    if (!alphaIdx.length) return "____";

    if (pass === CONF.SPELLING_PASSES) {
        return chars.map(c => /[a-zA-Z]/.test(c) ? "_" : c).join("");
    }

    if (pass === 1) {
        const vowelIdx = alphaIdx.filter(i => /[aeiouAEIOU]/.test(chars[i]));
        if (vowelIdx.length > 0) {
            const hide = new Set(vowelIdx);
            return chars.map((c, i) => hide.has(i) ? "_" : c).join("");
        }
        const hide = new Set(alphaIdx.filter((_, k) => k % 2 === 1));
        return chars.map((c, i) => hide.has(i) ? "_" : c).join("");
    }

    const keep = new Set([alphaIdx[0], alphaIdx[alphaIdx.length - 1]]);
    return chars.map((c, i) => (/[a-zA-Z]/.test(c) && !keep.has(i)) ? "_" : c).join("");
}

/**
 * Entry point for the Spelling Master stage.
 * Dispatches to retry mode or main-pass rendering based on spState.
 * @tag SPELLING ENGLISH
 */
function renderSpelling(el) {
    if (!spState.initialized) {
        spState.initialized = true;
        spState.pass        = 1;
        spState.retryQueue  = [];
        spState.retryMode   = false;
        spState.retryIndex  = 0;
        spState.masks       = {};
        stageIndex = 0;
        const shuffled = shuffle(items);
        items.splice(0, items.length, ...shuffled);
    }

    if (spState.retryMode) {
        if (spState.retryIndex >= spState.retryQueue.length) {
            spState.initialized = false;
            advanceToNextStage();
            return;
        }
        renderSpellItem(el, spState.retryQueue[spState.retryIndex], true);
        return;
    }

    const item = items[stageIndex];
    if (!item) {
        if (spState.retryQueue.length > 0) {
            spState.retryMode  = true;
            spState.retryIndex = 0;
            spState.pass       = 1;
            spState.masks      = {};
            setStatus("Let's redo the tricky ones — you can do it!");
            renderSpelling(el);
        } else {
            spState.initialized = false;
            advanceToNextStage();
        }
        return;
    }

    if (!spState.masks[stageIndex]) {
        spState.masks[stageIndex] = {
            1: makeSpellMask(item.answer, 1),
            2: makeSpellMask(item.answer, 2),
            3: makeSpellMask(item.answer, 3),
        };
    }

    renderSpellItem(el, item, false);
}

/**
 * Render a single spelling item (main pass or retry).
 * @tag SPELLING ENGLISH
 */
function renderSpellItem(el, item, isRetry) {
    const total   = isRetry ? spState.retryQueue.length : items.length;
    const current = isRetry ? spState.retryIndex + 1 : stageIndex + 1;
    const pass    = spState.pass;

    let mask;
    if (isRetry) {
        mask = makeSpellMask(item.answer, pass);
    } else {
        mask = (spState.masks[stageIndex] || {})[pass] || makeSpellMask(item.answer, pass);
    }

    // Labels match the phonics-based mask progression (vowels → first+last → all).
    const passDesc = pass === 1 ? "Vowels are hidden"
                   : pass === 2 ? "Only the first and last letter"
                   : "All hidden — type from memory!";
    const retryLabel = isRetry ? " — Retry" : "";
    const progLabel  = `${current} / ${total}${isRetry ? " retries" : ""} &nbsp;·&nbsp; Pass ${pass}/${CONF.SPELLING_PASSES}`;

    const badgeBg = pass === CONF.SPELLING_PASSES
        ? "var(--color-error, #FF3B30)"
        : "var(--color-primary, #D4619E)";

    // Letter count — especially critical for Pass 2 (first+last only) and Pass 3 (all hidden).
    const letterCount = (item.answer.match(/[a-zA-Z]/g) || []).length;
    const letterHint  = `<p class="sp-letter-hint">${letterCount} letter${letterCount === 1 ? '' : 's'}</p>`;

    // Retry mode: soften the tone — the child already missed this once.
    const subText = isRetry
        ? `One more try — you've got this! &nbsp;·&nbsp; ${escapeHtml(passDesc)}`
        : `${escapeHtml(passDesc)} &nbsp;·&nbsp; Listen, then type the word.`;

    el.innerHTML = `
        <p class="st-h1">Step 4 — Spelling Master${retryLabel}</p>
        <p class="st-sub">${subText}</p>
        <div style="text-align:center">
            <span class="sp-pass-badge" style="background:${badgeBg}">
                Pass ${pass} / ${CONF.SPELLING_PASSES}
            </span>
        </div>
        <div class="sp-mask-box">${escapeHtml(mask)}</div>
        ${letterHint}
        <p class="sp-meaning">${escapeHtml(item.question)}</p>
        <div class="st-input-row">
            <input class="st-input" id="answer-input" type="text" maxlength="${item.answer.length}"
                   autocomplete="off" spellcheck="false" placeholder="Type the word…"/>
            <button type="button" class="st-btn ghost" id="btn-listen-word"><i data-lucide="volume-2"></i> Listen</button>
            <button type="button" class="st-btn" id="spell-submit">Check</button>
        </div>
        <p id="sp-feedback" class="sp-feedback"></p>
        <p class="st-prog">${progLabel}</p>
    `;
    requestAnimationFrame(() => { if (window.lucide) lucide.createIcons(); });

    const inp       = el.querySelector("#answer-input");
    const submitBtn = el.querySelector("#spell-submit");
    const feedback  = el.querySelector("#sp-feedback");
    if (inp) inp.focus();

    const listenBtn = el.querySelector("#btn-listen-word");
    if (listenBtn) listenBtn.addEventListener("click", async () => {
        setStatus("Listening\u2026");
        await apiWordOnly(item.answer);
    });

    const lockInput = () => {
        if (inp)       inp.disabled       = true;
        if (submitBtn) submitBtn.disabled = true;
    };

    const doCheck = async () => {
        const val = (inp.value || "").trim();
        if (!val) return;

        if (val.toLowerCase() === item.answer.toLowerCase()) {
            // Correct
            lockInput();
            if (pass < CONF.SPELLING_PASSES) {
                inp.style.borderColor = "var(--color-success)";
                inp.style.boxShadow   = "0 0 0 4px var(--color-success-light)";
                feedback.style.color  = "var(--color-success-ink)";
                feedback.textContent  = "Pass " + pass + " \u2713";
                spState.pass++;
                setStatus("Pass " + pass + " done! Now pass " + spState.pass + "\u2026");
                await new Promise(r => setTimeout(r, 600));
                renderSpelling(el);
            } else {
                // All passes correct — word complete
                stageFxCorrect();
                inp.style.borderColor = "var(--color-success)";
                inp.style.boxShadow   = "0 0 0 4px var(--color-success-light)";
                feedback.style.color  = "var(--color-success-ink)";
                feedback.textContent  = "Perfect Spelling!";
                spState.pass = 1;
                if (!spState.masks[stageIndex]) spState.masks[stageIndex] = {};
                starCount++;
                updateStars();
                addWordVault(item.answer);

                if (!isRetry) {
                    stageIndex++;
                } else {
                    spState.retryIndex++;
                }
                setStatus("Spelling master!");
                await new Promise(r => setTimeout(r, 700));
                renderSpelling(el);
            }
        } else {
            // Wrong — show answer briefly, then move on
            bumpWrong(item);
            stageFxWrong();
            lockInput();
            inp.value             = "";
            inp.style.borderColor = "var(--color-error, #FF3B30)";
            inp.style.boxShadow   = "0 0 0 4px var(--color-error-light, rgba(255,59,48,0.12))";
            feedback.style.color  = "var(--color-error, #FF3B30)";
            feedback.textContent  = "Answer: " + item.answer;

            if (!spState.retryQueue.find(it => it.id === item.id)) {
                spState.retryQueue.push(item);
            }

            setStatus("Not quite \u2014 moving on, we\u2019ll retry it!");
            await new Promise(r => setTimeout(r, CONF.WRONG_ANSWER_DISPLAY));

            spState.pass = 1;
            if (!isRetry) {
                stageIndex++;
                if (stageIndex >= items.length) {
                    if (spState.retryQueue.length > 0) {
                        spState.retryMode  = true;
                        spState.retryIndex = 0;
                    } else {
                        spState.initialized = false;
                        advanceToNextStage();
                        return;
                    }
                }
            } else {
                spState.retryIndex++;
            }
            renderSpelling(el);
        }
    };

    if (submitBtn) submitBtn.addEventListener("click", doCheck);
    if (inp) inp.addEventListener("keydown", (e) => { if (e.key === "Enter") doCheck(); });
}
