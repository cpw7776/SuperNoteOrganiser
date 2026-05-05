# Project Authentication — SuperNoteOrganiser

> **N/A for SuperNoteOrganiser** — this is a single-user Streamlit prototype. There is no login screen, no users table, no sessions, no tokens, no role-based access control. The only "credential" the project handles is the `ANTHROPIC_API_KEY` environment variable, which is loaded from `.env` (or the shell environment) by `note_organiser/config.py::AppConfig.from_env`. The `context-docs-agent` reads this file in Phase 5.5a, confirms "still N/A — no auth in the prototype", and records that on its gate.
>
> **If the project ever distributes** (multi-user web app, hosted service, shared install): this doc has to be filled out properly. The `docs-auditor-agent`'s Legal Decision Tree (Section 5.4) already flags the relevant follow-ups (Privacy Policy + AI Content disclosure for Q1/Q3 if SuperNoteOrganiser becomes user-distributed).
>
> Everything below is the universal template body, kept intact so this file is still useful as a template. Do not delete.

---

## API-Key Handling (the actual auth-adjacent surface that exists)

The single piece of credential-like material in the project:

| Item | Where | Notes |
|------|-------|-------|
| `ANTHROPIC_API_KEY` | `.env` (gitignored) → loaded by `dotenv.load_dotenv(override=False)` in `AppConfig.from_env` → read directly via `os.environ.get("ANTHROPIC_API_KEY")` in `_build_annotator` | Required only for `NOTE_ORGANISER_ANNOTATOR=claude` (the default). Setting `NOTE_ORGANISER_ANNOTATOR=stub` runs the whole pipeline offline with no key. |

**Failure mode:** if `claude` is selected but no key is present, `_build_annotator` raises a `RuntimeError` with a helpful message — this is the project's only auth-style "deny" path.

**`.env` is gitignored.** If `.env` ever appears in `git status`, that's a bug — the `code-quality-agent`'s vulnerability scanner should flag a committed key as a finding.

---

## Universal-Template Body Below

## Overview

This document outlines the authentication flow, including frontend implementation, backend verification, and security measures.

> **[BUILD THIS OUT]** — Replace the examples below with your actual auth implementation.

---

## Frontend Authentication Flow

### 1. User Signup & Login

#### [Primary Auth Method — e.g., Email/Password]
- **Implementation:** `[FILE PATH]`
- **Library:** [e.g., Supabase Auth, NextAuth, Clerk]
- **Process:**
  1. [STEP 1 — e.g., User submits email/password]
  2. [STEP 2 — e.g., Auth provider creates user]
  3. [STEP 3 — e.g., Session token stored]
  4. [STEP 4 — e.g., User redirected to dashboard]

#### OAuth Authentication (if applicable)
- **Implementation:** `[FILE PATH]`
- **Supported Providers:** [e.g., Google, GitHub, Apple]
- **Callback Handler:** `[FILE PATH]`
- **Process:**
  1. [DESCRIBE THE FULL OAUTH FLOW]

### 2. Session Management
- **Storage:** [HOW SESSIONS ARE STORED — cookies, localStorage, etc.]
- **Access:** [HOW TO GET THE CURRENT SESSION IN CODE]
- **Expiry:** [SESSION LIFETIME AND REFRESH BEHAVIOR]

### 3. Logout Flow
- **Implementation:** `[FILE PATH]`
- **Process:**
  1. [WHAT HAPPENS ON LOGOUT — tokens cleared, redirects, etc.]

### 4. Password Reset (if applicable)
- **Page:** `[ROUTE]`
- **Implementation:** `[FILE PATH]`
- **Process:**
  1. [DESCRIBE THE RESET FLOW]

---

## Backend Authentication

### Route Protection
- **Middleware/Guard:** `[FILE PATH]`
- **How it works:** [DESCRIBE HOW API ROUTES VERIFY AUTH]
- **Public routes:** [LIST ROUTES THAT DON'T REQUIRE AUTH]

### Token Verification
- **Token type:** [e.g., JWT, session cookie, API key]
- **Verification method:** [e.g., signature check, database lookup]
- **Where verified:** [e.g., middleware, each route handler]

---

## Authorization (Roles & Permissions)

> **[BUILD THIS OUT]** — Document your permission model.

| Role | Access Level | Description |
|------|-------------|-------------|
| `[ROLE]` | [DESCRIPTION] | [WHAT THEY CAN DO] |
| `[ROLE]` | [DESCRIPTION] | [WHAT THEY CAN DO] |

---

## Security Measures

### Row Level Security (if applicable)
- [DESCRIBE YOUR RLS APPROACH]
- [WHICH TABLES HAVE RLS]
- [PATTERN USED — e.g., "all user-facing tables enforce user-owns-row policies"]

### API Security
- [INPUT VALIDATION APPROACH]
- [RATE LIMITING]
- [CORS CONFIGURATION]

### Known Security Considerations
- [ANYTHING THE AI AGENT SHOULD BE AWARE OF]
- [e.g., "Service role key bypasses RLS — only use in server routes"]
- [e.g., "OAuth is configured but not active yet"]

---

## Environment Variables (Auth-Related)

| Variable | Purpose | Where Used |
|----------|---------|------------|
| `[VAR_NAME]` | [PURPOSE] | [SERVER/CLIENT/BOTH] |
