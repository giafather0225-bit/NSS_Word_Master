/**
 * Master Cycle: Preview(grid+slideshow) → Training(7 phases/word) → Final(top wrong×3) → Sparta Challenge
 */
const CURRENT_SUBJECT = "vocabulary";
const LESSON = new URLSearchParams(location.search).get("lesson") || "Lesson_09";

function showAdminMsg(nearEl, msg, isError) {
    const key = '_adminMsg';
    let el = nearEl[key];
    if (!el) {
        el = document.createElement('p');
        el.style.cssText = 'margin:4px 0 0;font-size:13px;';
        nearEl.insertAdjacentElement('afterend', el);
        nearEl[key] = el;
    }
    el.style.color = isError ? 'var(--danger, #FF3B30)' : 'var(--success, #34C759)';
    el.textContent = msg;
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.textContent = ''; }, 3000);
}

const TP = { SHADOW1: 1, VISUAL: 2, PARTIAL: 3, MEANING_MC: 4, CONTEXT: 5, SPELL: 6, SENTENCE: 7 };

let APP_STATE = "PREVIEW";
let items = [];
let currentIndex = 0;
let trainingPhase = TP.SHADOW1;
let wrongMap = {};
let goldStamps = 0;
let magicFailCount = 0;

// ── 골드 스탬프 localStorage 영속 ──
function loadGoldStamps() {
    return Number(localStorage.getItem(`nss_gold_${LESSON}`) || 0);
}
function saveGoldStamps(n) {
    localStorage.setItem(`nss_gold_${LESSON}`, String(n));
}
let challengeQueue = [];
let challengeIndex = 0;
let previewAutoDone = false;
let previewRunning = false;
let lastTrainingSentence = "";
let partialMask = "";
let mcChoices = [];
let finalQueue = [];
let finalIndex = 0;
let lastSpellWrong = false;

function parseCardExtra(item) {
    try {
        if (!item || !item.extra_data) return {};
        return typeof item.extra_data === "string" ? JSON.parse(item.extra_data) : item.extra_data;
    } catch {
        return {};
    }
}

