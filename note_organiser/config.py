from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .annotators import ClaudeAnnotator, StubAnnotator
from .dedupers import FuzzyTitleDeduper
from .interfaces import Annotator
from .pipeline import Pipeline
from .renderers import KarpathyWikiRenderer
from .splitters import (
    BlankLineParagraphSplitter,
    ExtensionRoutedSplitter,
    MarkdownHeadingSplitter,
)
from .stores import JsonFileStore


@dataclass
class AppConfig:
    notes_dir: Path = Path("notes")
    wiki_dir: Path = Path("wiki")
    state_path: Path = Path("state/notes.json")
    annotator_kind: str = "claude"  # "claude" | "stub"
    model: str = "claude-sonnet-4-6"
    title_threshold: int = 85
    body_threshold: float = 0.4
    backlink_min_shared_tags: int = 2
    extra_splitters: list = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv(override=False)
        return cls(
            annotator_kind=os.environ.get("NOTE_ORGANISER_ANNOTATOR", "claude"),
            model=os.environ.get("NOTE_ORGANISER_MODEL", "claude-sonnet-4-6"),
        )


def _build_annotator(config: AppConfig) -> Annotator:
    if config.annotator_kind == "stub":
        return StubAnnotator()
    if config.annotator_kind == "claude":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Either export it, populate .env, "
                "or set NOTE_ORGANISER_ANNOTATOR=stub for an offline run."
            )
        return ClaudeAnnotator(model=config.model)
    raise ValueError(f"Unknown annotator_kind: {config.annotator_kind!r}")


def build_pipeline(config: AppConfig) -> Pipeline:
    splitter = ExtensionRoutedSplitter(
        [
            MarkdownHeadingSplitter(),
            BlankLineParagraphSplitter(),
            *config.extra_splitters,
        ]
    )
    annotator = _build_annotator(config)
    deduper = FuzzyTitleDeduper(
        title_threshold=config.title_threshold,
        body_threshold=config.body_threshold,
    )
    store = JsonFileStore(config.state_path)
    renderer = KarpathyWikiRenderer(
        backlink_min_shared_tags=config.backlink_min_shared_tags
    )
    return Pipeline(
        splitter=splitter,
        annotator=annotator,
        deduper=deduper,
        store=store,
        renderer=renderer,
        notes_dir=config.notes_dir,
        wiki_dir=config.wiki_dir,
    )
