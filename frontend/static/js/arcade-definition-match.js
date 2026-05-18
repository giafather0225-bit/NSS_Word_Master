/* ================================================================
   arcade-definition-match.js — Match or Not: is this word↔def pair right?
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const DM_CFG = {
  roundMs: 90000,         // Fix #11: 90 s (was 60 s)
  matchProbability: 0.5,
  basePoints: 40,         // Fix #11: was 30
  streakBonus: 10,        // Fix #11: was 8
  streakCap: 12,
  wrongPenalty: 20,
  feedbackMs: 180,
};

let _dm = null;

const DM_LEVELS = {
  easy:   { label: 'Easy',   roundMs: 120000, timeLabel: '120s' },
  normal: { label: 'Normal', roundMs:  90000, timeLabel:  '90s' },
  hard:   { label: 'Hard',   roundMs:  60000, timeLabel:  '60s' },
};

/** Level picker for Definition Match. @tag ARCADE */
async function dmShowLevelPicker() {
  dmStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="wi-level-picker">
      <h2 class="wi-level-title">Select Difficulty</h2>
      <div class="wi-level-sub">Definition Match</div>
      <div class="wi-level-list" id="dm-level-list">Loading…</div>
      <div class="arcade-how-to-play">
        <div class="arcade-htp-title">How to play</div>
        <ul class="arcade-htp-list">
          <li>A word appears at the top — choose the correct definition from four options.</li>
          <li>Answer quickly for a time bonus; wrong answers deduct points.</li>
          <li>Complete all rounds before the timer runs out.</li>
          <li>Harder levels show trickier definitions and give less time.</li>
        </ul>
      </div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Back</button>
    </div>`;

  const bests = await Promise.all(
    Object.keys(DM_LEVELS).map((lv) =>
      fetch(`/api/arcade/best/definition_match?level=${lv}`)
        .then((r) => (r.ok ? r.json() : { score: 0 }))
        .catch(() => ({ score: 0 }))
    )
  );

  const list = document.getElementById('dm-level-list');
  if (!list) return;
  list.innerHTML = Object.entries(DM_LEVELS)
    .map(([key, cfg], i) => {
      const pb = bests[i].score || 0;
      const pbAcc = bests[i].accuracy || 0;
      return `
        <div class="wi-level-card" onclick="dmStart('${key}')">
          <div class="wi-level-icon wi-level-icon--${key}">${key[0].toUpperCase()}</div>
          <div class="wi-level-name">${cfg.label}</div>
          <div class="wi-level-spec">${cfg.timeLabel} round</div>
          <div class="wi-level-pb">Best: ${pb}${_arcadeLevelStarsHTML(pbAcc)}</div>
        </div>`;
    })
    .join('');
}

/** Start a Match-or-Not round. @tag ARCADE */
async function dmStart(level = 'normal') {
  dmStop();
  const lv = DM_LEVELS[level] || DM_LEVELS.normal;
  DM_CFG.roundMs = lv.roundMs;
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="dm-view">
      <div class="wi-hud">
        <span>Score: <b id="dm-score">0</b></span>
        <span>Time: <b id="dm-time">${Math.round(lv.roundMs / 1000)}</b>s</span>
        <span>Streak: <b id="dm-streak">0</b></span>
      </div>
      <div class="dm-card" id="dm-card">
        <div class="dm-word" id="dm-word">—</div>
        <div class="dm-eq">=</div>
        <div class="dm-def" id="dm-def">—</div>
        <div class="dm-reveal" id="dm-reveal"></div>
      </div>
      <div class="dm-time-bar" aria-hidden="true">
        <div class="dm-time-fill" id="dm-time-fill" style="width:100%"></div>
      </div>
      <div class="dm-buttons">
        <button type="button" class="dm-btn dm-btn--no" id="dm-no"><span class="dm-btn-key">←</span> No</button>
        <button type="button" class="dm-btn dm-btn--yes" id="dm-yes">Yes <span class="dm-btn-key">→</span></button>
      </div>
      <div class="dm-hint">Tap Yes if the definition matches, No if it doesn't.</div>
      <button type="button" class="wi-btn secondary" onclick="arcadeReturnToLobby()">Quit</button>
    </div>`;

  if (typeof _arcadeShowTutorialOnce === 'function') _arcadeShowTutorialOnce('definition_match');

  const words = await _arcadeFetchWords(60);
  if (words.length < 4) {
    body.innerHTML = `
      <div class="wi-gameover">
        <h2>Not enough words</h2>
        <div class="stat">Need at least 4 words in the pool.</div>
        <button class="wi-btn" onclick="arcadeReturnToLobby()">Back</button>
      </div>`;
    return;
  }

  _dm = {
    pool: words,
    score: 0,
    streak: 0,
    correct: 0,
    total: 0,
    running: true,
    startedAt: performance.now(),
    current: null,
    lock: false,
    tickHandle: null,
    level,
    milestonesHit: new Set(),
    missedWords: [],
  };

  document.getElementById('dm-yes').addEventListener('click', () => _dmAnswer(true));
  document.getElementById('dm-no').addEventListener('click', () => _dmAnswer(false));
  document.addEventListener('keydown', _dmKeydown);

  if (typeof sfxStart === 'function') sfxStart();
  await _arcadeCountdown();
  _dmNextPair();
  _dm.tickHandle = setInterval(_dmTick, 500);  // Fix #19: setInterval instead of rAF
}