function escapeRe(s) {
    return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function wordEmoji(word) {
    if (!word || !String(word).length) return "📚";
    const pool = ["🦁", "🌟", "🎪", "📚", "🦋", "🍎", "🚀", "💡", "🎨", "🦄", "⚡", "🌈"];
    let h = 0;
    for (let i = 0; i < word.length; i++) h = (h * 31 + word.charCodeAt(i)) >>> 0;
    return pool[h % pool.length];
}

function makePartialMask(word) {
    const chars = [...String(word)];
    const letterIdx = [];
    chars.forEach((c, i) => {
        if (/[a-zA-Z]/.test(c)) letterIdx.push(i);
    });
    if (!letterIdx.length) return { mask: word, hidden: 0 };
    const nHide = Math.max(1, Math.floor(letterIdx.length * 0.42));
    const pick = shuffle(letterIdx).slice(0, nHide);
    const out = chars.map((c, i) => (pick.includes(i) ? (c === c.toUpperCase() ? "＿" : "_") : c));
    return { mask: out.join(""), hidden: pick.length };
}

function spellCompareHtml(expected, typed) {
    const e = [...String(expected)];
    const t = [...String(typed)];
    const maxL = Math.max(e.length, t.length);
    let html = "";
    for (let i = 0; i < maxL; i++) {
        const ec = e[i];
        const tc = t[i];
        if (tc === undefined) html += `<span class="spell-gap">·</span>`;
        else if (ec === undefined) html += `<span class="spell-extra">${escapeHtml(tc)}</span>`;
        else if (String(ec).toLowerCase() === String(tc).toLowerCase())
            html += `<span class="spell-ok">${escapeHtml(tc)}</span>`;
        else html += `<span class="spell-bad">${escapeHtml(tc)}</span>`;
    }
    return html;
}

/* ── Gia Edition 2.0 helpers ── */

/** 품사 → CSS class */
function posClass(pos) {
    const p = String(pos || "").toLowerCase();
    if (p.startsWith("n")) return "pos-noun";
    if (p.startsWith("v")) return "pos-verb";
    if (p.startsWith("adj")) return "pos-adj";
    return "pos-other";
}

/** 품사 → hex color */
function posColor(pos) {
    const p = String(pos || "").toLowerCase();
    if (p.startsWith("n")) return "#3B82F6";
    if (p.startsWith("v")) return "#EF4444";
    if (p.startsWith("adj")) return "#10B981";
    return "";
}

/** 단어를 의미 덩어리(chunk)로 분할 – VCV 경계 기반 */
function chunkWord(word) {
    const VOWELS = /[aeiouAEIOU]/;
    const len = word.length;
    if (len <= 3) return [word];
    const chunks = [];
    let start = 0;
    let chunkSize = 0;
    for (let i = 0; i < len; i++) {
        chunkSize++;
        if (chunkSize >= 3 && i < len - 2) {
            const cur = word[i];
            const next = word[i + 1];
            if (VOWELS.test(cur) && !VOWELS.test(next)) {
                const nextNext = word[i + 2];
                if (VOWELS.test(nextNext)) {
                    chunks.push(word.slice(start, i + 1));
                    start = i + 1;
                    chunkSize = 0;
                }
            }
        }
    }
    if (start < len) chunks.push(word.slice(start));
    return chunks.length > 1 ? chunks : [word];
}

/**
 * card-word 엘리먼트에 POS 컬러를 적용하고
 * chunk 스팬들로 단어를 렌더링.
 * @param {HTMLElement} el  #card-word
 * @param {string} word
 * @param {string} pos
 */
function renderWordColored(el, word, pos) {
    const color = posColor(pos);
    el.style.color = color || "";
    const chunks = chunkWord(word);
    if (chunks.length < 2) {
        el.textContent = word;
        return;
    }
    el.innerHTML = `<span class="chunk-word">${
        chunks.map((c, i) =>
            `<span class="chunk" data-idx="${i}">${escapeHtml(c)}</span>`
        ).join("")
    }</span>`;
}

/**
 * Preview 슬라이드쇼용 청킹 애니메이션.
 * 각 chunk를 순서대로 lit → unlit 하이라이트.
 */
function animateChunks(el, word, pos, totalMs) {
    renderWordColored(el, word, pos);
    const spans = el.querySelectorAll(".chunk");
    if (!spans.length) return;
    const delay = Math.max(220, Math.floor(totalMs / (spans.length + 1)));
    spans.forEach((span, i) => {
        const cls = i % 2 === 0 ? "chunk-lit-a" : "chunk-lit-b";
        setTimeout(() => {
            // 이전 chunk 해제
            spans.forEach(s => s.classList.remove("chunk-lit-a", "chunk-lit-b"));
            span.classList.add(cls);
        }, delay * (i + 1));
        setTimeout(() => span.classList.remove("chunk-lit-a", "chunk-lit-b"),
            delay * (i + 1) + delay - 60);
    });
}

/**
 * Phase 3 Debug Terminal: 틀린 글자 위치를 짚어주는 에러 로그.
 * @returns {string} HTML
 */
function buildDebugLog(expected, typed) {
    const e = [...String(expected)];
    const t = [...String(typed)];
    let firstErrIdx = -1;
    for (let i = 0; i < Math.max(e.length, t.length); i++) {
        if ((t[i] || "").toLowerCase() !== (e[i] || "").toLowerCase()) {
            firstErrIdx = i;
            break;
        }
    }
    if (firstErrIdx === -1) return ""; // no error

    const got = t[firstErrIdx] !== undefined
        ? `'${escapeHtml(t[firstErrIdx])}'`
        : "(missing)";
    const want = e[firstErrIdx] !== undefined
        ? `'${escapeHtml(e[firstErrIdx])}'`
        : "(extra char)";

    return `<div class="debug-terminal">
<span class="debug-line-err">&gt;&gt; Bug Detected at Index ${firstErrIdx}</span><br>
<span class="debug-line-hint">&gt;&gt; Got ${got} — expected ${want}</span><br>
<span class="debug-line-hint">&gt;&gt; Fix the bug and hit Enter again <span class="debug-cursor"></span></span>
</div>`;
}

function bumpWrong(item) {
    if (!item) return;
    wrongMap[item.id] = (wrongMap[item.id] || 0) + 1;
    const sr = document.getElementById("sr-hint");
    if (sr) sr.classList.remove("hidden");
}

function buildMcChoicesFixed(item) {
    const others = shuffle(
        items
            .filter((x) => x.id !== item.id)
            .map((x) => x.answer)
            .filter(Boolean),
    );
    const picks = [];
    for (const o of others) {
        if (o.toLowerCase() === item.answer.toLowerCase()) continue;
        if (!picks.includes(o)) picks.push(o);
        if (picks.length >= 3) break;
    }
    while (picks.length < 3) picks.push("—");
    return shuffle([item.answer, ...picks.slice(0, 3)]);
}

async function apiPreviewTTS(item) {
    const res = await fetch("/api/tts/preview_sequence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word: item.answer, meaning: item.question, example: item.hint }),
    });
    if (!res.ok) throw new Error("tts");
}

async function apiWordMeaning(word, meaning) {
    await fetch("/api/tts/word_meaning", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word, meaning }),
    });
}

async function apiSayLine(text) {
    await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    });
}

async function apiWordOnly(word) {
    await fetch("/api/tts/word_only", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word }),
    });
}

