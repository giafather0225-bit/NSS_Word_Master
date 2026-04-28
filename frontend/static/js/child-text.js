/* ================================================================
   child-text.js — Friendly-text replacement pass for stage UI
   Section: English / System
   Dependencies: none (DOM only)
   API endpoints: none
   ================================================================ */

/**
 * Friendly-text replacements for stage sub-titles and placeholders.
 * @tag ENGLISH SYSTEM
 */
const TEXT_REPLACEMENTS = {
    'Click a word, then click its meaning.':
        'Tap a word on the left, then find its meaning on the right.',
    'Type the missing word…':
        'Type the missing word.',
    'Some letters hidden':
        'Some letters are hidden.',
    'More letters hidden':
        'More letters are hidden now!',
    'Listen, then type the word.':
        'Listen and type the word.',
    'Use this word in a sentence':
        'Write a sentence using this word.',
};

/** @tag ENGLISH SYSTEM */
const roundRegex = /Round (\d+) of (\d+)\s*[·•]\s*Words (\d+)[–-](\d+)\s*[·•]\s*Click a word, then click its meaning\./;

/**
 * Walk .st-sub elements and apply friendly text replacements.
 * @tag ENGLISH SYSTEM
 */
function replaceDescriptionTexts() {
    document.querySelectorAll('.st-sub').forEach(el => {
        const roundMatch = el.textContent.match(roundRegex);
        if (roundMatch) {
            el.innerHTML = `Round ${roundMatch[1]}/${roundMatch[2]} · Words ${roundMatch[3]}–${roundMatch[4]} · Tap a word, then find its meaning! 👉`;
            return;
        }
        for (const [original, replacement] of Object.entries(TEXT_REPLACEMENTS)) {
            if (original === replacement) continue;
            if (el.textContent.includes(original)) {
                const next = el.textContent.replace(original, replacement);
                if (next !== el.textContent) el.textContent = next;
            }
        }
    });

    const answerInput = document.querySelector('#answer-input');
    if (answerInput) {
        if (answerInput.placeholder === 'Type the missing word…') {
            answerInput.placeholder = 'Type the missing word...';
        } else if (answerInput.placeholder === 'Type the word…') {
            answerInput.placeholder = 'Type the word...';
        }
    }

    const sentenceInput = document.querySelector('#sentence-input');
    if (sentenceInput && sentenceInput.placeholder === 'Your sentence…') {
        sentenceInput.placeholder = 'Write your sentence here...';
    }
}
