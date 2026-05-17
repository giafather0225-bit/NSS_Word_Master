/* ================================================================
   diary-write-media.js — Diary Write screen · Photos + STT/TTS speech
   Section: Diary
   Dependencies: diary-write.js (_dwState, _dwToast, _dwUpdateProgress, _dwReRenderPhotos, _dwListening, _dwSpeaking, _dwRec)
                 diary-write-html.js (_dwPhotosHTML)
   API endpoints: POST /api/diary/photo/multi · DELETE /api/diary/photo/:filename
   ================================================================ */

/* ── Photos ─────────────────────────────────────────────────────── */

/** @tag DIARY PHOTO */
async function _dwOnPhotoPick(e) {
    const files = Array.from(e.target.files || []);
    e.target.value = "";
    const room = 3 - _dwState.photos.length;
    const picked = files.slice(0, room);
    if (picked.length === 0) return;

    const today = new Date().toISOString().slice(0, 10);

    // Add optimistic local previews so the UI feels instant; replace each
    // tile's URL with the server-served URL once the upload returns.
    const placeholders = picked.map(f => ({
        id: "p-" + Date.now() + "-" + Math.random().toString(36).slice(2, 7),
        url: URL.createObjectURL(f),
        name: f.name,
        filename: null,
        uploading: true,
    }));
    _dwState.photos.push(...placeholders);
    _dwReRenderPhotos();
    _dwUpdateProgress();    // disable Save while uploads are in-flight

    // Upload sequentially — small N (≤3), and avoids race on filename uniqueness.
    for (let i = 0; i < picked.length; i++) {
        const f = picked[i];
        const ph = placeholders[i];
        const fd = new FormData();
        fd.append("entry_date", today);
        fd.append("file", f);
        try {
            const res = await fetch("/api/diary/photo/multi", { method: "POST", body: fd });
            if (!res.ok) throw new Error("upload failed: " + res.status);
            const data = await res.json();
            ph.filename  = data.filename  || null;
            ph.thumb_url = data.thumb_url || null;
            // Swap the blob URL for the server URL so it survives reload.
            try { URL.revokeObjectURL(ph.url); } catch (_) {}
            ph.url = data.photo_url || ph.url;
            ph.uploading = false;
        } catch (err) {
            // Drop the failed placeholder and notify.
            _dwState.photos = _dwState.photos.filter(p => p.id !== ph.id);
            _dwToast("Photo upload failed.", true);
        }
    }
    _dwReRenderPhotos();
    _dwUpdateProgress();    // re-enable Save once uploads settle
}

/** @tag DIARY PHOTO */
async function _dwRemovePhoto(id) {
    const target = _dwState.photos.find(p => p.id === id);
    _dwState.photos = _dwState.photos.filter(p => p.id !== id);
    _dwReRenderPhotos();
    // Best-effort backend cleanup so orphan files don't accumulate.
    if (target && target.filename) {
        try {
            await fetch("/api/diary/photo/" + encodeURIComponent(target.filename), { method: "DELETE" });
        } catch (e) {
            console.warn("[diary-write] photo DELETE failed:", target.filename, e);
        }
    }
}

/** @tag DIARY PHOTO */
function _dwReRenderPhotos() {
    const wrap = document.getElementById("dw-photos");
    if (!wrap) return;
    const tmp = document.createElement("div");
    tmp.innerHTML = _dwPhotosHTML();
    const newWrap = tmp.firstElementChild;
    // data-remove-pid 방식으로 XSS 방지 — onclick 인라인 핸들러 대신 이벤트 위임
    newWrap.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-remove-pid]");
        if (btn) _dwRemovePhoto(btn.dataset.removePid);
    });
    wrap.replaceWith(newWrap);
}

/* ── Speak (STT) / Listen (TTS) — Web Speech API ────────────────── */

let _dwRec = null;       // SpeechRecognition instance
let _dwListening = false;
let _dwSpeaking = false;

/** @tag DIARY */
function _dwGetRec() {
    if (_dwRec) return _dwRec;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.lang = "en-US";
    r.continuous = true;
    r.interimResults = false;
    r.onresult = (e) => {
        const ta = document.getElementById("dw-body");
        if (!ta) return;
        let added = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) added += e.results[i][0].transcript + " ";
        }
        if (!added) return;
        const start = ta.selectionStart || ta.value.length;
        const end   = ta.selectionEnd   || ta.value.length;
        ta.value = ta.value.slice(0, start) + added + ta.value.slice(end);
        const caret = start + added.length;
        ta.setSelectionRange(caret, caret);
        _dwState.body = ta.value;
        _dwUpdateProgress();
    };
    r.onend = () => {
        _dwListening = false;
        _dwReflectSpeakBtn();
    };
    r.onerror = (e) => {
        _dwListening = false;
        _dwReflectSpeakBtn();
        if (e && e.error === "not-allowed") _dwToast("Mic permission needed.", true);
    };
    _dwRec = r;
    return r;
}

/** @tag DIARY */
function _dwReflectSpeakBtn() {
    const btn = document.getElementById("dw-speak-btn");
    if (!btn) return;
    btn.innerHTML = _dwListening
        ? '<i data-lucide="circle-stop" style="width:16px;height:16px;stroke-width:1.5"></i>'
        : '<i data-lucide="mic" style="width:16px;height:16px;stroke-width:1.5"></i>';
    btn.title = _dwListening ? "Stop dictation" : "Speak — dictate into the page";
    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** @tag DIARY */
function _dwReflectListenBtn() {
    const btn = document.getElementById("dw-listen-btn");
    if (!btn) return;
    btn.innerHTML = _dwSpeaking
        ? '<i data-lucide="pause" style="width:16px;height:16px;stroke-width:1.5"></i>'
        : '<i data-lucide="volume-2" style="width:16px;height:16px;stroke-width:1.5"></i>';
    btn.title = _dwSpeaking ? "Stop reading" : "Listen — read this page aloud";
    if (typeof lucide !== "undefined") lucide.createIcons();
}

/** @tag DIARY */
function _dwToggleSpeak() {
    const rec = _dwGetRec();
    if (!rec) {
        _dwToast("Speech input isn't supported in this browser.", true);
        return;
    }
    if (_dwListening) {
        try { rec.stop(); } catch (_) {}
        _dwListening = false;
        _dwReflectSpeakBtn();
        return;
    }
    try {
        rec.start();
        _dwListening = true;
        _dwReflectSpeakBtn();
    } catch (err) {
        _dwToast("Couldn't start the mic.", true);
    }
}

/** @tag DIARY */
function _dwToggleListen() {
    const synth = window.speechSynthesis;
    if (!synth) {
        _dwToast("Speech output isn't supported in this browser.", true);
        return;
    }
    if (_dwSpeaking) {
        synth.cancel();
        _dwSpeaking = false;
        _dwReflectListenBtn();
        return;
    }
    const text = (
        (_dwState.title ? _dwState.title + ". " : "") +
        (_dwState.body || "")
    ).trim();
    if (!text) {
        _dwToast("Nothing to read yet.", false);
        return;
    }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = 0.95;
    u.onend   = () => { _dwSpeaking = false; _dwReflectListenBtn(); };
    u.onerror = () => { _dwSpeaking = false; _dwReflectListenBtn(); };
    synth.cancel();
    synth.speak(u);
    _dwSpeaking = true;
    _dwReflectListenBtn();
}
