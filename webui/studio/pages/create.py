from html import escape

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
    state.video_subject = st.text_input(
        "Brief / ý tưởng",
        value=state.video_subject,
        key="studio_video_subject",
        placeholder="Ví dụ: 5 thói quen giúp ngủ ngon hơn",
    ).strip()

    video_languages = [(tr("Auto Detect"), "")]
    for code in bootstrap.support_locales:
        video_languages.append((code, code))
    current_language = state.video_language
    values = [value for _, value in video_languages]
    language_index = values.index(current_language) if current_language in values else 0
    selected_language = st.selectbox(
        "Ngôn ngữ kịch bản",
        options=range(len(video_languages)),
        format_func=lambda x: video_languages[x][0],
        index=language_index,
    )
    state.video_language = video_languages[selected_language][1]
    st.caption("Nhập brief ngắn, sau đó dùng AI để tạo kịch bản và từ khóa nếu cần.")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(
            "Gợi ý AI",
            key="studio_generate_script",
            help=tr("Generate Video Script and Keywords"),
            use_container_width=True,
        ):
            actions.generate_script_and_terms(state)
    with col_b:
        if st.button(
            "Tạo lại từ khóa",
            key="studio_generate_terms",
            help=tr("Generate Video Keywords"),
            use_container_width=True,
        ):
            actions.generate_terms_only(state)

    state.video_script = st.text_area(
        "Kịch bản video",
        value=state.video_script,
        height=240,
        key="studio_video_script",
        placeholder="Dán kịch bản có sẵn hoặc để AI tạo từ brief.",
    )
    state.video_terms = st.text_area(
        "Từ khóa video",
        value=state.video_terms,
        key="studio_video_terms",
        placeholder="sleep routine, deep sleep, healthy habits",
    )


def _render_source_section(state):
    uploaded_files = source_settings.render_source_settings(state)
    st.caption("Chọn nguồn footage chính. Các giới hạn tải, cookie và tùy chọn kỹ thuật nằm ở phần Nâng cao.")
    return uploaded_files


def _render_audio_section(state):
    audio_settings.render_audio_settings(state)
    uploaded_audio_file = None
    with layout.advanced_accordion("Tùy chỉnh âm thanh nâng cao", expanded=False):
        uploaded_audio_file = audio_settings.render_audio_advanced_settings(state)
    return uploaded_audio_file


def _render_subtitle_section(state) -> None:
    subtitle_settings.render_subtitle_settings(state)
    with layout.advanced_accordion("Tinh chỉnh phụ đề nâng cao", expanded=False):
        subtitle_settings.render_subtitle_advanced_settings(state)


