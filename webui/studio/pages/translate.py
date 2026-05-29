from html import escape

import streamlit as st

from app.config import config
from app.models import const
from webui.studio import bootstrap, translate_jobs
from webui.studio.components import (
    audio_settings,
    layout,
    status as render_status,
    subtitle_settings,
)
from webui.studio.i18n import tr
from webui.studio.state import (
    build_translate_params,
    load_translate_state,
    save_translate_state,
)
from webui.studio.validators import validate_translate_request


def _render_source_section(state):
    uploaded_source_file = st.file_uploader(
        "Video nguồn",
        type=["mp4", "mov", "mkv", "webm", "MP4", "MOV", "MKV", "WEBM"],
        accept_multiple_files=False,
        key="studio_translate_source_file",
    )
    if uploaded_source_file:
        state.source_video_url = ""
        st.video(uploaded_source_file)

    state.source_video_url = st.text_input(
        "Hoặc URL video",
        value=state.source_video_url,
        placeholder="https://www.tiktok.com/@user/video/...",
        key="studio_translate_source_url",
    ).strip()

    languages = [(tr("Auto Detect"), "")]
    for code in bootstrap.support_locales:
        languages.append((code, code))

    source_values = [value for _, value in languages]
    source_index = (
        source_values.index(state.source_language)
        if state.source_language in source_values
        else 0
    )
    target_index = (
        source_values.index(state.target_language)
        if state.target_language in source_values
        else max(1, source_values.index("vi-VN") if "vi-VN" in source_values else 1)
    )
    col_a, col_b = st.columns(2)
    with col_a:
        selected_source = st.selectbox(
            "Ngôn ngữ gốc",
            options=range(len(languages)),
            format_func=lambda x: languages[x][0],
            index=source_index,
        )
        state.source_language = languages[selected_source][1]
    with col_b:
        selected_target = st.selectbox(
            "Dịch sang",
            options=range(1, len(languages)),
            format_func=lambda x: languages[x][0],
            index=max(0, target_index - 1),
        )
        state.target_language = languages[selected_target][1]
        state.video_language = state.target_language

    state.translated_script = st.text_area(
        "Kịch bản dịch thủ công (tùy chọn)",
        value=state.translated_script,
        height=160,
        placeholder="Để trống để AI dịch theo transcript. Nếu nhập thủ công, mỗi dòng nên tương ứng một segment.",
    )
    return uploaded_source_file


def _render_video_options(state) -> None:
    aspect_options = [
        ("Giữ tỷ lệ video gốc", "source"),
        ("Dọc 9:16", "9:16"),
        ("Ngang 16:9", "16:9"),
        ("Vuông 1:1", "1:1"),
    ]
    aspect_values = [value for _, value in aspect_options]
    selected_aspect = st.selectbox(
        "Tỷ lệ xuất",
        options=range(len(aspect_options)),
        format_func=lambda x: aspect_options[x][0],
        index=aspect_values.index(state.video_aspect)
        if state.video_aspect in aspect_values
        else 0,
    )
    state.video_aspect = aspect_options[selected_aspect][1]

    fit_options = [("Contain", "contain"), ("Cover", "cover")]
    fit_values = [value for _, value in fit_options]
    selected_fit = st.selectbox(
        "Cách fit video",
        options=range(len(fit_options)),
        format_func=lambda x: fit_options[x][0],
        index=fit_values.index(state.video_fit_mode)
        if state.video_fit_mode in fit_values
        else 0,
    )
    state.video_fit_mode = fit_options[selected_fit][1]
    state.n_threads = st.slider("Số luồng render", min_value=1, max_value=8, value=int(state.n_threads))