/** Stop the round. @tag ARCADE */
function dmStop() {
  if (_dm) {
    _dm.running = false;
    if (_dm.tickHandle) { clearInterval(_dm.tickHandle); _dm.tickHandle = null; }
  }
  document.removeEventListener('keydown', _dmKeydown);
  _dm = null;
}

function _dmKeydown(e) {
  if (!_dm || !_dm.running) return;
  if (e.key === 'ArrowRight' || e.key.toLowerCase() === 'y') _dmAnswer(true);
  else if (e.key === 'ArrowLeft' || e.key.toLowerCase() === 'n') _dmAnswer(false);
}

// Fix #19: setInterval-based tick (500ms) — no rAF waste
function _dmTick() {
  if (!_dm || !_dm.running) return;
  if (document.hidden) return;
  const elapsed = performance.now() - _dm.startedAt;
  const remain = Math.max(0, DM_CFG.roundMs - elapsed);
  const el = document.getElementById('dm-time');
  if (el) {
    el.textContent = String(Math.ceil(remain / 1000));
    el.classList.toggle('dm-time--urgent', remain <= 10000);
  }
  // Update time bar
  const fill = document.getElementById('dm-time-fill');
  if (fill) {
    const pct = (remain / DM_CFG.roundMs) * 100;
    fill.style.width = `${pct}%`;
    fill.classList.toggle('dm-time-fill--warn',   pct <= 40);
    fill.classList.toggle('dm-time-fill--danger',  pct <= 15);
  }
  if (remain <= 0) {
    if (_dm.tickHandle) { clearInterval(_dm.tickHandle); _dm.tickHandle = null; }
    _dmGameOver();
  }
}

function _dmNextPair() {
  if (!_dm) return;
  const pool = _dm.pool;
  const wordEntry = pool[Math.floor(Math.random() * pool.length)];
  const shouldMatch = Math.random() < DM_CFG.matchProbability;

  let defText = wordEntry.definition;
  let isMatch = true;
  if (!shouldMatch) {
    // pick a different entry whose definition clearly differs
    for (let i = 0; i < 8; i++) {
      const other = pool[Math.floor(Math.random() * pool.length)];
      if (
        other.word.toLowerCase() !== wordEntry.word.toLowerCase() &&
        other.definition.toLowerCase() !== wordEntry.definition.toLowerCase()
      ) {
        defText = other.definition;
        isMatch = false;
        break;
      }
    }
    // if no differing def found, force-match so isMatch stays correct
  }

  _dm.current = {
    word: wordEntry.word,
    definition: defText,
    correctDef: wordEntry.definition,
    isMatch,
  };
  _dm.lock = false;

  const wEl = document.getElementById('dm-word');
  const dEl = document.getElementById('dm-def');
  const card = document.getElementById('dm-card');
  if (wEl) wEl.textContent = wordEntry.word;
  if (dEl) dEl.textContent = defText;
  if (card) {
    card.classList.remove('dm-card--correct', 'dm-card--wrong', 'dm-card--slide-in');
    void card.offsetWidth;  // force reflow so animation restarts
    card.classList.add('dm-card--slide-in');
  }
}

