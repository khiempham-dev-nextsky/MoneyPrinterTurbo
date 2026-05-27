import streamlit as st

from app.config import config
from app.services import fonts as font_service
from webui.studio import bootstrap
from webui.studio.brand_presets import find_subtitle_preset, load_subtitle_presets
from webui.studio.i18n import tr
from webui.studio.state import StudioCreateState


def _apply_preset(state: StudioCreateState, preset_name: str) -> None:
    presets = load_subtitle_presets(bootstrap.brand_presets_file)
    preset = find_subtitle_preset(presets, preset_name)
    if not preset:
        return
    state.font_name = preset.font_name
    state.font_size = preset.font_size
    state.text_fore_color = preset.text_fore_color
    state.stroke_color = preset.stroke_color
    state.stroke_width = preset.stroke_width
    state.subtitle_position = preset.subtitle_position
    state.custom_position = preset.custom_position


def render_subtitle_settings(state: StudioCreateState) -> None:
    presets = load_subtitle_presets(bootstrap.brand_presets_file)
    preset_names = [preset.name for preset in presets]
    selected_preset = st.selectbox("Subtitle preset", options=preset_names, index=0)
    if st.button("Apply Subtitle Preset", key="studio_apply_subtitle_preset"):
        _apply_preset(state, selected_preset)

    state.subtitle_enabled = st.checkbox(tr("Enable Subtitles"), value=state.subtitle_enabled)
    font_names = font_service.list_font_names(bootstrap.font_dir)
    default_font = font_service.select_default_font_name(
        font_names=font_names,
        saved_font_name=state.font_name,
        ui_language=st.session_state.get("ui_language", bootstrap.system_locale),
        video_language=state.video_language,
    )
    font_index = font_names.index(default_font) if default_font in font_names else 0
    state.font_name = st.selectbox(
        tr("Font"),
        font_names,
        index=font_index,
        format_func=font_service.format_font_label,
    )
    config.ui["font_name"] = state.font_name

    subtitle_positions = [
        (tr("Top"), "top"),
        (tr("Center"), "center"),
        (tr("Bottom"), "bottom"),
        (tr("Custom"), "custom"),
    ]
    position_values = [value for _, value in subtitle_positions]
    position_index = position_values.index(state.subtitle_position) if state.subtitle_position in position_values else 2
    selected_position = st.selectbox(
        tr("Position"),
        options=range(len(subtitle_positions)),
        format_func=lambda x: subtitle_positions[x][0],
        index=position_index,
    )
    state.subtitle_position = subtitle_positions[selected_position][1]
    config.ui["subtitle_position"] = state.subtitle_position

    if state.subtitle_position == "custom":
        state.custom_position = st.number_input(
            tr("Custom Position (% from top)"),
            min_value=0.0,
            max_value=100.0,
            value=float(state.custom_position),
            step=1.0,
        )
        config.ui["custom_position"] = state.custom_position

    color_col, size_col = st.columns([1, 2])
    with color_col:
        state.text_fore_color = st.color_picker(
            tr("Font Color"),
            value=state.text_fore_color,
        )
        config.ui["text_fore_color"] = state.text_fore_color
    with size_col:
        state.font_size = st.slider(tr("Font Size"), 30, 100, int(state.font_size))
        config.ui["font_size"] = state.font_size

    stroke_color_col, stroke_width_col = st.columns([1, 2])
    with stroke_color_col:
        state.stroke_color = st.color_picker(tr("Stroke Color"), value=state.stroke_color)
    with stroke_width_col:
        state.stroke_width = st.slider(
            tr("Stroke Width"),
            min_value=0.0,
            max_value=10.0,
            value=float(state.stroke_width),
        )

    st.markdown(
        f"""
        <div style="background:#111827;border-radius:8px;padding:24px;text-align:center;">
          <span style="
            color:{state.text_fore_color};
            font-size:{min(state.font_size, 72)}px;
            font-weight:700;
            text-shadow: 0 0 {max(state.stroke_width, 0.5) * 2}px {state.stroke_color};
          ">Subtitle Preview</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

