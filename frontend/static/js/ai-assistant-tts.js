// ai-assistant-tts.js

class ShadowTTS {
  #audioEl = null;
  #isPlaying = false;

  async speak(text) {
    // 1) stop any active GIA TTS first
    this.#stopGiaTTS();

    // 2) stop any previous Shadow TTS immediately
    this.stop();

    // 3) play via edge-tts backend (Jenny Neural), fallback to browser SpeechSynthesis
    try {
      const cleanText = text.replace(/[\u{1F600}-\u{1F6FF}]/gu, '').trim();
      if (!cleanText) return;

      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: cleanText })
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        this.#audioEl = new Audio(url);
        this.#isPlaying = true;
        this.#audioEl.onended = () => {
          this.#isPlaying = false;
          URL.revokeObjectURL(url);
        };
        await this.#audioEl.play();
      } else {
        throw new Error('TTS API failed');
      }
    } catch (e) {
      console.warn('[ShadowTTS] edge-tts failed, using browser fallback:', e);
      try {
        const cleanText = text.replace(/[\u{1F600}-\u{1F6FF}]/gu, '').trim();
        const u = new SpeechSynthesisUtterance(cleanText);
        u.lang = 'en-US';
        u.rate = 0.95;
        u.onend = () => { this.#isPlaying = false; };
        this.#isPlaying = true;
        window.speechSynthesis.speak(u);
      } catch {
        this.#isPlaying = false;
      }
    }
  }

  stop() {
    if (this.#audioEl) {
      this.#audioEl.pause();
      this.#audioEl.currentTime = 0;
      this.#audioEl = null;
    }
    if (window.speechSynthesis?.speaking) {
      window.speechSynthesis.cancel();
    }
    this.#isPlaying = false;
  }

  get isPlaying() {
    return this.#isPlaying;
  }

  // stop GIA TTS
  #stopGiaTTS() {
    if (window.TTS && typeof window.TTS.stop === 'function') {
      window.TTS.stop();
    }
  }
}

window.ShadowTTS = new ShadowTTS();
