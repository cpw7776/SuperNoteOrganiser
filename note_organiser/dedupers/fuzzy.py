from __future__ import annotations

import re

from rapidfuzz import fuzz

from ..models import Note, NoteGroup

_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z\-']{2,}")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


class FuzzyTitleDeduper:
    """Group near-duplicate notes by title similarity AND body overlap.

    Two notes belong to the same group when:
      - rapidfuzz token_set_ratio of titles >= title_threshold, AND
      - Jaccard of body tokens >= body_threshold.

    Both thresholds are conservative — better to under-merge than to fuse
    distinct ideas in a prototype.
    """

    def __init__(self, title_threshold: int = 85, body_threshold: float = 0.4) -> None:
        self._title_threshold = title_threshold
        self._body_threshold = body_threshold

    def group(self, notes: list[Note]) -> list[NoteGroup]:
        groups: list[list[Note]] = []
        body_tokens = [_tokens(n.body) for n in notes]
        for idx, note in enumerate(notes):
            placed = False
            for group in groups:
                seed = group[0]
                seed_idx = notes.index(seed)
                if (
                    fuzz.token_set_ratio(note.title, seed.title) >= self._title_threshold
                    and _jaccard(body_tokens[idx], body_tokens[seed_idx])
                    >= self._body_threshold
                ):
                    group.append(note)
                    placed = True
                    break
            if not placed:
                groups.append([note])
        return [NoteGroup(members=g) for g in groups]
