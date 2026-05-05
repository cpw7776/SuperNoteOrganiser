# Extension API Reference — SuperNoteOrganiser

> **Reframed for SuperNoteOrganiser.** The project has no HTTP API. The "API" that matters here is the set of **Protocol contracts** in `note_organiser/interfaces.py` — these are the typed boundaries the orchestrator depends on. They are the project's extension surface: writing a new Splitter / Annotator / Deduper / Store / Renderer means implementing one of these Protocols. Update this file when a Protocol shape changes, when a new Protocol is added, or when a new concrete impl is registered in `config.py::build_pipeline`.
>
> Universal-template note kept for reference: *"This document provides a comprehensive reference for all API routes, organized by category."*

**Last Updated:** 2026-05-05
**Version:** 1.0

---

## Where the Protocols live

`note_organiser/interfaces.py` declares all five Protocols, each decorated with `@runtime_checkable`. They reference the Pydantic models in `note_organiser/models.py` (`RawChunk`, `Note`, `NoteGroup`).

The orchestrator (`note_organiser/pipeline.py`) imports only the Protocols. It never imports concrete impls.

Wiring concrete impls happens in exactly one place: **`note_organiser/config.py::build_pipeline()`**.

---

## Protocols

### `Splitter`

Turn a file's text into pre-annotation chunks.

```python
@runtime_checkable
class Splitter(Protocol):
    def supports(self, path: Path) -> bool: ...
    def split(self, path: Path, text: str) -> list[RawChunk]: ...
```

| Method | Returns | Purpose |
|--------|---------|---------|
| `supports(path)` | `bool` | Whether this splitter handles a given file. The `ExtensionRoutedSplitter` uses this to dispatch by file extension. |
| `split(path, text)` | `list[RawChunk]` | Produce one or more `RawChunk`s; each chunk's id is derived from its text via `content_hash`. |

**Default impls (registered in `config.py`):**
- `MarkdownHeadingSplitter` — splits on `#`/`##`/`###`
- `BlankLineParagraphSplitter` — splits on blank lines
- `ExtensionRoutedSplitter` — composite; picks the right impl by extension

**Adding a new Splitter:** Implement the Protocol, instantiate it inside the `ExtensionRoutedSplitter` list in `config.py::build_pipeline` (or pass via `AppConfig.extra_splitters`).

---

### `Annotator`

Turn a `RawChunk` into a fully-annotated `Note`. Also merges grouped notes.

```python
@runtime_checkable
class Annotator(Protocol):
    def annotate(self, chunk: RawChunk, taxonomy: list[str]) -> Note: ...
    def merge(self, group: NoteGroup) -> Note: ...
```

| Method | Returns | Purpose |
|--------|---------|---------|
| `annotate(chunk, taxonomy)` | `Note` | Produce a Note from a single chunk. `taxonomy` is the existing categories, ranked by frequency, so the annotator can prefer reusing one over inventing a new one. |
| `merge(group)` | `Note` | Reduce a `NoteGroup` (multiple notes the deduper believes describe the same idea) to a single canonical Note. The merged note's `versions` field MUST contain the original device-attributed snippets. |

**Default impls:**
- `ClaudeAnnotator` (`note_organiser/annotators/claude.py`) — calls Anthropic SDK; uses Sonnet 4.6 by default; supports prompt caching.
- `StubAnnotator` (`note_organiser/annotators/stub.py`) — offline, deterministic; for pipeline tests with no API key.

**Adding a new Annotator:** Implement the Protocol. Wire it into `_build_annotator` in `config.py` and add a value to the `NOTE_ORGANISER_ANNOTATOR` env-var dispatch.

---

### `Deduper`

Group `Note`s the impl believes describe the same idea.

```python
@runtime_checkable
class Deduper(Protocol):
    def group(self, notes: list[Note]) -> list[NoteGroup]: ...
```

| Method | Returns | Purpose |
|--------|---------|---------|
| `group(notes)` | `list[NoteGroup]` | Each input note appears in exactly one group. Singleton groups are valid (`is_singleton == True`). |

**Default impl:**
- `FuzzyTitleDeduper` (`note_organiser/dedupers/fuzzy.py`) — `rapidfuzz` on titles + cosine on bodies; thresholds in `AppConfig.title_threshold` (default 85) and `AppConfig.body_threshold` (default 0.4).

**Adding a new Deduper** (e.g. embedding-based cosine): Implement the Protocol. Swap in `config.py::build_pipeline`.

---

### `Store`

