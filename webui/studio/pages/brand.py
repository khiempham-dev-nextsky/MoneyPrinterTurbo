import streamlit as st

from webui.studio import bootstrap
from webui.studio.brand_presets import (
    SubtitlePreset,
    default_subtitle_presets,
    load_subtitle_presets,
    save_subtitle_presets,
)
from webui.studio.components import layout


def _render_preset_preview(preset: SubtitlePreset) -> None:
    st.markdown(
        f"""
        <div style="background:#111827;border-radius:8px;padding:24px;text-align:center;">
          <span style="
            color:{preset.text_fore_color};
            font-size:{min(preset.font_size, 72)}px;
            font-weight:700;
            text-shadow:0 0 {max(preset.stroke_width, 0.5) * 2}px {preset.stroke_color};
          ">{preset.name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page() -> None:
    layout.page_header(
        "Brand",
        "Manage subtitle presets that can be reused in the Create workflow.",
    )
    presets = load_subtitle_presets(bootstrap.brand_presets_file)
    if st.button("Reset to default presets"):
        presets = default_subtitle_presets()
        save_subtitle_presets(bootstrap.brand_presets_file, presets)
        st.rerun()

    selected_name = st.selectbox("Preset", options=[preset.name for preset in presets])
    selected = next(preset for preset in presets if preset.name == selected_name)
    _render_preset_preview(selected)

    with st.form("studio_new_subtitle_preset"):
        st.subheader("Create subtitle preset")
        name = st.text_input("Name")
        font_name = st.text_input("Font file", value=selected.font_name)
        font_size = st.slider("Font size", 30, 100, selected.font_size)
        text_fore_color = st.color_picker("Font color", selected.text_fore_color)
        stroke_color = st.color_picker("Stroke color", selected.stroke_color)
        stroke_width = st.slider("Stroke width", 0.0, 10.0, float(selected.stroke_width))
        subtitle_position = st.selectbox(
            "Position",
            options=["top", "center", "bottom", "custom"],
            index=["top", "center", "bottom", "custom"].index(selected.subtitle_position)
            if selected.subtitle_position in ["top", "center", "bottom", "custom"]
            else 2,
        )
        custom_position = st.number_input(
            "Custom position",
            min_value=0.0,
            max_value=100.0,
            value=float(selected.custom_position),
        )
        submitted = st.form_submit_button("Save Preset")
        if submitted and name.strip():
            presets = [preset for preset in presets if preset.name != name.strip()]
            presets.append(
                SubtitlePreset(
                    name=name.strip(),
                    font_name=font_name.strip(),
                    font_size=int(font_size),
                    text_fore_color=text_fore_color,
                    stroke_color=stroke_color,
                    stroke_width=float(stroke_width),
                    subtitle_position=subtitle_position,
                    custom_position=float(custom_position),
                )
            )
            save_subtitle_presets(bootstrap.brand_presets_file, presets)
            st.success("Preset saved")
            st.rerun()

