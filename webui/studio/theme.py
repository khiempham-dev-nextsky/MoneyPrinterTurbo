import streamlit as st


STUDIO_COLORS = {
    "primary": "#0066cc",
    "primary_focus": "#0071e3",
    "primary_on_dark": "#2997ff",
    "ink": "#1d1d1f",
    "body": "#1d1d1f",
    "body_strong": "#111111",
    "muted": "#6e6e73",
    "muted_soft": "#86868b",
    "divider_soft": "#f0f0f0",
    "hairline": "#e0e0e0",
    "hairline_strong": "#d2d2d7",
    "canvas": "#ffffff",
    "canvas_parchment": "#f5f5f7",
    "surface_soft": "#fafafc",
    "surface_card": "#ffffff",
    "surface_elevated": "#ffffff",
    "on_primary": "#ffffff",
    "link": "#0066cc",
    "warning": "#fff8e6",
    "warning_text": "#7a4b00",
    "success": "#ecfdf3",
    "success_text": "#027a48",
    "danger": "#fef3f2",
    "danger_text": "#b42318",
}


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        /* Apple-inspired operational studio tokens: light canvas, white cards, one blue action color. */
        :root {{
            --studio-primary: {STUDIO_COLORS["primary"]};
            --studio-primary-focus: {STUDIO_COLORS["primary_focus"]};
            --studio-primary-on-dark: {STUDIO_COLORS["primary_on_dark"]};
            --studio-canvas: {STUDIO_COLORS["canvas"]};
            --studio-app-canvas: {STUDIO_COLORS["canvas_parchment"]};
            --studio-surface-soft: {STUDIO_COLORS["surface_soft"]};
            --studio-surface-card: {STUDIO_COLORS["surface_card"]};
            --studio-surface-elevated: {STUDIO_COLORS["surface_elevated"]};
            --studio-divider-soft: {STUDIO_COLORS["divider_soft"]};
            --studio-hairline: {STUDIO_COLORS["hairline"]};
            --studio-hairline-strong: {STUDIO_COLORS["hairline_strong"]};
            --studio-ink: {STUDIO_COLORS["ink"]};
            --studio-body: {STUDIO_COLORS["body"]};
            --studio-muted: {STUDIO_COLORS["muted"]};
            --studio-muted-soft: {STUDIO_COLORS["muted_soft"]};
            --studio-link: {STUDIO_COLORS["link"]};
            --studio-on-primary: {STUDIO_COLORS["on_primary"]};
            --studio-warning: {STUDIO_COLORS["warning"]};
            --studio-warning-text: {STUDIO_COLORS["warning_text"]};
            --studio-success: {STUDIO_COLORS["success"]};
            --studio-success-text: {STUDIO_COLORS["success_text"]};
            --studio-danger: {STUDIO_COLORS["danger"]};
            --studio-danger-text: {STUDIO_COLORS["danger_text"]};
            --studio-radius-sm: 8px;
            --studio-radius-md: 11px;
            --studio-radius-lg: 18px;
            --studio-space-xs: 8px;
            --studio-space-sm: 12px;
            --studio-space-md: 16px;
            --studio-space-lg: 24px;
            --studio-space-xl: 32px;
            --studio-font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif;
            --studio-font-mono: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            background: var(--studio-app-canvas) !important;
            color: var(--studio-body);
            font-family: var(--studio-font-ui);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stMainBlockContainer"] {{
            max-width: 1280px;
            padding: 32px 40px 64px;
        }}

        h1, h2, h3, .studio-page-header h1 {{
            color: var(--studio-ink) !important;
            font-family: var(--studio-font-ui);
            letter-spacing: 0 !important;
        }}

        h1, .studio-page-header h1 {{
            padding-top: 0 !important;
            margin: 0 !important;
            font-size: 2.125rem !important;
            font-weight: 600 !important;
            line-height: 1.12 !important;
        }}

        h2 {{
            font-size: 1.35rem !important;
            font-weight: 600 !important;
            line-height: 1.22 !important;
        }}

        h3 {{
            font-size: 1rem !important;
            font-weight: 600 !important;
            line-height: 1.3 !important;
        }}

        p, label, span, .stMarkdown, .stCaption, [data-testid="stMarkdownContainer"] {{
            color: var(--studio-body);
            font-family: var(--studio-font-ui);
            letter-spacing: 0;
        }}

        div[data-testid="stMarkdownContainer"] p,
        [data-testid="stWidgetLabel"] p {{
            line-height: 1.45;
            letter-spacing: 0;
        }}

        [data-testid="stWidgetLabel"] .colored-text,
        [data-testid="stWidgetLabel"] [style*="color"],
        [data-testid="stWidgetLabel"] strong {{
            color: var(--studio-body) !important;
        }}

        .stCaption, caption, small {{
            color: var(--studio-muted) !important;
        }}

        a {{
            color: var(--studio-link) !important;
        }}

        hr {{
            border-color: var(--studio-divider-soft) !important;
            margin: 28px 0 !important;
        }}

        .studio-topbar {{
            align-items: center;
            border-bottom: 1px solid var(--studio-hairline);
            display: flex;
            gap: var(--studio-space-lg);
            justify-content: space-between;
            min-height: 52px;
            padding: 0 0 var(--studio-space-lg) 0;
            margin-bottom: var(--studio-space-xl);
        }}

        .studio-title {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .studio-title strong,
        .studio-sidebar-wordmark {{
            color: var(--studio-ink);
            font-family: var(--studio-font-ui);
            font-weight: 600;
            letter-spacing: 0;
            line-height: 1.1;
        }}

        .studio-title strong {{
            font-size: 0.96rem;
        }}

        .studio-title span,
        .studio-sidebar-caption {{
            color: var(--studio-muted);
            font-family: var(--studio-font-ui);
            font-size: 0.78rem;
            letter-spacing: 0;
            line-height: 1.35;
        }}

        .studio-page-header {{
            margin: 0 0 var(--studio-space-xl) 0;
        }}

        .studio-page-header p {{
            color: var(--studio-muted);
            margin: 10px 0 0 0;
            max-width: 760px;
            font-size: 1rem;
            line-height: 1.5;
        }}

        .studio-summary,
        .studio-section-shell {{
            background: var(--studio-surface-card);
            border: 1px solid var(--studio-hairline);
            border-radius: var(--studio-radius-lg);
        }}

        .studio-summary {{
            display: grid;
            gap: 0;
            padding: var(--studio-space-lg);
        }}

        .studio-summary-row {{
            align-items: baseline;
            border-bottom: 1px solid var(--studio-divider-soft);
            display: grid;
            gap: var(--studio-space-md);
            grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
            min-width: 0;
            padding: 10px 0;
        }}

        .studio-summary-row:first-child {{
            padding-top: 0;
        }}

        .studio-summary-row:last-child {{
            border-bottom: 0;
            padding-bottom: 0;
        }}

        .studio-summary-label {{
            color: var(--studio-muted);
            font-family: var(--studio-font-ui);
            font-size: 0.76rem;
            font-weight: 600;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            text-transform: uppercase;
            white-space: nowrap;
        }}

        .studio-summary-value {{
            color: var(--studio-ink);
            font-family: var(--studio-font-ui);
            font-size: 0.86rem;
            font-weight: 500;
            min-width: 0;
            overflow: hidden;
            text-align: right;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .studio-path {{
            color: var(--studio-muted);
            display: inline-block;
            font-family: var(--studio-font-mono);
            font-size: 0.78rem;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            vertical-align: bottom;
            white-space: nowrap;
        }}

        .studio-pill {{
            align-items: center;
            background: var(--studio-surface-soft);
            border: 1px solid var(--studio-hairline);
            border-radius: 999px;
            color: var(--studio-muted);
            display: inline-flex;
            font-size: 0.78rem;
            margin-right: 8px;
            padding: 5px 12px;
        }}

        .studio-section {{
            border-top: 1px solid var(--studio-divider-soft);
            margin-top: var(--studio-space-xl);
            padding-top: var(--studio-space-lg);
        }}

        .studio-sidebar-wordmark {{
            font-size: 1rem;
            padding: 4px 0 18px;
        }}

        .studio-sidebar-wordmark-compact {{
            text-align: center;
        }}

        .studio-sidebar-caption {{
            margin: -10px 0 18px;
        }}

        .studio-nav-button {{
            margin-bottom: 8px;
        }}

        section[data-testid="stSidebar"] {{
            background: var(--studio-surface-card);
            border-right: 1px solid var(--studio-hairline);
        }}

        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
            padding: 24px 16px;
        }}

        button[data-testid="stBaseButton-secondary"],
        button[data-testid="stBaseButton-primary"],
        button[data-testid="stBaseButton-tertiary"],
        .stDownloadButton button,
        a[data-testid="stLinkButton"] {{
            min-height: 44px;
            border-radius: 999px !important;
            border: 1px solid var(--studio-hairline-strong) !important;
            background: var(--studio-surface-card) !important;
            color: var(--studio-primary) !important;
            font-family: var(--studio-font-ui) !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            letter-spacing: 0 !important;
            box-shadow: none !important;
        }}

        button[data-testid="stBaseButton-secondary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover,
        button[data-testid="stBaseButton-tertiary"]:hover,
        .stDownloadButton button:hover,
        a[data-testid="stLinkButton"]:hover {{
            border-color: var(--studio-primary) !important;
            color: var(--studio-primary) !important;
        }}

        button[kind="primary"],
        button[data-testid="stBaseButton-primary"] {{
            border-color: var(--studio-primary) !important;
            background: var(--studio-primary) !important;
            color: var(--studio-on-primary) !important;
        }}

        button[kind="primary"] [data-testid="stMarkdownContainer"],
        button[kind="primary"] [data-testid="stMarkdownContainer"] *,
        button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"],
        button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] * {{
            color: var(--studio-on-primary) !important;
        }}

        section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {{
            background: rgba(0, 102, 204, 0.1) !important;
            border-color: rgba(0, 102, 204, 0.22) !important;
            color: var(--studio-primary) !important;
        }}

        section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"],
        section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] * {{
            color: var(--studio-primary) !important;
        }}

        button[data-testid="stBaseButton-segmented_control"],
        button[data-testid="stBaseButton-segmented_controlActive"] {{
            border-color: var(--studio-hairline-strong) !important;
            background: var(--studio-surface-card) !important;
            color: var(--studio-ink) !important;
            font-family: var(--studio-font-ui) !important;
            font-weight: 500 !important;
        }}

        button[data-testid="stBaseButton-segmented_controlActive"] {{
            border-color: rgba(0, 102, 204, 0.35) !important;
            background: rgba(0, 102, 204, 0.1) !important;
            color: var(--studio-primary) !important;
        }}

        button[data-testid="stBaseButton-segmented_controlActive"] *,
        button[data-testid="stBaseButton-segmented_control"]:hover *,
        button[data-testid="stBaseButton-segmented_controlActive"]:hover * {{
            color: var(--studio-primary) !important;
        }}

        button:disabled,
        button[disabled] {{
            opacity: 0.46 !important;
        }}

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] input,
        div[data-testid="stNumberInput"] input {{
            min-height: 44px;
            color: var(--studio-ink) !important;
            font-family: var(--studio-font-ui) !important;
            font-size: 0.95rem !important;
        }}

        div[data-baseweb="input"],
        div[data-baseweb="base-input"],
        div[data-baseweb="textarea"],
        div[data-baseweb="select"] > div {{
            border: 1px solid var(--studio-hairline-strong) !important;
            border-radius: var(--studio-radius-md) !important;
            background: var(--studio-surface-card) !important;
            color: var(--studio-ink) !important;
            box-shadow: none !important;
        }}

        div[data-baseweb="select"] *,
        div[data-baseweb="select"] span {{
            color: var(--studio-ink) !important;
            font-family: var(--studio-font-ui) !important;
        }}

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stNumberInput"] input:focus {{
            border-color: var(--studio-primary-focus) !important;
        }}

        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"],
        div[data-testid="stFileUploader"],
        div[data-testid="stAlert"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: var(--studio-radius-lg) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stExpander"] {{
            border-color: var(--studio-hairline) !important;
            background: var(--studio-surface-card) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 18px !important;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid var(--studio-hairline);
            overflow: hidden;
        }}

        div[data-testid="stProgress"] > div > div {{
            background: var(--studio-primary) !important;
        }}

        div[data-testid="stSlider"] div[role="slider"] {{
            background: var(--studio-primary) !important;
        }}

        div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] {{
            color: var(--studio-primary) !important;
        }}

        div[data-testid="stAlert"] {{
            border: 1px solid var(--studio-hairline) !important;
        }}

        code, pre {{
            border-radius: var(--studio-radius-sm) !important;
            background: var(--studio-surface-soft) !important;
            color: var(--studio-body) !important;
        }}

        div[data-testid="stVideo"] {{
            max-width: 720px;
        }}

        div[data-testid="stVideo"] video {{
            border-radius: var(--studio-radius-md);
            max-height: 420px;
            object-fit: contain;
        }}

        .studio-subtitle-preview {{
            align-items: center;
            background: linear-gradient(180deg, var(--studio-surface-card), var(--studio-surface-soft));
            border: 1px solid var(--studio-hairline);
            border-radius: var(--studio-radius-lg);
            display: flex;
            justify-content: center;
            min-height: 132px;
            padding: 22px;
            text-align: center;
        }}

        @media (max-width: 900px) {{
            [data-testid="stMainBlockContainer"] {{
                padding: 24px 20px 48px;
            }}
            .studio-topbar {{
                align-items: flex-start;
                flex-direction: column;
                gap: 14px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
