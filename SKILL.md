# GIA Learning App — Project Skill Sheet

## Project Overview
English vocabulary learning app for students.
5-step learning flow per lesson with AI scoring.

## Tech Stack
- Backend: Python / Flask
- Frontend: HTML / CSS / Vanilla JS
- AI Scoring: Ollama (local) / Google Gemini API (fallback)
- Speech Recognition: Web Speech API (built-in browser)

## File Structure
- frontend/templates/child.html ← main UI
- frontend/static/css/style.css ← all styles
- frontend/static/js/child.js ← core logic (DO NOT TOUCH)
- frontend/static/images/gia-logo.png ← logo (saved, not yet applied)

## Design System (Apple Style)
- Font: -apple-system, SF Pro
- BG: #F5F5F7
- Surface: #FFFFFF
- Primary: #4A9B8E
- Primary Light: #EAF4F2
- Primary Hover: #3A8B7E
- Text: #1D1D1F
- Secondary text: #6E6E73
- Border: #E0E0E5
- Success: #34C759
- Danger: #FF3B30
- Radius: 8/12/16/24px
- All CSS variables defined in style.css :root
- No gradients, no heavy shadows

## Learning Flow
Lesson Select → Preview → Word Match → Fill Blank → Spelling → Make a Sentence → Complete → Final Test (anytime)

## Sidebar Structure
- GIA avatar (36px, #4A9B8E bg) + English/Math toggle (pill style)
- TEXTBOOK dropdown (e.g. Voca_8000)
- LESSON dropdown (same style as TEXTBOOK, Lesson_01~22)
  - Completed: ✅ + [Test] button
  - Current: left border #4A9B8E
  - Locked: gray #C7C7CC
- Bottom: Final Test / Unit Test / Speed Runner (always active, no emoji)
- Footer: ⚙ Settings
- Sidebar auto-closes when Start clicked
- Hamburger (☰) toggles sidebar open/closed (slide animation 0.25s)

## Top Bar Structure
- Left: ☰ hamburger
- Center: Roadmap (Preview · Match · Fill · Spell · Write)
  - Active: white capsule pill + shadow
  - Done: #6E6E73 + ✓
  - Locked: #C7C7CC
- Right: 📖 Diary / ★ stars / progress bar 80px / % / word count

## Step Specifications

### Step 1 — Preview
- 4×5 word card grid (20 words)
- Card: white, border-radius 14px, shadow-sm, font-weight 500
- Hover: scale(1.02)
- Visited card: bg #F5F5F7, color #B0B0B5, ✓ top-right
- Click card → popup modal

#### Preview Popup
- Backdrop: rgba(0,0,0,0.3) + blur(8px)
- Modal: white, border-radius 24px, width 480px, padding 32px
- Content order:
  1. POS tag (e.g. VERB) — teal pill
  2. Word title — 32px bold
  3. Definition — 15px
  4. Example sentence — 13px italic, left border
  5. Listen button — outline style, 🔊 icon
  6. SHADOW section — 3 mic rows, ≥80% to pass, retry if fail
  7. SPELL section — 3 input rows (activates after Shadow done)
- Completed card: bg #F5F5F7, color #B0B0B5, ✓

### Step 2 — Word Match
- Left: word cards / Right: definition cards
- Card: height 56px, border-radius 12px, border 1px #E0E0E5
- Selected: bg #4A9B8E, white text
- Matched: both cards turn #34C759, stay green (never disappear)
- 7 words per round

### Step 3 — Fill the Blank
- Sentence card on top (border-radius 24px, bg #F5F5F7, font 18px)
- Blank: underline style in #4A9B8E
- Word tags below sentence (wrap 2 lines)
- Input + Check button below tags
- Progress: 1/20

### Step 4 — Spelling Master
- Letter box style (Wordle-like), 48×48px each
- Empty: border 2px #E0E0E5
- Correct: bg #34C759, white text
- Wrong: bg #FF3B30, shake animation
- 3 passes per word:
  - Pass 1: partial hint (e.g. _x_m_n_)
  - Pass 2: first letter only (e.g. e_______)
  - Pass 3: completely blank
- Wrong answers collected → retry at end
- Pass indicator: ●●○

### Step 5 — Make a Sentence
- Stage 1: drag-and-drop word scramble
- Stage 2: solo writing (word shown only, type full sentence)
- AI scoring: grammar + spelling
- Wrong → retry at end

### Final Test
- Part 1: 20 subjective (see definition → type word)
- Part 2: 20 objective MCQ (mixed word↔definition, 4 choices)
- Result screen: score + wrong words list
- Score < 90 → full reset to Preview

### Gia's Diary
- Access: 📖 icon in top bar
- Layout: lesson-grouped card grid
- Content: sentences from Step 5 only

## AI Scoring
- Primary: Ollama (local)
  - Model: gemma2:2b
  - Endpoint: http://localhost:11434
- Fallback: Google Gemini API (when Ollama slow or unavailable)
- Criteria: English grammar + spelling
- Used in: Step 5 Make a Sentence, Final Test

## Critical Rules (ALWAYS FOLLOW)
1. NEVER modify child.js
2. NEVER change existing element IDs or class names
3. ONLY modify child.html and style.css unless told otherwise
4. ADD new classes/IDs alongside existing ones
5. Always list modified files at end of response
6. Use CSS variables from :root, never hardcode colors
7. All UI text in ENGLISH only
8. NEVER output full file contents — show changed snippets only
9. Apple-style minimal design

## DEV Tools (in child.js — do not remove)
- DEV.go(step) — jump to step
- DEV.skip() — skip current word

## Pending Implementation
✅ 1. Design system
✅ 2. Sidebar + Top Bar
✅ 3. Preview grid
→  4. Preview popup (CURRENT)
   5. Word Match
   6. Fill the Blank
   7. Spelling
   8. Make a Sentence
   9. Final Test
   10. Gia's Diary
   11. Logo (gia-logo.png ready, not yet applied)
   12. Unit Test / Speed Runner
