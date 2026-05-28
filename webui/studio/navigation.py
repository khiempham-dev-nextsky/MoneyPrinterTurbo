from dataclasses import dataclass
from typing import Callable

import streamlit as st


@dataclass(frozen=True)
class NavigationItem:
    key: str
    label: str
    icon: str
    renderer: Callable[[], None] | None = None


def get_navigation_items() -> list[NavigationItem]:
    return [
        NavigationItem("create", "Create", ":material/add_circle:"),
        NavigationItem("projects", "Projects", ":material/folder_open:"),
        NavigationItem("assets", "Assets", ":material/perm_media:"),
        NavigationItem("brand", "Brand", ":material/format_paint:"),
        NavigationItem("settings", "Settings", ":material/tune:"),
    ]


def _sidebar_width_css(collapsed: bool) -> None:
    width = 72 if collapsed else 232
    compact_sidebar_css = ""
    if collapsed:
        compact_sidebar_css = """
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding: 24px 10px !important;
        }
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            align-items: center !important;
            flex: 0 0 52px !important;
            margin-left: -42px !important;
            max-width: 52px !important;
            min-width: 52px !important;
            width: 52px !important;
        }
        section[data-testid="stSidebar"] [data-testid="stButton"],
        section[data-testid="stSidebar"] button {
            max-width: 44px !important;
            min-width: 44px !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            width: 44px !important;
        }
        """
    st.markdown(
        f"""
        <style>
        section[data-testid="stSidebar"] {{
            min-width: {width}px !important;
            max-width: {width}px !important;
            width: {width}px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
            overflow-x: hidden;
        }}
        {compact_sidebar_css}
        @media (max-width: 700px) {{
            section[data-testid="stSidebar"] {{
                min-width: 72px !important;
                max-width: 72px !important;
                width: 72px !important;
            }}
            section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
                padding: 20px 10px !important;
            }}
            section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
                align-items: center !important;
                flex: 0 0 52px !important;
                margin-left: -42px !important;
                max-width: 52px !important;
                min-width: 52px !important;
                width: 52px !important;
            }}
            section[data-testid="stSidebar"] .studio-sidebar-wordmark,
            section[data-testid="stSidebar"] .studio-sidebar-caption {{
                display: none !important;
            }}
            section[data-testid="stSidebar"] [data-testid="stButton"],
            section[data-testid="stSidebar"] button {{
                max-width: 44px !important;
                min-width: 44px !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
                width: 44px !important;
            }}
            section[data-testid="stSidebar"] button p {{
                display: none !important;
            }}
            [data-testid="stMainBlockContainer"] {{
                box-sizing: border-box !important;
                max-width: 100vw !important;
                padding-left: 88px !important;
                padding-right: 16px !important;
                width: 100vw !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _set_current_page(page_key: str) -> None:
    st.session_state["studio_current_page"] = page_key


def render_sidebar(items: list[NavigationItem]) -> None:
    collapsed = bool(st.session_state.get("studio_sidebar_collapsed", False))
    current_page = st.session_state.get("studio_current_page", "create")
    valid_keys = {item.key for item in items}
    if current_page not in valid_keys:
        current_page = "create"
        st.session_state["studio_current_page"] = current_page

    _sidebar_width_css(collapsed)

    with st.sidebar:
        wordmark = "M" if collapsed else "MPT"
        wordmark_class = (
            "studio-sidebar-wordmark studio-sidebar-wordmark-compact"
            if collapsed
            else "studio-sidebar-wordmark"
        )
        st.markdown(
            f'<div class="{wordmark_class}">{wordmark}</div>',
            unsafe_allow_html=True,
        )
        if not collapsed:
            st.markdown(
                '<div class="studio-sidebar-caption">MoneyPrinterTurbo Studio</div>',
                unsafe_allow_html=True,
            )

        toggle_label = "" if collapsed else "Hide"
        if st.button(
            toggle_label,
            key="studio_sidebar_toggle",
            help="Toggle compact navigation",
            icon=":material/menu:" if collapsed else ":material/left_panel_close:",
            use_container_width=True,
        ):
            st.session_state["studio_sidebar_collapsed"] = not collapsed
            st.rerun()

        st.divider()

        for item in items:
            is_active = item.key == current_page
            button_label = "" if collapsed else item.label
            st.markdown('<div class="studio-nav-button">', unsafe_allow_html=True)
            if st.button(
                button_label,
                key=f"studio_nav_{item.key}",
                help=item.label,
                icon=item.icon,
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                _set_current_page(item.key)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def render_studio_app() -> None:
    from webui.studio.components import layout
    from webui.studio.pages import assets, brand, create, projects, settings

    pages = {
        "create": create.render_page,
        "projects": projects.render_page,
        "assets": assets.render_page,
        "brand": brand.render_page,
        "settings": settings.render_page,
    }
    items = [
        NavigationItem("create", "Create", ":material/add_circle:", pages["create"]),
        NavigationItem("projects", "Projects", ":material/folder_open:", pages["projects"]),
        NavigationItem("assets", "Assets", ":material/perm_media:", pages["assets"]),
        NavigationItem("brand", "Brand", ":material/format_paint:", pages["brand"]),
        NavigationItem("settings", "Settings", ":material/tune:", pages["settings"]),
    ]
    if "studio_current_page" not in st.session_state:
        st.session_state["studio_current_page"] = "create"

    render_sidebar(items)
    layout.render_top_bar()

    current_page = st.session_state.get("studio_current_page", "create")
    renderer = pages.get(current_page, create.render_page)
    renderer()
