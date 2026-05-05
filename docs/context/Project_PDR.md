# Project Design Reference — SuperNoteOrganiser

> **Version:** 1.0
> **Last Updated:** 2026-05-05
> **Status:** Prototype — single-user, local-only

---

## 1. Project Overview

**SuperNoteOrganiser** is a Streamlit prototype agent that ingests scattered notes captured across `.txt` and `.md` files (often on different devices at different times), groups them by heading / tag / category, dedupes near-duplicates via fuzzy title + body cosine matching, annotates each surviving note with an **Action / Why / Purpose** block reasoned out by Claude, and emits a Karpathy-style Markdown wiki ready to read or commit.

**Problem it solves:** A frequent dumping ground (phone notes, scratch markdown, hand-typed paragraphs) is a low-friction capture surface but a high-friction reading surface. Without structure, recall fails. Without dedupe, the same idea written three times pollutes search. Without action framing, half the notes turn into wishful-thinking artefacts. The pipeline turns raw capture into a navigable wiki where each idea has one canonical entry, an explicit action, and a "why".

**Audience:** A single user (the maintainer). The prototype assumes file-on-disk notes, no multi-tenancy, no user auth — and intentionally so. The architecture is modular enough that any of those assumptions could be swapped without rewriting the pipeline.

**Current state:** Bootstrapped on Claude Code on phone, pulled to Mac, kit applied. One commit on `main` (the prototype itself); kit installation is the next commit.

---

## 2. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | >=3.11 |
| UI | Streamlit | >=1.32 |
| LLM | Anthropic SDK (`anthropic`) | >=0.39 |
| Default model | `claude-sonnet-4-6` (configurable via `NOTE_ORGANISER_MODEL`) | — |
| Models | Pydantic | >=2.6 |
| Markdown | `markdown-it-py` + `python-frontmatter` | >=3.0 / >=1.1 |
| Fuzzy matching | `rapidfuzz` | >=3.6 |
| Env loading | `python-dotenv` | >=1.0 |
| Persistence | JSON file on disk (`state/notes.json` via `JsonFileStore`) | — |
| Build backend | `setuptools>=68` | — |
| Test framework | `pytest` (not yet wired — first test lands with the first feature that needs it) | — |

**Runtime requirement:** Python 3.11+. `pip install -e .` installs the package and registers a `note-organiser` console script that boots Streamlit.

---

## 3. System Architecture

```
                      ┌──────────────┐
   notes/*.txt   ───► │   Splitter   │ ───► RawChunk[]
   notes/*.md         └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │  Annotator   │ ───► Note (with Action/Why/Purpose)
                      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │   Deduper    │ ───► NoteGroup[]
                      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │  Annotator   │ ───► Note  (merge for non-singleton groups)
                      │   .merge()   │
                      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │    Store     │ ───► state/notes.json   (skip seen-by-content-hash)
                      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │   Renderer   │ ───► wiki/*.md  (Karpathy-style)
                      └──────────────┘
```

**Key architectural notes:**
- Every stage is a `typing.Protocol` declared in `note_organiser/interfaces.py`. The orchestrator (`pipeline.py`) depends on the Protocols, never on concrete impls.
- Wiring lives in exactly one place: `config.py::build_pipeline()`. To swap a backend (e.g. swap `JsonFileStore` for SQLite or replace `FuzzyTitleDeduper` with embeddings cosine), write a class that satisfies the Protocol and edit `build_pipeline`. Nothing else changes.
- Content-hash-based seen-tracking (`models.content_hash`) means re-running on the same `notes/` folder is idempotent — only new or changed notes are processed.
- Prompt caching is on by default in `ClaudeAnnotator` (Anthropic SDK supports it natively for Sonnet 4.6).

---

## 4. Repository Structure

```
SuperNoteOrganiser/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── CLAUDE.md                          ← added by /init
├── .claude/
│   └── agents/
│       ├── testing-agent.md
│       ├── code-quality-agent.md
│       ├── context-docs-agent.md
│       └── docs-auditor-agent.md
├── docs/
│   ├── README.md                      ← kit's universal setup guide
│   ├── CLAUDE_SNIPPET.md              ← customized for this project
│   ├── prompts/                       ← universal workflow prompts
│   ├── context/                       ← 7 context files (this is where this PDR lives)
│   └── prd/, ard/, architecture/,
│       plans/, bugs/, testing-agents/ ← .gitkeep only until per-feature files land
├── note_organiser/
│   ├── __init__.py
│   ├── app.py                         ← Streamlit entry
│   ├── config.py                      ← AppConfig + build_pipeline()
│   ├── interfaces.py                  ← Protocol contracts
│   ├── models.py                      ← Pydantic models + content_hash
│   ├── pipeline.py                    ← orchestrator
│   ├── prompts.py                     ← Claude prompt templates
│   ├── splitters/
│   ├── annotators/                    ← claude.py + stub.py
│   ├── dedupers/
│   ├── stores/                        ← jsonfile.py
│   └── renderers/                     ← karpathy_wiki.py
├── notes/                             ← user input (sample files ship)
├── wiki/                              ← generated output (.gitignored except .gitkeep)
└── state/                             ← persistence (.gitignored except .gitkeep)
```

**Route protection:** N/A — no HTTP routes. The Streamlit app runs locally and is intended for the maintainer alone.

---

## 5. Key Architectural Patterns

