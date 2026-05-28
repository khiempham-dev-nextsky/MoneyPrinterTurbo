from datetime import datetime
from html import escape
import json
from pathlib import Path
import re

import streamlit as st
import streamlit.components.v1 as components

from app.models import const
from webui.studio import bootstrap
from webui.studio.components import layout
from webui.studio.components.status import list_task_outputs


STATUS_OPTIONS = ["All", "Done", "Rendering", "Failed", "Draft", "Empty"]
SORT_OPTIONS = ["Newest", "Progress", "Status"]


def short_task_id(task_id: str) -> str:
    task_id = str(task_id or "")
    return f"{task_id[:8]}..." if len(task_id) > 8 else task_id


def truncate_middle(value: str, max_chars: int = 64) -> str:
    text = str(value or "")
    if len(text) <= max_chars:
        return text
    keep = max(8, (max_chars - 3) // 2)
    return f"{text[:keep]}...{text[-keep:]}"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def task_title(item: dict) -> str:
    subject = _clean_text(item.get("subject") or item.get("params", {}).get("video_subject", ""))
    if subject:
        return subject[:120]
    script = _clean_text(item.get("script", ""))
    if script:
        sentence = re.split(r"(?<=[.!?。！？])\s+", script)[0]
        return sentence[:120]
    return f"Task {short_task_id(item.get('task_id', ''))}"


def source_label(item: dict) -> str:
    source = _clean_text(item.get("source") or item.get("params", {}).get("video_source", ""))
    mapping = {
        "tiktok": "TikTok",
        "pexels": "Pexels",
        "pixabay": "Pixabay",
        "local": "Local",
    }
    return mapping.get(source.lower(), source.title() if source else "Unknown")


def task_status_key(item: dict) -> str:
    state = item.get("state")
    progress = int(item.get("progress") or 0)
    videos = item.get("videos") or []
    script = _clean_text(item.get("script", ""))

    if state == const.TASK_STATE_FAILED:
        return "failed"
    if state == const.TASK_STATE_PROCESSING:
        return "rendering"
    if state == const.TASK_STATE_COMPLETE or progress >= 100 or videos:
        return "done"
    if script:
        return "draft"
    return "empty"


def task_status_label(item: dict) -> str:
    return {
        "done": "Done",
        "rendering": "Rendering",
        "failed": "Failed",
        "draft": "Draft",
        "empty": "Empty",
    }[task_status_key(item)]


def task_progress(item: dict) -> int:
    progress = int(item.get("progress") or 0)
    if task_status_key(item) == "done":
        progress = max(progress, 100)
    return max(0, min(progress, 100))


def modified_time_label(item: dict) -> str:
    timestamp = item.get("modified_time")
    if not timestamp:
        return "-"
    try:
        return datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d %H:%M")
    except (OSError, TypeError, ValueError):
        return "-"


def script_keywords_summary(item: dict) -> str:
    script = _clean_text(item.get("script", ""))
    keywords = item.get("search_terms") or []
    if isinstance(keywords, str):
        keywords = [term.strip() for term in keywords.split(",") if term.strip()]
    word_count = len(script.split()) if script else 0
    return f"Script: {word_count} từ, {len(keywords)} từ khóa"


def render_log_summary(item: dict) -> str:
    status_key = task_status_key(item)
    error = _clean_text(item.get("error", ""))
    log_excerpt = _clean_text(item.get("log_excerpt", ""))
    if status_key == "failed" or error or "error" in log_excerpt.lower():
        return "Log: có lỗi, mở nhật ký để xem chi tiết"
    if status_key == "done":
        return "Log: completed, no errors"
    if log_excerpt:
        return f"Log: {log_excerpt[-120:]}"
    return "Log: chưa có nhật ký render"


def filter_and_sort_tasks(
    tasks: list[dict],
    search_query: str = "",
    source_filter: str = "All",
    status_filter: str = "All",
    sort_option: str = "Newest",
) -> list[dict]:
    query = _clean_text(search_query).lower()

    def matches(item: dict) -> bool:
        if source_filter != "All" and source_label(item) != source_filter:
            return False
        if status_filter != "All" and task_status_label(item) != status_filter:
            return False
        if not query:
            return True
        haystack = " ".join(
            [
                task_title(item),
                source_label(item),
                task_status_label(item),
                str(item.get("task_id", "")),
            ]
        ).lower()
        return query in haystack

    filtered = [item for item in tasks if matches(item)]
    if sort_option == "Progress":
        return sorted(filtered, key=lambda item: (task_progress(item), item.get("modified_time") or 0), reverse=True)
    if sort_option == "Status":
        order = {"rendering": 0, "failed": 1, "done": 2, "draft": 3, "empty": 4}
        return sorted(filtered, key=lambda item: (order[task_status_key(item)], -(item.get("modified_time") or 0)))
    return sorted(filtered, key=lambda item: item.get("modified_time") or 0, reverse=True)


def _badge(label: str, class_name: str) -> str:
    return f'<span class="studio-badge {class_name}">{escape(label)}</span>'


def _task_badges(item: dict) -> str:
    source_key = source_label(item).lower()
    status_key = task_status_key(item)
    return " ".join(
        [
            _badge(source_label(item), f"studio-badge-source-{source_key}"),
            _badge(task_status_label(item), f"studio-badge-status-{status_key}"),
        ]
    )


def _set_task_for_create(selected: dict) -> None:
    params = selected.get("params", {})
    st.session_state["video_subject"] = params.get("video_subject", "")
    st.session_state["video_script"] = selected.get("script", "")
    terms = selected.get("search_terms", "")
    st.session_state["video_terms"] = ", ".join(terms) if isinstance(terms, list) else str(terms or "")
    st.session_state["video_language"] = params.get("video_language", "")


def _continue_task_in_create(selected: dict) -> None:
    st.session_state["studio_active_render_task_id"] = selected["task_id"]
    st.session_state["studio_last_render_task_id"] = selected["task_id"]


def _render_copy_path_button(path: str) -> None:
    payload = json.dumps(str(path or ""))
    components.html(
        f"""
        <button
          style="width:100%;height:38px;border:1px solid #D8DEE6;border-radius:8px;background:#FFFFFF;color:#111827;font-weight:600;cursor:pointer;"
          onclick='navigator.clipboard.writeText({payload}).then(() => this.textContent = "Đã copy path")'
        >
          Copy path
        </button>
        """,
        height=44,
    )


def _render_projects_toolbar(outputs: list[dict]) -> tuple[str, str, str, str]:
    st.markdown('<div class="studio-project-toolbar-marker"></div>', unsafe_allow_html=True)
    source_options = ["All"] + sorted({source_label(item) for item in outputs})
    search_col, source_col, status_col, sort_col = st.columns([4, 1.4, 1.4, 1.4], gap="small")
    with search_col:
        search_query = st.text_input(
            "Search tasks",
            placeholder="Tìm theo subject, source hoặc ID...",
            key="studio_projects_search",
        )
    with source_col:
        source_filter = st.selectbox("Source", source_options, key="studio_projects_source_filter")
    with status_col:
        status_filter = st.selectbox("Status", STATUS_OPTIONS, key="studio_projects_status_filter")
    with sort_col:
        sort_option = st.selectbox("Sort", SORT_OPTIONS, key="studio_projects_sort")
    return search_query, source_filter, status_filter, sort_option


def _render_empty_projects_state() -> None:
    st.info("Chưa có project nào. Tạo video đầu tiên để xem task render tại đây.")
    st.page_link("create", label="Tạo video đầu tiên")


def _render_no_selected_task_state() -> None:
    st.info("Chọn một task để xem chi tiết.")


def _render_task_table_header() -> None:
    st.markdown('<div class="studio-task-table-header"></div>', unsafe_allow_html=True)
    columns = st.columns([3, 1, 1, 0.8, 1.2, 1.35, 1], gap="small")
    labels = ["Subject", "Source", "Status", "Videos", "Progress", "Updated", "Action"]
    for column, label in zip(columns, labels):
        with column:
            st.markdown(f'<div class="studio-task-table-heading">{escape(label)}</div>', unsafe_allow_html=True)


def _render_progress_indicator(progress: int) -> str:
    return f"""
    <div class="studio-task-table-progress">
      <div style="width:{progress}%"></div>
    </div>
    <span class="studio-task-table-muted">{progress}%</span>
    """


def _render_task_table(tasks: list[dict]) -> None:
    st.markdown("### Task list")
    if not tasks:
        st.warning("Không tìm thấy task phù hợp với bộ lọc hiện tại.")
        return

    _render_task_table_header()
    for item in tasks:
        progress = task_progress(item)
        with st.container(border=True):
            st.markdown('<div class="studio-task-table-row"></div>', unsafe_allow_html=True)
            columns = st.columns([3, 1, 1, 0.8, 1.2, 1.35, 1], gap="small")
            with columns[0]:
                st.markdown(
                    f"""
                    <div class="studio-task-table-title">{escape(task_title(item))}</div>
                    <div class="studio-task-table-muted">{escape(short_task_id(item.get("task_id", "")))}</div>
                    """,
                    unsafe_allow_html=True,
                )
            with columns[1]:
                source_key = source_label(item).lower()
                st.markdown(_badge(source_label(item), f"studio-badge-source-{source_key}"), unsafe_allow_html=True)
            with columns[2]:
                st.markdown(_badge(task_status_label(item), f"studio-badge-status-{task_status_key(item)}"), unsafe_allow_html=True)
            with columns[3]:
                st.markdown(
                    f'<span class="studio-task-table-muted">{len(item.get("videos") or [])}</span>',
                    unsafe_allow_html=True,
                )
            with columns[4]:
                st.markdown(_render_progress_indicator(progress), unsafe_allow_html=True)
            with columns[5]:
                st.markdown(
                    f'<span class="studio-task-table-muted">{escape(modified_time_label(item))}</span>',
                    unsafe_allow_html=True,
                )
            with columns[6]:
                if st.button(
                    " ",
                    icon=":material/visibility:",
                    help="Xem chi tiết",
                    key=f"studio_project_detail_{item['task_id']}",
                    use_container_width=True,
                ):
                    st.session_state["studio_selected_project_task_id"] = item["task_id"]
                    _render_task_detail_modal(item)


def _render_video_preview_card(selected: dict) -> None:
    st.markdown("### Video Preview")
    videos = selected.get("videos") or []
    with st.container(border=True):
        st.markdown('<div class="studio-project-video-preview-marker"></div>', unsafe_allow_html=True)
        if not videos:
            st.markdown(
                """
                <div class="studio-project-preview-empty">
                  <strong>Chưa có video output</strong>
                  <span>Task này chưa tạo final video hoặc output đã bị xóa.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return
        st.video(videos[0])
        if len(videos) > 1:
            st.caption(f"Có {len(videos)} video output. Video đầu tiên đang được preview.")


def _render_task_action_group(selected: dict) -> None:
    st.markdown("### Actions")
    status_key = task_status_key(selected)
    videos = selected.get("videos") or []
    if status_key == "done" and videos:
        st.link_button("Mở video", f"file://{videos[0]}", type="primary", use_container_width=True)
    else:
        if st.button("Tiếp tục chỉnh sửa", type="primary", use_container_width=True):
            _continue_task_in_create(selected)
            st.success("Đã đặt task này làm task đang theo dõi trong Create.")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Dùng lại cấu hình", use_container_width=True):
            _set_task_for_create(selected)
            st.success("Đã nạp script và cấu hình vào Create.")
    with col_b:
        st.link_button("Mở thư mục dự án", f"file://{selected['path']}", use_container_width=True)
    _render_copy_path_button(selected.get("path", ""))


def _render_script_keywords_panel(selected: dict) -> None:
    st.markdown("### Kịch bản & từ khóa")
    st.caption(script_keywords_summary(selected))
    with st.expander("Xem chi tiết kịch bản & từ khóa", expanded=False):
        script = selected.get("script", "")
        if script:
            st.text_area("Script", value=script, height=180)
        else:
            st.caption("Task này chưa có script.")
        keywords = selected.get("search_terms") or []
        if keywords:
            st.write(keywords)
        else:
            st.caption("Chưa có từ khóa.")


@st.dialog("Nhật ký render", width="large")
def _render_project_log_dialog(title: str, log_text: str) -> None:
    st.markdown('<div class="studio-project-log-dialog-marker"></div>', unsafe_allow_html=True)
    st.caption(title)
    if log_text:
        st.code(log_text)
    else:
        st.caption("Chưa có log render.")


def _render_render_log_panel(selected: dict) -> None:
    st.markdown("### Nhật ký render")
    st.caption(render_log_summary(selected))
    log_text = selected.get("log_excerpt", "")
    if st.button("Xem log đầy đủ", use_container_width=True):
        _render_project_log_dialog(task_title(selected), log_text)


def _render_task_metadata(selected: dict) -> None:
    progress = task_progress(selected)
    st.markdown(
        f"""
        <div class="studio-project-detail-header">
          <h3>{escape(task_title(selected))}</h3>
          <div>{_task_badges(selected)} {_badge(f'{progress}%', 'studio-badge-progress')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metadata = [
        ("Task ID", selected.get("task_id", "")),
        ("Source", source_label(selected)),
        ("Status", task_status_label(selected)),
        ("Videos", str(len(selected.get("videos") or []))),
        ("Progress", f"{progress}%"),
        ("Updated", modified_time_label(selected)),
        ("Path", truncate_middle(selected.get("path", ""), 72)),
    ]
    rows = "".join(
        f'<div><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in metadata
    )
    st.markdown(f'<div class="studio-project-meta-grid">{rows}</div>', unsafe_allow_html=True)
    if task_status_key(selected) == "failed":
        st.error(render_log_summary(selected))


def _render_task_detail_content(selected: dict | None) -> None:
    st.markdown('<div class="studio-task-detail-content-marker"></div>', unsafe_allow_html=True)
    st.markdown("### Task đang chọn")
    if not selected:
        _render_no_selected_task_state()
        return
    with st.container(border=True):
        st.markdown('<div class="studio-task-detail-marker"></div>', unsafe_allow_html=True)
        _render_task_metadata(selected)
        _render_video_preview_card(selected)
        _render_task_action_group(selected)
        _render_script_keywords_panel(selected)
        _render_render_log_panel(selected)


@st.dialog("Task đang chọn", width="large")
def _render_task_detail_modal(selected: dict) -> None:
    st.markdown('<div class="studio-task-detail-dialog-marker"></div>', unsafe_allow_html=True)
    _render_task_detail_content(selected)


def render_page() -> None:
    layout.page_header(
        "Projects",
        "Xem lại video đã render, kiểm tra log và tiếp tục chỉnh sửa.",
    )
    tasks_root = Path(bootstrap.root_dir) / "storage" / "tasks"
    outputs = list_task_outputs(tasks_root)
    if not outputs:
        _render_empty_projects_state()
        return

    search_query, source_filter, status_filter, sort_option = _render_projects_toolbar(outputs)
    filtered = filter_and_sort_tasks(outputs, search_query, source_filter, status_filter, sort_option)
    _render_task_table(filtered)
