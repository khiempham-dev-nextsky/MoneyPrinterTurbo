import streamlit as st

from app.config import config
from webui.studio.i18n import tr
from webui.studio.state import StudioCreateState


def render_source_settings(state: StudioCreateState):
    video_sources = [
        (tr("Pexels"), "pexels"),
        (tr("Pixabay"), "pixabay"),
        (tr("Local file"), "local"),
        (tr("TikTok"), "tiktok"),
    ]
    source_values = [value for _, value in video_sources]
    source_index = (
        source_values.index(state.video_source)
        if state.video_source in source_values
        else 0
    )
    selected_source_index = st.segmented_control(
        tr("Video Source"),
        options=range(len(video_sources)),
        format_func=lambda x: video_sources[x][0],
        default=source_index,
    )
    if selected_source_index is None:
        selected_source_index = source_index
    state.video_source = video_sources[selected_source_index][1]
    config.app["video_source"] = state.video_source

    uploaded_files = []
    if state.video_source == "local":
        local_file_types = ["mp4", "mov", "avi", "flv", "mkv", "jpg", "jpeg", "png"]
        uploaded_files = st.file_uploader(
            "Upload Local Files",
            type=local_file_types + [file_type.upper() for file_type in local_file_types],
            accept_multiple_files=True,
            key="studio_local_files",
        )
        if state.local_video_materials:
            st.caption(f"{len(state.local_video_materials)} local materials cached in session")

    if state.video_source == "tiktok":
        st.caption("Configure TikTok search provider and download limits in advanced source options.")

    return uploaded_files


def render_source_advanced_settings(state: StudioCreateState) -> None:
    if state.video_source == "tiktok":
        st.markdown("**TikTok search**")
        tiktok_providers = [
            (tr("SerpAPI"), "serpapi"),
            (tr("OpenAI Web Search"), "openai_web_search"),
        ]
        saved_provider = config.app.get("tiktok_search_provider", "serpapi")
        provider_values = [value for _, value in tiktok_providers]
        provider_index = provider_values.index(saved_provider) if saved_provider in provider_values else 0
        selected_provider_index = st.selectbox(
            tr("TikTok Search Provider"),
            options=range(len(tiktok_providers)),
            format_func=lambda x: tiktok_providers[x][0],
            index=provider_index,
        )
        provider = tiktok_providers[selected_provider_index][1]
        config.app["tiktok_search_provider"] = provider
        if provider == "serpapi":
            config.app["tiktok_search_api_key"] = st.text_input(
                tr("TikTok Search API Key"),
                value=config.app.get("tiktok_search_api_key", ""),
                type="password",
            ).strip()
        config.app["tiktok_max_search_results"] = st.number_input(
            tr("TikTok Max Search Results"),
            min_value=5,
            max_value=50,
            value=int(config.app.get("tiktok_max_search_results") or 20),
            step=1,
        )
        config.app["tiktok_max_downloads"] = st.number_input(
            tr("TikTok Max Downloads"),
            min_value=1,
            max_value=10,
            value=int(config.app.get("tiktok_max_downloads") or 5),
            step=1,
        )
        config.app["tiktok_min_duration"] = st.number_input(
            tr("TikTok Min Duration"),
            min_value=1,
            max_value=30,
            value=int(config.app.get("tiktok_min_duration") or 3),
            step=1,
        )
        config.app["tiktok_cookie_file"] = st.text_input(
            tr("TikTok Cookie File"),
            value=config.app.get("tiktok_cookie_file", ""),
        ).strip()

    st.markdown("**Video options**")
    render_video_options(state)


def render_video_options(state: StudioCreateState) -> None:
    concat_modes = [(tr("Sequential"), "sequential"), (tr("Random"), "random")]
    concat_values = [value for _, value in concat_modes]
    concat_index = concat_values.index(state.video_concat_mode) if state.video_concat_mode in concat_values else 1
    selected_concat = st.selectbox(
        tr("Video Concat Mode"),
        options=range(len(concat_modes)),
        format_func=lambda x: concat_modes[x][0],
        index=concat_index,
    )
    state.video_concat_mode = concat_modes[selected_concat][1]

    transition_modes = [
        (tr("None"), None),
        (tr("Shuffle"), "Shuffle"),
        (tr("FadeIn"), "FadeIn"),
        (tr("FadeOut"), "FadeOut"),
        (tr("SlideIn"), "SlideIn"),
        (tr("SlideOut"), "SlideOut"),
    ]
    transition_values = [value for _, value in transition_modes]
    selected_transition = st.selectbox(
        tr("Video Transition Mode"),
        options=range(len(transition_modes)),
        format_func=lambda x: transition_modes[x][0],
        index=transition_values.index(state.video_transition_mode)
        if state.video_transition_mode in transition_values
        else 0,
    )
    state.video_transition_mode = transition_modes[selected_transition][1]

    aspect_ratios = [(tr("Portrait"), "9:16"), (tr("Landscape"), "16:9")]
    aspect_values = [value for _, value in aspect_ratios]
    aspect_index = aspect_values.index(state.video_aspect) if state.video_aspect in aspect_values else 0
    selected_aspect = st.selectbox(
        tr("Video Ratio"),
        options=range(len(aspect_ratios)),
        format_func=lambda x: aspect_ratios[x][0],
        index=aspect_index,
    )
    state.video_aspect = aspect_ratios[selected_aspect][1]
    state.video_clip_duration = st.selectbox(
        tr("Clip Duration"),
        options=[2, 3, 4, 5, 6, 7, 8, 9, 10],
        index=[2, 3, 4, 5, 6, 7, 8, 9, 10].index(state.video_clip_duration)
        if state.video_clip_duration in [2, 3, 4, 5, 6, 7, 8, 9, 10]
        else 1,
    )
    state.video_count = st.selectbox(
        tr("Number of Videos Generated Simultaneously"),
        options=[1, 2, 3, 4, 5],
        index=[1, 2, 3, 4, 5].index(state.video_count)
        if state.video_count in [1, 2, 3, 4, 5]
        else 0,
    )
    state.n_threads = st.number_input(
        "Threads",
        min_value=1,
        max_value=16,
        value=int(state.n_threads or 2),
        step=1,
    )
