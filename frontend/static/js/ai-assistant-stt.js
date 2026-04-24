if (typeof window.ShadowSTT === 'undefined') { if (typeof window.ShadowSTT === 'undefined') {
if (typeof ShadowSTT === 'undefined') {
/* ai-assistant-stt.js — Speech Recognition (Shadow STT) */

class {
    constructor(onResult, onError, onEnd) {
        this.onResult = onResult;
        this.onError = onError;
        this.onEnd = onEnd;
        this.recognition = null;
        this.isRecording = false;

        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
            this.recognition = new SpeechRec();
            this.recognition.lang = 'en-US';
            this.recognition.continuous = false;
            this.recognition.interimResults = false;

            this.recognition.onresult = (e) => {
                const text = e.results[0][0].transcript;
                if (this.onResult) this.onResult(text);
            };

            this.recognition.onerror = (e) => {
                if (this.onError) this.onError(e.error);
                this.isRecording = false;
            };

            this.recognition.onend = () => {
                this.isRecording = false;
                if (this.onEnd) this.onEnd();
            };
        }
    }

    async startListening() {
        if (!this.recognition) {
            this.fallbackToText();
            return false;
        }

        try {
            // Check permissions explicitly for iOS Safari PWA
            if (navigator.permissions && navigator.permissions.query) {
                const status = await navigator.permissions.query({ name: 'microphone' }).catch(() => null);
                if (status && status.state === 'denied') {
                    if (this.onError) this.onError("not-allowed");
                    return false;
                }
            }

            this.isRecording = true;
            this.recognition.start();
            return true;
        } catch (err) {
            this.isRecording = false;
            if (this.onError) this.onError("not-allowed");
            return false;
        }
    }

    stopListening() {
        if (this.isRecording && this.recognition) {
            this.recognition.stop();
            this.isRecording = false;
        }
    }

    fallbackToText() {
        if (this.onError) this.onError("not-supported");
    }
}

window.ShadowSTT = ShadowSTT;
}
} }
