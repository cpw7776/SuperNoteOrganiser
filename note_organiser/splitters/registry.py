from __future__ import annotations

from pathlib import Path

from ..interfaces import Splitter
from ..models import RawChunk


class ExtensionRoutedSplitter:
    """A composite Splitter that delegates to the first registered Splitter
    that claims to support a given path. Lets the pipeline treat heterogeneous
    inputs uniformly."""

    def __init__(self, splitters: list[Splitter]) -> None:
        self._splitters = splitters

    def supports(self, path: Path) -> bool:
        return any(s.supports(path) for s in self._splitters)

    def split(self, path: Path, text: str) -> list[RawChunk]:
        for s in self._splitters:
            if s.supports(path):
                return s.split(path, text)
        return []
