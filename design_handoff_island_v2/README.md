# Handoff: Gia's Island — Phase 2 Screens (Game Loop + System)

## What's in this package

This is a **follow-up** to the original `design_handoff_island_map` handoff. It covers **8 NEW screens** added after the initial 8 (Map / Zone / Character / Evolution / Shop / Inventory / Onboarding / Complete). The earlier 8 are NOT in this package — see the original handoff for those.

### The 8 new screens (numbered ⑨–⑯)

| # | Screen | Purpose |
|---|---|---|
| ⑨ | Feed Interaction | Pick a treat → drag to character → gauges fill. Core daily action. |
| ⑩ | Sleep / Rest | Night cycle. Energy regenerates while away. |
| ⑪ | Farewell → Dex | Lifecycle close. Goodbye letter, character permanently added to dokgam. |
| ⑫ | Empty States | First-visit / nothing-yet states for zone, inventory, dokgam, friends. |
| ⑬ | Daily / Missions | Streak banner + attendance calendar + daily & weekly missions. |
| ⑭ | Mailbox | Lumi messages, friend gifts, event news. List + detail pane. |
| ⑮ | Settings | Account / sound / notifications / language / support / about. |
| ⑯ | Purchase Confirm | Buy / success / insufficient-balance modals. |

## 🚀 Quick Start: Where to Unzip

Same setup as the first handoff — drop this folder INSIDE your `NSS_Word_Master` repo root:

```bash
cd ~/path/to/NSS_Word_Master
unzip ~/Downloads/design_handoff_island_v2.zip
ls    # should now show: design_handoff_island_v2/
```

Then prompt Claude Code:

> Read `design_handoff_island_v2/README.md` and implement the Phase 2 Gia's Island screens in our Flask + Jinja2 codebase. Reuse the design tokens and patterns established in the previous handoff (`design_handoff_island_map/`) and in `frontend/static/css/island-*.css`. Start with **⑨ Feed Interaction** since it completes the core daily loop.

## About the Design Files

The files in `design_reference/` are **design references created as an HTML prototype** using React + Babel inline JSX. They are NOT production code — recreate the designs in the existing **NSS_Word_Master** Flask + Jinja2 + vanilla-JS codebase, reusing patterns from the previous handoff.

**Only these 3 .jsx files contain Phase 2 screens** — the rest are shared infrastructure already covered in the first handoff:

- `screens-loop.jsx` — ⑨ Feed, ⑩ Sleep, ⑪ Farewell, ⑫ Empty states
- `screens-meta.jsx` — ⑬ Daily, ⑭ Mailbox
- `screens-system.jsx` — ⑮ Settings, ⑯ Purchase modal

## Fidelity

**High-fidelity (hifi).** Final colors, typography, spacing, and component structure are decided. Variations shown in the canvas (e.g. multiple feed stages, multiple settings sections) are sequential states or nav targets, not options to choose from.

## Design Tokens (reminder)

All tokens already exist in `frontend/static/css/theme.css`. Key ones used heavily in this phase:

```css
/* Currency colors */
--diary-primary:   #E09AAE   /* primary CTA, "claim" buttons */
--rewards-primary: #B8A4DC   /* Lumi (✨) accents, Lumi messages in mailbox */
--arcade-primary:  #EEC770   /* gem (💎) accents, streak fire, gifts */
--math-primary:    #8AC4A8   /* success state, completed missions */

/* Surfaces */
--bg-page:    #FAF6EF
--bg-card:    #FFFFFF
--bg-surface: #EFE8DB        /* gauge tracks, secondary chips */

/* Type */
--font-display: 'Quicksand'  /* headings, gauge labels, numbers */
--font-body:    'Nunito'     /* default body */
--font-hand:    'Caveat'     /* paper/diary copy, friendly accents — used heavily in farewell letter */

/* Radii */
--r-md: 12px;  --r-lg: 16px;  --r-2xl: 28px;
```

---

## ⑨ Feed Interaction

**Route**: `/island/<zone>/feed`

**3 states** (single page, transitions between them):
1. **select** — food tray visible at bottom, Lumi tip "Pick a treat & drag it to Clover ✨" in a paper card
2. **drag** — selected food item appears mid-air with a dashed arrow pointing to character
3. **result** — `+150 XP` toast appears, hearts/sparkles around character, gauges refill animated

