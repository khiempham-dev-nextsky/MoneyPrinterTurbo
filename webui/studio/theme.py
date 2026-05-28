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
            padding-left: 16px !important;
            padding-right: 16px !important;
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
        .studio-badge {{
            border-radius: 999px;
            display: inline-flex;
            font-size: 0.76rem;
            font-weight: 700;
            line-height: 1;
            padding: 5px 9px;
            white-space: nowrap;
        }}
        .studio-badge-source-tiktok {{
            background: #FCE7F3;
            color: #9D174D;
        }}
        .studio-badge-source-pexels {{
            background: #D1FAE5;
            color: #065F46;
        }}
        .studio-badge-source-pixabay {{
            background: #DBEAFE;
            color: #1D4ED8;
        }}
        .studio-badge-source-local,
        .studio-badge-source-unknown {{
            background: #F3F4F6;
            color: #374151;
        }}
        .studio-badge-status-done {{
            background: #D1FAE5;
            color: #047857;
        }}
        .studio-badge-status-rendering {{
            background: #EDE9FE;
            color: #6D28D9;
        }}
        .studio-badge-status-failed {{
            background: #FEE2E2;
            color: #B91C1C;
        }}
        .studio-badge-status-draft,
        .studio-badge-status-empty {{
            background: #F3F4F6;
            color: #4B5563;
        }}
        .studio-badge-progress {{
            background: #EFF6FF;
            color: #1D4ED8;
        }}
        .studio-task-card {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .studio-task-card-active .studio-task-title {{
            color: {STUDIO_COLORS["primary"]};
        }}
        .studio-task-title {{
            color: {STUDIO_COLORS["text"]};
            font-size: 0.98rem;
            font-weight: 750;
            line-height: 1.35;
        }}
        .studio-task-meta {{
            align-items: center;
            color: {STUDIO_COLORS["muted"]};
            display: flex;
            flex-wrap: wrap;
            font-size: 0.78rem;
            gap: 7px;
        }}
        .studio-project-detail-header {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 14px;
        }}
        .studio-project-detail-header h3 {{
            margin: 0 !important;
        }}
        .studio-project-meta-grid {{
            border: 1px solid {STUDIO_COLORS["border"]};
            border-radius: 8px;
            display: grid;
            gap: 0;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            margin-bottom: 16px;
            overflow: hidden;
        }}
        .studio-project-meta-grid div {{
            border-bottom: 1px solid {STUDIO_COLORS["border"]};
            min-width: 0;
            padding: 10px 12px;
        }}
        .studio-project-meta-grid div:nth-last-child(-n+2) {{
            border-bottom: none;
        }}
        .studio-project-meta-grid span {{
            color: {STUDIO_COLORS["muted"]};
            display: block;
            font-size: 0.76rem;
            margin-bottom: 4px;
        }}
        .studio-project-meta-grid strong {{
            color: {STUDIO_COLORS["text"]};
            display: block;
            font-size: 0.86rem;
            overflow-wrap: anywhere;
        }}
        .studio-project-preview-empty {{
            align-items: center;
            aspect-ratio: 9 / 16;
            background: {STUDIO_COLORS["surface_alt"]};
            border: 1px dashed {STUDIO_COLORS["border"]};
            border-radius: 12px;
            color: {STUDIO_COLORS["muted"]};
            display: flex;
            flex-direction: column;
            gap: 8px;
            justify-content: center;
            margin: 0 auto;
            max-height: 420px;
            padding: 18px;
            text-align: center;
            width: min(100%, 240px);
        }}
        .studio-project-preview-empty strong {{
            color: {STUDIO_COLORS["text"]};
        }}
        div[data-testid="stVerticalBlock"]:has(.studio-project-video-preview-marker) video {{
            max-height: 520px;
        }}
        div[role="dialog"]:has(.studio-project-log-dialog-marker) {{
            width: min(92vw, 1120px);
        }}
        div[role="dialog"]:has(.studio-project-log-dialog-marker) pre {{
            max-height: 70vh;
            overflow: auto;
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
