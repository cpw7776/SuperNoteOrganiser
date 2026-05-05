# Context Files Index — SuperNoteOrganiser

## Quick Reference to Key Context Documents

This index is the master file catalog for **SuperNoteOrganiser** — a Streamlit prototype agent that ingests scattered `.txt` and `.md` notes, annotates each with an Action / Why / Purpose block via Claude, dedupes near-duplicates, and emits a Karpathy-style Markdown wiki. Single-user, file-on-disk, no real DB or HTTP API.

This file is the project-level source of truth for "where does X live" — every other doc points back here. Keep it current: every new file added to the project must appear here.

---

## Sources of Truth

### Project-Level Source of Truth — `docs/context/` (7 files)

These are **authoritative**. When in doubt, trust these over comments, memory, or assumptions. Skipping even one update on a feature is a common failure mode — the `context-docs-agent` enforces this in Phase 5.5a.

| File | Covers | Update when... |
|------|--------|---------------|
| `Context_Index_File.md` | All files in the project | Any file added, renamed, or removed anywhere |
| `database_reference_guide.md` | The JSON file store schema (`state/notes.json`), the `Note` Pydantic model, on-disk layout under `state/` | The `Note` model changes, the store schema changes, or `state/` layout changes |
| `API_REFERENCE.md` | The Protocol contracts in `note_organiser/interfaces.py` (Splitter, Annotator, Deduper, Store, Renderer) — the project's "extension API" | A Protocol changes shape, a new Protocol is added, or a new concrete impl is registered in `config.py::build_pipeline` |
| `CHANGELOG.md` | Feature history | **Always** — every feature and fix |
| `PRODUCTION_READY.md` | Roadmap, milestone status, known bugs, doubles as the project's epics tracker | Status changes, items completed, bugs added/resolved |
| `Project_Authentication.md` | **N/A** for this prototype (no user auth, only `ANTHROPIC_API_KEY` env-var) — kept as universal template stub | Never (read & confirm still N/A on each Phase 5.5a run) |
| `Project_PDR.md` | Project design rationale, conventions, scope, architectural patterns | Architectural or product decisions |

### Feature-Level Source of Truth — PRD & ADR (one per epic/feature)

| Document | Covers | Update when... |
|----------|--------|---------------|
| `docs/prd/[feature].md` | What to build, task checklist, acceptance criteria | Plan changes, tasks ticked off |
| `docs/ard/[feature].md` | How to build it, decisions, data flow | Implementation deviates from plan |
| `docs/architecture/[feature].md` | End-to-end flow for the feature (button-to-store-to-wiki) | When the design itself changes |
| `docs/plans/[feature].md` | Implementation plan snapshot + retrospective | Snapshot in Phase 2.3, retrospective in Phase 5.2 |

**Rule:** Check for existing PRD/ADR before creating new ones — update, don't duplicate.

---

## When to Consult Each Document

### Before Starting Work
| Document | When to Consult |
|----------|-----------------|
| `PRODUCTION_READY.md` | Check current milestone status and known bugs |
| `Project_PDR.md` | System-level changes, architecture, the modular Protocol-based design |
| `database_reference_guide.md` | Before changing the `Note` model, `JsonFileStore`, or anything in `state/` |
| `API_REFERENCE.md` | Before changing any Protocol in `interfaces.py` or adding a new pluggable backend |
| `docs/prd/[feature].md` | Existing feature requirements if PRD exists |

### During Development
| Document | When to Consult |
|----------|-----------------|
| `docs/prd/[feature].md` | Implementation details, acceptance criteria, task breakdown |
| `docs/ard/[feature].md` | Architectural decisions, trade-offs, rationale |
| `docs/bugs/*.md` | When encountering similar issues — check if already documented |

### After Completing Work — MANDATORY AUDIT (do not skip)

Run through **every applicable file** in `docs/context/` and update if the feature touched it:

