import os
import webbrowser
from uuid import UUID

import streamlit as st
from loguru import logger

from app.services import llm
from webui.studio import bootstrap
from webui.studio.i18n import tr
from webui.studio.state import StudioCreateState, save_create_state


def open_task_folder(task_id: str) -> None:
    try:
        normalized_task_id = str(UUID(str(task_id)))
        tasks_root = os.path.abspath(os.path.join(bootstrap.root_dir, "storage", "tasks"))
        path = os.path.abspath(os.path.join(tasks_root, normalized_task_id))
        if not path.startswith(tasks_root + os.sep):
            logger.warning(f"invalid task folder path: {path}")
            return
        if os.path.isdir(path):
            webbrowser.open(f"file://{path}")
    except Exception as exc:
        logger.error(exc)


def generate_script_and_terms(state: StudioCreateState) -> None:
    with st.spinner(tr("Generating Video Script and Keywords")):
        script = llm.generate_script(
            video_subject=state.video_subject,
            language=state.video_language,
        )
        terms = llm.generate_terms(state.video_subject, script)
    if "Error: " in script:
        st.error(tr(script))
        return
    if "Error: " in terms:
        st.error(tr(terms))
        return
    state.video_script = script
    state.video_terms = ", ".join(terms)
    save_create_state(state)
    st.rerun()


def generate_terms_only(state: StudioCreateState) -> None:
    if not state.video_script:
        st.error(tr("Please Enter the Video Subject"))
        return
    with st.spinner(tr("Generating Video Keywords")):
        terms = llm.generate_terms(state.video_subject, state.video_script)
    if "Error: " in terms:
        st.error(tr(terms))
        return
    state.video_terms = ", ".join(terms)
    save_create_state(state)
    st.rerun()


def render_video_generation(
    state: StudioCreateState,
    uploaded_files,
    uploaded_audio_file,
) -> None:
    from webui.studio import render_jobs

    try:
        snapshot = render_jobs.start_render_job(state, uploaded_files, uploaded_audio_file)
    except ValueError as exc:
        st.error(str(exc))
        return
    st.success(f"Render task started: {snapshot.task_id}")
    st.rerun()