**Layout**:
- Full-screen, zone-tinted bg (`zone-forest` etc., depends on which zone the active character is in)
- Top bar: back button, "Feed Clover" title, gem balance
- Mini gauge HUD (Hunger + Friendship) pinned top-left/right with `backdrop-filter: blur(4px)` over the bg
- Character stage center, with a soft elliptical floor shadow (`background: rgba(58,106,84,.18); border-radius: 50%; filter: blur(6px)`) + `float` animation on the character image
- Food tray bottom (white card, top border, 3-column grid): each food shows emoji 30px + name + "+N XP". Selected card has 2px diary border + diary-light bg.

**Interaction**:
- Tap food → highlights it in tray
- Drag from tray onto character → triggers `result` state
- After result: 1.2s celebration, then return to `select` with updated gauge values

**Animations**:
- Character `float`: 3s ease-in-out infinite (`translateY(-4px)` at midpoint)
- Result hearts: 3 emoji floating up with staggered 0.2s delay
- Gauge fill: 600ms ease-out

## ⑩ Sleep / Rest

**Route**: `/island/<zone>/sleep` (or auto-redirected from zone after 22:00 local)

**2 states**:
1. **sleeping** — character on bed, rotated -12° + brightness .85, animated z's floating up
2. **wake** — character upright, "Good morning!" message, energy bar full

**Layout**:
- Full-screen `night` mode (forced — even if app theme is day): `linear-gradient(180deg, #1A1827 0%, #2A2147 60%, #1A1B3A 100%)` + animated stars layer (the `.stars` class from styles.css)
- Moon top-right (64px, `radial-gradient(circle at 35% 35%, #FFF6D9, #F2E2A8)` + soft glow)
- Centered: bed (240×80 ellipse, `linear-gradient(180deg, #3A3750, #2E2C42)`) with character resting on top
- Energy bar: 300px wide pill, glassy bg, "Wakes in 4h 12m · or tap to wake early" hint
- CTA button: "🔔 Wake gently" (sleeping) / "☀️ Start the day" (wake — primary diary color)

**Behavior**:
- Energy regenerates at ~10%/hour while sleeping (server-side timestamp diff on next page load)
- Tapping "Wake gently" early forfeits 50% of remaining energy gain
- After hitting 100% energy, screen auto-transitions to `wake` state

## ⑪ Farewell → Dex

**Route**: `/island/<zone>/farewell` (triggered when character reaches Final A or B + 14 days raised)

**2 sequential states** (NOT side-by-side — second replaces first):

### State 1: `goodbye` (the letter)
- Soft pastel bg: `linear-gradient(180deg, #FBEEF2 0%, #F2ECFA 50%, #EEF4FA 100%)`
- 12 floating petal emojis (🌸) scattered absolutely with staggered float animations
- 2-column: left = character (Final A illustration, 200px, floating), right = letter card
- **Letter card** uses `.paper` class (lined diary paper), rotated `-1.2deg`, in Caveat handwriting font:
  > Dear Gia, Thank you for raising me. I'll fly to the legendary forest now — but I'll always be in your dokgam ✨ — Clover 🍀
- Top-right corner of letter: tiny "raised 14 days" stamp
- Bottom: "Save letter" + "Say goodbye →" (primary)

### State 2: `dex` (added to collection)
- Same bg, letter replaced with celebration card
- "Added to Collection" eyebrow → "Clover · Forest 04/12" h1
- Center: dex card (160×200) with character + "NEW" badge, surrounded by golden radial glow
- Reward strip: `+1 ✨ Lumi`, `+50 💎`, `Dex 4/12`
- CTAs: "📖 View dokgam" / "🌱 Raise next" (primary)

**Critical**: this is a once-per-character, irreversible flow. The character record moves from `state:'active'` to `state:'completed'` and gets archived to the dokgam.

## ⑫ Empty States

**4 variants** — same shell, different copy/icon. All use:
- 140px dotted-border circle with floating icon (64px)
- Title (h1, 24px) + subtitle (14px secondary) + Caveat hand-line (20px rewards-ink)
- Primary CTA button

