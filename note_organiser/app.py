from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import streamlit as st

from note_organiser.config import AppConfig, build_pipeline


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


_WIKI_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+\.md)\)")
_NOTE_H2_RE = re.compile(
    r'<h2\s+id="([^"]+)"\s+class="note-card__title">([^<]+)</h2>'
)


def _render_wiki_browser(config: AppConfig) -> None:
    index = config.wiki_dir / "index.md"
    if not index.exists():
        st.info("No wiki yet. Click **Process new notes** in the sidebar.")
        return

    pages = sorted(p for p in config.wiki_dir.glob("*.md") if p.name != "index.md")
    page_names = ["index.md"] + [p.name for p in pages]

    query_page = st.query_params.get("page")
    if query_page in page_names:
        st.session_state["wiki_page_select"] = query_page
    elif "wiki_page_select" not in st.session_state:
        st.session_state["wiki_page_select"] = "index.md"

    def _on_select() -> None:
        st.query_params["page"] = st.session_state["wiki_page_select"]
        st.query_params["tab"] = "Wiki"

    choice = st.selectbox(
        "Page", page_names, key="wiki_page_select", on_change=_on_select
    )
    md = (config.wiki_dir / choice).read_text(encoding="utf-8")
    md_clickable = _WIKI_LINK_RE.sub(
        lambda m: f'<a href="?page={m.group(2)}&tab=Wiki" target="_self">{m.group(1)}</a>',
        md,
    )

    note_headings = [
        (slug, html.unescape(title)) for slug, title in _NOTE_H2_RE.findall(md)
    ]

    if len(note_headings) >= 2:
        col_toc, col_body = st.columns([1, 4], gap="medium")
        with col_toc:
            toc_html = ['<div class="wiki-toc">',
                        '<div class="wiki-toc__label">On this page</div>']
            for slug, title in note_headings:
                toc_html.append(
                    f'<a class="wiki-toc__item" href="#{slug}">{html.escape(title)}</a>'
                )
            toc_html.append("</div>")
            st.markdown("\n".join(toc_html), unsafe_allow_html=True)
        with col_body:
            st.markdown(md_clickable, unsafe_allow_html=True)
    else:
        st.markdown(md_clickable, unsafe_allow_html=True)


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

    notes_sorted = sorted(notes, key=lambda n: (n.category, n.title.lower()))
    categories = sorted({n.category for n in notes_sorted})

    col_search, col_cat = st.columns([2, 1])
    with col_search:
        query = st.text_input(
            "Search",
            placeholder=f"Search {len(notes_sorted)} notes — title, summary, tag, or note text",
            key="notes_search",
            label_visibility="collapsed",
        )
    with col_cat:
        cat_filter = st.selectbox(
            "Category",
            ["All categories"] + categories,
            key="notes_category",
            label_visibility="collapsed",
        )

    q = (query or "").strip().lower()
    def _match(n) -> bool:
        if cat_filter != "All categories" and n.category != cat_filter:
            return False
        if not q:
            return True
        haystack = " ".join(
            [n.title, n.summary, n.body, " ".join(n.tags), n.category]
        ).lower()
        return q in haystack

    filtered = [n for n in notes_sorted if _match(n)]
    st.caption(f"{len(filtered)} of {len(notes_sorted)} match · click a row to inspect")

    if not filtered:
        st.info("No matches. Clear the search or pick a different category.")
        return

    rows = [
        {
            "title": n.title,
            "category": n.category,
            "tags": ", ".join(n.tags),
            "summary": n.summary,
            "sources": ", ".join(n.sources),
        }
        for n in filtered
    ]
    event = st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
        height=420,
        on_select="rerun",
        selection_mode="single-row",
        key="notes_table",
    )

    selected_rows = (
        event.selection.rows
        if event is not None and getattr(event, "selection", None)
        else []
    )
    selected_idx = selected_rows[0] if selected_rows else 0
    note = filtered[selected_idx]
    with st.container(border=True):
        st.markdown(f"### {html.escape(note.title)}")
        if note.summary:
            st.markdown(f"_{html.escape(note.summary)}_")

        body_html = "<br>".join(
            html.escape(line) for line in note.body.strip().splitlines() or [""]
        )
        sections = [
            _section_html("orig", "Original note", body_html),
            _section_html("act", "Action", html.escape(note.action.action)),
            _section_html("why", "Why", html.escape(note.action.why)),
            _section_html("pur", "Purpose", html.escape(note.action.purpose)),
        ]

        meta_bits = []
        if note.tags:
            tags_html = " ".join(
                f'<span class="nb-tag">#{html.escape(t)}</span>' for t in note.tags
            )
            meta_bits.append(
                f'<span class="nb-meta-bit"><span class="nb-meta-key">Tags</span> {tags_html}</span>'
            )
        if note.sources:
            srcs = ", ".join(
                f'<span class="nb-source">{html.escape(s)}</span>'
                for s in sorted(set(note.sources))
            )
            meta_bits.append(
                f'<span class="nb-meta-bit"><span class="nb-meta-key">Source</span> {srcs}</span>'
            )
        if note.devices:
            devs = ", ".join(
                f'<span class="nb-device">{html.escape(d)}</span>'
                for d in sorted(set(note.devices))
            )
            meta_bits.append(
                f'<span class="nb-meta-bit"><span class="nb-meta-key">Device</span> {devs}</span>'
            )
        if meta_bits:
            sections.append(f'<div class="nb-meta">{"".join(meta_bits)}</div>')

        st.markdown("\n".join(sections), unsafe_allow_html=True)

        if note.versions:
            with st.expander(f"{len(note.versions)} merged versions"):
                for i, v in enumerate(note.versions, 1):
                    st.markdown(f"**v{i}:** {v}")


