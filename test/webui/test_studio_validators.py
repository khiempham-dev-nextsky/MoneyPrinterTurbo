import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.schema import VideoParams
from webui.studio.validators import validate_render_request


class TestStudioValidators(unittest.TestCase):
    def _messages(self, params, app_config):
        return [issue.message for issue in validate_render_request(params, app_config)]

    def test_requires_script_or_subject(self):
        params = VideoParams(video_subject="", video_script="")

        messages = self._messages(params, {"pexels_api_keys": ["key"]})

        self.assertIn("Video Script and Subject Cannot Both Be Empty", messages)

    def test_requires_pexels_key_for_pexels_source(self):
        params = VideoParams(video_subject="Sleep", video_source="pexels")

        messages = self._messages(params, {"pexels_api_keys": []})

        self.assertIn("Please Enter the Pexels API Key", messages)

    def test_requires_pixabay_key_for_pixabay_source(self):
        params = VideoParams(video_subject="Sleep", video_source="pixabay")

        messages = self._messages(params, {"pixabay_api_keys": ""})

        self.assertIn("Please Enter the Pixabay API Key", messages)

    def test_requires_local_materials_for_local_source(self):
        params = VideoParams(video_subject="Sleep", video_source="local")

        messages = self._messages(params, {})

        self.assertIn("Please Upload Local Files", messages)

    def test_requires_serpapi_key_for_tiktok_serpapi_source(self):
        params = VideoParams(video_subject="Sleep", video_source="tiktok")

        messages = self._messages(
            params,
            {
                "tiktok_search_provider": "serpapi",
                "tiktok_search_api_key": "",
            },
        )

        self.assertIn("Please Enter the TikTok Search API Key", messages)

    def test_requires_openai_key_for_tiktok_openai_web_search_source(self):
        params = VideoParams(video_subject="Sleep", video_source="tiktok")

        messages = self._messages(
            params,
            {
                "tiktok_search_provider": "openai_web_search",
                "openai_api_key": "",
            },
        )

        self.assertIn("Please Enter the OpenAI API Key", messages)

    def test_accepts_configured_tiktok_openai_source(self):
        params = VideoParams(video_subject="Sleep", video_source="tiktok")

        issues = validate_render_request(
            params,
            {
                "tiktok_search_provider": "openai_web_search",
                "openai_api_key": "key",
            },
        )

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
