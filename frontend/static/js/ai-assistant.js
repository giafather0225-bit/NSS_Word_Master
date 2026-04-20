/* ai-assistant.js — Main Logic (V2 Ultimate + CR) */

(function shadowAssistantInit() {
    'use strict';
  
    // 의존성 확인
    if (typeof ShadowSTT === 'undefined') {
      console.error('[Shadow] ai-assistant-stt.js not loaded');
      return;
    }
    if (typeof ShadowTTS === 'undefined') {
      console.error('[Shadow] ai-assistant-tts.js not loaded');
      return;
    }
  
    // DOM 준비 대기
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
            network: "인터넷이 쉬고 있어! 다시 연결되면 알려줄게 🗺️",
            gemini_fail: "머리가 복잡해졌어. 한 번만 더 물어봐! 🤔",
            mic_denied: "네 목소리가 안 들려! 마이크 권한을 허용해줘 🎙️",
            mic_not_supported: "키보드로 타자를 쳐서 물어볼 수 있어요! ⌨️",
            limit: "섀도우도 좀 쉬어야 해! 내일 또 만나자 😴",
            timeout: "섀도우가 너무 오래 생각했어! 다시 물어봐줄래? ⏰",
            empty: "뭐라고 했어? 섀도우가 못 들었어! 다시 말해줘 👂"
        };
    
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
                    renderBubble("우리 조금 있으면 쉬는 시간이야! 🕐", false);
                    if (window.ShadowTTS) window.ShadowTTS.speak("우리 조금 있으면 쉬는 시간이야!");
                }
                if (currentSessionSec >= 15 * 60) {
                    clearInterval(timerInterval);
                    restOverlay.classList.remove('hidden');
                    document.getElementById('shadow-input-area').style.pointerEvents = 'none';
                    document.getElementById('shadow-input-area').style.opacity = '0.5';
                    if (window.ShadowTTS) window.ShadowTTS.speak("잠깐 휴식 시간이야. 10분 뒤에 만나!");
                    
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

        function openWidget() {
            rootPanel.classList.remove('hidden');
            fabBtn.setAttribute('aria-expanded', 'true');
            if (window.visualViewport) window.visualViewport.addEventListener('resize', handleViewportResize);
            input?.focus();
        }

        function closeWidget() {
            rootPanel.classList.add('hidden');
            fabBtn.setAttribute('aria-expanded', 'false');
            if (window.visualViewport) window.visualViewport.removeEventListener('resize', handleViewportResize);
            if (window.ShadowTTS?.isPlaying) window.ShadowTTS.stop();
        }
    
        fabBtn.addEventListener('click', () => {
            if (!localStorage.getItem('shadow_onboarded')) {
                onboarding.style.display = 'flex';
                chatPanel.style.display = 'none';
            } else {
                onboarding.style.display = 'none';
                chatPanel.style.display = 'block';
            }
            openWidget();
        });
    
        closeBtn.addEventListener('click', closeWidget);
    
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
            chatPanel.style.display = 'block';
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
            bubble.className = \`shadow-msg shadow-msg--\${isUser ? 'user' : 'assistant'}\`;
            
            const txtSpan = document.createElement('span');
            txtSpan.className = 'shadow-msg-text';
            if (isError) txtSpan.style.color = 'red';
            txtSpan.textContent = text;
            bubble.appendChild(txtSpan);
            
            messagesBox.appendChild(bubble);
            if(!skipScroll) messagesBox.scrollTop = messagesBox.scrollHeight;
        }
    
        // STT Init
        if (window.ShadowSTT) {
            stt = new window.ShadowSTT(
                (text) => { input.value = text; handleSend(); },
                (err) => { 
                    statusText.textContent = '대화 가능';
                    statusDot.style.background = '#4CAF50';
                    if (err === 'not-allowed') {
                        showMicDeniedNotice();
                        hideMicButton();
                    }
                },
                () => { 
                    statusText.textContent = '대화 가능';
                    statusDot.style.background = '#4CAF50';
                }
            );
        }
    
        micBtn.addEventListener('click', async () => {
            if (isDebouncing) return;
            if (stt && !stt.isRecording) {
                statusText.textContent = '듣고 있어...';
                statusDot.style.background = 'red';
                await stt.startListening();
            } else if (stt && stt.isRecording) {
                stt.stopListening();
            }
        });
    
        sendBtn.addEventListener('click', handleSend);
    
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
            
            statusText.textContent = '생각하는 중...';
            statusDot.style.background = 'orange';
    
            try {
                const res = await fetch("/api/assistant/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: text, history: historyLog, session_id: sessionId })
                });
    
                thinkingIndicator.classList.add('hidden');
                statusText.textContent = '대화 가능';
                statusDot.style.background = '#4CAF50';
    
                if (res.status === 429) {
                    renderBubble(ERROR_MESSAGES.limit, false);
                    document.getElementById('shadow-input-area').style.pointerEvents = 'none';
                    return;
                }
                if (!res.ok) throw new Error("Fallback Error");
    
                const data = await res.json();
                
                renderBubble(data.reply, false);
                saveHistory('assistant', data.reply);
                remainingLabel.textContent = data.remaining_today;
                
                if (window.ShadowTTS) window.ShadowTTS.speak(data.reply);
    
            } catch (e) {
                thinkingIndicator.classList.add('hidden');
                statusText.textContent = '대화 가능';
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
