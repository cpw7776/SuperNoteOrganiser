# Feature Lifecycle

> **This is the single prompt for all feature work.** Point the AI at an epic and let it run. There are only **three stop points** in the entire flow — everything else runs autonomously.

> **Model:** Switch to **claude-opus-4-6** before running this prompt.

> **Stop Points:**
> 1. **Requirements & Scope Approval** — The AI reads your rough epic, presents its understanding, asks ALL questions to build out the full feature, then presents a scope table for approval.
> 2. **Plan Mode Approval** — The AI enters plan mode, reads the codebase, and presents a high-level implementation plan (task breakdown, architecture direction, risks). You approve before it writes PRD/ADR docs.
> 3. **Manual Testing Handoff** — After implementation + automated testing, the AI stops for you (or a testing agent) to verify manually. Then it finishes everything.

---

## Launch

Proceed with Epic/User Story/Feature: **[INSERT EPIC/FEATURE ID]**

---

## Skills to Invoke (across the full lifecycle)

> **[CUSTOMIZE]** Replace with your project's skills. These are examples — keep the ones that match your setup, rename or remove the rest.

- `/brainstorming` — Requirements exploration and feature shaping
- `/using-git-worktrees` — Isolated feature branch (optional)
- `/writing-plans` — Implementation plan document (created in Phase 2, updated as a learning doc in Phase 5)
- `/architecture-patterns` — Modular architecture design
- `/vulnerability-scanner` — Security at design + completion
- `/db-best-practices` — Database changes (e.g., Supabase, Prisma, Drizzle, raw SQL)
- `/framework-best-practices` — Framework-specific patterns (e.g., React/Next.js, Django, Rails)
- `/tdd` — Test-driven development throughout
- `/coding-standards` — Language/framework best practices
- `/technical-writing` — Documentation quality
- `/simplify` — Code reuse, reduce complexity, DRY
- `/code-review` — Code quality audit
- `/performance` — Performance checks
- `/web-design-guidelines` — UI/UX and accessibility
- `/agent-browser` — Browser automation testing

---

## PHASE 1: Kickoff & Requirements (INTERACTIVE)

**This is the only phase where the AI should ask questions. Batch ALL questions here — do not drip-feed them across later phases.**

**Epics will often be rough — voice notes, quick ideas, half-formed thoughts. Your job is to take that rough input and help the user shape it into a fully specified feature.**

### 1.1 Branch Setup
- Ask: "Do you want to use a git worktree for isolation, or work on a regular branch?"
- If worktree: Run `/using-git-worktrees` to create `feature/{ID}-{short-description}`
- If regular branch: `git checkout -b feature/{ID}-{short-description}` from `main`
- Confirm branch is active

### 1.2 Understand the Epic
- Read the Epic/User Story provided
- Read all relevant context: `docs/context/Context_Index_File.md`, `docs/context/PRODUCTION_READY.md`, `docs/context/database_reference_guide.md`, `docs/context/API_REFERENCE.md`
- Present back to the user: **"Here's what I understand so far..."** — summarise the feature intent, the user problem it solves, and your initial read on what needs to happen
- Be explicit about what's clear and what's vague or missing

### 1.3 Feature Build-Out Questions
Run `/brainstorming` against the Epic to explore requirements and edge cases. Then compile ALL clarifying questions into a single batch:

- **Requirements questions** — What exactly should this do? What are the user flows? What are the edge cases? What should happen on error?
- **Design questions** — UI/UX decisions, where does this live in the app, how does the user discover and interact with it?
- **Technical questions** — Data model changes, API needs, auth/authz implications, integration with existing features?
- **Scope questions** — What's in v1 vs later? Are there related features that should be considered now?

**Use the `AskUserQuestion` tool (interactive terminal selector) for ALL questions.** Batch related questions (up to 4 per call), provide 2-4 options with descriptions, and use `multiSelect: true` when choices aren't mutually exclusive. This gives the user selectable options they can navigate with arrow keys. If answers raise follow-up questions, batch those too — do NOT proceed until requirements are fully resolved.

### 1.4 Stack & Technology Research (when needed)
**If the feature involves unfamiliar libraries, APIs, patterns, or technology choices:**
- Identify what needs researching (e.g., "which charting library?", "how does X API work?", "best approach for real-time updates?")
- Research options, compare tradeoffs (performance, bundle size, maintenance, community)
- Present a recommendation with reasoning
- Get user confirmation on the tech choice before proceeding

