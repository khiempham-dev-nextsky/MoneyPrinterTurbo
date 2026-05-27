from dataclasses import asdict, dataclass, field, fields
from typing import Any

import streamlit as st

from app.config import config
from app.models.schema import (
    MaterialInfo,
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)


@dataclass
class StudioCreateState:
    video_subject: str = ""
    video_script: str = ""
    video_terms: str = ""
    video_language: str = ""
    active_step: str = "brief"
    local_video_materials: list[dict[str, Any]] = field(default_factory=list)
    uploaded_audio_path: str | None = None
    custom_audio_file: str | None = None

    video_source: str = "pexels"
    video_aspect: str = VideoAspect.portrait.value
    video_concat_mode: str = VideoConcatMode.random.value
    video_transition_mode: str | None = None
    video_clip_duration: int = 3
    video_count: int = 1
    n_threads: int = 2

    voice_name: str = ""
    voice_volume: float = 1.0
    voice_rate: float = 1.0
    bgm_type: str = "random"
    bgm_file: str = ""
    bgm_volume: float = 0.2

    subtitle_enabled: bool = True
    subtitle_position: str = "bottom"
    custom_position: float = 70.0
    font_name: str = "STHeitiMedium.ttc"
    text_fore_color: str = "#FFFFFF"
    text_background_color: bool | str = True
    font_size: int = 60
    stroke_color: str = "#000000"
    stroke_width: float = 1.5


@dataclass
class StudioRenderSnapshot:
    task_id: str
    state: int | None = None
    progress: int = 0
    status_label: str = "Idle"
    log_lines: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    task_dir: str = ""
    error: str = ""


def serialize_create_state(state: StudioCreateState) -> dict[str, Any]:
    return asdict(state)


def deserialize_create_state(payload: dict[str, Any] | None) -> StudioCreateState:
    if not isinstance(payload, dict):
        return StudioCreateState()
    valid_names = {item.name for item in fields(StudioCreateState)}
    values = {key: value for key, value in payload.items() if key in valid_names}
    return StudioCreateState(**values)


def material_records_to_infos(records: list[dict[str, Any]]) -> list[MaterialInfo]:
    materials = []
    for record in records:
        url = record.get("url", "")
        if not url:
            continue
        material = MaterialInfo()
        material.provider = record.get("provider", "local")
        material.url = url
        material.duration = record.get("duration", 0)
        materials.append(material)
    return materials


def build_video_params(state: StudioCreateState) -> VideoParams:
    params = VideoParams(
        video_subject=state.video_subject.strip(),
        video_script=state.video_script,
        video_terms=state.video_terms,
        video_aspect=state.video_aspect,
        video_concat_mode=state.video_concat_mode,
        video_transition_mode=state.video_transition_mode,
        video_clip_duration=int(state.video_clip_duration),
        video_count=int(state.video_count),
        video_source=state.video_source,
        custom_audio_file=state.custom_audio_file,
        video_language=state.video_language,
        voice_name=state.voice_name,
        voice_volume=float(state.voice_volume),
        voice_rate=float(state.voice_rate),
        bgm_type=state.bgm_type,
        bgm_file=state.bgm_file,
        bgm_volume=float(state.bgm_volume),
        subtitle_enabled=bool(state.subtitle_enabled),
        subtitle_position=state.subtitle_position,
        custom_position=float(state.custom_position),
        font_name=state.font_name,
        text_fore_color=state.text_fore_color,
        text_background_color=state.text_background_color,
        font_size=int(state.font_size),
        stroke_color=state.stroke_color,
        stroke_width=float(state.stroke_width),
        n_threads=int(state.n_threads),
    )
    if state.video_source == "local":
        params.video_materials = material_records_to_infos(state.local_video_materials)
    return params


def _default_create_state() -> StudioCreateState:
    return StudioCreateState(
        video_subject=st.session_state.get("video_subject", ""),
        video_script=st.session_state.get("video_script", ""),
        video_terms=st.session_state.get("video_terms", ""),
        video_language=st.session_state.get("video_language", ""),
        local_video_materials=st.session_state.get("local_video_materials", []),
        video_source=config.app.get("video_source", "pexels"),
        subtitle_position=config.ui.get("subtitle_position", "bottom"),
        custom_position=float(config.ui.get("custom_position", 70.0)),
        font_name=config.ui.get("font_name", "STHeitiMedium.ttc"),
        text_fore_color=config.ui.get("text_fore_color", "#FFFFFF"),
        font_size=int(config.ui.get("font_size", 60)),
        voice_name=config.ui.get("voice_name", ""),
    )


def load_create_state() -> StudioCreateState:
    default_state = _default_create_state()
    saved_state = st.session_state.get("studio_create_state")
    if isinstance(saved_state, dict):
        merged = serialize_create_state(default_state)
        merged.update(saved_state)
        return deserialize_create_state(merged)
    return default_state


def save_create_state(state: StudioCreateState) -> None:
    st.session_state["studio_create_state"] = serialize_create_state(state)
    st.session_state["video_subject"] = state.video_subject
    st.session_state["video_script"] = state.video_script
    st.session_state["video_terms"] = state.video_terms
    st.session_state["video_language"] = state.video_language
    st.session_state["local_video_materials"] = state.local_video_materials
