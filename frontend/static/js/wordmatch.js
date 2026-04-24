/* ================================================================
   wordmatch.js — Step 2: Word Match (dual-column matching with SVG lines).
   Section: English / Word Match
   Palette B — connector uses var(--color-success) Sage; ghost uses
   var(--section-primary) Baby Blue.
   Dependencies: core.js, tts-client.js, analytics.js
   API endpoints: none
   ================================================================ */

/**
 * Remove the scroll/resize handlers that redraw SVG lines, and remove the SVG overlay.
 * @tag WORD_MATCH SYSTEM
 */
function clearWmScrollHandler() {
    if (wmState.scrollHandler) {
        window.removeEventListener("scroll", wmState.scrollHandler, true);
        window.removeEventListener("resize", wmState.scrollHandler, true);
        wmState.scrollHandler = null;
    }
    const old = document.getElementById("wm-svg-overlay");
    if (old) old.remove();
}

/**
 * Double-rAF scheduler — ensures layout is finalized (fonts, reflow) before drawing.
 * @tag WORD_MATCH
 */
function scheduleWmDraw() {
    requestAnimationFrame(function () {
        requestAnimationFrame(drawWmLines);
    });
}

/**
 * Re-draw all Bezier connection lines for matched word–meaning pairs,
 * plus a Baby Blue ghost line for the currently selected word (if any).
 * @tag WORD_MATCH
 */
function drawWmLines() {
    const svg = document.getElementById("wm-svg-overlay");
    if (!svg) return;
    const host = svg.parentElement;
    if (!host) return;
    const colRect = host.getBoundingClientRect();
    if (colRect.width === 0) return; // layout not ready

    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Solid lines — matched pairs
    for (const mi of wmState.matched) {
        const wordBtn    = document.getElementById("wm-w-" + mi);
        const meaningBtn = document.getElementById("wm-m-" + mi);
        if (!wordBtn || !meaningBtn) continue;

        const wr = wordBtn.getBoundingClientRect();
        const mr = meaningBtn.getBoundingClientRect();

        const x1 = wr.right - colRect.left;
        const y1 = (wr.top + wr.bottom) / 2 - colRect.top;
        const x2 = mr.left - colRect.left;
        const y2 = (mr.top + mr.bottom) / 2 - colRect.top;
        const cx = (x1 + x2) / 2;

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", "M " + x1 + " " + y1 + " C " + cx + " " + y1 + " " + cx + " " + y2 + " " + x2 + " " + y2);
        svg.appendChild(path);
    }

    // Ghost line — currently selected word (not yet matched)
    if (wmState.selectedWordIdx !== null && !wmState.matched.has(wmState.selectedWordIdx)) {
        const wordBtn = document.getElementById("wm-w-" + wmState.selectedWordIdx);
        if (wordBtn) {
            const wr = wordBtn.getBoundingClientRect();
            const x1 = wr.right - colRect.left;
            const y1 = (wr.top + wr.bottom) / 2 - colRect.top;
            const x2 = colRect.width + 10; // extend 10px past connector
            const y2 = y1;
            const cx = (x1 + x2) / 2;

            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", "M " + x1 + " " + y1 + " C " + cx + " " + y1 + " " + cx + " " + y2 + " " + x2 + " " + y2);
            path.classList.add("ghost");
            svg.appendChild(path);
        }
    }
}

/**
 * Update button visual states (selected/matched) and progress text
 * without re-rendering the entire stage.
 * @tag WORD_MATCH
 */
