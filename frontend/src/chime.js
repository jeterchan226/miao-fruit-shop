// WebAudio 提示音；需在使用者手勢中先呼叫 unlock()。無外部音檔。
export function createChime() {
  let ctx = null;

  function ensureCtx() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
    }
    return ctx;
  }

  return {
    unlock() {
      const c = ensureCtx();
      if (c && c.state === 'suspended') c.resume();
    },
    play() {
      const c = ensureCtx();
      if (!c) return;
      if (c.state === 'suspended') c.resume();
      try {
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, c.currentTime);
        gain.gain.setValueAtTime(0.001, c.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.3, c.currentTime + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.35);
        osc.connect(gain).connect(c.destination);
        osc.start();
        osc.stop(c.currentTime + 0.36);
      } catch {
        /* 忽略播放失敗 */
      }
    },
  };
}