_NOTE_BLOCK_CSS = """
<style>
.nb {
  margin: 0.55rem 0 0.7rem 0;
  padding: 0.55rem 0.85rem;
  border-left: 3px solid #6b7280;
  border-radius: 0 4px 4px 0;
  background: rgba(255,255,255,0.02);
}
.nb-l {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.55;
  margin-bottom: 0.25rem;
}
.nb-b { margin: 0; line-height: 1.5; }
.nb-orig { border-color: #9ca3af; }
.nb-orig .nb-b { font-style: italic; opacity: 0.92; }
.nb-act  { border-color: #34d399; }
.nb-why  { border-color: #60a5fa; }
.nb-pur  { border-color: #fbbf24; }
.nb-ver  { border-color: #a78bfa; }
.nb-meta {
  margin-top: 0.6rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255,255,255,0.07);
  font-size: 0.82rem;
  opacity: 0.78;
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem 1.2rem;
}
.nb-meta-bit { display: inline-flex; gap: 0.35rem; align-items: baseline; flex-wrap: wrap; }
.nb-meta-key {
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.55;
}
.nb-tag {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.78rem;
  padding: 0.05rem 0.4rem;
  border-radius: 4px;
  background: rgba(96,165,250,0.12);
  color: #93c5fd;
}
.nb-source {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: #fbbf24;
}
.nb-device {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: #34d399;
}
.note-card {
  margin: 1.4rem 0;
  padding: 1rem 1.25rem 0.6rem 1.25rem;
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.18);
}
.note-card__title {
  margin: 0 0 0.4rem 0 !important;
  padding: 0 !important;
  border-bottom: none !important;
  font-size: 1.4rem !important;
  scroll-margin-top: 1rem;
}
.note-card__summary {
  margin: 0 0 0.55rem 0;
  opacity: 0.85;
  font-size: 0.95rem;
}
.note-card .nb { background: rgba(255,255,255,0.015); }
.wiki-toc {
  position: sticky;
  top: 1rem;
  padding: 0.6rem 0.8rem;
  border-left: 2px solid rgba(255,255,255,0.08);
}
.wiki-toc__label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.55;
  margin-bottom: 0.55rem;
}
.wiki-toc__item {
  display: block;
  padding: 0.25rem 0;
  font-size: 0.92rem;
  text-decoration: none !important;
  opacity: 0.85;
  border-bottom: 1px dashed rgba(255,255,255,0.05);
}
.wiki-toc__item:hover { opacity: 1; }
.wiki-toc__item:last-child { border-bottom: none; }
</style>
"""


def _section_html(kind: str, label: str, body_html: str) -> str:
    return (
        f'<div class="nb nb-{kind}">'
        f'<div class="nb-l">{label}</div>'
        f'<div class="nb-b">{body_html}</div>'
        f'</div>'
    )


