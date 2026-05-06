# Changelog — SuperNoteOrganiser

All notable changes to **SuperNoteOrganiser** are documented in this file.

> **Format:** Each entry includes: what changed, why, files affected, and any DB / API / Auth changes (DB = `Note` model + `JsonFileStore` schema; API = the Protocol contracts in `interfaces.py`; Auth = N/A for this single-user prototype).
> **Rule:** Every feature and every fix gets a changelog entry. No exceptions. (The `context-docs-agent` enforces this — line 4 of its gate can only ever show `Entry added — MANDATORY`.)

---

## [Unreleased]

### Make README.md a mandatory line in the Phase 5.5b docs gate — 2026-05-06

This project is public on GitHub (`cpw7776/SuperNoteOrganiser`); the root `README.md` is the front door for any visitor and must stay accurate as the project evolves. Promoted README review to a mandatory gate item in `.claude/agents/docs-auditor-agent.md`, mirroring the CHANGELOG mandatory rule in `context-docs-agent`.

**Changes:**
- New section **5.1.c — README.md (MANDATORY review every run)** in the docs-auditor: agent must read the README every Phase 5.5b run, decide between Update / Skip-with-explicit-reason, and record the action.
- New gate-block line **`1.c. README.md (MANDATORY): [Updated — {what} / Reviewed, no update needed because {explicit signal-grounded reason}]`** — same shape as the CHANGELOG mandatory line.
- Failure-mode section explicitly calls out 1.c: a bare skip ("no update needed" / "minor change") is a gate failure; the skip reason must reference a concrete signal the agent checked.
- `CLAUDE.md` Post-Feature Gates summary updated to flag the new mandatory line so any session reading CLAUDE.md upfront knows what's expected.

**Files affected:**
- `.claude/agents/docs-auditor-agent.md` — added 5.1.c, added 1.c to gate format, reinforced failure-mode rule
- `CLAUDE.md` — updated DOCUMENTATION GATE summary

**DB changes:** None.
**API changes:** None.
**Auth changes:** None.

---

### UI polish — note cards, wiki TOC, click-to-inspect, sticky settings, re-render — 2026-05-06

Iterative polish on the Streamlit UI based on dogfooding the app with real notes (stub + Venice runs):

- **Note cards on the wiki.** Each note on a category page is now wrapped in a `<div class="note-card">` with a 1px subtle border, faint background tint, rounded corners and generous internal padding — visually clear where one note ends and the next begins when scrolling a multi-note category. The `## Title` was switched from markdown auto-id headings to explicit `<h2 id="{slug}" class="note-card__title">` HTML so the slugs are guaranteed to match the TOC anchors. The renderer's `slugify()` is now also the source of truth for those ids.
- **"On this page" TOC.** Multi-note category pages get a sticky left-column TOC listing each note with anchor links. Skipped on the index page (it already has links to each category in its body). Implemented as `st.columns([1, 4])` with the TOC in the left column; CSS `position: sticky` keeps it in view on scroll.
- **Visual hierarchy for Action/Why/Purpose.** Each section (Original note, Action, Why, Purpose, Versions, Meta) renders as a coloured-left-border block with a small uppercase label. Colour key: Original=gray (italic), Action=green, Why=blue, Purpose=amber, Versions=purple. Tags render as blue chip pills, source filenames in amber monospace, devices in green monospace. Same visual language used in the wiki's rendered `.md` files AND the Notes-tab inspector — single shared CSS injected once at session start. `_section_html()` helper exists in both `app.py` and `karpathy_wiki.py` to keep the markup identical.
- **Notes tab redesign.** Removed the redundant "Inspect a note" selectbox below the table — selecting a row in the dataframe now drives the inspector via `on_select="rerun"` + `selection_mode="single-row"`. Kept the top search box + category filter (those filter the underlying table). Added a search-prompted placeholder showing the count and a caption "click a row to inspect" so the new affordance is discoverable.
- **Sticky sidebar settings.** Annotator / Model / Notes-dir / Wiki-dir all persist via URL query params (alongside the existing `tab` and `page` params). Survives browser refresh, Streamlit hot-reload, and full server restart. API keys stay in `.env`, never in the URL.
- **Re-render wiki button.** New sidebar button that re-runs `KarpathyWikiRenderer.render(store.all(), wiki_dir)` against the existing store — useful after any renderer formatting change without paying for re-annotation. Saved a Venice round trip during this session's iteration.
- **`use_container_width` deprecation cleanup.** Streamlit's `use_container_width` is removed after 2025-12-31; switched to `width="stretch"` on the dataframe.

