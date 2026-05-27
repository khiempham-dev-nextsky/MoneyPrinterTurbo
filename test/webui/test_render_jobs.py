import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import streamlit as st
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import const
from app.services import state as sm
from webui.studio import bootstrap, render_jobs
from webui.studio.state import StudioCreateState


class TestRenderJobs(unittest.TestCase):
    def tearDown(self):
        render_jobs.clear_active_render_task()

    def test_start_render_job_records_active_task_and_starts_executor(self):
        started = []

        def background_runner(target, *args, **kwargs):
            started.append((target, args, kwargs))

        state = StudioCreateState(
            video_subject="Local task",
            video_script="Use a local clip.",
            video_source="local",
            local_video_materials=[
                {"provider": "local", "url": "/tmp/local.mp4", "duration": 5}
            ],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(
                render_jobs.utils,
                "task_dir",
                side_effect=lambda sub_dir="": str(Path(tmp_dir) / sub_dir)
                if sub_dir
                else str(Path(tmp_dir)),
            ):
                snapshot = render_jobs.start_render_job(
                    state,
                    uploaded_files=[],
                    uploaded_audio_file=None,
                    background_runner=background_runner,
                )
                active_snapshot = render_jobs.get_active_render_snapshot()

        self.assertEqual(st.session_state["studio_active_render_task_id"], snapshot.task_id)
        self.assertEqual(st.session_state["studio_last_render_task_id"], snapshot.task_id)
        self.assertEqual(snapshot.progress, 0)
        self.assertIsNotNone(active_snapshot)
        self.assertEqual(active_snapshot.task_id, snapshot.task_id)
        self.assertEqual(len(started), 1)

    def test_active_snapshot_recovers_when_page_navigation_drops_active_session_key(self):
        started = []

        def background_runner(target, *args, **kwargs):
            started.append((target, args, kwargs))

        state = StudioCreateState(
            video_subject="Local task",
            video_script="Use a local clip.",
            video_source="local",
            local_video_materials=[
                {"provider": "local", "url": "/tmp/local.mp4", "duration": 5}
            ],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(
                render_jobs.utils,
                "task_dir",
                side_effect=lambda sub_dir="": str(Path(tmp_dir) / sub_dir)
                if sub_dir
                else str(Path(tmp_dir)),
            ):
                snapshot = render_jobs.start_render_job(
                    state,
                    uploaded_files=[],
                    uploaded_audio_file=None,
                    background_runner=background_runner,
                )
                sm.state.update_task(
                    snapshot.task_id,
                    state=const.TASK_STATE_PROCESSING,
                    progress=45,
                )
                del st.session_state["studio_active_render_task_id"]

                active_snapshot = render_jobs.get_active_render_snapshot()

        self.assertIsNotNone(active_snapshot)
        self.assertEqual(active_snapshot.task_id, snapshot.task_id)
        self.assertEqual(active_snapshot.progress, 45)
        self.assertEqual(
            st.session_state["studio_active_render_task_id"],
            snapshot.task_id,
        )

    def test_append_render_log_writes_registry_and_task_log_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            task_dir = Path(tmp_dir)

            render_jobs.append_render_log(
                "task-1",
                "Downloading materials",
                task_dir=str(task_dir),
            )

            snapshot = render_jobs.get_render_snapshot("task-1", task_dir=str(task_dir))
            log_file_text = (task_dir / "studio-render.log").read_text(encoding="utf-8")

        self.assertIn("Downloading materials", snapshot.log_lines)
        self.assertIn("Downloading materials", log_file_text)

    def test_get_render_snapshot_reads_state_log_and_outputs(self):
        task_id = "snapshot-task"
        with tempfile.TemporaryDirectory() as tmp_dir:
            task_dir = Path(tmp_dir)
            final_video = task_dir / "final-1.mp4"
            final_video.write_bytes(b"fake")
            (task_dir / "studio-render.log").write_text("Task completed\n", encoding="utf-8")
            sm.state.update_task(
                task_id,
                state=const.TASK_STATE_COMPLETE,
                progress=100,
                videos=[str(final_video)],
            )

            try:
                snapshot = render_jobs.get_render_snapshot(task_id, task_dir=str(task_dir))
            finally:
                sm.state.delete_task(task_id)

        self.assertEqual(snapshot.task_id, task_id)
        self.assertEqual(snapshot.status_label, "Completed")
        self.assertEqual(snapshot.progress, 100)
        self.assertEqual(snapshot.videos, [str(final_video)])
        self.assertIn("Task completed", snapshot.log_lines)

    def test_bootstrap_log_init_preserves_external_render_job_sink(self):
        received = []

        bootstrap.init_log()
        sink_id = logger.add(
            lambda message: received.append(str(message)),
            filter=lambda record: record["extra"].get("studio_task_id") == "task-keep",
        )
        try:
            bootstrap.init_log()
            logger.bind(studio_task_id="task-keep").info("keep this sink")
        finally:
            logger.remove(sink_id)

        self.assertTrue(any("keep this sink" in line for line in received), received)


if __name__ == "__main__":
    unittest.main()
