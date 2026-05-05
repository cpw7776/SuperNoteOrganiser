# Persistence Reference — SuperNoteOrganiser

> **Reframed for SuperNoteOrganiser.** The project has no SQL database — persistence is a single JSON file on disk (`state/notes.json`) handled by `JsonFileStore`. The universal-template "Database Reference Guide" structure is repurposed here to document that store: the on-disk schema, the in-memory model, and the change-impact rules. Update this file when the `Note` model, the `JsonFileStore`, or the `state/` layout changes.
>
> Universal-template note kept for reference: *"Comprehensive reference for all database interactions, data structures, and change impact analysis."*

**Last Updated:** 2026-05-05
**Version:** 1.0

---

## Recent Changes

> Document every model / store change here, newest first.

### v1.0.0 — 2026-05-05 — Initial bootstrap
- `Note` model (Pydantic v2) with fields: `note_id`, `title`, `body`, `category`, `tags`, `summary`, `action` (Action sub-model), `sources`, `devices`, `versions`.
- `Action` sub-model with `action`, `why`, `purpose`.
- `RawChunk` model with `text`, `source_path`, `heading?`, `device?`, `mtime?`, plus a `note_id` property derived from `content_hash(text)`.
- `NoteGroup` model wrapping `members: list[Note]` plus `is_singleton` property.
- `JsonFileStore` providing atomic writes via tempfile + `os.replace`.

---

## Storage Surface

### Path
- `state/notes.json` — single JSON object, top-level keys are `note_id` strings (12-char sha256 prefix), values are serialised `Note` records.
- Parent directory created on first write (`_flush()` calls `mkdir(parents=True, exist_ok=True)`).
- Git: `state/*.json` is `.gitignore`d (only `state/.gitkeep` is tracked).

### Atomicity
`JsonFileStore._flush()` writes to `state/notes.json.tmp` then `os.replace(tmp, final)` — atomic on POSIX. A crash mid-write either leaves the old file intact or atomically swaps to the new one; never a half-written file.

### Forward-compat tolerance
On load, individual record-validation errors are silently dropped (`except Exception: continue`). Rationale: a future schema change adds a non-breaking field to `Note`; rolling back to an older binary still loads what it can. Don't tighten this without thinking through the rollback story.

---

## In-Memory Model — `note_organiser/models.py`

### `Note` (Pydantic BaseModel)
| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `note_id` | `str` | required | Stable id; equals `content_hash(text)` of the source RawChunk text |
| `title` | `str` | required | Short, human-readable; what wiki TOC entries display |
| `body` | `str` | required | Full prose body of the note |
| `category` | `str` | required | Bucket name; influences wiki folder layout |
| `tags` | `list[str]` | `[]` | Free-form tags; used by renderer for backlink discovery |
| `summary` | `str` | `""` | Optional 1-line summary; mostly for hover/preview UI |
| `action` | `Action` | required | The Action / Why / Purpose triad |
| `sources` | `list[str]` | `[]` | Original file paths the note derives from |
| `devices` | `list[str]` | `[]` | Device hints (e.g. "phone", "laptop") |
| `versions` | `list[str]` | `[]` | Original device-attributed snippets retained after a deduper-driven merge |

### `Action` (Pydantic BaseModel)
| Field | Type | Purpose |
|-------|------|---------|
| `action` | `str` | What the user should do |
| `why` | `str` | Why it matters / motivation |
| `purpose` | `str` | The higher-level purpose this serves |

### `RawChunk` (Pydantic BaseModel)
| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `text` | `str` | required | The pre-annotation prose |
| `source_path` | `Path` | required | Where the chunk was extracted from |
| `heading` | `str \| None` | `None` | If the chunk came from a Markdown heading |
| `device` | `str \| None` | `None` | Device hint if a Splitter inferred one |
| `mtime` | `datetime \| None` | `None` | Source file mtime; informational only |

`RawChunk.note_id` is a property (not a field) computed from `content_hash(text)` — derived, never stored.

### `NoteGroup` (Pydantic BaseModel)
| Field | Type | Purpose |
|-------|------|---------|
| `members` | `list[Note]` | Notes the deduper grouped together |

`NoteGroup.is_singleton` — convenience property; `len(members) == 1`.

### `content_hash(text: str) -> str`
- Lowercase + collapse whitespace (`re.sub(r"\s+", " ", text).strip().lower()`).
- sha256 of the utf-8 bytes.
- Truncate to 12 hex chars.
- **Stable across runs and across devices** — that's the whole point. Same text → same id → already-seen → skip.

---

## `JsonFileStore` API

`JsonFileStore` satisfies the `Store` Protocol (see `docs/context/API_REFERENCE.md`).

| Method | Signature | Behaviour |
|--------|-----------|-----------|
| `seen` | `(note_id: str) -> bool` | Has this id been ingested? Used by the pipeline to short-circuit re-processing. |
| `get` | `(note_id: str) -> Note \| None` | Lookup; returns None if absent. |
| `upsert` | `(note: Note) -> None` | Insert or update by `note.note_id`. Writes immediately (atomic flush). |
| `delete` | `(note_id: str) -> None` | Remove if present; flush. |
| `all` | `() -> list[Note]` | Snapshot of every stored Note. |
| `taxonomy` | `() -> list[str]` | Categories ordered by descending frequency (uses `collections.Counter.most_common`). |
| `reset` | `() -> None` | Drop in-memory cache and unlink the JSON file. Used by "Reset state" UI control. |

**Threading note:** `JsonFileStore` is single-threaded by design. The Streamlit app is single-process; if a future feature parallelises ingestion, the store needs a lock around `_flush`.

---

## Change-Impact Rules

| Change type | Required updates |
|-------------|-------------------|
| New field on `Note` | Update `models.py`. Confirm `JsonFileStore._load` tolerance still loads old state. Update this doc. Update `API_REFERENCE.md` if the Annotator Protocol shape changes. Update CHANGELOG. |
| New field on `RawChunk` | Update `models.py`. Update Splitter impls if they need to populate it. Update this doc. Update CHANGELOG. |
| Rename a field | Add a migration — older `state/notes.json` files won't have the new name. Either bump the file format version + migrate on load, OR keep the old name as an alias for a release. |
| Replace `JsonFileStore` with another `Store` impl (e.g. SQLite) | The Protocol is the boundary; adding a new impl doesn't change this doc — but updating the *default* in `config.py::build_pipeline` does. Update this doc to point to the new default schema. |
| Change `content_hash` | **Breaking change.** Every existing note's id changes — re-ingest is required. Don't do this without an explicit migration story (delete-and-rebuild is acceptable for the prototype). |

---

## On-Disk Layout (`state/`)

```
state/
├── .gitkeep            ← tracked
└── notes.json          ← runtime, .gitignored
    {
      "<note_id>": {
        "note_id": "...",
        "title": "...",
        "body": "...",
        "category": "...",
        "tags": [],
        "summary": "",
        "action": { "action": "...", "why": "...", "purpose": "..." },
        "sources": [],
        "devices": [],
        "versions": []
      },
      ...
    }
```
