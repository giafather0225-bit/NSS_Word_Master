/* ai-assistant.js */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Inject DOM for the Assistant Widget if it doesn't exist
    if (!document.getElementById('gia-assistant-widget')) {
        const widgetHTML = `
            <div id="gia-assistant-widget">
                <div id="gia-assistant-panel">
                    <div id="gia-assistant-header">
                        <span>✨ Shadow 튜터</span>
                        <button id="gia-assistant-close">&times;</button>
                    </div>
                    <div id="gia-assistant-chat">
                        <div class="chat-bubble ai">안녕 지아! 뭐든 물어보렴! ✨</div>
                    </div>
                    <div id="gia-assistant-input-area">
                        <button id="gia-assistant-mic" title="음성으로 질문하기">🎙</button>
                        <input type="text" id="gia-assistant-text" placeholder="궁금한 걸 물어봐!" autocomplete="off" />
                    </div>
                </div>
                <div id="gia-assistant-button" title="Shadow 부르기">
                    <img src="/static/img/GIA_Logo.png" alt="GIA Logo">
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    const widget = document.getElementById('gia-assistant-widget');
    const panel = document.getElementById('gia-assistant-panel');
    const btn = document.getElementById('gia-assistant-button');
    const closeBtn = document.getElementById('gia-assistant-close');
    const chatBox = document.getElementById('gia-assistant-chat');
    const input = document.getElementById('gia-assistant-text');
    const micBtn = document.getElementById('gia-assistant-mic');

    let recognition = null;
    let isListening = false;

    // 2. Setup Web Speech API for STT
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'ko-KR'; // Default to Korean, handles English well too
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isListening = true;
            micBtn.classList.add('recording');
            btn.classList.add('listening');
            input.placeholder = "듣고 있어요...";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            input.value = transcript;
            sendMessage(transcript);
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            stopListening();
            input.placeholder = "궁금한 걸 물어봐!";
        };

        recognition.onend = () => {
            stopListening();
        };
    } else {
        micBtn.style.display = 'none'; // Hide if not supported
    }

    function togglePanel() {
        if (panel.classList.contains('open')) {
            panel.classList.remove('open');
        } else {
            panel.classList.add('open');
            input.focus();
        }
    }

    function stopListening() {
        isListening = false;
        micBtn.classList.remove('recording');
        btn.classList.remove('listening');
        input.placeholder = "궁금한 걸 물어봐!";
    }

    // 3. UI Interactions
    btn.addEventListener('click', togglePanel);
    closeBtn.addEventListener('click', () => panel.classList.remove('open'));

    micBtn.addEventListener('click', () => {
        if (isListening) {
            recognition.stop();
        } else if (recognition) {
            recognition.start();
        } else {
            alert("이 브라우저에서는 음성 인식을 지원하지 않아요.");
        }
    });

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const text = input.value.trim();
            if (text) {
                sendMessage(text);
                input.value = '';
            }
        }
    });

    // 4. Send Message to AI & TTS
    async function sendMessage(text) {
        // Add User Bubble
        chatBox.innerHTML += \`<div class="chat-bubble user">\${text}</div>\`;
        chatBox.scrollTop = chatBox.scrollHeight;

        // Add Loading AI Bubble
        const loadingId = 'loading-' + Date.now();
        chatBox.innerHTML += \`<div id="\${loadingId}" class="chat-bubble ai"><span class="loading-dots">생각하는 중</span></div>\`;
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const res = await fetch("/api/assistant/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    // Pass current page title/subject as context
                    context: document.title || 'Math/English Study'
                })
            });

            if (!res.ok) throw new Error("AI 응답 실패");
            const data = await res.json();
            
            // Remove loading and show real response
            document.getElementById(loadingId).remove();
            chatBox.innerHTML += \`<div class="chat-bubble ai">\${data.message}</div>\`;
            chatBox.scrollTop = chatBox.scrollHeight;

            // Play TTS! Using tts-client.js fallback logic
            if (window._speakLocal) {
                // If the app exports _speakLocal from tts-client.js
                window._speakLocal(data.message.replace(/[\u{1F600}-\u{1F6FF}]/gu, '')); // remove emojis for tts
            } else {
                 // Try native speech output directly
                const u = new SpeechSynthesisUtterance(data.message.replace(/[\u{1F600}-\u{1F6FF}]/gu, ''));
                u.lang = /[가-힣]/.test(data.message) ? 'ko-KR' : 'en-US';
                window.speechSynthesis.speak(u);
            }

        } catch (err) {
            console.error(err);
            document.getElementById(loadingId).remove();
            chatBox.innerHTML += \`<div class="chat-bubble ai">앗, 섀도우가 잠깐 조는 것 같아. 다시 시도해볼래?</div>\`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }
});