| Variant | Route | Icon | Title | Hand line | CTA |
|---|---|---|---|---|---|
| `zone` | empty zone screen | 🌱 | "No friend here yet" | "Every legend starts with one little seed ✨" | "🛍️ Open shop" |
| `inv` | empty inventory | 🧺 | "Your basket is empty" | "It's quiet in here…" | "🛍️ Browse shop" |
| `dex` | empty dokgam | 📖 | "No memories yet" | "The first page is always the sweetest" | "🌱 Start raising" |
| `friends` | no friends added | 🏝️ | "No island visits yet" | "Better with company" | "＋ Add a friend" |

**Decorative add-ons** (subtle, opacity .35–.4):
- `dex` variant adds a 6×2 grid of silhouette dex cards below the CTA
- `inv` variant adds a 4×2 grid of dashed empty squares below the CTA

## ⑬ Daily / Missions

**Route**: `/island/daily`

**3 tabs**: Attendance / Missions / Weekly. All share a **streak banner** at top:
- Gradient bg (`arcade-light → diary-light`), 🔥 emoji 34px, "4-day streak" h2 in arcade-ink, "Come back tomorrow for ✨ 1 Lumi" sub, Caveat tagline "nice rhythm!" on right.

### Attendance tab
- 7-day grid (M T W T F S S), each cell 1.5px border:
  - Claimed days: `math-light` bg, `✓` glyph
  - Today: `diary-light` bg + diary border + pulse animation + "TODAY" pill above
  - Future: white bg, day number
- Each cell shows day reward at bottom (`💎10 / 💎10 / 💎15 / 💎15 / 💎20 / ✨1 / 💎50`)
- Big "Claim Day 4 · 💎 15" CTA below grid (primary, full width, 48px tall)
- Day-7 mega reward callout (rewards-light bg, 🎁 + "3 days to go · 💎 50 + Lumi chest")

### Missions tab (daily)
- "Today" header + "Resets in 6h 23m" countdown
- Vertical list of mission cards. Each card:
  - 40px circle (math green if done, surface if not) with check or icon
  - Title + 6px gauge bar with progress + "n/N" count
  - Right side: pill button "💎 N" if claimable, or `chip-locked` 🔒 if gated
- Done missions get strikethrough + math-light bg

Default mission set:
| ico | title | reward |
|---|---|---|
| 🍖 | Feed Clover | 💎 10 |
| 💕 | Play 3 times | 💎 15 |
| 🌱 | Visit every zone | 💎 20 |
| 🛍️ | Buy something at shop | ✨ 1 |
| 🏝️ | Visit a friend's island (locked) | 💎 30 |

### Weekly tab
- Larger cards (52×52 icon tiles in `rewards-light`)
- 8px tall progress bar with `linear-gradient(90deg,#B8A4DC,#E09AAE)` fill
- Bottom: paper card with Caveat "You're 2 missions away from a Lumi 💕"

## ⑭ Mailbox

**Route**: `/island/mail`

**Layout**: Master/detail. Left list (260px when detail open, full-width otherwise), right detail pane.

**Top bar**: title + "3 new" pill chip (diary bg, white text), `⋯` overflow

**Filter row**: pill buttons `All (6) / 🌙 Lumi (3) / 🎁 Gifts (2) / 🌸 Events (1)`. Active pill has diary border + diary-light bg.

**List item**:
- 38px circle avatar — bg color depends on type: `rewards-light` for Lumi, `arcade-light` for gifts, `diary-light` for events
- From + time (relative)
- Preview text (2 lines max, ellipsis), bolder when unread
- Unread indicator: 6px diary-color dot at left edge
- Gift attachment: 18px emoji on right side

**Detail pane** (when message opened):
- 52px avatar + name h2 + "Xm ago" sub
- Body in `.paper` card, written in Caveat font with greeting/sign-off:
  > Hi Gia, [body] — Lumi 🌙
- If gift attached: arcade-light callout with item, "Claim" CTA (secondary/arcade button)
- Bottom actions: "→ Go to Forest" (contextual deep link) + "Mark read" (ghost)

**Default seed messages** (use these for demo data):
1. Lumi · "Clover misses you! Come feed them ✨" · 2m · unread
2. Mina · "sent you a Mushroom Lantern 🍄" · 1h · unread, gift
3. Lumi · "Your weekly Lumi is ready to claim" · 3h · unread, gift ✨
4. Spring Event · "New decor in shop until Sunday" · 1d
5. Joon · "sent you 💎 20" · 2d, gift
6. Lumi · "Welcome to Gia's Island!" · 5d (welcome message)

