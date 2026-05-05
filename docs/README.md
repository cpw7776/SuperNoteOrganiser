# AI Dev Workflow Kit

> **Drop this kit into any project's root to get a full AI-assisted development workflow.**

This kit provides a complete system for AI coding agents to build features, fix bugs, debug issues, and maintain documentation with minimal human intervention. It includes **universal prompt files** (used as-is), **sub-agent definitions** (universal but customizable for your stack), **context file templates** (you build these out for your project), and a **CLAUDE.md snippet** to wire everything together.

---

## Quick Setup

### 1. Copy the folders

Copy both `docs/` and `.claude/` into your project root:

```
your-project/
├── .claude/
│   └── agents/               ← Sub-agents invoked by feature-lifecycle.md (customize per-stack)
│       ├── testing-agent.md
│       ├── code-quality-agent.md
│       ├── context-docs-agent.md
│       └── docs-auditor-agent.md
├── docs/
│   ├── context/              ← Build these out for YOUR project
│   ├── prompts/              ← Ready to use (universal — 3 stops in feature-lifecycle)
│   ├── prd/                  ← Empty — PRDs created per feature
│   ├── ard/                  ← Empty — ADRs created per feature
│   ├── architecture/         ← Empty — Architecture docs created per feature
│   ├── plans/                ← Empty — Plan docs created per feature
│   ├── bugs/                 ← Empty — Bug reports created as needed
│   └── testing-agents/       ← Empty — Test plans generated per feature
├── CLAUDE.md                 ← Add the snippet from docs/CLAUDE_SNIPPET.md
└── ...
```

### 2. Build out your context files

The `docs/context/` folder contains **templates** with placeholders. You need to fill these in for your project:

| File | What to do | Effort |
|------|-----------|--------|
| `Context_Index_File.md` | **Build out fully** — catalog every file in your project | Medium-High |
| `Project_PDR.md` | **Build out fully** — your tech stack, architecture, patterns | Medium |
| `API_REFERENCE.md` | **Build out fully** — all your API routes | Medium-High |
| `database_reference_guide.md` | **Build out fully** — all tables, columns, RLS, migrations | Medium-High |
| `CHANGELOG.md` | **Start fresh** — begin logging changes from now | Low |
| `PRODUCTION_READY.md` | **Build out** — your roadmap/release criteria | Low-Medium |
| `Project_Authentication.md` | **Build out** — your auth flow, session handling | Medium |

**Tip:** Ask the AI agent to help build these out. Point it at the template and your codebase and say: *"Read this template and build out the context file for this project."*

### 3. Customize the sub-agents

Each sub-agent in `.claude/agents/` has `[CUSTOMIZE]` markers for project-specific bits:
- `testing-agent.md` — dev server URL, auth model, credential env vars
- `code-quality-agent.md` — test/build commands, test-process name for `pkill`
- `context-docs-agent.md` — target file list (if your context files differ from the 7 defaults)
- `docs-auditor-agent.md` — decision trees for your doc surfaces (Help Center paths, FAQ path, tour component path, legal page paths)

### 4. Add the CLAUDE.md snippet

Copy the contents of `docs/CLAUDE_SNIPPET.md` into your project's `CLAUDE.md` file (create one if it doesn't exist). This tells the AI agent where everything is and how to use it.

### 5. Start using the prompts

The prompts in `docs/prompts/` are ready to use immediately:

| Prompt | When to use | How to use |
|--------|------------|-----------|
| `feature-lifecycle.md` | Building a new feature or epic | Paste into chat, replace `[INSERT EPIC/FEATURE ID]` |
| `bugfix.md` | Fixing a known bug | Paste into chat, replace `[INSERT BUG DESCRIPTION]` |
| `debug.md` | Diagnosing an unknown issue | Paste into chat, replace `[INSERT ISSUE DESCRIPTION]` |
| `create-testing-agent.md` | Auto-invoked during feature lifecycle Phase 2.7 | Referenced automatically — no manual action needed |

---

## What's Universal vs. What's Project-Specific