**Skip this step if the feature uses only the existing stack with no new dependencies.**

### 1.5 Update the Epic
- Update the Epic document with ALL answers and decisions — nothing undocumented
- Everything discussed becomes part of the written spec

### 1.6 Scope Confirmation
Before proceeding, produce a scope table:

| # | What | Why | Files/Areas Affected |
|---|------|-----|----------------------|
| 1 | ... | ... | ... |

Present the scope table and wait for approval. This is the last time you stop before autonomous execution begins.

**Once the user approves the scope, proceed through Phases 2–5 autonomously. Do not stop unless confidence drops below 90% on a specific decision.**

---

## PHASE 2: Planning & Documentation (AUTONOMOUS)

**Role:** Senior Full-Stack Developer & Architect creating a plan for a junior dev or less capable LLM to execute. Every task must be small, explicit, and self-contained.

### 2.1 Enter Plan Mode

**Immediately after scope approval, enter plan mode (`/plan`).** This is the fast alignment gate before you invest time writing documents.

In plan mode you can read, search, and think — but you **cannot** write or edit files. Use this constraint intentionally: plan mode is for structuring your approach, not producing artifacts.

**In plan mode, produce:**
1. **High-level task breakdown** — the major implementation steps in execution order (DB migration → API routes → components → tests → docs)
2. **Architecture direction** — key technical decisions (new tables, shared components, data flow)
3. **Risk flags** — anything uncertain, complex, or likely to change during implementation
4. **Estimated scope** — rough number of files touched, new files created, test files needed

Present this plan for alignment. The user may approve, adjust, or redirect before you spend time on detailed documents.

**Once the plan is approved, exit plan mode to begin writing documents.**

### 2.2 Existing Document Check

**Check first — do not create duplicates.** Search `docs/prd/`, `docs/ard/`, and `docs/architecture/` for existing PRD/ADR/Architecture docs for this feature or a previous version of it.

- **If documents exist:** Update the existing documents — do NOT create new ones. This might be v2 or v3 of a feature; the existing PRD is the one to extend.
- **If documents do not exist:** Create them using the structure below.
- If this feature supersedes an older document, note it under a "Supersedes" heading.

### 2.3 Implementation Plan Document

Run `/writing-plans` to produce `docs/plans/YYYY-MM-DD-<feature-name>.md`. This is the **initial plan snapshot** — what we believed would happen before writing any code. It captures the approach, task breakdown, file paths, and technical decisions at planning time.

This document has a dual purpose:
- **During implementation (Phase 3):** Reference for the planned approach
- **After implementation (Phase 5):** Updated as a **learning document** — what changed, what we didn't foresee, and why. The PRD gets rewritten to match reality; the plan doc preserves the journey.

### 2.4 PRD (Product Requirements Document)

Flesh out the approved plan into a detailed PRD. The PRD is the implementation checklist — every task the agent will execute in Phase 3 lives here.

- Break into small, incremental tasks with checkable boxes (`- [ ]`)
- Embed `STOP: AI Test` markers where automated tests should run during implementation
- Embed `STOP: Human Verification` after every major feature addition (these guide the manual testing checklist later)
- End with a Human Testing Plan (click-by-click instructions for manual testing later)
- Define complete validation plan: user journey, success criteria, edge cases

### 2.5 ADR (Architecture Decision Record)
Run `/architecture-patterns` then document:
- Technical approach, data flow, and schema
- Modular design: reusable utilities, hooks, components — no one-off implementations
- Security by design: Run `/vulnerability-scanner` to identify threats. Document auth, validation, sanitization for every endpoint/form
- URL-addressable routing: all user-visible view modes must be directly linkable and survive refresh/back-forward
- Justification with alternatives and tradeoffs

### 2.6 Feature Architecture Document
Output: `docs/architecture/Feature_Architecture_[Feature_Name].md`

Run `/architecture-patterns` then document:
1. **Button-to-Database Flow** — Trigger, every file/function/handler in sequence, completion behavior
2. **Modular Code & Dependencies** — Shared/reusable components, helpers, external libraries
3. **Data Architecture** — Tables read/updated, schema changes, local state management
4. **Integration Points** — Cross-feature interactions. What breaks if removed?
5. **Security** — Run `/vulnerability-scanner`: auth/authz, input validation, data exposure
6. **Future Modernization Guide** — Tech debt, update priorities, scaling at 10x

### 2.7 Feature-Specific Testing Agent File

