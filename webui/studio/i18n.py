import streamlit as st

from app.config import config
from app.utils import utils
from webui.studio import bootstrap


def load_locales() -> dict:
    return utils.load_locales(bootstrap.i18n_dir)


def tr(key: str) -> str:
    locales = load_locales()
    loc = locales.get(st.session_state.get("ui_language", ""), {})
    return loc.get("Translation", {}).get(key, key)


def render_language_selector() -> None:
    locales = load_locales()
    display_languages = []
    selected_index = 0
    current_language = st.session_state.get("ui_language", config.ui.get("language", ""))

    for index, code in enumerate(locales.keys()):
        display_languages.append(f"{code} - {locales[code].get('Language')}")
        if code == current_language:
            selected_index = index

    selected_language = st.selectbox(
        "Language / 语言",
        options=display_languages,
        index=selected_index,
        key="studio_language_selector",
        label_visibility="collapsed",
    )
    if selected_language:
        code = selected_language.split(" - ")[0].strip()
        st.session_state["ui_language"] = code
        config.ui["language"] = code

