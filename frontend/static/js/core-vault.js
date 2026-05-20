/* ================================================================
   core-vault.js — Word vault state + helpers (extracted from core.js)
   Section: English / System
   Dependencies: core.js ($())
   API endpoints: none
   ================================================================ */

// ─── Word vault ───────────────────────────────────────────────
// Set of words the child has flagged during a study session. Rendered
// as a horizontal chip strip below the stage card.
/** @tag MY_WORDS */
const wordVaultSet = new Set();

/**
 * Render the word-vault chip list. No-op if the container is absent.
 * @tag MY_WORDS DAILY_WORDS
 */
function renderWordVault() {
    const el = $("word-vault");
    if (!el) return;
    el.innerHTML = "";
    [...wordVaultSet].sort((a, b) => a.localeCompare(b)).forEach((w) => {
        const s = document.createElement("span");
        s.className = "vault-chip";
        s.textContent = w;
        el.appendChild(s);
    });
}

/**
 * Add a word to the vault and re-render. Trims the input and drops
 * empty strings.
 * @tag MY_WORDS DAILY_WORDS
 */
function addWordVault(word) {
    const w = String(word || "").trim();
    if (!w) return;
    wordVaultSet.add(w);
    renderWordVault();
}
