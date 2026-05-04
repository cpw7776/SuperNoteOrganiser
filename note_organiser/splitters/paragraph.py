from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from ..models import RawChunk

_BLANK_LINE = re.compile(r"\n\s*\n+")


class BlankLineParagraphSplitter:
    """Split plain-text dumps on blank lines. Heading is left None — the
    annotator will infer one downstream."""

    EXTENSIONS = {".txt"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def split(self, path: Path, text: str) -> list[RawChunk]:
        device = self._device_from_path(path)
        mtime = datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None
        paragraphs = [p.strip() for p in _BLANK_LINE.split(text) if p.strip()]
        return [
            RawChunk(text=p, source_path=path, heading=None, device=device, mtime=mtime)
            for p in paragraphs
        ]

    @staticmethod
    def _device_from_path(path: Path) -> str | None:
        stem = path.stem.lower()
        for device in ("phone", "laptop", "tablet", "desktop"):
            if device in stem:
                return device
        return None
