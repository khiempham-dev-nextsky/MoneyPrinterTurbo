import json
from pathlib import Path

import streamlit as st

from app.models import const
from app.services import state as sm
from webui.studio.components import layout
from webui.studio.state import StudioRenderSnapshot


def read_task_script_data(task_dir: str | Path) -> dict:
    script_file = Path(task_dir) / "script.json"
    if not script_file.exists():
        return {}
    try:
        payload = json.loads(script_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def read_task_log_lines(task_dir: str | Path, limit: int = 80) -> list[str]:
    log_file = Path(task_dir) / "studio-render.log"
    if not log_file.exists():
        return []
    try:
        return log_file.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return []


def list_task_outputs(tasks_root: str | Path, limit: int = 20) -> list[dict]:
    root = Path(tasks_root)
    if not root.exists():
        return []
    task_dirs = [item for item in root.iterdir() if item.is_dir()]
    task_dirs.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    outputs = []
    for task_dir in task_dirs[:limit]:
        videos = sorted(str(path) for path in task_dir.glob("final-*.mp4"))
        script_data = read_task_script_data(task_dir)
        log_lines = read_task_log_lines(task_dir)
        params = script_data.get("params", {}) if isinstance(script_data, dict) else {}
        task_state = sm.state.get_task(task_dir.name) or {}
        outputs.append(
            {
                "task_id": task_dir.name,
                "path": str(task_dir),
                "videos": videos,
                "log_path": str(task_dir / "studio-render.log") if log_lines else "",
                "log_excerpt": "\n".join(log_lines[-20:]),
                "script": script_data.get("script", ""),
                "search_terms": script_data.get("search_terms", []),
                "subject": params.get("video_subject", ""),
                "source": params.get("video_source", ""),
                "params": params,
                "modified_time": task_dir.stat().st_mtime,
                "state": task_state.get("state"),
                "progress": task_state.get("progress", 0),
            }
        )
    return outputs


def render_video_outputs(videos: list[str]) -> None:
    if not videos:
        st.info("No final videos found for this task.")
        return
    cols = st.columns(min(len(videos), 3))
    for index, video_path in enumerate(videos):
        with cols[index % len(cols)]:
            with st.container(border=True):
                st.video(video_path)
                layout.path_text(video_path, max_length=72)


def _state_badge(snapshot: StudioRenderSnapshot) -> None:
    if snapshot.state == const.TASK_STATE_COMPLETE:
        st.success(snapshot.status_label)
    elif snapshot.state == const.TASK_STATE_FAILED:
        st.error(snapshot.status_label)
    elif snapshot.state == const.TASK_STATE_PROCESSING:
        st.info(snapshot.status_label)
    else:
        st.warning(snapshot.status_label)


def render_active_render_panel(snapshot: StudioRenderSnapshot | None) -> None:
    if not snapshot:
        st.info("No active render task.")
        return

    from webui.studio import render_jobs

    _state_badge(snapshot)
    st.progress(max(0, min(int(snapshot.progress or 0), 100)) / 100)
    st.caption(f"Task: {snapshot.task_id}")

    if snapshot.error:
        st.error(snapshot.error)

    log_expanded = snapshot.state == const.TASK_STATE_PROCESSING
    with st.expander("Render log", expanded=log_expanded):
        if snapshot.log_lines:
            st.code("\n".join(snapshot.log_lines[-80:]))
        else:
            st.caption("No log lines yet.")

    if snapshot.videos:
        render_video_outputs(snapshot.videos)

    col_a, col_b = st.columns(2)
    with col_a:
        st.link_button(
            "Open Project Folder",
            f"file://{snapshot.task_dir}",
            use_container_width=True,
        )
    with col_b:
        if st.button("Clear active task", use_container_width=True):
            render_jobs.clear_active_render_task()
            st.rerun()

    if st.button("Refresh status", use_container_width=True):
        st.rerun()
