from contextlib import contextmanager
from html import escape

import streamlit as st

from app.config import config
from webui.studio import i18n


def render_top_bar() -> None:
    title_col, language_col = st.columns([4, 1])
    with title_col:
        st.markdown(
            f"""
            <div class="studio-topbar">
              <div class="studio-title">
                <strong>MoneyPrinterTurbo Studio</strong>
                <span>Studio v{config.project_version} · Create · Render · Review</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with language_col:
        i18n.render_language_selector()


def page_header(title: str, description: str = "") -> None:
    st.markdown(
        f"""
        <div class="studio-page-header">
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def section_card():
    with st.container(border=True):
        yield


def truncate_middle(value: str, max_length: int = 80) -> str:
    text = str(value or "")
    if len(text) <= max_length:
        return text

    marker = "..."
    if max_length <= len(marker) + 8:
        return text[:max_length]

    budget = max_length - len(marker)
    last_segment = text.rsplit("/", 1)[-1]
    tail_length = min(len(last_segment), max(12, budget - 12))
    head_length = budget - tail_length
    if head_length < 8:
        head_length = max(8, budget // 2)
        tail_length = budget - head_length

    return f"{text[:head_length]}{marker}{text[-tail_length:]}"


def path_text(path: str, max_length: int = 88) -> None:
    st.markdown(
        f'<span class="studio-path" title="{escape(str(path or ""))}">'
        f"{escape(truncate_middle(str(path or ''), max_length=max_length))}"
        "</span>",
        unsafe_allow_html=True,
    )


def summary_block(items: list[tuple[str, str]]) -> None:
    rows = [
        (
            '<div class="studio-summary-row">'
            f'<span class="studio-summary-label">{escape(str(label))}</span>'
            f'<span class="studio-summary-value" title="{escape(str(value or "-"))}">'
            f"{escape(str(value or '-'))}</span>"
            "</div>"
        )
        for label, value in items
    ]
    st.markdown(
        f"""<div class="studio-summary">{''.join(rows)}</div>""",
        unsafe_allow_html=True,
    )
