# SuperNoteOrganiser

Prototype agent app that ingests notes scattered across `.txt` and `.md` files
(possibly captured on different devices at different times), groups them by
heading / tag / category, and emits a Karpathy-style Markdown wiki. Every note
also gets an **Action / Why / Purpose** block reasoned out by Claude.

## Quick start

```bash
pip install -e .
cp .env.example .env   # add your ANTHROPIC_API_KEY
streamlit run note_organiser/app.py
```

Drop notes into `notes/`. Click **Process new notes** in the sidebar. The
generated wiki appears in `wiki/`. Re-running only processes notes that are new
or have changed (content-hash dedupe via `state/notes.json`).

Run with no API key by setting `NOTE_ORGANISER_ANNOTATOR=stub` — the offline
stub annotator wires the whole pipeline so you can see the output shape.

## Architecture

The pipeline is intentionally modular. Every stage is a `typing.Protocol` in
`note_organiser/interfaces.py`; concrete implementations live under
`splitters/`, `annotators/`, `dedupers/`, `stores/`, `renderers/`. The
orchestrator in `pipeline.py` knows nothing about file formats, LLM providers,
or storage. Wiring happens in one place — `config.py::build_pipeline`.

| Stage     | Default impl                          | Swap by writing… |
|-----------|---------------------------------------|------------------|
| Split     | `MarkdownHeadingSplitter`, `BlankLineParagraphSplitter` | another `Splitter` |
| Annotate  | `ClaudeAnnotator` (Sonnet 4.6, prompt-cached) | another `Annotator` |
| Dedupe    | `FuzzyTitleDeduper`                   | another `Deduper` |
| Store     | `JsonFileStore`                       | another `Store` |
| Render    | `KarpathyWikiRenderer`                | another `Renderer` |
