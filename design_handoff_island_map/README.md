# Handoff: Gia's Island — Island Map & Companion Screens

## Overview

**Gia's Island** is the gamification layer of NSS Word Master. It's a Tamagotchi-style hub where the learner cares for characters across 5 themed zones (Forest/Ocean/Savanna/Space/Legend). This handoff covers the visual design for **8 screens** that make up the Island feature, with the **Island Map** as the main hub.

The 5 zones map to subjects:
- 🌳 **Forest** — English (Baby Blue)
- 🌊 **Ocean** — Math (Mint)
- 🦁 **Savanna** — Diary (Pink)
- 🚀 **Space** — Review (Lavender)
- ✨ **Legend** — All-subjects unlock (Diary Pink anchor)

## About the Design Files

The files in `design_reference/` are **design references created as an HTML prototype** in a design tool. They are NOT production code to copy directly. They use React + Babel inline JSX with a custom design canvas component to lay out 8 screens side-by-side for review.

**Your task**: recreate these designs in the existing **NSS_Word_Master** codebase, which is a Flask + Jinja2 + vanilla-JS app. The Island feature already has scaffolding in place:

```
frontend/static/css/island-main.css
frontend/static/css/island-screens.css
frontend/static/css/island-zones.css
frontend/static/js/island-result.js
frontend/templates/island/  (templates)
```

You should:
1. Read these existing files first to understand the current scaffolding
2. Implement the new visual design within that scaffolding (extend the CSS, add new templates/JS as needed)
3. Use design tokens from `frontend/static/css/theme.css` — do NOT hard-code colors

## Fidelity

**High-fidelity (hifi).** Final colors, typography, spacing, and component structure are decided. The design canvas in the prototype shows intentional variations (gauge styles, etc.) — these are options to choose from, not all to ship. The README below specifies the chosen direction.

## Critical Asset: `island_map.png`

The Island Map screen uses a single illustrated PNG (`design_reference/img/island_map.png`, 1376×768) as a full-bleed backdrop. **This must be present at the production path** (e.g., `frontend/static/img/island/island_map.png`). The 5 zone hotspots are positioned **on top of the artwork** at exact percentage coordinates calibrated to features in the illustration:

```js
// CALIBRATED — do not change without re-checking against the artwork
const HOTSPOTS = {
  forest:  { left: '17%', top: '42%', size: 150 },  // wooded area + mushrooms (left)
  space:   { left: '47%', top: '22%', size: 110 },  // observatory dome (top center)
  legend:  { left: '50%', top: '50%', size: 130 },  // central crystals
  ocean:   { left: '88%', top: '60%', size: 130 },  // coral reef + seaweed (below lighthouse)
  savanna: { left: '48%', top: '80%', size: 170 },  // grassland (bottom)
};
```

