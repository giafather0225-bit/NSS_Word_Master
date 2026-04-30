export const ANIMATIONS = {
  // Character states
  idle:    { duration: 3000, distance: 4 },
  happy:   { scale: 1.05, duration: 600 },
  sad:     { rotation: 3, opacity: 0.8 },
  feed:    { bounceHeight: 8, duration: 400 },
  levelUp: { glowDuration: 800, glowColor: '#FFD700', textRise: 20 },

  // Evolution
  evolve1: { fadeOut: 600, fadeIn: 800, glowOpacity: 0.4 },
  evolve2: { fadeOut: 800, fadeIn: 1200, glowOpacity: 0.7, bloomSize: 120 },

  // Character complete celebration
  complete: {
    particleDuration: 2000,
    textFadeIn: 600,
    bloomOpacity: 0.6,
  },

  // Legend unlock
  legendUnlock: {
    darkOverlay: 400,
    goldSpreadDuration: 1200,
    islandReveal: 800,
    textFadeIn: 600,
  },

  // Screen transitions
  mapToZone:     { zoomDuration: 400 },
  zoneToMap:     { zoomDuration: 400 },
  zoneToChar:    { slideDuration: 300 },
  charToZone:    { slideDuration: 300 },
};
