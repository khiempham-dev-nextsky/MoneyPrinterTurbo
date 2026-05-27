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
        NavigationItem("create", "Create", "+"),
        NavigationItem("projects", "Projects", "P"),
        NavigationItem("assets", "Assets", "A"),
        NavigationItem("brand", "Brand", "B"),
        NavigationItem("settings", "Settings", "S"),
    ]


def _sidebar_width_css(collapsed: bool) -> None:
    width = 88 if collapsed else 232
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
        st.markdown(
            '<div class="studio-sidebar-wordmark">MPT</div>',
            unsafe_allow_html=True,
        )
        if not collapsed:
            st.markdown(
                '<div class="studio-sidebar-caption">MoneyPrinterTurbo Studio</div>',
                unsafe_allow_html=True,
            )

        toggle_label = "MENU" if collapsed else "MIN"
        if st.button(
            toggle_label,
            key="studio_sidebar_toggle",
            help="Toggle compact navigation",
            use_container_width=True,
        ):
            st.session_state["studio_sidebar_collapsed"] = not collapsed
            st.rerun()

        st.divider()

        for item in items:
            is_active = item.key == current_page
            button_label = item.icon if collapsed else f"{item.icon}  {item.label}"
            st.markdown('<div class="studio-nav-button">', unsafe_allow_html=True)
            if st.button(
                button_label,
                key=f"studio_nav_{item.key}",
                help=item.label,
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
        NavigationItem("create", "Create", "+", pages["create"]),
        NavigationItem("projects", "Projects", "P", pages["projects"]),
        NavigationItem("assets", "Assets", "A", pages["assets"]),
        NavigationItem("brand", "Brand", "B", pages["brand"]),
        NavigationItem("settings", "Settings", "S", pages["settings"]),
    ]
    if "studio_current_page" not in st.session_state:
        st.session_state["studio_current_page"] = "create"

    render_sidebar(items)
    layout.render_top_bar()

    current_page = st.session_state.get("studio_current_page", "create")
    renderer = pages.get(current_page, create.render_page)
    renderer()