function _dmAnswer(saidYes) {
  if (!_dm || !_dm.running || _dm.lock) return;
  _dm.lock = true;
  const correct = saidYes === _dm.current.isMatch;
  _dm.total += 1;

  if (correct) {
    _dm.correct += 1;
    _dm.streak += 1;
    const bonus = Math.min(DM_CFG.streakCap, _dm.streak) * DM_CFG.streakBonus;
    const gained = DM_CFG.basePoints + bonus;
    const prevScore = _dm.score;
    _dm.score += gained;
    if (typeof _arcadeFloatScore === 'function') _arcadeFloatScore(gained);
    if (typeof _arcadeCheckMilestone === 'function') _arcadeCheckMilestone(_dm.milestonesHit, prevScore, _dm.score, _dm.streak);
    if (typeof sfxHit === 'function') sfxHit(_dm.streak);
    if (_dm.streak > 0 && _dm.streak % 5 === 0) {
      if (typeof sfxCombo === 'function') sfxCombo();
      if (typeof _arcadeShowCombo === 'function') _arcadeShowCombo(_dm.streak);
    }
  } else {
    _dm.streak = 0;
    _dm.score = Math.max(0, _dm.score - DM_CFG.wrongPenalty);
    if (typeof sfxMiss === 'function') sfxMiss();
    _dm.missedWords.push({ word: _dm.current.word, def: _dm.current.correctDef });
  }
  _dmUpdateHUD();
  if (correct && typeof _arcadeScorePop === 'function') _arcadeScorePop(document.getElementById('dm-score'));

  const card = document.getElementById('dm-card');
  const reveal = document.getElementById('dm-reveal');
  if (card) {
    card.classList.add(correct ? 'dm-card--correct' : 'dm-card--wrong');
  }
  if (!correct && reveal) {
    // Always show the correct definition on wrong answer so the user learns
    if (_dm.current.isMatch) {
      reveal.textContent = `Yes — "${_dm.current.word}" = ${_dm.current.correctDef}`;
    } else {
      reveal.textContent = `No — "${_dm.current.word}" = ${_dm.current.correctDef}`;
    }
    reveal.classList.add('dm-reveal--show');
  }
  setTimeout(() => {
    if (reveal) { reveal.textContent = ''; reveal.classList.remove('dm-reveal--show'); }
    if (_dm && _dm.running) _dmNextPair();
  }, correct ? DM_CFG.feedbackMs : DM_CFG.feedbackMs * 3);
}

function _dmUpdateHUD() {
  const s = document.getElementById('dm-score');
  const st = document.getElementById('dm-streak');
  if (s) s.textContent = String(_dm.score);
  if (st) { st.textContent = String(_dm.streak); if (typeof _arcadeApplyStreakStyle === 'function') _arcadeApplyStreakStyle(st, _dm.streak); }
}

async function _dmGameOver() {
  if (!_dm) return;
  _dm.running = false;
  if (_dm.tickHandle) { clearInterval(_dm.tickHandle); _dm.tickHandle = null; }
  document.removeEventListener('keydown', _dmKeydown);
  const state = { ..._dm };  // M-1: snapshot before null
  _dm = null;                 // M-1: null immediately to prevent stale callbacks
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('definition_match', state.score, state.correct, state.total, accuracy, state.level || 'normal');
  const missed = state.missedWords || [];
  const extras = missed.length > 0
    ? `<div class="cw-missed">
        <div class="cw-missed-title">Missed words (${missed.length})</div>
        ${missed.map((m) => `<div class="cw-missed-row"><b>${m.word.toUpperCase()}</b> — ${m.def}</div>`).join('')}
      </div>`
    : '';
  _arcadeRenderGameOver({ state, accuracy, result, replayFn: () => dmStart(state.level || 'normal'), extras });
}
