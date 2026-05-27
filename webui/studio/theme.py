import streamlit as st


STUDIO_COLORS = {
    "primary": "#ffffff",
    "ink": "#ffffff",
    "body": "#cccccc",
    "body_strong": "#e6e6e6",
    "muted": "#999999",
    "muted_soft": "#666666",
    "hairline": "#262626",
    "hairline_strong": "#3a3a3a",
    "canvas": "#000000",
    "surface_soft": "#0d0d0d",
    "surface_card": "#141414",
    "surface_elevated": "#1f1f1f",
    "on_primary": "#000000",
    "on_dark": "#ffffff",
    "link": "#c3d9f3",
    "warning": "#d4a017",
    "success": "#5fa657",
    "danger": "#d06b6b",
}


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        /* DESIGN.md Bugatti-inspired studio tokens: black canvas, monochrome type, square surfaces. */
        :root {{
            --studio-canvas: {STUDIO_COLORS["canvas"]};
            --studio-surface-soft: {STUDIO_COLORS["surface_soft"]};
            --studio-surface-card: {STUDIO_COLORS["surface_card"]};
            --studio-surface-elevated: {STUDIO_COLORS["surface_elevated"]};
            --studio-hairline: {STUDIO_COLORS["hairline"]};
            --studio-hairline-strong: {STUDIO_COLORS["hairline_strong"]};
            --studio-ink: {STUDIO_COLORS["ink"]};
            --studio-body: {STUDIO_COLORS["body"]};
            --studio-muted: {STUDIO_COLORS["muted"]};
            --studio-link: {STUDIO_COLORS["link"]};
            --studio-space-xs: 8px;
            --studio-space-sm: 12px;
            --studio-space-md: 16px;
            --studio-space-lg: 24px;
            --studio-space-xl: 40px;
        }}

        .stApp, [data-testid="stAppViewContainer"] {{
            background: var(--studio-canvas);
            color: var(--studio-body);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stMainBlockContainer"] {{
            max-width: 1280px;
            padding: 32px 48px 64px;
        }}

        h1, h2, h3, .studio-wordmark, .studio-page-header h1 {{
            color: var(--studio-ink) !important;
            font-family: "Saira Condensed", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-weight: 400 !important;
            text-transform: uppercase;
        }}

        h1, .studio-page-header h1 {{
            padding-top: 0 !important;
            margin: 0 !important;
            font-size: 2rem !important;
            line-height: 1.15 !important;
            letter-spacing: 3px !important;
        }}

        h2 {{
            font-size: 1.4rem !important;
            letter-spacing: 2px !important;
        }}

        h3 {{
            font-size: 1rem !important;
            letter-spacing: 1.5px !important;
        }}

        p, label, span, .stMarkdown, .stCaption, [data-testid="stMarkdownContainer"] {{
            color: var(--studio-body);
            font-family: Cormorant Garamond, Garamond, "Times New Roman", serif;
            font-weight: 400;
        }}

        .stCaption, caption, small {{
            color: var(--studio-muted) !important;
        }}

        a {{
            color: var(--studio-link) !important;
        }}

        hr {{
            border-color: var(--studio-hairline) !important;
            margin: 40px 0 !important;
        }}

        .studio-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--studio-space-lg);
            min-height: 56px;
            padding: 0 0 var(--studio-space-lg) 0;
            border-bottom: 1px solid var(--studio-hairline);
            margin-bottom: var(--studio-space-xl);
        }}

        .studio-title {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .studio-title strong {{
            color: var(--studio-ink);
            font-family: "Saira Condensed", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size: 0.9rem;
            font-weight: 400;
            letter-spacing: 6px;
            line-height: 1;
            text-transform: uppercase;
        }}

        .studio-title span {{
            color: var(--studio-muted);
            font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
            font-size: 0.72rem;
            letter-spacing: 2px;
            line-height: 1.4;
            text-transform: uppercase;
        }}

        .studio-page-header {{
            margin: 0 0 var(--studio-space-xl) 0;
        }}

        .studio-page-header p {{
            color: var(--studio-muted);
            margin: 12px 0 0 0;
            max-width: 720px;
            font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
            font-size: 0.72rem;
            letter-spacing: 2px;
            line-height: 1.55;
            text-transform: uppercase;
        }}

        .studio-summary {{
            border: 1px solid var(--studio-hairline);
            border-radius: 0px;
            padding: var(--studio-space-lg);
            background: var(--studio-surface-card);
            display: grid;
            gap: 12px;
        }}

        .studio-summary-row {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: var(--studio-space-md);
            border-bottom: 1px solid var(--studio-hairline);
            padding-bottom: 10px;
        }}

        .studio-summary-row:last-child {{
            border-bottom: 0;
            padding-bottom: 0;
        }}

        .studio-summary-label {{
            color: var(--studio-muted);
            font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
            font-size: 0.68rem;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        .studio-summary-value {{
            color: var(--studio-ink);
            font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
            font-size: 0.74rem;
            letter-spacing: 1px;
            text-align: right;
        }}

        .studio-pill {{
            display: inline-flex;
            align-items: center;
            border: 1px solid var(--studio-hairline-strong);
            border-radius: 999px;
            padding: 4px 12px;
            font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
            font-size: 0.68rem;
            letter-spacing: 2px;
            color: var(--studio-muted);
            margin-right: 8px;
            text-transform: uppercase;
        }}

        .studio-section {{
            border-top: 1px solid var(--studio-hairline);
            padding-top: var(--studio-space-lg);
            margin-top: var(--studio-space-xl);
        }}

        .studio-sidebar-wordmark {{
            color: var(--studio-ink);
            font-family: "Saira Condensed", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size: 0.82rem;
            font-weight: 400;
            letter-spacing: 5px;
            line-height: 1.2;
            padding: 6px 0 24px;
            text-transform: uppercase;
        }}

        .studio-sidebar-caption {{
            color: var(--studio-muted);
            font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
            font-size: 0.64rem;
            letter-spacing: 2px;
            line-height: 1.5;
            margin: -14px 0 22px;
            text-transform: uppercase;
        }}

        .studio-nav-button {{
            margin-bottom: 8px;
        }}

        section[data-testid="stSidebar"] {{
            background: var(--studio-canvas);
            border-right: 1px solid var(--studio-hairline);
        }}

        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
            padding: 24px 16px;
        }}

        .stButton > button, .stDownloadButton > button, a[data-testid="stLinkButton"] {{
            min-height: 44px;
            border-radius: 999px !important;
            border: 1px solid var(--studio-hairline-strong) !important;
            background: transparent !important;
            color: var(--studio-ink) !important;
            font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace !important;
            font-size: 0.74rem !important;
            font-weight: 400 !important;
            letter-spacing: 2.5px !important;
            text-transform: uppercase !important;
            box-shadow: none !important;
        }}

        .stButton > button:hover, .stDownloadButton > button:hover, a[data-testid="stLinkButton"]:hover {{
            border-color: var(--studio-ink) !important;
            color: var(--studio-ink) !important;
        }}

        .stButton > button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {{
            border-color: var(--studio-ink) !important;
            background: transparent !important;
        }}

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] > div,
        div[data-testid="stNumberInput"] input {{
            min-height: 44px;
            border-radius: 0px !important;
            border: 0 !important;
            border-bottom: 1px solid var(--studio-hairline-strong) !important;
            background: transparent !important;
            color: var(--studio-ink) !important;
            box-shadow: none !important;
            font-family: Cormorant Garamond, Garamond, "Times New Roman", serif !important;
            font-size: 1rem !important;
        }}

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stNumberInput"] input:focus {{
            border-bottom-color: var(--studio-ink) !important;
        }}

        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"],
        div[data-testid="stFileUploader"],
        div[data-testid="stAlert"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 0px !important;
        }}

        div[data-testid="stExpander"] {{
            border-color: var(--studio-hairline) !important;
            background: var(--studio-surface-soft) !important;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid var(--studio-hairline);
        }}

        div[data-testid="stProgress"] > div > div {{
            background: var(--studio-ink) !important;
        }}

        code, pre {{
            border-radius: 0px !important;
            background: var(--studio-surface-soft) !important;
            color: var(--studio-body) !important;
        }}

        @media (max-width: 900px) {{
            [data-testid="stMainBlockContainer"] {{
                padding: 24px 18px 48px;
            }}
            .studio-topbar {{
                align-items: flex-start;
                flex-direction: column;
                gap: 16px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
