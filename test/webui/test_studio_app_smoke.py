import sys
import subprocess
import unittest
from html import unescape
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestStudioAppSmoke(unittest.TestCase):
    def test_main_entrypoint_boots_when_cwd_is_not_project_root(self):
        app_path = Path(__file__).parent.parent.parent / "webui" / "Main.py"

        result = subprocess.run(
            [sys.executable, str(app_path)],
            cwd="/tmp",
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 0, output)
        self.assertNotIn("ModuleNotFoundError: No module named 'webui'", output)

    def test_main_entrypoint_renders_studio_create_page(self):
        app_path = Path(__file__).parent.parent.parent / "webui" / "Main.py"

        app = AppTest.from_file(str(app_path)).run(timeout=30)

        self.assertEqual(app.exception, [])
        markdown_values = [item.value for item in app.markdown]
        subheader_values = [item.value for item in app.subheader]
        visible_values = [unescape(value) for value in markdown_values + subheader_values]
        self.assertTrue(
            any("MoneyPrinterTurbo Studio" in value for value in markdown_values),
            markdown_values,
        )
        self.assertTrue(
            any("Tạo video" in value for value in visible_values),
            markdown_values,
        )
        self.assertTrue(any("Nội dung" in value for value in visible_values), visible_values)
        self.assertTrue(
            any("Tóm tắt video" in value for value in visible_values),
            visible_values,
        )

    def test_create_page_source_no_longer_uses_tabbed_workflow(self):
        create_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "pages" / "create.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("st.tabs", create_source)
        self.assertNotIn('"1. Brief"', create_source)
        self.assertNotIn('"6. Review & Render"', create_source)

    def test_create_page_renders_guided_creation_flow(self):
        app_path = Path(__file__).parent.parent.parent / "webui" / "Main.py"

        app = AppTest.from_file(str(app_path)).run(timeout=30)

        self.assertEqual(app.exception, [])
        visible_values = [
            unescape(value)
            for value in (
                [item.value for item in app.markdown]
                + [item.value for item in app.subheader]
                + [item.label for item in app.button]
            )
        ]
        expected_copy = [
            "Tạo video",
            "Tạo video ngắn từ brief hoặc kịch bản có sẵn",
            "Nội dung",
            "Nguồn video",
            "Giọng đọc & âm thanh",
            "Phụ đề & thương hiệu",
            "Nâng cao",
            "Tóm tắt video",
            "Preview 9:16",
            "Tiến trình",
            "Nhật ký hệ thống",
        ]
        for text in expected_copy:
            self.assertTrue(
                any(text in value for value in visible_values),
                f"Missing {text!r} in {visible_values}",
            )

    def test_create_page_source_defines_guided_components(self):
        create_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "pages" / "create.py"
        ).read_text(encoding="utf-8")

        self.assertIn("_render_video_summary_panel", create_source)
        self.assertIn("_render_video_preview_frame", create_source)
        self.assertIn("_render_render_progress_panel", create_source)
        self.assertIn("_render_system_log_panel", create_source)
        self.assertIn("_render_primary_cta_group", create_source)
        self.assertIn("layout.section_card", create_source)
        self.assertIn("layout.advanced_accordion", create_source)
        self.assertIn("st.columns([6, 4]", create_source)
        self.assertIn('gap="small"', create_source)

    def test_create_page_places_advanced_settings_after_video_source(self):
        create_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "pages" / "create.py"
        ).read_text(encoding="utf-8")

        source_index = create_source.index('layout.section_card("Nguồn video"')
        advanced_index = create_source.index('layout.section_card("Nâng cao"')
        audio_index = create_source.index('layout.section_card("Giọng đọc & âm thanh"')

        self.assertLess(source_index, advanced_index)
        self.assertLess(advanced_index, audio_index)

    def test_create_page_opens_system_log_in_dialog(self):
        create_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "pages" / "create.py"
        ).read_text(encoding="utf-8")
        system_log_panel = create_source[
            create_source.index("def _render_system_log_panel")
            : create_source.index("def _render_render_progress_panel")
        ]

        self.assertIn("st.dialog", create_source)
        self.assertIn("_render_system_log_dialog", create_source)
        self.assertIn("Mở nhật ký hệ thống", system_log_panel)
        self.assertNotIn("layout.advanced_accordion", system_log_panel)

    def test_create_page_theme_supports_sticky_render_preview(self):
        theme_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "theme.py"
        ).read_text(encoding="utf-8")

        self.assertIn("studio-sticky-render-anchor", theme_source)
        self.assertIn("position: sticky", theme_source)
        self.assertIn("aspect-ratio: 9 / 16", theme_source)
        self.assertIn("studio-video-preview-frame", theme_source)
        self.assertIn("studio-summary-row", theme_source)
        self.assertIn("max-width: none", theme_source)
        self.assertIn("padding-left: 6px", theme_source)
        self.assertIn("studio-log-dialog-marker", theme_source)

    def test_studio_navigation_uses_plain_text_labels(self):
        navigation_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "navigation.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn('icon="', navigation_source)

    def test_studio_sidebar_uses_responsive_initial_state(self):
        bootstrap_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "bootstrap.py"
        ).read_text(encoding="utf-8")

        self.assertIn('initial_sidebar_state="auto"', bootstrap_source)
        self.assertNotIn('initial_sidebar_state="expanded"', bootstrap_source)


if __name__ == "__main__":
    unittest.main()