Run `docs/prompts/create-testing-agent.md` to generate `docs/testing-agents/{feature-name}-tests.md` from the PRD + ADR + Feature Architecture doc. This is the feature-specific test plan the Phase 4 testing sub-agent will execute.

### 2.8 Skills Map
Identify which skills apply at each PRD step (e.g., `/db-best-practices` for DB tasks, `/tdd` for tests).

**Proceed immediately to Phase 3. Do not stop.**

---

## PHASE 3: Implementation (AUTONOMOUS)

### 3.0 Resource Management (CUSTOMIZE — adjust for your hardware)

> **[CUSTOMIZE]** The rules below are written for a 16GB MacBook Air with no fan. Adjust caps/limits for your hardware. If you're on a workstation with 64GB+ RAM, you can relax the parallel-agent cap and the "never full test suite" rule, but keep the "kill processes when done" discipline — orphaned dev servers and test workers still cost memory even on large machines.

- **Max 2 parallel agents at a time** (raise for large-memory hardware).
- **Kill processes AS SOON AS they finish.** After every test run, build, TypeScript check, or agent completion, immediately check and kill orphaned processes: `ps aux | grep -E "node|vitest|dev-server" | grep -v grep`. Dev servers and test runners must NEVER be left running.
- **Never leave processes running.** Kill them the moment they are done.
- **Never run back-to-back heavy operations** (test suite → tsc → build) without checking the machine isn't already hot. Combine into one chained command where possible.
- **Never run tests in watch mode.** Always use single-run (`npm run test:run`, `npx vitest run`, `pytest`). If a test process hangs: `pkill -f vitest` (or equivalent) immediately.
- **At the end of every session**, run a final process check and kill anything left behind.

### 3.1 Pre-Flight: Clean Baseline

**Before writing any feature code, establish a clean baseline:**

1. Run `[TEST_COMMAND]` (single-run, NOT watch mode) — capture current test results
2. Run `[BUILD_COMMAND]` — confirm clean build
3. **If any tests fail or the build is broken:** Fix them NOW, even if they are unrelated to this feature. Do not start feature work on a broken baseline.
4. Commit baseline fixes separately (e.g., "fix: resolve pre-existing test failures before [feature name]")

### 3.2 TDD Implementation Cycle

Run `/tdd` to enforce this cycle for each PRD task:

1. Write failing test
2. Implement minimum code to pass
3. Run `/simplify` — check for code reuse opportunities, reduce complexity
4. Lint
5. Tick off PRD task
6. Move to next task

**Test Rule:** If a test fails, fix the **code**, not the test — unless the test logic itself is wrong.

**Confidence Rule:** If confidence drops below 90% on any requirement or architectural decision, **STOP** and ask the user (multiple-choice format). Otherwise keep going.

### 3.3 Mid-Implementation Checks
- After every major component/feature addition: run `[TEST_COMMAND]` to catch regressions early
- Run `/coding-standards` periodically to prevent drift
- Keep tests passing at all times — never accumulate broken tests

### Implementation complete → Proceed immediately to Phase 4. Do not stop.

---

## PHASE 4: Verification (AUTONOMOUS → then STOPS)

### 4.1 Browser Testing (via testing-agent sub-agent)

**Do NOT run agent-browser inline. Invoke the dedicated testing-agent sub-agent.**

The testing-agent lives at `.claude/agents/testing-agent.md` and has mandatory RAM-hygiene pre-flight + teardown. Running agent-browser inline bypasses these safeguards and can leave multi-GB of orphaned MCP/chromium processes.

**Invocation:**

1. Confirm the feature-specific test plan exists at `docs/testing-agents/{feature-name}-tests.md` (generated in Phase 2.7). If not, generate it now via `docs/prompts/create-testing-agent.md` before proceeding.
2. Start the dev server on a known port: `[DEV_SERVER_COMMAND]` (e.g. `npm run dev`, localhost:3000 by default; use a different port per worktree).
3. If in a worktree: symlink `.env.local` from main.
4. Invoke the testing-agent with this input block:
   - Feature name
   - Dev server URL (e.g. `http://localhost:3000`)
   - Path to the test plan
   - Tiers / roles to test (if applicable to your auth model)
5. Wait for the testing-agent to complete and paste its full test results block (PASS/FAIL/SKIP table + Reliability Notes) into the main transcript. The main agent must NOT paraphrase — paste verbatim.

**If the testing-agent asks for help (bad creds, missing env, wrong branch), answer it immediately. Do not defer to the end report.**

