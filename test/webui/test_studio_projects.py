import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import const
from webui.studio.components.status import list_task_outputs, read_task_script_data
from webui.studio.pages import projects


class TestStudioProjects(unittest.TestCase):
    def test_read_task_script_data_returns_script_terms_and_params(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            task_dir = Path(tmp_dir)
            (task_dir / "script.json").write_text(
                json.dumps(
                    {
                        "script": "Video script",
                        "search_terms": ["sleep", "routine"],
                        "params": {
                            "video_subject": "Sleep",
                            "video_source": "tiktok",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = read_task_script_data(task_dir)

        self.assertEqual(result["script"], "Video script")
        self.assertEqual(result["search_terms"], ["sleep", "routine"])
        self.assertEqual(result["params"]["video_subject"], "Sleep")
        self.assertEqual(result["params"]["video_source"], "tiktok")

    def test_read_task_script_data_returns_empty_dict_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = read_task_script_data(tmp_dir)

        self.assertEqual(result, {})

    def test_list_task_outputs_includes_in_progress_task_log(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tasks_root = Path(tmp_dir)
            task_dir = tasks_root / "task-with-log"
            task_dir.mkdir()
            (task_dir / "studio-render.log").write_text(
                "Preparing task\nDownloading materials\n",
                encoding="utf-8",
            )

            outputs = list_task_outputs(tasks_root)

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0]["task_id"], "task-with-log")
        self.assertEqual(outputs[0]["videos"], [])
        self.assertEqual(outputs[0]["log_path"], str(task_dir / "studio-render.log"))
        self.assertIn("Downloading materials", outputs[0]["log_excerpt"])

    def test_project_task_view_helpers_create_scan_friendly_metadata(self):
        item = {
            "task_id": "d3a67136-f7ad-4f77-97b4-7d0d733c2a8d",
            "subject": "",
            "script": "Một giấc ngủ ngon bắt đầu từ những thói quen nhỏ.",
            "source": "tiktok",
            "videos": ["final-1.mp4"],
            "progress": 100,
            "state": None,
        }

        self.assertEqual(projects.task_title(item), "Một giấc ngủ ngon bắt đầu từ những thói quen nhỏ.")
        self.assertEqual(projects.short_task_id(item["task_id"]), "d3a67136...")
        self.assertEqual(projects.task_status_key(item), "done")
        self.assertEqual(projects.task_status_label(item), "Done")
        self.assertEqual(projects.source_label(item), "TikTok")

    def test_project_filters_searches_and_sorts_tasks(self):
        tasks = [
            {
                "task_id": "old-pexels",
                "subject": "Office planning",
                "source": "pexels",
                "videos": [],
                "progress": 0,
                "state": None,
                "modified_time": 10,
            },
            {
                "task_id": "new-tiktok",
                "subject": "Sleep routine",
                "source": "tiktok",
                "videos": ["final-1.mp4"],
                "progress": 100,
                "state": const.TASK_STATE_COMPLETE,
                "modified_time": 20,
            },
        ]

        filtered = projects.filter_and_sort_tasks(
            tasks,
            search_query="sleep",
            source_filter="TikTok",
            status_filter="Done",
            sort_option="Newest",
        )

        self.assertEqual([item["task_id"] for item in filtered], ["new-tiktok"])

    def test_project_page_source_defines_dashboard_components(self):
        projects_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "pages" / "projects.py"
        ).read_text(encoding="utf-8")

        expected_components = [
            "_render_projects_toolbar",
            "_render_task_table",
            "_render_task_detail_modal",
            "_render_task_detail_content",
            "_render_video_preview_card",
            "_render_task_action_group",
            "_render_script_keywords_panel",
            "_render_render_log_panel",
            "_render_empty_projects_state",
        ]
        for component in expected_components:
            self.assertIn(component, projects_source)
        self.assertIn('st.dialog("Task đang chọn"', projects_source)
        self.assertIn('icon=":material/visibility:"', projects_source)
        self.assertIn('help="Xem chi tiết"', projects_source)
        self.assertIn("studio-task-table-header", projects_source)
        self.assertIn("studio-task-table-row", projects_source)
        self.assertIn("studio-task-detail-dialog-marker", projects_source)
        self.assertIn("studio-task-detail-content-marker", projects_source)
        self.assertNotIn("list_col, detail_col", projects_source)
        self.assertNotIn("studio-task-card", projects_source)
        self.assertNotIn("Preview task", projects_source)

    def test_project_dashboard_theme_defines_badges_and_preview_states(self):
        theme_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "theme.py"
        ).read_text(encoding="utf-8")

        expected_classes = [
            "studio-badge-status-done",
            "studio-badge-status-rendering",
            "studio-badge-status-failed",
            "studio-badge-source-tiktok",
            "studio-task-table-header",
            "studio-task-table-row",
            "studio-task-table-title",
            "studio-task-detail-dialog-marker",
            "studio-task-detail-content-marker",
            "overflow-y: auto",
            "align-items: center",
            "studio-project-meta-grid",
            "studio-project-preview-empty",
            "studio-project-log-dialog-marker",
        ]
        for class_name in expected_classes:
            self.assertIn(class_name, theme_source)


if __name__ == "__main__":
    unittest.main()
