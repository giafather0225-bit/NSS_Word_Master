/* ================================================================
   core-stage.js — Stage-card visibility + sentence string helpers
                   (extracted from core.js)
   Section: English / System
   Dependencies: core.js ($(), escapeRe, sessionActive),
                 navigation.js (switchView, optional)
   API endpoints: none
   ================================================================ */

// ─── Stage-card visibility ────────────────────────────────────

/**
 * Exit the active English lesson — cancel any TTS, drop the lesson
 * header, and either route back to the English idle view or fall
 * back to the generic idle card.
 * @tag ENGLISH NAVIGATION
 */
function exitEnglishLesson() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (typeof sessionActive !== 'undefined') { window.sessionActive = false; }
    const hdr = document.getElementById('english-lesson-header');
    if (hdr) hdr.remove();
    if (typeof switchView === 'function') switchView('english');
    else showIdleCard();
}

/**
 * Show the idle card, hide the stage card. Also restores the sidebar
 * to its expanded state and clears the persisted collapse flag.
 * @tag NAVIGATION
 */
function showIdleCard() {
    const _engHdr = document.getElementById('english-lesson-header');
    if (_engHdr) _engHdr.remove();

    const iw = $("idle-wrapper");
    const sc = $("stage-card");
    if (iw) iw.classList.remove("hidden");
    if (sc) sc.classList.add("hidden");
    const _sb = document.getElementById("sidebar");
    if (_sb) _sb.classList.remove("collapsed");
    localStorage.removeItem('sb_collapsed');
}

/**
 * Show the stage card, hide the idle card. Re-creates an empty #stage
 * child if the previous transition removed it; preserves the existing
 * .stage-header (#roadmap) so nav doesn't flash.
 * @tag NAVIGATION
 */
function showStageCard() {
    const iw = $("idle-wrapper");
    const sc = $("stage-card");
    if (iw) iw.classList.add("hidden");
    if (sc) {
        sc.classList.remove("hidden");
        sc.style.display = "";
        sc.classList.remove("fx-swoosh");
        if (!sc.querySelector("#stage")) {
            const stageDiv = document.createElement('div');
            stageDiv.id = 'stage';
            sc.appendChild(stageDiv);
        }
    }
}

/**
 * Animate the stage card out with a swoosh, then call onDone after
 * the animation completes (~440 ms).
 * @tag NAVIGATION SYSTEM
 */
function animateStageClear(onDone) {
    const card = $("stage-card");
    if (!card) {
        if (onDone) onDone();
        return;
    }
    card.classList.add("fx-swoosh");
    setTimeout(() => {
        if (onDone) onDone();
    }, 440);
}

// ─── Sentence utilities ───────────────────────────────────────

/**
 * Replace all (case-insensitive) occurrences of word in sentence with
 * "________".
 * @tag FILL_BLANK FINAL_TEST
 */
function replaceWordWithBlank(sentence, word) {
    const re = new RegExp(escapeRe(word), "gi");
    return String(sentence).replace(re, "________");
}

/**
 * Return true if sentence contains word. Uses a word-boundary check
 * for Latin words; falls back to substring contains for anything else.
 * @tag SENTENCE FILL_BLANK
 */
function sentenceHasWord(sentence, word) {
    const w = String(word).trim();
    if (!w) return false;
    if (/^[a-zA-Z-']+$/.test(w)) {
        return new RegExp(`\\b${escapeRe(w)}\\b`, "i").test(sentence);
    }
    return sentence.toLowerCase().includes(w.toLowerCase());
}
