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
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def summary_block(items: list[tuple[str, str]]) -> None:
    st.markdown('<div class="studio-summary">', unsafe_allow_html=True)
    for label, value in items:
        st.markdown(f"**{label}:** {value or '-'}")
    st.markdown("</div>", unsafe_allow_html=True)

