# CLAUDE.md Snippet — AI Dev Workflow Kit

> **Instructions:** Copy the content below into your project's `CLAUDE.md` file. Customize the sections marked with `[CUSTOMIZE]` for your project's specific tools and conventions.

---

## Documentation System

This project uses a structured documentation system in `docs/`. **Read before you build.**

### Context Files — Source of Truth (`docs/context/`)

Before starting any work, read the relevant context files:

| File | Read when... |
|------|-------------|
| `docs/context/Context_Index_File.md` | Always — find any file in the project |
| `docs/context/Project_PDR.md` | Understanding architecture, patterns, tech stack |
| `docs/context/database_reference_guide.md` | Before ANY database changes |
| `docs/context/API_REFERENCE.md` | Before ANY API route changes |
| `docs/context/Project_Authentication.md` | Before ANY auth or RLS changes |
| `docs/context/PRODUCTION_READY.md` | Checking milestone status, known bugs |
| `docs/context/CHANGELOG.md` | Understanding recent changes |

### Workflow Prompts (`docs/prompts/`)

| Prompt | When to use |
|--------|------------|
| `docs/prompts/feature-lifecycle.md` | Full feature development — 3 stop points, otherwise autonomous |
| `docs/prompts/bugfix.md` | Investigating and fixing a known bug |
| `docs/prompts/debug.md` | Diagnosing an unknown issue |
| `docs/prompts/create-testing-agent.md` | Generate a feature-specific browser test plan (invoked during Phase 2.7) |

### Sub-Agents (`.claude/agents/`)

These are invoked by `feature-lifecycle.md` — do not run them inline.

| Sub-agent | Invoked from | Produces |
|-----------|--------------|----------|
| `.claude/agents/testing-agent.md` | Phase 4.1 | PASS/FAIL/SKIP test results block (verbatim) |
| `.claude/agents/code-quality-agent.md` | Phase 5.3 | `CODE QUALITY GATE:` block (11 items, verbatim) |
| `.claude/agents/context-docs-agent.md` | Phase 5.5a | `CONTEXT DOCS GATE:` block (verbatim) |
| `.claude/agents/docs-auditor-agent.md` | Phase 5.5b | `DOCUMENTATION GATE (User-Facing):` block (verbatim) |

### Feature Documentation (created per feature)

| Folder | Contains |
|--------|---------|
| `docs/prd/` | Product Requirements Documents (what to build) |
| `docs/ard/` | Architecture Decision Records (how to build it) |
| `docs/architecture/` | Feature architecture docs (button-to-DB flows) |
| `docs/plans/` | Implementation plans + retrospectives |
| `docs/bugs/` | Bug reports with investigation and resolution |
| `docs/testing-agents/` | Feature-specific browser test plans |

### Documentation Rules

1. **Never skip doc updates.** Every feature must update every affected context file in `docs/context/`.
2. **Check before creating.** Search for existing PRD/ADR before creating new ones — update, don't duplicate.
3. **CHANGELOG is mandatory.** Every feature and every fix gets an entry. No exceptions.
4. **Context Index stays current.** Every new file created must be added to `docs/context/Context_Index_File.md`.
5. **PRDs match reality.** After implementation, rewrite the PRD to reflect what was actually built.

---

## Development Workflow

### Feature Development
Use `docs/prompts/feature-lifecycle.md` for all feature work. Three stop points:
1. Scope approval (after questions)
2. Plan mode approval (before writing docs)
3. Manual testing handoff (after automated testing)

### Bug Fixes
Use `docs/prompts/bugfix.md`. One stop point after investigation, before applying the fix.

### Debugging
Use `docs/prompts/debug.md`. One stop point after diagnosis, before applying the fix.

---

## Commands (SuperNoteOrganiser)

| Command | Purpose |
|---------|---------|
| `pip install -e .` | Editable install — also doubles as the `code-quality-agent`'s "build" check |
| `streamlit run note_organiser/app.py` | Start the Streamlit dev server (default `http://localhost:8501`) |
| `note-organiser` | Console-script entry (calls `note_organiser.app:cli_run`) |
| `pytest` | Run all tests (no watch mode by default — safe). No test suite exists yet; first feature that needs it adds the harness. |
| `pytest -q tests/test_models.py` | Single test file, quiet — what `code-quality-agent` step 5.9 uses |
| `NOTE_ORGANISER_ANNOTATOR=stub streamlit run note_organiser/app.py` | Run the full pipeline offline (no API key) — useful for UI-only testing |
| `grep -rn "print(\|pdb\.set_trace\|breakpoint()" note_organiser/` | Debug-statement sweep (`code-quality-agent` step 5.6) |

### ⚠️ Test Command Safety

