import os
import sys

import streamlit as st
from loguru import logger

from app.config import config
from app.utils import utils

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
font_dir = os.path.join(root_dir, "resource", "fonts")
song_dir = os.path.join(root_dir, "resource", "songs")
i18n_dir = os.path.join(root_dir, "webui", "i18n")
brand_presets_file = os.path.join(root_dir, "webui", ".streamlit", "brand_presets.json")
system_locale = utils.get_system_locale()

support_locales = [
    "zh-CN",
    "zh-HK",
    "zh-TW",
    "de-DE",
    "en-US",
    "fr-FR",
    "vi-VN",
    "th-TH",
    "tr-TR",
]

_stdout_sink_id = None
_log_initialized = False


def ensure_root_on_path() -> None:
    if root_dir not in sys.path:
        sys.path.append(root_dir)


def init_page_config() -> None:
    st.set_page_config(
        page_title="MoneyPrinterTurbo Studio",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Report a bug": "https://github.com/harry0703/MoneyPrinterTurbo/issues",
            "About": (
                "# MoneyPrinterTurbo Studio\n"
                "Create short videos from a topic, script, stock/local/TikTok materials, "
                "voiceover, music, and subtitles."
            ),
        },
    )


def init_log() -> None:
    global _log_initialized, _stdout_sink_id

    if _stdout_sink_id is not None:
        try:
            logger.remove(_stdout_sink_id)
        except ValueError:
            pass
    elif not _log_initialized:
        logger.remove()
    _log_initialized = True

    def format_record(record):
        file_path = record["file"].path
        relative_path = os.path.relpath(file_path, root_dir)
        record["file"].path = f"./{relative_path}"
        record["message"] = record["message"].replace(root_dir, ".")
        return (
            "<green>{time:%Y-%m-%d %H:%M:%S}</> | "
            + "<level>{level}</> | "
            + '"{file.path}:{line}":<blue> {function}</> '
            + "- <level>{message}</>\n"
        )

    _stdout_sink_id = logger.add(
        sys.stdout,
        level="DEBUG",
        format=format_record,
        colorize=True,
    )


def init_session_state() -> None:
    defaults = {
        "video_subject": "",
        "video_script": "",
        "video_terms": "",
        "ui_language": config.ui.get("language", system_locale),
        "local_video_materials": [],
        "studio_active_project": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def boot() -> None:
    ensure_root_on_path()
    init_page_config()
    init_log()
    init_session_state()