The artwork has zone visuals baked in (a lighthouse for Ocean's coral, an observatory dome for Space, etc.) — keep the image as-is, never add CSS gradients on top that fight with the art.

## Screens

### ① Island Map (main hub)

**Purpose**: Daily landing screen. Learner sees all 5 zones at a glance, sees today's character status, picks a zone to enter.

**Layout**:
- Full-bleed backdrop: `<img src="...island_map.png">` covering 100% × 100%, `object-fit: cover`
- Floating glassy top bar (currency stats + nav icons), `position: absolute; top: 0`
- 5 absolutely-positioned zone hotspots (see HOTSPOTS table above)
- 4 floating character "bubbles" (40px circles, white bg, drop shadow, gentle float animation) near their respective zones
- Bottom-left: streak panel
- Bottom-right: "Today on the Island" summary panel

**Zone hotspot anatomy**:
- Outer ring: `border: 3px solid var(--<zone>-primary)`, circular, `radial-gradient(circle, rgba(255,255,255,.18), transparent 70%)` fill, `box-shadow: 0 6px 20px rgba(0,0,0,.18), inset 0 0 0 6px rgba(255,255,255,.25)`
- Label pill: pinned to bottom of ring (`bottom: -10px; transform: translateX(-50%)`), white bg with 2px colored border, `border-radius: 999px`, `padding: 4px 12px`, Quicksand 800 13px
- Status badges (top-right of ring):
  - `!` red badge (`#D97A7A`, white text) — gauges low / needs care
  - `✨` yellow badge (`#EEC770`, pulsing) — character ready to evolve
- **Locked state** (Legend before progress complete): replace ring fill with frosted glass (`backdrop-filter: blur(3px)`, dashed border), show 🔒 + progress text "1 / 4" inside

**Top bar** (height 56–60px, `background: rgba(255,255,255,.92); backdrop-filter: blur(10px)`):
- Left: 💎 Lumi count, ✨ Legend Lumi count, 🔥 Streak days — each a pill with colored bg
- Right: 🎒 Inventory, 📖 Collection, ⚙️ Settings — round icon buttons

**Streak panel** (bottom-left):
- White rounded box, `padding: 12px 16px`, `border-radius: 14px`
- "STREAK" label + 7 dots, lit dots = `#EEC770` with `#D8AE55` border, last lit dot has 🔥 above

**Today panel** (bottom-right, width 230px):
- White rounded box with backdrop blur
- Title "Today on the Island" (Quicksand 800 14px)
- 3 lines: emoji + character name + status snippet

**Day/Night mode**:
- Day: backdrop image at full saturation, ☀️ in top-right with warm glow
- Night: backdrop `filter: brightness(.5) saturate(.7) hue-rotate(-15deg)`, overlay `radial-gradient` dark scrim, animated stars layer on top, 🌙 with cool glow
- Trigger: time-of-day OR explicit toggle. Spec says auto-switch after 18:00.

**Lumi earned toast**: appears top-center after a study session. White pill with 💎 + amount, slide-down + fade animation.

### ② Zone Detail

**Purpose**: Inside a single zone (e.g., Forest). Active character lives here. Learner feeds, plays, evolves.

**Layout**: Full-screen, zone-tinted bg (`var(--<zone>-light)`), back button top-left, large character art center, gauges + actions below.

**Components**:
- **Character stage**: 320px tall, centered, character emoji/illustration at 120px size with shadow on the floor underneath
- **Gauges** (chosen direction: **bar** — horizontal bars with colored fill, label + percentage):
  - Hunger: `--color-warning` fill
  - Happiness: `--color-primary` fill (pink)
  - 12px height, full rounded corners, animated fill transition (300ms ease)
- **Mood states**: character displays differently — happy (default), hungry (sad emoji + "I'm hungry!" speech bubble + warning border on hunger gauge), sad (low happiness)
- **Action row**: 4 buttons in a row (Feed, Play, Pet, Sleep) — each is a 64px square, rounded, icon + label below

### ③ Character Detail

**Purpose**: View character's full evolution tree, stats, info.

**Layout**: 2-column. Left: large character art (uses real `clover_baby.png`, `clover_mid_a.png`, etc.). Right: stats card + evolution path.

**Evolution tree**: 5 stages visualized as connected nodes:
```
Baby ─→ Mid A ─→ Final A
         └→ Mid B ─→ Final B
```
- Current stage: lit, colored, scaled 1.0
- Past stages: faded but visible
- Future stages: greyscale silhouette
- Branch point: shows `?` until choice is made

### ④ Evolution Branch Modal

**Purpose**: When character is ready to branch, learner picks A or B. **Irreversible**.

**Layout**: Modal overlay (`rgba(43,39,34,.55)` backdrop). Card center, max-width 600px. 2 large preview tiles side-by-side, "Choose carefully — this is permanent" warning at bottom.

**Tile**: each shows the Mid → Final preview illustration of that path, character traits below ("Grass-type · Healing"), CTA "Choose this path" button.

### ⑤ Shop

**Purpose**: Buy evolution stones, food, decor; exchange currencies.

**Layout**: 4 tabs across top (Evolution / Food / Decor / Exchange). Active tab indicator: 3px bottom border in tab color. Grid of cards below — 3 columns, each card 220×280, image + name + price + buy button.

### ⑥ Inventory & Collection

**Inventory tab**: Grid of owned items with counts. 4-column grid, 90px square cells, item icon + count badge.

**Collection (도감)**: Grid of all 30 characters, sorted by zone. Owned characters shown in full color; unowned greyscale silhouette with `?`. 5×6 grid. Tapping a character opens a detail card.

### ⑦ Onboarding

**4 steps**, full-screen, one at a time:
1. **Greet** — Lumi (👽 placeholder; will be illustration) waves, speech bubble "Hi! I'm Lumi. Let's pick your first friend!"
2. **Zone select** — 4 unlocked zones in a 2×2 grid (Legend locked). Tap to select.
3. **Friend select** — Show 5 baby characters of chosen zone. Tap to pick.
4. **Name** — Name input (default = species name), confirm button.

Progress dots at bottom (4 total).

### ⑧ Character Complete (celebration modal)

**Purpose**: When learner reaches Final A or Final B, show full-screen celebration.

**Layout**: Full-screen, dark backdrop with confetti/sparkle particles. Center: character illustration at 200px, scaled-up, with light rays emanating. Below: "Clover is now Final A! 🎉" + Lumi reward + "Continue" button. Auto-dismiss option.

## Interactions & Behavior

| Action | Trigger | Result |
|---|---|---|
| Tap zone hotspot | Click on hotspot | Navigate to Zone Detail |
| Tap locked zone | Click on Legend (when locked) | Toast: "Complete all 4 zones to unlock Legend" |
| Tap character bubble on map | Click | Pulse animation + tooltip with character name + status |
| Hunger drops below 30% | Time-based decay (server-side or local) | Show ❗ badge on zone hotspot, character mood = "hungry" |
| Character ready to evolve | All criteria met | Show ✨ pulsing badge on hotspot |
| Earn Lumi | Finish study session | Slide-in toast top-center, +N Lumi |
| 18:00 transition | Wall clock | Smooth 400ms fade to night theme |
| Streak hits multiple of 5 | Login | Highlight 🔥 with bigger pulse |

## State Management

The Island feature needs the following state (server-side persistence):

```typescript
type IslandState = {
  zones: {
    [zoneId in 'forest'|'ocean'|'savanna'|'space'|'legend']: {
      unlocked: boolean;
      activeCharacterId: string | null;
      progressTowardsLegend: number;  // 0-4
    }
  };
  characters: {
    [characterId: string]: {
      species: string;             // e.g. 'clover'
      stage: 'baby'|'mid_a'|'mid_b'|'final_a'|'final_b';
      hunger: number;              // 0-100
      happiness: number;           // 0-100
      lastFed: timestamp;
      lastPlayed: timestamp;
      branchChoice: 'A'|'B'|null;
      customName: string;
    }
  };
  inventory: { [itemId: string]: number };
  collection: { [characterId: string]: { caught: boolean; finalStage?: 'A'|'B' } };
  currencies: { lumi: number; legendLumi: number };
  streak: number;
  lastLogin: timestamp;
};
```

Hunger/happiness decay should run server-side (cron or on next page load) so it persists across sessions.

## Design Tokens

All tokens already exist in `frontend/static/css/theme.css` — **use these, do not hard-code**:

```css
/* Zone colors */
--english-primary: #7FA8CC;   /* Forest */
--math-primary:    #8AC4A8;   /* Ocean */
--diary-primary:   #E09AAE;   /* Savanna */
--rewards-primary: #B8A4DC;   /* Space */
--review-primary:  #EBA98C;   /* Legend uses Diary Pink anchor */

/* Currency */
--xp-color, --xp-bg               /* Lumi */
--color-secondary (Arcade Butter) /* Lumi accent */

/* Surfaces */
--bg-page: #FAF6EF              /* warm cream */
--bg-card: #FFFFFF
--shadow-soft: 0 2px 10px rgba(120,90,60,.06)

/* Type */
--font-family-display: 'Quicksand'   /* zone labels, headings */
--font-family:         'Nunito'      /* body */
--font-family-hand:    'Caveat'      /* speech bubbles, friendly accents */

/* Radii */
--radius-md: 12px;
--radius-lg: 16px;
--radius-full: 9999px;
```

## Assets

Located in `design_reference/img/`:
- `island_map.png` (1376×768) — **REQUIRED**, full-bleed Island Map backdrop
- `clover_baby.png`, `clover_mid_a.png`, `clover_mid_b.png`, `clover_final_a.png`, `clover_final_b.png` — Clover (Forest) evolution illustrations
- `zone_forest.png`, `zone_ocean.png`, `zone_savanna.png`, `zone_space.png`, `zone_legend.png` — zone backdrops for Zone Detail screen

The remaining 29 characters do not have illustrations yet. Use emoji placeholders in code, structured so swapping in PNGs later is one line:

```js
const CHARS = {
  clover: { name: 'Clover', img: '/static/img/island/clover_baby.png', emoji: '🍀' },
  axie:   { name: 'Axie',   img: null, emoji: '🐠' },  // emoji until art ships
  // ...
};
// in component:
char.img ? <img src={char.img} /> : <span>{char.emoji}</span>
```

## Files in This Bundle

```
design_handoff_island_map/
├── README.md                          ← this file
└── design_reference/
    ├── Gia's Island.html              ← entry point, all 8 screens
    ├── screens-map.jsx                ← Island Map (most relevant)
    ├── screens-detail.jsx             ← Zone Detail, Character Detail, Evolution, Onboarding, Complete
    ├── screens-shop.jsx               ← Shop, Inventory, Collection
    ├── design-canvas.jsx              ← layout shell (NOT production — for review only)
    ├── tweaks-panel.jsx               ← live-preview toggles (NOT production)
    ├── styles.css                     ← shared styles for the prototype
    └── img/                           ← all illustrations
```

To preview: open `Gia's Island.html` in a browser (no build step).

## Implementation Notes for Claude Code

1. **Don't ship the prototype HTML.** It uses Babel-in-browser, React UMD, and a custom design canvas — none of that belongs in production.
2. **Read existing Island scaffolding first**: `frontend/static/css/island-*.css`, `frontend/static/js/island-*.js`, `frontend/templates/island/`. Match patterns there.
3. **Hotspot positioning** is percentage-based on a fixed-aspect-ratio container. The container's aspect ratio MUST match the artwork (1376:768 ≈ 16:9). Wrap with `aspect-ratio: 1376/768` and let it scale to the viewport with `max-width: 100%`.
4. **The map should be the route `/island/`** in the Flask app. Each zone hotspot links to `/island/<zone>/`.
5. **Mobile first?** Confirm with PM. Current design assumes desktop/tablet (the Island UX is rich; phone will need rework).
6. **Accessibility**: hotspots must be `<button>` elements with `aria-label="Enter Forest zone"`, keyboard-focusable, with visible focus rings.
