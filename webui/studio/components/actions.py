import os
import webbrowser
from uuid import UUID, uuid4

import streamlit as st
from loguru import logger

from app.config import config
from app.models.schema import MaterialInfo
from app.services import llm
from app.services import task as tm
from app.utils import utils
from webui.studio import bootstrap
from webui.studio.i18n import tr
from webui.studio.state import StudioCreateState, build_video_params, save_create_state
from webui.studio.validators import validate_render_request


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


def persist_uploaded_audio(task_id: str, uploaded_audio_file) -> str:
    task_dir = utils.task_dir(task_id)
    _, audio_ext = os.path.splitext(os.path.basename(uploaded_audio_file.name))
    audio_ext = audio_ext.lower() or ".mp3"
    custom_audio_path = os.path.join(task_dir, f"custom-audio{audio_ext}")
    with open(custom_audio_path, "wb") as file:
        file.write(uploaded_audio_file.getbuffer())
    return custom_audio_path


def persist_uploaded_materials(uploaded_files) -> list[dict]:
    local_videos_dir = utils.storage_dir("local_videos", create=True)
    persisted_materials = []
    for file in uploaded_files:
        file_path = os.path.join(local_videos_dir, f"{file.file_id}_{file.name}")
        with open(file_path, "wb") as output:
            output.write(file.getbuffer())
        material = MaterialInfo()
        material.provider = "local"
        material.url = file_path
        persisted_materials.append(
            {
                "provider": material.provider,
                "url": material.url,
                "duration": material.duration,
            }
        )
    return persisted_materials


def render_video_generation(
    state: StudioCreateState,
    uploaded_files,
    uploaded_audio_file,
) -> None:
    task_id = str(uuid4())

    if uploaded_files:
        state.local_video_materials = persist_uploaded_materials(uploaded_files)
        save_create_state(state)

    if uploaded_audio_file:
        state.custom_audio_file = persist_uploaded_audio(task_id, uploaded_audio_file)

    params = build_video_params(state)
    issues = validate_render_request(params, dict(config.app))
    if issues:
        for issue in issues:
            st.error(tr(issue.message))
        return

    config.save_config()
    log_records = []

    with st.status("Rendering video", expanded=True) as status:
        log_container = st.empty()

        def log_received(message):
            if config.ui.get("hide_log", False):
                return
            log_records.append(message)
            log_container.code("\n".join(log_records[-80:]))

        logger.add(log_received)
        st.write("Preparing task")
        logger.info(tr("Start Generating Video"))
        logger.info(utils.to_json(params))
        result = tm.start(task_id=task_id, params=params)

        if not result or "videos" not in result:
            status.update(label="Video generation failed", state="error", expanded=True)
            st.error(tr("Video Generation Failed"))
            return

        status.update(label="Video generation completed", state="complete", expanded=False)

    video_files = result.get("videos", [])
    st.success(tr("Video Generation Completed"))
    if video_files:
        cols = st.columns(min(len(video_files), 3))
        for index, url in enumerate(video_files):
            cols[index % len(cols)].video(url)
            cols[index % len(cols)].code(url)
    open_task_folder(task_id)

