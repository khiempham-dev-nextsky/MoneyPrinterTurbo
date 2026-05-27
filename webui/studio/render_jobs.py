import os
import threading
from pathlib import Path
from uuid import uuid4

import streamlit as st
from loguru import logger

from app.config import config
from app.models import const
from app.models.schema import MaterialInfo
from app.services import state as sm
from app.services import task as tm
from app.utils import utils
from webui.studio.i18n import tr
from webui.studio.state import (
    StudioCreateState,
    StudioRenderSnapshot,
    build_video_params,
    save_create_state,
)
from webui.studio.validators import validate_render_request


_REGISTRY_LOCK = threading.Lock()
_REGISTRY: dict[str, dict] = {}
_ACTIVE_TASK_ID: str | None = None
_MAX_LOG_LINES = 300


def _registry_record(task_id: str) -> dict:
    with _REGISTRY_LOCK:
        return _REGISTRY.setdefault(
            task_id,
            {
                "log_lines": [],
                "result": None,
                "error": "",
            },
        )


def _task_dir(task_id: str) -> Path:
    task_dir = Path(utils.task_dir(task_id))
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def _task_dir_path(task_id: str) -> Path:
    return Path(utils.storage_dir()) / "tasks" / task_id


def append_render_log(task_id: str, line: str, task_dir: str | None = None) -> None:
    cleaned = str(line or "").rstrip()
    if not cleaned:
        return

    record = _registry_record(task_id)
    with _REGISTRY_LOCK:
        record["log_lines"].append(cleaned)
        record["log_lines"] = record["log_lines"][-_MAX_LOG_LINES:]

    directory = Path(task_dir) if task_dir else _task_dir(task_id)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "studio-render.log").open("a", encoding="utf-8") as file:
        file.write(cleaned + "\n")


def _read_log_file(task_dir: Path) -> list[str]:
    log_file = task_dir / "studio-render.log"
    if not log_file.exists():
        return []
    try:
        return log_file.read_text(encoding="utf-8").splitlines()[-_MAX_LOG_LINES:]
    except OSError:
        return []


def _status_label(task_state: int | None, missing: bool = False) -> str:
    if missing:
        return "Task not found"
    if task_state == const.TASK_STATE_COMPLETE:
        return "Completed"
    if task_state == const.TASK_STATE_FAILED:
        return "Failed"
    if task_state == const.TASK_STATE_PROCESSING:
        return "Rendering"
    return "Idle"


def get_render_snapshot(task_id: str, task_dir: str | None = None) -> StudioRenderSnapshot:
    directory = Path(task_dir) if task_dir else _task_dir_path(task_id)
    task = sm.state.get_task(task_id) or {}
    record = _registry_record(task_id)

    registry_lines = list(record.get("log_lines") or [])
    file_lines = _read_log_file(directory)
    log_lines = (file_lines + [line for line in registry_lines if line not in file_lines])[
        -_MAX_LOG_LINES:
    ]

    videos = task.get("videos") or []
    if not videos:
        videos = sorted(str(path) for path in directory.glob("final-*.mp4"))

    state = task.get("state")
    progress = int(task.get("progress") or 0)
    missing = not task and not directory.exists()

    return StudioRenderSnapshot(
        task_id=task_id,
        state=state,
        progress=progress,
        status_label=_status_label(state, missing=missing),
        log_lines=log_lines,
        videos=list(videos),
        task_dir=str(directory),
        error=str(record.get("error") or task.get("error") or ""),
    )


def get_active_render_snapshot() -> StudioRenderSnapshot | None:
    task_id = (
        st.session_state.get("studio_active_render_task_id")
        or st.session_state.get("studio_last_render_task_id")
        or _ACTIVE_TASK_ID
    )
    if not task_id:
        return None
    task_id = str(task_id)
    st.session_state["studio_active_render_task_id"] = task_id
    return get_render_snapshot(task_id)


def clear_active_render_task() -> None:
    global _ACTIVE_TASK_ID
    _ACTIVE_TASK_ID = None
    if "studio_active_render_task_id" in st.session_state:
        del st.session_state["studio_active_render_task_id"]
    if "studio_last_render_task_id" in st.session_state:
        del st.session_state["studio_last_render_task_id"]


def persist_uploaded_audio(task_id: str, uploaded_audio_file) -> str:
    task_dir = _task_dir(task_id)
    _, audio_ext = os.path.splitext(os.path.basename(uploaded_audio_file.name))
    audio_ext = audio_ext.lower() or ".mp3"
    custom_audio_path = task_dir / f"custom-audio{audio_ext}"
    with custom_audio_path.open("wb") as file:
        file.write(uploaded_audio_file.getbuffer())
    return str(custom_audio_path)


def persist_uploaded_materials(uploaded_files) -> list[dict]:
    local_videos_dir = Path(utils.storage_dir("local_videos", create=True))
    persisted_materials = []
    for file in uploaded_files:
        file_path = local_videos_dir / f"{file.file_id}_{file.name}"
        with file_path.open("wb") as output:
            output.write(file.getbuffer())
        material = MaterialInfo()
        material.provider = "local"
        material.url = str(file_path)
        persisted_materials.append(
            {
                "provider": material.provider,
                "url": material.url,
                "duration": material.duration,
            }
        )
    return persisted_materials


def _start_background_thread(target, *args, **kwargs) -> threading.Thread:
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


def _run_render_job(task_id: str, params) -> None:
    task_dir = _task_dir(task_id)

    def sink(message):
        append_render_log(task_id, str(message).rstrip(), task_dir=str(task_dir))

    sink_id = logger.add(
        sink,
        level="DEBUG",
        filter=lambda record: record["extra"].get("studio_task_id") == task_id,
    )
    try:
        with logger.contextualize(studio_task_id=task_id):
            append_render_log(task_id, tr("Start Generating Video"), task_dir=str(task_dir))
            logger.info(utils.to_json(params))
            result = tm.start(task_id=task_id, params=params)
            if not result or "videos" not in result:
                sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
                _registry_record(task_id)["error"] = tr("Video Generation Failed")
                return
            _registry_record(task_id)["result"] = result
    except Exception as exc:
        logger.exception(exc)
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED, error=str(exc))
        _registry_record(task_id)["error"] = str(exc)
        append_render_log(task_id, f"ERROR: {exc}", task_dir=str(task_dir))
    finally:
        logger.remove(sink_id)


def start_render_job(
    state: StudioCreateState,
    uploaded_files,
    uploaded_audio_file,
    background_runner=_start_background_thread,
) -> StudioRenderSnapshot:
    global _ACTIVE_TASK_ID
    task_id = str(uuid4())
    _task_dir(task_id)

    if uploaded_files:
        state.local_video_materials = persist_uploaded_materials(uploaded_files)

    if uploaded_audio_file:
        state.custom_audio_file = persist_uploaded_audio(task_id, uploaded_audio_file)

    params = build_video_params(state)
    issues = validate_render_request(params, dict(config.app))
    if issues:
        raise ValueError("\n".join(tr(issue.message) for issue in issues))

    save_create_state(state)
    st.session_state["studio_active_render_task_id"] = task_id
    st.session_state["studio_last_render_task_id"] = task_id
    st.session_state["studio_render_autorefresh"] = True
    _ACTIVE_TASK_ID = task_id

    config.save_config()
    _registry_record(task_id)
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=0)
    append_render_log(task_id, "Queued render task")
    background_runner(_run_render_job, task_id, params)
    return get_render_snapshot(task_id)
