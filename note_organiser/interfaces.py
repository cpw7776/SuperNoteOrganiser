"""Stage contracts. The pipeline depends on these Protocols only — never on
concrete implementations. Add a new backend by writing a class that satisfies
the relevant Protocol and registering it in `config.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from .models import Note, NoteGroup, RawChunk


@runtime_checkable
class Splitter(Protocol):
    def supports(self, path: Path) -> bool: ...
    def split(self, path: Path, text: str) -> list[RawChunk]: ...


@runtime_checkable
class Annotator(Protocol):
    def annotate(self, chunk: RawChunk, taxonomy: list[str]) -> Note: ...
    def merge(self, group: NoteGroup) -> Note: ...


@runtime_checkable
class Deduper(Protocol):
    def group(self, notes: list[Note]) -> list[NoteGroup]: ...


@runtime_checkable
class Store(Protocol):
    def seen(self, note_id: str) -> bool: ...
    def get(self, note_id: str) -> Note | None: ...
    def upsert(self, note: Note) -> None: ...
    def delete(self, note_id: str) -> None: ...
    def all(self) -> list[Note]: ...
    def taxonomy(self) -> list[str]: ...
    def reset(self) -> None: ...


@runtime_checkable
class Renderer(Protocol):
    def render(self, notes: list[Note], out_dir: Path) -> None: ...
