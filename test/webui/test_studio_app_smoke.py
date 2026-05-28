import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from webui.studio.components import layout


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
        visible_values = markdown_values + subheader_values
        self.assertTrue(
            any("MoneyPrinterTurbo Studio" in value for value in markdown_values),
            markdown_values,
        )
        self.assertTrue(
            any("Create Video" in value for value in markdown_values),
            markdown_values,
        )
        self.assertTrue(
            any("Brief & Script" in value for value in visible_values),
            visible_values,
        )
        self.assertTrue(
            any("Render & Monitor" in value for value in visible_values),
            visible_values,
        )
        self.assertTrue(
            any("Studio v" in value for value in markdown_values),
            markdown_values,
        )

    def test_studio_shell_uses_custom_compact_sidebar(self):
        root = Path(__file__).parent.parent.parent
        navigation_source = (root / "webui" / "studio" / "navigation.py").read_text(
            encoding="utf-8"
        )
        theme_source = (root / "webui" / "studio" / "theme.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("st.navigation", navigation_source)
        self.assertIn("render_sidebar", navigation_source)
        self.assertIn("studio_sidebar_collapsed", navigation_source)
        self.assertIn("studio-nav-button", navigation_source)
        self.assertIn("@media (max-width: 700px)", navigation_source)
        self.assertIn("width: 72px", navigation_source)
        self.assertIn('[data-testid="stVerticalBlock"]', navigation_source)
        self.assertIn("padding-left: 88px", navigation_source)
        self.assertNotIn("font-size: 0 !important", navigation_source)
        self.assertIn('"primary": "#0066cc"', theme_source)
        self.assertIn('"canvas": "#ffffff"', theme_source)
        self.assertIn('"canvas_parchment": "#f5f5f7"', theme_source)
        self.assertIn('"surface_card": "#ffffff"', theme_source)
        self.assertIn('"ink": "#1d1d1f"', theme_source)
        self.assertNotIn('"canvas": "#000000"', theme_source)
        self.assertNotIn("black canvas", theme_source)

    def test_custom_shell_renders_each_studio_page(self):
        app_path = Path(__file__).parent.parent.parent / "webui" / "Main.py"
        expected_headers = {
            "create": "Create Video",
            "projects": "Projects",
            "assets": "Assets",
            "brand": "Brand",
            "settings": "Settings",
        }

        for page_key, heading in expected_headers.items():
            with self.subTest(page_key=page_key):
                app = AppTest.from_file(str(app_path))
                app.session_state["studio_current_page"] = page_key
                app.run(timeout=30)

                self.assertEqual(app.exception, [])
                markdown_values = [item.value for item in app.markdown]
                self.assertTrue(
                    any(f"<h1>{heading}</h1>" in value for value in markdown_values),
                    markdown_values,
                )

    def test_collapsed_sidebar_keeps_icon_navigation_visible(self):
        app_path = Path(__file__).parent.parent.parent / "webui" / "Main.py"
        app = AppTest.from_file(str(app_path))
        app.session_state["studio_sidebar_collapsed"] = True
        app.run(timeout=30)

        self.assertEqual(app.exception, [])
        sidebar_labels = [button.label for button in app.sidebar.button]
        sidebar_icons = [button.icon for button in app.sidebar.button]
        self.assertEqual(sidebar_labels, ["", "", "", "", "", ""])
        self.assertIn(":material/menu:", sidebar_icons)
        self.assertIn(":material/add_circle:", sidebar_icons)
        self.assertIn(":material/folder_open:", sidebar_icons)
        self.assertIn(":material/perm_media:", sidebar_icons)
        self.assertIn(":material/format_paint:", sidebar_icons)
        self.assertIn(":material/tune:", sidebar_icons)
        self.assertNotIn("P  Projects", sidebar_labels)

    def test_create_page_source_no_longer_uses_tabbed_workflow(self):
        create_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "pages" / "create.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("st.tabs", create_source)
        self.assertNotIn('"1. Brief"', create_source)
        self.assertNotIn('"6. Review & Render"', create_source)
        self.assertIn("layout.section_card", create_source)

    def test_summary_block_generates_renderable_inline_html(self):
        with patch.object(layout.st, "markdown") as markdown:
            layout.summary_block([("Subject", ""), ("Source", "tiktok")])

        html = markdown.call_args.args[0]
        kwargs = markdown.call_args.kwargs
        self.assertTrue(kwargs["unsafe_allow_html"])
        self.assertNotIn("\n            <div", html)
        self.assertIn('<span class="studio-summary-value" title="-">-</span>', html)
        self.assertIn(
            '<span class="studio-summary-value" title="tiktok">tiktok</span>',
            html,
        )

    def test_theme_uses_readable_system_fonts_for_operational_controls(self):
        theme_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "theme.py"
        ).read_text(encoding="utf-8")

        self.assertIn("-apple-system, BlinkMacSystemFont", theme_source)
        self.assertNotIn("Cormorant Garamond", theme_source)
        self.assertNotIn("text-transform: uppercase !important", theme_source)
        self.assertNotIn("letter-spacing: 2.5px", theme_source)
        self.assertIn(
            'button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"]',
            theme_source,
        )
        self.assertIn(
            '[data-testid="stWidgetLabel"] .colored-text',
            theme_source,
        )

    def test_layout_helpers_keep_long_paths_readable(self):
        long_path = "/Users/example/MoneyPrinterTurbo/storage/tasks/abc/final-video-output.mp4"

        truncated = layout.truncate_middle(long_path, max_length=42)

        self.assertLessEqual(len(truncated), 42)
        self.assertTrue(truncated.startswith("/Users/example"))
        self.assertTrue(truncated.endswith("final-video-output.mp4"))
        self.assertIn("...", truncated)

    def test_project_asset_brand_pages_use_light_layout_primitives(self):
        root = Path(__file__).parent.parent.parent
        project_source = (root / "webui" / "studio" / "pages" / "projects.py").read_text(
            encoding="utf-8"
        )
        assets_source = (root / "webui" / "studio" / "pages" / "assets.py").read_text(
            encoding="utf-8"
        )
        brand_source = (root / "webui" / "studio" / "pages" / "brand.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("layout.truncate_middle", project_source)
        self.assertIn("layout.section_card", project_source)
        self.assertIn("layout.truncate_middle", assets_source)
        self.assertIn("layout.section_card", assets_source)
        self.assertIn("studio-subtitle-preview", brand_source)


if __name__ == "__main__":
    unittest.main()