def main() -> None:
    st.set_page_config(page_title="SuperNoteOrganiser", layout="wide")
    st.markdown(_NOTE_BLOCK_CSS, unsafe_allow_html=True)
    st.title("SuperNoteOrganiser")
    st.caption(
        "Drop notes into `notes/`, click **Process new notes**, and a "
        "Karpathy-style wiki appears in `wiki/` — every note carries an "
        "Action / Why / Purpose block."
    )

    if "config" not in st.session_state:
        st.session_state["config"] = AppConfig.from_env()
    config: AppConfig = st.session_state["config"]

    # Sidebar settings persist via URL query params: survives browser refresh,
    # streamlit hot-reload on save, and full server restart (URL stays in
    # browser history). On first render, seed widget state from query params
    # if present, otherwise from env-loaded AppConfig.
    annotator_options = ["claude", "venice", "stub"]
    qp = st.query_params

    if "annotator_kind_widget" not in st.session_state:
        qp_annotator = qp.get("annotator")
        st.session_state["annotator_kind_widget"] = (
            qp_annotator if qp_annotator in annotator_options else config.annotator_kind
        )
    if "model_widget" not in st.session_state:
        st.session_state["model_widget"] = qp.get("model") or config.model
    if "notes_dir_widget" not in st.session_state:
        st.session_state["notes_dir_widget"] = qp.get("notes_dir") or str(config.notes_dir)
    if "wiki_dir_widget" not in st.session_state:
        st.session_state["wiki_dir_widget"] = qp.get("wiki_dir") or str(config.wiki_dir)

    def _persist(key: str, qp_name: str) -> None:
        st.query_params[qp_name] = st.session_state[key]

    with st.sidebar:
        st.header("Pipeline")
        config.annotator_kind = st.selectbox(
            "Annotator",
            annotator_options,
            key="annotator_kind_widget",
            on_change=lambda: _persist("annotator_kind_widget", "annotator"),
            help=(
                "claude → Anthropic API (ANTHROPIC_API_KEY). "
                "venice → Venice AI (VENICE_API_KEY, OpenAI-compatible). "
                "stub → offline, no key needed."
            ),
        )
        model_help = (
            "claude: e.g. 'claude-sonnet-4-6'. venice: e.g. 'llama-3.3-70b'. "
            "stub: ignored."
        )
        config.model = st.text_input(
            "Model",
            key="model_widget",
            on_change=lambda: _persist("model_widget", "model"),
            help=model_help,
        )
        config.notes_dir = Path(
            st.text_input(
                "Notes dir",
                key="notes_dir_widget",
                on_change=lambda: _persist("notes_dir_widget", "notes_dir"),
            )
        )
        config.wiki_dir = Path(
            st.text_input(
                "Wiki dir",
                key="wiki_dir_widget",
                on_change=lambda: _persist("wiki_dir_widget", "wiki_dir"),
            )
        )
        run_clicked = st.button("Process new notes", type="primary")
        if st.button(
            "Re-render wiki",
            help=(
                "Rewrite wiki/ from the existing store without re-annotating. "
                "Use after changing the renderer's output format."
            ),
        ):
            from note_organiser.renderers import KarpathyWikiRenderer
            from note_organiser.stores import JsonFileStore
            store = JsonFileStore(config.state_path)
            renderer = KarpathyWikiRenderer(
                backlink_min_shared_tags=config.backlink_min_shared_tags
            )
            renderer.render(store.all(), config.wiki_dir)
            st.toast(f"Re-rendered {len(store.all())} notes.")
        st.divider()
        if st.button("Reset processed-state", help="Forget every note. Files in notes/ are untouched."):
            from note_organiser.stores import JsonFileStore
            JsonFileStore(config.state_path).reset()
            st.toast("State cleared.")

    if run_clicked:
        try:
            _run_pipeline(config)
        except Exception as exc:
            st.error(str(exc))

    tab_options = ["Inbox", "Wiki", "Notes"]
    query_tab = st.query_params.get("tab")
    if query_tab in tab_options:
        st.session_state["active_tab"] = query_tab
    elif "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "Inbox"

    def _on_tab_change() -> None:
        st.query_params["tab"] = st.session_state["active_tab"]

    active = st.radio(
        "View",
        tab_options,
        key="active_tab",
        horizontal=True,
        label_visibility="collapsed",
        on_change=_on_tab_change,
    )
    if active == "Inbox":
        _render_inbox(config)
    elif active == "Wiki":
        _render_wiki_browser(config)
    else:
        _render_notes_table(config)


main()