async function apiExampleFull(sentence) {
    await fetch("/api/tts/example_full", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sentence }),
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("lesson-route-hint").textContent = `레슨: ${LESSON} · 영-영 정의 매칭 + 맥락 + 철자`;

    const stepTitle = document.getElementById("current-step-title");
    const progBar = document.getElementById("study-progress");
    const substepInd = document.getElementById("substep-indicator");
    const substepTitle = document.getElementById("substep-title");
    const cardWord = document.getElementById("card-word");
    const cardMeaning = document.getElementById("card-meaning");
    const cardExample = document.getElementById("card-example");
    const cardChipOwn = document.getElementById("card-chip-own");
    const cardChipFinal = document.getElementById("card-chip-final");
    const cardBackHint = document.getElementById("card-back-hint");
    const lessonGrid = document.getElementById("lesson-card-grid");
    const inputContainer = document.getElementById("input-container");
    const answerInput = document.getElementById("answer-input");
    const submitBtn = document.getElementById("submit-btn");
    const inputInstruction = document.getElementById("input-instruction");
    const partialHint = document.getElementById("partial-hint");
    const spellFeedback = document.getElementById("spell-feedback");
    const audioActions = document.getElementById("audio-actions");
    const btnPlayExample = document.getElementById("btn-play-example");
    const btnPlayWord = document.getElementById("btn-play-word");
    const btnEchoTip = document.getElementById("btn-echo-tip");
    const mcGrid = document.getElementById("mc-grid");
    const tutorModal = document.getElementById("tutor-modal");
    const tutorFeedbackText = document.getElementById("tutor-feedback-text");
    const spartaOverlay = document.getElementById("sparta-overlay");
    const penaltyCounter = document.getElementById("penalty-counter");
    const flashcard = document.getElementById("flashcard");
    const previewGate = document.getElementById("preview-gate");
    const previewSlideshowBar = document.getElementById("preview-slideshow-bar");
    const previewDots = document.getElementById("preview-dots");
    const previewProgressLabel = document.getElementById("preview-progress-label");
    const btnPreviewToTraining = document.getElementById("btn-preview-to-training");
    const magicFailStrip = document.getElementById("magic-fail-strip");
    const magicFailCountEl = document.getElementById("magic-fail-count");
    const goldCountEl = document.getElementById("gold-count");
    const adminModal = document.getElementById("admin-modal");
    const visualFallback = document.getElementById("visual-fallback");
    const visualEmoji = document.getElementById("visual-emoji");
    const visualHint = document.getElementById("visual-hint");
    const debugTerminal = document.getElementById("debug-terminal");

    function updateMagicStrip() {
        magicFailCountEl.textContent = String(magicFailCount);
        penaltyCounter.textContent = `(마법 해제: ${magicFailCount}회)`;
    }

    function updateGold() {
        goldCountEl.textContent = String(goldStamps);
        saveGoldStamps(goldStamps);
    }

    function resetTrainingUI() {
        mcGrid.classList.add("hidden");
        mcGrid.innerHTML = "";
        audioActions.classList.add("hidden");
        partialHint.classList.add("hidden");
        spellFeedback.classList.add("hidden");
        spellFeedback.innerHTML = "";
        debugTerminal.classList.add("hidden");
        debugTerminal.innerHTML = "";
        visualFallback.classList.add("hidden");
        cardChipFinal.classList.add("hidden");
        btnEchoTip.classList.add("hidden");
        lastSpellWrong = false;
    }

    function resetCardShell() {
        cardWord.classList.remove("hidden");
        cardMeaning.classList.add("hidden");
        cardExample.classList.add("hidden");
        cardChipOwn.classList.add("hidden");
        inputContainer.style.display = "none";
        answerInput.value = "";
        answerInput.disabled = false;
        flashcard.classList.remove("flipped");
        resetTrainingUI();
    }

    function trainingProgress01() {
        const totalPhases = 7;
        const wordBlock = currentIndex * totalPhases + (trainingPhase - 1);
        const denom = Math.max(1, items.length * totalPhases);
        return wordBlock / denom;
    }

    function progressPct() {
        if (!items.length) return 0;
        if (APP_STATE === "CHALLENGE" && challengeQueue.length)
            return (challengeIndex / challengeQueue.length) * 100;
        if (APP_STATE === "FINAL" && finalQueue.length) return (finalIndex / finalQueue.length) * 85 + 10;
        if (APP_STATE === "TRAINING") return trainingProgress01() * 70;
        if (APP_STATE === "PREVIEW" && items.length) {
            if (previewAutoDone) return 100;
            return (currentIndex / items.length) * 8;
        }
        return 0;
    }

    function renderLessonGrid() {
        lessonGrid.innerHTML = "";
        lessonGrid.classList.remove("hidden");
        items.forEach((it) => {
            const tile = document.createElement("div");
            tile.className = "lesson-tile";
            const ex = parseCardExtra(it);
            const img = ex.image || ex.image_url;
            tile.innerHTML = `
                <div class="lesson-tile-word">${escapeHtml(it.answer)}</div>
                <div class="lesson-tile-def">${escapeHtml(it.question.slice(0, 80))}${it.question.length > 80 ? "…" : ""}</div>
                ${img ? `<div class="lesson-tile-img"><img src="${escapeHtml(img)}" alt="" loading="lazy"/></div>` : `<div class="lesson-tile-emoji">${wordEmoji(it.answer)}</div>`}
            `;
            lessonGrid.appendChild(tile);
        });
    }

    function renderPreviewDots(i) {
        previewDots.innerHTML = "";
        items.forEach((_, idx) => {
            const d = document.createElement("span");
            d.className = "preview-dot" + (idx === i ? " active" : "") + (idx < i ? " done" : "");
            previewDots.appendChild(d);
        });
        previewProgressLabel.textContent = `${i + 1} / ${items.length}`;
    }

    async function buildChallengeQueue() {
        let byItem = {};
        try {
            const res = await fetch(`/api/practice/sentences/${CURRENT_SUBJECT}/${LESSON}`);
            if (res.ok) {
                const data = await res.json();
                byItem = data.by_item_id || {};
            }
        } catch {}

        const pool = [];
        for (const item of items) {
            const own = byItem[item.id];
            let useOwn = own && String(own).trim() && Math.random() < 0.5;
            let displayExample = "";
            if (useOwn) {
                try {
                    displayExample = `"${own.replace(new RegExp(escapeRe(item.answer), "gi"), "________")}"`;
                    if (!displayExample.includes("________")) useOwn = false;
                } catch {
                    useOwn = false;
                }
            }
            if (!useOwn) {
                const displayHint = item.hint.replace(new RegExp(escapeRe(item.answer), "gi"), "________");
                displayExample = `"${displayHint}"`;
            }
            pool.push({
                item,
                mode: useOwn ? "own" : "example",
                displayExample,
                answer: item.answer,
            });
        }
        challengeQueue = shuffle(pool);
        challengeIndex = 0;
    }

    function buildFinalQueue() {
        const scored = items.map((it) => ({ it, n: wrongMap[it.id] || 0 }));
        scored.sort((a, b) => b.n - a.n);
        const top = scored.filter((x) => x.n > 0).slice(0, 3).map((x) => x.it);
        let q = top.length ? top : shuffle(items).slice(0, Math.min(3, items.length));
        if (q.length < Math.min(3, items.length) && items.length >= 3) {
            const rest = shuffle(items.filter((i) => !q.includes(i)));
            while (q.length < 3 && rest.length) q.push(rest.pop());
        }
        finalQueue = q.map((it) => ({
            item: it,
            kind: Math.random() < 0.5 ? "mc" : "ctx",
        }));
        finalIndex = 0;
    }

    function currentItem() {
        if (APP_STATE === "FINAL") return finalQueue[finalIndex]?.item;
        if (APP_STATE === "CHALLENGE") return challengeQueue[challengeIndex]?.item;
        return items[currentIndex];
    }

    function renderArena() {
        previewGate.classList.add("hidden");
        if (APP_STATE === "PREVIEW" && previewAutoDone) {
            previewGate.classList.remove("hidden");
            previewSlideshowBar.classList.remove("hidden");
            lessonGrid.classList.remove("hidden");
            stepTitle.textContent = "워밍업 완료 ✓";
            progBar.style.width = "8%";
            return;
        }

        if (APP_STATE === "CHALLENGE") {
            if (challengeIndex >= challengeQueue.length) {
                transitionState();
                return;
            }
        } else if (APP_STATE === "FINAL") {
            if (finalIndex >= finalQueue.length) {
                transitionState();
                return;
            }
        } else if (APP_STATE === "TRAINING" && currentIndex >= items.length) {
            transitionState();
            return;
        }

        const item = currentItem();
        resetCardShell();

        const imgWrap = document.getElementById("card-image-wrap");
        const imgEl = document.getElementById("card-image");
        const extra = parseCardExtra(item);
        const imgUrl = extra.image || extra.image_url;

        function applyImage() {
            if (imgUrl) {
                imgEl.src = imgUrl;
                imgEl.alt = item.answer;
                imgEl.onerror = () => {
                    imgWrap.classList.add("hidden");
                    if (APP_STATE !== "PREVIEW") {
                        visualFallback.classList.remove("hidden");
                        visualEmoji.textContent = wordEmoji(item.answer);
                        visualHint.textContent = `첫 글자: 「${item.answer[0] || "?"}」 · ${item.answer.length}글자`;
                    }
                };
                imgWrap.classList.remove("hidden");
            } else {
                imgWrap.classList.add("hidden");
                imgEl.removeAttribute("src");
            }
        }

        if (APP_STATE === "PREVIEW") {
            stepTitle.textContent = "1단계 · 눈도장 Preview";
            lessonGrid.classList.remove("hidden");
            substepInd.classList.add("hidden");
            magicFailStrip.classList.add("hidden");
            previewSlideshowBar.classList.remove("hidden");
            applyImage();
            visualFallback.classList.add("hidden");
            cardMeaning.classList.remove("hidden");
            cardExample.classList.remove("hidden");
            const exPreview = parseCardExtra(item);
            renderWordColored(cardWord, item.answer, exPreview.pos || "");
            cardMeaning.textContent = item.question;
            cardExample.textContent = `"${item.hint}"`;
            renderPreviewDots(currentIndex);
            cardBackHint.textContent = item.answer;
        } else if (APP_STATE === "TRAINING") {
            stepTitle.textContent = "2단계 · 기억의 사다리";
            lessonGrid.classList.add("hidden");
            substepInd.classList.remove("hidden");
            magicFailStrip.classList.add("hidden");
            previewSlideshowBar.classList.add("hidden");
            inputContainer.style.display = "flex";
            answerInput.style.display = "block";
            submitBtn.classList.remove("hidden");
            applyImage();

            const phaseLabels = {
                1: "① 따라쓰기 + 듣기",
                2: "② 이미지/연상 → 단어 인출",
                3: "③ 빈 글자 채우기 (인출)",
                4: "④ Meaning Match (영영)",
                5: "⑤ 문맥 · 예문 듣고 빈칸",
                6: "⑥ Spelling Master (발음만)",
                7: "⑦ 나만의 문장 + AI",
            };
            substepTitle.textContent = `${phaseLabels[trainingPhase]} · ${currentIndex + 1}/${items.length}`;

            const exTrain = parseCardExtra(item);
            if (trainingPhase === TP.SHADOW1) {
                renderWordColored(cardWord, item.answer, exTrain.pos || "");
                cardMeaning.classList.remove("hidden");
                cardMeaning.textContent = item.question;
                inputInstruction.textContent = "단어를 보고 그대로 타이핑 (소리도 들어요).";
                void apiWordMeaning(item.answer, item.question);
            } else if (trainingPhase === TP.VISUAL) {
                cardWord.classList.add("hidden");
                cardMeaning.classList.add("hidden");
                cardExample.classList.add("hidden");
                if (imgUrl) {
                    imgWrap.classList.remove("hidden");
                    visualFallback.classList.add("hidden");
                } else {
                    imgWrap.classList.add("hidden");
                    visualFallback.classList.remove("hidden");
                    visualEmoji.textContent = wordEmoji(item.answer);
                    visualHint.textContent = `머릿속 그림과 연결! 첫 글자: 「${item.answer[0] || "?"}」 · 길이 ${item.answer.length}`;
                }
                inputInstruction.textContent = "누워 있는 뜻/그림을 떠올리며 단어 전체를 입력해요.";
            } else if (trainingPhase === TP.PARTIAL) {
                const { mask } = makePartialMask(item.answer);
                partialMask = mask;
                partialHint.textContent = mask;
                partialHint.classList.remove("hidden");
                cardWord.textContent = "???";
                cardMeaning.classList.remove("hidden");
                cardMeaning.textContent = item.question;
                inputInstruction.textContent = "빈 칸을 메워서 완전한 단어로!";
            } else if (trainingPhase === TP.MEANING_MC) {
                cardWord.textContent = "?";
                cardMeaning.classList.remove("hidden");
                cardMeaning.textContent = item.question;
                inputInstruction.textContent = "영어 정의에 맞는 단어를 고르거나 아래에 직접 입력.";
                mcChoices = buildMcChoicesFixed(item);
                mcGrid.innerHTML = "";
                mcChoices.forEach((c) => {
                    const b = document.createElement("button");
                    b.type = "button";
                    b.className = "mc-btn";
                    b.textContent = c;
                    b.onclick = () => pickMc(c, item);
                    mcGrid.appendChild(b);
                });
                mcGrid.classList.remove("hidden");
            } else if (trainingPhase === TP.CONTEXT) {
                cardWord.textContent = "???";
                const dh = item.hint.replace(new RegExp(escapeRe(item.answer), "gi"), "________");
                cardExample.classList.remove("hidden");
                cardExample.textContent = `"${dh}"`;
                inputInstruction.textContent = "예문 전체를 먼저 듣고, 빈칸 단어를 적어요.";
                audioActions.classList.remove("hidden");
                btnPlayExample.classList.remove("hidden");
                btnPlayWord.classList.add("hidden");
                btnEchoTip.classList.remove("hidden");
            } else if (trainingPhase === TP.SPELL) {
                cardWord.textContent = "🔊";
                cardMeaning.classList.remove("hidden");
                cardMeaning.textContent = "(발음만 들었어요 — 철자 전체를 입력)";
                inputInstruction.textContent = "틀리면 어느 글자가 다른지 색으로 보여 드려요.";
                audioActions.classList.remove("hidden");
                btnPlayExample.classList.add("hidden");
                btnPlayWord.classList.remove("hidden");
                btnEchoTip.classList.remove("hidden");
                void apiWordOnly(item.answer);
            } else if (trainingPhase === TP.SENTENCE) {
                renderWordColored(cardWord, item.answer, exTrain.pos || "");
                cardMeaning.classList.remove("hidden");
                cardMeaning.textContent = item.question;
                inputInstruction.textContent = `「${item.answer}」을 꼭 넣어 한 문장만! 하고 싶은 말을 써 볼까?`;
            }
        } else if (APP_STATE === "FINAL") {
            stepTitle.textContent = "파이널 — 자주 틀린 단어 🔥";
            lessonGrid.classList.add("hidden");
            substepInd.classList.remove("hidden");
            substepTitle.textContent = `복습 ${finalIndex + 1} / ${finalQueue.length}`;
            cardChipFinal.classList.remove("hidden");
            magicFailStrip.classList.add("hidden");
            inputContainer.style.display = "flex";
            answerInput.style.display = "block";
            const slot = finalQueue[finalIndex];
            applyImage();
            visualFallback.classList.add("hidden");
            if (slot.kind === "mc") {
                trainingPhase = TP.MEANING_MC;
                cardWord.textContent = "?";
                cardMeaning.classList.remove("hidden");
                cardMeaning.textContent = slot.item.question;
                inputInstruction.textContent = "파이널: 정의에 맞는 단어!";
                mcChoices = buildMcChoicesFixed(slot.item);
                mcGrid.innerHTML = "";
                mcChoices.forEach((c) => {
                    const b = document.createElement("button");
                    b.type = "button";
                    b.className = "mc-btn";
                    b.textContent = c;
                    b.onclick = () => pickMcFinal(c, slot.item);
                    mcGrid.appendChild(b);
                });
                mcGrid.classList.remove("hidden");
            } else {
                cardWord.textContent = "???";
                const dh = slot.item.hint.replace(new RegExp(escapeRe(slot.item.answer), "gi"), "________");
                cardExample.classList.remove("hidden");
                cardExample.textContent = `"${dh}"`;
                inputInstruction.textContent = "예문을 듣고 빈칸을 채워요.";
                audioActions.classList.remove("hidden");
                btnPlayExample.classList.remove("hidden");
                btnPlayWord.classList.add("hidden");
            }
            cardBackHint.textContent = slot.item.answer;
        } else if (APP_STATE === "CHALLENGE") {
            const slot = challengeQueue[challengeIndex];
            stepTitle.textContent = "3단계 · 스파르타 시험 👑";
            lessonGrid.classList.add("hidden");
            substepInd.classList.add("hidden");
            magicFailStrip.classList.remove("hidden");
            updateMagicStrip();
            inputContainer.style.display = "flex";
            answerInput.style.display = "block";
            cardMeaning.classList.add("hidden");
            cardWord.textContent = "???";
            cardExample.textContent = slot.displayExample;
            cardExample.classList.remove("hidden");
            if (slot.mode === "own") cardChipOwn.classList.remove("hidden");
            applyImage();
            visualFallback.classList.add("hidden");
        }

        progBar.style.width = `${Math.min(100, progressPct())}%`;
    }

    function pickMc(choice, item) {
        if (choice.toLowerCase() === item.answer.toLowerCase()) {
            mcGrid.classList.add("hidden");
            void apiWordMeaning(item.answer, item.question);
            advancePhaseOrWord();
        } else {
            bumpWrong(item);
            mcGrid.querySelectorAll(".mc-btn").forEach((b) => b.classList.add("mc-shake"));
            setTimeout(() => mcGrid.querySelectorAll(".mc-btn").forEach((b) => b.classList.remove("mc-shake")), 400);
        }
    }

    function pickMcFinal(choice, item) {
        if (choice.toLowerCase() === item.answer.toLowerCase()) {
            mcGrid.classList.add("hidden");
            finalIndex++;
            renderArena();
        } else {
            bumpWrong(item);
        }
    }

    function advancePhaseOrWord() {
        if (APP_STATE !== "TRAINING") return;
        if (trainingPhase < TP.SENTENCE) {
            trainingPhase++;
            renderArena();
        } else {
            trainingPhase = TP.SHADOW1;
            currentIndex++;
            renderArena();
        }
    }

    function transitionState() {
        if (APP_STATE === "PREVIEW") {
            APP_STATE = "TRAINING";
            currentIndex = 0;
            trainingPhase = TP.SHADOW1;
            previewGate.classList.add("hidden");
            lessonGrid.classList.add("hidden");
            renderArena();
        } else if (APP_STATE === "TRAINING") {
            APP_STATE = "FINAL";
            buildFinalQueue();
            finalIndex = 0;
            renderArena();
        } else if (APP_STATE === "FINAL") {
            APP_STATE = "CHALLENGE";
            buildChallengeQueue().then(() => renderArena());
        } else if (APP_STATE === "CHALLENGE") {
            void fetch("/api/progress/challenge_complete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ subject: CURRENT_SUBJECT, lesson: LESSON }),
            });
            window.location.href = "/?cleared=1";
        }
    }

    async function runPreviewSlideshow() {
        if (!items.length || previewRunning || previewAutoDone) return;
        previewRunning = true;
        previewAutoDone = false;
        await apiSayLine(`Today we have ${items.length} words! Let's listen to each one.`);
        for (let i = 0; i < items.length; i++) {
            currentIndex = i;
            renderArena();
            const itEx = parseCardExtra(items[i]);
            // 청킹 애니메이션 (TTS 재생과 동시에)
            animateChunks(cardWord, items[i].answer, itEx.pos || "", 2400);
            try {
                await apiPreviewTTS(items[i]);
            } catch {
                await apiSayLine(`${items[i].answer}. ${items[i].question}.`);
            }
        }
        previewRunning = false;
        previewAutoDone = true;
        currentIndex = Math.max(0, items.length - 1);
        renderArena();
    }

    async function handleSubmit() {
        if (APP_STATE === "PREVIEW") return;

        const val = answerInput.value.trim();
        const item = currentItem();

        if (APP_STATE === "FINAL") {
            const slot = finalQueue[finalIndex];
            if (slot.kind === "mc") {
                if (!val) return;
                if (val.toLowerCase() === slot.item.answer.toLowerCase()) {
                    finalIndex++;
                    renderArena();
                } else bumpWrong(slot.item);
                return;
            }
            if (!val) return;
            if (val.toLowerCase() === slot.item.answer.toLowerCase()) {
                finalIndex++;
                renderArena();
            } else bumpWrong(slot.item);
            return;
        }

        if (APP_STATE === "TRAINING") {
            if (trainingPhase === TP.MEANING_MC) {
                if (!val) return;
                if (val.toLowerCase() === item.answer.toLowerCase()) {
                    mcGrid.classList.add("hidden");
                    await apiWordMeaning(item.answer, item.question);
                    advancePhaseOrWord();
                } else {
                    bumpWrong(item);
                    answerInput.style.color = "red";
                    setTimeout(() => (answerInput.style.color = ""), 400);
                }
                return;
            }
            if (trainingPhase === TP.SENTENCE) {
                if (val.split(/\s+/).length < 2) {
                    answerInput.style.borderColor = 'var(--danger, #FF3B30)';
                    answerInput.placeholder = '한 문장으로 써 볼까?';
                    setTimeout(() => {
                        answerInput.style.borderColor = '';
                        answerInput.placeholder = '';
                    }, 2000);
                    return;
                }
                lastTrainingSentence = val;
                answerInput.disabled = true;
                submitBtn.textContent = "…";
                try {
                    const res = await fetch("/api/tutor", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ word: item.answer, sentence: val }),
                    });
                    if (!res.ok) throw new Error(`tutor ${res.status}`);
                    const d = await res.json();
                    const rawFeedback = d.feedback || "";
                    // XSS 방지: 먼저 HTML 이스케이프 후 safe markdown 변환
                    const escaped = escapeHtml(rawFeedback);
                    // Story Relay 섹션 감지 후 스타일 박스 적용
                    const storyStart = /📖\s*\*\*Story Relay\*\*/;
                    const cheerStart = /🎉\s*\*\*Cheer\*\*/;
                    let styledFeedback;
                    if (storyStart.test(escaped) && cheerStart.test(escaped)) {
                        styledFeedback = escaped
                            .replace(storyStart, '📖 **Story Relay**\n<div class="story-relay">')
                            .replace(cheerStart, '</div>\n\n🎉 **Cheer**');
                    } else {
                        styledFeedback = escaped;
                    }
                    styledFeedback = styledFeedback
                        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                        .replace(/\n/g, "<br>");
                    tutorFeedbackText.innerHTML = styledFeedback;
                    tutorModal.classList.remove("hidden");
                } catch {
                    tutorFeedbackText.innerHTML = `🪄 <strong>${escapeHtml(item.answer)}</strong> — 멋진 문장이에요! 💖<br>✨ Ollama가 잠깐 자고 있어요. 잠시 후 다시 시도해봐요!<br>🌟 아빠가 정말 자랑스러워할 거예요!`;
                    tutorModal.classList.remove("hidden");
                } finally {
                    answerInput.disabled = false;
                    submitBtn.textContent = "확인";
                }
                return;
            }

            if (!val) return;

            if (trainingPhase === TP.SHADOW1 || trainingPhase === TP.VISUAL) {
                if (val.toLowerCase() === item.answer.toLowerCase()) {
                    await apiWordMeaning(item.answer, item.question);
                    advancePhaseOrWord();
                } else {
                    bumpWrong(item);
                    answerInput.style.color = "red";
                    setTimeout(() => (answerInput.style.color = ""), 400);
                }
                return;
            }

            if (trainingPhase === TP.PARTIAL) {
                if (val.toLowerCase() === item.answer.toLowerCase()) {
                    await apiWordMeaning(item.answer, item.question);
                    advancePhaseOrWord();
                } else {
                    bumpWrong(item);
                    partialHint.textContent = `${partialMask} → 아직 달라요. 다시!`;
                }
                return;
            }

            if (trainingPhase === TP.CONTEXT) {
                if (val.toLowerCase() === item.answer.toLowerCase()) {
                    await apiWordMeaning(item.answer, item.question);
                    advancePhaseOrWord();
                } else {
                    bumpWrong(item);
                    answerInput.style.color = "red";
                    setTimeout(() => (answerInput.style.color = ""), 400);
                }
                return;
            }

            if (trainingPhase === TP.SPELL) {
                if (val.toLowerCase() === item.answer.toLowerCase()) {
                    // ✓ 성공 — System Optimized
                    spellFeedback.classList.add("hidden");
                    debugTerminal.innerHTML = `<div class="debug-terminal">
<span class="debug-line-ok">&gt;&gt; System Optimized. Spelling Verified. ✓</span><br>
<span class="debug-line-ok">&gt;&gt; "${escapeHtml(item.answer)}" — perfect run! 🚀</span>
</div>`;
                    debugTerminal.classList.remove("hidden");
                    debugTerminal.querySelector(".debug-terminal").style.border = "1px solid #3fb950";
                    await apiWordMeaning(item.answer, "Perfect spelling!");
                    advancePhaseOrWord();
                } else {
                    bumpWrong(item);
                    // Debug Terminal 에러 로그 (바로 리셋하지 않음)
                    const debugHtml = buildDebugLog(item.answer, val);
                    if (debugHtml) {
                        debugTerminal.innerHTML = debugHtml;
                        debugTerminal.classList.remove("hidden");
                    }
                    spellFeedback.innerHTML = spellCompareHtml(item.answer, val);
                    spellFeedback.classList.remove("hidden");
                    lastSpellWrong = true;
                    // 입력창을 지우지 않고 커서만 이동 (스스로 수정하도록)
                    answerInput.focus();
                }
                return;
            }
        }

        if (APP_STATE === "CHALLENGE") {
            if (!val) return;
            const slot = challengeQueue[challengeIndex];
            if (val.toLowerCase() === slot.answer.toLowerCase()) {
                challengeIndex++;
                renderArena();
            } else spartaReset();
        }
    }

    function spartaReset() {
        magicFailCount++;
        updateMagicStrip();
        void fetch("/api/progress/sparta_reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: CURRENT_SUBJECT, lesson: LESSON }),
        });
        inputContainer.style.display = "none";
        spartaOverlay.classList.remove("hidden");
        void apiSayLine("앗! 마법이 풀렸어요. 첫 시험 문제부터!");
        challengeIndex = 0;
        answerInput.value = "";
        setTimeout(() => {
            spartaOverlay.classList.add("hidden");
            inputContainer.style.display = "flex";
            renderArena();
        }, 2200);
    }

    function validateChallengeLive() {
        if (APP_STATE !== "CHALLENGE") return;
        const val = answerInput.value.trim().toLowerCase();
        if (!val) return;
        const target = challengeQueue[challengeIndex].answer.toLowerCase();
        if (!target.startsWith(val)) spartaReset();
    }

    btnPlayExample.addEventListener("click", () => {
        const it = currentItem();
        if (it) void apiExampleFull(it.hint);
    });
    btnPlayWord.addEventListener("click", () => {
        const it = currentItem();
        if (it) void apiWordOnly(it.answer);
    });
    btnEchoTip.addEventListener("click", () => {
        void apiSayLine("Listen carefully, then say it out loud with me in your mind!");
    });

    submitBtn.addEventListener("click", handleSubmit);
    answerInput.addEventListener("keyup", (e) => {
        if (APP_STATE === "CHALLENGE") validateChallengeLive();
        if (e.key === "Enter") handleSubmit();
    });

    flashcard.addEventListener("click", () => flashcard.classList.toggle("flipped"));
    flashcard.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            flashcard.classList.toggle("flipped");
        }
    });

    btnPreviewToTraining.addEventListener("click", () => transitionState());

    document.getElementById("btn-tutor-next").addEventListener("click", async () => {
        tutorModal.classList.add("hidden");
        const item = items[currentIndex];
        try {
            await fetch("/api/practice/sentence", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    subject: CURRENT_SUBJECT,
                    lesson: LESSON,
                    item_id: item.id,
                    sentence: lastTrainingSentence,
                }),
            });
        } catch {}
        goldStamps++;
        updateGold();
        await apiWordMeaning(item.answer, "Great job!");
        trainingPhase = TP.SHADOW1;
        currentIndex++;
        answerInput.disabled = false;
        submitBtn.textContent = "확인";
        renderArena();
    });

    document.getElementById("btn-study-home").addEventListener("click", (e) => {
        e.preventDefault();
        window.location.href = "/";
    });

    document.getElementById("btn-dad-settings").addEventListener("click", () =>
        adminModal.classList.remove("hidden"));
    document.getElementById("admin-close").addEventListener("click", () => adminModal.classList.add("hidden"));

    document.getElementById("btn-add-reward").addEventListener("click", async () => {
        const title = document.getElementById("admin-reward-title").value;
        const desc = document.getElementById("admin-reward-desc").value;
        const rewardBtn = document.getElementById("btn-add-reward");
        if (!title || !desc) return showAdminMsg(rewardBtn, "제목과 조건을 입력해 주세요.", true);
        await fetch("/api/rewards", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description: desc }),
        });
        document.getElementById("admin-reward-title").value = "";
        document.getElementById("admin-reward-desc").value = "";
        showAdminMsg(rewardBtn, "저장했어요!", false);
    });

    document.getElementById("btn-add-sch").addEventListener("click", async () => {
        const date = document.getElementById("admin-sch-date").value;
        const memo = document.getElementById("admin-sch-memo").value;
        const schBtn = document.getElementById("btn-add-sch");
        if (!date || !memo) return showAdminMsg(schBtn, "날짜와 메모를 입력해 주세요.", true);
        await fetch("/api/schedules", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ test_date: date, memo }),
        });
        document.getElementById("admin-sch-date").value = "";
        document.getElementById("admin-sch-memo").value = "";
        showAdminMsg(schBtn, "저장했어요!", false);
    });

    (async function init() {
        try {
            const res = await fetch(`/api/study/${CURRENT_SUBJECT}/${LESSON}`);
            if (!res.ok) throw new Error("load");
            const data = await res.json();
            items = data.items || [];
            if (!items.length) {
                console.error("단어가 없어요. 홈에서 사진을 넣거나 init_db를 실행해 주세요.");
                window.location.href = "/";
                return;
            }
            APP_STATE = "PREVIEW";
            currentIndex = 0;
            trainingPhase = TP.SHADOW1;
            magicFailCount = 0;
            goldStamps = loadGoldStamps();
            updateGold();
            challengeQueue = [];
            challengeIndex = 0;
            previewAutoDone = false;
            wrongMap = {};
            renderLessonGrid();
            renderArena();
            runPreviewSlideshow();
        } catch {
            console.error("데이터를 불러오지 못했어요.");
            window.location.href = "/";
        }
    })();
});
