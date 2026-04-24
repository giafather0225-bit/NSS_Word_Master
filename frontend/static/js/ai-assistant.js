/* ai-assistant.js — Main Logic (V2 Ultimate + CR) */

(function shadowAssistantInit() {
    'use strict';
  
    // dependency check
    if (typeof ShadowSTT === 'undefined') {
      console.warn('[Shadow] ai-assistant-stt.js not loaded - STT disabled');
    }
    if (typeof ShadowTTS === 'undefined') {
      console.warn('[Shadow] ai-assistant-tts.js not loaded - TTS disabled');
    }
  
    // wait for DOM
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  
    function init() {
        const root = document.getElementById('shadow-assistant-root');
        if (!root) {
            console.error('[Shadow] #shadow-assistant-root not found in DOM');
            return;
        }
    
        const ERROR_MESSAGES = {
            network: "No internet connection. I'll let you know when it's back!",
            gemini_fail: "Something went wrong. Try asking again!",
            mic_denied: "I can't hear you! Please allow microphone access.",
            mic_not_supported: "Voice isn't supported here — try typing your question!",
            timeout: "Shadow took too long thinking. Try asking again!",
            empty: "Didn't catch that! Say it again."
        };

        const LIMIT_MESSAGES = [
            "Ugh, I'm SO sleepy right now... Talk tomorrow?",
            "My tummy is growling like crazy. Gotta eat! See you tomorrow!",
            "I'm running on empty today. Let's pick this up tomorrow!",
            "Yawwwn... I literally cannot keep my eyes open. Tomorrow, okay?",
            "I need a snack break. A long one. See you tomorrow!",
            "Brain's full! No more room today. Back tomorrow fresh!",
            "Okay I'm done for today, I need a nap. Bye for now!",
        ];
    
        const fabBtn = document.getElementById('shadow-fab');
        const rootPanel = document.getElementById('shadow-assistant-root');
        const closeBtn = document.getElementById('shadow-close-btn');
        const sendBtn = document.getElementById('shadow-send-btn');
        const micBtn = document.getElementById('shadow-mic-btn');
        const input = document.getElementById('shadow-text-input');
        const messagesBox = document.getElementById('shadow-messages');
        
        const onboarding = document.getElementById('shadow-onboarding');
        const chatPanel = document.getElementById('shadow-chat');
        const permitBtn = document.getElementById('shadow-onboarding-ok');
        
        const remainingLabel = document.getElementById('shadow-turn-badge');
        const statusDot = document.getElementById('shadow-status-dot');
        const statusText = document.getElementById('shadow-header-status');
        const thinkingIndicator = document.getElementById('shadow-thinking');
        
        const restOverlay = document.getElementById('shadow-rest-overlay');
        const restOkBtn = document.getElementById('shadow-rest-ok');
        
        let historyLog = [];
        let sessionId = "gia-" + Date.now().toString();
        let isDebouncing = false;
        
        let timerStarted = false;
        let stt = null;

        // --- EXAM OVERLAY OBSERVER ---
        const EXAM_OVERLAY_IDS = ['exam-overlay', 'ut-overlay'];

        function updateFabVisibility() {
            const fab = document.getElementById('shadow-fab');
            if (!fab) return;

            const examActive = EXAM_OVERLAY_IDS.some(id => {
                const el = document.getElementById(id);
                return el && !el.classList.contains('hidden');
            });

            if (examActive) {
                fab.style.display = 'none';
                fab.setAttribute('aria-hidden', 'true');
                closeWidget();
            } else {
                fab.style.display = '';
                fab.removeAttribute('aria-hidden');
            }
        }

        const examObserver = new MutationObserver(updateFabVisibility);
        EXAM_OVERLAY_IDS.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                examObserver.observe(el, { attributes: true, attributeFilter: ['class'] });
            }
        });
    
        // --- 15 MIN TIMER ---
        const MAX_15M_SEC = 15 * 60; 
        let currentSessionSec = 0;
        let timerInterval = null;
    
        function startTimer() {
            if (timerStarted) return;
            timerStarted = true;
            currentSessionSec = 0;
            
            const timerFill = document.getElementById('shadow-timer-fill');
            const timerBar = document.getElementById('shadow-timer-bar');

            timerInterval = setInterval(() => {
                currentSessionSec += 1;
                
                const pct = (currentSessionSec / MAX_15M_SEC) * 100;
                timerFill.style.width = pct + "%";
                timerBar.setAttribute("aria-valuenow", currentSessionSec);
    
                if (currentSessionSec === 12 * 60) {
                    renderBubble("Break time coming up soon!", false);
                    if (window.ShadowTTS) window.ShadowTTS.speak("Break time coming up soon!");
                }
                if (currentSessionSec >= 15 * 60) {
                    clearInterval(timerInterval);
                    restOverlay.classList.remove('hidden');
                    document.getElementById('shadow-input-area').style.pointerEvents = 'none';
                    document.getElementById('shadow-input-area').style.opacity = '0.5';
                    if (window.ShadowTTS) window.ShadowTTS.speak("Time for a quick break. See you in 10 minutes!");
                    
                    setTimeout(() => {
                        document.getElementById('shadow-input-area').style.pointerEvents = 'auto';
                        document.getElementById('shadow-input-area').style.opacity = '1.0';
                        restOverlay.classList.add('hidden');
                        timerStarted = false; 
                        currentSessionSec = 0;
                        timerFill.style.width = "0%";
                        timerBar.setAttribute("aria-valuenow", 0);
                    }, 10 * 60 * 1000);
                }
            }, 1000);
        }
        
        restOkBtn.addEventListener('click', () => {
            restOverlay.classList.add('hidden');
        });

        function isOpen() {
            return !rootPanel.classList.contains('hidden');
        }

        function openWidget() {
            rootPanel.classList.remove('hidden');
            fabBtn.setAttribute('aria-expanded', 'true');
            fabBtn.classList.add('active');
            stopWakeWord();
            if (window.visualViewport) window.visualViewport.addEventListener('resize', handleViewportResize);
            input?.focus();
        }

        function closeWidget() {
            rootPanel.classList.add('hidden');
            fabBtn.setAttribute('aria-expanded', 'false');
            fabBtn.classList.remove('active');
            if (window.visualViewport) window.visualViewport.removeEventListener('resize', handleViewportResize);
            if (window.ShadowTTS?.isPlaying) window.ShadowTTS.stop();
            startWakeWord();
        }

        fabBtn.addEventListener('click', () => {
            if (isOpen()) { closeWidget(); return; }
            if (!localStorage.getItem('shadow_onboarded')) {
                onboarding.style.display = 'flex';
                chatPanel.style.display = 'none';
            } else {
                onboarding.style.display = 'none';
                chatPanel.style.display = 'flex';
            }
            openWidget();
        });

        closeBtn.addEventListener('click', closeWidget);

        // --- WAKE WORD ("Shadow") ---
        let wakeRecognition = null;

        function startWakeWord() {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRec || isOpen()) return;
            try {
                wakeRecognition = new SpeechRec();
                wakeRecognition.lang = 'en-US';
                wakeRecognition.continuous = true;
                wakeRecognition.interimResults = true;
                wakeRecognition.onresult = (e) => {
                    for (let i = e.resultIndex; i < e.results.length; i++) {
                        const t = e.results[i][0].transcript.toLowerCase();
                        if (t.includes('shadow')) {
                            wakeRecognition.stop();
                            onWakeWord();
                            return;
                        }
                    }
                };
                wakeRecognition.onend = () => {
                    if (!isOpen()) startWakeWord();
                };
                wakeRecognition.onerror = () => {};
                wakeRecognition.start();
            } catch (e) {}
        }

        function stopWakeWord() {
            try { wakeRecognition?.stop(); } catch (e) {}
            wakeRecognition = null;
        }

        function onWakeWord() {
            if (!localStorage.getItem('shadow_onboarded')) {
                onboarding.style.display = 'flex';
                chatPanel.style.display = 'none';
            } else {
                onboarding.style.display = 'none';
                chatPanel.style.display = 'flex';
            }
            openWidget();
            fabBtn.classList.add('active');
            const greeting = "Hey! Go ahead, I'm listening.";
            renderBubble(greeting, false);
            if (window.ShadowTTS) window.ShadowTTS.speak(greeting);
            setTimeout(() => {
                if (stt && !stt.isRecording) {
                    statusText.textContent = 'Listening...';
                    statusDot.style.background = 'red';
                    lastInputWasVoice = true;
                    stt.startListening();
                }
            }, 800);
        }

        startWakeWord();
    
        // --- EVENT BUBBLING MITIGATION ---
        document.addEventListener('keydown', (e) => {
            const isWidgetOpen = !rootPanel.classList.contains('hidden');
            if (!isWidgetOpen) return;
        
            const focusInWidget = rootPanel.contains(document.activeElement);
        
            if (e.key === 'Escape') {
              e.stopPropagation();
              e.preventDefault();
              closeWidget();
              fabBtn?.focus();
              return;
            }
        
            if (e.key === 'Enter' && focusInWidget) {
              if (document.activeElement === input && input.value.trim()) {
                e.stopPropagation();
                e.preventDefault();
                lastInputWasVoice = false;
                handleSend();
              }
            }
        }, true);
    
        function handleViewportResize() {
            const offset = window.innerHeight - window.visualViewport.height;
            rootPanel.style.bottom = (offset + 20) + 'px';
        }
    
        input.addEventListener('input', () => {
            sendBtn.disabled = input.value.trim().length === 0;
        });

        // --- ONBOARDING LOGIC ---
        function showMicDeniedNotice() {
            const notice = document.getElementById('shadow-mic-denied');
            if (notice) notice.classList.remove('hidden');
            setTimeout(() => notice?.classList.add('hidden'), 3000);
        }
          
        function hideMicButton() {
            if (micBtn) {
              micBtn.style.display = 'none';
              localStorage.setItem('shadow_mic_denied', 'true');
            }
        }

        async function requestMicPermission() {
            try {
              if (navigator.permissions?.query) {
                const status = await navigator.permissions.query({ name: 'microphone' });
                if (status.state === 'denied') return false;
              }
              const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
              stream.getTracks().forEach(t => t.stop());
              return true;
            } catch {
              return false;
            }
        }

        permitBtn.addEventListener('click', () => {
            requestMicPermission().then(granted => {
              if (!granted) {
                showMicDeniedNotice();
                hideMicButton();
              }
            });
      
            localStorage.setItem('shadow_onboarded', 'true');
            onboarding.style.display = 'none';
            chatPanel.style.display = 'flex';
            input?.focus();
        }, { once: true });
    
        // --- HISTORY ---
        function loadHistory() {
            try {
                const saved = sessionStorage.getItem('shadow_history');
                if (saved) {
                    historyLog = JSON.parse(saved);
                    historyLog.forEach(msg => renderBubble(msg.content, msg.role === 'user', false, true));
                }
            } catch (e) {
                console.warn(e);
            }
        }
    
        function saveHistory(role, content) {
            historyLog.push({ role, content });
            if (historyLog.length > 10) historyLog = historyLog.slice(-10);
            try {
                sessionStorage.setItem('shadow_history', JSON.stringify(historyLog));
            } catch (e) {
                sessionStorage.removeItem('shadow_history');
            }
        }
    
        function renderBubble(text, isUser, isError = false, skipScroll = false) {
            const bubble = document.createElement('div');
            bubble.className = `shadow-msg shadow-msg--${isUser ? 'user' : 'assistant'}`;
            
            const txtSpan = document.createElement('span');
            txtSpan.className = 'shadow-msg-text';
            if (isError) txtSpan.style.color = 'red';
            txtSpan.textContent = text;
            bubble.appendChild(txtSpan);
            
            messagesBox.appendChild(bubble);
            if(!skipScroll) messagesBox.scrollTop = messagesBox.scrollHeight;
        }
    
        let lastInputWasVoice = false;

        // STT Init
        if (window.ShadowSTT) {
            stt = new window.ShadowSTT(
                (text) => { input.value = text; lastInputWasVoice = true; handleSend(); },
                (err) => { 
                    statusText.textContent = 'Ready';
                    statusDot.style.background = '#4CAF50';
                    if (err === 'not-allowed') {
                        showMicDeniedNotice();
                        hideMicButton();
                    }
                },
                () => { 
                    statusText.textContent = 'Ready';
                    statusDot.style.background = '#4CAF50';
                }
            );
        }
    
        micBtn.addEventListener('click', async () => {
            if (isDebouncing) return;
            if (stt && !stt.isRecording) {
                statusText.textContent = 'Listening...';
                statusDot.style.background = 'red';
                await stt.startListening();
            } else if (stt && stt.isRecording) {
                stt.stopListening();
            }
        });
    
        sendBtn.addEventListener('click', () => { lastInputWasVoice = false; handleSend(); });
    
        async function handleSend() {
            if (isDebouncing) return;
            
            let text = input.value.trim();
            if (!text) {
                if (stt && stt.isRecording) stt.stopListening(); 
                return;
            }
    
            if (navigator.onLine === false) {
                renderBubble(ERROR_MESSAGES.network, false, true);
                return;
            }
    
            startTimer();
            isDebouncing = true;
            sendBtn.disabled = true;
            micBtn.style.opacity = '0.4';
            input.readOnly = true;
    
            renderBubble(text, true);
            saveHistory('user', text);
            input.value = '';
    
            thinkingIndicator.classList.remove('hidden');
            messagesBox.scrollTop = messagesBox.scrollHeight;
            
            statusText.textContent = 'Thinking...';
            statusDot.style.background = 'orange';
    
            try {
                const res = await fetch("/api/assistant/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        message: text,
                        history: historyLog,
                        session_id: sessionId,
                        context: window.shadowContext || null,
                    })
                });
    
                thinkingIndicator.classList.add('hidden');
                statusText.textContent = 'Ready';
                statusDot.style.background = '#4CAF50';
    
                if (res.status === 429) {
                    const msg = LIMIT_MESSAGES[Math.floor(Math.random() * LIMIT_MESSAGES.length)];
                    renderBubble(msg, false);
                    return;
                }
                if (!res.ok) throw new Error("Fallback Error");
    
                const data = await res.json();
                
                var reply = data.reply || data.message || 'No response received!';
                renderBubble(reply, false);
                saveHistory('assistant', reply);
                if (data.remaining_today !== undefined) remainingLabel.textContent = data.remaining_today;
                
                if (lastInputWasVoice && window.ShadowTTS) window.ShadowTTS.speak(reply);
                lastInputWasVoice = false;
    
            } catch (e) {
                thinkingIndicator.classList.add('hidden');
                statusText.textContent = 'Ready';
                statusDot.style.background = '#4CAF50';
                renderBubble(ERROR_MESSAGES.gemini_fail, false, true);
            } finally {
                setTimeout(() => {
                    isDebouncing = false;
                    sendBtn.disabled = false;
                    micBtn.style.opacity = '1.0';
                    input.readOnly = false;
                    input.focus();
                }, 2000);
            }
        }
    
        loadHistory();
        console.log('[Shadow] Assistant initialized');
    }

})();