Persist `Note`s by id; track which ids have been seen.

```python
@runtime_checkable
class Store(Protocol):
    def seen(self, note_id: str) -> bool: ...
    def get(self, note_id: str) -> Note | None: ...
    def upsert(self, note: Note) -> None: ...
    def delete(self, note_id: str) -> None: ...
    def all(self) -> list[Note]: ...
    def taxonomy(self) -> list[str]: ...
    def reset(self) -> None: ...
```

| Method | Returns | Purpose |
|--------|---------|---------|
| `seen(note_id)` | `bool` | The pipeline calls this to skip already-ingested chunks (idempotency). |
| `get(note_id)` | `Note \| None` | Fetch one note. |
| `upsert(note)` | `None` | Insert or replace by `note.note_id`. Implementations should make writes durable before returning. |
| `delete(note_id)` | `None` | Remove if present. |
| `all()` | `list[Note]` | Snapshot of every stored note (for renderer + UI). |
| `taxonomy()` | `list[str]` | Categories ordered by descending frequency — fed back into Annotator.annotate(). |
| `reset()` | `None` | Drop everything. Backs the "Reset state" UI control. |

**Default impl:**
- `JsonFileStore` (`note_organiser/stores/jsonfile.py`) — single JSON file at `state/notes.json`, atomic writes via tempfile + `os.replace`. Schema documented in `docs/context/database_reference_guide.md`.

**Adding a new Store** (e.g. SQLite): Implement the Protocol. Swap in `config.py::build_pipeline`. Update `database_reference_guide.md` to document the new default schema.

---

### `Renderer`

Emit notes to a target medium.

```python
@runtime_checkable
class Renderer(Protocol):
    def render(self, notes: list[Note], out_dir: Path) -> None: ...
```

| Method | Returns | Purpose |
|--------|---------|---------|
| `render(notes, out_dir)` | `None` | Write every note's representation under `out_dir`. The renderer owns layout decisions (folders by category, backlinks, TOC). |

**Default impl:**
- `KarpathyWikiRenderer` (`note_organiser/renderers/karpathy_wiki.py`) — Karpathy-style cross-linked Markdown wiki. Backlink threshold: `AppConfig.backlink_min_shared_tags` (default 2 shared tags between two notes triggers a backlink).

**Adding a new Renderer** (e.g. Logseq, Obsidian, single-page HTML): Implement the Protocol. Swap in `config.py::build_pipeline`.

---

## Wiring (`config.py::build_pipeline`)

The single function that instantiates all five concrete Protocols and assembles the `Pipeline`. **No code outside this function should call a concrete-class constructor for a Protocol-satisfying type.**

```python
def build_pipeline(config: AppConfig) -> Pipeline:
    splitter  = ExtensionRoutedSplitter([
                  MarkdownHeadingSplitter(),
                  BlankLineParagraphSplitter(),
                  *config.extra_splitters,
                ])
    annotator = _build_annotator(config)            # claude or stub
    deduper   = FuzzyTitleDeduper(...)
    store     = JsonFileStore(config.state_path)
    renderer  = KarpathyWikiRenderer(
                  backlink_min_shared_tags=config.backlink_min_shared_tags,
                )
    return Pipeline(splitter=splitter, annotator=annotator,
                    deduper=deduper, store=store, renderer=renderer,
                    notes_dir=config.notes_dir, wiki_dir=config.wiki_dir)
```

### Change-impact rules

| Change type | Required updates |
|-------------|-------------------|
| New method on a Protocol | Update `interfaces.py`. Update every concrete impl (compiler error if missing — Protocols are runtime-checkable). Update this doc. Update CHANGELOG. |
| Rename a Protocol method | Same as above; rename in every impl. Bump version in this doc. |
| New Protocol | Add to `interfaces.py`. Add at least one concrete impl. Wire into `config.py::build_pipeline`. Add a new section to this doc. CHANGELOG. |
| New concrete impl | Wire into `config.py::build_pipeline` (or expose via `AppConfig.extra_splitters` / equivalent). Add it to the "Default impls" list under the relevant Protocol section. CHANGELOG. |
| Change a Protocol method's signature | Same as "New method" — but call out the breaking change explicitly in CHANGELOG. |

---

## Why this is the project's "API"

The Protocol contracts are the *only* surface a third party (or the maintainer adding a new backend) interacts with. Everything else — the Streamlit UI, the Pipeline orchestrator, the models — is internal. If a Protocol changes shape without updating this doc, that's a silent contract break.
