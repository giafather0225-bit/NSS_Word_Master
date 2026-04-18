/* ================================================================
   analytics.js — Learning analytics tracking (stage start/complete,
                  word attempts, challenge-reset counters).
   Section: System
   Dependencies: core.js
   API endpoints: /api/learning/log, /api/learning/word-attempts-batch
   ================================================================ */

// ─── Per-stage tracking state ─────────────────────────────────
/**
 * ISO timestamp when the current stage was started.
 * @tag SYSTEM
 */
let _stageStartTime = null;

/**
 * Accumulated word-attempt records for the current stage.
 * @tag SYSTEM
 */
let _stageAttempts = [];

/**
 * Record that a new stage run has begun.
 * Resets the start timestamp and attempts buffer.
 * @tag SYSTEM NAVIGATION
 */
function _trackStageStart() {
    _stageStartTime = new Date().toISOString();
    _stageAttempts = [];
}

/**
 * Append a single word-attempt record to the current-stage buffer.
 * @tag SYSTEM ACTIVE_RECALL
 */
function _trackWordAttempt(item, isCorrect, userAnswer) {
    _stageAttempts.push({
        study_item_id: item.id,
        textbook: currentTextbook,
        lesson: selectedLesson,
        word: item.answer || item.word || "",
        stage: stage || "",
        is_correct: isCorrect,
        user_answer: userAnswer || "",
        attempted_at: new Date().toISOString()
    });
}

/**
 * POST the completed stage log and all word-attempt records to the backend,
 * then reset the tracking state.
 * @tag SYSTEM NAVIGATION
 */
function _trackStageComplete(completedStage) {
    const now = new Date().toISOString();
    const durationSec = _stageStartTime
        ? Math.round((new Date(now) - new Date(_stageStartTime)) / 1000)
        : 0;
    const wordCount = items.length || 0;
    const wrongKeys = Object.keys(wrongMap).filter(k => wrongMap[k] > 0);
    const correctCount = wordCount - wrongKeys.length;
    const wrongWords = wrongKeys.map(k => {
        const it = items.find(i => String(i.id) === String(k));
        return it ? (it.answer || it.word || k) : k;
    });

    fetch("/api/learning/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            textbook: currentTextbook,
            lesson: selectedLesson,
            stage: completedStage || "",
            word_count: wordCount,
            correct_count: Math.max(0, correctCount),
            wrong_words: wrongWords,
            started_at: _stageStartTime || "",
            completed_at: now,
            duration_sec: durationSec
        })
    }).catch(() => {});

    if (_stageAttempts.length > 0) {
        fetch("/api/learning/word-attempts-batch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ attempts: _stageAttempts })
        }).catch(() => {});
    }

    _stageStartTime = null;
    _stageAttempts = [];
}

// ─── XP Award Helpers ─────────────────────────────────────────

/**
 * Award XP for a word answered correctly.
 * Called by stage modules on each correct answer.
 * @tag XP @tag AWARD @tag ACADEMY
 * @param {string} word - The word that was answered correctly
 */
async function _awardWordXP(word) {
    try {
        await fetch('/api/xp/award', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'word_correct', detail: word })
        });
    } catch (_) {}
}

/**
 * Award XP for completing a stage and refresh home dashboard if visible.
 * @tag XP @tag AWARD @tag ACADEMY
 * @param {string} completedStage - The stage key that was completed
 */
async function _awardStageXP(completedStage) {
    try {
        const res = await fetch('/api/xp/award', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'stage_complete', detail: completedStage })
        });
        if (res.ok) {
            const data = await res.json();
            // Refresh summary bar if home is visible
            if (typeof renderSummaryBar === 'function' && document.getElementById('home-dashboard')) {
                renderSummaryBar();
            }
            // Always update the top bar XP display
            if (typeof _updateTopBarXP === 'function') {
                _updateTopBarXP(data);
            }
            // Show XP toast if we earned XP
            if (data.xp_awarded > 0) _showXPToast(`+${data.xp_awarded} XP`);
            if (data.bonus_xp > 0) _showXPToast(`Streak bonus +${data.bonus_xp} XP!`);
        }
    } catch (_) {}
}

/**
 * Award XP for completing a review session.
 * @tag XP @tag AWARD @tag REVIEW
 */
async function _awardReviewXP() {
    try {
        await fetch('/api/xp/award', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'review_complete', detail: '' })
        });
    } catch (_) {}
}

/**
 * Brief XP toast notification.
 * @tag XP @tag HOME_DASHBOARD
 * @param {string} text - Toast message to show
 */
function _showXPToast(text) {
    const toast = document.createElement('div');
    toast.className = 'xp-toast';
    toast.textContent = text;
    document.body.appendChild(toast);
    requestAnimationFrame(() => { toast.classList.add('show'); });
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
    // Also show a float-up particle near the XP count in the top bar
    const layer = document.getElementById('particle-layer');
    const starsEl = document.getElementById('stars-count');
    if (layer && starsEl) {
        const rect = starsEl.getBoundingClientRect();
        const floater = document.createElement('div');
        floater.className = 'xp-float';
        floater.textContent = text;
        floater.style.left = rect.left + 'px';
        floater.style.top = rect.top + 'px';
        layer.appendChild(floater);
        setTimeout(() => floater.remove(), 1300);
    }
}

// ─── Challenge-reset counter (sessionStorage, per-day key) ────
/**
 * Build today's challenge-reset sessionStorage key.
 * @tag FINAL_TEST SYSTEM
 */
function challengeResetStorageKey() {
    return `nss_challenge_reset_${new Date().toISOString().slice(0, 10)}`;
}

/**
 * Remove stale per-day challenge-reset keys from sessionStorage.
 * Called once at startup; only today's key survives.
 * @tag FINAL_TEST SYSTEM
 */
function pruneStaleChallengeResets() {
    const todayKey = challengeResetStorageKey();
    for (let i = sessionStorage.length - 1; i >= 0; i--) {
        const k = sessionStorage.key(i);
        if (k && k.startsWith('nss_challenge_reset_') && k !== todayKey) {
            sessionStorage.removeItem(k);
        }
    }
}

if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', pruneStaleChallengeResets);
    } else {
        pruneStaleChallengeResets();
    }
}

/**
 * Return the number of challenge resets that have occurred today.
 * @tag FINAL_TEST
 */
function loadChallengeResetsToday() {
    return Number(sessionStorage.getItem(challengeResetStorageKey()) || 0);
}

/**
 * Increment today's challenge-reset counter and return the new value.
 * @tag FINAL_TEST
 */
function bumpChallengeResetToday() {
    const k = challengeResetStorageKey();
    const n = Number(sessionStorage.getItem(k) || 0) + 1;
    sessionStorage.setItem(k, String(n));
    return n;
}
