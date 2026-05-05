# SuperNoteOrganiser — Production Ready

> **Goal:** Reach v0.1 — a stable, daily-driver-ready prototype the maintainer can use on their actual notes corpus without surprises. Target date: TBD.
> This document doubles as the project's epics tracker (per the `context-docs-agent` adaptation: no separate root epics tracker).
> **Last Updated:** 2026-05-05

---

## Release Criteria

| # | Requirement | Epic | Priority | Status |
|---|-------------|------|----------|--------|
| 1 | Bootstrap pipeline + Streamlit app working end-to-end (stub annotator) | Bootstrap | P0 | Done — initial commit |
| 2 | AI Dev Workflow Kit installed and customized for SuperNoteOrganiser | Tooling | P0 | In progress (this session) |
| 3 | `CLAUDE.md` written via `/init` + augmented with kit snippet | Tooling | P0 | Pending — final step of this session |
| 4 | First commit pushed to `cpw7776/SuperNoteOrganiser` with kit installed | Tooling | P0 | Pending |
| 5 | Live-Claude annotator path verified end-to-end on the maintainer's `notes/` | Validation | P0 | Not started |
| 6 | First test suite landed (pytest harness + tests for `Note`, `content_hash`, `JsonFileStore`, `FuzzyTitleDeduper`) | Quality | P1 | Not started |
| 7 | Prompt-cache verification: confirm `ClaudeAnnotator` is actually getting cache hits on subsequent runs (Anthropic SDK metrics) | Quality | P1 | Not started |
| 8 | Round-trip test on a real notes corpus (50+ files): wiki output reviewed by maintainer; flag false-merges, false-dedupes | Validation | P1 | Not started |
| 9 | LICENSE chosen and added | Distribution | P1 | Not started |
| 10 | Tag v0.1 | Release | P1 | Not started |
| 11 | Optional: pluggable embedding-based deduper (instead of fuzzy title match) | Future | P2 | Not started |
| 12 | Optional: SQLite store backend for >10k notes | Future | P2 | Not started |

**Priority guide:**
- **P0** — Must ship before v0.1. Blocks release.
- **P1** — Should ship before v0.1. Important but not blocking.
- **P2** — Post-v0.1.

---

## P0 — Critical Blockers

### Bootstrap (Item 1)
- **What:** Working Streamlit app, modular pipeline, both `claude` and `stub` annotators, sample notes ingest end-to-end into `wiki/`.
- **Status:** Done. Initial commit `7540200 Bootstrap modular note-to-wiki agent prototype`.

### Kit installation + customization (Item 2)
- **What:** Copy the AI Dev Workflow Kit's `docs/` and `.claude/` into the repo. Replace every `[CUSTOMIZE]` and `[PLACEHOLDER]` marker with project-specific content. Preserve original universal hints as inline comments so the customized files remain useful as templates if copied to a non-Python project.
- **Why:** Without the kit, AI agent sessions on this repo lose continuity — every session has to re-derive the conventions. With the kit's verbatim gate blocks, post-implementation work becomes mechanically auditable.
- **Status:** In progress this session. Sub-agents and 4 of 7 context files done; 3 remaining (database_reference_guide, API_REFERENCE, Project_Authentication) and CLAUDE_SNIPPET.md.

### CLAUDE.md (Item 3)
- **What:** Run `/init` to generate a baseline `CLAUDE.md`, then merge in the customized `docs/CLAUDE_SNIPPET.md` content.
- **Why:** `CLAUDE.md` is what every Claude Code session loads first. Without it, the agent has no idea about the kit, the gates, the conventions, or the project's preferences (commands, env-vars, the stub-vs-claude annotator split).
- **Status:** Pending — user runs `/init` after the kit moulding is committed.

### First push (Item 4)
- **What:** Commit the kit installation in the SuperNoteOrganiser repo, push to `cpw7776/SuperNoteOrganiser` on GitHub.
- **Status:** Pending — the existing repo already exists; we just push the new commits.

### Live-Claude annotator validation (Item 5)
- **What:** Run the pipeline with `NOTE_ORGANISER_ANNOTATOR=claude` on the maintainer's actual notes corpus. Verify the Action/Why/Purpose blocks are sensible, the merge logic preserves device attribution, the dedupe doesn't collapse semantically distinct notes, and prompt caching actually engages (cache_creation_input_tokens > 0 then cache_read_input_tokens > 0 on rerun).
- **Status:** Not started.

---

## Open Questions

| # | Question | Notes |
|---|----------|-------|
| 1 | Should the kit's `docs/` be checked in, or `.gitignore`-d? | Currently checked in. The PRD/ADR/architecture/plans subfolders accumulate per-feature artefacts that ARE valuable history. Keep checked in. |
| 2 | LICENSE — MIT, Apache-2.0, or other? | MIT is the default for this kind of prototype. Defer until the project is ready to share. |
| 3 | When will tests start landing? | Item 6. Open question whether to retro-add tests for the bootstrap modules, or only require tests for new features going forward. The kit's gate accepts "No tests yet for {module} — flagged for follow-up" as a recorded skip. |
| 4 | Prompt-cache verification — does the Anthropic SDK expose cache hit/miss metrics in a way the test plan can assert on? | Item 7. Yes, via the `usage` field on `Message` responses (`cache_creation_input_tokens`, `cache_read_input_tokens`). Confirm and write a small test. |
| 5 | Real-corpus testing — how big is the maintainer's actual notes corpus? Affects whether `JsonFileStore` is sufficient or if Item 12 (SQLite) is needed before v0.1. | Item 8 + 12. Likely <1k notes for the foreseeable future, so the JSON store is fine. |

---

## Known Bugs

| # | Bug | Severity | Status | Report |
|---|-----|----------|--------|--------|
| — | None known yet | — | — | — |

---

## Pre-Release Checklist (v0.1)

- [ ] Items 1–4 (bootstrap + kit + CLAUDE.md + push) complete
- [ ] Item 5 (live-Claude end-to-end) complete on maintainer's real notes
- [ ] First test suite landed; `code-quality-agent` Tests gate-line shows real PASS counts, not "No tests yet"
- [ ] No outstanding `[CUSTOMIZE]` / `[PLACEHOLDER]` markers in active files (universal-template hints kept as inline comments are fine)
- [ ] All universal-template universals visible (preserved as inline comments) in customized agents
- [ ] LICENSE file present at repo root
- [ ] README.md (root) is current and accurate (matches what the kit + Streamlit app actually do)
- [ ] CLAUDE.md present at repo root and references `docs/CLAUDE_SNIPPET.md`
- [ ] CHANGELOG entry exists for every commit since the bootstrap
- [ ] Tagged v0.1
