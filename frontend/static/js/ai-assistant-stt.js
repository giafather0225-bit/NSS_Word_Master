/* ================================================================
   ai-assistant-stt.js — Speech Recognition (Shadow STT)
   Section: AI Assistant
   Exports: window.ShadowSTT (class)
     new ShadowSTT(onResult, onError, onEnd)
       .startListening()  → Promise<boolean>
       .stopListening()
       .isRecording
   ================================================================ */

(function () {
    if (typeof window.ShadowSTT !== "undefined") return;

    class ShadowSTT {
        constructor(onResult, onError, onEnd) {
            this.onResult = onResult;
            this.onError  = onError;
            this.onEnd    = onEnd;
            this.recognition = null;
            this.isRecording = false;

            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRec) return;

            const r = new SpeechRec();
            r.lang = "en-US";
            r.continuous = false;
            r.interimResults = false;

            r.onresult = (e) => {
                const text = e.results[0][0].transcript;
                if (this.onResult) this.onResult(text);
            };
            r.onerror = (e) => {
                this.isRecording = false;
                if (this.onError) this.onError(e.error);
            };
            r.onend = () => {
                this.isRecording = false;
                if (this.onEnd) this.onEnd();
            };
            this.recognition = r;
        }

        async startListening() {
            if (!this.recognition) {
                if (this.onError) this.onError("not-supported");
                return false;
            }
            // iOS Safari PWA: explicit permission probe to surface a clear error.
            try {
                if (navigator.permissions && navigator.permissions.query) {
                    const status = await navigator.permissions
                        .query({ name: "microphone" })
                        .catch(() => null);
                    if (status && status.state === "denied") {
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
                try { this.recognition.stop(); } catch (_) {}
                this.isRecording = false;
            }
        }
    }

    window.ShadowSTT = ShadowSTT;
})();
