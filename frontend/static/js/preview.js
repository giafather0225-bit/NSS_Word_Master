/* ================================================================
   preview.js — Step 1: Preview + Shadow + Spell
   Section: English / Preview
   Dependencies: core.js, tts-client.js, analytics.js
   API endpoints: /api/tts/preview_word_meaning, /api/tts/example_full,
                  /api/tts/word_only
   ================================================================ */

/** Render 4×5 word-card grid for Step 1. @tag PREVIEW ENGLISH */
function renderPreview(el) {
    previewDoneMap.clear();
    function buildGrid() {
        el.innerHTML = "";
        const hdr = document.createElement("div"); hdr.className = "preview-header";
        hdr.innerHTML = `<h2>Step 1 — Preview</h2><span class="preview-prog-pill" id="prev-prog">${previewDoneMap.size} / ${items.length}</span>`;
        el.appendChild(hdr);
        const grid = document.createElement("div"); grid.className = "preview-grid"; grid.id = "preview-grid";
        items.forEach(item => {
            const st = previewDoneMap.get(item.id);
            const card = document.createElement("div");
            card.className = `preview-card${st === "ok" ? " done" : st === "miss" ? " failed" : ""}`;
            card.dataset.id = item.id;
            card.innerHTML = `<div class="pc-word">${escapeHtml(item.answer)}</div>
                ${st === "ok" ? '<span class="pc-badge ok">✓</span>' : ""}
                ${st === "miss" ? '<span class="pc-badge miss">~</span>' : ""}`;
            card.addEventListener("click", () => openPreviewModal(item, buildGrid));
            grid.appendChild(card);
        });
        el.appendChild(grid);
        updateRoadmapUI(); updateProgressPct();
    }
    buildGrid();
}

/**
 * Open preview popup modal with Shadow and Spell flows.
 * @tag PREVIEW SHADOW SPELL TTS
 */