def _render_step_overview() -> None:
    st.markdown(
        """
        <div class="studio-create-step-strip">
          <span class="studio-step-pill"><strong>1</strong> Nội dung</span>
          <span class="studio-step-pill"><strong>2</strong> Nguồn video</span>
          <span class="studio-step-pill"><strong>3</strong> Giọng đọc</span>
          <span class="studio-step-pill"><strong>4</strong> Phụ đề & xuất</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _friendly_value(value: str | None, fallback: str = "-") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _render_video_summary_panel(state) -> None:
    st.markdown("### Tóm tắt video")
    layout.summary_block(
        [
            ("Nội dung", _friendly_value(state.video_subject, "Chưa nhập")),
            ("Nguồn", state.video_source),
            ("Tỷ lệ", state.video_aspect),
            ("Giọng", _friendly_value(state.voice_name, "Chưa chọn")),
            ("Phụ đề", "Bật" if state.subtitle_enabled else "Tắt"),
            ("Số video", str(state.video_count)),
        ]
    )


def _render_video_preview_frame(state) -> None:
    title = _friendly_value(state.video_subject or state.video_script, "Chưa có nội dung")
    safe_title = escape(title[:90])
    safe_source = escape(str(state.video_source))
    subtitle_state = "bật" if state.subtitle_enabled else "tắt"
    st.markdown("### Preview 9:16")
    st.markdown(
        f"""
        <div class="studio-video-preview-frame">
          <span>9:16 Preview</span>
          <strong>{safe_title}</strong>
          <small>Nguồn: {safe_source} · Phụ đề: {subtitle_state}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _friendly_render_stage(snapshot) -> tuple[str, str]:
    if not snapshot:
        return "Chưa bắt đầu", "Nhập nội dung và bấm Tạo video để bắt đầu."
    if snapshot.state == const.TASK_STATE_COMPLETE:
        return "Hoàn tất", "Video đã render xong. Bạn có thể xem output bên dưới."
    if snapshot.state == const.TASK_STATE_FAILED:
        return "Có lỗi khi tạo video", snapshot.error or "Mở nhật ký hệ thống để xem chi tiết."

    log_text = "\n".join(snapshot.log_lines[-40:]).lower()
    stage_rules = [
        (("generating video script", "script"), "Đang tạo script"),
        (("downloading videos", "discovering", "material", "source"), "Đang tìm source"),
        (("generating audio", "tts", "voice"), "Đang tạo voice"),
        (("subtitle", "subtitles"), "Đang render phụ đề"),
        (("combine", "concat", "rendering video", "composite"), "Đang ghép video"),
    ]
    for needles, label in stage_rules:
        if any(needle in log_text for needle in needles):
            return label, snapshot.status_label
    if snapshot.state == const.TASK_STATE_PROCESSING:
        return "Đang tạo video", snapshot.status_label
    return "Sẵn sàng", snapshot.status_label


@st.dialog("Nhật ký hệ thống", width="large")
def _render_system_log_dialog(log_text: str) -> None:
    st.markdown('<div class="studio-log-dialog-marker"></div>', unsafe_allow_html=True)
    if log_text:
        st.caption("Log render mới nhất, cuộn trong modal để xem đầy đủ.")
        st.code(log_text)
    else:
        st.caption("Chưa có log render.")


def _render_system_log_panel(snapshot) -> None:
    st.markdown("### Nhật ký hệ thống")
    log_lines = snapshot.log_lines if snapshot and snapshot.log_lines else []
    log_text = "\n".join(log_lines[-300:])
    if st.button("Mở nhật ký hệ thống", use_container_width=True):
        _render_system_log_dialog(log_text)
    if log_lines:
        st.caption(f"Có {len(log_lines)} dòng log. Mở modal để xem chi tiết.")
    else:
        st.caption("Chưa có log render.")


def _render_render_progress_panel(snapshot, issues) -> None:
    st.markdown("### Tiến trình")
    if issues and not snapshot:
        st.warning("Cần bổ sung thông tin trước khi tạo video.")
    stage, helper = _friendly_render_stage(snapshot)
    safe_stage = escape(stage)
    safe_helper = escape(helper)
    st.markdown(
        f"""
        <div class="studio-render-status">
          <strong>{safe_stage}</strong>
          <span>{safe_helper}</span>
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
                render_jobs.clear_active_render_task()
                st.rerun()
    if snapshot and st.button("Làm mới tiến trình", use_container_width=True):
        st.rerun()


def _render_primary_cta_group(state, uploaded_files, uploaded_audio_file, issues) -> None:
    if st.button(
        tr("Generate Video"),
        type="primary",
        use_container_width=True,
        disabled=bool(issues),
    ):
        save_create_state(state)
        actions.render_video_generation(state, uploaded_files, uploaded_audio_file)
    st.button(
        "Lưu preset",
        use_container_width=True,
        disabled=True,
        help="Preset toàn bộ workflow chưa có trong logic hiện tại.",
    )


def _render_active_render_status() -> None:
    snapshot = render_jobs.get_active_render_snapshot()
    _render_render_progress_panel(snapshot, issues=[])
    _render_system_log_panel(snapshot)


if hasattr(st, "fragment"):
    _render_active_render_status_fragment = st.fragment(run_every="2s")(
        _render_active_render_status
    )
else:
    _render_active_render_status_fragment = _render_active_render_status


def _render_render_rail(state, uploaded_files, uploaded_audio_file) -> None:
    st.markdown('<div class="studio-render-card-marker"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="studio-render-card-title">
          <h3>Xuất video</h3>
          <p>Kiểm tra nhanh cấu hình, xem tiến trình và tạo video.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    params = build_video_params(state)
    issues = validate_render_request(params, dict(config.app))
    if issues:
        for issue in issues:
            st.warning(tr(issue.message))
    else:
        st.success("Đã sẵn sàng tạo video.")

    _render_video_summary_panel(state)
    _render_video_preview_frame(state)
    _render_primary_cta_group(state, uploaded_files, uploaded_audio_file, issues)

    st.divider()
    snapshot = render_jobs.get_active_render_snapshot()
    if (
        snapshot
        and snapshot.state == const.TASK_STATE_PROCESSING
        and st.session_state.get("studio_render_autorefresh", True)
    ):
        _render_active_render_status_fragment()
    else:
        _render_render_progress_panel(snapshot, issues)
        _render_system_log_panel(snapshot)


def render_page() -> None:
    layout.page_header(
        "Tạo video",
        "Tạo video ngắn từ brief hoặc kịch bản có sẵn",
    )
    state = load_create_state()
    _render_step_overview()

    main_col, render_col = st.columns([6, 4], gap="small")
    with main_col:
        with layout.section_card("Nội dung", "Viết brief, chỉnh kịch bản và từ khóa tìm footage."):
            _render_brief_and_script_section(state)
        with layout.section_card("Nguồn video", "Chọn TikTok, Pexels, Pixabay hoặc file local."):
            uploaded_files = _render_source_section(state)
        with layout.section_card("Nâng cao", "Tùy chọn kỹ thuật cho source, ratio, thời lượng clip và số luồng."):
            with layout.advanced_accordion("Mở tùy chọn nâng cao", expanded=False):
                source_settings.render_source_advanced_settings(state)
        with layout.section_card("Giọng đọc & âm thanh", "Chọn voice, nghe thử và cấu hình nhạc nền khi cần."):
            uploaded_audio_file = _render_audio_section(state)
        with layout.section_card("Phụ đề & thương hiệu", "Dùng preset phụ đề và xem preview nhanh."):
            _render_subtitle_section(state)

    with render_col:
        with st.container(border=True):
            _render_render_rail(state, uploaded_files, uploaded_audio_file)

    save_create_state(state)
