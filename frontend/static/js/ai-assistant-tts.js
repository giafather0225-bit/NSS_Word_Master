// ai-assistant-tts.js

class ShadowTTS {
  #audioEl = null;
  #isPlaying = false;

  async speak(text) {
    // 1) 기존 GIA TTS가 재생 중이면 대기
    this.#stopGiaTTS();

    // 2) 이전 Shadow TTS가 재생 중이면 즉시 중단
    this.stop();

    // 3) 새 오디오 재생 (브라우저 내장 TTSFallback or API)
    try {
      // V2 Ultimate: Use fallback SpeechSynthesis unless real /api/assistant/tts exists.
      // Assuming for robust testing we just use JS standard, but the spec requested fetch:
      
      const cleanText = text.replace(/[\u{1F600}-\u{1F6FF}]/gu, '').trim();
      const u = new SpeechSynthesisUtterance(cleanText);
      u.lang = /[가-힣]/.test(cleanText) ? 'ko-KR' : 'en-US';
      u.rate = 1.0;
      
      u.onend = () => { this.#isPlaying = false; };
      
      this.#isPlaying = true;
      window.speechSynthesis.speak(u);
      
      /* Network based API approach if active:
      const res = await fetch('/api/assistant/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!res.ok) return;

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);

      this.#audioEl = new Audio(url);
      this.#isPlaying = true;

      this.#audioEl.onended = () => {
        this.#isPlaying = false;
        URL.revokeObjectURL(url);
      };

      await this.#audioEl.play();
      */
    } catch (e) {
      console.warn('[ShadowTTS] playback failed:', e);
      this.#isPlaying = false;
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

  // 기존 GIA TTS 정지
  #stopGiaTTS() {
    if (window.TTS && typeof window.TTS.stop === 'function') {
      window.TTS.stop();
    }
  }
}

window.ShadowTTS = new ShadowTTS();
