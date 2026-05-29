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
        NavigationItem("translate", "Translate", "🌐"),
        NavigationItem("projects", "Projects", "🗂️"),
        NavigationItem("assets", "Assets", "🎞️"),
        NavigationItem("brand", "Brand", "🎨"),
        NavigationItem("settings", "Settings", "⚙️"),
    ]


def render_studio_app() -> None:
    from webui.studio.components import layout
    from webui.studio.pages import assets, brand, create, projects, settings, translate

    layout.render_top_bar()

    pages = [
        st.Page(create.render_page, title="Create", url_path="create"),
        st.Page(translate.render_page, title="Translate", url_path="translate"),
        st.Page(projects.render_page, title="Projects", url_path="projects"),
        st.Page(assets.render_page, title="Assets", url_path="assets"),
        st.Page(brand.render_page, title="Brand", url_path="brand"),
        st.Page(settings.render_page, title="Settings", url_path="settings"),
    ]
    page = st.navigation(pages)
    page.run()
