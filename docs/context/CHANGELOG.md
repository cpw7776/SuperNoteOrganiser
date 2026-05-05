# Changelog — SuperNoteOrganiser

All notable changes to **SuperNoteOrganiser** are documented in this file.

> **Format:** Each entry includes: what changed, why, files affected, and any DB / API / Auth changes (DB = `Note` model + `JsonFileStore` schema; API = the Protocol contracts in `interfaces.py`; Auth = N/A for this single-user prototype).
> **Rule:** Every feature and every fix gets a changelog entry. No exceptions. (The `context-docs-agent` enforces this — line 4 of its gate can only ever show `Entry added — MANDATORY`.)

---

## [Unreleased]

### Apply AI Dev Workflow Kit to the project — 2026-05-05

Installed the universal AI Dev Workflow Kit (`docs/` + `.claude/agents/`) into the SuperNoteOrganiser repo and customized every `[CUSTOMIZE]` / `[PLACEHOLDER]` marker for this project's stack (Python 3.11+ / Streamlit / Anthropic SDK / file-based JSON store, no auth, no HTTP API). The four sub-agents now reference real commands (`pytest`, `pip install -e .`, `streamlit run note_organiser/app.py`), the right env vars (`ANTHROPIC_API_KEY`, `NOTE_ORGANISER_*`), and the right user-facing surfaces (`README.md`, `.env.example`, the Streamlit sidebar copy in `app.py`). The seven context files are reframed for this project: `database_reference_guide.md` documents the `Note` model + `state/notes.json` schema; `API_REFERENCE.md` documents the Protocol contracts in `interfaces.py` (the project's extension API); `Project_Authentication.md` is N/A for the prototype but kept as a stub.

**New files:**
- `.claude/agents/testing-agent.md` — Phase 4 verification agent customized for Streamlit on `localhost:8501`, no auth
- `.claude/agents/code-quality-agent.md` — Phase 5.3 quality gate customized for pytest + `pip install -e .`
- `.claude/agents/context-docs-agent.md` — Phase 5.5a context-doc auditor for the 7 files (6 active + 1 N/A)
- `.claude/agents/docs-auditor-agent.md` — Phase 5.5b user-facing auditor; added Section 5.1.b for SuperNoteOrganiser's surfaces (README + .env.example + Streamlit sidebar)
- `docs/README.md` — kit's universal setup guide (descriptive, not project-specific)
- `docs/CLAUDE_SNIPPET.md` — snippet customized for this project's commands, conventions, and skills/tools
- `docs/prompts/feature-lifecycle.md` — universal full-feature workflow prompt (3 stop points)
- `docs/prompts/bugfix.md` — universal bug-fix workflow prompt
- `docs/prompts/debug.md` — universal debug workflow prompt
- `docs/prompts/create-testing-agent.md` — feature-test-plan generator (invoked Phase 2.7)
- `docs/context/Context_Index_File.md` — full file catalog
- `docs/context/Project_PDR.md` — design rationale + 5 architectural patterns
- `docs/context/CHANGELOG.md` — this file (with this entry)
- `docs/context/PRODUCTION_READY.md` — roadmap to v0.1
- `docs/context/database_reference_guide.md` — `Note` model + `JsonFileStore` schema (reframed from "DB" template)
- `docs/context/API_REFERENCE.md` — Protocol contracts (reframed from "HTTP API" template)
- `docs/context/Project_Authentication.md` — N/A stub (no user auth)
- `docs/{prd,ard,architecture,plans,bugs,testing-agents}/.gitkeep` — empty per-feature folders

**Modified:** None (this is the kit's first install in this repo).
**Removed:** None.

**DB changes:** None — no schema changes; the docs just describe what was already there.
**API changes:** None — Protocol contracts are unchanged; the docs just describe what was already there.
**Auth changes:** None — auth was N/A and remains N/A.