## ⑮ Settings

**Route**: `/island/settings`

**Layout**: Two-pane. Left = 200px side-nav, right = panel.

**Side nav items** (icon + label, active = diary-light bg + diary-ink text):
- 👤 Account · 🔊 Sound · 🔔 Notifications · 🌐 Language · 💬 Support · ℹ️ About

### Account panel
- Profile header (white card): 64px avatar (diary→rewards gradient with 🌿 emoji) + name "Gia" + Island ID + Caveat "since 12 days ago" + Edit button
- Rows: Email · Linked accounts · Invite code · Cloud save (with `● ON` indicator)
- Spacer + danger rows: Sign out · Delete account (red)

### Sound panel
- Music (with volume slider sub-row) · Sound effects · Character voices · Ambient sounds · Haptics — all toggle rows
- Volume slider: 4px track, diary fill, white thumb with diary border

### Notifications panel
- Top callout (rewards-light): "🌙 Lumi will only send what you turn on below."
- Toggles: Hunger reminders · Evolution ready · Daily streak (9pm) · Friend gifts · Events & news
- Quiet hours row (chevron, opens range picker): "22:00 – 08:00"

### Language panel
- 5 options: 한국어 / English / 日本語 / 中文 / Español
- Selected has `✓` in diary color on the right

### Support panel
- Help center · Contact us · Report a bug · Rate the app — all chevron rows

### About panel
- Version · ToS · Privacy policy · Open-source licenses · Credits
- Bottom paper card with Caveat "made with care 💕" + "© 2026 Gia's Island"

**Toggle component spec**:
- 42×24 pill, diary fill when on, surface when off
- 20px white circle thumb, slides 18px on toggle, 200ms ease

## ⑯ Purchase Confirm

**Modal pattern, NOT a route.** Shown over the shop with a `rgba(43,39,34,.5)` scrim.

**3 states**:

### confirm
- 96px circle bg (arcade-light for gems, rewards-light for Lumi) with item emoji floating
- Item name h1 + 13px description
- **Price breakdown** in surface-bg rounded box:
  - Price: `💎 30`
  - Balance: `💎 240`
  - ─── divider ───
  - After purchase: `💎 210`
- 2-button row: Cancel (1fr) + Buy 💎 30 (2fr, primary)
- Hint: "You can disable purchase confirmations in Settings"

### success
- 96px math-light circle with item + green ✓ checkmark badge top-right
- "Got it!" h1 + Caveat "{item name} added to your basket ✨"
- 2-button row: "Keep shopping" + "Use now →" (primary)

### insufficient
- 96px `#FFE5E5` circle with item (no animation)
- "Not enough gems" h1 + "You need 💎 N more to buy {name}"
- Current balance row
- **Earn-more options** (2 sub-cards):
  - 💱 Exchange Lumi (arcade-light) — `1 ✨ → 💎 50`
  - 🎯 Complete missions (diary-light) — `Earn up to 💎 60 today`
- Single full-width "Maybe later" button

**Important**: support a "skip confirm for low-cost items" preference (settable in Settings → Account or as a checkbox in the modal). Lumi (✨) purchases should ALWAYS confirm regardless — they're rare resources.

---

## Interactions & Behavior Summary

| Trigger | Result |
|---|---|
| Hunger drops below 30% | Push Lumi mailbox message; show ❗ on map |
| Tap food in tray | Select highlight |
| Drag food onto character | Feed action; gauges refill; +XP toast |
| 22:00 local time, character in zone | Auto-redirect to Sleep state on next visit |
| Character reaches Final stage + 14d raised | Trigger Farewell flow (one-time, irreversible) |
| Empty zone visited | Show Empty State with shop CTA |
| Daily mission completed | Pulse claim button; tap to claim → +reward toast |
| Streak hits 7 | Day-7 mega reward callout becomes claimable |
| New mailbox message arrives | Red dot on Mailbox icon in topbar |
| Tap shop item | Open Purchase Confirm modal |
| Insufficient balance | Switch modal to insufficient variant; offer earn paths |

## State Additions (extends Phase 1 schema)

