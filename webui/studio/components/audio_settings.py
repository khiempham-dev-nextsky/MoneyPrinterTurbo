import os
from uuid import uuid4

import streamlit as st

from app.config import config
from app.services import voice
from app.utils import utils
from webui.studio.i18n import tr
from webui.studio.state import StudioCreateState


def _voices_for_server(server: str) -> list[str]:
    if server == "siliconflow":
        return voice.get_siliconflow_voices()
    if server == "gemini-tts":
        return voice.get_gemini_voices()
    all_voices = voice.get_all_azure_voices(filter_locals=None)
    if server == "azure-tts-v2":
        return [item for item in all_voices if "V2" in item]
    return [item for item in all_voices if "V2" not in item]


def render_audio_settings(state: StudioCreateState):
    tts_servers = [
        ("azure-tts-v1", "Azure TTS V1"),
        ("azure-tts-v2", "Azure TTS V2"),
        ("siliconflow", "SiliconFlow TTS"),
        ("gemini-tts", "Google Gemini TTS"),
    ]
    saved_server = config.ui.get("tts_server", "azure-tts-v1")
    server_values = [value for value, _ in tts_servers]
    server_index = server_values.index(saved_server) if saved_server in server_values else 0
    selected_server_index = st.selectbox(
        tr("TTS Servers"),
        options=range(len(tts_servers)),
        format_func=lambda x: tts_servers[x][1],
        index=server_index,
    )
    selected_server = tts_servers[selected_server_index][0]
    config.ui["tts_server"] = selected_server

    filtered_voices = _voices_for_server(selected_server)
    friendly_names = {
        item: item.replace("Female", tr("Female")).replace("Male", tr("Male")).replace("Neural", "")
        for item in filtered_voices
    }
    saved_voice = config.ui.get("voice_name", "")
    saved_voice_index = 0
    if saved_voice in friendly_names:
        saved_voice_index = list(friendly_names.keys()).index(saved_voice)
    elif friendly_names:
        for index, item in enumerate(filtered_voices):
            if item.lower().startswith(st.session_state.get("ui_language", "").lower()):
                saved_voice_index = index
                break

    if friendly_names:
        selected_friendly = st.selectbox(
            tr("Speech Synthesis"),
            options=list(friendly_names.values()),
            index=min(saved_voice_index, len(friendly_names) - 1),
        )
        state.voice_name = list(friendly_names.keys())[
            list(friendly_names.values()).index(selected_friendly)
        ]
        config.ui["voice_name"] = state.voice_name
    else:
        st.warning(tr("No voices available for the selected TTS server. Please select another server."))
        state.voice_name = ""
        config.ui["voice_name"] = ""

    if friendly_names and st.button(tr("Play Voice"), key="studio_play_voice"):
        play_content = state.video_subject or state.video_script or tr("Voice Example")
        with st.spinner(tr("Synthesizing Voice")):
            temp_dir = utils.storage_dir("temp", create=True)
            audio_file = os.path.join(temp_dir, f"tmp-voice-{str(uuid4())}.mp3")
            sub_maker = voice.tts(
                text=play_content,
                voice_name=state.voice_name,
                voice_rate=state.voice_rate,
                voice_file=audio_file,
                voice_volume=state.voice_volume,
            )
            if sub_maker and os.path.exists(audio_file):
                st.audio(audio_file, format="audio/mp3")
                os.remove(audio_file)

    return None


def render_audio_advanced_settings(state: StudioCreateState):
    selected_server = config.ui.get("tts_server", "azure-tts-v1")

    if selected_server == "azure-tts-v2" or (
        state.voice_name and voice.is_azure_v2_voice(state.voice_name)
    ):
        config.azure["speech_region"] = st.text_input(
            tr("Speech Region"),
            value=config.azure.get("speech_region", ""),
        )
        config.azure["speech_key"] = st.text_input(
            tr("Speech Key"),
            value=config.azure.get("speech_key", ""),
            type="password",
        )

    if selected_server == "siliconflow" or (
        state.voice_name and voice.is_siliconflow_voice(state.voice_name)
    ):
        config.siliconflow["api_key"] = st.text_input(
            tr("SiliconFlow API Key"),
            value=config.siliconflow.get("api_key", ""),
            type="password",
        )
        st.info(
            tr("SiliconFlow TTS Settings")
            + ":\n- "
            + tr("Speed: Range [0.25, 4.0], default is 1.0")
            + "\n- "
            + tr("Volume: Uses Speech Volume setting, default 1.0 maps to gain 0")
        )

    col_a, col_b = st.columns(2)
    volume_options = [0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0]
    rate_options = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0]
    with col_a:
        state.voice_volume = st.selectbox(
            tr("Speech Volume"),
            options=volume_options,
            index=volume_options.index(state.voice_volume)
            if state.voice_volume in volume_options
            else 2,
        )
    with col_b:
        state.voice_rate = st.selectbox(
            tr("Speech Rate"),
            options=rate_options,
            index=rate_options.index(state.voice_rate)
            if state.voice_rate in rate_options
            else 2,
        )

    uploaded_audio_file = st.file_uploader(
        tr("Custom Audio File"),
        type=["mp3", "wav", "m4a", "aac", "flac", "ogg", "MP3", "WAV", "M4A", "AAC", "FLAC", "OGG"],
        accept_multiple_files=False,
        key="studio_custom_audio",
    )
    if uploaded_audio_file:
        st.audio(uploaded_audio_file, format="audio/mp3")
        st.info(tr("Custom audio will be used directly. TTS synthesis will be skipped for this task."))

    bgm_options = [
        (tr("No Background Music"), ""),
        (tr("Random Background Music"), "random"),
        (tr("Custom Background Music"), "custom"),
    ]
    bgm_values = [value for _, value in bgm_options]
    selected_bgm = st.selectbox(
        tr("Background Music"),
        options=range(len(bgm_options)),
        format_func=lambda x: bgm_options[x][0],
        index=bgm_values.index(state.bgm_type) if state.bgm_type in bgm_values else 1,
    )
    state.bgm_type = bgm_options[selected_bgm][1]
    if state.bgm_type == "custom":
        state.bgm_file = st.text_input(tr("Custom Background Music File"))
    state.bgm_volume = st.selectbox(
        tr("Background Music Volume"),
        options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        index=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0].index(
            state.bgm_volume
        )
        if state.bgm_volume in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        else 2,
    )
    return uploaded_audio_file
