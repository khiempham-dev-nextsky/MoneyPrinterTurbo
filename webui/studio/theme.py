import streamlit as st


STUDIO_COLORS = {
    "page_bg": "#F7F8FA",
    "surface": "#FFFFFF",
    "surface_alt": "#F1F3F5",
    "border": "#D8DEE6",
    "text": "#111827",
    "muted": "#5B6472",
    "primary": "#2563EB",
    "success": "#0F766E",
    "warning": "#B45309",
    "danger": "#B91C1C",
    "accent": "#7C3AED",
}


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        h1, h2, h3 {{
            letter-spacing: 0;
        }}
        h1 {{
            padding-top: 0 !important;
            font-size: 1.85rem !important;
        }}
        h2 {{
            font-size: 1.35rem !important;
        }}
        h3 {{
            font-size: 1.05rem !important;
        }}
        .studio-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 10px 0 18px 0;
            border-bottom: 1px solid {STUDIO_COLORS["border"]};
            margin-bottom: 18px;
        }}
        .studio-title {{
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .studio-title strong {{
            color: {STUDIO_COLORS["text"]};
            font-size: 1.1rem;
        }}
        .studio-title span {{
            color: {STUDIO_COLORS["muted"]};
            font-size: 0.86rem;
        }}
        .studio-page-header {{
            margin: 0 0 14px 0;
        }}
        .studio-page-header p {{
            color: {STUDIO_COLORS["muted"]};
            margin-top: -6px;
        }}
        .studio-summary {{
            border: 1px solid {STUDIO_COLORS["border"]};
            border-radius: 8px;
            padding: 12px 14px;
            background: {STUDIO_COLORS["surface"]};
        }}
        .studio-pill {{
            display: inline-flex;
            align-items: center;
            border: 1px solid {STUDIO_COLORS["border"]};
            border-radius: 999px;
            padding: 2px 8px;
            font-size: 0.8rem;
            color: {STUDIO_COLORS["muted"]};
            margin-right: 6px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