def _render_audio_section(state) -> None:
    col_voice, col_source = st.columns(2)
    with col_voice:
        state.voice_enabled = st.toggle(
            "Giọng đọc dịch",
            value=bool(state.voice_enabled),
            help="Bật để tạo giọng đọc bản dịch bằng TTS.",
        )
    with col_source:
        state.source_audio_enabled = st.toggle(
            "Âm thanh gốc",
            value=bool(state.source_audio_enabled),
            help="Giữ lại tiếng gốc của video khi xuất bản dịch.",
        )

    if state.source_audio_enabled:
        state.source_audio_volume = st.slider(
            "Âm lượng âm thanh gốc",
            min_value=0.0,
            max_value=1.0,
            value=float(state.source_audio_volume),
            step=0.05,
        )

    if not state.voice_enabled:
        st.caption("Đang tắt giọng đọc dịch; video sẽ giữ âm thanh gốc nếu bật Âm thanh gốc.")
        return

    dubbing_options = [
        ("Tự nhiên", "natural"),
        ("Liền mạch", "continuous"),
        ("Khớp nhịp video", "sync"),
    ]
    dubbing_values = [value for _, value in dubbing_options]
    selected_dubbing = st.selectbox(
        "Chế độ lồng tiếng",
        options=range(len(dubbing_options)),
        format_func=lambda x: dubbing_options[x][0],
        index=dubbing_values.index(state.dubbing_mode)
        if state.dubbing_mode in dubbing_values
        else 0,
    )
    state.dubbing_mode = dubbing_options[selected_dubbing][1]
    if state.dubbing_mode == "natural":
        st.caption("TTS toàn bộ bản dịch một lần như giọng đọc ban đầu, nghe liền mạch hơn.")
    elif state.dubbing_mode == "continuous":
        st.caption("TTS từng câu nhưng rút ngắn khoảng nghỉ để giọng đọc liền mạch hơn.")
    else:
        st.caption("TTS từng câu và đặt vào đúng timestamp của video gốc.")

    audio_settings.render_audio_settings(state)
    with layout.advanced_accordion("Tùy chỉnh âm thanh nâng cao", expanded=False):
        audio_settings.render_audio_advanced_settings(state, allow_custom_audio=False)


def _render_subtitle_section(state) -> None:
    subtitle_settings.render_subtitle_settings(state)
    with layout.advanced_accordion("Tinh chỉnh phụ đề nâng cao", expanded=False):
        subtitle_settings.render_subtitle_advanced_settings(state)


def _friendly_value(value: str | None, fallback: str = "-") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _render_translate_summary_panel(state) -> None:
    st.markdown("### Tóm tắt")
    source = state.source_video_url or state.source_video_path
    dubbing_labels = {
        "natural": "Tự nhiên",
        "continuous": "Liền mạch",
        "sync": "Khớp nhịp",
    }
    layout.summary_block(
        [
            ("Nguồn", _friendly_value(source, "Chưa chọn")),
            ("Ngôn ngữ gốc", _friendly_value(state.source_language, "Tự động")),
            ("Dịch sang", state.target_language),
            ("Tỷ lệ", state.video_aspect),
            ("Giọng đọc", "Bật" if state.voice_enabled else "Tắt"),
            ("Âm thanh gốc", "Bật" if state.source_audio_enabled else "Tắt"),
            (
                "Lồng tiếng",
                dubbing_labels.get(state.dubbing_mode, state.dubbing_mode)
                if state.voice_enabled
                else "-",
            ),
            (
                "Giọng",
                _friendly_value(state.voice_name, "Chưa chọn") if state.voice_enabled else "-",
            ),
            ("Phụ đề", "Bật" if state.subtitle_enabled else "Tắt"),
        ]
    )


def _friendly_translate_stage(snapshot) -> tuple[str, str]:
    if not snapshot:
        return "Chưa bắt đầu", "Upload video hoặc nhập URL, chọn voice rồi bấm Dịch video."
    if snapshot.state == const.TASK_STATE_COMPLETE:
        return "Hoàn tất", "Video dịch đã render xong."
    if snapshot.state == const.TASK_STATE_FAILED:
        return "Có lỗi khi dịch video", snapshot.error or "Mở nhật ký để xem chi tiết."

    log_text = "\n".join(snapshot.log_lines[-40:]).lower()
    stage_rules = [
        (("source video", "download", "queued"), "Đang lấy video nguồn"),
        (("extract", "source-audio", "ffmpeg"), "Đang tách audio"),
        (("transcribe", "whisper", "subtitle"), "Đang nghe và tạo transcript"),
        (("translate", "llm"), "Đang dịch bằng LLM"),
        (("tts", "audio", "voice"), "Đang tạo giọng đọc"),
        (("render", "composite", "final"), "Đang render video dịch"),
    ]
    for needles, label in stage_rules:
        if any(needle in log_text for needle in needles):
            return label, snapshot.status_label
    return "Đang dịch video", snapshot.status_label


@st.dialog("Nhật ký dịch video", width="large")
def _render_system_log_dialog(log_text: str) -> None:
    st.markdown('<div class="studio-log-dialog-marker"></div>', unsafe_allow_html=True)
    if log_text:
        st.caption("Log mới nhất, cuộn trong modal để xem đầy đủ.")
        st.code(log_text)
    else:
        st.caption("Chưa có log.")


