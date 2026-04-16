# GIA Learning App — Math Section Spec (MATH_SPEC.md)

## Overview
- **Product**: Math learning section within GIA Learning App — CPA-based instruction, adaptive placement, massive practice, spaced repetition, and integrated gamification.
- **Status**: Planning Phase — not yet in development.
- **Target User**: GIA (currently G2, MAP Math RIT 205 / 94th percentile, Math Kangaroo 82%)
- **Grade Range**: G3 -> G6 (expandable)
- **Curriculum Base**: Go Math (Houghton Mifflin Harcourt), aligned with Common Core State Standards
- **Entry Point**: Home Dashboard -> Math tab (#tab-math) in existing sidebar

---

## Tech Stack (Shared with English App)
- **Backend**: Python / FastAPI (add `routers/math_*.py`)
- **Frontend**: HTML, CSS, Vanilla JS (same SPA shell — child.html)
- **Database**: SQLite WAL at `~/NSS_Learning/database/voca.db` (add Math tables — fully separate from English tables)
- **AI**: Ollama (gemma2:2b) / Gemini fallback — for word problem generation, hint generation
- **TTS**: edge-tts (for Learn card narration, problem reading)
- **XP/Streak**: Shared system with English (`xp_logs`, `streak_logs` tables)

---

## 7 Pedagogical Pillars (Research-Validated)

### Pillar 1: CPA-First (Concrete -> Pictorial -> Abstract)
- **Evidence**: IES WWC Strong Evidence (28 studies), Singapore TIMSS 2023 #1 (615 pts)
- **Implementation**: Every concept introduced with virtual manipulatives (Concrete) -> visual models like bar models, arrays, number lines (Pictorial) -> symbolic notation (Abstract)
- **App**: Learn cards follow C->P->A sequence; Try includes manipulative interactions; Practice is Abstract only
- **Stage Rules**:
  - **Learn + Try**: Virtual Manipulatives available (interactive drag-and-drop)
  - **Practice R1~R3**: Answer input only (Abstract stage)
  - **CPA Fallback on Practice errors**: Show Pictorial image in feedback (no interactive manipulatives)

### Pillar 2: Explicit Instruction (Explicit -> Guided -> Independent)
- **Evidence**: IES Strong Evidence (43 studies), Hattie d=0.57
- **Implementation**: LEARN (teacher models) -> TRY (guided with hints + Step-by-Step Solution UI) -> PRACTICE (independent, no hints, answer only)

### Pillar 3: Interleaved Practice + Massed Repetition
- **Evidence**: IES-funded studies d=0.83, accuracy improvement +34pp
- **Implementation**: Min 25-30 problems per concept; Practice rounds mix current + 15-20% review from prior lessons; 9+ variant types per fact (direct, reverse, MC, T/F, array, word problem, bar model, comparison, two-blank)

### Pillar 4: Immediate Feedback + CPA Fallback
- **Evidence**: Hattie d=0.70, PMC 2020 confirms immediate > delayed feedback
- **Implementation**: Within 3 seconds show correct answer + reasoning + Pictorial image + new similar problem; On error: show abstract answer -> pictorial model image -> new problem

### Pillar 5: Spaced Repetition + Daily Mixed Review
- **Evidence**: USF 2021, Hattie d=0.60, IES recommendation
- **Implementation**: Wrong items reviewed on day 1, 3, 7, 21; Daily Challenge = 50% new + 30% spaced review + 20% spiral from older units

### Pillar 6: Fluency vs Thinking (Dual Track)
- **Evidence**: IES Strong Evidence (27 studies), Hamline 2020 correlation study
- **Implementation**: 3-phase approach per fact set:
  - Phase A: Untimed recall (understand first)
  - Phase B: Gentle timer (10s per problem)
  - Phase C: Speed challenge (5s per problem)
- Fact Fluency track (speed, daily 2-3 min) separated from Kangaroo Practice track (depth, no time pressure)

### Pillar 7: Growth-Mindset Messaging
- **Evidence**: Moderate (Dweck effort-praise solid, Boaler's neuro claims debated)
- **Implementation**: Praise strategy not ability; replace "Wrong!" with "Not yet — let's try another way!"; delay hints ~30 seconds to encourage productive struggle; keep tone encouraging without over-promising

---

## 10 Additional Features

| # | Feature | Priority | Notes |
|---|---------|----------|-------|
| 1 | Virtual Manipulatives | Must | Base Ten Blocks, Number Line, Array Grid, Fraction Bars, Bar Model Builder — all 5 interactive (drag-and-drop, mouse/trackpad). Used in Learn + Try stages only. |
| 2 | Step-by-Step Solution UI | High | Replaces scratchpad (no touchscreen on MacBook Air); guided multi-step input fields for showing work. Try stage only. |
| 3 | Math Glossary (EN) | High | Tap any math term -> plain English definition + visual example |
| 4 | 3-Read Strategy UI | High | For word problems: Read 1 (story), Read 2 (question), Read 3 (data) — lightweight guide overlay |
| 5 | Parent Dashboard (Math) | Must | Integrated with existing parent dashboard; Math tab/filter added |
| 6 | Gamification | Med | Shared XP/Streak/Badge system with English; Math-specific badges ("Multiplication Master", "Fraction Explorer") |
| 7 | Wrong Answer Classification | High | Phase 1: all errors treated as concept_gap (1 correct = mastered). Phase 2+: auto-tag careless/concept_gap/reading_error/timeout with differential mastery criteria. |
| 8 | Animation/Video | Med | Short CPA transition animations (Lottie/Rive); e.g., Base Ten Blocks regrouping animation. Phase 1: static SVG + TTS only. |
| 9 | Offline Mode | Med | Cache problem JSON locally; sync progress on reconnect |
| 10 | Placement Test | Must | First-time entry: 15-20 adaptive questions across G2-G6; per-domain level assignment |

---

## Navigation Flow

### Entry
```
Home Dashboard
  -> [Today's Tasks] includes:
      Math Daily Challenge (0/5) ...... +5 XP
      Math Fact Fluency (0/3) ......... +3 XP
  -> [Section Cards] Math card -> enters Math mode
  -> OR Sidebar #tab-math -> enters Math mode
```

### First-Time Entry
```
Math tab (first click ever)
  -> "Let's find out where you are!" screen
  -> Placement Test (15-20 adaptive questions, G2-G6 range)
  -> Results: per-domain level assignment
      e.g., Addition/Subtraction: G4, Multiplication: G3-mid, Fractions: G3-start
  -> Academy starting points auto-configured
  -> Math Home
```

### Math Sidebar (Accordion — one open at a time)
```
<- Home
MATH
  Academy                   (accordion)
    Grade: [G3 dropdown]
    Unit:  [U1: Addition & Subtraction dropdown]
    Lesson: [L2: Addition Strategies dropdown]
    ---
    Unit Test  (unlocks after all lessons pass)
  Fact Fluency              (accordion)
    Today: 0/3 rounds
    Best Streak: 42
    [Start] button
  Kangaroo Practice         (accordion)
    This Week: 2/5 sets
    [Start] button
  My Problems               (accordion)
    12 items to review
    Weak Area: Regrouping
    [Review Now] button
  Settings
```

---

## Academy Learning Flow

```
Lesson Select
  -> Pretest (5 Q)
     - 5/5 correct = skip Learn + Try, go to Practice R1
     - < 5/5 = proceed to Learn
  -> LEARN (5-8 CPA concept cards with TTS + static SVG + manipulative interaction)
  -> TRY (5 guided problems with 2-level hints + Step-by-Step Solution UI + manipulatives)
  -> PRACTICE Round 1: Basic (10 Q, pass >= 80%, answer input only)
  -> PRACTICE Round 2: Mixed/Variant (10 Q, pass >= 80%)
  -> PRACTICE Round 3: Advanced (5 Q, pass >= 80% = 4/5)
  -> WRONG REVIEW (auto-collected wrong items, new similar problems, 1 correct = mastered)
  -> Lesson Complete -> XP awarded
  -> After all lessons in unit -> UNIT TEST unlocked (20 Q, pass >= 90%)
```

### Adaptive Difficulty Logic
```
Pretest: 5/5 correct -> skip Learn/Try, go straight to Practice R1
Practice: 5 consecutive correct -> bump to next round early
Practice: 3 consecutive wrong -> drop difficulty, show additional hints
Cross-grade: if mastery shown in current grade domain -> offer next grade content
```

### Session Rules
- **No session timeout** for Math (unlike English's 2-day limit)
- Progress is saved per stage; student can resume at any time
- No auto-reset mechanism

### Unit Test Failure
- Analyze wrong answers by lesson tag
- Identify the lesson with the most errors = "weak lesson"
- Display: "You need more practice on [Lesson Name]! Let's review."
- Redirect to that lesson's Practice stages

---

## Curriculum Structure (Go Math Aligned)

### G3 (12 Units)
| Unit | Topic | Go Math Ch |
|------|-------|-----------|
| U1 | Addition & Subtraction within 1,000 | Ch 1 |
| U2 | Data & Graphs | Ch 2 |
| U3 | Understand Multiplication | Ch 3 |
| U4 | Multiplication Facts | Ch 4 |
| U5 | Use Multiplication Facts | Ch 5 |
| U6 | Understand Division | Ch 6 |
| U7 | Division Facts | Ch 7 |
| U8 | Fractions | Ch 8 |
| U9 | Compare Fractions | Ch 9 |
| U10 | Time, Length, Mass | Ch 10 |
| U11 | Perimeter & Area | Ch 11 |
| U12 | Two-Dimensional Shapes | Ch 12 |

### G4 (13 Units)
| Unit | Topic |
|------|-------|
| U1 | Place Value to One Million |
| U2 | Multi-Digit Addition & Subtraction |
| U3 | Multiply by 1-Digit |
| U4 | Multiply by 2-Digit |
| U5 | Divide by 1-Digit |
| U6 | Factors & Multiples |
| U7 | Fraction Equivalence |
| U8 | Add & Subtract Fractions |
| U9 | Multiply Fractions by Whole Numbers |
| U10 | Decimals |
| U11 | 2-D Figures & Angles |
| U12 | Measurement (Perimeter & Area) |
| U13 | Data & Line Plots |

### G5 (11 Units)
| Unit | Topic |
|------|-------|
| U1 | Place Value & Expressions |
| U2 | Multi-Digit Division |
| U3 | Add & Subtract Decimals |
| U4 | Multiply Decimals |
| U5 | Divide Decimals |
| U6 | Add & Subtract Fractions (Unlike Denom) |
| U7 | Multiply Fractions |
| U8 | Divide Fractions |
| U9 | Volume |
| U10 | Coordinate Plane |
| U11 | 2-D Figure Classification |

### G6 (13 Units)
| Unit | Topic |
|------|-------|
| U1 | Whole Numbers & Decimals Review |
| U2 | Fraction Operations Review |
| U3 | Ratios & Rates |
| U4 | Percents |
| U5 | Unit Conversion |
| U6 | Integers & Number Line |
| U7 | Expressions |
| U8 | Equations (One-Variable) |
| U9 | Inequalities |
| U10 | Area |
| U11 | Surface Area & Volume |
| U12 | Data & Statistics |
| U13 | Variability & Data Displays |

---

## Lesson Structure (Per Lesson)

| Stage | Problems | Pass Criteria | Method |
|-------|----------|---------------|--------|
| Pretest | 5 | 5/5 = skip Learn/Try -> R1 | adaptive |
| Learn | 5-8 cards | view all | CPA cards with TTS, static SVG, manipulative interaction |
| Try | 5 | guided (no pass/fail) | 2-level hints, Step-by-Step Solution UI, manipulatives |
| Practice R1 (Basic) | 10 | >= 80% | direct calculation, single-type, answer input only |
| Practice R2 (Mixed) | 10 | >= 80% | T/F, reverse, word problem, drag-sort |
| Practice R3 (Advanced) | 5 | >= 80% (4/5) | multi-step, puzzle, Kangaroo-style |
| Wrong Review | varies | 1 correct = mastered | new similar problems for each wrong item |

**Unit Test**: 20 questions, pass >= 90%, random from all lessons in unit. Fail -> redirected to weak lesson (most errors by lesson tag).

---

## Problem Types

### Type A: Pure Arithmetic (Auto-Generated)
- Template: `{a} {op} {b} = ?`
- Parameters: digit range, regrouping flag, operation
- Unlimited generation via algorithm
- Used in: Fact Fluency, Practice R1, Daily Challenge

### Type B: Word Problems (Template + Variable Substitution)
- Template bank: 50-100 templates per unit
- Variables: names, objects, numbers (within range)
- Expandable via AI (Ollama/Gemini)
- Used in: Practice R2, R3, Unit Test, Daily Challenge

### Type C: Visual/Logic/Pattern (Manual JSON)
- Hand-crafted based on Math Kangaroo patterns
- Includes: shape composition, pattern recognition, data classification, logical reasoning
- Used in: Kangaroo Practice, Practice R3

---

## Problem JSON Schema

### Standard Problem
```json
{
  "id": "u1L2_p1_01",
  "unit": "u1_add_sub_1000",
  "lesson": "L2_addition_strategies",
  "stage": "practice_r1",
  "type": "input | mc | tf | drag_sort | open_pair | open_triple",
  "difficulty": 1-5,
  "concept": "3-digit addition with regrouping",
  "question": "467 + 258 = ?",
  "visual": "description of visual aid or manipulative",
  "options": ["615", "725", "715", "825"],
  "answer": "725",
  "answer_validation": "optional: formula or condition for open-ended",
  "hints": ["hint_1 text", "hint_2 text"],
  "feedback_correct": "Great job! 725 is close to your estimate of 700.",
  "feedback_wrong": "Let's check the ones column: 7+8=15, not 5.",
  "solution_steps": [
    "Ones: 7+8=15, write 5 carry 1",
    "Tens: 6+5+1=12, write 2 carry 1",
    "Hundreds: 4+2+1=7"
  ],
  "tags": ["addition", "regrouping", "3-digit"],
  "three_read": {
    "read1": "optional — story summary",
    "read2": "optional — what to find",
    "read3": "optional — given data"
  }
}
```

### Template Problem (Auto-Gen)
```json
{
  "id": "tpl_add_3digit_regroup",
  "template": "{a} + {b} = ?",
  "variables": {
    "a": {"min": 100, "max": 899, "constraint": "ones_digit >= 5"},
    "b": {"min": 100, "max": 899, "constraint": "ones_digit >= 5"}
  },
  "answer_formula": "a + b",
  "distractor_rules": ["+10", "-10", "no_carry_ones", "swap_digits"],
  "concept": "3-digit addition with regrouping",
  "difficulty": 2
}
```

### Learn Card
```json
{
  "id": "u1L2_learn_01",
  "title": "What is Addition?",
  "type": "concept | example | interactive",
  "cpa_phase": "concrete | pictorial | abstract",
  "content": "Addition means putting groups together...",
  "visual": "animation: two groups of base-ten blocks sliding together",
  "visual_type": "svg | png | manipulative",
  "tts": "Addition means putting groups together to find the total.",
  "interaction": "none | tap | drag | quiz_mini"
}
```

---

## Step-by-Step Solution UI (Try Stage Only)

Since the app runs on MacBook Air (no touchscreen), free-form drawing is not practical. Step-by-Step Solution UI is provided **only in the Try stage** to teach problem-solving process. Practice stages require answer-only input.

### Design

**Example: 467 + 258 using Standard Algorithm**
```
Step 1 — Ones:  7 + 8 = [___]  -> Write [___], Carry [___]
Step 2 — Tens:  6 + 5 + [carried] = [___]  -> Write [___], Carry [___]
Step 3 — Hundreds: 4 + 2 + [carried] = [___]
Answer: [_______]
```

**Example: Word Problem with Bar Model**
```
Read 1: What is this about? [dropdown: stickers / books / marbles]
Read 2: What do we need to find? [dropdown: total / difference / each group]
Read 3: Numbers given: [___] and [___]
Operation: [dropdown: + / - / x / /]
Answer: [___]
```

**Strategy Selection (Try stage)**
```
"Choose your strategy:"
  - Break Apart (Expanded Form)
  - Number Line Jumps
  - Standard Algorithm
-> Selected strategy shows corresponding step-by-step UI
```

### Future Enhancement
- iPad version: add Apple Pencil scratchpad overlay
- Handwriting recognition for free-form math input

---

## Virtual Manipulatives (Learn + Try Stages Only)

All 5 types are interactive with drag-and-drop (mouse/trackpad compatible).

| Manipulative | Used For | Grades |
|-------------|----------|--------|
| Base Ten Blocks | Place value, addition/subtraction with regrouping | G3-G4 |
| Number Line | Addition, subtraction, fractions, decimals | G3-G6 |
| Array Grid | Multiplication, division concepts | G3-G4 |
| Fraction Bars | Fraction comparison, equivalence, operations | G3-G6 |
| Bar Model Builder | Word problems, part-whole relationships | G3-G6 |

**Stage Rules**:
- **Learn**: Manipulatives embedded in CPA concept cards (interactive)
- **Try**: Manipulatives available as tools while solving guided problems
- **Practice**: Not available. On wrong answer, feedback includes Pictorial image (static, not interactive) per Pillar 4 CPA Fallback
- **Wrong Review / Unit Test**: Not available

---

## Fact Fluency Module

### Structure
- 60-second timed rounds
- 3 rounds per daily session
- Phase progression per fact set:
  - Phase A: Untimed (understand) — must get 10/10 correct
  - Phase B: Gentle timer (10s/problem) — must get 10/10
  - Phase C: Speed (5s/problem) — track speed + accuracy, mastery at 95%+

### Fact Sets (G3 Focus)
1. Addition facts to 20 (review)
2. Subtraction facts to 20 (review)
3. Multiplication x2, x5, x10 (intro)
4. Multiplication x3, x4
5. Multiplication x6, x7
6. Multiplication x8, x9
7. Division facts (inverse of above)
8. Mixed operations

### XP
- Complete 3 rounds: +3 XP/day
- New personal best: +2 XP bonus
- Fact set mastered (Phase C, 95%+ accuracy): +5 XP + badge

---

## Daily Challenge Module

### Structure
- 5-10 mixed problems daily
- Composition: 50% current unit + 30% spaced review (wrong items from days 1,3,7,21 ago) + 20% spiral (random from completed units)
- No time pressure
- Immediate feedback with CPA fallback (Pictorial image, not interactive manipulative)

### XP
- Complete daily challenge: +5 XP
- All correct: +3 XP bonus

---

## Kangaroo Practice Module

### Structure
- Weekly sets: 5 problems per set, 2-3 sets per week
- Difficulty: mirrors Math Kangaroo Pre-Ecolier / Ecolier level
- Categories: Logical Thinking, Geometry, Arithmetic, Pattern/Function, Data/Probability
- No time pressure, encourage multiple solution strategies
- **All problems must be based on actual Math Kangaroo past problems**
  - Direct use or pattern-based variations
  - Source attribution: "Based on MK [year] [level] #[number]"
  - Sources: mathkangaroo.org, matematica.pt, mathkangaroo.in

### XP
- Complete a set: +5 XP
- All correct in a set: +5 XP bonus

---

## My Problems Module

### Structure
- Auto-collects all wrong answers from all modules
- **Phase 1 (M1-M5)**: All errors treated as `concept_gap`, mastered after 1 correct on similar problem
- **Phase 2+ (future)**: Auto-tag error types with differential mastery:
  - `careless`: 1 correct = mastered (same concept previously correct + fast response + near-miss answer)
  - `concept_gap`: 2 consecutive correct = mastered (same concept failed multiple times)
  - `reading_error`: Word problem only (calculation correct but wrong answer due to misreading)
  - `timeout`: Fact Fluency time expiry
- Groups by concept/skill (e.g., "Regrouping in subtraction", "Fraction comparison")
- Generates new similar problems for each wrong item
- Spaced repetition schedule: day 1, 3, 7, 21

### Parent Dashboard View
- Shows weak areas chart
- Shows error type distribution (pie chart) — Phase 2+ only
- Shows improvement trend over time

---

## Placement Test Design

### Trigger
- First time Math tab is clicked
- Parent can reset from Parent Dashboard

### Structure
- 15-20 questions, adaptive (CAT-style)
- Starts at estimated grade level (G3 for GIA)
- Correct -> harder question; Wrong -> easier question
- Covers all 5 Common Core domains:
  - Operations & Algebraic Thinking
  - Number & Operations in Base Ten
  - Number & Operations — Fractions
  - Measurement & Data
  - Geometry

### Output
- Per-domain level: e.g., "Operations: G3.5, Fractions: G3.0, Geometry: G4.0"
- Academy auto-configures starting units per domain
- Results saved to DB, visible in Parent Dashboard
- Estimated MAP RIT displayed (approximate)

---

## XP Rules (Math — added to shared system)

| Action | XP | Limit |
|--------|-----|-------|
| Practice problem correct | +1 | per problem |
| Lesson complete (all stages passed) | +10 | once/lesson |
| Unit Test pass | +15 | once/unit |
| Daily Challenge complete | +5 | once/day |
| Daily Challenge all correct | +3 | once/day |
| Fact Fluency 3 rounds | +3 | once/day |
| Fact Fluency personal best | +2 | per occurrence |
| Fact set mastered (Phase C 95%+) | +5 | once/fact set |
| Kangaroo set complete | +5 | once/set |
| Kangaroo set all correct | +5 | once/set |

No XP for: Pretest, Learn cards, failed tests (retry pass = full XP)

---

## Streak Rules (Updated — Shared with English)

- **Default**: English AND Math activity both required to maintain streak
  - English: Review + Daily Words (existing rules)
  - Math: Daily Challenge OR Fact Fluency OR Academy lesson
- **Parent configurable** via Parent Dashboard:
  - `both` (default): English AND Math required
  - `english_only`: Only English activity required
  - `math_only`: Only Math activity required
  - `either`: English OR Math activity sufficient
- Approved Day Off -> streak frozen (maintained) — applies to both subjects
- Stored in `task_settings` table as `streak_condition` key

---

## Database Schema (New Math Tables)

> **Design Decision**: Math tables are completely separate from English tables. Rationale: English is word-based (word/definition/example), Math is problem-based (question/solution_steps/error_type) — fundamentally different schemas. Only XP (`xp_logs`) and Streak (`streak_logs`) are shared.

### math_placement_results
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| test_date | String | YYYY-MM-DD |
| domain | String | "operations", "base_ten", "fractions", "measurement", "geometry" |
| estimated_grade | String | e.g., "G3.5" |
| rit_estimate | Integer | approximate MAP RIT |
| raw_score | Integer | |
| total_questions | Integer | |
| detail_json | String | JSON: per-question results |

### math_problems
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| problem_id | String UNIQUE | e.g., "u1L2_p1_01" |
| grade | String | "G3" |
| unit | String | "u1_add_sub_1000" |
| lesson | String | "L2_addition_strategies" |
| stage | String | "pretest/learn/try/practice_r1/r2/r3" |
| type | String | "input/mc/tf/drag_sort/open_pair" |
| difficulty | Integer | 1-5 |
| concept | String | |
| question_json | String | Full problem JSON |
| tags_json | String | JSON array of tags |
| is_active | Boolean | default True, for soft delete |

### math_progress
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| grade | String | |
| unit | String | |
| lesson | String | |
| stage | String | current stage |
| is_completed | Boolean | |
| pretest_score | Integer | nullable |
| pretest_passed | Boolean | True if 5/5 |
| pretest_skipped | Boolean | True if skipped via pretest |
| best_score_r1 | Integer | |
| best_score_r2 | Integer | |
| best_score_r3 | Integer | |
| unit_test_score | Integer | nullable |
| unit_test_passed | Boolean | default False |
| attempts | Integer | total attempts |
| last_accessed | String | ISO 8601 |

### math_attempts
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| problem_id | String FK -> math_problems.problem_id | |
| grade | String | |
| unit | String | |
| lesson | String | |
| stage | String | |
| is_correct | Boolean | |
| user_answer | String | |
| error_type | String | Phase 1: always "concept_gap". Phase 2+: "careless/concept_gap/reading_error/timeout/none" |
| time_spent_sec | Integer | |
| attempted_at | String | ISO 8601 |

### math_wrong_review
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| problem_id | String FK | |
| original_attempt_id | Integer FK -> math_attempts.id | |
| next_review_date | String | YYYY-MM-DD |
| interval_days | Integer | 1, 3, 7, 21 |
| times_reviewed | Integer | |
| is_mastered | Boolean | Phase 1: 1 correct = True |

### math_fact_fluency
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| fact_set | String | "mult_2", "mult_3", etc. |
| current_phase | String | "A/B/C" |
| best_score | Integer | |
| best_time_sec | Integer | |
| accuracy_pct | Float | for Phase C mastery check (95%+) |
| total_rounds | Integer | |
| last_played | String | ISO 8601 |

### math_daily_challenge
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| challenge_date | String | YYYY-MM-DD |
| problems_json | String | JSON array of problem_ids |
| score | Integer | |
| total | Integer | |
| completed | Boolean | |

### math_kangaroo_progress
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| set_id | String | e.g., "kangaroo_week12_set1" |
| category | String | "logic/geometry/arithmetic/pattern/data" |
| difficulty_level | String | "pre_ecolier" / "ecolier" |
| score | Integer | |
| total | Integer | |
| completed_at | String | nullable |

### Existing Table Modifications (Migration 002)

**streak_logs** — add column:
| Column | Type | Notes |
|--------|------|-------|
| math_done | Boolean | default False |

**task_settings** — add row:
| task_key | is_required | xp_value | is_active |
|----------|-------------|----------|-----------|
| streak_condition | — | — | True |

Store `streak_condition` value ("both"/"english_only"/"math_only"/"either") in a new `config_value` column or use `AppConfig` table.

---

## API Endpoints

### Academy
```
GET  /api/math/academy/grades
GET  /api/math/academy/{grade}/units
GET  /api/math/academy/{grade}/{unit}/lessons
GET  /api/math/academy/{grade}/{unit}/{lesson}/pretest
GET  /api/math/academy/{grade}/{unit}/{lesson}/learn
GET  /api/math/academy/{grade}/{unit}/{lesson}/try
GET  /api/math/academy/{grade}/{unit}/{lesson}/practice/{round}
POST /api/math/academy/submit-answer
GET  /api/math/academy/{grade}/{unit}/unit-test
POST /api/math/academy/unit-test/submit
```

### Placement
```
GET  /api/math/placement/status
POST /api/math/placement/start
POST /api/math/placement/submit-answer
GET  /api/math/placement/results
```

### Fact Fluency
```
GET  /api/math/fluency/status
POST /api/math/fluency/start-round
POST /api/math/fluency/submit-answer
GET  /api/math/fluency/summary
```

### Daily Challenge
```
GET  /api/math/daily/today
POST /api/math/daily/submit-answer
```

### Kangaroo
```
GET  /api/math/kangaroo/sets
GET  /api/math/kangaroo/set/{set_id}
POST /api/math/kangaroo/submit-answer
```

### My Problems (Wrong Review)
```
GET  /api/math/my-problems/summary
GET  /api/math/my-problems/review
POST /api/math/my-problems/submit-answer
```

---

## Frontend Integration

### Script Loading Order (child.html — Math files added after English)
```html
<!-- ... existing English scripts ... -->

<!-- Math modules -->
<script src="/static/js/math-navigation.js?v=1"></script>
<script src="/static/js/math-academy.js?v=1"></script>
<script src="/static/js/math-learn-cards.js?v=1"></script>
<script src="/static/js/math-problem-ui.js?v=1"></script>
<script src="/static/js/math-step-solver.js?v=1"></script>
<script src="/static/js/math-manipulatives.js?v=1"></script>
<script src="/static/js/math-fluency.js?v=1"></script>
<script src="/static/js/math-kangaroo.js?v=1"></script>
<script src="/static/js/math-problems.js?v=1"></script>
<script src="/static/js/math-daily.js?v=1"></script>
<script src="/static/js/math-glossary.js?v=1"></script>
```

### CSS Files
```html
<link rel="stylesheet" href="/static/css/math-academy.css?v=1">
<link rel="stylesheet" href="/static/css/math-fluency.css?v=1">
<link rel="stylesheet" href="/static/css/math-kangaroo.css?v=1">
<link rel="stylesheet" href="/static/css/math-problems.css?v=1">
<link rel="stylesheet" href="/static/css/math-manipulatives.css?v=1">
```

### CSS Naming Convention
- All Math CSS classes use `.math-*` prefix
- Example: `.math-card`, `.math-sidebar`, `.math-manipulative-area`
- Uses `var(--token)` from theme.css only — no hard-coded hex values

### DOM Integration
- `#stage-area` reused for Math content
- `renderMathStage()` function replaces `renderStage()` when in Math mode
- `setSubject('math')` already wired in navigation.js — toggles `body.math-mode` class
- Math sidebar content replaces English sidebar content on tab switch

---

## Parent Dashboard — Math Section

Added as a tab/filter within existing Parent Dashboard (`/api/parent/*`):

### Overview Tab (Math)
- Current grade/unit/lesson progress
- Placement Test results (per-domain levels)
- Estimated MAP RIT trend
- Weekly study time (minutes)
- Weekly problems solved count

### Performance Tab (Math)
- Score trend per unit (line chart)
- Domain strength radar chart (5 axes: Operations, Base Ten, Fractions, Measurement, Geometry)
- Error type distribution (Phase 2+ only)
- Weak concept list with recommended lessons

### Fact Fluency Tab (Math)
- Fact set progress (Phase A/B/C per set)
- Speed trend chart
- Facts not yet mastered list

### Kangaroo Tab (Math)
- Category scores over time
- Comparison with Math Kangaroo percentile benchmarks

### Streak Configuration
- Setting: "Streak Condition" dropdown
  - Both subjects (default)
  - English only
  - Math only
  - Either subject

---

## Content Creation Workflow

1. **User prepares** Go Math textbook-based materials (problems, concepts, visual descriptions)
2. **JSON conversion** — manual input or Claude-assisted formatting into Problem JSON Schema
3. **Gap filling** — Claude generates additional problems via templates, following grade-level number/operation ranges strictly
4. **Review** — User verifies against Go Math textbook for accuracy, difficulty alignment
5. **Kangaroo content** — must be based on actual Math Kangaroo past problems with source attribution
6. **Quality checks** before commit:
   - Correct answers verified
   - No duplicate options
   - Difficulty matches grade level
   - Number ranges within grade constraints (e.g., G3 multiplication: 1-digit x 1-digit only)

---

## Data Quality & Verification Principles

1. All concept explanations and problems aligned to Common Core State Standards + Go Math textbook
2. Teaching methods use only research-validated approaches: CPA, bar models, number lines (no ad-hoc inventions)
3. Kangaroo Practice must be based on actual Math Kangaroo past problems
   - Direct use or pattern-based variations
   - Source attribution: "Based on MK [year] [level] #[number]"
   - Sources: mathkangaroo.org, matematica.pt, mathkangaroo.in
4. Word problems reference Go Math textbook problem types/difficulty
5. Auto-generated problems strictly follow grade-level number/operation ranges
   - Example: G3 multiplication is single-digit x single-digit only; G4 introduces two-digit x one-digit
6. All problems verified after creation: correct answers, no duplicate options, difficulty alignment

---

## File Structure

```
NSS_Word_Master/
├── MATH_SPEC.md
├── backend/
│   ├── routers/
│   │   ├── math_academy.py       # /api/math/academy/*
│   │   ├── math_practice.py      # /api/math/practice/*
│   │   ├── math_placement.py     # /api/math/placement/*
│   │   ├── math_fluency.py       # /api/math/fluency/*
│   │   ├── math_daily.py         # /api/math/daily/*
│   │   ├── math_kangaroo.py      # /api/math/kangaroo/*
│   │   └── math_problems.py      # /api/math/my-problems/*
│   ├── services/
│   │   ├── math_engine.py        # Problem generation, template engine, auto-gen
│   │   ├── math_adaptive.py      # Placement test CAT logic, difficulty adjustment
│   │   └── math_spaced.py        # Spaced repetition for wrong items
│   ├── data/
│   │   └── math/
│   │       ├── G3/
│   │       │   ├── U1_add_sub_1000/
│   │       │   │   ├── L1_rounding_estimation.json
│   │       │   │   ├── L2_addition_strategies.json
│   │       │   │   ├── L3_subtraction_strategies.json
│   │       │   │   ├── L4_word_problems.json
│   │       │   │   └── unit_test.json
│   │       │   ├── U2_data_graphs/
│   │       │   └── ...
│   │       ├── G4/
│   │       ├── G5/
│   │       ├── G6/
│   │       ├── fact_fluency/
│   │       ├── kangaroo/
│   │       └── placement/
│   └── migrations/
│       └── 002_add_math_tables.py
├── frontend/
│   └── static/
│       ├── css/
│       │   ├── math-academy.css
│       │   ├── math-fluency.css
│       │   ├── math-kangaroo.css
│       │   ├── math-problems.css
│       │   └── math-manipulatives.css
│       └── js/
│           ├── math-navigation.js     # Math sidebar, grade/unit/lesson dropdowns
│           ├── math-academy.js        # Pretest, Learn, Try, Practice, Wrong Review
│           ├── math-learn-cards.js    # CPA card renderer with static SVG + TTS
│           ├── math-problem-ui.js     # Problem type renderers (MC, input, TF, drag)
│           ├── math-step-solver.js    # Step-by-step solution UI (Try stage only)
│           ├── math-manipulatives.js  # Virtual manipulatives (all 5 types, Learn+Try only)
│           ├── math-fluency.js        # Fact Fluency timer + rounds
│           ├── math-kangaroo.js       # Kangaroo Practice UI
│           ├── math-problems.js       # My Problems (wrong review)
│           ├── math-daily.js          # Daily Challenge
│           └── math-glossary.js       # Math term popup definitions
```

---

## Problem Count Estimates (Per Grade)

| Category | Per Unit | G3 (12 units) | Method |
|----------|----------|---------------|--------|
| Learn cards | 5-8 x 4 lessons | ~288 | Manual |
| Try (guided) | 5 x 4 lessons | ~240 | Mixed |
| Practice R1 | 10 x 4 lessons | ~480 | Template + Manual |
| Practice R2 | 10 x 4 lessons | ~480 | Template + Manual |
| Practice R3 | 5 x 4 lessons | ~240 | Manual |
| Unit Test | 20 | ~240 | Random from bank |
| **Fixed total** | | **~1,968** | |
| Fact Fluency | unlimited | infinite | Algorithmic |
| Daily Challenge | unlimited | infinite | Algorithmic + Spaced |
| Kangaroo | ~25/grade | ~100+ | Manual (MK-based) |

**G3-G6 total fixed problems: ~8,000+**
Plus unlimited auto-generated: Fact Fluency + Daily Challenge

---

## Sample Data Created (G3 Unit 1)

- **Lesson 1: Rounding & Estimation** — Complete
  - Pretest (5), Learn (7 cards), Try (5), Practice R1 (10), Practice R2 (10)
- **Lesson 2: Addition Strategies** — Complete
  - Pretest (5), Learn (8 cards), Try (5), Practice R1 (10), Practice R2 (10), Practice R3 (5)
- **Lesson 3: Subtraction Strategies** — Not started
- **Lesson 4: Word Problem Solving** — Not started

---

## Implementation Phases (Priority Order)

```
Phase 1: M1 -> M3 -> M4 (Core Learning Flow)
  M1:  DB migration + API skeleton + Math sidebar toggle
  M3:  Academy Learn cards (static SVG + TTS + manipulative interaction)
  M4:  Practice R1-R3 + problem type renderers + Wrong Review (basic)

Phase 2: M5 -> M6 (Learning Effectiveness)
  M5:  Wrong Review enhancement + My Problems + spaced repetition (day 1,3,7,21)
  M6:  Fact Fluency module (3 phases, timed rounds)

Phase 3: M2 -> M10 -> M11 (User Experience)
  M2:  Placement Test (CAT adaptive logic + UI)
  M10: Virtual Manipulatives (all 5 types, interactive drag-and-drop)
  M11: Step-by-Step Solution UI (Try stage)

Phase 4: M7 -> M8 -> M9 (Daily Learning + Management)
  M7:  Daily Challenge (50% current + 30% spaced + 20% spiral)
  M8:  Kangaroo Practice (MK-based problems)
  M9:  Parent Dashboard Math integration

Phase 5: M12 -> M15 -> M16 (Content + Extras)
  M12: Math Glossary + 3-Read Strategy UI
  M15: G3 full problem bank (all 12 units)
  M16: G4-G6 problem banks

Phase 6: M13 -> M14 (Polish)
  M13: Animations (Lottie/Rive) — upgrade Learn card CPA transitions
  M14: Offline mode
```

### Phase Dependencies
```
M1 is prerequisite for all others
M3 requires M1
M4 requires M3
M5 requires M4
M6 requires M1 (independent of M3-M5)
M7 requires M4 + M5
M8 requires M1 (independent)
M9 requires M4
M10 requires M3 (enhances Learn/Try)
M11 requires M4 (enhances Try)
M12 requires M3
M13 requires M10
M14 requires M4
M15 requires M4
M16 requires M15
```

---

## GIA Profile (For Adaptive Design)

- **Current Grade**: G2 (entering G3 Fall 2026)
- **MAP Math RIT**: 205 (94th percentile) — G3-high / G4-average level
- **MAP Reading RIT**: 199 (90th percentile)
- **MAP Language RIT**: 198 (89th percentile)
- **Math Kangaroo Pre-Ecolier**: 79/96 (82%)
  - Logic: 100%, Geometry: 83%, Operations: 83%, Pattern: 75%, Data: 75%
- **Strengths**: Logical reasoning, basic arithmetic
- **Growth Areas**: Pattern recognition, data classification, geometry composition
- **Next Event**: Math Kangaroo Round 2 (May 30, 2026)
- **Language**: English (native), Korean (family)

---

*Document version: 2026-04-17 — Planning Phase (finalized via Q&A review)*
*To be updated as implementation progresses.*