function updateWmButtonStates(el) {
    el.querySelectorAll(".wm-word-btn").forEach(btn => {
        const idx = Number(btn.dataset.idx);
        const matched  = wmState.matched.has(idx);
        const selected = wmState.selectedWordIdx === idx;
        btn.classList.toggle("wm-matched", matched);
        btn.classList.toggle("wm-selected", selected && !matched);
        btn.disabled = matched;
    });
    el.querySelectorAll(".wm-meaning-btn").forEach(btn => {
        const idx = Number(btn.dataset.idx);
        const matched = wmState.matched.has(idx);
        btn.classList.toggle("wm-matched", matched);
        btn.disabled = matched;
    });
    const prog = el.querySelector(".st-prog");
    if (prog) {
        const batchStart = wmState.batchIdx * wmState.BATCH_SIZE;
        const batchEnd   = Math.min(batchStart + wmState.BATCH_SIZE, items.length);
        let batchMatchedCount = 0;
        for (let i = batchStart; i < batchEnd; i++) {
            if (wmState.matched.has(i)) batchMatchedCount++;
        }
        prog.textContent = batchMatchedCount + " / " + (batchEnd - batchStart) + " matched";
    }
    scheduleWmDraw();
}

/**
 * Render the Word Match stage for the current batch/round.
 * @tag WORD_MATCH ENGLISH
 */
