import streamlit as st

from app.config import config
from app.models import const
from webui.studio import bootstrap
from webui.studio import render_jobs
from webui.studio.components import (
    actions,
    audio_settings,
    layout,
    source_settings,
    status as render_status,
    subtitle_settings,
)
from webui.studio.i18n import tr
from webui.studio.state import build_video_params, load_create_state, save_create_state
from webui.studio.validators import validate_render_request


def _render_brief_and_script_section(state) -> None:
    st.subheader("Brief & Script")
    state.video_subject = st.text_input(
        tr("Video Subject"),
        value=state.video_subject,
        key="studio_video_subject",
    ).strip()

    video_languages = [(tr("Auto Detect"), "")]
    for code in bootstrap.support_locales:
        video_languages.append((code, code))
    current_language = state.video_language
    values = [value for _, value in video_languages]
    language_index = values.index(current_language) if current_language in values else 0
    selected_language = st.selectbox(
        tr("Script Language"),
        options=range(len(video_languages)),
        format_func=lambda x: video_languages[x][0],
        index=language_index,
    )
    state.video_language = video_languages[selected_language][1]
    st.caption("Start with a topic, then generate or refine the script and keywords.")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(tr("Generate Video Script and Keywords"), key="studio_generate_script"):
            actions.generate_script_and_terms(state)
    with col_b:
        if st.button(tr("Generate Video Keywords"), key="studio_generate_terms"):
            actions.generate_terms_only(state)

    state.video_script = st.text_area(
        tr("Video Script"),
        value=state.video_script,
        height=280,
        key="studio_video_script",
    )
    state.video_terms = st.text_area(
        tr("Video Keywords"),
        value=state.video_terms,
        key="studio_video_terms",
    )


def _render_source_section(state):
    st.subheader("Source & Materials")
    uploaded_files = source_settings.render_source_settings(state)
    with st.expander("Advanced source and video options", expanded=False):
        source_settings.render_source_advanced_settings(state)
    return uploaded_files


def _render_audio_section(state):
    st.subheader("Voice & Audio")
    audio_settings.render_audio_settings(state)
    uploaded_audio_file = None
    with st.expander("Audio, provider keys, and background music", expanded=False):
        uploaded_audio_file = audio_settings.render_audio_advanced_settings(state)
    return uploaded_audio_file


def _render_subtitle_section(state) -> None:
    st.subheader("Subtitles & Brand")
    subtitle_settings.render_subtitle_settings(state)
    with st.expander("Subtitle fine tuning", expanded=False):
        subtitle_settings.render_subtitle_advanced_settings(state)


def _render_active_render_status() -> None:
    snapshot = render_jobs.get_active_render_snapshot()
    render_status.render_active_render_panel(snapshot)


if hasattr(st, "fragment"):
    _render_active_render_status_fragment = st.fragment(run_every="2s")(
        _render_active_render_status
    )
else:
    _render_active_render_status_fragment = _render_active_render_status


def _render_render_rail(state, uploaded_files, uploaded_audio_file) -> None:
    st.subheader("Render & Monitor")
    params = build_video_params(state)
    issues = validate_render_request(params, dict(config.app))
    if issues:
        for issue in issues:
            st.warning(tr(issue.message))
    else:
        st.success("Ready to render")

    layout.summary_block(
        [
            ("Subject", state.video_subject),
            ("Source", state.video_source),
            ("Language", state.video_language or "auto"),
            ("Aspect", state.video_aspect),
            ("Voice", state.voice_name),
            ("Subtitle font", state.font_name),
            ("Video count", str(state.video_count)),
        ]
    )

    if st.button(
        tr("Generate Video"),
        type="primary",
        use_container_width=True,
        disabled=bool(issues),
    ):
        save_create_state(state)
        actions.render_video_generation(state, uploaded_files, uploaded_audio_file)

    st.divider()
    snapshot = render_jobs.get_active_render_snapshot()
    if (
        snapshot
        and snapshot.state == const.TASK_STATE_PROCESSING
        and st.session_state.get("studio_render_autorefresh", True)
    ):
        _render_active_render_status_fragment()
    else:
        _render_active_render_status()


def render_page() -> None:
    layout.page_header(
        "Create Video",
        "Create, tune, render, and monitor one video from a single page.",
    )
    state = load_create_state()

    main_col, render_col = st.columns([7, 3], gap="large")
    with main_col:
        with layout.section_card():
            _render_brief_and_script_section(state)
        with layout.section_card():
            uploaded_files = _render_source_section(state)
        with layout.section_card():
            uploaded_audio_file = _render_audio_section(state)
        with layout.section_card():
            _render_subtitle_section(state)

    with render_col:
        with layout.section_card():
            _render_render_rail(state, uploaded_files, uploaded_audio_file)

    save_create_state(state)