### Universal (use as-is)
- `docs/prompts/feature-lifecycle.md` — Full feature development cycle with 3 stop points and sub-agent delegation for Phases 4 + 5
- `docs/prompts/bugfix.md` — Bug investigation and fix protocol
- `docs/prompts/debug.md` — Systematic diagnosis protocol
- `docs/prompts/create-testing-agent.md` — Test plan generator

### Universal-with-customize (edit the `[CUSTOMIZE]` markers)
- `.claude/agents/testing-agent.md` — dev server URL, auth model, credentials
- `.claude/agents/code-quality-agent.md` — test/build commands, process names
- `.claude/agents/context-docs-agent.md` — target file list
- `.claude/agents/docs-auditor-agent.md` — decision-tree targets + doc paths

### Project-specific (build out from templates)
- Everything in `docs/context/` — Templates with `[PLACEHOLDER]` markers
- `docs/CLAUDE_SNIPPET.md` — Customize tool/skill references for your stack

---

## Folder Purpose Reference

| Folder | Purpose | Who creates files |
|--------|---------|-------------------|
| `.claude/agents/` | Sub-agents invoked by feature-lifecycle.md | You (copy from this kit, then customize) |
| `docs/context/` | Project-level source of truth (7 files, always current) | You (initial), AI (maintains via context-docs-agent) |
| `docs/prompts/` | Workflow prompts for the AI agent | You (this kit provides them) |
| `docs/prd/` | Product Requirements Documents (one per feature) | AI (during feature lifecycle Phase 2) |
| `docs/ard/` | Architecture Decision Records (one per feature) | AI (during feature lifecycle Phase 2) |
| `docs/architecture/` | Feature architecture docs (button-to-DB flows) | AI (during feature lifecycle Phase 2) |
| `docs/plans/` | Implementation plan snapshot + retrospective (dual-purpose) | AI (snapshot in Phase 2.3, retrospective in Phase 5.2) |
| `docs/bugs/` | Bug reports with investigation + resolution | AI (during bugfix protocol) |
| `docs/testing-agents/` | Feature-specific test plans | AI (during feature lifecycle Phase 2.7) |

---

## How the System Works

```
You write a rough epic/idea
        ↓
Feature Lifecycle prompt (3 stop points, rest is autonomous)
        ↓
Phase 1: AI asks ALL questions, shapes the feature → YOU APPROVE SCOPE
        ↓
Phase 2.1: AI enters plan mode → YOU APPROVE PLAN
Phase 2.2–2.8: AI writes PRD/ADR/Architecture/plan-snapshot/test-plan (autonomous)
        ↓
Phase 3: AI implements (TDD, incremental, autonomous)
        ↓
Phase 4: testing-agent sub-agent runs browser tests → YOU DO MANUAL TESTING
        ↓
Phase 5: AI reconciles plan vs reality, updates plan doc as learning artefact,
         then delegates to code-quality-agent, context-docs-agent,
         and docs-auditor-agent — each produces a verbatim gate block
         that must appear before commit.
```

Bugs and debug issues use standalone protocols with one stop point each (after investigation/diagnosis, before fix).

---

## Why sub-agents with verbatim gate blocks?

The Phase 5 delegation pattern exists because inline Phase-5 execution was historically lossy:

- "I ran the code review and everything looks good" — no proof, tests may or may not have run.
- "Documentation is up to date" — no proof, CHANGELOG entry often forgotten.
- Security findings deferred to "follow-up PRs" that never land.

Each sub-agent ends its run by printing a **canonical gate block**. The main agent pastes that block into the transcript **verbatim** — that's the mechanical proof the work was done. If the gate is missing, truncated, paraphrased, or shows an unresolved failure, Phase 5 is not complete and the feature can't ship.

- `CODE QUALITY GATE:` — 11 items, including **two** vulnerability-scanner passes (one early, one post-cleanup). Cleanup can introduce new vulns; the second pass catches them.
- `CONTEXT DOCS GATE:` — one line per context file, plus the epics tracker. Line 4 (CHANGELOG) can only show `Entry added — MANDATORY` — no exceptions.
- `DOCUMENTATION GATE (User-Facing):` — every decision-tree question answered YES/NO with evidence. "No update needed" without per-question answers is a gate failure.
