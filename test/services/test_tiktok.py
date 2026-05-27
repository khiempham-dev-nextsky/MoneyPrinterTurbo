import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import config
from app.services import tiktok


class TestTikTokService(unittest.TestCase):
    def setUp(self):
        self.original_app_config = dict(config.app)
        self.original_proxy_config = dict(config.proxy)

    def tearDown(self):
        config.app.clear()
        config.app.update(self.original_app_config)
        config.proxy.clear()
        config.proxy.update(self.original_proxy_config)

    def test_canonicalize_tiktok_url_normalizes_video_url(self):
        url = "https://www.tiktok.com/@creator/video/1234567890?lang=en&utm_source=test#x"

        result = tiktok.canonicalize_tiktok_url(url)

        self.assertEqual(result, "https://www.tiktok.com/@creator/video/1234567890")

    def test_canonicalize_tiktok_url_rejects_non_video_url(self):
        with self.assertRaises(ValueError):
            tiktok.canonicalize_tiktok_url("https://www.tiktok.com/tag/skincare")

    def test_canonicalize_tiktok_url_rejects_placeholder_video_id(self):
        with self.assertRaises(ValueError):
            tiktok.canonicalize_tiktok_url("https://www.tiktok.com/@creator/video/...")

    def test_parse_serpapi_results_filters_and_dedupes_tiktok_videos(self):
        payload = {
            "organic_results": [
                {
                    "link": "https://www.tiktok.com/@a/video/111?lang=en",
                    "title": "A",
                    "snippet": "first",
                },
                {
                    "link": "https://www.tiktok.com/@a/video/111?share=1",
                    "title": "A duplicate",
                    "snippet": "duplicate",
                },
                {
                    "link": "https://www.tiktok.com/tag/skincare",
                    "title": "Tag",
                    "snippet": "not a video",
                },
                {
                    "link": "https://example.com/@a/video/222",
                    "title": "External",
                    "snippet": "not tiktok",
                },
                {
                    "link": "https://www.tiktok.com/@b/video/222",
                    "title": "B",
                    "snippet": "second",
                },
                {
                    "link": "https://example.com/article",
                    "title": "Embedded TikTok",
                    "snippet": "Watch https://www.tiktok.com/@c/video/333?lang=en",
                },
            ]
        }

        results = tiktok.parse_serpapi_results(payload, query="site:tiktok.com review")

        self.assertEqual(
            [item["url"] for item in results],
            [
                "https://www.tiktok.com/@a/video/111",
                "https://www.tiktok.com/@b/video/222",
                "https://www.tiktok.com/@c/video/333",
            ],
        )
        self.assertEqual(results[0]["title"], "A")
        self.assertEqual(results[0]["snippet"], "first")
        self.assertEqual(results[0]["query"], "site:tiktok.com review")

    def test_get_tiktok_search_api_key_prefers_config(self):
        config.app["tiktok_search_api_key"] = "config-key"

        with patch.dict(os.environ, {"SERPAPI_API_KEY": "env-key"}, clear=False):
            result = tiktok.get_tiktok_search_api_key()

        self.assertEqual(result, "config-key")

    def test_get_tiktok_search_api_key_uses_environment_fallback(self):
        config.app["tiktok_search_api_key"] = ""

        with patch.dict(os.environ, {"SERPAPI_API_KEY": "env-key"}, clear=False):
            result = tiktok.get_tiktok_search_api_key()

        self.assertEqual(result, "env-key")

    def test_get_openai_api_key_uses_environment_fallback(self):
        config.app["openai_api_key"] = ""

        with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-env-key"}, clear=False):
            result = tiktok.get_openai_api_key()

        self.assertEqual(result, "openai-env-key")

    def test_extract_json_string_array_reads_plain_json(self):
        result = tiktok.extract_json_string_array('["one", "two"]')

        self.assertEqual(result, ["one", "two"])

    def test_extract_json_string_array_recovers_embedded_json(self):
        result = tiktok.extract_json_string_array('Here are queries:\n["one", "two"]\nDone')

        self.assertEqual(result, ["one", "two"])

    def test_build_tiktok_search_queries_from_terms_wraps_plain_keywords(self):
        result = tiktok.build_tiktok_search_queries_from_terms(
            ["sleep routine", "avoid caffeine"],
            amount=5,
        )

        self.assertEqual(
            result,
            [
                '"https://www.tiktok.com/@" "/video/" "sleep routine"',
                '"https://www.tiktok.com/@" "/video/" "avoid caffeine"',
            ],
        )

    def test_build_tiktok_search_queries_from_terms_keeps_existing_site_query(self):
        result = tiktok.build_tiktok_search_queries_from_terms(
            ["site:tiktok.com/@ inurl:/video sleep routine"],
            amount=5,
        )

        self.assertEqual(result, ["site:tiktok.com/@ inurl:/video sleep routine"])

    def test_rank_tiktok_candidates_only_returns_candidate_urls(self):
        candidates = [
            {
                "url": "https://www.tiktok.com/@a/video/111",
                "title": "relevant",
                "snippet": "matches",
            },
            {
                "url": "https://www.tiktok.com/@b/video/222",
                "title": "less relevant",
                "snippet": "different",
            },
        ]

        with patch(
            "app.services.tiktok.llm._generate_response",
            return_value='["https://www.tiktok.com/@b/video/222", "https://evil.example/video/9"]',
        ):
            result = tiktok.rank_tiktok_candidates(
                video_subject="skin care",
                video_script="honest skincare review",
                candidates=candidates,
                max_downloads=3,
            )

        self.assertEqual(result, ["https://www.tiktok.com/@b/video/222"])

    def test_rank_tiktok_candidates_falls_back_to_candidate_order_on_llm_error(self):
        candidates = [
            {"url": "https://www.tiktok.com/@a/video/111", "title": "A", "snippet": ""},
            {"url": "https://www.tiktok.com/@b/video/222", "title": "B", "snippet": ""},
        ]

        with patch(
            "app.services.tiktok.llm._generate_response",
            return_value="not json",
        ):
            result = tiktok.rank_tiktok_candidates(
                video_subject="skin care",
                video_script="honest skincare review",
                candidates=candidates,
                max_downloads=1,
            )

        self.assertEqual(result, ["https://www.tiktok.com/@a/video/111"])

    def test_parse_openai_web_search_response_extracts_tiktok_sources(self):
        payload = {
            "output_text": "I found https://www.tiktok.com/@text/video/333.",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Candidate video.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url": "https://www.tiktok.com/@a/video/111?lang=en",
                                    "title": "A",
                                },
                                {
                                    "type": "url_citation",
                                    "url": "https://www.tiktok.com/tag/skincare",
                                    "title": "Tag",
                                },
                            ],
                        }
                    ],
                },
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {
                                "url": "https://www.tiktok.com/@b/video/222?share=1",
                                "title": "B",
                            }
                        ]
                    },
                },
            ],
        }

        result = tiktok.parse_openai_web_search_response(payload, query="skin care")

        self.assertEqual(
            [item["url"] for item in result],
            [
                "https://www.tiktok.com/@a/video/111",
                "https://www.tiktok.com/@b/video/222",
                "https://www.tiktok.com/@text/video/333",
            ],
        )
        self.assertEqual(result[0]["provider"], "openai_web_search")
        self.assertEqual(result[0]["title"], "A")
        self.assertEqual(result[0]["query"], "skin care")

    def test_search_tiktok_urls_uses_openai_web_search_provider(self):
        config.app["tiktok_search_provider"] = "openai_web_search"
        config.app["tiktok_search_api_key"] = ""
        config.app["openai_api_key"] = "openai-key"
        config.app["openai_base_url"] = ""
        config.app["openai_model_name"] = "gpt-5-mini"
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "Candidate",
                                    "annotations": [
                                        {
                                            "type": "url_citation",
                                            "url": "https://www.tiktok.com/@a/video/111",
                                            "title": "A",
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

        with patch("app.services.tiktok.requests.post", side_effect=fake_post):
            result = tiktok.search_tiktok_urls(
                ["site:tiktok.com/@ inurl:/video productive work"],
                max_results=5,
            )

        self.assertEqual(result[0]["url"], "https://www.tiktok.com/@a/video/111")
        self.assertEqual(captured["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer openai-key")
        self.assertEqual(captured["json"]["model"], "gpt-5-mini")
        self.assertEqual(captured["json"]["tools"][0]["type"], "web_search")
        self.assertNotIn("filters", captured["json"]["tools"][0])
        self.assertIn('"https://www.tiktok.com/@" "/video/" "productive work"', captured["json"]["input"])
        self.assertNotIn("site:tiktok.com", captured["json"]["input"])
        self.assertNotIn("inurl:/video", captured["json"]["input"])

    def test_search_tiktok_urls_openai_runs_queries_until_it_has_enough_results(self):
        config.app["tiktok_search_provider"] = "openai_web_search"
        config.app["openai_api_key"] = "openai-key"
        captured_inputs = []

        class FakeResponse:
            def __init__(self, url):
                self.url = url

            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "Candidate",
                                    "annotations": [
                                        {
                                            "type": "url_citation",
                                            "url": self.url,
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }

        def fake_post(url, **kwargs):
            captured_inputs.append(kwargs["json"]["input"])
            if len(captured_inputs) == 1:
                return FakeResponse("https://www.tiktok.com/@a/video/111")
            return FakeResponse("https://www.tiktok.com/@b/video/222")

        with patch("app.services.tiktok.requests.post", side_effect=fake_post) as post:
            result = tiktok.search_tiktok_urls(["first query", "second query"], max_results=2)

        self.assertEqual(post.call_count, 2)
        self.assertEqual(
            [item["url"] for item in result],
            [
                "https://www.tiktok.com/@a/video/111",
                "https://www.tiktok.com/@b/video/222",
            ],
        )
        self.assertIn('"https://www.tiktok.com/@" "/video/" "first query"', captured_inputs[0])
        self.assertIn('"https://www.tiktok.com/@" "/video/" "second query"', captured_inputs[1])

    def test_search_tiktok_urls_openai_uses_configured_read_timeout(self):
        config.app["tiktok_search_provider"] = "openai_web_search"
        config.app["openai_api_key"] = "openai-key"
        config.app["tiktok_openai_web_search_timeout"] = 240
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "https://www.tiktok.com/@a/video/111",
                                    "annotations": [],
                                }
                            ],
                        }
                    ]
                }

        def fake_post(url, **kwargs):
            captured["timeout"] = kwargs["timeout"]
            return FakeResponse()

        with patch("app.services.tiktok.requests.post", side_effect=fake_post):
            tiktok.search_tiktok_urls(["sleep routine"], max_results=5)

        self.assertEqual(captured["timeout"], (30, 240))

    def test_search_tiktok_urls_openai_provider_requires_openai_key(self):
        config.app["tiktok_search_provider"] = "openai_web_search"
        config.app["openai_api_key"] = ""

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(ValueError, "openai_api_key is not set"):
                tiktok.search_tiktok_urls(["site:tiktok.com test"], max_results=5)

    def test_download_tiktok_video_uses_youtube_dl_options(self):
        config.app["tiktok_cookie_file"] = ""
        captured_opts = {}

        class FakeYoutubeDL:
            def __init__(self, opts):
                captured_opts.update(opts)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return None

            def download(self, urls):
                self.urls = urls

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("app.services.tiktok._tiktok_cache_dir", return_value=temp_dir),
                patch("app.services.tiktok.YoutubeDL", FakeYoutubeDL),
                patch("app.services.tiktok.glob.glob", return_value=[os.path.join(temp_dir, "video.mp4")]),
            ):
                result = tiktok.download_tiktok_video(
                    "https://www.tiktok.com/@a/video/111", task_id="task-id"
                )

        self.assertEqual(result, os.path.join(temp_dir, "video.mp4"))
        self.assertEqual(captured_opts["format"], "mp4/bestvideo+bestaudio/best")
        self.assertEqual(captured_opts["merge_output_format"], "mp4")
        self.assertTrue(captured_opts["noplaylist"])
        self.assertNotIn("cookiefile", captured_opts)

    def test_download_tiktok_video_uses_cookiefile_when_configured(self):
        config.app["tiktok_cookie_file"] = "/tmp/cookies.txt"
        captured_opts = {}

        class FakeYoutubeDL:
            def __init__(self, opts):
                captured_opts.update(opts)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return None

            def download(self, urls):
                self.urls = urls

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "video.mp4")
            with (
                patch("app.services.tiktok._tiktok_cache_dir", return_value=temp_dir),
                patch("app.services.tiktok.YoutubeDL", FakeYoutubeDL),
                patch("app.services.tiktok.glob.glob", return_value=[output_path]),
            ):
                tiktok.download_tiktok_video(
                    "https://www.tiktok.com/@a/video/111", task_id="task-id"
                )

        self.assertEqual(captured_opts["cookiefile"], "/tmp/cookies.txt")

    def test_validate_tiktok_video_rejects_missing_file(self):
        with self.assertRaises(ValueError):
            tiktok.validate_tiktok_video("/tmp/does-not-exist.mp4", min_duration=3)

    def test_validate_tiktok_video_rejects_zero_byte_file(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as fp:
            with self.assertRaises(ValueError):
                tiktok.validate_tiktok_video(fp.name, min_duration=3)

    def test_validate_tiktok_video_rejects_short_video(self):
        class FakeVideoFileClip:
            duration = 2
            fps = 30

            def __init__(self, path):
                self.path = path

            def close(self):
                return None

        with tempfile.NamedTemporaryFile(suffix=".mp4") as fp:
            fp.write(b"not-empty")
            fp.flush()
            with patch("app.services.tiktok.VideoFileClip", FakeVideoFileClip):
                with self.assertRaises(ValueError):
                    tiktok.validate_tiktok_video(fp.name, min_duration=3)

    def test_discover_and_download_continues_after_failed_download(self):
        config.app["tiktok_max_downloads"] = 2
        config.app["tiktok_min_duration"] = 3
        candidates = [
            {"url": "https://www.tiktok.com/@a/video/111", "title": "A", "snippet": ""},
            {"url": "https://www.tiktok.com/@b/video/222", "title": "B", "snippet": ""},
        ]

        def fake_download(url, task_id):
            if url.endswith("/111"):
                raise RuntimeError("download failed")
            return "/tmp/good.mp4"

        with (
            patch("app.services.tiktok.generate_tiktok_search_queries", return_value=["query"]),
            patch("app.services.tiktok.search_tiktok_urls", return_value=candidates),
            patch(
                "app.services.tiktok.rank_tiktok_candidates",
                return_value=[item["url"] for item in candidates],
            ),
            patch("app.services.tiktok.download_tiktok_video", side_effect=fake_download),
            patch("app.services.tiktok.validate_tiktok_video", return_value=6),
        ):
            result = tiktok.discover_and_download_videos(
                task_id="task-id",
                video_subject="skin care",
                video_script="honest review",
                video_language="en-US",
                search_terms=[],
                audio_duration=10,
                max_clip_duration=5,
            )

        self.assertEqual(result, ["/tmp/good.mp4"])

    def test_discover_and_download_stops_at_max_downloads(self):
        config.app["tiktok_max_downloads"] = 1
        config.app["tiktok_min_duration"] = 3
        candidates = [
            {"url": "https://www.tiktok.com/@a/video/111", "title": "A", "snippet": ""},
            {"url": "https://www.tiktok.com/@b/video/222", "title": "B", "snippet": ""},
        ]

        with (
            patch("app.services.tiktok.generate_tiktok_search_queries", return_value=["query"]),
            patch("app.services.tiktok.search_tiktok_urls", return_value=candidates),
            patch(
                "app.services.tiktok.rank_tiktok_candidates",
                return_value=[item["url"] for item in candidates],
            ),
            patch("app.services.tiktok.download_tiktok_video", return_value="/tmp/good.mp4") as download,
            patch("app.services.tiktok.validate_tiktok_video", return_value=6),
        ):
            result = tiktok.discover_and_download_videos(
                task_id="task-id",
                video_subject="skin care",
                video_script="honest review",
                video_language="en-US",
                search_terms=[],
                audio_duration=30,
                max_clip_duration=5,
            )

        self.assertEqual(result, ["/tmp/good.mp4"])
        self.assertEqual(download.call_count, 1)

    def test_discover_and_download_uses_search_terms_before_tiktok_query_llm(self):
        config.app["tiktok_max_downloads"] = 1
        config.app["tiktok_min_duration"] = 3

        with (
            patch("app.services.tiktok.generate_tiktok_search_queries") as generate_queries,
            patch(
                "app.services.tiktok.search_tiktok_urls",
                return_value=[
                    {
                        "url": "https://www.tiktok.com/@a/video/111",
                        "title": "A",
                        "snippet": "",
                    }
                ],
            ) as search_urls,
            patch(
                "app.services.tiktok.rank_tiktok_candidates",
                return_value=["https://www.tiktok.com/@a/video/111"],
            ),
            patch("app.services.tiktok.download_tiktok_video", return_value="/tmp/good.mp4"),
            patch("app.services.tiktok.validate_tiktok_video", return_value=6),
        ):
            result = tiktok.discover_and_download_videos(
                task_id="task-id",
                video_subject="sleep health",
                video_script="sleep well",
                video_language="vi-VN",
                search_terms=["sleep routine", "avoid caffeine"],
                audio_duration=5,
                max_clip_duration=5,
            )

        self.assertEqual(result, ["/tmp/good.mp4"])
        generate_queries.assert_not_called()
        search_urls.assert_called_once_with(
            queries=[
                '"https://www.tiktok.com/@" "/video/" "sleep routine"',
                '"https://www.tiktok.com/@" "/video/" "avoid caffeine"',
            ],
            max_results=20,
        )


if __name__ == "__main__":
    unittest.main()
