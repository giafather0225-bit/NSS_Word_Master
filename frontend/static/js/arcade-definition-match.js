/* ================================================================
   arcade-definition-match.js — Match or Not: is this word↔def pair right?
   Section: Arcade
   Dependencies: arcade.js
   API endpoints: GET /api/arcade/words, POST /api/arcade/score
   ================================================================ */

/** @tag ARCADE */
const DM_CFG = {
  roundMs: 60000,
  matchProbability: 0.5,
  basePoints: 30,
  streakBonus: 8,
  streakCap: 12,
  wrongPenalty: 20,
  feedbackMs: 180,
};

let _dm = null;

/** Start a Match-or-Not round. @tag ARCADE */
async function dmStart() {
  dmStop();
  const body = document.getElementById('arcade-body');
  if (!body) return;

  body.innerHTML = `
    <div class="dm-view">
      <div class="wi-hud">
        <span>Score: <b id="dm-score">0</b></span>
        <span>Time: <b id="dm-time">60</b>s</span>
        <span>Streak: <b id="dm-streak">0</b></span>
      </div>
      <div class="dm-card" id="dm-card">
        <div class="dm-word" id="dm-word">—</div>
        <div class="dm-eq">=</div>
        <div class="dm-def" id="dm-def">—</div>
      </div>
      <div class="dm-buttons">
        <button type="button" class="dm-btn dm-btn--no" id="dm-no">No</button>
        <button type="button" class="dm-btn dm-btn--yes" id="dm-yes">Yes</button>
      </div>
      <div class="dm-hint">Tap Yes if the definition matches, No if it doesn't.<br>Keys: ← No · → Yes</div>
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
  };

  document.getElementById('dm-yes').addEventListener('click', () => _dmAnswer(true));
  document.getElementById('dm-no').addEventListener('click', () => _dmAnswer(false));
  document.addEventListener('keydown', _dmKeydown);

  if (typeof sfxStart === 'function') sfxStart();
  _dmNextPair();
  _dmTick();
}

/** Stop the round. @tag ARCADE */
function dmStop() {
  if (_dm) _dm.running = false;
  document.removeEventListener('keydown', _dmKeydown);
  _dm = null;
}

function _dmKeydown(e) {
  if (!_dm || !_dm.running) return;
  if (e.key === 'ArrowRight' || e.key.toLowerCase() === 'y') _dmAnswer(true);
  else if (e.key === 'ArrowLeft' || e.key.toLowerCase() === 'n') _dmAnswer(false);
}

function _dmTick() {
  if (!_dm || !_dm.running) return;
  const elapsed = performance.now() - _dm.startedAt;
  const remain = Math.max(0, DM_CFG.roundMs - elapsed);
  const el = document.getElementById('dm-time');
  if (el) el.textContent = String(Math.ceil(remain / 1000));
  if (remain <= 0) {
    _dmGameOver();
    return;
  }
  requestAnimationFrame(_dmTick);
}

function _dmNextPair() {
  if (!_dm) return;
  const pool = _dm.pool;
  const wordEntry = pool[Math.floor(Math.random() * pool.length)];
  const shouldMatch = Math.random() < DM_CFG.matchProbability;

  let defText = wordEntry.definition;
  if (!shouldMatch) {
    // pick a different entry whose definition clearly differs
    for (let i = 0; i < 8; i++) {
      const other = pool[Math.floor(Math.random() * pool.length)];
      if (
        other.word.toLowerCase() !== wordEntry.word.toLowerCase() &&
        other.definition.toLowerCase() !== wordEntry.definition.toLowerCase()
      ) {
        defText = other.definition;
        break;
      }
    }
  }

  _dm.current = {
    word: wordEntry.word,
    definition: defText,
    isMatch: defText === wordEntry.definition,
  };
  _dm.lock = false;

  const wEl = document.getElementById('dm-word');
  const dEl = document.getElementById('dm-def');
  const card = document.getElementById('dm-card');
  if (wEl) wEl.textContent = wordEntry.word;
  if (dEl) dEl.textContent = defText;
  if (card) {
    card.classList.remove('dm-card--correct', 'dm-card--wrong');
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
    _dm.score += DM_CFG.basePoints + bonus;
    if (typeof sfxHit === 'function') sfxHit(_dm.streak);
    if (_dm.streak > 0 && _dm.streak % 5 === 0 && typeof sfxCombo === 'function') sfxCombo();
  } else {
    _dm.streak = 0;
    _dm.score = Math.max(0, _dm.score - DM_CFG.wrongPenalty);
    if (typeof sfxMiss === 'function') sfxMiss();
  }
  _dmUpdateHUD();

  const card = document.getElementById('dm-card');
  if (card) {
    card.classList.add(correct ? 'dm-card--correct' : 'dm-card--wrong');
  }
  setTimeout(() => {
    if (_dm && _dm.running) _dmNextPair();
  }, correct ? DM_CFG.feedbackMs : DM_CFG.feedbackMs * 2);
}

function _dmUpdateHUD() {
  const s = document.getElementById('dm-score');
  const st = document.getElementById('dm-streak');
  if (s) s.textContent = String(_dm.score);
  if (st) st.textContent = String(_dm.streak);
}

async function _dmGameOver() {
  if (!_dm) return;
  const state = _dm;
  _dm.running = false;
  document.removeEventListener('keydown', _dmKeydown);
  const accuracy = state.total > 0 ? state.correct / state.total : 0;
  const result = await _arcadeReportScore('definition_match', state.score, state.correct, state.total, accuracy);
  _arcadeRenderGameOver({ state, accuracy, result, replay: 'dmStart()' });
}
