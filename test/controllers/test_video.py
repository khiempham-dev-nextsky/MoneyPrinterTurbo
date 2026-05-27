import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.controllers.v1 import video
from app.models.exception import HttpException
from app.models.schema import TaskVideoRequest


class TestVideoController(unittest.TestCase):
    def test_create_task_rejects_unsupported_video_source(self):
        request = types.SimpleNamespace(headers={})
        body = TaskVideoRequest(
            video_subject="cat",
            video_script="A cat plays.",
            video_source="douyin",
        )

        with self.assertRaises(HttpException) as cm:
            video.create_task(request=request, body=body, stop_at="video")

        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("unsupported video_source: douyin", cm.exception.message)

    def test_create_task_rejects_tiktok_without_search_api_key(self):
        request = types.SimpleNamespace(headers={})
        body = TaskVideoRequest(
            video_subject="cat",
            video_script="cat",
            video_source="tiktok",
        )

        with patch.dict(
            video.config.app,
            {"tiktok_search_provider": "serpapi", "tiktok_search_api_key": ""},
            clear=False,
        ):
            with self.assertRaises(HttpException) as cm:
                video.create_task(request=request, body=body, stop_at="video")

        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("tiktok_search_api_key is not set", cm.exception.message)

    def test_create_task_allows_tiktok_search_api_key_from_environment(self):
        request = types.SimpleNamespace(headers={})
        body = TaskVideoRequest(
            video_subject="cat",
            video_script="cat",
            video_source="tiktok",
        )

        with (
            patch.dict(video.config.app, {"tiktok_search_api_key": ""}, clear=False),
            patch.dict("os.environ", {"SERPAPI_API_KEY": "env-key"}, clear=False),
            patch.object(video.task_manager, "add_task") as add_task,
            patch.object(video.sm.state, "update_task"),
        ):
            response = video.create_task(request=request, body=body, stop_at="video")

        self.assertEqual(response["status"], 200)
        add_task.assert_called_once()

    def test_create_task_allows_tiktok_with_openai_web_search_key(self):
        request = types.SimpleNamespace(headers={})
        body = TaskVideoRequest(
            video_subject="cat",
            video_script="cat",
            video_source="tiktok",
        )

        with (
            patch.dict(
                video.config.app,
                {
                    "tiktok_search_provider": "openai_web_search",
                    "tiktok_search_api_key": "",
                    "openai_api_key": "openai-key",
                },
                clear=False,
            ),
            patch.object(video.task_manager, "add_task") as add_task,
            patch.object(video.sm.state, "update_task"),
        ):
            response = video.create_task(request=request, body=body, stop_at="video")

        self.assertEqual(response["status"], 200)
        add_task.assert_called_once()

    def test_create_task_rejects_tiktok_openai_web_search_without_openai_key(self):
        request = types.SimpleNamespace(headers={})
        body = TaskVideoRequest(
            video_subject="cat",
            video_script="cat",
            video_source="tiktok",
        )

        with (
            patch.dict(
                video.config.app,
                {
                    "tiktok_search_provider": "openai_web_search",
                    "tiktok_search_api_key": "",
                    "openai_api_key": "",
                },
                clear=False,
            ),
            patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False),
        ):
            with self.assertRaises(HttpException) as cm:
                video.create_task(request=request, body=body, stop_at="video")

        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("openai_api_key is not set", cm.exception.message)


if __name__ == "__main__":
    unittest.main()
