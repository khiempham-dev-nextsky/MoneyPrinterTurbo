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
                <strong>MoneyPrinterTurbo Studio v{config.project_version}</strong>
                <span>Create, style, render, and review short videos from one workspace.</span>
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
          <h1>{escape(title)}</h1>
          <p>{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def section_card(title: str, description: str = ""):
    with st.container(border=True):
        description_html = (
            f'<p class="studio-section-card-description">{escape(description)}</p>'
            if description
            else ""
        )
        st.markdown(
            f"""
            <div class="studio-section-card-marker"></div>
            <div class="studio-section-card-heading">
              <h3>{escape(title)}</h3>
              {description_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        yield


@contextmanager
def advanced_accordion(label: str, expanded: bool = False):
    with st.expander(label, expanded=expanded):
        yield


def summary_block(items: list[tuple[str, str]]) -> None:
    rows = []
    for label, value in items:
        rows.append(
            f'<div class="studio-summary-row"><span>{escape(str(label))}</span>'
            f'<strong>{escape(str(value or "-"))}</strong></div>'
        )
    st.markdown(
        f'<div class="studio-summary">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )
