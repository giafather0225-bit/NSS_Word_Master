# NSS Word Master — GIA Learning App

A single-user learning app for children covering **English vocabulary** (5-stage lesson flow with AI scoring) and **Math** (Academy, Daily Challenge, Fact Fluency, Placement, Kangaroo practice, Glossary, Wrong-Problem review). XP, streaks, reward shop, parent dashboard, and growth themes round out the experience.

**Phases 1–10 complete.** See [`CLAUDE.md`](CLAUDE.md) for the full project spec.

---

## Tech Stack

- **Backend**: Python / FastAPI (`backend/routers/`)
- **Frontend**: HTML + CSS + Vanilla JS (no bundler)
- **Database**: SQLite WAL at `~/NSS_Learning/database/voca.db`
- **AI**: Ollama (`gemma2:2b`, local) with Gemini fallback
- **TTS**: edge-tts (in-memory BytesIO → Blob)
- **Speech recognition**: Web Speech API

---

## Install & Run

```bash
# 1. Clone + install
git clone https://github.com/giafather0225-bit/NSS_Word_Master.git
cd NSS_Word_Master
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure (optional — see .env.example)
cp .env.example .env

# 3. Run migrations (first-time setup)
cd backend && python3 migrations/001_add_new_tables.py
cd ..

# 4. Start the server
python3 app.py
# → http://localhost:8000
```

Ollama must be running locally for AI features (`ollama serve`); otherwise the app falls back to Gemini if `GEMINI_API_KEY` is configured.

---

## Project Layout

```
NSS_Word_Master/
├── CLAUDE.md                  # Project spec (work principles, phases, schema)
├── MATH_SPEC.md               # Math module spec (detailed)
├── API_INDEX.md               # ★ Math API reference (this doc tree)
├── README.md                  # You are here
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── database.py            # SQLite engine + get_db()
│   ├── models.py              # SQLAlchemy models (23 tables)
│   ├── routers/               # All HTTP endpoints (split by domain)
│   ├── services/              # XP, streak, academy session, backup, etc.
│   ├── data/                  # Content: lessons, daily words, kangaroo, glossary
│   ├── migrations/            # Idempotent schema migrations
│   ├── API_INDEX.md           # Full endpoint index (English + Math + System)
│   └── DB_INDEX.md            # SQLAlchemy model reference
└── frontend/
    ├── templates/child.html   # Main SPA entry
    └── static/                # css/ + js/ + img/
```

---

## API Documentation

- **[`API_INDEX.md`](API_INDEX.md)** — full Math API reference: 40+ endpoints across 7 routers (Academy, Daily Challenge, Fluency, Placement, Kangaroo, Glossary, My Problems). Includes request/response schemas, XP rules, error formats, caching behavior.
- [`backend/API_INDEX.md`](backend/API_INDEX.md) — condensed table of *all* endpoints (English + Math + System) with "defined in" / "called from" mapping.
- [`backend/DB_INDEX.md`](backend/DB_INDEX.md) — database schema reference.

---

## Work Principles

Short list (full version in [`CLAUDE.md`](CLAUDE.md)):

1. Read existing code before modifying — never break shipped features.
2. Max 300 lines per file — split into modules when approaching the limit.
3. CSS uses `theme.css` variables only — no hard-coded hex colors.
4. All API endpoints: proper error handling + correct HTTP status codes.
5. DB schema changes must ship with an idempotent migration.
6. Python: type hints + docstrings. JS: JSDoc `@tag` comments on every function.
7. No N+1 queries. Use indexes. `async/await` consistently.
8. Sanitize every user input. Prompt-injection defense on AI calls.
9. After any change: smoke-test 5-Stage learning, Review, Final Test, Unit Test, Word Manager.
10. UI text in English only. Apple-minimal design — no gradients, no heavy shadows.

---

## Quick References

```bash
# Find functions by tag
grep -r "@tag XP" .

# List all registered endpoints
grep -rn "router\." backend/routers/

# DB status
sqlite3 ~/NSS_Learning/database/voca.db ".tables"

# Run tests
cd backend && pytest
```

---

## License

Private project. GitHub: https://github.com/giafather0225-bit/NSS_Word_Master