Once the testing-agent completes, it handles its own RAM teardown. The main agent should NOT invoke agent-browser or MCP browser tools directly.

### 4.2 Automated Tests

- Run `[TEST_COMMAND]` — ALL tests must pass (not just new ones)
- Run `[BUILD_COMMAND]` — zero errors
- If failures: fix the code (not the tests unless test logic is wrong), re-run until clean

### 4.3 Coverage & Mobile Check

**Coverage:** Confirm browser testing + automated tests cover all new UI, modified functionality, edge cases, auth gates. Flag any gaps.

**Mobile Responsiveness (MANDATORY):** Check all touched pages at 375px viewport:
- No horizontal overflow or content cut off
- Touch targets at least 44px
- Grids stack to single column on mobile
- Modals/dialogs fit within viewport
- Text readable (minimum `text-xs` / 12px)
- Buttons/tiles wrap without overflow
- Fixed/floating elements don't obscure content
- Forms usable — inputs not cramped, labels visible

Fix any mobile issues before proceeding.

### 4.4 Test Summary
- Browser test result: passed / failed / fixed (from testing-agent verbatim block)
- Automated test result: passed / failed / fixed
- Build result: clean / errors fixed
- Coverage gaps flagged for human testing

---

### ⏸️ STOP: Manual Testing Handoff

**This is the only mid-flow stop.** Generate a concise manual testing checklist of anything that:
- Was not fully covered by browser automation (complex interactions, edge cases, multi-step flows)
- Relies on real device/mobile behavior
- Involves billing, auth edge cases, or third-party integrations
- Felt uncertain or flaky during browser testing

Format:
> **Human Test [N]: [Name]**
> - Steps: [what to do]
> - Expected: [what should happen]

**Present the checklist and wait for the user to complete manual testing and report back with results (what passed, what failed, what issues were found).**

---

## PHASE 5: Reconciliation & Completion (AUTONOMOUS)

**Once the user confirms manual testing is done and reports results, run everything below without stopping.**

### 5.1 Plan vs Reality

**Run this AFTER manual testing results come back — not before.** Compare the original plan against what actually happened across the entire feature, including the user's manual testing findings:

- What was implemented exactly as planned?
- What deviated? Why?
- Unexpected issues discovered during implementation?
- Issues found during manual testing — what broke, what was unexpected?
- Any planned tasks skipped or deferred?
- Anything the user flagged during testing that needs addressing before completion?

**If manual testing revealed bugs or issues:** Before fixing anything, run a **Test Autopsy** for each bug:

1. **Why did automated tests pass when this feature was broken?** Identify the specific gap — wrong assertions, over-mocking, missing edge case, testing implementation instead of behavior, or missing integration coverage.
2. **Write new/rewritten tests first** that fail against the current broken behavior (TDD — the fix starts with a failing test, always).
3. **Then fix the code** and verify the new tests pass.
4. Re-run `[TEST_COMMAND]` and `[BUILD_COMMAND]` after fixes.
5. If fixes are significant, re-run the relevant browser tests from Phase 4.

**Do NOT just fix the code and move on.** If tests passed while the feature was broken, the test suite has a gap. Closing that gap is as important as fixing the bug itself.

### 5.2 Update Plan Document (Learning Doc)

**Open the plan document from Phase 2.3 (`docs/plans/YYYY-MM-DD-<feature-name>.md`) and update it as a retrospective.** This is NOT a rewrite to match reality — that's the PRD's job. This is the learning document that preserves what changed and why.

Add a `## Retrospective` section at the end covering:

- **What went as planned** — which tasks executed exactly as written? This validates the planning process.
- **What changed and why** — for each deviation: what did the original plan say, what actually happened, and what caused the change?
- **What we didn't foresee** — blind spots in the original plan. Things that seemed simple but weren't, dependencies that weren't obvious, edge cases that emerged during implementation.
- **What we'd do differently** — if starting this feature again with current knowledge, what would change in the planning phase?
- **Patterns to reuse** — approaches, utilities, or architectural decisions that worked well and should be applied to similar features.

