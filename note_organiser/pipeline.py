from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from .interfaces import Annotator, Deduper, Renderer, Splitter, Store
from .models import Note, RawChunk

ProgressCb = Callable[[str, int, int], None]


@dataclass
class PipelineResult:
    discovered: int = 0
    new_chunks: int = 0
    annotated: int = 0
    merged_groups: int = 0
    notes_total: int = 0
    skipped_seen: int = 0
    errors: list[str] = field(default_factory=list)


class Pipeline:
    """The orchestrator. Knows nothing about Markdown, Anthropic, JSON, or
    Streamlit — only the five Protocols it composes.
    """

    def __init__(
        self,
        splitter: Splitter,
        annotator: Annotator,
        deduper: Deduper,
        store: Store,
        renderer: Renderer,
        notes_dir: Path,
        wiki_dir: Path,
    ) -> None:
        self._splitter = splitter
        self._annotator = annotator
        self._deduper = deduper
        self._store = store
        self._renderer = renderer
        self._notes_dir = notes_dir
        self._wiki_dir = wiki_dir

    def discover_chunks(self) -> list[RawChunk]:
        chunks: list[RawChunk] = []
        for path in sorted(self._iter_files(self._notes_dir)):
            if not self._splitter.supports(path):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            chunks.extend(self._splitter.split(path, text))
        return chunks

    def run(self, progress: ProgressCb | None = None) -> PipelineResult:
        result = PipelineResult()
        chunks = self.discover_chunks()
        result.discovered = len(chunks)

        new_chunks = [c for c in chunks if not self._store.seen(c.note_id)]
        result.new_chunks = len(new_chunks)
        result.skipped_seen = result.discovered - result.new_chunks

        fresh_notes: list[Note] = []
        for i, chunk in enumerate(new_chunks, 1):
            if progress:
                progress("annotate", i, len(new_chunks))
            try:
                note = self._annotator.annotate(chunk, self._store.taxonomy())
            except Exception as exc:
                result.errors.append(f"annotate({chunk.source_path.name}): {exc}")
                continue
            fresh_notes.append(note)
            self._store.upsert(note)
            result.annotated += 1

        all_notes = self._store.all()
        groups = self._deduper.group(all_notes)
        merged_notes: list[Note] = []
        for i, group in enumerate(groups, 1):
            if progress:
                progress("merge", i, len(groups))
            if group.is_singleton:
                merged_notes.append(group.members[0])
                continue
            try:
                merged = self._annotator.merge(group)
            except Exception as exc:
                result.errors.append(f"merge: {exc}")
                merged_notes.extend(group.members)
                continue
            self._store.upsert(merged)
            for member in group.members:
                if member.note_id != merged.note_id:
                    self._store.delete(member.note_id)
            merged_notes.append(merged)
            result.merged_groups += 1

        if progress:
            progress("render", 1, 1)
        self._renderer.render(merged_notes, self._wiki_dir)
        result.notes_total = len(merged_notes)
        return result

    @staticmethod
    def _iter_files(root: Path) -> Iterable[Path]:
        if not root.exists():
            return []
        return [p for p in root.rglob("*") if p.is_file() and not p.name.startswith(".")]
