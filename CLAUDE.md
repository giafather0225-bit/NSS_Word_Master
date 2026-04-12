# GIA Learning App — Project Spec (CLAUDE.md)

## Overview
- **Product**: English vocabulary learning app with a 5-step lesson flow and AI scoring.
- **Status**: Active development — redesigning UI/UX while preserving backend logic.

---

## Tech Stack
- **Backend**: Python / Flask
- **Frontend**: HTML, CSS, Vanilla JS
- **AI Scoring**: Ollama (primary, model: gemma2:2b, http://localhost:11434) / Google Gemini API (fallback)
- **Speech**: Web Speech API (browser-based)
- **TTS**: edge-tts library → in-memory BytesIO stream → browser fetch → Blob → Audio object (no temp files, no afplay)

---

## File Structure
NSS_Word_Master/ ├── CLAUDE.md ├── backend/ │ ├── main.py │ ├── tts_edge.py ← TTS: BytesIO in-memory, no temp files │ └── tts_say.py └── frontend/ ├── templates/ │ └── child.html ← main UI (modify allowed) └── static/ ├── css/ │ ├── style.css ← common styles + CSS variables │ ├── preview.css ← Step 1: Preview │ ├── wordmatch.css ← Step 2: Word Match │ ├── fillblank.css ← Step 3: Fill the Blank │ ├── spelling.css ← Step 4: Spelling Master │ ├── sentence.css ← Step 5: Make a Sentence │ └── finaltest.css ← Final Test ├── js/ │ └── child.js ← core logic (modify allowed) └── images/ └── gia-logo.png ← saved, not yet applied

Copy
---

## Design System (Apple Minimal Style)
```css
:root {
  --bg:             #F5F5F7;
  --surface:        #FFFFFF;
  --primary:        #4A9B8E;
  --primary-hover:  #3A8B7E;
  --primary-light:  #EAF4F2;
  --text-primary:   #1D1D1F;
  --text-secondary: #6E6E73;
  --border:         #E0E0E5;
  --success:        #34C759;
  --danger:         #FF3B30;
}
Font: -apple-system, SF Pro, sans-serif
Radii: 8 / 12 / 16 / 24 px
No gradients, no heavy shadows
All colors via CSS variables — no hard-coded hex in component CSS
Critical Rules
child.js modification is allowed
Do NOT change existing element IDs or class names without explicit instruction
Edit child.html, CSS files, and child.js as needed
Add new classes/IDs for new UI features only
Output only changed snippets — never full file contents
Use CSS variables — no hard-coded colors
UI text in English only
Apple-style minimal design — no gradients, no heavy shadows
List modified files at the end of every response
Dev Tools (child.js — do not modify)
DEV.go(1) → Preview
DEV.go(2) → Word Match
DEV.go(3) → Fill the Blank
DEV.go(4) → Spelling Master
DEV.go(5) → Make a Sentence
DEV.go(6) → Final Test
DEV.skip() → skip current word
Learning Flow
Lesson Select → Preview → Word Match → Fill Blank → Spelling → Make a Sentence → Complete → Final Test

Sidebar
Fixed width: 240px, always visible on desktop
Auto-closes when Start button is clicked (adds sidebar-closed class)
Hamburger (☰) toggles open/closed with 0.25s slide animation
CSS open: width: 240px; opacity: 1; transform: translateX(0)
CSS closed: width: 0; overflow: hidden; padding: 0; min-width: 0; border: none
Sidebar Layout (top to bottom)
GIA avatar (36px circle, var(--primary)) + "GIA" label (17px, var(--text-primary))
English / Math pill toggle (active: white + shadow, inactive: var(--text-secondary))
TEXTBOOK label (11px, var(--text-secondary)) + dropdown (e.g., Voca_8000)
LESSON label (11px, var(--text-secondary)) + dropdown (Lesson_01 ~ Lesson_22)
Divider
Final Test / Unit Test / Speed Runner (always active, 13px, var(--text-secondary))
Settings icon (bottom)
Top Bar
Left: hamburger (☰)
Center: step roadmap capsule pills
Active: white bg, shadow 0 1px 4px rgba(0,0,0,0.15), 12px, weight 600, var(--text-primary)
Completed: var(--text-secondary) + ✓
Locked: var(--border) color
Connectors: 1px solid var(--border)
Right: 📖 Diary icon, ★ stars, progress bar (80px, 3px, fill var(--primary)), % + word count
TTS
Library: edge-tts
Stream: in-memory BytesIO (no disk write, no afplay)
Browser: fetch /api/tts/ → Blob → new Audio(objectURL) → .play()
Stop: stopAudio() → currentAudio.pause() + revokeObjectURL + speechSynthesis.cancel() + activeRec.abort()
AbortController (ttsAbort) cancels in-flight fetch on popup close
AI Scoring
Primary: Ollama, model gemma2:2b, endpoint http://localhost:11434
Fallback: Google Gemini API
Used in: Step 5 (Make a Sentence) and Final Test
Criteria: English grammar + spelling accuracy
Step Specs
Step 1 — Preview
4×5 word card grid (20 cards)
Card: bg var(--surface), border 1px solid var(--border), radius 14px
Hover: bg var(--bg)
Visited/completed: bg var(--bg), text var(--text-secondary), ✓ top-right
Click → popup modal
Preview Popup
Backdrop: rgba(0,0,0,0.3) + blur(8px)
Modal: white, radius 24px, width 480px, padding 32px
Close (×): stops all audio immediately via stopAudio()
Backdrop click: also triggers stopAudio() + close
Content:
POS tag pill (bg var(--primary-light), color var(--primary), 11px)
Word (32px, weight 700)
Definition (15px, var(--text-primary))
Example (13px italic, var(--text-secondary), left border 2px var(--border))
Listen button → fetch TTS → play via Audio object
Guidance: "Listen first, then repeat after the audio" (12px, var(--text-secondary))
SHADOW section (3 rows, mic 🎤 button, ○/✓, score %)
Pass: ≥80% accuracy
Guidance shown after Listen: "Press the mic and repeat the word"
SPELL section (3 rows, input, ○/✓/✗)
Activates after Shadow complete
Guidance shown after Shadow: "Great! Now type the word"
Correct: border var(--success), bg #F0FBF4
Wrong: border var(--danger), shake animation
Step 2 — Word Match
Dual column: words (left) / definitions (right)
Card: height 56px, bg var(--surface), border 1px solid var(--border), radius 8px, 13px font
Hover: bg var(--bg)
Selected: border var(--primary), bg var(--primary-light), color var(--primary)
Matched: border var(--success), bg #F0FBF4, opacity 0.6, pointer-events none
Wrong flash: border var(--danger), shake 0.3s
7 words per round
Step 3 — Fill the Blank
Sentence card: bg var(--surface), border 1px solid var(--border), radius 16px, padding 32px, 18px font
Blank: border-bottom 2px solid var(--primary), min-width 80px, inline-block
Word tags: pill style, bg var(--bg), border var(--border), radius 9999px, padding 6px 14px, 13px
Selected tag: bg var(--primary-light), border var(--primary), color var(--primary)
Used tag: opacity 0.4, pointer-events none
Correct: border var(--success), bg #F0FBF4
Wrong: border var(--danger), shake 0.3s
Progress: 13px, var(--text-secondary)
Step 4 — Spelling Master
Wordle-style letter boxes: 48×48px, border 2px solid var(--border), radius 8px, 20px bold
Active box: border var(--primary)
Correct: bg var(--success), color white, border var(--success)
Wrong: bg var(--danger), color white, border var(--danger), shake 0.3s
Pass indicator: ●●○ dots (8px circle, filled: var(--primary), empty: var(--border))
3 passes per word (hint → first letter → blank)
Wrong answers collected for retry
Step 5 — Make a Sentence
Stage 1: drag-and-drop word scramble
Word cards: pill style, bg var(--bg), border var(--border), radius 9999px, padding 8px 16px
Dragging: opacity 0.5, border var(--primary)
Drop zone: border 2px dashed var(--border), radius 12px, min-height 56px, bg #FAFAFA
Drag-over: border var(--primary), bg var(--primary-light)
Dropped cards: bg var(--primary-light), border var(--primary), color var(--primary)
Stage 2: solo writing (word shown)
Input: border-bottom 2px solid var(--border), focus: var(--primary), 16px font
AI scores grammar + spelling
Score: 24px bold, var(--primary)
Correct: bg #F0FBF4, border var(--success)
Retry: bg #FFF5F5, border var(--danger)
Final Test
Part 1: fill-in (20 items)
Part 2: multiple-choice (20 items)
Question card: bg var(--surface), border var(--border), radius 12px, padding 20px
Fill-in input: border-bottom 2px solid var(--border), focus: var(--primary)
MCQ options: pill buttons, selected: bg var(--primary-light), border var(--primary)
Score screen: 48px bold, ≥90: var(--success), <90: var(--danger)
Score <90 → full reset to Preview
Gia's Diary
Access: 📖 icon in Top Bar
Content: lesson-grouped card grid of sentences created in Step 5
Status: not yet implemented
Implementation Status
✅ 1. Design system ✅ 2. Sidebar + Top Bar ✅ 3. Preview grid ✅ 4. Preview popup → 5. Word Match ← CURRENT 6. Fill the Blank 7. Spelling Master 8. Make a Sentence 9. Final Test 10. Gia's Diary 11. Logo (gia-logo.png, saved, not yet applied) 12. Unit Test / Speed Runner (later)