This document becomes a reference for future planning — not "what was built" (that's the PRD/ADR) but "what we learned about how to plan."

### 5.3 Code Quality & Security — MANDATORY (delegated to code-quality-agent)

**Delegate this section to the `code-quality-agent` sub-agent at `.claude/agents/code-quality-agent.md`. Do NOT run `/code-review`, `/vulnerability-scanner`, `/simplify`, `/performance`, or `/coding-standards` inline — the agent runs them in the correct order with the correct failure handling.**

**Invocation input:**
- Feature name
- List of changed files (`git diff --name-only main...HEAD`)
- Path to the PRD

**Gate-output-required rule:**
The code-quality-agent's final message is a verbatim `CODE QUALITY GATE:` block with 11 numbered items (items 2 and 8 are both `/vulnerability-scanner` — a mandatory first pass and a post-cleanup second pass). You MUST paste that block into the main transcript exactly as the agent produced it. If the block is missing, has fewer than 11 items, item 8 does not show CLEAN, or any item shows a failure state, you cannot proceed to 5.4 — re-run the agent or escalate to the user.

**Do not print a paraphrased or summarised gate.** The main agent's job is to orchestrate and relay, not to re-author the gate.

### 5.4 UI & Responsiveness Review
- Run `/web-design-guidelines` on all new/changed UI
- Verify cursor/hover info on all new buttons and interactive elements
- Verify responsive across phone (375px), tablet (768px), laptop (1440px)

### 5.5 Documentation — MANDATORY (delegated to two sub-agents, sequential)

**Launch these two sub-agents sequentially (NOT parallel — respect the RAM budget). Each produces a verbatim gate block that must appear in the main transcript.**

#### 5.5a — context-docs-agent

Invoke `.claude/agents/context-docs-agent.md` first (lighter, completes quickly).

**Input:**
- Feature name
- `git diff --name-status main...HEAD` output
- List of API route changes, DB schema changes, auth/RLS changes, epic IDs touched, bug IDs resolved

**Required output:** Paste the agent's verbatim `CONTEXT DOCS GATE:` block into the main transcript.

#### 5.5b — docs-auditor-agent

Once context-docs-agent completes, invoke `.claude/agents/docs-auditor-agent.md`.

**Input:**
- Feature name
- `git diff --name-only main...HEAD` output
- Path to PRD and ADR
- List of new pages/routes, new buttons/modals/panels, new tier-gated behaviours, third-party APIs touched

**Required output:** Paste the agent's verbatim `DOCUMENTATION GATE (User-Facing):` block (with every decision-tree answer shown) into the main transcript.

### 5.6 Gate Output Required Rule — cannot proceed to git until all three gates are pasted

Before Phase 5.7 (Git), the main transcript must contain, in order:
1. The verbatim `CODE QUALITY GATE:` block from code-quality-agent (11 items — item 8 must show CLEAN from the post-cleanup vulnerability scan).
2. The verbatim `CONTEXT DOCS GATE:` block from context-docs-agent.
3. The verbatim `DOCUMENTATION GATE (User-Facing):` block from docs-auditor-agent (every decision-tree question answered).

**Enforcement:** If any gate block is missing, truncated, paraphrased, or shows an unresolved failure, Phase 5 is NOT complete. You must re-invoke the relevant sub-agent or escalate to the user. Do NOT commit, do NOT merge, do NOT declare the feature done.

"I ran the checks and everything was fine" is NOT acceptable. The gate blocks are the proof. No blocks = no completion.

### 5.7 Git
- Commit all changes (code + docs) with descriptive message
- If lint clean and build passes: merge to main

### 5.8 Next Steps
- Review your epics/roadmap document, identify next logical step with 2-3 options
- Provide a **context summary block** for the next context window

---

## Summary of Stop Points

Phase 4 (browser testing) and Phase 5 (code quality + documentation) run via dedicated sub-agents (`testing-agent`, `code-quality-agent`, `context-docs-agent`, `docs-auditor-agent`). Each sub-agent produces a verbatim gate block; progression through Phase 4 and Phase 5 is gated on those blocks appearing in the main transcript. No new human stop points are introduced — the three stops below still cover the only moments the AI pauses for the user.

| When | Why | What happens next |
|------|-----|-------------------|
| Phase 1.3–1.6 — Questions & Scope | Shape the feature from rough idea to full spec | Approve scope, AI enters plan mode |
| Phase 2.1 — Plan mode approval | Fast alignment on approach before writing docs | Approve plan, AI exits plan mode, writes PRD/ADR, then runs Phases 3–5 |
| Phase 4.4 — Manual testing handoff | Human must verify on real device/browser | Complete testing, confirm, AI runs Phase 5 |

Everything else runs autonomously. The AI only adds an unscheduled stop if confidence drops below 90% on a specific decision.
