import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from webui.studio.assets import get_source_diagnostics, scan_asset_directory


class TestStudioAssets(unittest.TestCase):
    def test_scan_asset_directory_returns_empty_for_missing_directory(self):
        result = scan_asset_directory("/path/that/does/not/exist", provider="local")

        self.assertEqual(result, [])

    def test_scan_asset_directory_reads_supported_media_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            video = root / "clip.mp4"
            image = root / "cover.PNG"
            ignored = root / "notes.txt"
            video.write_bytes(b"video")
            image.write_bytes(b"image")
            ignored.write_text("ignore", encoding="utf-8")

            result = scan_asset_directory(root, provider="local")

        self.assertEqual({item.name for item in result}, {"clip.mp4", "cover.PNG"})
        self.assertTrue(all(item.provider == "local" for item in result))
        self.assertTrue(all(item.size_bytes > 0 for item in result))

    def test_get_source_diagnostics_reports_missing_and_configured_sources(self):
        diagnostics = get_source_diagnostics(
            {
                "pexels_api_keys": ["pexels-key"],
                "pixabay_api_keys": [],
                "tiktok_search_provider": "openai_web_search",
                "openai_api_key": "openai-key",
                "tiktok_cookie_file": "/missing/cookies.json",
            }
        )

        by_name = {item.name: item for item in diagnostics}
        self.assertEqual(by_name["Pexels"].state, "configured")
        self.assertEqual(by_name["Pixabay"].state, "missing")
        self.assertEqual(by_name["TikTok Search"].state, "configured")
        self.assertEqual(by_name["TikTok Cookie"].state, "optional")


if __name__ == "__main__":
    unittest.main()