```typescript
type IslandStateV2 = IslandState & {
  // ⑨ feeding history (for cooldowns + analytics)
  feedHistory: { [characterId: string]: { lastFed: timestamp; count: number } };

  // ⑩ sleep / energy
  energy: { [characterId: string]: { value: number; lastTickAt: timestamp } };

  // ⑬ daily / missions
  daily: {
    streak: number;
    lastClaimedDay: number;        // 1–7 within current week
    weekStart: timestamp;
    todayMissions: Mission[];
    weeklyMissions: Mission[];
  };

  // ⑭ mailbox
  mail: {
    messages: Message[];           // see seed list above
    lastReadAt: timestamp;
  };

  // ⑮ settings
  settings: {
    sound: { music: boolean; sfx: boolean; voices: boolean; ambient: boolean; haptics: boolean; musicVol: number };
    notify: { hunger: boolean; evolution: boolean; streak: boolean; gifts: boolean; events: boolean; quietHours: [string, string] };
    language: 'ko'|'en'|'ja'|'zh'|'es';
    confirmPurchases: boolean;
  };
};

type Mission = {
  id: string;
  icon: string;       // emoji
  title: string;
  progress: number;
  total: number;
  reward: { kind: 'gem'|'lumi'; amount: number };
  done: boolean;
  locked?: boolean;
};

type Message = {
  id: string;
  type: 'lumi'|'gift'|'event';
  from: string;
  preview: string;
  body: string;       // long form, shown in detail pane
  sentAt: timestamp;
  unread: boolean;
  gift?: { kind: 'item'|'gem'|'lumi'; id?: string; amount?: number; emoji: string };
  deepLink?: string;  // e.g. '/island/forest' for "Go to Forest" CTA
};
```

## Files in This Bundle

```
design_handoff_island_v2/
├── README.md                         ← this file
└── design_reference/
    ├── Gia's Island.html             ← entry point, all 16 screens (Phase 1 + 2)
    ├── screens-loop.jsx              ← ⑨ Feed, ⑩ Sleep, ⑪ Farewell, ⑫ Empty (NEW)
    ├── screens-meta.jsx              ← ⑬ Daily, ⑭ Mailbox (NEW)
    ├── screens-system.jsx            ← ⑮ Settings, ⑯ Purchase modal (NEW)
    ├── styles.css                    ← shared styles (same as Phase 1)
    ├── screens-map.jsx               ← Phase 1 reference (don't reimplement)
    ├── screens-detail.jsx            ← Phase 1 reference
    ├── screens-shop.jsx              ← Phase 1 reference (the modal in ⑯ replaces direct buys)
    ├── design-canvas.jsx             ← prototype shell (NOT production)
    ├── tweaks-panel.jsx              ← prototype tweaks (NOT production)
    └── img/                          ← clover_baby/mid_a/final_a only (used in Phase 2 screens)
```

To preview: open `Gia's Island.html` in a browser. The new sections are ⑨–⑯ at the bottom of the canvas.

## Implementation Notes for Claude Code

1. **Reuse Phase 1 patterns.** Top bar, gauge bars, paper cards, chip styles, tab styles — all already exist in `frontend/static/css/island-*.css`. Don't fork them.
2. **Caveat handwriting font** (`var(--font-hand)`) is the emotional anchor of this phase. Use it everywhere a "human" voice speaks: Lumi messages, farewell letter, empty-state taglines, success modals. Never use it for UI labels or numbers.
3. **The Mailbox detail pane is master/detail desktop pattern**. On mobile it should become a stack (list pushes off-screen left, detail slides in from right).
4. **Purchase modal is a modal, not a page.** It overlays whatever screen the user was on (usually Shop). Closing returns to that screen, not back-stack.
5. **Settings toggle persistence**: each toggle should save on flip (no Save button), with a brief confirmation toast.
6. **Empty states** should ship for EVERY list/grid in the app, not just the four shown. The 4 here are templates — copy the pattern for any new empty list.
7. **Accessibility**:
   - Drag-to-feed must have a tap-to-feed fallback (tap food → tap character)
   - All toggles need `role="switch"` + `aria-checked`
   - Mailbox unread state must be conveyed by more than just bold weight (the dot indicator is good)
   - Modal needs focus trap + Esc to dismiss
