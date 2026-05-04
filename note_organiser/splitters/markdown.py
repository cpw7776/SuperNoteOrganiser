from __future__ import annotations

from datetime import datetime
from pathlib import Path

import frontmatter
from markdown_it import MarkdownIt

from ..models import RawChunk


class MarkdownHeadingSplitter:
    """Split a Markdown file at every `#`/`##`/`###` heading.

    Each heading + the prose under it (until the next heading of equal-or-shallower
    depth) becomes one RawChunk carrying that heading.
    """

    EXTENSIONS = {".md", ".markdown"}

    def __init__(self) -> None:
        self._md = MarkdownIt("commonmark")

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def split(self, path: Path, text: str) -> list[RawChunk]:
        post = frontmatter.loads(text)
        body = post.content
        device = post.metadata.get("device") if isinstance(post.metadata, dict) else None
        mtime = datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None

        tokens = self._md.parse(body)
        lines = body.splitlines()

        sections: list[tuple[str | None, list[str]]] = []
        current_heading: str | None = None
        current_start: int | None = None

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.type == "heading_open":
                if current_start is not None:
                    end = tok.map[0] if tok.map else len(lines)
                    sections.append((current_heading, lines[current_start:end]))
                inline = tokens[i + 1]
                current_heading = inline.content.strip()
                current_start = tok.map[1] if tok.map else None
                i += 3
                continue
            i += 1

        if current_start is not None:
            sections.append((current_heading, lines[current_start:]))

        if not sections:
            sections = [(None, lines)]

        chunks: list[RawChunk] = []
        for heading, content_lines in sections:
            content = "\n".join(content_lines).strip()
            if not content and not heading:
                continue
            chunks.append(
                RawChunk(
                    text=content if content else (heading or ""),
                    source_path=path,
                    heading=heading,
                    device=device,
                    mtime=mtime,
                )
            )
        return chunks
