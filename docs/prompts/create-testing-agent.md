# Create Testing Agent

> **Purpose:** Generate a feature-specific testing agent file from a PRD and architecture doc. This is invoked during Phase 2 (Planning) of the feature lifecycle, after the PRD and ADR are written.

> **Output:** A test plan file saved to `docs/testing-agents/{feature-name}-tests.md`

> **Base agent:** The generated file is executed by `.claude/agents/testing-agent.md` during Phase 4.

---

## Input Required

You need two documents to generate the testing agent:

1. **PRD** — from `docs/prd/`. Contains:
   - Task list (what was built)
   - `STOP: Human Verification` markers (what needs manual testing)
   - Human Testing Plan (click-by-click instructions)
   - Acceptance criteria

2. **Architecture Doc** — from `docs/ard/` or `docs/architecture/`. Contains:
   - User flows (button-to-database)
   - API routes involved
   - Auth/authz requirements
   - Data model
   - Role/tier gating rules

---

## Generation Process

### Step 1: Read the Source Documents

```
Read the PRD file: docs/prd/{feature}.md
Read the ARD file: docs/ard/{feature}.md
Read the architecture file: docs/architecture/Feature_Architecture_{Feature}.md (if exists)
```

### Step 2: Extract Test Dimensions

From the PRD and architecture docs, identify:

**User Flows:**
- What are the primary happy paths? (user does X → sees Y)
- What are the error/edge cases? (empty input, timeout, no auth, wrong role/tier)
- What async operations exist? (AI generation, file upload, webhook callbacks)

**Auth & Role/Tier Matrix:**
- Which roles/tiers can access this feature?
- Which roles/tiers are blocked? (need gate tests)
- Does behavior differ by role/tier? (e.g., different permissions or feature access)
- Does it require auth? (need unauthenticated redirect test)

**Routes & Pages:**
- What URLs does the user visit?
- What API routes are called?
- What are the navigation transitions?

**Form Inputs:**
- What fields exist?
- Which are required vs optional?
- What validation rules apply?
- What values should the test use?

**Async Operations:**
- What triggers async work?
- How long does it take? (set appropriate timeouts)
- What does the loading state look like?
- What does the success state look like?
- What does the error state look like?

**Responsive Requirements:**
- Does this feature have mobile-specific layout?
- Are there touch targets to verify?

### Step 3: Generate Test Scenarios

Create test scenarios following this template for each:

```markdown
### T{N}: {Descriptive Name}

**Role/Tier:** {e.g., Unauthenticated | Free | Pro | Admin — customize for your project's roles}
**Priority:** {Critical | High | Medium | Low}
**Type:** {Auth gate | Smoke test | End-to-end | Interaction | Validation | Responsive | Role-specific | Error handling}
**Async:** {Yes — expected {min}–{max} seconds | No}
**API endpoint:** {POST /api/... | None}
**Depends on:** {T{M} if it requires a prior test's state | None}

**Steps:**
1. {Concrete action — navigate, click, fill, wait}
2. {Each step should be one browser action}
3. {Use real form values, not placeholders}
4. {For steps that trigger API calls, note: "→ triggers POST /api/..."}

**Pass criteria (ALL must be true):**
- **Network:** {expected endpoint} returns 200
- **Console:** no errors related to {feature API path}
- **UI:** {specific observable outcome — exact text, element count, component visible}
- **Timing:** {if async: completes within min–max range. Faster than min = suspicious}

**Fail indicators (ANY means FAIL):**
- **Network:** {endpoint} returns 4xx/5xx, or no API call made at all
- **Console:** errors containing "{api path}" or "400" or "500"
- **UI:** error toast appears, loading stops without results, page unchanged after submit
- **Timing:** completes instantly when async operation expected (< 3 seconds = not actually running)

**Verify:**
- {What to check — page text, URL, element presence}
- Screenshot before: `{test-id}-before.png`
- Screenshot after: `{test-id}-after.png`
```

### Step 4: Design Execution Order

Arrange tests to minimize login/logout cycles:

1. Unauthenticated tests first (no login needed)
2. Lowest-privilege role/tier tests (login once)
3. Mid-privilege role/tier tests (login once)
4. Highest-privilege role/tier tests (login once)
5. Admin tests if applicable

Within each role/tier group, order by dependency (tests that create state needed by later tests go first).

### Step 5: Set Configuration

```yaml
feature: {kebab-case-feature-name}
evidence_dir: /tmp/test-evidence/{feature-name}
roles_required: [{list of roles/tiers this feature touches}]
async_timeout: {max seconds for the longest async operation}
dev_server: http://localhost:{PORT}
credentials_source: .env.local
```

**Process safety:** When the testing agent runs unit/integration tests as part of verification, it MUST use single-run commands only (e.g., `npx vitest run`, NOT `npx vitest`). Watch mode spawns persistent workers that consume CPU indefinitely. If any test process hangs, kill it immediately (`pkill -f vitest`) before continuing.

### Step 6: Write the File

Save to `docs/testing-agents/{feature-name}-tests.md` using this structure:

```markdown
# Testing Agent: {Feature Name}

> **Feature:** {Feature Name}
> **Routes:** {comma-separated list of routes}
> **Generated from:** {PRD filename} + {ARD filename}
> **Base agent:** `.claude/agents/testing-agent.md`

---

## Test Configuration
{yaml block from Step 5}

---

## Credentials Setup
{standard credential extraction — copy from existing test plan or document your credential loading approach}

---

## Test Scenarios
{all T1..TN scenarios from Step 3}

---

## Execution Order
{ordered list from Step 4, with rationale for grouping}

---

## Cleanup
{any feature-specific cleanup instructions}

---

## Previous Results
{empty results table for tracking across invocations}

| Test | Status | Notes |
|------|--------|-------|
{one row per test, all pending}
```

---

## Quality Checklist

Before saving the generated file, verify:

- [ ] Every `STOP: Human Verification` in the PRD has a corresponding test scenario
- [ ] Every API route in the architecture doc is exercised by at least one test
- [ ] Auth gate tests exist for every role/tier that should be blocked
- [ ] At least one test covers the primary happy path end-to-end
- [ ] Every form has a validation test (empty required fields)
- [ ] Async operations have explicit timeouts AND minimum expected times
- [ ] A mobile responsive test exists (375px viewport)
- [ ] Tests use concrete form values, not placeholders like "test" or "example"
- [ ] Execution order minimizes login/logout cycles
- [ ] **Every test that triggers an API call specifies the expected endpoint and status code**
- [ ] **Every test has explicit FAIL indicators, not just success criteria**
- [ ] **Every async test has a minimum expected time (to catch fake completions)**
- [ ] Every test has a unique, descriptive screenshot filename
- [ ] Tests that create state (e.g., create a record) note the identifiable name for cleanup

---

## Example Invocation

During Phase 2 of the feature lifecycle, after writing the PRD and ADR:

```
Agent tool:
  prompt: |
    Read the PRD at docs/prd/{feature}.md and the ARD at
    docs/ard/{feature}.md.

    Follow the instructions in docs/prompts/create-testing-agent.md to
    generate a feature-specific testing agent file.

    Save the output to docs/testing-agents/{feature-name}-tests.md.
```

During Phase 4, the parent agent invokes:

```
Agent tool:
  prompt: |
    You are the testing sub-agent. Read your base instructions from
    .claude/agents/testing-agent.md, then execute the test plan in
    docs/testing-agents/{feature-name}-tests.md.

    The dev server is running on localhost:{PORT}.
    Report results in the format specified by the base agent.
```
