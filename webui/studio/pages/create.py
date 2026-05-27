import streamlit as st

from app.config import config
from webui.studio import bootstrap
from webui.studio.components import actions, audio_settings, layout, source_settings, subtitle_settings
from webui.studio.i18n import tr
from webui.studio.state import build_video_params, load_create_state, save_create_state
from webui.studio.validators import validate_render_request


def _render_brief_step(state) -> None:
    st.subheader("Brief")
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
    st.caption("Start with a topic. The next step can generate or refine the script.")


def _render_script_step(state) -> None:
    st.subheader("Script & Keywords")
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


def _render_review(state) -> None:
    st.subheader("Review & Render")
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


def render_page() -> None:
    layout.page_header(
        "Create Video",
        "Build a short video through a guided studio workflow.",
    )
    state = load_create_state()

    uploaded_files = []
    uploaded_audio_file = None
    tabs = st.tabs(
        [
            "1. Brief",
            "2. Script & Keywords",
            "3. Source & Materials",
            "4. Voice & Audio",
            "5. Subtitles & Brand",
            "6. Review & Render",
        ]
    )

    with tabs[0]:
        _render_brief_step(state)
    with tabs[1]:
        _render_script_step(state)
    with tabs[2]:
        st.subheader("Source & Materials")
        uploaded_files = source_settings.render_source_settings(state)
        with st.expander("Advanced video options", expanded=False):
            source_settings.render_video_options(state)
    with tabs[3]:
        st.subheader("Voice & Audio")
        uploaded_audio_file = audio_settings.render_audio_settings(state)
    with tabs[4]:
        st.subheader("Subtitles & Brand")
        subtitle_settings.render_subtitle_settings(state)
    with tabs[5]:
        _render_review(state)
        if st.button(tr("Generate Video"), type="primary", use_container_width=True):
            save_create_state(state)
            actions.render_video_generation(state, uploaded_files, uploaded_audio_file)

    save_create_state(state)

