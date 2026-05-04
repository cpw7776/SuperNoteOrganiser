from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def content_hash(text: str) -> str:
    return hashlib.sha256(_normalise(text).encode("utf-8")).hexdigest()[:12]


class RawChunk(BaseModel):
    """One pre-annotation note unit produced by a Splitter."""

    text: str
    source_path: Path
    heading: str | None = None
    device: str | None = None
    mtime: datetime | None = None

    @property
    def note_id(self) -> str:
        return content_hash(self.text)


class Action(BaseModel):
    action: str
    why: str
    purpose: str


class Note(BaseModel):
    note_id: str
    title: str
    body: str
    category: str
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    action: Action
    sources: list[str] = Field(default_factory=list)
    devices: list[str] = Field(default_factory=list)
    versions: list[str] = Field(
        default_factory=list,
        description="Original device-attributed snippets, kept after a merge.",
    )


class NoteGroup(BaseModel):
    """A cluster of Notes the Deduper believes describe the same idea."""

    members: list[Note]

    @property
    def is_singleton(self) -> bool:
        return len(self.members) == 1
