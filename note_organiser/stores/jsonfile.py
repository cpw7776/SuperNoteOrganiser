from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

from ..models import Note


class JsonFileStore:
    """Plain JSON-on-disk store keyed by `note_id`.

    Atomic writes: serialise to a sibling tempfile then `os.replace`, so a
    crash mid-write never leaves a half-written state file.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._notes: dict[str, Note] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        for nid, blob in data.items():
            try:
                self._notes[nid] = Note.model_validate(blob)
            except Exception:  # tolerate forward-incompatible state
                continue

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        payload = {nid: n.model_dump(mode="json") for nid, n in self._notes.items()}
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, self._path)

    def seen(self, note_id: str) -> bool:
        return note_id in self._notes

    def get(self, note_id: str) -> Note | None:
        return self._notes.get(note_id)

    def upsert(self, note: Note) -> None:
        self._notes[note.note_id] = note
        self._flush()

    def delete(self, note_id: str) -> None:
        if note_id in self._notes:
            del self._notes[note_id]
            self._flush()

    def all(self) -> list[Note]:
        return list(self._notes.values())

    def taxonomy(self) -> list[str]:
        counter = Counter(n.category for n in self._notes.values())
        return [c for c, _ in counter.most_common()]

    def reset(self) -> None:
        self._notes = {}
        if self._path.exists():
            self._path.unlink()
