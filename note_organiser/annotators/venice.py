"""Venice AI annotator — uses Venice's OpenAI-compatible API.

Venice hosts open-source models (Llama, Qwen, Mistral, etc.) behind an
OpenAI-compatible chat-completions endpoint. Structured-output support is
inconsistent across the model catalogue: most models reject
`response_format={"type": "json_object"}` with a 400. We therefore prompt
for plain JSON and extract it permissively from the model's text response
(handling raw JSON, JSON wrapped in code fences, and JSON embedded in prose).
"""

from __future__ import annotations

import json
import os
import re

from openai import OpenAI

from ..models import Action, Note, NoteGroup, RawChunk
from ..prompts import ANNOTATE_TOOL, MERGE_TOOL, SYSTEM_PROMPT

VENICE_BASE_URL = "https://api.venice.ai/api/v1"
DEFAULT_VENICE_MODEL = "llama-3.3-70b"


class VeniceAnnotator:
    """Annotator backed by Venice AI via the OpenAI SDK.

    Uses `response_format={"type": "json_object"}` and embeds the JSON
    schema in the system prompt; the SDK enforces JSON-only output.
    """

    def __init__(
        self,
        model: str = DEFAULT_VENICE_MODEL,
        max_tokens: int = 1024,
        client: OpenAI | None = None,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = client or OpenAI(
            api_key=os.environ.get("VENICE_API_KEY"),
            base_url=VENICE_BASE_URL,
        )

    def annotate(self, chunk: RawChunk, taxonomy: list[str]) -> Note:
        system = self._system_prompt(taxonomy, ANNOTATE_TOOL)
        user_text = self._user_message(chunk)
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_text},
            ],
        )
        payload = self._extract_json(response)
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
        system = self._system_prompt([], MERGE_TOOL)
        user_text = (
            "These notes appear to describe the same idea captured at "
            "different times or on different devices. Produce a single "
            "canonical merged note as JSON matching the schema, preserving "
            "every distinct insight.\n\n" + bodies
        )
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_text},
            ],
        )
        payload = self._extract_json(response)
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
    def _system_prompt(taxonomy: list[str], tool: dict) -> str:
        taxonomy_block = (
            "Running taxonomy (existing categories, in order of frequency):\n"
            + ("\n".join(f"- {c}" for c in taxonomy) if taxonomy else "- (empty)")
        )
        schema_desc = json.dumps(tool["input_schema"], indent=2)
        json_instruction = (
            "\n\nReturn ONLY a single JSON object matching this schema "
            "(no prose, no code fences, no commentary):\n"
            f"```\n{schema_desc}\n```"
        )
        return SYSTEM_PROMPT + "\n\n" + taxonomy_block + json_instruction

    @staticmethod
    def _user_message(chunk: RawChunk) -> str:
        parts = [f"Source file: {chunk.source_path.name}"]
        if chunk.device:
            parts.append(f"Device: {chunk.device}")
        if chunk.heading:
            parts.append(f"Original heading: {chunk.heading}")
        parts.append("Note text:\n" + chunk.text)
        parts.append("Respond with the structured annotation as JSON.")
        return "\n\n".join(parts)

    @staticmethod
    def _extract_json(response) -> dict:
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Venice model returned empty content.")

        # 1. Try parsing the whole response as JSON (best case).
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 2. Try a fenced ```json … ``` (or ``` … ```) block.
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if fence:
            try:
                return json.loads(fence.group(1))
            except json.JSONDecodeError:
                pass

        # 3. Take the largest balanced {...} slice in the response.
        first = content.find("{")
        last = content.rfind("}")
        if first != -1 and last > first:
            try:
                return json.loads(content[first : last + 1])
            except json.JSONDecodeError:
                pass

        raise RuntimeError(
            f"Venice model returned non-JSON content: {content[:300]!r}"
        )
