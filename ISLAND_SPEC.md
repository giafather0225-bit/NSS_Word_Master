# ISLAND_SPEC.md — Gia's Island System Complete Specification
> Version 1.0 | Last Updated: 2025-04-29
> Language: English only (UI, all text, notifications)

---

## 1. OVERVIEW

Gia's Island is a Tamagotchi + island-building + Pokémon collection hybrid system integrated into the NSS Word Master app. It replaces the legacy Growth Theme system entirely.

**Three Core Pillars:**
1. **Raising** (키우기) — Central mechanic. Raise characters by studying.
2. **Decorating** (꾸미기) — Place items to beautify each zone.
3. **Collecting** (컬렉팅) — Complete characters to unlock new ones.

**Platform:** Mac desktop only (MacBook Air M1), wide 2-column layout.
**Entry Point:** Home screen right column — replaces OceanWorldCard with Island card.

---

## 2. ZONES

### 2.1 Zone Layout (Island Map)

```
        🚀 Space
   🌳 Forest  ✨Legend  🌊 Ocean
        🦁 Savanna
```

- 5 zones total, displayed as irregular island map
- Zone boundaries: natural terrain (rivers, hills, forest edges) — no hard lines
- Each zone has unique color tone to distinguish
- Legend zone: center position, surrounded by 4 zones, fog effect when locked

### 2.2 Zone Backgrounds

| Zone | Background |
|------|-----------|
| 🌳 Forest | Green trees, sunlight, warm atmosphere |
| 🌊 Ocean | Blue water, coral, waves |
| 🦁 Savanna | Green grassland, white clouds, blue sky |
| 🚀 Space | Dark blue, stars, galaxy |
| ✨ Legend | Golden mist, mystical, sacred |

### 2.3 Zone Unlock Conditions

