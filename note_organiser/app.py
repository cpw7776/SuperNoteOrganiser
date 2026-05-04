from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

from .config import AppConfig, build_pipeline


def cli_run() -> None:
    """Console entrypoint: `note-organiser` runs the same Streamlit app."""
    import streamlit.web.cli as stcli

    sys.argv = ["streamlit", "run", str(Path(__file__).resolve())]
    stcli.main()


def _run_pipeline(config: AppConfig) -> None:
    pipeline = build_pipeline(config)
    progress = st.progress(0.0, text="Starting…")
    log = st.empty()

    def cb(stage: str, i: int, total: int) -> None:
        ratio = i / max(total, 1)
        # spread the bar across stages: annotate 0-0.6, merge 0.6-0.9, render 0.9-1.0
        bands = {"annotate": (0.0, 0.6), "merge": (0.6, 0.9), "render": (0.9, 1.0)}
        lo, hi = bands.get(stage, (0.0, 1.0))
        progress.progress(lo + (hi - lo) * ratio, text=f"{stage} {i}/{total}")
        log.write(f"{stage}: {i}/{total}")

    result = pipeline.run(progress=cb)
    progress.progress(1.0, text="Done")
    st.success(
        f"Discovered {result.discovered} chunks · "
        f"new {result.new_chunks} · annotated {result.annotated} · "
        f"merged groups {result.merged_groups} · total notes {result.notes_total} · "
        f"skipped (already seen) {result.skipped_seen}"
    )
    if result.errors:
        with st.expander(f"{len(result.errors)} errors"):
            for err in result.errors:
                st.code(err)


def _render_wiki_browser(config: AppConfig) -> None:
    index = config.wiki_dir / "index.md"
    if not index.exists():
        st.info("No wiki yet. Click **Process new notes** in the sidebar.")
        return

    pages = sorted(p for p in config.wiki_dir.glob("*.md") if p.name != "index.md")
    page_names = ["index.md"] + [p.name for p in pages]
    choice = st.selectbox("Page", page_names, index=0)
    md = (config.wiki_dir / choice).read_text(encoding="utf-8")
    st.markdown(md)


def _render_inbox(config: AppConfig) -> None:
    pipeline = build_pipeline(config)
    chunks = pipeline.discover_chunks()
    seen_ids = {n.note_id for n in pipeline._store.all()}  # type: ignore[attr-defined]
    new = [c for c in chunks if c.note_id not in seen_ids]
    st.caption(f"{len(chunks)} discovered · {len(new)} unprocessed")
    for chunk in new:
        with st.container(border=True):
            st.write(
                f"**{chunk.heading or '(no heading)'}** · "
                f"`{chunk.source_path.name}`"
                + (f" · device={chunk.device}" if chunk.device else "")
            )
            st.write(chunk.text)


def _render_notes_table(config: AppConfig) -> None:
    pipeline = build_pipeline(config)
    notes = pipeline._store.all()  # type: ignore[attr-defined]
    if not notes:
        st.info("No notes yet.")
        return
    rows = [
        {
            "title": n.title,
            "category": n.category,
            "tags": ", ".join(n.tags),
            "summary": n.summary,
            "sources": ", ".join(n.sources),
        }
        for n in sorted(notes, key=lambda n: (n.category, n.title.lower()))
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    titles = [n.title for n in notes]
    pick = st.selectbox("Inspect a note", titles, index=0)
    note = next(n for n in notes if n.title == pick)
    with st.container(border=True):
        st.markdown(f"### {note.title}")
        st.markdown(f"_{note.summary}_")
        st.markdown(note.body)
        st.markdown(f"**Action:** {note.action.action}")
        st.markdown(f"**Why:** {note.action.why}")
        st.markdown(f"**Purpose:** {note.action.purpose}")
        if note.versions:
            with st.expander(f"{len(note.versions)} merged versions"):
                for i, v in enumerate(note.versions, 1):
                    st.markdown(f"**v{i}:** {v}")


def main() -> None:
    st.set_page_config(page_title="SuperNoteOrganiser", layout="wide")
    st.title("SuperNoteOrganiser")
    st.caption(
        "Drop notes into `notes/`, click **Process new notes**, and a "
        "Karpathy-style wiki appears in `wiki/` — every note carries an "
        "Action / Why / Purpose block."
    )

    if "config" not in st.session_state:
        st.session_state["config"] = AppConfig.from_env()
    config: AppConfig = st.session_state["config"]

    with st.sidebar:
        st.header("Pipeline")
        config.annotator_kind = st.selectbox(
            "Annotator",
            ["claude", "stub"],
            index=0 if config.annotator_kind == "claude" else 1,
            help="Use 'stub' to wire up the pipeline without an API key.",
        )
        config.model = st.text_input("Model", value=config.model)
        config.notes_dir = Path(st.text_input("Notes dir", value=str(config.notes_dir)))
        config.wiki_dir = Path(st.text_input("Wiki dir", value=str(config.wiki_dir)))
        run_clicked = st.button("Process new notes", type="primary")
        st.divider()
        if st.button("Reset processed-state", help="Forget every note. Files in notes/ are untouched."):
            from .stores import JsonFileStore
            JsonFileStore(config.state_path).reset()
            st.toast("State cleared.")

    if run_clicked:
        try:
            _run_pipeline(config)
        except Exception as exc:
            st.error(str(exc))

    tab_inbox, tab_wiki, tab_notes = st.tabs(["Inbox", "Wiki", "Notes"])
    with tab_inbox:
        _render_inbox(config)
    with tab_wiki:
        _render_wiki_browser(config)
    with tab_notes:
        _render_notes_table(config)


main()
