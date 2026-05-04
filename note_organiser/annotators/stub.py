from __future__ import annotations

import re
from collections import Counter

from ..models import Action, Note, NoteGroup, RawChunk

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "for", "is",
    "are", "was", "were", "be", "been", "this", "that", "with", "as", "it",
    "its", "you", "your", "i", "me", "my", "we", "our", "they", "their", "so",
    "if", "at", "by", "from", "have", "has", "had", "do", "does", "did", "not",
    "no", "yes", "than", "then", "into", "out", "up", "down", "there", "here",
    "what", "when", "where", "why", "how", "would", "could", "should", "will",
    "can", "may", "might", "just", "also", "more", "most", "less", "least",
    "some", "any", "all", "each", "every",
}


class StubAnnotator:
    """Offline annotator. Uses simple heuristics so the pipeline can be
    exercised end-to-end without an Anthropic API key. NOT a substitute for
    the real model — quality is poor by design."""

    def annotate(self, chunk: RawChunk, taxonomy: list[str]) -> Note:
        title = chunk.heading or self._heuristic_title(chunk.text)
        category = chunk.heading or (taxonomy[0] if taxonomy else "Uncategorised")
        tags = self._top_keywords(chunk.text, k=4)
        summary = self._first_sentence(chunk.text)
        action_text = f"Reflect on: {summary}"
        return Note(
            note_id=chunk.note_id,
            title=title,
            body=chunk.text,
            category=category,
            tags=tags,
            summary=summary,
            action=Action(
                action=action_text,
                why="Stub annotator: replace with ClaudeAnnotator for real reasoning.",
                purpose="To exercise the pipeline end-to-end without an API key.",
            ),
            sources=[chunk.source_path.name],
            devices=[chunk.device] if chunk.device else [],
        )

    def merge(self, group: NoteGroup) -> Note:
        if group.is_singleton:
            return group.members[0]
        seed = group.members[0]
        merged_body = "\n\n---\n\n".join(m.body for m in group.members)
        return Note(
            note_id=seed.note_id,
            title=seed.title,
            body=merged_body,
            category=seed.category,
            tags=sorted({t for m in group.members for t in m.tags}),
            summary=seed.summary,
            action=seed.action,
            sources=sorted({s for m in group.members for s in m.sources}),
            devices=sorted({d for m in group.members for d in m.devices}),
            versions=[m.body for m in group.members],
        )

    @staticmethod
    def _first_sentence(text: str) -> str:
        match = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
        first = match[0] if match else text.strip()
        return first[:160]

    @classmethod
    def _heuristic_title(cls, text: str) -> str:
        first = cls._first_sentence(text)
        words = first.split()
        return " ".join(words[:9]) + ("…" if len(words) > 9 else "")

    @staticmethod
    def _top_keywords(text: str, k: int = 4) -> list[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", text.lower())
        words = [w for w in words if w not in _STOPWORDS]
        common = [w for w, _ in Counter(words).most_common(k)]
        return common