| File | Update if... |
|------|-------------|
| `Context_Index_File.md` | Any new or removed files anywhere in the project |
| `database_reference_guide.md` | Note model / store schema / `state/` layout changed |
| `API_REFERENCE.md` | A Protocol changed, was added, or a new concrete impl was registered |
| `CHANGELOG.md` | **Always** — add a summary entry for this feature |
| `PRODUCTION_READY.md` | Milestone status changed, bugs added/resolved |
| `Project_PDR.md` | Architectural patterns, conventions, or scope changed |

`Project_Authentication.md` is N/A for this prototype — the `context-docs-agent` reads, confirms still N/A, and records that on its gate.

Also update:
- `docs/prd/[feature].md` — tick off completed tasks, note any deviations

### Bug Documentation
| Situation | Action |
|-----------|--------|
| Bug found | Create `docs/bugs/BUG-NNN-description.md` |
| Bug fixed | Update bug report + `PRODUCTION_READY.md` Known Bugs table |
| Complex debug | Document attempted fixes and root cause in bug report |

---

## Project File Catalog

### Root
| File | Purpose |
|------|---------|
| `README.md` | GitHub-facing front door — one-paragraph pitch + Quick start + Architecture table |
| `pyproject.toml` | Project metadata, dependencies, console script (`note-organiser`), setuptools build backend |
| `.env.example` | Env-var contract: `ANTHROPIC_API_KEY`, `NOTE_ORGANISER_MODEL`, `NOTE_ORGANISER_ANNOTATOR` |
| `.gitignore` | Ignores `__pycache__/`, `.venv/`, `.env`, generated `wiki/*.md`, `state/*.json` |
| `CLAUDE.md` | (To be added by `/init`) AI agent instructions — conventions, commands, workflow rules, kit gates |

### Source — `note_organiser/`

#### Top-level package files
| File | Purpose |
|------|---------|
| `note_organiser/__init__.py` | Package marker |
| `note_organiser/app.py` | Streamlit UI entry point (`note-organiser` console script calls `cli_run`); the only place the user sees in-app text |
| `note_organiser/config.py` | `AppConfig` dataclass + `build_pipeline()` — the single wiring location for all backends |
| `note_organiser/interfaces.py` | The five `typing.Protocol` contracts: `Splitter`, `Annotator`, `Deduper`, `Store`, `Renderer`. The project's extension API. |
| `note_organiser/models.py` | Pydantic models: `RawChunk`, `Note`, `NoteGroup`, `Action`. Plus the `content_hash()` helper for ID/dedupe. |
| `note_organiser/pipeline.py` | The orchestrator — knows nothing about file formats, LLMs, or storage; just sequences the five Protocols |
| `note_organiser/prompts.py` | Prompt templates fed to the Claude annotator |

#### Pluggable backends
| File | Purpose |
|------|---------|
| `note_organiser/splitters/__init__.py` | Splitter exports |
| `note_organiser/splitters/markdown.py` | `MarkdownHeadingSplitter` — splits on `#` / `##` / `###` |
| `note_organiser/splitters/paragraph.py` | `BlankLineParagraphSplitter` — splits on blank lines |
| `note_organiser/splitters/registry.py` | `ExtensionRoutedSplitter` — picks splitter by file extension |
| `note_organiser/annotators/__init__.py` | Annotator exports |
| `note_organiser/annotators/claude.py` | `ClaudeAnnotator` — Anthropic SDK, prompt-cached, default Sonnet 4.6 |
| `note_organiser/annotators/stub.py` | `StubAnnotator` — offline, deterministic output for pipeline tests with no API key |
| `note_organiser/dedupers/__init__.py` | Deduper exports |
| `note_organiser/dedupers/fuzzy.py` | `FuzzyTitleDeduper` — uses rapidfuzz on titles + body cosine |
| `note_organiser/stores/__init__.py` | Store exports |
| `note_organiser/stores/jsonfile.py` | `JsonFileStore` — single-file JSON-on-disk; persists `Note`s by `note_id` |
| `note_organiser/renderers/__init__.py` | Renderer exports |
| `note_organiser/renderers/karpathy_wiki.py` | `KarpathyWikiRenderer` — emits the Karpathy-style Markdown wiki under `wiki/` |

