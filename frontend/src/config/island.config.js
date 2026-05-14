export const ISLAND_CONFIG = {
  zones: {
    forest:  { label: 'Forest',  lucideIcon: 'tree-pine',  subject: 'english' },
    ocean:   { label: 'Ocean',   lucideIcon: 'waves',      subject: 'math' },
    savanna: { label: 'Savanna', lucideIcon: 'paw-print',  subject: 'diary' },
    space:   { label: 'Space',   lucideIcon: 'rocket',     subject: 'review' },
    legend:  { label: 'Legend',  lucideIcon: 'sparkles',   subject: 'all' },
  },
  ui: {
    lockScreen: {
      text: "Complete 1st evolution on 1 character in all 4 zones",
      fogOpacity: 0.85,
    },
    nameMaxLength: 8,
    gaugeWarningThreshold: 20,
    gaugeDecayThreshold: 60,
  },
  errors: {
    loadFail: "Connection failed. Try again?",
    purchaseFail: "Purchase failed. Please try again.",
    evolveFail: "Evolution failed. Stone was not used.",
    offline: "You're offline",
    retryMax: 3,
  },
};
