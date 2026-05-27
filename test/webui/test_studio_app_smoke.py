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
        self.assertTrue(
            any("MoneyPrinterTurbo Studio" in value for value in markdown_values),
            markdown_values,
        )
        self.assertTrue(
            any("Create Video" in value for value in markdown_values),
            markdown_values,
        )


if __name__ == "__main__":
    unittest.main()