function renderMeaningMatch(el) {
    clearWmScrollHandler();

    if (!wmState.initialized) {
        wmState.initialized = true;
        const shuffled = shuffle(items);
        items.splice(0, items.length, ...shuffled);
        wmState.reset();
        wmState.initialized = true;
    }

    const n = items.length;
    if (!n) { advanceToNextStage(); return; }

    const batchStart   = wmState.batchIdx * wmState.BATCH_SIZE;
    const batchEnd     = Math.min(batchStart + wmState.BATCH_SIZE, n);
    const totalBatches = Math.ceil(n / wmState.BATCH_SIZE);
    const batchSize    = batchEnd - batchStart;

    if (!wmState.shuffleOrder) {
        const batchIndices = [];
        for (let i = batchStart; i < batchEnd; i++) batchIndices.push(i);
        wmState.shuffleOrder = shuffle(batchIndices);
    }

    const roundLabel = "Round " + (wmState.round + 1) + " of 3"
        + (totalBatches > 1 ? " \u00b7 Words " + (batchStart + 1) + "\u2013" + batchEnd : "");

    let wordColHtml = "";
    for (let i = batchStart; i < batchEnd; i++) {
        const matched  = wmState.matched.has(i);
        const selected = wmState.selectedWordIdx === i;
        const cls = "wm-word-btn" + (matched ? " wm-matched" : selected ? " wm-selected" : "");
        const dis = matched ? " disabled" : "";
        wordColHtml += "<button class='" + cls + "' id='wm-w-" + i + "' data-idx='" + i + "' type='button'" + dis + ">"
                    + escapeHtml(items[i].answer) + "</button>";
    }

    let meaningColHtml = "";
    for (let k = 0; k < wmState.shuffleOrder.length; k++) {
        const mi = wmState.shuffleOrder[k];
        const matched = wmState.matched.has(mi);
        const cls = "wm-meaning-btn" + (matched ? " wm-matched" : "");
        const dis = matched ? " disabled" : "";
        meaningColHtml += "<button class='" + cls + "' id='wm-m-" + mi + "' data-idx='" + mi + "' type='button'" + dis + ">"
                       + escapeHtml(items[mi].question) + "</button>";
    }

    let batchMatchedCount = 0;
    for (let i = batchStart; i < batchEnd; i++) {
        if (wmState.matched.has(i)) batchMatchedCount++;
    }

    el.innerHTML = "<p class='st-h1'>Step 2 \u2014 Word Match</p>"
        + "<p class='st-sub'>" + escapeHtml(roundLabel) + " &nbsp;\u00b7&nbsp; Click a word, then click its meaning.</p>"
        + "<div class='wm-grid'>"
        +   "<div class='wm-col wm-col-words'>" + wordColHtml + "</div>"
        +   "<div class='wm-col-connector'></div>"
        +   "<div class='wm-col wm-col-meanings'>" + meaningColHtml + "</div>"
        + "</div>"
        + "<p class='st-prog'>" + batchMatchedCount + " / " + batchSize + " matched</p>";

    // SVG overlay inside connector column (no longer body-fixed)
    const svgNS = "http://www.w3.org/2000/svg";
    const connectorCol = el.querySelector(".wm-col-connector");
    if (connectorCol) {
        const svgEl = document.createElementNS(svgNS, "svg");
        svgEl.setAttribute("id", "wm-svg-overlay");
        svgEl.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible";
        connectorCol.appendChild(svgEl);
    }

    scheduleWmDraw();

    wmState.scrollHandler = function () { scheduleWmDraw(); };
    window.addEventListener("scroll", wmState.scrollHandler, { passive: true, capture: true });
    window.addEventListener("resize", wmState.scrollHandler, { passive: true });

    // Wire word buttons
    el.querySelectorAll(".wm-word-btn:not([disabled])").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const idx = Number(btn.dataset.idx);
            wmState.selectedWordIdx = (wmState.selectedWordIdx === idx) ? null : idx;
            updateWmButtonStates(el);
        });
    });

    // Wire meaning buttons
    el.querySelectorAll(".wm-meaning-btn:not([disabled])").forEach(function (btn) {
        btn.addEventListener("click", async function () {
            if (wmState.selectedWordIdx === null) {
                setStatus("👈 Click a word first!");
                return;
            }
            const mi = Number(btn.dataset.idx);
            const prevSelected = wmState.selectedWordIdx;

            if (prevSelected === mi) {
                // Correct match
                wmState.matched.add(mi);
                wmState.selectedWordIdx = null;
                stageFxCorrect();
                starCount++;
                updateStars();
                addWordVault(items[mi].answer);

                let batchDone = true;
                for (let i = batchStart; i < batchEnd; i++) {
                    if (!wmState.matched.has(i)) { batchDone = false; break; }
                }

                if (batchDone) {
                    scheduleWmDraw();
                    await new Promise(function (r) { setTimeout(r, 700); });

                    const hasNextBatch = (wmState.batchIdx + 1) < totalBatches;
                    if (hasNextBatch) {
                        wmState.batchIdx++;
                        wmState.selectedWordIdx = null;
                        wmState.shuffleOrder    = null;
                        setStatus("Great! Keep going \u2014 next group! \ud83d\udcaa");
                        renderMeaningMatch(el);
                    } else if (wmState.round < 2) {
                        wmState.round++;
                        wmState.batchIdx        = 0;
                        wmState.matched         = new Set();
                        wmState.selectedWordIdx = null;
                        wmState.shuffleOrder    = null;
                        setStatus("Round " + (wmState.round + 1) + " \u2014 go! \ud83d\udd04");
                        renderMeaningMatch(el);
                    } else {
                        items.forEach(it => { if (!wrongMap[it.id]) _trackWordAttempt(it, true, it.answer); });
                        setStatus("Word Match complete!");
                        await new Promise(function (r) { setTimeout(r, 600); });
                        clearWmScrollHandler();
                        advanceToNextStage();
                    }
                } else {
                    renderMeaningMatch(el);
                }
            } else {
                // Wrong match — flash BOTH the picked word and the clicked meaning
                // in Dusty Coral so the child clearly sees which pair was wrong.
                stageFxWrong();
                const wrongWordBtn = el.querySelector("#wm-w-" + prevSelected);
                btn.classList.add("wm-shake", "wm-wrong");
                if (wrongWordBtn) wrongWordBtn.classList.add("wm-wrong");
                setStatus("Not quite — try again!");
                await new Promise(function (r) { setTimeout(r, 700); });
                btn.classList.remove("wm-shake", "wm-wrong");
                if (wrongWordBtn) wrongWordBtn.classList.remove("wm-wrong");
                wmState.selectedWordIdx = null;
                renderMeaningMatch(el);
            }
        });
    });
}
