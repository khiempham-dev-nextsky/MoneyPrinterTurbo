import json
from pathlib import Path

import streamlit as st


def read_task_script_data(task_dir: str | Path) -> dict:
    script_file = Path(task_dir) / "script.json"
    if not script_file.exists():
        return {}
    try:
        payload = json.loads(script_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


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
        params = script_data.get("params", {}) if isinstance(script_data, dict) else {}
        outputs.append(
            {
                "task_id": task_dir.name,
                "path": str(task_dir),
                "videos": videos,
                "script": script_data.get("script", ""),
                "search_terms": script_data.get("search_terms", []),
                "subject": params.get("video_subject", ""),
                "source": params.get("video_source", ""),
                "params": params,
                "modified_time": task_dir.stat().st_mtime,
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
            st.video(video_path)
            st.code(video_path)