### Pattern: Protocol-first stage definition
- **What:** Every pipeline stage is a `typing.Protocol` (`Splitter`, `Annotator`, `Deduper`, `Store`, `Renderer`). The orchestrator imports only from `interfaces.py`.
- **Where used:** `note_organiser/interfaces.py`, `note_organiser/pipeline.py`, every `*/__init__.py` under `note_organiser/`.
- **Why:** Lets new backends drop in without touching the orchestrator. Concrete impls are independently swappable and independently testable.

### Pattern: Single-place wiring (`config.py::build_pipeline`)
- **What:** All concrete-class instantiation happens in one function. Nothing else in the codebase calls a concrete backend constructor.
- **Where used:** `note_organiser/config.py`. Streamlit (`app.py`) and any future CLI/test harness call `build_pipeline(AppConfig.from_env())`.
- **Why:** Changing a default impl is a one-line edit. Reading wiring is trivial — there's one place to look.

### Pattern: Content-hash-based idempotency
- **What:** Each `RawChunk` has a `note_id` derived from `content_hash(text)` (sha256 of normalised text, truncated to 12 chars). The store skips already-seen ids.
- **Where used:** `note_organiser/models.py::content_hash`, `JsonFileStore.seen()`.
- **Why:** Re-running on the same notes folder is safe and cheap. Edited notes get a new id and re-process; untouched notes don't.

### Pattern: Stub backends for offline tests
- **What:** Every external-dependency Protocol has a stub impl (`StubAnnotator` for Anthropic; the markdown/paragraph splitters are deterministic and need no stub). Setting `NOTE_ORGANISER_ANNOTATOR=stub` runs the entire pipeline with no API calls.
- **Where used:** `note_organiser/annotators/stub.py`, `note_organiser/config.py::_build_annotator`.
- **Why:** Tests and demos work without an API key and without burning credits. Pipeline shape is verifiable in isolation from the LLM.

### Pattern: Devices-attribution preserved through merge
- **What:** When the deduper groups multiple `Note`s into a `NoteGroup` and the Annotator merges them, the original device-attributed snippets are preserved on `Note.versions`.
- **Where used:** `note_organiser/models.py::Note`, `note_organiser/annotators/claude.py::merge`.
- **Why:** The merged note is the canonical entry, but the original phrasings (often device-specific — "phone note vs laptop note") stay as evidence. Important for trust when the wiki is reviewed.

---

## 6. Feature Status

The roadmap lives in `docs/context/PRODUCTION_READY.md` (which doubles as the epics tracker). Top-level summary:

| # | Item | Status |
|---|------|--------|
| 1 | Bootstrap pipeline + Streamlit app | Done (initial commit) |
| 2 | Apply AI Dev Workflow Kit + customize | In progress (this session) |
| 3 | Add CLAUDE.md via /init + push to GitHub | Pending |
| 4 | First test suite (pytest) covering models + JsonFileStore + fuzzy deduper | Not started |
| 5 | Quality polish: dead-code sweep, type hints audit, prompt-caching verification | Not started |
| 6 | Real on-device usage on the maintainer's notes corpus | Not started |

---

## 7. Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Required for `ClaudeAnnotator`. Not needed when `NOTE_ORGANISER_ANNOTATOR=stub`. |
| `NOTE_ORGANISER_MODEL` | Claude model id. Default `claude-sonnet-4-6`. |
| `NOTE_ORGANISER_ANNOTATOR` | `claude` (default) or `stub` (offline). |

`config.py::AppConfig.from_env` calls `dotenv.load_dotenv(override=False)` so a `.env` at the repo root is honoured but doesn't clobber explicit shell exports.

---

## 8. Development Commands

| Command | Purpose |
|---------|---------|
| `pip install -e .` | Editable install — also doubles as the `code-quality-agent`'s "build" check |
| `streamlit run note_organiser/app.py` | Start the Streamlit dev server (default `http://localhost:8501`) |
| `note-organiser` | Console-script entry (calls `note_organiser.app:cli_run`) |
| `pytest` | Run the test suite (none exists yet — first feature that needs it adds the harness). Note: `pytest` does NOT default to watch mode, so this is safe. |
| `pytest -q tests/test_models.py` | Single test file, quiet — what `code-quality-agent` step 5.9 uses |
| `grep -rn "print(\|pdb\.set_trace\|breakpoint()" note_organiser/` | The kit's debug-statement sweep (step 5.6) |
| `NOTE_ORGANISER_ANNOTATOR=stub streamlit run note_organiser/app.py` | Run the full pipeline offline (no API key needed) — useful for UI testing |

**Testing note:** pytest runs once and exits by default — there is no watch-mode trap to avoid (unlike vitest in the universal kit's warning). Still, the `code-quality-agent` only runs targeted test files, never the full suite without parent-agent approval.

---

## 9. Key Reference Documents

| Document | Purpose |
|----------|---------|
| `README.md` (root) | Front door for GitHub visitors; install + Quick start + Architecture |
| `CLAUDE.md` (root) | AI agent instructions (added by `/init`, augmented from `docs/CLAUDE_SNIPPET.md`) |
| `docs/context/Context_Index_File.md` | Master file catalog |
| `docs/context/database_reference_guide.md` | `Note` model + JsonFileStore schema |
| `docs/context/API_REFERENCE.md` | Protocol contracts (extension API) |
| `docs/context/CHANGELOG.md` | Chronological change history |
| `docs/context/PRODUCTION_READY.md` | Roadmap, release criteria, known bugs |
