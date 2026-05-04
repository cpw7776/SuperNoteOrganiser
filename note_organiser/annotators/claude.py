from __future__ import annotations

import os

from anthropic import Anthropic

from ..models import Action, Note, NoteGroup, RawChunk
from ..prompts import ANNOTATE_TOOL, MERGE_TOOL, system_blocks


class ClaudeAnnotator:
    """Annotator backed by the Anthropic SDK. Uses tool-use to force
    structured output and prompt caching on the (stable) system prompt."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1024,
        client: Anthropic | None = None,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = client or Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def annotate(self, chunk: RawChunk, taxonomy: list[str]) -> Note:
        user_text = self._user_message(chunk)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_blocks(taxonomy),
            tools=[ANNOTATE_TOOL],
            tool_choice={"type": "tool", "name": "annotate_note"},
            messages=[{"role": "user", "content": user_text}],
        )
        payload = self._extract_tool_input(response, "annotate_note")
        return Note(
            note_id=chunk.note_id,
            title=payload["title"],
            body=chunk.text,
            category=payload["category"],
            tags=list(payload.get("tags", [])),
            summary=payload.get("summary", ""),
            action=Action(
                action=payload["action"],
                why=payload["why"],
                purpose=payload["purpose"],
            ),
            sources=[str(chunk.source_path.name)],
            devices=[chunk.device] if chunk.device else [],
        )

    def merge(self, group: NoteGroup) -> Note:
        if group.is_singleton:
            return group.members[0]
        bodies = "\n\n---\n\n".join(
            f"[from {m.sources[0] if m.sources else 'unknown'}"
            f"{', device=' + m.devices[0] if m.devices else ''}]\n{m.body}"
            for m in group.members
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_blocks(taxonomy=[]),
            tools=[MERGE_TOOL],
            tool_choice={"type": "tool", "name": "merge_notes"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "These notes appear to describe the same idea captured at "
                        "different times or on different devices. Produce a single "
                        "canonical merged note via the `merge_notes` tool, "
                        "preserving every distinct insight.\n\n" + bodies
                    ),
                }
            ],
        )
        payload = self._extract_tool_input(response, "merge_notes")

        seed = group.members[0]
        return Note(
            note_id=seed.note_id,
            title=payload["title"],
            body=payload["merged_body"],
            category=payload["category"],
            tags=list(payload.get("tags", [])),
            summary=payload.get("summary", seed.summary),
            action=Action(
                action=payload["action"],
                why=payload["why"],
                purpose=payload["purpose"],
            ),
            sources=sorted({s for m in group.members for s in m.sources}),
            devices=sorted({d for m in group.members for d in m.devices}),
            versions=[m.body for m in group.members],
        )

    @staticmethod
    def _user_message(chunk: RawChunk) -> str:
        parts = [f"Source file: {chunk.source_path.name}"]
        if chunk.device:
            parts.append(f"Device: {chunk.device}")
        if chunk.heading:
            parts.append(f"Original heading: {chunk.heading}")
        parts.append("Note text:\n" + chunk.text)
        parts.append("Call the `annotate_note` tool with the structured annotation.")
        return "\n\n".join(parts)

    @staticmethod
    def _extract_tool_input(response, tool_name: str) -> dict:
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
                return dict(block.input)
        raise RuntimeError(f"Model did not call expected tool {tool_name!r}.")