function openPreviewModal(item, onClose) {
    const modal = $('preview-modal'), content = $('pm-content');
    if (!modal || !content) return;
    const extra = parseItemExtra(item);
    const posRaw = (extra.pos || '').replace(/[.\s]/g, '').toLowerCase();
    const posMap = { n:'noun', v:'verb', adj:'adjective', adv:'adverb', prep:'preposition',
        conj:'conjunction', pron:'pronoun', noun:'noun', verb:'verb', adjective:'adjective',
        adverb:'adverb', preposition:'preposition' };
    const posLabel = posMap[posRaw] || posRaw;
    const word = item.answer.trim();

    content.innerHTML = `
        ${posLabel ? `<p class="pm-pos"><span data-pos="${posLabel}">${posLabel}</span></p>` : ''}
        <p class="pm-word" id="pm-word">${escapeHtml(word)}</p>
        ${item.question ? `<p class="pm-meaning" id="pm-meaning">${escapeHtml(item.question)}</p>` : ''}
        ${item.hint ? `<div class="pm-example" id="pm-example">"${escapeHtml(item.hint)}"</div>` : ''}
        <div class="pm-divider"></div>
        <button type="button" class="pm-listen-btn" id="pm-listen">🔊 Listen</button>
        <p class="pm-listen-hint hidden" id="pm-listen-hint">Press the mic and repeat the word</p>
        <p class="pm-shadow-label locked" id="pm-shadow-label">SHADOW (Repeat 3×)</p>
        <div class="pm-shadow-rows" id="pm-shadow-rows"></div>
        <p class="pm-spell-unlock-hint hidden" id="pm-spell-unlock-hint">Great! Now type the word</p>
        <p class="pm-spell-label locked" id="pm-spell-label">SPELL (Type 3×)</p>
        <div class="pm-spell-rows locked" id="pm-spell-rows"></div>
        <div class="pm-verdict" id="pm-verdict"></div>`;

    modal.classList.remove('hidden'); modal.hidden = false; modal.style.display = '';

    const shadowState = [null,null,null], shadowRec = [false,false,false];
    const spellState = [null,null,null];
    let spellUnlocked = false, listenDone = false, activeRec = null;
    let shadowFailCount = 0;
    const SHADOW_AUTO_PASS_THRESHOLD = 3;

    /** Levenshtein similarity 0–100. */
    function similarity(a, b) {
        a = a.toLowerCase().trim(); b = b.toLowerCase().trim();
        if (a === b) return 100;
        const m = a.length, n = b.length;
        const dp = Array.from({length:m+1}, (_,i) => Array.from({length:n+1}, (_,j) => i===0?j:j===0?i:0));
        for (let i=1;i<=m;i++) for (let j=1;j<=n;j++)
            dp[i][j] = a[i-1]===b[j-1] ? dp[i-1][j-1] : 1+Math.min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1]);
        return Math.round((1 - dp[m][n] / Math.max(m,n)) * 100);
    }

    // ── Shadow rows ──────────────────────────────────────────────
    function buildShadowRows() {
        const el = $('pm-shadow-rows'); if (!el) return; el.innerHTML = '';
        shadowState.forEach((score, i) => {
            const passed = score!==null && score>=90, autoPassed = score===-1, rec = shadowRec[i];
            const done = passed || autoPassed;
            const row = document.createElement('div'); row.className = 'pm-shadow-row';
            const mic = document.createElement('button'); mic.type = 'button';
            mic.className = 'pm-mic-btn'+(rec?' recording':done?' done':'');
            if (autoPassed) mic.classList.add('auto-passed');
            mic.innerHTML = rec ? '&#9209;' : '🎤'; mic.disabled = done || !listenDone;
            if (!done && !rec && listenDone) mic.addEventListener('click', () => startShadow(i));
            const icon = document.createElement('span'); icon.className = 'pm-row-icon';
            icon.textContent = done ? '✓' : '○';
            icon.style.color = autoPassed ? 'var(--color-warning)' : passed ? 'var(--color-success)' : '#B0B0B5';
            const scoreEl = document.createElement('span'); scoreEl.className = 'pm-score-text';
            scoreEl.textContent = autoPassed ? 'auto' : (score!==null ? score+'%' : '');
            if (autoPassed) scoreEl.style.color = 'var(--color-warning)';
            row.append(mic, icon, scoreEl); el.appendChild(row);
        });
    }

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    function startShadow(i) {
        if (!SpeechRec) { shadowState[i]=100; buildShadowRows(); checkShadowDone(); return; }
        shadowRec[i] = true; buildShadowRows();
        const rec = new SpeechRec(); rec.lang='en-US'; rec.interimResults=false; rec.maxAlternatives=3;
        rec.onresult = e => {
            const score = Math.max(...Array.from(e.results[0]).map(a=>similarity(a.transcript,word)));
            shadowRec[i]=false; shadowState[i]=score; buildShadowRows();
            _trackWordAttempt(item, score>=90, `shadow_${i+1}:${score}%`);
            if (score>=90) checkShadowDone();
            else {
                shadowFailCount++;
                if (shadowFailCount >= SHADOW_AUTO_PASS_THRESHOLD) {
                    triggerShadowAutoPass();
                } else {
                    setTimeout(()=>{ shadowState[i]=null; buildShadowRows(); }, 1500);
                }
            }
        };
        rec.onerror = () => {
            shadowRec[i]=false; activeRec=null;
            shadowFailCount++;
            if (shadowFailCount >= SHADOW_AUTO_PASS_THRESHOLD) triggerShadowAutoPass();
            else buildShadowRows();
        };
        rec.onend   = () => { if (shadowRec[i]) { shadowRec[i]=false; buildShadowRows(); } activeRec=null; };
        activeRec=rec; rec.start();
    }

    function checkShadowDone() {
        if (!shadowState.every(s=>s!==null&&s>=90)) return;
        spellUnlocked = true;
        const h = $('pm-spell-unlock-hint'); if (h) h.classList.remove('hidden');
        buildSpellRows();
    }

    /** @tag PREVIEW SHADOW — Auto-pass after 3 failed attempts */
    function triggerShadowAutoPass() {
        shadowState.forEach((s,i) => { if (s===null || s<90) shadowState[i] = -1; });
        buildShadowRows();
        const verdict = $('pm-verdict');
        if (verdict) {
            verdict.className = 'pm-verdict auto-pass';
            verdict.textContent = "Good try! Let's move on \uD83D\uDCAA";
            setTimeout(() => { verdict.className = 'pm-verdict'; verdict.textContent = ''; }, 2000);
        }
        spellUnlocked = true;
        const h = $('pm-spell-unlock-hint'); if (h) h.classList.remove('hidden');
        buildSpellRows();
    }

    // ── Spell rows ───────────────────────────────────────────────
    function buildSpellRows() {
        const rowsEl=$('pm-spell-rows'), labelEl=$('pm-spell-label'); if (!rowsEl) return;
        const locked=!spellUnlocked;
        if (labelEl) labelEl.classList.toggle('locked',locked);
        rowsEl.classList.toggle('locked',locked); rowsEl.innerHTML='';
        spellState.forEach((result, i) => {
            const row=document.createElement('div'); row.className='pm-spell-row';
            const inp=document.createElement('input'); inp.type='text';
            inp.className='pm-typing-input'+(result===true?' correct':result===false?' wrong':'');
            inp.id=`pm-inp-${i}`; inp.autocomplete='off';
            inp.setAttribute('autocorrect','off'); inp.setAttribute('autocapitalize','off'); inp.setAttribute('spellcheck','false');
            inp.placeholder=locked?'Complete Shadow first…':'Type the word…';
            inp.disabled=locked||result!==null;
            if (result===true) inp.value=word;
            const icon=document.createElement('span'); icon.className='pm-row-icon';
            icon.textContent=result===true?'✓':result===false?'✗':'○';
            icon.style.color=result===true?'#34C759':result===false?'#FF3B30':'#B0B0B5';
            const btn=document.createElement('button'); btn.type='button'; btn.className='pm-chk-btn'; btn.textContent='Check';
            btn.disabled=locked||result!==null;
            btn.addEventListener('click',()=>checkSpell(i));
            inp.addEventListener('keydown',e=>{if(e.key==='Enter')checkSpell(i);});
            row.append(inp,icon,btn); rowsEl.appendChild(row);
        });
        if (!locked) {
            const first=spellState.findIndex(s=>s===null);
            if (first!==-1) setTimeout(()=>{ const e=$(`pm-inp-${first}`); if(e) e.focus(); },60);
        }
    }

    function checkSpell(i) {
        const inp=$(`pm-inp-${i}`), guess=(inp?inp.value:'').trim(); if(!guess) return;
        const correct=guess.toLowerCase()===word.toLowerCase();
        spellState[i]=correct;
        if (correct) fetch('/api/tts/word_only',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word})})
            .then(r=>r.blob()).then(b=>{const u=URL.createObjectURL(b);const a=new Audio(u);a.onended=()=>URL.revokeObjectURL(u);a.play().catch(()=>{});}).catch(()=>{});
        buildSpellRows();
        if (spellState.every(s=>s!==null)) evaluateSpell();
    }

    function evaluateSpell() {
        const allOk=spellState.every(s=>s===true), verdict=$('pm-verdict');
        if (!allOk) {
            verdict.className='pm-verdict retry'; verdict.textContent='Not quite — try the missed ones again!';
            setTimeout(()=>{ spellState.forEach((s,i)=>{ if(s===false) spellState[i]=null; }); verdict.className='pm-verdict'; buildSpellRows(); },1000);
            return;
        }
        showVerdict();
    }

    function showVerdict() {
        const hadAutoPass = shadowState.some(s => s === -1);
        const msgs = hadAutoPass
            ? ["Nice effort! Keep it up!", "Good job finishing!"]
            : ['Perfect! You nailed it!', 'Amazing! All three! ⭐', "That's the way!"];
        const verdict=$('pm-verdict');
        verdict.className='pm-verdict pass';
        verdict.innerHTML=msgs[Math.floor(Math.random()*msgs.length)]+'<br><button type="button" class="pm-next-btn" id="pm-next">Next word →</button>';
        $('pm-next').dataset.created=Date.now();
        $('pm-next').addEventListener('click',()=>closeModal(hadAutoPass ? 'auto-pass' : 'ok'));
        particleBurst(hadAutoPass ? 12 : 20);
    }

    // ── TTS playback ─────────────────────────────────────────────
    let ttsAbort=null, currentAudio=null;
    const _playTTS = async (url, body) => {
        ttsAbort = new AbortController();
        const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:ttsAbort.signal});
        if (!res.ok) return;
        const blob = await res.blob(); if (blob.size<100) return;
        const blobUrl = URL.createObjectURL(blob);
        currentAudio = new Audio(blobUrl);
        await new Promise(resolve => {
            currentAudio.onended = () => { URL.revokeObjectURL(blobUrl); currentAudio=null; resolve(); };
            currentAudio.onerror = () => { URL.revokeObjectURL(blobUrl); currentAudio=null; resolve(); };
            currentAudio.play().catch(()=>resolve());
        });
    };

    $('pm-listen').addEventListener('click', async () => {
        const btn=$('pm-listen'), wordEl=$('pm-word'), meaningEl=$('pm-meaning'), exampleEl=$('pm-example');
        btn.disabled=true; btn.classList.add('playing'); btn.textContent='🎵 Playing…';
        const hl=(el,on)=>el&&el.classList.toggle('tts-hl',on);
        try {
            for (let j=0;j<3;j++) {
                hl(wordEl,true); hl(meaningEl,false);
                await _playTTS('/api/tts/preview_word_meaning',{word,meaning:item.question||'',rep:j+1});
                hl(wordEl,false);
                if (meaningEl) { hl(meaningEl,true); await new Promise(r=>setTimeout(r,300)); hl(meaningEl,false); }
                if (j<2) await new Promise(r=>setTimeout(r,350));
            }
            if (item.hint&&exampleEl) {
                await new Promise(r=>setTimeout(r,300));
                hl(exampleEl,true);
                await _playTTS('/api/tts/example_full',{sentence:item.hint});
                hl(exampleEl,false);
            }
        } catch(e) { if (e.name!=='AbortError') console.warn('[TTS]',e); }
        finally {
            hl(wordEl,false); hl(meaningEl,false); hl(exampleEl,false);
            btn.disabled=false; btn.classList.remove('playing'); btn.textContent='🔊 Listen';
            ttsAbort=null; listenDone=true;
            const sl=$('pm-shadow-label'); if(sl) sl.classList.remove('locked');
            const lh=$('pm-listen-hint'); if(lh) lh.classList.remove('hidden');
            buildShadowRows();
        }
    });

    const _modalAC = new AbortController(), _modalSig = {signal:_modalAC.signal};

    function stopAudio() {
        if (ttsAbort) { ttsAbort.abort(); ttsAbort=null; }
        if (currentAudio) { currentAudio.pause(); currentAudio.currentTime=0; currentAudio=null; }
        window.speechSynthesis.cancel();
        document.querySelectorAll('audio').forEach(a=>{a.pause();a.currentTime=0;});
        if (activeRec) { try{activeRec.abort();}catch(_){} activeRec=null; }
    }

    function closeModal(status) {
        stopAudio(); _modalAC.abort();
        const effectiveStatus = (status === 'auto-pass') ? 'ok' : status;
        previewDoneMap.set(item.id, effectiveStatus);
        addWordVault(word);
        modal.classList.add('hidden');
        if (typeof onClose==="function") onClose(effectiveStatus);
        const card=document.querySelector(`.preview-card[data-id="${item.id}"]`);
        if (card) {
            card.classList.remove('done','failed','auto-passed');
            if (status === 'auto-pass') {
                card.classList.add('done','auto-passed');
            } else {
                card.classList.add(effectiveStatus==='ok'?'done':'failed');
            }
            const old=card.querySelector('.pc-badge'); if(old) old.remove();
            const badge=document.createElement('span');
            badge.className=`pc-badge ${effectiveStatus==='ok'?'ok':'miss'}`;
            badge.textContent=effectiveStatus==='ok'?'✓':'~';
            card.appendChild(badge);
        }
        if (previewDoneMap.size>=items.length) {
            const m=$('preview-modal'); if(m){m.classList.add('hidden');m.hidden=true;}
            stageFxCorrect(); setStatus("Preview complete!");
            setTimeout(()=>{ if(stage===STAGE.PREVIEW||stage===null) advanceToNextStage(); },800);
        } else {
            setStatus(`${[...previewDoneMap.values()].filter(v=>v==="ok").length} / ${items.length} done`);
        }
    }

    $('pm-close-btn').addEventListener('click',()=>closeModal('skip'),_modalSig);
    modal.addEventListener('click',e=>{
        if (e.target!==modal) return;
        const shadowLocked=document.querySelector('.pm-shadow-label.locked');
        const listenBtn=document.getElementById('pm-listen');
        if (shadowLocked&&!(listenBtn&&listenBtn.classList.contains('playing'))) { stopAudio(); closeModal('skip'); }
    },_modalSig);

    function escHandler(e) {
        if (e.key==='Escape') closeModal('skip');
        if (e.key==='Enter') {
            const n=document.getElementById('pm-next');
            if (n&&Date.now()-parseInt(n.dataset.created||'0')>300) { e.preventDefault(); n.click(); }
        }
    }
    document.addEventListener('keydown',escHandler,_modalSig);
    buildShadowRows(); buildSpellRows();
}

window.openPreviewModal = openPreviewModal;
