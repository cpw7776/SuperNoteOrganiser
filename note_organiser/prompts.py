"""Prompts and tool schemas for the Claude annotator.

The system prompt is large and reused across every note in a batch, so it is
designed to be stable enough to benefit from prompt caching (`cache_control`
applied by the annotator on the last system block).
"""

from __future__ import annotations

ANNOTATE_TOOL = {
    "name": "annotate_note",
    "description": (
        "Capture the structured annotation for a single note: a clean title, "
        "the best-fitting category, tags, a one-line summary, and the "
        "Action / Why / Purpose triple."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Short, specific title (max ~80 chars). Avoid generic words like 'Note'.",
            },
            "category": {
                "type": "string",
                "description": (
                    "Pick from the taxonomy if a category fits well. "
                    "Only invent a new category when nothing fits."
                ),
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-6 lower-case tags, hyphenated.",
            },
            "summary": {
                "type": "string",
                "description": "One sentence capturing the note's idea.",
            },
            "action": {
                "type": "string",
                "description": "A concrete behaviour, habit, or rule the user could adopt.",
            },
            "why": {
                "type": "string",
                "description": "The reasoning that makes the action follow from the note's logic.",
            },
            "purpose": {
                "type": "string",
                "description": "The deeper aim or value the action serves.",
            },
        },
        "required": ["title", "category", "tags", "summary", "action", "why", "purpose"],
    },
}


MERGE_TOOL = {
    "name": "merge_notes",
    "description": (
        "Produce a single canonical note that fairly merges several near-duplicate "
        "notes captured at different times or on different devices. Preserve every "
        "distinct insight; do not invent new claims."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "category": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
            "merged_body": {
                "type": "string",
                "description": "The unified note body, written as the user would write it.",
            },
            "action": {"type": "string"},
            "why": {"type": "string"},
            "purpose": {"type": "string"},
        },
        "required": [
            "title",
            "category",
            "tags",
            "summary",
            "merged_body",
            "action",
            "why",
            "purpose",
        ],
    },
}


SYSTEM_PROMPT = """\
You are the SuperNoteOrganiser annotator. The user keeps notes across many
devices — phone, laptop, paper photos — under loose, overlapping headings such
as "Original Thoughts", "Memories", "Favourite Quotes", "South America". Your
job is to take ONE raw note at a time and return a structured annotation via
the `annotate_note` tool.

Guidelines:
- Reuse an existing category from the running taxonomy when one fits. Only
  propose a new category when nothing in the taxonomy is a reasonable home.
- The title should be specific to this note's idea, not the file or heading.
- Tags should be lower-case, hyphenated, and chosen so two notes about the
  same topic will share at least two tags.
- The Action / Why / Purpose triple is the heart of the annotation. It is NOT
  a paraphrase. It turns the note's reasoning into something the user can
  actually do.
  - **Action:** a concrete, doable behaviour or rule.
  - **Why:** the causal logic that makes the action follow from the note.
  - **Purpose:** the deeper value the action ultimately serves.

Worked example (study this carefully — match this depth and shape):

Note text:
  "Sex should be something sacred, something not easily attained, to keep it
   special in a relationship. Perhaps instead of having sex whenever each of
   you want, you limit it to a time and even place (except when trying for a
   baby). This would help you look forward to the act, to know this was the
   only time you were able to caress the body of your partner — you would
   spend more time to make it last and both were satisfied."

Annotation:
  title:    "Make sex sacred by rationing it"
  category: "Original Thoughts"
  tags:     ["relationships", "intimacy", "self-discipline", "scarcity"]
  summary:  "Limiting sex to a chosen time and place preserves its specialness."
  action:   "Choose one day a week as the only time for sex with your partner; pick a private, deliberate setting."
  why:      "When something is always available it stops feeling novel; rationing creates anticipation, attention, and care during the act itself."
  purpose:  "To keep sex sacred and deeply enjoyable as the relationship matures."

Always respond by calling the `annotate_note` tool. Never reply in plain text.
"""


def system_blocks(taxonomy: list[str]) -> list[dict]:
    """System prompt structured for prompt caching.

    The static instructions and worked example go in the cached block; the
    short, changing taxonomy goes in a separate uncached block.
    """
    taxonomy_block = (
        "Running taxonomy (existing categories, in order of frequency):\n"
        + ("\n".join(f"- {c}" for c in taxonomy) if taxonomy else "- (empty)")
    )
    return [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": taxonomy_block,
        },
    ]