### User data — `notes/`, `wiki/`, `state/`
| Path | Purpose |
|------|---------|
| `notes/` | User input — drop `.txt` or `.md` files here for the pipeline to ingest. Sample files (`phone_dump.txt`, `south_america.md`, `thoughts.md`) ship for local testing. |
| `wiki/` | Generated output — Markdown wiki produced by `KarpathyWikiRenderer`. Contents are git-ignored except `.gitkeep`. |
| `state/` | Persistence — `state/notes.json` is the `JsonFileStore`'s on-disk file. Git-ignored except `.gitkeep`. |

### Documentation — `docs/`

#### Root of `docs/`
| File | Purpose |
|------|---------|
| `docs/README.md` | The kit's setup guide (universal — describes how to use the kit in any project) |
| `docs/CLAUDE_SNIPPET.md` | Snippet customized for this project; pasted into the root-level `CLAUDE.md` |

#### Universal Prompts — `docs/prompts/`
| File | Purpose |
|------|---------|
| `docs/prompts/feature-lifecycle.md` | Full feature dev cycle — 3 stop points, otherwise autonomous |
| `docs/prompts/bugfix.md` | Investigate + fix a known bug |
| `docs/prompts/debug.md` | Diagnose an unknown issue |
| `docs/prompts/create-testing-agent.md` | Generate a feature-specific test plan (Phase 2.7 of feature-lifecycle) |

#### Sub-Agents — `.claude/agents/` (root-level, not under docs/)
| File | Purpose |
|------|---------|
| `.claude/agents/testing-agent.md` | Phase 4 verification — Streamlit UI on `localhost:8501` |
| `.claude/agents/code-quality-agent.md` | Phase 5.3 — pytest + `pip install -e .` + 5 quality skills |
| `.claude/agents/context-docs-agent.md` | Phase 5.5a — keeps the 7 context files current (6 active + 1 N/A) |
| `.claude/agents/docs-auditor-agent.md` | Phase 5.5b — README + .env.example + Streamlit sidebar copy + PRD/ADR rewrite |

#### Context Files — `docs/context/`
| File | Purpose |
|------|---------|
| `docs/context/Context_Index_File.md` | This file — master file catalog |
| `docs/context/Project_PDR.md` | Design rationale, architectural patterns, conventions |
| `docs/context/CHANGELOG.md` | Chronological change history |
| `docs/context/PRODUCTION_READY.md` | Roadmap, milestone status, known bugs (also serves as epics tracker) |
| `docs/context/database_reference_guide.md` | JSON-store schema (Note model, `state/notes.json` layout) |
| `docs/context/API_REFERENCE.md` | Protocol contracts in `interfaces.py` — the project's extension API |
| `docs/context/Project_Authentication.md` | N/A for prototype (no user auth) — universal template stub |

#### Feature Documentation Folders — `docs/{prd,ard,architecture,plans,bugs,testing-agents}/`
Empty placeholders containing only `.gitkeep`. Files are created per feature during the lifecycle:
- `docs/prd/` — PRDs, one per feature
- `docs/ard/` — ADRs, one per feature
- `docs/architecture/` — Feature architecture docs
- `docs/plans/` — Implementation plan snapshot + retrospective
- `docs/bugs/` — Bug reports
- `docs/testing-agents/` — Feature-specific test plans

### Tests
None yet. Test directory and pytest config will land with the first feature that adds them. Until then, the `code-quality-agent` records its Tests gate-line as `No tests yet for {module} — flagged for follow-up`.