`pytest` does NOT default to watch mode (unlike `vitest` in the universal kit's warning), so a bare `pytest` invocation is safe — runs once and exits. The `code-quality-agent` still scopes test runs to changed files only; never run the full suite without parent-agent approval.

- **Single file:** `pytest -q tests/test_models.py`
- **If tests hang:** `pkill -f pytest` and investigate. Almost certainly a network call without timeout — likely the Anthropic SDK invoked without `NOTE_ORGANISER_ANNOTATOR=stub`.

### ⚠️ Anthropic API Cost Safety

`NOTE_ORGANISER_ANNOTATOR=claude` (the default) calls the live Anthropic API. **Tests and pipeline experiments should default to `NOTE_ORGANISER_ANNOTATOR=stub`.** Live-Claude runs are intentional and rare — the first end-to-end validation on the maintainer's real notes (item 5 in `docs/context/PRODUCTION_READY.md`) and manual user-driven Streamlit runs. If a test needs to exercise the `ClaudeAnnotator` code path, prefer mocking the SDK `Messages.create` call over hitting the live API.

---

## Conventions (SuperNoteOrganiser)

- **Python 3.11+ only.** Use modern syntax: `X | None` over `Optional[X]`, `from __future__ import annotations` at the top of every module that uses forward refs (already present in all current modules).
- **Pydantic v2.** Use `BaseModel` + `Field`, `model_validate`, `model_dump(mode="json")`. Don't reach for `dict()` / `parse_obj_as` (v1 idioms).
- **Protocols are the boundary.** New backends implement a Protocol from `note_organiser/interfaces.py` and are wired in `note_organiser/config.py::build_pipeline`. Code outside `config.py` should not import concrete backend classes.
- **Atomic file writes.** Anything that writes to `state/` or `wiki/` should use the tempfile + `os.replace` pattern (see `JsonFileStore._flush` for the canonical example).
- **No `print()` for runtime signals.** Use `logging` (or surface to the Streamlit UI). The `code-quality-agent`'s debug-statement sweep removes `print(`, `pdb.set_trace`, `breakpoint()`.
- **Stub backends mirror real ones.** Every external-dependency Protocol that gets a Claude/network impl also gets a deterministic stub for offline tests (today: only Annotator).
- **`content_hash` is load-bearing.** Don't change the algorithm without a migration story — every existing note id depends on it.
- **No tests yet, but the gate accepts that.** Until tests land (`PRODUCTION_READY.md` item 6), `code-quality-agent` line 9 records `No tests yet for {module} — flagged for follow-up`. Don't paper over with a false PASS.

---

## Skills / Tools

The kit's sub-agents invoke five Claude Code skills via slash-command. All apply to Python and are ready to use:

| Skill | Used by | Purpose |
|-------|---------|---------|
| `/code-review` | code-quality-agent step 5.1 | General code review on changed files |
| `/vulnerability-scanner` | code-quality-agent steps 5.2 + 5.8 | Security scan, run TWICE (early + post-cleanup) |
| `/simplify` | code-quality-agent step 5.3 | DRY / reuse / quality improvements |
| `/performance` | code-quality-agent step 5.4 | Scoped to changed components only |
| `/coding-standards` | code-quality-agent step 5.5 | Style / standard violations |

The `claude-api` skill is also relevant (auto-triggers on imports of `anthropic`); use it when modifying `note_organiser/annotators/claude.py` or `note_organiser/prompts.py` — it covers prompt caching best practices, model selection, and tool-use patterns.

For browser automation in the `testing-agent` (Phase 4): use `npx agent-browser` exclusively. Do NOT use `mcp__playwright__*` or `mcp__apify__*` tools — they leak Node processes and consume multi-GB of RAM.

---

## Post-Feature Gates (produced by sub-agents)

Phase 5 of `feature-lifecycle.md` delegates to three sub-agents. Each produces a verbatim gate block. All three blocks MUST appear in the main transcript, in this order, before committing:

1. **`CODE QUALITY GATE:`** — 11 items, from `.claude/agents/code-quality-agent.md`. Line 8 (`/vulnerability-scanner (2)`) must show `CLEAN`.
2. **`CONTEXT DOCS GATE:`** — from `.claude/agents/context-docs-agent.md`. Line 4 (`Changelog`) must show `Entry added — MANDATORY`.
3. **`DOCUMENTATION GATE (User-Facing):`** — from `.claude/agents/docs-auditor-agent.md`. Every decision-tree question must be answered YES/NO with evidence.

Do not commit until all three gate blocks are present, verbatim, and none show an unresolved failure. "I ran the checks and everything was fine" is NOT acceptable — the gate blocks are the proof.
