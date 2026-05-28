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
        .block-container,
        [data-testid="stMainBlockContainer"] {{
            max-width: none !important;
            padding-left: 6px !important;
            padding-right: 6px !important;
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
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 12px 14px;
            background: {STUDIO_COLORS["surface"]};
        }}
        .studio-summary-row {{
            display: grid;
            gap: 8px;
            grid-template-columns: minmax(72px, 0.65fr) 1fr;
        }}
        .studio-summary-row span {{
            color: {STUDIO_COLORS["muted"]};
            font-size: 0.82rem;
            font-weight: 500;
        }}
        .studio-summary-row strong {{
            color: {STUDIO_COLORS["text"]};
            font-size: 0.84rem;
            font-weight: 650;
            overflow-wrap: anywhere;
        }}
        .studio-create-step-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 4px 0 18px;
        }}
        .studio-step-pill {{
            align-items: center;
            background: {STUDIO_COLORS["surface"]};
            border: 1px solid {STUDIO_COLORS["border"]};
            border-radius: 999px;
            color: {STUDIO_COLORS["muted"]};
            display: inline-flex;
            font-size: 0.84rem;
            font-weight: 600;
            gap: 6px;
            padding: 6px 11px;
        }}
        .studio-step-pill strong {{
            color: {STUDIO_COLORS["primary"]};
        }}
        .studio-section-card-heading {{
            margin-bottom: 14px;
        }}
        .studio-section-card-heading h3 {{
            margin: 0 0 4px !important;
        }}
        .studio-section-card-description {{
            color: {STUDIO_COLORS["muted"]};
            margin: 0;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.studio-section-card-marker),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.studio-render-card-marker) {{
            background: {STUDIO_COLORS["surface"]};
            border-color: {STUDIO_COLORS["border"]};
            padding: 18px;
        }}
        [data-testid="stVerticalBlock"]:has(.studio-sticky-render-anchor) {{
            position: sticky;
            top: 22px;
        }}
        .studio-render-card-title {{
            margin: 0 0 10px;
        }}
        .studio-render-card-title h3 {{
            margin: 0 0 3px !important;
        }}
        .studio-render-card-title p,
        .studio-render-helper {{
            color: {STUDIO_COLORS["muted"]};
            margin: 0;
        }}
        .studio-video-preview-frame {{
            aspect-ratio: 9 / 16;
            align-items: center;
            background: linear-gradient(180deg, #111827 0%, #1f2937 58%, #374151 100%);
            border-radius: 14px;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            gap: 10px;
            justify-content: center;
            margin: 8px auto 12px;
            max-height: 360px;
            overflow: hidden;
            padding: 18px;
            text-align: center;
            width: min(100%, 210px);
        }}
        .studio-video-preview-frame span {{
            color: rgba(255, 255, 255, 0.72);
            font-size: 0.76rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .studio-video-preview-frame strong {{
            color: #ffffff;
            font-size: 1rem;
            line-height: 1.35;
        }}
        .studio-render-status {{
            background: {STUDIO_COLORS["surface_alt"]};
            border: 1px solid {STUDIO_COLORS["border"]};
            border-radius: 10px;
            padding: 12px;
        }}
        .studio-render-status strong {{
            display: block;
            margin-bottom: 4px;
        }}
        div[role="dialog"]:has(.studio-log-dialog-marker) {{
            width: min(92vw, 1120px);
        }}
        div[role="dialog"]:has(.studio-log-dialog-marker) pre {{
            max-height: 70vh;
            overflow: auto;
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