| Zone | Unlock Condition |
|------|-----------------|
| Zone 1 (Player's choice) | Unlocked at onboarding |
| Zone 2 | Complete 1 character in Zone 1 |
| Zone 3 | Complete 1 character in Zone 2 |
| Zone 4 | Complete 1 character in Zone 3 |
| Legend Zone | Complete 1st evolution on 1 character in all 4 zones |

### 2.4 Zone-Subject Mapping

| Zone | Subject | Characters |
|------|---------|-----------|
| 🌳 Forest | English | Sprout, Clover, Mossy, Fernlie, Blossie |
| 🌊 Ocean | Math | Axie, Finn, Delphi, Bubbles, Starla |
| 🦁 Savanna | Diary | Mane, Ellie, Leo, Zuri, Rhino |
| 🚀 Space | Review | Lumie, Twinkle, Orbee, Nova, Cosmo |
| ✨ Legend | All | Dragon, Unicorn, Phoenix, Gumiho, Qilin |

---

## 3. CHARACTER ROSTER

### 3.1 Forest Zone (English)

| # | Name | Concept | Evo Keyword |
|---|------|---------|-------------|
| 1 | Sprout | Small green sprout | Seedling → Bloom Tree |
| 2 | Clover | Three-leaf clover | Lucky Four-leaf |
| 3 | Mossy | Moss-covered stone spirit | Moss Spirit |
| 4 | Fernlie | Fern fairy | Ancient Fern |
| 5 | Blossie | Flower bud | Cherry Blossom |

### 3.2 Ocean Zone (Math)

| # | Name | Concept | Evo Keyword |
|---|------|---------|-------------|
| 1 | Axie | Pink axolotl with external gills | Giant Axolotl |
| 2 | Finn | Clownfish (orange/white stripes) | School Leader |
| 3 | Delphi | Dolphin (gray + white belly) | Spinner Dolphin |
| 4 | Bubbles | Pufferfish (round when inflated) | Pufferfish King |
| 5 | Starla | Starfish (5-pointed, math connection) | Crystal Starfish |

### 3.3 Savanna Zone (Diary)

| # | Name | Concept | Evo Keyword |
|---|------|---------|-------------|
| 1 | Mane | Baby horse (brown, no mane) | Wild Stallion |
| 2 | Ellie | Baby elephant (big eyes, small ears) | Gentle Giant |
| 3 | Leo | Baby lion (fluffy, no mane) | Pride Leader |
| 4 | Zuri | Baby giraffe (short neck) | Tall Watcher |
| 5 | Rhino | Baby rhino (one small horn, gray) | Stone Rhino |

### 3.4 Space Zone (Review)

| # | Name | Concept | Evo Keyword |
|---|------|---------|-------------|
| 1 | Lumie | Small alien (big eyes, one antenna, green) | Cosmic Elder |
| 2 | Twinkle | 5-pointed star creature with face | Supernova Star |
| 3 | Orbee | Planet spirit (small Saturn rings, expression) | Ringed Giant |
| 4 | Nova | Comet fairy with tail | Shooting Nova |
| 5 | Cosmo | Retro robot / space probe | Deep Space Bot |

### 3.5 Legend Zone

| # | Name | Origin | A Form | B Form |
|---|------|--------|--------|--------|
| 1 | Dragon | East/West | Flame Dragon | Ice Dragon |
| 2 | Unicorn | Western | Light Unicorn | Moon Unicorn |
| 3 | Phoenix | Eastern | Immortal Phoenix | Storm Phoenix |
| 4 | Gumiho | Korean/Eastern | Golden Gumiho | Shadow Gumiho |
| 5 | Qilin | Chinese/Korean | Sky Qilin | Earth Qilin |

### 3.6 Evolution Branch Attributes

| Zone | A Form Attribute | B Form Attribute |
|------|-----------------|-----------------|
| Forest (English) | English XP +3% + hunger decay slower | Lumi production +3 + happiness decay slower |
| Ocean (Math) | Math XP +3% + hunger decay slower | Lumi production +3 + happiness decay slower |
| Savanna (Diary) | Diary XP +3% + hunger decay slower | Lumi production +3 + happiness decay slower |
| Space (Review) | Review XP +3% + hunger decay slower | Lumi production +3 + happiness decay slower |
| Legend | All subjects XP +2% + hunger decay slower | Lumi production +8 + happiness decay slower |

**Final Evolution Bonus:**
- A Form Final: Subject XP +5% (cumulative)
- B Form Final: Lumi production +5 additional (cumulative)

---

## 4. CHARACTER GROWTH SYSTEM

### 4.1 Level Structure

```
baby (Lv1 → Lv5) → 1st Evolution possible
    ↓ Evolution Stone (First_A or First_B)
mid_a or mid_b (Lv6 → Lv10) → 2nd Evolution possible
    ↓ Evolution Stone (Second — shared)
final_a or final_b (COMPLETE)
```

### 4.2 Level XP Requirements

| Level | Required XP | Estimated Time |
|-------|------------|----------------|
| 1→2 | 100 | 1~2 days |
| 2→3 | 150 | 2~3 days |
| 3→4 | 200 | 2~3 days |
| 4→5 | 300 | 3~4 days |
| **Lv5 → 1st Evolution** | — | ~10~12 days |
| 5→6 (post-evo) | 100 | 1~2 days |
| 6→7 | 150 | 2~3 days |
| 7→8 | 200 | 2~3 days |
| 8→9 | 300 | 3~4 days |
| 9→10 | 400 | 4~5 days |
| **Lv10 → 2nd Evolution** | — | additional 12~17 days |

**Target:** ~3~4 weeks per character completion.

### 4.3 Character XP Sources

| Activity | Character XP |
|---------|-------------|
| English stage complete | +10 (Forest character) |
| English Final Test pass | +30 (Forest character) |
| Math lesson complete | +20 (Ocean character) |
| Math Unit Test pass | +50 (Ocean character) |
| Diary entry | +15 (Savanna character) |
| Review complete | +10 (Space character) |
| Streak bonus | +10 (all active characters) |

**XP Multiplier by Gauge Status:**

| Status | XP Reduction | XP Rate |
|--------|-------------|---------|
| Normal (both 60+) | None | 100% |
| One below 60 | -20% | 80% |
| One below 20 | -40% | 60% |
| Both below 20 | -80% | 20% |
| Evolution stone use | Blocked if any gauge < 20 | — |

### 4.4 Evolution Rules

- **1st Evolution:** Choose A or B branch → branch locked permanently
- **2nd Evolution:** Auto-follows 1st branch (mid_a → final_a, mid_b → final_b)
- Evolution stone: First_A or First_B for 1st evo; Second (shared) for 2nd evo
- Wrong branch stone use → "This character is type A!" notification → blocked
- Branch cannot be changed — must adopt new character for other branch

### 4.5 Legend Character Evolution (Special Rules)

| Stage | Condition |
|-------|-----------|
| baby → mid | 14 consecutive days + Legend Evolution Stone (First A or B) |
| mid → final | 30 consecutive days + Legend Evolution Stone (Second) |

- Legend characters use **consecutive days** system instead of XP
- 4 subjects all completed in one day = +1 legend gauge
- Missing any subject = 0 for that day (no decrease, just no progress)
- Breaking streak → gauge resets to 0 + character sad animation + happiness -10

### 4.6 Completed Character Benefits

| Type | Daily Lumi Production | XP Boost |
|------|----------------------|---------|
| Normal character (A form) | +5 | Subject XP +1.5% (cumulative) |
| Normal character (B form) | +5 additional production | Subject XP +1.5% |
| Legend character (A form) | +20 | All subjects XP +3% |
| Legend character (B form) | +20 additional | All subjects XP +3% |

**Completed characters:**
- No longer need care gauge management
- Permanently reside in their zone
- Continue producing lumi + XP boost forever

---

## 5. CARE SYSTEM

### 5.1 Gauges

Two gauges per active character: **Hunger** (0-100) and **Happiness** (0-100).

### 5.2 Gauge Increase (Study Activities)

| Activity | Hunger | Happiness |
|---------|--------|-----------|
| English stage complete | +20 | — |
| English Final Test pass | +30 | +30 |
| Math lesson complete | +20 | — |
| Math Unit Test pass | +30 | +30 |
| Diary entry | +25 | +20 |
| Review complete | +20 | +15 |
| Streak maintained | — | +10 (all active) |
| Legend 4-subject complete | — | +20 (legend char) |

### 5.3 Gauge Decay

| Gauge | Decay Rule |
|-------|-----------|
| Hunger | -15 every midnight |
| Happiness | -20 if no study for 2 consecutive days |

### 5.4 Food Items (Shop)

| Item | Effect | Lumi Cost | Daily Limit |
|------|--------|-----------|-------------|
| Small Food | Character XP +50 | 20 | 1x per character per day |
| Big Food | Character XP +150 | 50 | 1x per character per day |
| Special Food | Character XP +300 | 90 | 1x per character per day |

- Food is used on **specific character** (player selects)
- Daily limit resets at midnight
- Already-used food button disabled with tooltip

---

## 6. CURRENCY SYSTEM

### 6.1 Three-Currency Structure

| Currency | Earn | Spend |
|---------|------|-------|
| **XP** | All study activities | Real-world rewards (YouTube, Roblox, etc.) in Reward Shop |
| **Lumi 💎** | Study + streak + completed character production | Evolution stones, food, decorations, exchange |
| **Legend Lumi ✨** | Exchange 100 Lumi = 1 Legend Lumi | Legend zone items only |

### 6.2 Lumi Earn Rates

| Source | Lumi |
|--------|------|
| English stage complete | +3 |
| English Final Test pass | +15 |
| Math lesson complete | +10 |
| Math Unit Test pass | +20 |
| Diary entry | +8 |
| Review complete | +5 |
| Streak maintained | +5/day |
| Completed normal character (daily) | +5/character |
| Completed legend character (daily) | +20/character |

### 6.3 Exchange Rate

- 100 Lumi = 1 Legend Lumi (set in app_config: `lumi_exchange_rate = 100`)

### 6.4 Currency Rules

- Lumi cannot go negative → purchase buttons disabled when insufficient
- No maximum holding limit for any currency
- Lumi log retained for 90 days, then auto-deleted

---

## 7. SHOP SYSTEM

### 7.1 Shop Structure (Integrated with Reward Shop)

Reward Shop now has 5 tabs:

| Tab | Content | Currency |
|-----|---------|---------|
| 🎁 Rewards | Real-world rewards (existing system) | XP |
| 🧬 Evolution | Evolution stones (6 types) | Lumi / Legend Lumi |
| 🍖 Food | Food items (3 types) | Lumi |
| 🌿 Decor | Zone decoration items | Lumi / Legend Lumi |
| 💱 Exchange | Lumi → Legend Lumi | — |

### 7.2 Evolution Stones

| Item | Type | Price | Currency |
|------|------|-------|---------|
| 1st Evolution Stone A | Normal | 50 | Lumi |
| 1st Evolution Stone B | Normal | 50 | Lumi |
| 2nd Evolution Stone | Normal (shared) | 80 | Lumi |
| Legend 1st Stone A | Legend | 10 | Legend Lumi |
| Legend 1st Stone B | Legend | 10 | Legend Lumi |
| Legend 2nd Stone | Legend (shared) | 20 | Legend Lumi |

### 7.3 Decoration Items

**🌳 Forest (9 items)**

| Category | Items | Lumi |
|---------|-------|------|
| Props | Mushroom Lantern, Signpost, Honey Jar | 30 / 40 / 50 |
| Buildings | Cabin, Fairy Gate, Treehouse | 60 / 80 / 120 |
| Special | Firefly Effect, Flower Rain, Forest Mist | 100 / 150 / 200 |

**🌊 Ocean (9 items)**

| Category | Items | Lumi |
|---------|-------|------|
| Props | Treasure Chest, Shell Chime, Coral Lantern | 30 / 40 / 50 |
| Buildings | Underwater Garden, Sea Cave, Underwater Palace | 60 / 80 / 120 |
| Special | Bubble Effect, Light Pillar, Aurora | 100 / 150 / 200 |

**🦁 Savanna (9 items)**

| Category | Items | Lumi |
|---------|-------|------|
| Landscape | Baobab Tree, Pride Rock, Oasis | 30 / 40 / 50 |
| Nature | Waterfall, Cliff, Cave | 60 / 80 / 120 |
| Special | Sunset Effect, Great Migration, Starry Sky | 100 / 150 / 200 |

**🚀 Space (9 items)**

| Category | Items | Lumi |
|---------|-------|------|
| Landscape | Meteorite, Crater, Nebula | 30 / 40 / 50 |
| Nature | Black Hole, Asteroid Belt, Star Cloud | 60 / 80 / 120 |
| Special | Meteor Shower, Aurora, Wormhole | 100 / 150 / 200 |

**✨ Legend (10 items — Legend Lumi only)**

| Category | Items | Legend Lumi |
|---------|-------|------------|
| Dragon | Dragon's Nest | 5 |
| Unicorn | Rainbow Bridge | 5 |
| Phoenix | Phoenix Flame Tree | 5 |
| Gumiho | Gumiho Shrine | 5 |
| Qilin | Qilin's Footprints | 5 |
| Common | Sacred Tree | 8 |
| Common | Magic Circle | 8 |
| Common | Golden Aura Effect | 10 |
| Common | Rainbow Waterfall | 10 |
| Common | Star Altar | 12 |

### 7.4 Decoration Rules

- Max placement per zone: **All purchased items** (no limit — Forest/Ocean/Savanna/Space up to 9 items each, Legend up to 10)
- Duplicate purchase: **NOT allowed** (decoration items) — shows "Owned" badge
- Evolution stones: Duplicate purchase **ALLOWED** (consumable)
- Decoration **sell back**: 50% of purchase price in Lumi
- Sell-back UI: Inventory → item detail → "Sell" button → confirmation popup
- Evolution stones and food: **NOT sellable**

---

## 8. ONBOARDING

### 8.1 Flow (First-time only, cannot skip)

1. **Slide 1:** "Hi! I'm Lumi 🌟 This is Gia's Island!"
2. **Slide 2:** "Study to earn XP, convert to Lumi, and raise your characters!"
3. **Slide 3:** "Ready to meet your first friend?" → Zone selection
4. **Zone Selection:** 4 zone cards (name + silhouette + one-line description)
5. **Character Selection:** Choose from 5 silhouettes in selected zone
6. **Naming:** Enter name (max 8 chars, default name OK) → confirm
7. **Entry:** Into island main screen

### 8.2 Onboarding Rules

- **One-time only** — stored in `app_config: island_initialized = true`
- **Cannot skip** — naming + first character required for island to function
- **Name rules:**
  - Max 8 characters
  - Default name OK (no change required)
  - **Cannot be changed** after confirmation
  - No rename feature ever

---

## 9. UI / UX DESIGN

### 9.1 Island Main Screen (Map View)

```
┌─────────────────────────────────────────────────────┐
│  💎 1,250  ✨ 30  🔥 5 days    🎒 📖 ⚙️            │
│                                                     │
│         🚀 Space                                    │
│    🌳Forest  ✨Legend  🌊Ocean    [Zone Summary      │
│         🦁Savanna                  Panel]           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Top bar (always visible):**
- Left: 💎 Lumi balance / ✨ Legend Lumi balance / 🔥 streak
- Right: 🎒 Inventory / 📖 Collection / ⚙️ Settings

**Island map features:**
- Zoom in/out: trackpad pinch or +/- buttons
- Default: full island visible
- Max zoom: one zone fills screen
- Background: sky + white clouds (daytime); starry night sky (18:00~06:00)
- Zone boundaries: natural terrain, no hard lines

**Character display on map:**
- Active character: small icon on zone + idle animation
- Completed characters: multiple small icons in zone
- Warning badge: ❗ on character icon when gauge low
- Evolution ready: ✨ badge on character icon
- Locked zone: 🔒 icon, no characters shown

### 9.2 Zone Detail Screen

```
┌─────────────────────────────────────────────────────┐
│  LEFT (character area 50%)   RIGHT (info panel 50%) │
│                                                     │
│   [Character large]          Axie  Lv.3             │
│   Animation playing          ──────────────         │
│                              Hunger  ████████ 85%   │
│   Status text                Happy   █████░░░ 62%   │
│   "Axie is excited!"                               │
│                              XP to evolve: 340/600  │
│   [Completed chars below]    Evolution stone: None  │
│   [Silhouettes for locked]   Lumi production: +5/d  │
│                                                     │
│                              [ Feed ]               │
│                              [ Evolve ] (if ready)  │
│                              [ Shop → ]             │
└─────────────────────────────────────────────────────┘
```

**Right panel top:** 
- Legend zone: shows consecutive days progress bar (14-day / 30-day)

### 9.3 Character Detail Screen

- Back button (top-left) + ESC key → slide back to zone detail
- Large character image + name + level
- Hunger/Happiness gauges
- XP progress bar (current level)
- Evolution path tree (baby → mid_a/mid_b → final_a/final_b)
  - Unlocked stages: color image
  - Locked stages: silhouette
  - Chosen branch: colored; unchosen: gray + 🔒
- Feed button / Evolve button (disabled with tooltip if not ready)

### 9.4 Evolution Branch Selection UI

- Full-screen modal
- Left: A form silhouette + attribute description
- Right: B form silhouette + attribute description
- Bottom: "This choice cannot be undone" warning
- Confirm button after selection
- After 1st evolution: chosen branch in color, other branch gray + 🔒

### 9.5 Character Silhouette System

- Unadopted characters: black silhouette
- Name hidden: "???"
- Hover tooltip: "Complete previous character to unlock"
- First character in each zone: available from start
- Each completion → next character silhouette unlocked

### 9.6 Legend Zone Locked State

```
🔒 The Legend Isle
[Fog background]
Forest ✅  Ocean ⬜  Savanna ⬜  Space ⬜
1 / 4 complete
```

### 9.7 Collection (Dokgam) UI

- Entry: 📖 button in top bar
- Layout: zone-divided grid
- Completed: color image + name + completion date
- Incomplete: silhouette + "???"
- Legend: separate section
- Filters: All / By Zone / Completed Only / In Progress
- Sort: Default / Completion Date / By Zone
- Character detail: tap → modal (stage, attributes, evo history for completed)

### 9.8 Inventory UI

- Entry: 🎒 button in top bar
- Tabs: All / Evolution Stones / Food / Decoration
- Each item: image + name + quantity
- Tap to use or place

### 9.9 Lumi Log UI

- Entry: tap Lumi balance display
- Shows: date / earn-spend history / balance
- Filter: All / Earned / Spent
- Period: last 90 days

### 9.10 Notifications

- **App open:** popup for hungry/unhappy characters ("Axie is hungry! 🍖")
- **Island map:** ❗ badge on character icons with low gauges
- **Evolution ready:** ✨ badge + popup on app open
- **Level up:** shown on study completion result screen + ▲ badge on character icon

---

## 10. ANIMATIONS

All animation values stored in `frontend/src/config/animations.config.js` for easy modification.

### 10.1 Character State Animations

| State | Condition | Animation |
|-------|-----------|-----------|
| Idle | Always | Gentle up/down float (3s loop, minimal movement) |
| Happy | Both gauges 60%+ | Subtle scale pulse (scale 1.05, 600ms) |
| Sad | Any gauge below 20% | Slow side sway + slight opacity reduction |
| Feed | Food item used | Single small bounce |
| Level Up | Level reached | Glow then fade |
| 1st Evolution | Stone used | Fade out → new form fade in |
| 2nd Evolution | Stone used | Slower fade + light bloom |

### 10.2 Event Animations

| Event | Animation |
|-------|-----------|
| Character complete | Full-screen modal: zone gradient bg + radial bloom + particles (zone-themed) + character name fade in + attribute display |
| Zone unlock | Toast: "[Zone] is now open!" + lock icon dissolves + brightens on map |
| Legend unlock | Full-screen: screen darkens → golden light spreads → island silhouette emerges from mist → "The Legend Isle awakens..." text fade |
| Legend streak broken | Character sad animation + gauge reset animation + "Your streak was broken. Start again today!" |

### 10.3 Screen Transitions

| Transition | Animation |
|-----------|-----------|
| Map → Zone detail | Smooth zoom into zone |
| Zone detail → Map | Zoom out back to full island |
| Zone detail → Character detail | Slide right |
| Character detail → Zone detail | Slide left |

### 10.4 Lumi Earned Notification

- During study: **never shown**
- On study completion result screen: "+5 💎" display
- App open (daily production): "💎 +20 Lumi earned!" toast
- Exchange: "✨ Legend Lumi +1 earned!" toast

---

## 11. DATABASE DESIGN

### 11.1 Tables to DELETE (migration 018)

- `rewards` (legacy, unused)
- `schedules` (legacy, unused)
- `growth_theme_progress` (replaced by island system)

### 11.2 New Tables (10 tables)

**1. island_characters** — Character catalog (seed data: 30 characters)

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| name | String | "Axie", "Leo", etc. |
| zone | String | forest/ocean/savanna/space/legend |
| subject | String | english/math/diary/review/all |
| order_index | Integer | Position in zone 1~5 |
| description | String | Character description |
| images | String | JSON {"baby","mid_a","mid_b","final_a","final_b"} |
| lumi_production | Integer | Daily lumi when completed |
| xp_boost_pct | Float | XP boost % when completed |
| xp_boost_a_pct | Float | A form additional boost |
| xp_boost_b_pct | Float | B form: extra lumi |
| is_legend | Boolean | Legend character flag |
| unlock_requires_character_id | Integer FK nullable | Previous character required |
| is_available | Boolean | Available for adoption (first in zone = True) |
| evo_first_xp | Integer | XP needed for 1st evo (Lv5 = 750 cumulative) |
| evo_second_xp | Integer | XP needed for 2nd evo (Lv10 = 2250 cumulative) |

**2. island_character_progress** — Gia's character progress

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| character_id | Integer FK → island_characters.id | (NO UNIQUE — can adopt same char twice for A/B) |
| stage | String | baby/mid_a/mid_b/final_a/final_b |
| level | Integer | Current level 1~10 |
| current_xp | Integer | XP accumulated in current level |
| hunger | Integer | 0~100 |
| happiness | Integer | 0~100 |
| is_completed | Boolean | Completion flag |
| is_active | Boolean | Currently being raised |
| is_legend_type | Boolean | Legend character (ignore hunger/happiness) |
| boost_active | Boolean | True when completed |
| boost_subject | String | english/math/diary/review/all |
| last_production_date | String | Last daily lumi production date |
| last_decay_date | String | Last decay applied date |
| pos_x | Integer | Position on island map (completed chars) |
| pos_y | Integer | Position on island map (completed chars) |
| adopted_at | DateTime | |
| completed_at | DateTime | nullable |

**3. island_care_log** — Care history (auto-delete after 30 days)

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| character_progress_id | Integer FK | |
| action | String | feed/play/decay |
| hunger_change | Integer | +/- amount |
| happiness_change | Integer | +/- amount |
| source | String | english/math/diary/review/food_item/auto_decay |
| logged_at | DateTime | |

**4. island_shop_items** — Shop catalog (seed data: 55 items)

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| name | String | Item name |
| category | String | evolution/decoration/food |
| sub_category | String | prop/nature/special / null |
| zone | String | forest/ocean/savanna/space/legend/all |
| evolution_type | String | null/first_a/first_b/second/legend_first_a/legend_first_b/legend_second |
| price | Integer | |
| is_legend_currency | Boolean | True = Legend Lumi required |
| image | String | Image path |
| is_active | Boolean | |
| description | String | Item description |

**5. island_inventory** — Owned items

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| shop_item_id | Integer FK | |
| item_type | String | evolution/decoration/food |
| quantity | Integer | |
| used_on_character_progress_id | Integer FK nullable | Which character evolution stone was used on |
| purchased_at | DateTime | |

**6. island_placed_items** — Placed decorations

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| shop_item_id | Integer FK UNIQUE | (one item per zone, no duplicates) |
| zone | String | |
| pos_x | Integer | |
| pos_y | Integer | |
| is_placed | Boolean | False = recalled to inventory |
| placed_at | DateTime | |

**7. island_currency** — Lumi balance (single row, id=1)

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | id=1 always, upsert |
| lumi | Integer | CHECK (lumi >= 0) |
| legend_lumi | Integer | CHECK (legend_lumi >= 0) |
| total_earned | Integer | Cumulative lumi earned |
| updated_at | DateTime | |

**8. island_lumi_log** — Lumi transaction history (auto-delete after 90 days)

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| currency_type | String | lumi/legend_lumi |
| action | String | earn/spend/exchange |
| amount | Integer | +/- |
| source | String | english/math/diary/review/shop/exchange/production |
| balance_after | Integer | Balance after transaction |
| legend_balance_after | Integer | Legend lumi balance (for exchange) |
| character_progress_id | Integer FK nullable | For production logs |
| earned_date | Date | For duplicate prevention (production type) |
| created_at | DateTime | |

**9. island_legend_progress** — Legend character streak tracking

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| character_id | Integer FK → island_characters.id | |
| consecutive_days | Integer | Current streak |
| total_days | Integer | Cumulative days |
| last_completed_date | Date | Last day all 4 subjects completed |
| is_unlocked | Boolean | Legend zone unlocked flag |
| is_completed | Boolean | Character completed |
| completed_at | DateTime | nullable |

**10. island_zone_status** — Zone unlock tracking (seed: 5 rows)

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| zone | String | forest/ocean/savanna/space/legend |
| is_unlocked | Boolean | forest/ocean/savanna/space start True; legend = False |
| unlocked_at | DateTime | nullable |
| first_completed_at | DateTime | nullable — when first char completed in zone |

### 11.3 app_config Keys to Add

```
island_initialized          = false        # Onboarding complete flag
lumi_exchange_rate          = 100          # Lumi per Legend Lumi
lumi_rule_english_stage     = 3
lumi_rule_english_final     = 15
lumi_rule_math_lesson       = 10
lumi_rule_math_unit         = 20
lumi_rule_diary             = 8
lumi_rule_review            = 5
lumi_rule_streak            = 5
lumi_boost_total            = 0            # Cached total boost
lumi_boost_english          = 0            # Cached English XP boost %
lumi_boost_math             = 0            # Cached Math XP boost %
lumi_boost_diary            = 0            # Cached Diary XP boost %
lumi_boost_review           = 0            # Cached Review XP boost %
island_on                   = true         # Parent can disable island
```

---

## 12. API ENDPOINTS (34 total)

### 12.1 Island Status & Onboarding

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/status | Full island state (zones/chars/lumi) |
| GET | /api/island/onboarding/status | Onboarding complete check |
| POST | /api/island/onboarding/complete | Mark onboarding complete |

### 12.2 Zone Management

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/zone/status | Zone unlock status all 5 |
| POST | /api/island/zone/unlock | Unlock zone |

### 12.3 Character Management

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/characters | Full character catalog |
| GET | /api/island/character/active | Currently raising (by zone) |
| GET | /api/island/character/completed | Completed characters |
| GET | /api/island/character/silhouette | Silhouette unlock status |
| POST | /api/island/character/adopt | Adopt + name character |
| POST | /api/island/character/evolve | Use evolution stone + validate branch |
| POST | /api/island/evolve/validate | Pre-validate evolution eligibility |
| GET | /api/island/character/{id}/history | Character evolution history |

### 12.4 Care System

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/care/{character_id} | Character gauge status |
| POST | /api/island/care/feed | Use food item on character |

### 12.5 Daily Processing

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/island/daily | App open: decay + lumi production batch |

### 12.6 Currency

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/currency | Lumi + Legend Lumi balance |
| POST | /api/island/lumi/earn | Study complete → award lumi |
| POST | /api/island/lumi/exchange | Lumi → Legend Lumi |
| GET | /api/island/lumi/log | Transaction history |

### 12.7 Shop & Inventory

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/shop | Full shop catalog |
| POST | /api/island/shop/buy | Purchase item |
| GET | /api/island/inventory | Owned items list |
| GET | /api/island/placed | Placed decoration list |
| POST | /api/island/decorate/place | Place item in zone |
| POST | /api/island/decorate/remove | Recall item to inventory |

### 12.8 Legend System

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/legend/progress | Legend gauge status |
| POST | /api/island/legend/daily | Check 4-subject completion |
| GET | /api/island/legend/unlock/status | Legend zone unlock condition progress |

### 12.9 Boost & Notifications

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/boost/status | XP boost by subject |
| GET | /api/island/notifications | Unread notifications |
| POST | /api/island/notifications/read | Mark read |

### 12.10 Config & Stats

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/island/config | Island app_config values |
| POST | /api/island/config/update | Parent update settings |
| GET | /api/island/stats/summary | Parent dashboard summary (Phase 2) |

---

## 13. BACKEND SERVICES

### 13.1 New Service Files

| File | Role |
|------|------|
| `services/lumi_engine.py` | Lumi earn/spend/exchange logic |
| `services/island_care_engine.py` | Decay calculation, gauge update |
| `services/island_production_engine.py` | Completed character daily lumi batch |
| `routers/island.py` | All island API routes |
| `services/island_service.py` | Evolution branch validation logic |

### 13.2 Existing Files to Modify

| File | Modification |
|------|-------------|
| `services/xp_engine.py` | Add lumi award call on study complete |
| `services/streak_engine.py` | Add streak lumi award |
| `backend/main.py` | On app start: run decay + lumi production batch |
| `routers/diary.py` | On diary complete: call lumi_engine + island_care_engine |
| `routers/study.py` | On English complete: same |
| `routers/math_academy.py` | On Math complete: same |
| `routers/review.py` | On Review complete: same |
| `frontend/static/js/reward-shop.js` | Add Island tabs, remove legacy shell refs |
| `frontend/static/js/parent-panel.js` | Remove growth_theme, add island ON/OFF |

### 13.3 Files to DELETE

| File | Reason |
|------|--------|
| `backend/routers/growth_theme.py` | Replaced by island router |
| `backend/models/gamification.py` | growth_theme models removed |

### 13.4 Performance Policies

| Item | Policy |
|------|--------|
| island_care_log | Auto-delete after 30 days |
| island_lumi_log | Auto-delete after 90 days |
| Decay execution | Calculate elapsed days on app open, batch apply |
| Daily lumi production | Batch process on app open (single transaction) |
| XP boost | Cache in app_config, update only on character complete |

---

## 14. SETTINGS

Island-related settings (added to existing Settings screen):

| Setting | Default |
|---------|---------|
| Sound effects ON/OFF | ON |
| Notifications ON/OFF | ON (gauge warning) |
| Gauge warning threshold | 20% |
| Data reset | Requires parent password |

Parent dashboard: Island ON/OFF toggle (stored in `app_config: island_on`)

---

## 15. CONFIG FILES

### 15.1 animations.config.js

Location: `frontend/src/config/animations.config.js`

```javascript
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
```

### 15.2 island.config.js

Location: `frontend/src/config/island.config.js`

```javascript
export const ISLAND_CONFIG = {
  zones: {
    forest:  { label: 'Forest',  emoji: '🌳', subject: 'english' },
    ocean:   { label: 'Ocean',   emoji: '🌊', subject: 'math' },
    savanna: { label: 'Savanna', emoji: '🦁', subject: 'diary' },
    space:   { label: 'Space',   emoji: '🚀', subject: 'review' },
    legend:  { label: 'Legend',  emoji: '✨', subject: 'all' },
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
```

---

## 16. PHASE 2 ITEMS (Future — Do Not Implement Now)

| Item | Description |
|------|-------------|
| Parent Dashboard Island Section | Character progress, lumi log, gauge status widget |
| BGM | Zone-specific background music (5 tracks) |
| AI Chat System | Ollama integration for character interaction |
| Arcade Integration | Arcade score → lumi bonus |
| Collection Dokgam Detail Expansion | Extended character lore |
| Character Accessories | Hats, ribbons, character customization |

---

## 17. MIGRATION PLAN

**Migration:** `018_island_tables.py`

Actions:
1. DROP `rewards` table
2. DROP `schedules` table
3. DROP `growth_theme_progress` table
4. CREATE all 10 island tables
5. SEED `island_zone_status` (5 rows: forest/ocean/savanna/space = unlocked, legend = locked)
6. SEED `island_shop_items` (55 items: 6 evolution stones + 3 food + 36 normal decor + 10 legend decor)
7. SEED `island_characters` (30 characters)
8. ADD `app_config` keys (island_initialized, lumi rules, boost cache, exchange rate)

---

*End of ISLAND_SPEC.md*