**Modified:**
- `note_organiser/app.py` — large rewrite of `_render_wiki_browser` (TOC + columns + query-param-driven page select), `_render_notes_table` (search + filter + clickable rows + inspector), sidebar (sticky settings + re-render button), main (CSS injection)
- `note_organiser/renderers/karpathy_wiki.py` — `_render_note` emits explicit HTML cards with `<h2 id="...">` headings; `_meta_html()` produces structured tags/source/device markup; `_section_html()` helper

**DB changes:** None.
**API changes:** None — internal renderer/UI changes only.
**Auth changes:** None.

---

### Add Venice AI annotator + fix wiki navigation + fix relative imports — 2026-05-06

Three changes landed during initial bootstrap testing:

1. **VeniceAnnotator** — new `Annotator` impl using Venice AI's OpenAI-compatible API at `https://api.venice.ai/api/v1`. Embeds the `ANNOTATE_TOOL` / `MERGE_TOOL` JSON schemas in the system prompt and asks the model for plain JSON. Originally tried `response_format={"type": "json_object"}` but Venice rejects that on most of its catalogue (Llama 3.3 70B returns a 400: *"response_format is not supported by this model"*). Replaced with permissive parsing in `_extract_json`: tries raw JSON, then a ```` ```json ``` ```` fence, then the largest `{…}` slice. Verified end-to-end against `llama-3.3-70b` — produces correctly-shaped Action/Why/Purpose annotations following the system prompt's worked example. Wired into `config.py::_build_annotator` under `NOTE_ORGANISER_ANNOTATOR=venice`. Reads `VENICE_API_KEY` from env.

2. **Wiki navigation** — links inside rendered wiki pages (`[text](slug.md)`) were dead: `streamlit run` opened them in a new tab, and the new tab defaulted to the Inbox tab. Fix: rewrite links into explicit HTML anchors `<a href="?page=slug.md&tab=Wiki" target="_self">…</a>`, render with `unsafe_allow_html=True`, drive the page selectbox + active tab from `st.query_params`. Also replaced `st.tabs` with a stateful `st.radio` so the active view persists across query-param-triggered reruns. Bookmarkable URLs now work.

3. **Relative imports → absolute imports** — `note_organiser/app.py` had `from .config import …` and `from .stores import …`. `streamlit run note_organiser/app.py` execs the file as the top-level `__main__` module, so relative imports raised `ImportError: attempted relative import with no known parent package`. Switched to `from note_organiser.config import …` / `from note_organiser.stores import …`. Works because `pip install -e .` registers the package on `sys.path`.

**New files:**
- `note_organiser/annotators/venice.py` — VeniceAnnotator class

**Modified:**
- `pyproject.toml` — added `openai>=1.50` dependency
- `note_organiser/annotators/__init__.py` — export VeniceAnnotator
- `note_organiser/config.py` — `_build_annotator` dispatches on `venice`; AppConfig docstring updated
- `note_organiser/app.py` — sidebar dropdown adds `venice` option; wiki tab uses query-param routing + HTML anchors with `target="_self"`; tabs replaced with stateful radio
- `.env.example` — added `VENICE_API_KEY`; added comment showing venice-mode env vars

**DB changes:** None.
**API changes:** New concrete `Annotator` impl (`VeniceAnnotator`); the `Annotator` Protocol shape is unchanged.
**Auth changes:** None — but the project now reads a second optional env var (`VENICE_API_KEY`).

---

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
