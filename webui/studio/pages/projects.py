from pathlib import Path

import streamlit as st

from webui.studio import bootstrap
from webui.studio.components import layout
from webui.studio.components.status import list_task_outputs, render_video_outputs


def render_page() -> None:
    layout.page_header(
        "Projects",
        "Review recent render tasks and open final videos without leaving the studio.",
    )
    tasks_root = Path(bootstrap.root_dir) / "storage" / "tasks"
    outputs = list_task_outputs(tasks_root)
    if not outputs:
        st.info("No rendered tasks found yet.")
        return

    table = [
        {
            "Task": item["task_id"],
            "Subject": item.get("subject", ""),
            "Source": item.get("source", ""),
            "Videos": len(item["videos"]),
            "Path": item["path"],
        }
        for item in outputs
    ]
    st.dataframe(table, use_container_width=True, hide_index=True)

    selected_task = st.selectbox(
        "Preview task",
        options=[item["task_id"] for item in outputs],
        index=0,
    )
    selected = next(item for item in outputs if item["task_id"] == selected_task)
    st.code(selected["path"])
    if selected.get("script"):
        with st.expander("Script and keywords", expanded=False):
            st.text_area("Script", value=selected.get("script", ""), height=160)
            st.write(selected.get("search_terms", []))
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Reuse in Create", use_container_width=True):
            params = selected.get("params", {})
            st.session_state["video_subject"] = params.get("video_subject", "")
            st.session_state["video_script"] = selected.get("script", "")
            terms = selected.get("search_terms", "")
            st.session_state["video_terms"] = (
                ", ".join(terms) if isinstance(terms, list) else str(terms or "")
            )
            st.session_state["video_language"] = params.get("video_language", "")
            st.success("Loaded task script into Create.")
    with col_b:
        st.link_button("Open Project Folder", f"file://{selected['path']}", use_container_width=True)
    render_video_outputs(selected["videos"])
