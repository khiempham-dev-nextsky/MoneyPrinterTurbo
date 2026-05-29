import threading
from pathlib import Path
from uuid import uuid4

import streamlit as st
from loguru import logger

from app.config import config
from app.models import const
from app.services import source_video
from app.services import state as sm
from app.services import translate_video as translate_service
from app.utils import utils
from webui.studio.i18n import tr
from webui.studio.state import (
    StudioRenderSnapshot,
    StudioTranslateState,
    build_translate_params,
    save_translate_state,
)
from webui.studio.validators import validate_translate_request


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


def append_translate_log(task_id: str, line: str, task_dir: str | None = None) -> None:
    cleaned = str(line or "").rstrip()
    if not cleaned:
        return

    record = _registry_record(task_id)
    with _REGISTRY_LOCK:
        record["log_lines"].append(cleaned)
        record["log_lines"] = record["log_lines"][-_MAX_LOG_LINES:]

    directory = Path(task_dir) if task_dir else _task_dir(task_id)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "studio-translate.log").open("a", encoding="utf-8") as file:
        file.write(cleaned + "\n")


def _read_log_file(task_dir: Path) -> list[str]:
    log_file = task_dir / "studio-translate.log"
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
        return "Translating"
    return "Idle"


def get_translate_snapshot(task_id: str, task_dir: str | None = None) -> StudioRenderSnapshot:
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


def get_active_translate_snapshot() -> StudioRenderSnapshot | None:
    task_id = (
        st.session_state.get("studio_active_translate_task_id")
        or st.session_state.get("studio_last_translate_task_id")
        or _ACTIVE_TASK_ID
    )
    if not task_id:
        return None
    task_id = str(task_id)
    st.session_state["studio_active_translate_task_id"] = task_id
    return get_translate_snapshot(task_id)


def clear_active_translate_task() -> None:
    global _ACTIVE_TASK_ID
    _ACTIVE_TASK_ID = None
    for key in ("studio_active_translate_task_id", "studio_last_translate_task_id"):
        if key in st.session_state:
            del st.session_state[key]


def _start_background_thread(target, *args, **kwargs) -> threading.Thread:
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


def _run_translate_job(task_id: str, params) -> None:
    task_dir = _task_dir(task_id)

    def sink(message):
        append_translate_log(task_id, str(message).rstrip(), task_dir=str(task_dir))

    sink_id = logger.add(
        sink,
        level="DEBUG",
        filter=lambda record: record["extra"].get("studio_translate_task_id") == task_id,
    )
    try:
        with logger.contextualize(studio_translate_task_id=task_id):
            append_translate_log(task_id, "Start translating video", task_dir=str(task_dir))
            result = translate_service.start(task_id=task_id, params=params)
            if not result or "videos" not in result:
                sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
                _registry_record(task_id)["error"] = "Video translation failed"
                return
            _registry_record(task_id)["result"] = result
    except Exception as exc:
        logger.exception(exc)
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED, error=str(exc))
        _registry_record(task_id)["error"] = str(exc)
        append_translate_log(task_id, f"ERROR: {exc}", task_dir=str(task_dir))
    finally:
        logger.remove(sink_id)


def start_translate_job(
    state: StudioTranslateState,
    uploaded_source_file=None,
    background_runner=_start_background_thread,
) -> StudioRenderSnapshot:
    global _ACTIVE_TASK_ID
    task_id = str(uuid4())
    _task_dir(task_id)

    if uploaded_source_file:
        state.source_video_path = source_video.persist_uploaded_source_video(
            task_id,
            uploaded_source_file,
        )

    params = build_translate_params(state)
    issues = validate_translate_request(params, dict(config.app))
    if issues:
        raise ValueError("\n".join(tr(issue.message) for issue in issues))

    save_translate_state(state)
    st.session_state["studio_active_translate_task_id"] = task_id
    st.session_state["studio_last_translate_task_id"] = task_id
    st.session_state["studio_translate_autorefresh"] = True
    _ACTIVE_TASK_ID = task_id

    config.save_config()
    _registry_record(task_id)
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=0)
    append_translate_log(task_id, "Queued translate task")
    background_runner(_run_translate_job, task_id, params)
    return get_translate_snapshot(task_id)
