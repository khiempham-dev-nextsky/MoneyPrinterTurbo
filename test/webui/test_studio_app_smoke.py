import sys
import subprocess
import unittest
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
            any("DESIGN.md" in value for value in markdown_values),
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
        self.assertIn('"canvas": "#000000"', theme_source)
        self.assertIn('"hairline": "#262626"', theme_source)
        self.assertIn("border-radius: 0px", theme_source)
        self.assertIn("letter-spacing: 2", theme_source)

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
        self.assertIn("+", sidebar_labels)
        self.assertIn("P", sidebar_labels)
        self.assertIn("A", sidebar_labels)
        self.assertIn("B", sidebar_labels)
        self.assertIn("S", sidebar_labels)
        self.assertNotIn("+  Create", sidebar_labels)

    def test_create_page_source_no_longer_uses_tabbed_workflow(self):
        create_source = (
            Path(__file__).parent.parent.parent / "webui" / "studio" / "pages" / "create.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("st.tabs", create_source)
        self.assertNotIn('"1. Brief"', create_source)
        self.assertNotIn('"6. Review & Render"', create_source)


if __name__ == "__main__":
    unittest.main()
