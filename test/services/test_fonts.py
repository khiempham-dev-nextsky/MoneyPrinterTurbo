import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services import fonts
from app.utils import utils


class TestFontService(unittest.TestCase):
    def test_list_font_names_prioritizes_vietnamese_recommended_fonts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for filename in [
                "Zed.ttf",
                "BeVietnamPro-Regular.ttf",
                "BeVietnamPro-Bold.ttf",
                "NotoSans-VF.ttf",
                "ignored.txt",
            ]:
                Path(tmp_dir, filename).write_text("", encoding="utf-8")

            result = fonts.list_font_names(tmp_dir)

        self.assertEqual(
            result,
            [
                "BeVietnamPro-Bold.ttf",
                "BeVietnamPro-Regular.ttf",
                "NotoSans-VF.ttf",
                "Zed.ttf",
            ],
        )

    def test_format_font_label_marks_vietnamese_recommended_fonts(self):
        self.assertEqual(
            fonts.format_font_label("BeVietnamPro-Bold.ttf"),
            "BeVietnamPro-Bold.ttf (Khuyến nghị tiếng Việt)",
        )
        self.assertEqual(fonts.format_font_label("Zed.ttf"), "Zed.ttf")

    def test_select_default_font_keeps_saved_font_when_available(self):
        result = fonts.select_default_font_name(
            ["BeVietnamPro-Bold.ttf", "MicrosoftYaHeiBold.ttc"],
            saved_font_name="MicrosoftYaHeiBold.ttc",
            ui_language="vi-VN",
        )

        self.assertEqual(result, "MicrosoftYaHeiBold.ttc")

    def test_select_default_font_prefers_vietnamese_font_for_vietnamese_locale(self):
        result = fonts.select_default_font_name(
            ["BeVietnamPro-Bold.ttf", "MicrosoftYaHeiBold.ttc"],
            saved_font_name="Missing.ttf",
            ui_language="vi-VN",
        )

        self.assertEqual(result, "BeVietnamPro-Bold.ttf")

    def test_select_default_font_uses_existing_default_for_non_vietnamese_locale(self):
        result = fonts.select_default_font_name(
            ["BeVietnamPro-Bold.ttf", "MicrosoftYaHeiBold.ttc"],
            saved_font_name="Missing.ttf",
            ui_language="en-US",
        )

        self.assertEqual(result, "MicrosoftYaHeiBold.ttc")

    def test_select_default_font_falls_back_to_first_font(self):
        result = fonts.select_default_font_name(
            ["Zed.ttf"],
            saved_font_name="Missing.ttf",
            ui_language="en-US",
        )

        self.assertEqual(result, "Zed.ttf")

    def test_bundled_be_vietnam_pro_fonts_render_vietnamese_text(self):
        sample_text = "Tiếng Việt: ă â ê ô ơ ư đ Á À Ả Ã Ạ"

        for font_name in ["BeVietnamPro-Bold.ttf", "BeVietnamPro-Regular.ttf"]:
            with self.subTest(font_name=font_name):
                font = ImageFont.truetype(utils.font_dir(font_name), 48)
                left, top, right, bottom = font.getbbox(sample_text)

                self.assertGreater(right - left, 0)
                self.assertGreater(bottom - top, 0)


if __name__ == "__main__":
    unittest.main()
