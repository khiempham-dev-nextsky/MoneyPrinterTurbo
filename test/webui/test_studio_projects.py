import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from webui.studio.components.status import list_task_outputs, read_task_script_data


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


if __name__ == "__main__":
    unittest.main()
