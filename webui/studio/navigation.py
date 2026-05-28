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
        NavigationItem("create", "Create", "🎬"),
        NavigationItem("projects", "Projects", "🗂️"),
        NavigationItem("assets", "Assets", "🎞️"),
        NavigationItem("brand", "Brand", "🎨"),
        NavigationItem("settings", "Settings", "⚙️"),
    ]


def render_studio_app() -> None:
    from webui.studio.components import layout
    from webui.studio.pages import assets, brand, create, projects, settings

    layout.render_top_bar()

    pages = [
        st.Page(create.render_page, title="Create", icon="🎬", url_path="create"),
        st.Page(projects.render_page, title="Projects", icon="🗂️", url_path="projects"),
        st.Page(assets.render_page, title="Assets", icon="🎞️", url_path="assets"),
        st.Page(brand.render_page, title="Brand", icon="🎨", url_path="brand"),
        st.Page(settings.render_page, title="Settings", icon="⚙️", url_path="settings"),
    ]
    page = st.navigation(pages)
    page.run()
