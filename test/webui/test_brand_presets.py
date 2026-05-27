import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from webui.studio.brand_presets import (
    SubtitlePreset,
    default_subtitle_presets,
    find_subtitle_preset,
    load_subtitle_presets,
    save_subtitle_presets,
)


class TestBrandPresets(unittest.TestCase):
    def test_default_presets_include_vietnamese_caption_preset(self):
        presets = default_subtitle_presets()

        self.assertIn("Clean Vietnamese Shorts", [preset.name for preset in presets])
        vietnamese = find_subtitle_preset(presets, "Clean Vietnamese Shorts")
        self.assertEqual(vietnamese.font_name, "BeVietnamPro-Bold.ttf")

    def test_save_and_load_presets_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "brand_presets.json")
            presets = [
                SubtitlePreset(
                    name="Custom",
                    font_name="BeVietnamPro-Regular.ttf",
                    font_size=54,
                    text_fore_color="#FAFAFA",
                    stroke_color="#101010",
                    stroke_width=1.2,
                    subtitle_position="bottom",
                    custom_position=70.0,
                )
            ]

            save_subtitle_presets(path, presets)
            loaded = load_subtitle_presets(path)

        self.assertEqual(loaded, presets)

    def test_load_presets_falls_back_to_defaults_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "brand_presets.json")
            path.write_text("{not-json", encoding="utf-8")

            loaded = load_subtitle_presets(path)

        self.assertEqual(loaded, default_subtitle_presets())

    def test_load_presets_ignores_incomplete_records(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "brand_presets.json")
            path.write_text(json.dumps([{"name": "Broken"}]), encoding="utf-8")

            loaded = load_subtitle_presets(path)

        self.assertEqual(loaded, default_subtitle_presets())


if __name__ == "__main__":
    unittest.main()
