# Debug Protocol

> **Standalone — use anytime. Not part of the feature lifecycle.**

> **Philosophy:** Diagnose thoroughly first, then fix. One stop point — after diagnosis, before applying the fix.

**The Issue:** [INSERT ISSUE DESCRIPTION]

## Skills to Invoke
- `/tdd` — Write failing test to reproduce

---

## Phase 1: Diagnose (AUTONOMOUS)

**Do NOT guess-and-check. Complete the full diagnosis before proposing any fix.**

### 1.1 Three Hypotheses
List **exactly 3** root causes ranked by probability with reasoning.

### 1.2 Elimination Strategy

| Hypothesis | Diagnostic Action | If True | If False |
|------------|-------------------|---------|----------|
| A (Most Likely) | [specific test/log] | [result] | [result] |
| B | [specific test/log] | [result] | [result] |
| C | [specific test/log] | [result] | [result] |

### 1.3 Execute ALL Diagnostics
- Test all three hypotheses systematically
- Show results for each, explain what each proves or disproves
- Identify the confirmed root cause (or if none match, generate new hypotheses and repeat)

---

## ⏸️ STOP: Present Diagnosis & Fix Plan

Present:
1. **Confirmed root cause** with evidence
2. **Proposed fix** — what will change and why
3. **Failing test** that will prove the fix works (from `/tdd`)

Wait for user approval before applying the fix.

---

## Phase 2: Fix (AUTONOMOUS after approval)

1. Write the failing test that reproduces the bug
2. Implement the fix
3. Verify the test passes
4. Run `[TEST_COMMAND]` — all tests must pass
5. Run `[BUILD_COMMAND]` — zero errors
6. Remove ALL diagnostic logging
7. Commit with descriptive message

Report: what changed, what was fixed, what to verify manually (if anything).