def _render_system_log_panel(snapshot) -> None:
    st.markdown("### Nhật ký hệ thống")
    log_lines = snapshot.log_lines if snapshot and snapshot.log_lines else []
    log_text = "\n".join(log_lines[-300:])
    if st.button("Mở nhật ký", use_container_width=True):
        _render_system_log_dialog(log_text)
    if log_lines:
        st.caption(f"Có {len(log_lines)} dòng log.")
    else:
        st.caption("Chưa có log.")


def _render_progress_panel(snapshot, issues) -> None:
    st.markdown("### Tiến trình")
    if issues and not snapshot:
        st.warning("Cần bổ sung thông tin trước khi dịch video.")
    stage, helper = _friendly_translate_stage(snapshot)
    st.markdown(
        f"""
        <div class="studio-render-status">
          <strong>{escape(stage)}</strong>
          <span>{escape(helper)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    progress = max(0, min(int(snapshot.progress or 0), 100)) if snapshot else 0
    st.progress(progress / 100)
    if snapshot and snapshot.error:
        st.error(snapshot.error)
    if snapshot and snapshot.videos:
        render_status.render_video_outputs(snapshot.videos)
    if snapshot and snapshot.task_dir:
        col_a, col_b = st.columns(2)
        with col_a:
            st.link_button("Mở thư mục", f"file://{snapshot.task_dir}", use_container_width=True)
        with col_b:
            if st.button("Xóa task", use_container_width=True):
                translate_jobs.clear_active_translate_task()
                st.rerun()
    if snapshot and st.button("Làm mới tiến trình", use_container_width=True):
        st.rerun()


def _start_translate(state, uploaded_source_file, issues) -> None:
    if st.button("Dịch video", type="primary", use_container_width=True, disabled=bool(issues)):
        save_translate_state(state)
        try:
            snapshot = translate_jobs.start_translate_job(state, uploaded_source_file)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success(f"Translate task started: {snapshot.task_id}")
        st.rerun()


def _render_active_translate_status() -> None:
    snapshot = translate_jobs.get_active_translate_snapshot()
    _render_progress_panel(snapshot, issues=[])
    _render_system_log_panel(snapshot)


if hasattr(st, "fragment"):
    _render_active_translate_status_fragment = st.fragment(run_every="2s")(
        _render_active_translate_status
    )
else:
    _render_active_translate_status_fragment = _render_active_translate_status


def _render_translate_rail(state, uploaded_source_file) -> None:
    st.markdown('<div class="studio-render-card-marker"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="studio-render-card-title">
          <h3>Xuất video dịch</h3>
          <p>Kiểm tra nguồn, voice, phụ đề và tiến trình dịch.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    params = build_translate_params(state)
    issues = validate_translate_request(params, dict(config.app))
    if issues:
        for issue in issues:
            st.warning(tr(issue.message))
    else:
        st.success("Đã sẵn sàng dịch video.")

    _render_translate_summary_panel(state)
    _start_translate(state, uploaded_source_file, issues)

    st.divider()
    snapshot = translate_jobs.get_active_translate_snapshot()
    if (
        snapshot
        and snapshot.state == const.TASK_STATE_PROCESSING
        and st.session_state.get("studio_translate_autorefresh", True)
    ):
        _render_active_translate_status_fragment()
    else:
        _render_progress_panel(snapshot, issues)
        _render_system_log_panel(snapshot)


def render_page() -> None:
    layout.page_header(
        "Dịch video",
        "Nghe video nguồn, dịch transcript và render giọng đọc mới",
    )
    state = load_translate_state()

    main_col, render_col = st.columns([6, 4], gap="small")
    with main_col:
        with layout.section_card("Video nguồn", "Upload file hoặc nhập URL TikTok/video public."):
            uploaded_source_file = _render_source_section(state)
        with layout.section_card("Nâng cao", "Tùy chọn tỷ lệ, fit video và số luồng render."):
            with layout.advanced_accordion("Mở tùy chọn nâng cao", expanded=False):
                _render_video_options(state)
        with layout.section_card("Giọng đọc & âm thanh", "Chọn voice TTS cho bản dịch."):
            _render_audio_section(state)
        with layout.section_card("Phụ đề", "Chọn preset phụ đề cho video dịch."):
            _render_subtitle_section(state)

    with render_col:
        with st.container(border=True):
            _render_translate_rail(state, uploaded_source_file)

    save_translate_state(state)
